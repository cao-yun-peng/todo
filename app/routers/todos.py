from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    User,
    Todo,
)

from app.schemas import (
    TodoCreate,
    TodoUpdate,
    TodoResponse,
)

from app.auth import get_current_user


router = APIRouter(
    prefix="/todos",
    tags=["todos"],
)


# ============================================================
# 创建 Todo
# ============================================================

@router.post(
    "",
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
        owner_id=current_user.id,
    )

    db.add(todo)
    db.commit()
    db.refresh(todo)

    return todo


# ============================================================
# 查询自己的全部 Todo
# ============================================================

@router.get(
    "",
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
# 查询自己的一个 Todo
# ============================================================

@router.get(
    "/{todo_id}",
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
# 修改 Todo
# ============================================================

@router.put(
    "/{todo_id}",
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
# 删除 Todo
# ============================================================

@router.delete(
    "/{todo_id}",
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