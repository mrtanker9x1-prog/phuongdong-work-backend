import hashlib
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from .database import get_db, engine, Base
from .models import User, TagGroup, Tag, Project, Stage, Task, Subtask, Comment, TaskActivity
from .schemas import (
    UserOut, UserBase, UserCreate, UserUpdate, UserPermissionsUpdate, ChangePasswordRequest, ChangeMyPasswordRequest,
    LoginRequest, AuthResponse,
    TagGroupOut, TagGroupCreate,
    TagOut, TagCreate, TagBase,
    ProjectOut, ProjectCreate,
    StageOut, StageCreate, StageBase,
    TaskOut, TaskCreate, TaskUpdate, TaskHandoverRequest,
    SubtaskOut, SubtaskCreate, SubtaskUpdate,
    CommentOut, CommentCreate
)
from .seed import seed_database

# Khởi tạo bảng và nạp dữ liệu mẫu
Base.metadata.create_all(bind=engine)
try:
    seed_database()
except Exception as e:
    pass

app = FastAPI(title="Phương Đông Work API", version="1.0.0")

# CORS cho phép Frontend Next.js kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def hash_password(password: str) -> str:
    salt = "phuongdong_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

@app.get("/")
def read_root():
    return {"message": "Phương Đông Work API is running", "status": "online"}

