from pydantic import BaseModel


class UserSchema(BaseModel):
    username: str


class UserInSchema(UserSchema):
    password: str


class UserDBSchema(UserInSchema):
    role: str = "user"
    is_active: bool = True


class ChangePasswordScheme(BaseModel):
    old_password: str
    new_password: str
