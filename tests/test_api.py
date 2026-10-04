from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app

from app.database import (
    Base,
    get_db,
)


# ============================================================
# 1. 测试数据库
# ============================================================

TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
)


# ============================================================
# 2. 用测试数据库替换正式数据库
# ============================================================

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ============================================================
# 3. 创建测试客户端
# ============================================================

client = TestClient(app)


# ============================================================
# 4. 每个测试前清空并重新创建数据库
# ============================================================

def setup_function():
    Base.metadata.drop_all(
        bind=test_engine
    )

    Base.metadata.create_all(
        bind=test_engine
    )


# ============================================================
# 5. 测试
# ============================================================

def test_root():

    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "Todo backend is running"
    }


def test_register_user():

    response = client.post(
        "/users/register",
        json={
            "username": "coco",
            "password": "12345678",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "coco"

    assert "id" in data

    assert "password" not in data

    assert "password_hash" not in data



def test_login():

    client.post(
        "/users/register",
        json={
            "username": "coco",
            "password": "12345678",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "coco",
            "password": "12345678",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data

    assert data["token_type"] == "bearer"

def register_and_login(
    username="coco",
    password="12345678",
):
    client.post(
        "/users/register",
        json={
            "username": username,
            "password": password,
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )

    token = response.json()[
        "access_token"
    ]

    return {
        "Authorization": f"Bearer {token}"
    }

def test_create_todo():

    headers = register_and_login()

    response = client.post(
        "/todos",
        json={
            "title": "学习 FastAPI"
        },
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "学习 FastAPI"

    assert data["completed"] is False

    assert data["owner_id"] == 1

def test_create_todo_without_login():

    response = client.post(
        "/todos",
        json={
            "title": "偷偷创建 Todo"
        },
    )

    assert response.status_code == 401

def test_users_cannot_see_each_others_todos():

    coco_headers = register_and_login(
        username="coco",
        password="12345678",
    )

    client.post(
        "/todos",
        json={
            "title": "coco 的 Todo"
        },
        headers=coco_headers,
    )

    zhangsan_headers = register_and_login(
        username="zhangsan",
        password="abcdefgh",
    )

    response = client.get(
        "/todos",
        headers=zhangsan_headers,
    )

    assert response.status_code == 200

    assert response.json() == []

def test_user_cannot_access_other_users_todo():

    coco_headers = register_and_login(
        "coco",
        "12345678",
    )

    create_response = client.post(
        "/todos",
        json={
            "title": "coco 的秘密 Todo"
        },
        headers=coco_headers,
    )

    todo_id = create_response.json()["id"]

    zhangsan_headers = register_and_login(
        "zhangsan",
        "abcdefgh",
    )

    response = client.get(
        f"/todos/{todo_id}",
        headers=zhangsan_headers,
    )

    assert response.status_code == 404