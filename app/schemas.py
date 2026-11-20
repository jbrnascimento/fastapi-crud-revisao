
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
    field_validator,
    EmailStr,
)

def validate_title_value(value: str) -> str:
    value = value.strip()

    if not value:
        raise ValueError("O título não pode conter apenas espaços")

    return value

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    done: bool = False

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value):
        if not isinstance(value, str):
            return value

        return validate_title_value(value)


class TaskPublic(TaskCreate):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)
    

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    done: bool | None = None

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value):
        if not isinstance(value, str):
            return value

        return validate_title_value(value)

    @model_validator(mode="after")
    def validate_fields(self):
        if not self.model_fields_set:
            raise ValueError("Informe pelo menos um campo para atualizar")
        
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title não pode ser null")

        if "done" in self.model_fields_set and self.done is None:
            raise ValueError("done não pode ser null")

        return self


def validate_name_value(value: str) -> str:
    value = value.strip()

    if not value:
        raise ValueError("O nome não pode conter apenas espaços")

    return value


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value):
        if not isinstance(value, str):
            return value

        return validate_name_value(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()

        return value


class UserPublic(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value):
        if not isinstance(value, str):
            return value

        return validate_name_value(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            return value.strip().lower()

        return value

    @model_validator(mode="after")
    def validate_fields(self):
        if not self.model_fields_set:
            raise ValueError("Informe pelo menos um campo para atualizar")

        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name não pode ser null")

        if "email" in self.model_fields_set and self.email is None:
            raise ValueError("email não pode ser null")

        return self

class RefreshToken(BaseModel):
    refresh_token: str = Field(min_length=1)    