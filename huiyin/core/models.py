"""
Huiyin - Core Data Models
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict


class Role(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


class TaskStatus(str, Enum):
    PENDING = "pending"
    TRIGGERED = "triggered"
    REPLIED = "replied"
    CANCELLED = "cancelled"
    CONVERTED = "converted"


class GenerationMode(str, Enum):
    PRE_GENERATED = "pre_generated"
    DEFERRED = "deferred"


@dataclass
class Message:
    role: Role
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SplitMessage:
    messages: List[str]
    delays: List[float]


@dataclass
class FutureTask:
    trigger_time: datetime
    generation_mode: GenerationMode
    task_id: Optional[str] = None
    content: Optional[SplitMessage] = None
    reason: str = ""
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    hidden_context: Optional[str] = None
    force_break_bounds: bool = False
    break_reason: str = ""


@dataclass
class DualTrackResponse:
    reply: str
    delay_seconds: float = 1.5
    is_split: bool = False
    split_messages: Optional[List[str]] = None
    split_delays: Optional[List[float]] = None
    future_task: Optional[FutureTask] = None


@dataclass
class UserProfile:
    tags: Dict[str, Any] = field(default_factory=dict)
    abstract_impression: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
