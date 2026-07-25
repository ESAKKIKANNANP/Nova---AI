# =============================================================================
# backend/tests/test_chat_agent.py
#
# Unit tests for the Chat Agent and WebSocket endpoint.
# =============================================================================

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from api.v1.endpoints.chat import router

# Setup a test FastAPI app
app = FastAPI()
app.include_router(router, prefix="/chat")
client = TestClient(app)

def test_chat_websocket_streaming():
    """
    Tests the websocket endpoint simulating a LangGraph token stream.
    Since LangGraph astream_events is deeply integrated with LangChain, 
    we mock it to yield fake tokens.
    """
    with patch("api.v1.endpoints.chat.chat_app") as mock_app:
        
        # Async generator mock for astream_events
        async def mock_stream(*args, **kwargs):
            yield {"event": "on_chat_model_stream", "data": {"chunk": type('obj', (object,), {'content': 'Hello'})}}
            yield {"event": "on_chat_model_stream", "data": {"chunk": type('obj', (object,), {'content': ' World'})}}
            
        mock_app.astream_events = mock_stream
        
        with client.websocket_connect("/chat/stream/test_session") as websocket:
            websocket.send_text("Explain the model.")
            
            # Receive tokens
            data1 = websocket.receive_text()
            data2 = websocket.receive_text()
            done = websocket.receive_text()
            
            assert data1 == "Hello"
            assert data2 == " World"
            assert done == "[DONE]"

def test_chat_history():
    """Tests retrieving chat history from the checkpointer."""
    with patch("api.v1.endpoints.chat.chat_app") as mock_app:
        # Mock State Snapshot
        from langchain_core.messages import HumanMessage, AIMessage
        
        mock_snapshot = type('obj', (object,), {
            'values': {
                'messages': [
                    HumanMessage(content="Hi"),
                    AIMessage(content="Hello there")
                ]
            }
        })
        
        mock_app.get_state.return_value = mock_snapshot
        
        response = client.get("/chat/history/test_session")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Hi"
        assert data["messages"][1]["role"] == "ai"
        assert data["messages"][1]["content"] == "Hello there"
