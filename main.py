from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)

from pydantic import BaseModel, Field

from pwdlib import PasswordHash

from sqlalchemy import (
    create_engine,
    String,
    Boolean,
    ForeignKey,
    select,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
    Session,
)


app = FastAPI()


# ============================================================
# 1. 数据库配置
# ============================================================

DATABASE_URL = "sqlite:///./todo.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


# ============================================================
# 2. 数据库 Model
# ============================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255)
    )

    # 一个 User 可以拥有多个 Todo
    todos: Mapped[list["Todo"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    title: Mapped[str] = mapped_column(
        String(200)
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    # Todo 属于哪个用户
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    # Todo 对应的 User 对象
    owner: Mapped["User"] = relationship(
        back_populates="todos"
    )


Base.metadata.create_all(engine)


# ============================================================
# 3. API Schema
# ============================================================

class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserResponse(BaseModel):
    id: int
    username: str

    model_config = {
        "from_attributes": True
    }


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class TodoCreate(BaseModel):
    title: str


class TodoUpdate(BaseModel):
    title: str
    completed: bool


class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool
    owner_id: int

    model_config = {
        "from_attributes": True
    }


# ============================================================
# 4. 数据库 Session
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# 5. 密码工具
# ============================================================

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:

    return password_hash.verify(
        plain_password,
        hashed_password,
    )


# ============================================================
# 6. JWT
# ============================================================

SECRET_KEY = "change-this-before-production"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(
    user_id: int
) -> str:

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return token


# ============================================================
# 7. OAuth2
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login"
)


# ============================================================
# 8. 获取当前用户
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (InvalidTokenError, ValueError):

        raise credentials_exception

    user = db.get(
        User,
        user_id,
    )

    if user is None:

        raise credentials_exception

    return user


# ============================================================
# 9. 基础接口
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Todo backend is running"
    }


# ============================================================
# 10. 注册
# ============================================================

@app.post(
    "/users/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):

    statement = select(User).where(
        User.username == user_data.username
    )

    existing_user = db.scalar(statement)

    if existing_user is not None:

        raise HTTPException(
            status_code=400,
            detail="Username already exists",
        )

    user = User(
        username=user_data.username,
        password_hash=hash_password(
            user_data.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# 11. 登录
# ============================================================

@app.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    statement = select(User).where(
        User.username == form_data.username
    )

    user = db.scalar(statement)

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not verify_password(
        form_data.password,
        user.password_hash,
    ):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token(
        user.id
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# ============================================================
# 12. 当前登录用户
# ============================================================

@app.get(
    "/users/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):

    return current_user


# ============================================================
# 13. 创建 Todo
# ============================================================

@app.post(
    "/todos",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_todo(
    todo_data: TodoCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    todo = Todo(
        title=todo_data.title,
        completed=False,

        # 最关键的一句
        owner_id=current_user.id,
    )

    db.add(todo)
    db.commit()
    db.refresh(todo)

    return todo


# ============================================================
# 14. 查看自己的所有 Todo
# ============================================================

@app.get(
    "/todos",
    response_model=list[TodoResponse],
)
def get_todos(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    statement = select(Todo).where(
        Todo.owner_id == current_user.id
    )

    todos = db.scalars(
        statement
    ).all()

    return todos


# ============================================================
# 15. 查看自己的某一个 Todo
# ============================================================

@app.get(
    "/todos/{todo_id}",
    response_model=TodoResponse,
)
def get_todo(
    todo_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    statement = select(Todo).where(
        Todo.id == todo_id,
        Todo.owner_id == current_user.id,
    )

    todo = db.scalar(statement)

    if todo is None:

        raise HTTPException(
            status_code=404,
            detail="Todo not found",
        )

    return todo


# ============================================================
# 16. 修改自己的 Todo
# ============================================================

@app.put(
    "/todos/{todo_id}",
    response_model=TodoResponse,
)
def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    statement = select(Todo).where(
        Todo.id == todo_id,
        Todo.owner_id == current_user.id,
    )

    todo = db.scalar(statement)

    if todo is None:

        raise HTTPException(
            status_code=404,
            detail="Todo not found",
        )

    todo.title = todo_data.title
    todo.completed = todo_data.completed

    db.commit()
    db.refresh(todo)

    return todo


# ============================================================
# 17. 删除自己的 Todo
# ============================================================

@app.delete(
    "/todos/{todo_id}",
    response_model=TodoResponse,
)
def delete_todo(
    todo_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):

    statement = select(Todo).where(
        Todo.id == todo_id,
        Todo.owner_id == current_user.id,
    )

    todo = db.scalar(statement)

    if todo is None:

        raise HTTPException(
            status_code=404,
            detail="Todo not found",
        )

    db.delete(todo)
    db.commit()

    return todo