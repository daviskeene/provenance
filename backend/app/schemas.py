from pydantic import BaseModel
from typing import List


class StartSessionResponse(BaseModel):
    session_id: int


class EventCreate(BaseModel):
    character: str


class FinalizeSessionResponse(BaseModel):
    success: bool


class VerifyResponse(BaseModel):
    verified: bool
    message: str