# ----------------- AUTHENTICATION API -----------------
@app.post("/api/auth/login", response_model=AuthResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    u_clean = login_data.username.strip().lower()
    user = db.query(User).filter(
        (User.username == u_clean) | (User.email == u_clean)
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Tên tài khoản hoặc mật khẩu không chính xác")
        
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Tài khoản này đã bị khóa")
        
    if user.password_hash and not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Tên tài khoản hoặc mật khẩu không chính xác")
        
    token = f"pd_token_{user.id}_{int(datetime.utcnow().timestamp())}"
    return AuthResponse(access_token=token, token_type="bearer", user=user)

@app.post("/api/auth/register", response_model=AuthResponse)
def register(reg_data: UserCreate, db: Session = Depends(get_db)):
    u_clean = reg_data.username.strip().lower()
    existing = db.query(User).filter(
        (User.username == u_clean) | 
        ((User.email == u_clean) if u_clean else False)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên tài khoản này đã được sử dụng")
        
    pwd_hash = hash_password(reg_data.password)
    user = User(
        username=u_clean,
        full_name=reg_data.full_name.strip(),
        position=reg_data.position or "Chuyên viên",
        email=reg_data.email or f"{u_clean}@phuongdong.local",
        password_hash=pwd_hash,
        role=reg_data.role or "member",
        department=reg_data.department or "Team 1",
        avatar_url=reg_data.avatar_url or f"https://api.dicebear.com/7.x/avataaars/svg?seed={reg_data.full_name}"
    )
    
    if reg_data.team_ids:
        teams = db.query(Tag).filter(Tag.id.in_(reg_data.team_ids)).all()
        user.allowed_teams = teams
    elif reg_data.department:
        matching_team = db.query(Tag).filter(Tag.name == reg_data.department).first()
        if matching_team:
            user.allowed_teams = [matching_team]
            
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = f"pd_token_{user.id}_{int(datetime.utcnow().timestamp())}"
    return AuthResponse(access_token=token, token_type="bearer", user=user)

@app.put("/api/auth/change-my-password")
def change_my_password(data: ChangeMyPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
        
    if data.current_password and user.password_hash:
        if not verify_password(data.current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không chính xác")
            
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Đổi mật khẩu thành công!"}

@app.get("/api/auth/me", response_model=UserOut)
def get_me(user_id: int = Query(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin tài khoản")
    return user

# ----------------- USERS API -----------------
@app.get("/api/users", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()

@app.post("/api/users", response_model=UserOut)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    u_clean = user_in.username.strip().lower()
    existing = db.query(User).filter(User.username == u_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên tài khoản này đã tồn tại")
        
    pwd_hash = hash_password(user_in.password if user_in.password else "123456")
    user = User(
        username=u_clean,
        full_name=user_in.full_name.strip(),
        position=user_in.position or "Chuyên viên",
        email=user_in.email or f"{u_clean}@phuongdong.local",
        password_hash=pwd_hash,
        role=user_in.role or "member",
        department=user_in.department or "Team 1",
        avatar_url=user_in.avatar_url or f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_in.full_name}"
    )
    if user_in.team_ids:
        teams = db.query(Tag).filter(Tag.id.in_(user_in.team_ids)).all()
        user.allowed_teams = teams
        
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.put("/api/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = user_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

@app.put("/api/users/{user_id}/permissions", response_model=UserOut)
def update_user_permissions(user_id: int, perm_in: UserPermissionsUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if perm_in.role:
        user.role = perm_in.role
    if perm_in.department:
        user.department = perm_in.department
        
    if perm_in.allowed_team_ids is not None:
        teams = db.query(Tag).filter(Tag.id.in_(perm_in.allowed_team_ids)).all()
        user.allowed_teams = teams
        
    db.commit()
    db.refresh(user)
    return user

@app.put("/api/users/{user_id}/password")
def change_user_password(user_id: int, pwd_in: ChangePasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(pwd_in.password)
    db.commit()
    return {"message": "Mật khẩu đã được cập nhật thành công"}

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# ----------------- TAG GROUPS & TAGS API -----------------
@app.get("/api/tag-groups", response_model=List[TagGroupOut])
def get_tag_groups(db: Session = Depends(get_db)):
    return db.query(TagGroup).order_by(TagGroup.id).all()

@app.post("/api/tag-groups", response_model=TagGroupOut)
def create_tag_group(group_in: TagGroupCreate, db: Session = Depends(get_db)):
    group = TagGroup(**group_in.dict())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group

@app.get("/api/tags", response_model=List[TagOut])
def get_tags(group_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Tag)
    if group_id:
        query = query.filter(Tag.group_id == group_id)
    return query.order_by(Tag.id).all()

@app.post("/api/tags", response_model=TagOut)
def create_tag(tag_in: TagCreate, db: Session = Depends(get_db)):
    tag = Tag(**tag_in.dict())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@app.put("/api/tags/{tag_id}", response_model=TagOut)
def update_tag(tag_id: int, tag_in: TagBase, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    tag.name = tag_in.name
    if tag_in.color:
        tag.color = tag_in.color
    if tag_in.bg_color:
        tag.bg_color = tag_in.bg_color
    db.commit()
    db.refresh(tag)
    return tag

@app.delete("/api/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()
    return {"message": "Tag deleted successfully"}

# ----------------- PROJECTS & STAGES API -----------------
@app.get("/api/projects", response_model=List[ProjectOut])
def get_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.id).all()

@app.post("/api/projects", response_model=ProjectOut)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**project_in.dict())
    db.add(project)
    db.commit()
    db.refresh(project)
    
    default_stages = [
        {"name": "Cần làm (To Do)", "order_index": 1, "color": "#64748b", "is_done_stage": False},
        {"name": "Đang thực hiện (In Progress)", "order_index": 2, "color": "#2563eb", "is_done_stage": False},
        {"name": "Chờ duyệt (Review)", "order_index": 3, "color": "#d97706", "is_done_stage": False},
        {"name": "Đã hoàn thành (Done)", "order_index": 4, "color": "#16a34a", "is_done_stage": True}
    ]
    for s in default_stages:
        stage = Stage(project_id=project.id, **s)
        db.add(stage)
    db.commit()
    db.refresh(project)
    return project

@app.get("/api/stages", response_model=List[StageOut])
def get_stages(project_id: int, db: Session = Depends(get_db)):
    return db.query(Stage).filter(Stage.project_id == project_id).order_by(Stage.order_index).all()

# ----------------- TASKS API -----------------
@app.get("/api/tasks", response_model=List[TaskOut])
def get_tasks(
    project_id: Optional[int] = None,
    stage_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    team_tag_id: Optional[int] = None,
    service_tag_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    
    if user_id:
        req_user = db.query(User).filter(User.id == user_id).first()
        if req_user and req_user.role != "admin":
            allowed_team_ids = [t.id for t in req_user.allowed_teams]
            if allowed_team_ids:
                query = query.filter(
                    Task.tags.any(Tag.id.in_(allowed_team_ids)) |
                    (Task.direct_assignee_id == user_id) |
                    (Task.creator_id == user_id)
                )
            else:
                query = query.filter(
                    (Task.direct_assignee_id == user_id) |
                    (Task.creator_id == user_id)
                )
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if stage_id:
        query = query.filter(Task.stage_id == stage_id)
    if assignee_id:
        query = query.filter(Task.direct_assignee_id == assignee_id)
    if priority:
        query = query.filter(Task.priority == priority.lower())
    if status:
        query = query.filter(Task.status == status.upper())
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%") | Task.description.ilike(f"%{search}%"))
        
    if tag_id:
        query = query.filter(Task.tags.any(Tag.id == tag_id))
    if team_tag_id:
        query = query.filter(Task.tags.any(Tag.id == team_tag_id))
    if service_tag_id:
        query = query.filter(Task.tags.any(Tag.id == service_tag_id))

    return query.order_by(Task.id.desc()).all()

@app.get("/api/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/api/tasks", response_model=TaskOut)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    tag_ids = task_in.tag_ids
    subtasks_data = getattr(task_in, 'subtasks', []) or []
    task_dict = task_in.dict(exclude={"tag_ids", "subtasks"})
    
    task = Task(**task_dict)
    
    if tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        task.tags = tags
        
    db.add(task)
    db.commit()
    db.refresh(task)

    if subtasks_data:
        for idx, sub_item in enumerate(subtasks_data):
            if isinstance(sub_item, str):
                if sub_item.strip():
                    db.add(Subtask(task_id=task.id, title=sub_item.strip(), order_index=idx + 1))
            elif isinstance(sub_item, dict):
                title = sub_item.get("title", "").strip()
                if title:
                    db.add(Subtask(
                        task_id=task.id,
                        title=title,
                        assignee_id=sub_item.get("assignee_id"),
                        deliverable_link=sub_item.get("deliverable_link"),
                        deliverable_note=sub_item.get("deliverable_note"),
                        status=sub_item.get("status", "TODO"),
                        order_index=idx + 1
                    ))
        db.commit()
        db.refresh(task)

    act = TaskActivity(
        task_id=task.id,
        user_id=task.creator_id,
        action="created",
        detail=f"Đã tạo công việc: {task.title}"
    )
    db.add(act)
    db.commit()
    db.refresh(task)
    
    return task

@app.put("/api/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task_in: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_in.dict(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)
    
    if "stage_id" in update_data and update_data["stage_id"] != task.stage_id:
        old_stage = task.stage.name if task.stage else "Unknown"
        new_stage_obj = db.query(Stage).filter(Stage.id == update_data["stage_id"]).first()
        new_stage_name = new_stage_obj.name if new_stage_obj else "Unknown"
        
        act = TaskActivity(
            task_id=task.id,
            action="changed_status",
            detail=f"Chuyển giai đoạn từ '{old_stage}' sang '{new_stage_name}'"
        )
        db.add(act)
        
        if new_stage_obj and new_stage_obj.is_done_stage:
            task.status = "DONE"
            task.progress = 100
        else:
            task.status = "IN_PROGRESS"

    for key, value in update_data.items():
        setattr(task, key, value)
        
    if tag_ids is not None:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        task.tags = tags

    db.commit()
    db.refresh(task)
    return task

@app.post("/api/tasks/{task_id}/move", response_model=TaskOut)
def move_task(task_id: int, stage_id: int = Query(...), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
        
    task.stage_id = stage_id
    if stage.is_done_stage:
        task.status = "DONE"
        task.progress = 100
    else:
        task.status = "IN_PROGRESS"
        
    db.commit()
    db.refresh(task)
    return task

@app.post("/api/tasks/{task_id}/handover", response_model=TaskOut)
def handover_task(task_id: int, handover_data: TaskHandoverRequest, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy công việc")

    sender = db.query(User).filter(User.id == handover_data.sender_id).first() if handover_data.sender_id else None
    next_user = db.query(User).filter(User.id == handover_data.next_assignee_id).first()
    if not next_user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người nhận bàn giao")

    # 1. Update Assignee
    task.direct_assignee_id = next_user.id

    # 2. If stage is specified
    if handover_data.next_stage_id:
        next_stage = db.query(Stage).filter(Stage.id == handover_data.next_stage_id).first()
        if next_stage:
            task.stage_id = next_stage.id
            if next_stage.is_done_stage:
                task.status = "DONE"
                task.progress = 100
            else:
                task.status = "IN_PROGRESS"

    # 3. If service tag changed (e.g. Content -> Design -> Ads)
    if handover_data.next_service_tag_id:
        service_tag = db.query(Tag).filter(Tag.id == handover_data.next_service_tag_id).first()
        if service_tag:
            team_tags = [t for t in task.tags if t.group and t.group.code == 'team']
            other_tags = [t for t in task.tags if t.group and t.group.code not in ['team', 'service']]
            task.tags = team_tags + [service_tag] + other_tags

    sender_info = f"{sender.full_name} ({sender.position or 'Chuyên viên'})" if sender else "Thành viên"
    receiver_info = f"{next_user.full_name} ({next_user.position or 'Chuyên viên'})"
    note_text = f': "{handover_data.handover_note.strip()}"' if handover_data.handover_note and handover_data.handover_note.strip() else ""

    detail_text = f"🔄 Bàn giao việc: {sender_info} ➔ {receiver_info}{note_text}"

    # Add Activity History Log
    act = TaskActivity(
        task_id=task.id,
        user_id=handover_data.sender_id,
        action="handover",
        detail=detail_text
    )
    db.add(act)

    # Add Comment
    comm = Comment(
        task_id=task.id,
        user_id=handover_data.sender_id,
        content=detail_text
    )
    db.add(comm)

    db.commit()
    db.refresh(task)
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}

# ----------------- SUBTASKS & COMMENTS API -----------------
@app.post("/api/subtasks", response_model=SubtaskOut)
def create_subtask(sub_in: SubtaskCreate, db: Session = Depends(get_db)):
    sub = Subtask(**sub_in.dict())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

@app.post("/api/subtasks/{subtask_id}", response_model=SubtaskOut)
@app.put("/api/subtasks/{subtask_id}", response_model=SubtaskOut)
@app.patch("/api/subtasks/{subtask_id}", response_model=SubtaskOut)
def update_subtask(subtask_id: int, sub_in: SubtaskUpdate, db: Session = Depends(get_db)):
    sub = db.query(Subtask).filter(Subtask.id == subtask_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subtask not found")
    
    update_data = sub_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sub, field, value)
        
    if "is_completed" in update_data:
        sub.status = "DONE" if sub.is_completed else "TODO"
    elif "status" in update_data:
        sub.is_completed = (sub.status == "DONE")
        
    db.commit()
    db.refresh(sub)
    return sub

@app.post("/api/subtasks/{subtask_id}/toggle", response_model=SubtaskOut)
@app.put("/api/subtasks/{subtask_id}/toggle", response_model=SubtaskOut)
def toggle_subtask(subtask_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subtask).filter(Subtask.id == subtask_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subtask not found")
    sub.is_completed = not sub.is_completed
    sub.status = "DONE" if sub.is_completed else "TODO"
    db.commit()
    db.refresh(sub)
    return sub

@app.delete("/api/subtasks/{subtask_id}")
def delete_subtask(subtask_id: int, db: Session = Depends(get_db)):
    sub = db.query(Subtask).filter(Subtask.id == subtask_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subtask not found")
    db.delete(sub)
    db.commit()
    return {"message": "Subtask deleted successfully"}

@app.post("/api/comments", response_model=CommentOut)
def create_comment(comm_in: CommentCreate, db: Session = Depends(get_db)):
    comm = Comment(**comm_in.dict())
    db.add(comm)
    db.commit()
    db.refresh(comm)
    return comm

# ----------------- STATS / DASHBOARD & KPI API -----------------
def get_date_range_for_period(period: str):
    now = datetime.utcnow()
    if period == "today":
        start = datetime(now.year, now.month, now.day, 0, 0, 0)
        end = datetime(now.year, now.month, now.day, 23, 59, 59)
        return start, end
    elif period == "this_week":
        start = now - timedelta(days=now.weekday())
        start = datetime(start.year, start.month, start.day, 0, 0, 0)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        return start, end
    elif period == "last_week":
        start = now - timedelta(days=now.weekday() + 7)
        start = datetime(start.year, start.month, start.day, 0, 0, 0)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        return start, end
    elif period == "this_month":
        start = datetime(now.year, now.month, 1, 0, 0, 0)
        if now.month == 12:
            end = datetime(now.year, 12, 31, 23, 59, 59)
        else:
            next_month = datetime(now.year, now.month + 1, 1, 0, 0, 0)
            end = next_month - timedelta(seconds=1)
        return start, end
    elif period == "last_month":
        if now.month == 1:
            start = datetime(now.year - 1, 12, 1, 0, 0, 0)
            end = datetime(now.year - 1, 12, 31, 23, 59, 59)
        else:
            start = datetime(now.year, now.month - 1, 1, 0, 0, 0)
            next_month = datetime(now.year, now.month, 1, 0, 0, 0)
            end = next_month - timedelta(seconds=1)
        return start, end
    return None, None

@app.get("/api/stats/overview")
def get_stats_overview(
    project_id: Optional[int] = None,
    user_id: Optional[int] = None,
    period: Optional[str] = "all",
    db: Session = Depends(get_db)
):
    task_query = db.query(Task)
    if project_id:
        task_query = task_query.filter(Task.project_id == project_id)
        
    if user_id:
        req_user = db.query(User).filter(User.id == user_id).first()
        if req_user and req_user.role != "admin":
            allowed_team_ids = [t.id for t in req_user.allowed_teams]
            if allowed_team_ids:
                task_query = task_query.filter(
                    Task.tags.any(Tag.id.in_(allowed_team_ids)) |
                    (Task.direct_assignee_id == user_id) |
                    (Task.creator_id == user_id)
                )
            else:
                task_query = task_query.filter(
                    (Task.direct_assignee_id == user_id) |
                    (Task.creator_id == user_id)
                )
    
    # Filter by period if specified
    start_dt, end_dt = get_date_range_for_period(period)
    if start_dt and end_dt:
        # Match tasks created, updated or due in this period
        task_query = task_query.filter(
            (Task.created_at >= start_dt) & (Task.created_at <= end_dt) |
            (Task.due_date >= start_dt) & (Task.due_date <= end_dt) |
            (Task.start_date >= start_dt) & (Task.start_date <= end_dt)
        )
        
    tasks = task_query.all()
    total_tasks = len(tasks)
    done_tasks = len([t for t in tasks if t.status == "DONE"])
    in_progress = len([t for t in tasks if t.status == "IN_PROGRESS"])
    todo = len([t for t in tasks if t.status == "TODO"])
    review = len([t for t in tasks if t.status == "REVIEW"])
    total_estimated_hours = sum([t.estimated_hours or 0 for t in tasks])
    
    now = datetime.utcnow()
    overdue = len([t for t in tasks if t.due_date and t.due_date < now and t.status != "DONE"])
    
    # Team stats
    team_group = db.query(TagGroup).filter(TagGroup.code == "team").first()
    team_stats = []
    if team_group:
        for tag in team_group.tags:
            count = len([t for t in tasks if any(tg.id == tag.id for tg in t.tags)])
            team_stats.append({
                "id": tag.id,
                "name": tag.name,
                "color": tag.color,
                "bg_color": tag.bg_color,
                "count": count
            })

    # Service stats
    service_group = db.query(TagGroup).filter(TagGroup.code == "service").first()
    service_stats = []
    if service_group:
        for tag in service_group.tags:
            count = len([t for t in tasks if any(tg.id == tag.id for tg in t.tags)])
            service_stats.append({
                "id": tag.id,
                "name": tag.name,
                "color": tag.color,
                "bg_color": tag.bg_color,
                "count": count
            })

    # Member KPI Breakdown
    all_users = db.query(User).order_by(User.id).all()
    member_kpis = []
    
    for u in all_users:
        # User is involved if they are direct assignee OR assigned to any subtask/step
        u_tasks = [
            t for t in tasks 
            if t.direct_assignee_id == u.id or any(st.assignee_id == u.id for st in t.subtasks)
        ]
        u_total = len(u_tasks)
        
        # Calculate done, in-progress, todo, overdue based on sequential workflow steps
        u_done = 0
        u_in_progress = 0
        u_todo = 0
        u_review = 0
        u_overdue = 0
        
        for t in u_tasks:
            # If task has subtasks/steps
            if t.subtasks:
                user_steps = [st for st in t.subtasks if st.assignee_id == u.id]
                if user_steps:
                    all_user_steps_done = all(st.status == "DONE" or st.is_completed for st in user_steps)
                    if all_user_steps_done:
                        u_done += 1
                    else:
                        # Find the first uncompleted step in the entire task
                        first_uncompleted_step = next(
                            (st for st in sorted(t.subtasks, key=lambda s: s.order_index or 0) if st.status != "DONE" and not st.is_completed),
                            None
                        )
                        
                        # Is this user responsible for the bottleneck step?
                        if first_uncompleted_step and first_uncompleted_step.assignee_id == u.id:
                            u_in_progress += 1
                            # If task deadline has passed, the bottleneck person gets the overdue blame
                            if t.due_date and t.due_date < now and t.status != "DONE":
                                u_overdue += 1
                        else:
                            # User is in subsequent step waiting for previous handover -> NOT overdue, counted as waiting/todo
                            u_todo += 1
                else:
                    # User is direct assignee of the whole task
                    if t.status == "DONE":
                        u_done += 1
                    elif t.status == "IN_PROGRESS":
                        u_in_progress += 1
                    else:
                        u_todo += 1
                    if t.due_date and t.due_date < now and t.status != "DONE":
                        u_overdue += 1
            else:
                # Standard task without subtasks
                if t.status == "DONE":
                    u_done += 1
                elif t.status == "IN_PROGRESS":
                    u_in_progress += 1
                elif t.status == "REVIEW":
                    u_review += 1
                else:
                    u_todo += 1
                if t.due_date and t.due_date < now and t.status != "DONE":
                    u_overdue += 1
                    
        u_hours = sum([t.estimated_hours or 0 for t in u_tasks])
        u_comp_rate = round((u_done / u_total * 100) if u_total > 0 else 0, 1)
        
        # Calculate KPI score out of 100
        if u_total == 0:
            kpi_score = 100.0
            kpi_grade = "Chưa có việc"
        else:
            penalty = (u_overdue / u_total) * 40.0
            base_score = (u_done / u_total) * 70.0 + (u_in_progress / u_total) * 20.0 + (u_review / u_total) * 25.0
            kpi_score = max(0.0, min(100.0, round(base_score + 30.0 - penalty, 1)))
            
            if kpi_score >= 90:
                kpi_grade = "Xuất Sắc 🏆"
            elif kpi_score >= 75:
                kpi_grade = "Tốt ⭐"
            elif kpi_score >= 60:
                kpi_grade = "Đạt Yêu Cầu ✓"
            else:
                kpi_grade = "Cần Cải Thiện ⚠️"

        # Upcoming tasks (Due in future)
        upcoming = [
            {
                "id": t.id,
                "title": t.title,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "priority": t.priority,
                "status": t.status,
                "tags": [{"name": tg.name, "color": tg.color, "bg_color": tg.bg_color} for tg in t.tags]
            }
            for t in sorted([t for t in u_tasks if t.status != "DONE"], key=lambda x: x.due_date or datetime.max)
        ]

        # Tasks summary list
        task_list_summary = [
            {
                "id": t.id,
                "title": t.title,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "priority": t.priority,
                "status": t.status,
                "progress": t.progress or 0,
                "estimated_hours": t.estimated_hours or 0,
                "tags": [{"name": tg.name, "color": tg.color, "bg_color": tg.bg_color} for tg in t.tags]
            }
            for t in u_tasks
        ]

        member_kpis.append({
            "user_id": u.id,
            "full_name": u.full_name,
            "username": u.username,
            "position": u.position or "Chuyên viên",
            "department": u.department or "Team 1",
            "role": u.role,
            "avatar_url": u.avatar_url,
            "total_tasks": u_total,
            "done_tasks": u_done,
            "in_progress_tasks": u_in_progress,
            "todo_tasks": u_todo,
            "review_tasks": u_review,
            "overdue_tasks": u_overdue,
            "total_estimated_hours": u_hours,
            "completion_rate": u_comp_rate,
            "kpi_score": kpi_score,
            "kpi_grade": kpi_grade,
            "upcoming_tasks": upcoming,
            "tasks_list": task_list_summary
        })

    return {
        "period": period,
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
        "in_progress": in_progress,
        "todo": todo,
        "review": review,
        "overdue": overdue,
        "total_estimated_hours": total_estimated_hours,
        "completion_rate": round((done_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1),
        "team_stats": team_stats,
        "service_stats": service_stats,
        "member_kpis": member_kpis
    }
