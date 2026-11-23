from __future__ import annotations
from pydantic import BaseModel


class ProgressResponse(BaseModel):
    activities: list[str]
    lessons: int
    exercises: int
    hours: float
    streak: int
    badges: list[str]


class RecordActivityRequest(BaseModel):
    activityId: str
