"""
ORM models package.

Import all models here so SQLAlchemy's metadata is fully populated
before Base.metadata.create_all() is called in main.py.
"""
from backend.app.db.models.parent import Parent             # noqa: F401
from backend.app.db.models.child import Child               # noqa: F401
from backend.app.db.models.lesson import Lesson, Question, QuestionOption  # noqa: F401
from backend.app.db.models.progress import Progress, Activity, Badge       # noqa: F401
from backend.app.db.models.conversation import Conversation, Message       # noqa: F401
from backend.app.db.models.friend import FriendRequest, Friendship         # noqa: F401
from backend.app.db.models.english_session import EnglishSession, SessionParticipant  # noqa: F401
from backend.app.db.models.document import RAGDocument      # noqa: F401
