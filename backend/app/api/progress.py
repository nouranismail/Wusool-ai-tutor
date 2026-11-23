"""
GET  /api/progress
POST /api/progress/activities
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_child, get_db
from backend.app.db.models.child import Child
from backend.app.db.models.progress import Activity, Badge, Progress
from backend.app.schemas.progress import ProgressResponse, RecordActivityRequest

router = APIRouter()


@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    prog = db.query(Progress).filter(Progress.child_id == child.id).first()
    activities = [
        a.activity_id
        for a in db.query(Activity).filter(Activity.child_id == child.id).all()
    ]
    badges = [
        b.badge_key
        for b in db.query(Badge).filter(Badge.child_id == child.id).all()
    ]

    if not prog:
        return ProgressResponse(
            activities=activities, lessons=0, exercises=0, hours=0.0, streak=0, badges=badges
        )

    return ProgressResponse(
        activities=activities,
        lessons=prog.lessons_count,
        exercises=prog.exercises_count,
        hours=round(prog.hours, 2),
        streak=prog.streak,
        badges=badges,
    )


@router.post("/progress/activities", status_code=204)
def record_activity(
    body: RecordActivityRequest,
    child: Child = Depends(get_current_child),
    db: Session = Depends(get_db),
):
    db.add(Activity(child_id=child.id, activity_id=body.activityId))

    prog = db.query(Progress).filter(Progress.child_id == child.id).first()
    if prog:
        if ":explain" in body.activityId:
            prog.lessons_count += 1
        elif ":exercises" in body.activityId:
            prog.exercises_count += 1
        prog.hours += 0.1  # approximate per-activity time increment
    db.commit()
    return Response(status_code=204)
