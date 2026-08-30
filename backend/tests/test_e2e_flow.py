"""
End-to-end integration test verifying full user journey:
1. Signup & Auth
2. Profile update (PATCH /api/auth/me)
3. Onboarding initialization & question answering
4. Skill DAG Graph retrieval
5. Next activity generation
6. Persistent Chat Session & Tutor interaction
7. Activity submission, evaluation, and mastery update
"""
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import get_db, SessionLocal
from app.db.models import SkillNode, SkillEdge, User, LearnerProfile
from app.config import settings

client = TestClient(app)


def test_full_user_journey():
    # 1. Signup
    test_user_id = str(uuid.uuid4())[:8]
    email = f"learner_{test_user_id}@test.com"
    username = f"user_{test_user_id}"
    password = "SecurePassword123!"

    signup_res = client.post("/api/auth/signup", json={
        "email": email,
        "username": username,
        "password": password,
        "display_name": f"Test Learner {test_user_id}",
    })
    assert signup_res.status_code == 201, signup_res.text
    auth_data = signup_res.json()
    token = auth_data["access_token"]
    learner_id = auth_data["learner_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Me
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["learner_id"] == learner_id

    # 3. Update Profile (PATCH /api/auth/me)
    patch_res = client.patch("/api/auth/me", headers=headers, json={
        "display_name": "Updated Super Learner",
        "target_role": "Senior Cloud Architect",
        "weekly_hours": 12.0,
        "learning_preferences": ["projects", "exercises"],
        "preferences": {"animations": True}
    })
    assert patch_res.status_code == 200
    updated_me = patch_res.json()
    assert updated_me["display_name"] == "Updated Super Learner"
    assert updated_me["target_role"] == "Senior Cloud Architect"
    assert updated_me["weekly_hours"] == 12.0
    assert updated_me["learning_preferences"] == ["projects", "exercises"]

    # 4. Onboarding Chat
    onboard_chat_res = client.post("/api/onboarding/chat", headers=headers, json={
        "message": "I want to master backend web architectures and databases."
    })
    assert onboard_chat_res.status_code == 200
    onboard_data = onboard_chat_res.json()
    assert "state" in onboard_data

    # 5. Skill Graph DAG
    graph_res = client.get("/api/graph", headers=headers)
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert len(graph_data["nodes"]) > 0
    assert len(graph_data["edges"]) > 0

    # 6. Next Activity
    act_res = client.get(f"/api/learners/{learner_id}/next-activity", headers=headers)
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert "activity" in act_data
    activity_id = act_data["activity_id"]

    # 7. Persistent Chat Session
    new_sess_res = client.post("/api/chat/sessions", headers=headers, json={
        "title": "Database Optimization Session"
    })
    assert new_sess_res.status_code == 201
    session_id = new_sess_res.json()["id"]

    # Send chat message to tutor
    msg_res = client.post(f"/api/chat/sessions/{session_id}/messages", headers=headers, json={
        "content": "Can you give me a hint about connection pooling and query optimization?",
        "activity_id": activity_id,
    })
    assert msg_res.status_code == 200
    msg_data = msg_res.json()
    assert "assistant_message" in msg_data
    assert len(msg_data["assistant_message"]["content"]) > 0

    # Retrieve session history
    get_sess_res = client.get(f"/api/chat/sessions/{session_id}", headers=headers)
    assert get_sess_res.status_code == 200
    sess_detail = get_sess_res.json()
    assert len(sess_detail["messages"]) >= 2

    # 8. Submit Activity Solution
    submit_res = client.post(f"/api/learners/{learner_id}/activities/{activity_id}/submit", headers=headers, json={
        "answer": "I implemented an indexed B-tree database structure with connection pooling, prepared statements, and async query batching.",
    })
    assert submit_res.status_code == 200
    submit_data = submit_res.json()
    assert "evaluation" in submit_data
    assert "score" in submit_data["evaluation"]
    assert "learner_state" in submit_data
    assert submit_data["learner_state"]["attempts"] >= 1

    # 9. Verify History
    history_res = client.get(f"/api/learners/{learner_id}/activities", headers=headers)
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert history_data["activities_completed"] >= 1

    print("\n✅ Full End-to-End User Journey test passed successfully!")


if __name__ == "__main__":
    test_full_user_journey()
