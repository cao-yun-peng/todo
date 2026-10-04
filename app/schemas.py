from pydantic import BaseModel, Field


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