def test_signup_and_login(client):
    # 1. 회원가입
    response = client.post(
        "/usr/signup",
        json={
            "email": "test@test.com",
            "username": "testuser",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@test.com"

    # 2. 로그인
    response = client.post(
        "/usr/login",
        json={
            "email": "test@test.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()