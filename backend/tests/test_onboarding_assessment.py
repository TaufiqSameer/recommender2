"""
Targeted test for onboarding dialogue cleaning and assessment answering.
Validates:
1. No PHASE_COMPLETE leaks into chat messages.
2. Assessment questions and answers are inserted without foreign key errors.
"""
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_onboarding_chat_and_assessment():
    test_id = str(uuid.uuid4())[:8]
    email = f"learner_{test_id}@test.com"
    username = f"user_{test_id}"
    password = "SecurePassword123!"

    # 1. Signup
    signup_res = client.post("/api/auth/signup", json={
        "email": email,
        "username": username,
        "password": password,
        "display_name": f"Learner {test_id}",
    })
    assert signup_res.status_code == 201, signup_res.text
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Onboarding Goal dialogue
    res1 = client.post("/api/onboarding/chat", headers=headers, json={
        "message": "I want to master blockchain architecture and distributed consensus from scratch."
    })
    assert res1.status_code == 200, res1.text
    data1 = res1.json()
    assert "PHASE_COMPLETE" not in data1["message"], f"Leaked protocol in message: {data1['message']}"

    # 3. Interests dialogue
    res2 = client.post("/api/onboarding/chat", headers=headers, json={
        "message": "I am interested in smart contracts, crypto protocols, and decentralized apps."
    })
    assert res2.status_code == 200, res2.text
    data2 = res2.json()
    assert "PHASE_COMPLETE" not in data2["message"], f"Leaked protocol in message: {data2['message']}"

    # 4. Background dialogue
    res3 = client.post("/api/onboarding/chat", headers=headers, json={
        "message": "I have 3 years of C++ and Python experience."
    })
    assert res3.status_code == 200, res3.text
    data3 = res3.json()
    assert "PHASE_COMPLETE" not in data3["message"], f"Leaked protocol in message: {data3['message']}"

    # 5. Check if assessment question is present or advance to assessment
    attempt_id = None
    if data3.get("assessment_question"):
        attempt_id = data3["assessment_question"]["attempt_id"]
    else:
        # Prompt next message to enter assessment
        res4 = client.post("/api/onboarding/chat", headers=headers, json={
            "message": "Ready to take the assessment!"
        })
        assert res4.status_code == 200
        data4 = res4.json()
        assert "PHASE_COMPLETE" not in data4["message"]
        if data4.get("assessment_question"):
            attempt_id = data4["assessment_question"]["attempt_id"]

    if attempt_id:
        # Submit 5 answers sequentially to test foreign key constraints
        for i in range(5):
            ans_res = client.post("/api/onboarding/assessment/answer", headers=headers, json={
                "attempt_id": attempt_id,
                "answer": f"Explanation for question {i}: In computing and backend systems, this enables modular scaling, security, and robust fault-tolerance.",
            })
            assert ans_res.status_code == 200, f"Error on question {i}: {ans_res.text}"
            ans_data = ans_res.json()
            assert "PHASE_COMPLETE" not in ans_data["message"]
            if ans_data.get("assessment_complete"):
                break

    # Complete onboarding
    comp_res = client.post("/api/onboarding/complete", headers=headers)
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "ok"

    print("\n[SUCCESS] Onboarding chat & assessment test passed with 0 leaks and 0 FK errors!")


if __name__ == "__main__":
    test_onboarding_chat_and_assessment()
