# =============================================================================
# backend/tests/test_models.py
#
# Unit tests for the SQLAlchemy database models.
# Runs against an in-memory SQLite database to verify schemas and relationships.
# =============================================================================

from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from models.base import Base
from models.user import User
from models.project import Project
from models.dataset import Dataset
from models.pipeline_run import PipelineRun
from models.model_artifact import ModelArtifact
from models.report import Report
from models.chat_history import ChatHistory


@pytest.fixture(name="db_session")
def fixture_db_session() -> Session:
    """
    Creates an in-memory SQLite database, creates all schemas,
    and yields a session. Tears down the database after execution.
    """
    # SQLite in-memory database
    engine = create_engine("sqlite:///:memory:", future=True)
    
    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)
    
    # Session factory
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.mark.unit
def test_user_creation_and_fields(db_session: Session) -> None:
    """Test that a User model can be created and fields are validated."""
    user = User(
        email="test_analyst@example.com",
        hashed_password="hashedpassword123",
        full_name="Alice Vance",
        role="analyst",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.email == "test_analyst@example.com"
    assert user.hashed_password == "hashedpassword123"
    assert user.full_name == "Alice Vance"
    assert user.role == "analyst"
    assert user.is_active is True
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


@pytest.mark.unit
def test_project_cascade_delete(db_session: Session) -> None:
    """Test project model creation and cascading delete of associated elements."""
    user = User(
        email="owner@example.com",
        hashed_password="securepassword",
        role="admin"
    )
    db_session.add(user)
    db_session.commit()

    project = Project(
        name="Predictive Customer Value",
        description="Predict LTV based on user activity logs.",
        owner_id=user.id
    )
    db_session.add(project)
    db_session.commit()

    dataset = Dataset(
        name="user_activity.csv",
        source_type="file_upload",
        storage_uri="s3://buckets/user_activity.csv",
        file_size_bytes=102450,
        row_count=5000,
        column_count=12,
        schema_metadata={"columns": ["id", "timestamp", "spend"]},
        project_id=project.id
    )
    
    run = PipelineRun(
        goal="Identify top spending segments",
        status="completed",
        plan={"steps": ["load", "clean", "cluster"]},
        project_id=project.id,
        dataset_id=None # We will link it in relationship later
    )

    db_session.add_all([dataset, run])
    db_session.commit()
    
    # Establish direct relations
    run.dataset_id = dataset.id
    db_session.commit()

    # Create model artifact and report
    model_art = ModelArtifact(
        name="LTV Random Forest",
        algorithm="RandomForestRegressor",
        storage_uri="s3://models/ltv_rf.pkl",
        is_deployed=False,
        project_id=project.id,
        pipeline_run_id=run.id
    )

    report_doc = Report(
        title="LTV Segment Analysis",
        summary="Executive summary of user segment findings.",
        content_markdown="# Findings\n\nHigh spender segment correlates with weekend visits.",
        file_format="pdf",
        storage_uri="s3://reports/ltv_segment_report.pdf",
        project_id=project.id,
        pipeline_run_id=run.id
    )

    chat = ChatHistory(
        session_id=uuid.uuid4(),
        sender="user",
        message_text="What are the key drivers of higher spend?",
        project_id=project.id
    )

    db_session.add_all([model_art, report_doc, chat])
    db_session.commit()

    # Query to verify they are registered
    assert db_session.query(Dataset).count() == 1
    assert db_session.query(PipelineRun).count() == 1
    assert db_session.query(ModelArtifact).count() == 1
    assert db_session.query(Report).count() == 1
    assert db_session.query(ChatHistory).count() == 1

    # Verify back-populating relationships
    assert len(project.datasets) == 1
    assert len(project.pipeline_runs) == 1
    assert len(project.models) == 1
    assert len(project.reports) == 1
    assert len(project.chat_histories) == 1

    # Delete project and verify cascading delete deletes all children
    db_session.delete(project)
    db_session.commit()

    assert db_session.query(Project).count() == 0
    assert db_session.query(Dataset).count() == 0
    assert db_session.query(PipelineRun).count() == 0
    assert db_session.query(ModelArtifact).count() == 0
    assert db_session.query(Report).count() == 0
    assert db_session.query(ChatHistory).count() == 0


@pytest.mark.unit
def test_pipeline_run_ondelete_set_null(db_session: Session) -> None:
    """Test that deleting a dataset sets the reference dataset_id on pipeline run to NULL."""
    user = User(email="test@example.com", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    project = Project(name="Test Proj", owner_id=user.id)
    db_session.add(project)
    db_session.commit()

    dataset = Dataset(
        name="churn_data.csv",
        source_type="file_upload",
        storage_uri="s3://uri",
        project_id=project.id
    )
    db_session.add(dataset)
    db_session.commit()

    run = PipelineRun(
        goal="Predict churn",
        status="pending",
        project_id=project.id,
        dataset_id=dataset.id
    )
    db_session.add(run)
    db_session.commit()

    # Delete dataset
    db_session.delete(dataset)
    db_session.commit()

    # Verify pipeline run still exists but dataset_id is set to None (ondelete="SET NULL")
    db_session.refresh(run)
    assert run.dataset_id is None
    assert db_session.query(PipelineRun).count() == 1
