from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    subject: str = Field(..., description="Тема для раскраски", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "капибара"
            }
        }


class PrintRequest(BaseModel):
    subject: str = Field(..., description="Тема для раскраски", min_length=1)
    enhance: bool = Field(True, description="Улучшить изображение для раскраски")

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "динозавр",
                "enhance": True
            }
        }


class GenerateResponse(BaseModel):
    status: str
    subject: str
    original_file: str
    enhanced_file: Optional[str] = None
    openai_url: str


class PrintResponse(BaseModel):
    status: str
    subject: str
    file: str
    print_message: str


class HealthResponse(BaseModel):
    status: str
    message: str
    openai_configured: bool
    printing_enabled: bool


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str


# Модели для Алисы
class AliceRequest(BaseModel):
    version: str
    session: dict
    request: dict


class AliceResponse(BaseModel):
    version: str
    session: dict
    response: dict