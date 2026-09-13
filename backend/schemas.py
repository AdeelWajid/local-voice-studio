from pydantic import BaseModel, Field, field_validator
from typing import Literal

class GenerateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    voice_id: str
    language: Literal['EN', 'ZH', 'JA', 'ES', 'AR'] = 'EN'
    emotion_mode: Literal['speaker', 'vector', 'description', 'auto_text'] = 'vector'
    emotion_vector: list[float] = Field(default_factory=lambda: [0.0] * 8)
    emotion_alpha: float = Field(default=0.6, ge=0.0, le=1.0)
    duration_factor: float = Field(default=1.0, ge=0.5, le=2.0)
    emotion_text: str | None = Field(default=None, max_length=500)
    use_random: bool = False

    @field_validator('emotion_text')
    @classmethod
    def clean_emotion_text(cls, value):
        return value.strip() if value else value

    @field_validator('emotion_vector')
    @classmethod
    def vector_shape(cls, value):
        if len(value) != 8 or any(not 0 <= item <= 1 for item in value):
            raise ValueError('Emotion vector must contain exactly 8 values between 0 and 1.')
        return value

    @field_validator('text')
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError('Enter some text to generate speech.')
        return value
