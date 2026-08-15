from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ----------------- TAG SCHEMAS -----------------
class TagBase(BaseModel):
    name: str
    color: Optional[str] = "#2563eb"
    bg_color: Optional[str] = "#dbeafe"

class TagCreate(TagBase):
    group_id: int

class TagOut(TagBase):
    id: int
    group_id: int

    class Config:
        from_attributes = True

class TagGroupBase(BaseModel):
    name: str
    code: str
    color: Optional[str] = "#3b82f6"

class TagGroupCreate(TagGroupBase):
    pass

class TagGroupOut(TagGroupBase):
    id: int
    tags: List[TagOut] = []

    class Config:
        from_attributes = True

# ----------------- USER & AUTH SCHEMAS -----------------
class UserBase(BaseModel):
    username: Optional[str] = None
    full_name: str
    position: Optional[str] = "Chuyên viên"
    email: Optional[str] = None
    role: Optional[str] = "member" # admin, manager, member
    department: Optional[str] = "Team 1"
    avatar_url: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    full_name: str
    password: str
    position: Optional[str] = "Chuyên viên"
    email: Optional[str] = None
    role: Optional[str] = "member"
    department: Optional[str] = "Team 1"
    team_ids: Optional[List[int]] = []
    avatar_url: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None

class TaskHandoverRequest(BaseModel):
    task_id: int
    sender_id: Optional[int] = None
    next_assignee_id: int
    next_stage_id: Optional[int] = None
    next_service_tag_id: Optional[int] = None
    handover_note: Optional[str] = None

class UserPermissionsUpdate(BaseModel):
    role: Optional[str] = None
    department: Optional[str] = None
    allowed_team_ids: List[int] = []

class ChangePasswordRequest(BaseModel):
    password: str

class ChangeMyPasswordRequest(BaseModel):
    user_id: int
    current_password: Optional[str] = None
    new_password: str

class UserOut(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime
    allowed_teams: List[TagOut] = []

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# ----------------- STAGE SCHEMAS -----------------
class StageBase(BaseModel):
    name: str
    order_index: int = 0
    color: Optional[str] = "#64748b"
    is_done_stage: bool = False

class StageCreate(StageBase):
    project_id: int

class StageOut(StageBase):
    id: int
    project_id: int

    class Config:
        from_attributes = True

# ----------------- PROJECT SCHEMAS -----------------
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#4f46e5"
    status: Optional[str] = "active"

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int
    stages: List[StageOut] = []
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- SUBTASK SCHEMAS -----------------
class SubtaskBase(BaseModel):
    title: str
    is_completed: Optional[bool] = False
    order_index: Optional[int] = 0

class SubtaskCreate(SubtaskBase):
    task_id: int

class SubtaskOut(SubtaskBase):
    id: int
    task_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- COMMENT SCHEMAS -----------------
class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    task_id: int
    user_id: Optional[int] = None

class CommentOut(CommentBase):
    id: int
    task_id: int
    user_id: Optional[int] = None
    user: Optional[UserOut] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- TASK ACTIVITY SCHEMAS -----------------
class TaskActivityOut(BaseModel):
    id: int
    task_id: int
    user_id: Optional[int] = None
    action: str
    detail: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- TASK SCHEMAS -----------------
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "TODO"
    order_index: Optional[int] = 0
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = 0.0
    progress: Optional[int] = 0
    direct_assignee_id: Optional[int] = None

class TaskCreate(TaskBase):
    project_id: int
    stage_id: int
    creator_id: Optional[int] = None
    tag_ids: Optional[List[int]] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    stage_id: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    order_index: Optional[int] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    progress: Optional[int] = None
    direct_assignee_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None

class TaskOut(TaskBase):
    id: int
    project_id: int
    stage_id: int
    creator_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    creator: Optional[UserOut] = None
    assignee: Optional[UserOut] = None
    tags: List[TagOut] = []
    subtasks: List[SubtaskOut] = []
    comments: List[CommentOut] = []
    activities: List[TaskActivityOut] = []

    class Config:
        from_attributes = True
