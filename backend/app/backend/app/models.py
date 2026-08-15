from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

task_tags_association = Table(
    'task_tags',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

user_allowed_teams = Table(
    'user_allowed_teams',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=True) # Tên tài khoản đăng nhập (VD: admin, namle...)
    full_name = Column(String(100), nullable=False)
    position = Column(String(100), default="Chuyên viên") # Chức vụ / Vị trí chuyên môn (Content, Design, Ads...)
    email = Column(String(100), nullable=True) # Tuỳ chọn
    password_hash = Column(String(255), nullable=True) # SHA-256 salted hash
    role = Column(String(50), default="member") # admin, manager, member, guest
    department = Column(String(100), default="Team 1")
    avatar_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    assigned_tasks = relationship("Task", foreign_keys="Task.direct_assignee_id", back_populates="assignee")
    created_tasks = relationship("Task", foreign_keys="Task.creator_id", back_populates="creator")
    comments = relationship("Comment", back_populates="user")
    allowed_teams = relationship("Tag", secondary=user_allowed_teams, back_populates="allowed_users")

class TagGroup(Base):
    __tablename__ = 'tag_groups'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) # "Đội ngũ (Team)", "Dịch vụ (Service)", "Tính chất"
    code = Column(String(50), unique=True, nullable=False) # "team", "service", "priority"
    color = Column(String(50), default="#3b82f6")
    created_at = Column(DateTime, default=datetime.utcnow)

    tags = relationship("Tag", back_populates="group", cascade="all, delete-orphan")

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('tag_groups.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False) # "Team 1", "Team 2", "Ads Facebook", "Content"
    color = Column(String(50), default="#2563eb") # text color
    bg_color = Column(String(50), default="#dbeafe") # background badge color
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("TagGroup", back_populates="tags")
    tasks = relationship("Task", secondary=task_tags_association, back_populates="tags")
    allowed_users = relationship("User", secondary=user_allowed_teams, back_populates="allowed_teams")

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(50), default="#4f46e5")
    status = Column(String(50), default="active") # active, completed, archived
    created_at = Column(DateTime, default=datetime.utcnow)

    stages = relationship("Stage", back_populates="project", cascade="all, delete-orphan", order_by="Stage.order_index")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Stage(Base):
    __tablename__ = 'stages'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False) # "To Do", "In Progress", "Review", "Done"
    order_index = Column(Integer, default=0)
    color = Column(String(50), default="#64748b")
    is_done_stage = Column(Boolean, default=False)

    project = relationship("Project", back_populates="stages")
    tasks = relationship("Task", back_populates="stage", cascade="all, delete-orphan", order_by="Task.order_index")

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    stage_id = Column(Integer, ForeignKey('stages.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(50), default="medium") # urgent, high, medium, low
    status = Column(String(50), default="TODO") # TODO, IN_PROGRESS, REVIEW, DONE, CANCELLED
    order_index = Column(Integer, default=0)
    
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, default=0.0)
    progress = Column(Integer, default=0) # 0 to 100%

    creator_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    direct_assignee_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    stage = relationship("Stage", back_populates="tasks")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[direct_assignee_id], back_populates="assigned_tasks")
    
    tags = relationship("Tag", secondary=task_tags_association, back_populates="tasks")
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan", order_by="Subtask.order_index")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan", order_by="Comment.created_at.desc()")
    activities = relationship("TaskActivity", back_populates="task", cascade="all, delete-orphan", order_by="TaskActivity.created_at.desc()")

class Subtask(Base):
    __tablename__ = 'subtasks'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    is_completed = Column(Boolean, default=False)
    status = Column(String(50), default="TODO") # TODO, IN_PROGRESS, DONE
    assignee_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    deliverable_link = Column(Text, nullable=True) # Link ảnh, link bài viết, Google Drive, Figma...
    deliverable_note = Column(Text, nullable=True) # Nội dung content hoặc ghi chú nghiệm thu
    due_date = Column(DateTime, nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="subtasks")
    assignee = relationship("User", foreign_keys=[assignee_id])

class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="comments")
    user = relationship("User", back_populates="comments")

class TaskActivity(Base):
    __tablename__ = 'task_activities'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = Column(String(100), nullable=False) # "created", "changed_status", "assigned", "commented"
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="activities")
