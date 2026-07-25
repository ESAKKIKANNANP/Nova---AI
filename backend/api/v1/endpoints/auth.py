# =============================================================================
# backend/api/v1/endpoints/auth.py
#
# Endpoints for Authentication: Registration, Login, Refresh.
# =============================================================================

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr

from db.session import get_async_db
from db.models.user import User, RoleEnum
from services.auth_service import (
    verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
)
from api.v1.dependencies.auth import get_current_user

router = APIRouter()

class UserCreate(BaseModel):
    name: str | None = None
    email: EmailStr
    password: str
    confirmPassword: str | None = None
    role: RoleEnum = RoleEnum.VIEWER

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str
    createdAt: str
    updatedAt: str

class AuthTokens(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int

class AuthResponse(BaseModel):
    user: UserResponse
    tokens: AuthTokens

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: AuthResponse

def _role_for_frontend(role: RoleEnum) -> str:
    role_map = {
        RoleEnum.ADMIN: "admin",
        RoleEnum.ANALYST: "analyst",
        RoleEnum.VIEWER: "viewer",
    }
    return role_map.get(role, "viewer")

def _display_name(user: User, fallback_name: str | None = None) -> str:
    if fallback_name:
        return fallback_name
    return user.email.split("@", 1)[0]

def _auth_response(user: User, name: str | None = None) -> ApiResponse:
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    now = datetime.now(timezone.utc).isoformat()
    return ApiResponse(
        success=True,
        message="Authenticated successfully",
        data=AuthResponse(
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                name=_display_name(user, name),
                role=_role_for_frontend(user.role),
                createdAt=now,
                updatedAt=now,
            ),
            tokens=AuthTokens(
                accessToken=access_token,
                refreshToken=refresh_token,
                expiresIn=30 * 60,
            ),
        ),
    )

@router.post("/register", response_model=ApiResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
    if user_data.confirmPassword is not None and user_data.password != user_data.confirmPassword:
        raise HTTPException(status_code=422, detail="Passwords do not match")

    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_verified=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return _auth_response(new_user, user_data.name)

@router.post("/login")
async def login(response: Response, credentials: LoginRequest, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalars().first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _auth_response(user)
    
    # Store refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=payload.data.tokens.refreshToken,
        httponly=True,
        samesite="lax",
        secure=False, # Set to True in prod over HTTPS
        max_age=7 * 24 * 60 * 60 # 7 days
    )
    
    return payload

@router.post("/refresh")
async def refresh_token(response: Response, refresh_token: str = None, db: AsyncSession = Depends(get_async_db)):
    """In a real app, you'd pull the refresh_token from cookies using FastAPI's Request/Cookie Depends.
       For this mock, we assume it's passed or intercepted."""
    # Assuming the token is manually passed or extracted via Cookie
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    user_id = payload.get("sub")
    
    # Validate user exists
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    new_access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
