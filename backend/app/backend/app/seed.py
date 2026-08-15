import hashlib
from datetime import datetime, timedelta
from .database import SessionLocal, engine, Base
from .models import User, TagGroup, Tag, Project, Stage, Task, Subtask, Comment, TaskActivity

def hash_password(password: str) -> str:
    salt = "phuongdong_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Kiểm tra nếu đã có tài khoản
    existing_admin = db.query(User).filter(User.username == "admin").first()
    if existing_admin:
        db.close()
        return

    # 1. Khởi tạo Nhóm Tag & Danh sách Tag (Đội nhóm & Dịch vụ)
    group_team = db.query(TagGroup).filter(TagGroup.code == "team").first()
    if not group_team:
        group_team = TagGroup(name="Đội nhóm (Team)", code="team", color="#2563eb")
        db.add(group_team)
        db.commit()

    group_service = db.query(TagGroup).filter(TagGroup.code == "service").first()
    if not group_service:
        group_service = TagGroup(name="Loại dịch vụ (Service)", code="service", color="#059669")
        db.add(group_service)
        db.commit()

    group_priority = db.query(TagGroup).filter(TagGroup.code == "priority").first()
    if not group_priority:
        group_priority = TagGroup(name="Mức độ ưu tiên", code="priority", color="#dc2626")
        db.add(group_priority)
        db.commit()

    team_tags_data = [
        {"name": "Team 1", "color": "#1d4ed8", "bg_color": "#dbeafe"},
        {"name": "Team 2", "color": "#7c3aed", "bg_color": "#ede9fe"},
        {"name": "Team 3", "color": "#c026d3", "bg_color": "#fae8ff"},
        {"name": "Team 4", "color": "#db2777", "bg_color": "#fce7f3"},
        {"name": "Team 5", "color": "#ea580c", "bg_color": "#ffedd5"},
        {"name": "Team 6", "color": "#d97706", "bg_color": "#fef3c7"},
        {"name": "Team 7", "color": "#0d9488", "bg_color": "#ccfbf1"}
    ]
    team_tags = []
    for t in team_tags_data:
        tag = db.query(Tag).filter(Tag.name == t["name"]).first()
        if not tag:
            tag = Tag(group_id=group_team.id, **t)
            db.add(tag)
            db.commit()
        team_tags.append(tag)

    service_tags_data = [
        {"name": "Khám Chữa Bệnh & Dịch Vụ Y Tế", "color": "#15803d", "bg_color": "#dcfce7"},
        {"name": "Truyền Thông & Quảng Cáo Bệnh Viện", "color": "#047857", "bg_color": "#d1fae5"},
        {"name": "Thiết Kế Banner & POSM", "color": "#0e7490", "bg_color": "#cffafe"},
        {"name": "Bài Viết Y Khoa & Content", "color": "#4338ca", "bg_color": "#e0e7ff"},
        {"name": "SEO & Báo Chí PR", "color": "#6d28d9", "bg_color": "#ede9fe"},
        {"name": "Hệ Thống Web & App Đặt Lịch", "color": "#9333ea", "bg_color": "#f3e8ff"},
        {"name": "CSKH & Hotline Tư Vấn", "color": "#b91c1c", "bg_color": "#fee2e2"}
    ]
    service_tags = []
    for s in service_tags_data:
        tag = db.query(Tag).filter(Tag.name == s["name"]).first()
        if not tag:
            tag = Tag(group_id=group_service.id, **s)
            db.add(tag)
            db.commit()
        service_tags.append(tag)

    default_pwd_hash = hash_password("123456")

    # 2. Khởi tạo Thành viên / Users Phương Đông (Không bắt buộc email)
    # Admin (username: admin / pass: 123456)
    admin_user = User(
        username="admin",
        full_name="Quản Trị Viên (Admin)",
        position="Quản Trị Viên / Ban Giám Đốc",
        email="admin@phuongdong.vn",
        password_hash=default_pwd_hash,
        role="admin",
        department="Ban Giám Đốc",
        avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=AdminPhuongDong"
    )
    admin_user.allowed_teams = team_tags
    db.add(admin_user)

    # Quản lý Team 1, Team 2, Team 3 (username: namle / pass: 123456)
    manager_123 = User(
        username="namle",
        full_name="Lê Hoàng Nam",
        position="Trưởng Nhóm Marketing (Leader)",
        email="nam.le@phuongdong.vn",
        password_hash=default_pwd_hash,
        role="manager",
        department="Team 1",
        avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=LeaderNam"
    )
    manager_123.allowed_teams = [team_tags[0], team_tags[1], team_tags[2]]
    db.add(manager_123)

    # Quản lý Team 4, Team 5 (username: linhtran / pass: 123456)
    manager_45 = User(
        username="linhtran",
        full_name="Trần Thùy Linh",
        position="Trưởng Nhóm Truyền Thông (Leader)",
        email="linh.tran@phuongdong.vn",
        password_hash=default_pwd_hash,
        role="manager",
        department="Team 4",
        avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=LeaderLinh"
    )
    manager_45.allowed_teams = [team_tags[3], team_tags[4]]
    db.add(manager_45)

    # Nhân viên Team 1 (username: hungpham / pass: 123456)
    staff_team1 = User(
        username="hungpham",
        full_name="Phạm Hùng",
        position="Chuyên Viên Viết Content (Content Creator)",
        email="hung.pham@phuongdong.vn",
        password_hash=default_pwd_hash,
        role="member",
        department="Team 1",
        avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=HungPham"
    )
    staff_team1.allowed_teams = [team_tags[0]]
    db.add(staff_team1)

    # Nhân viên Team 2 (username: thaovu / pass: 123456)
    staff_team2 = User(
        username="thaovu",
        full_name="Vũ Phương Thảo",
        position="Chuyên Viên Thiết Kế (Graphic Designer)",
        email="thao.vu@phuongdong.vn",
        password_hash=default_pwd_hash,
        role="member",
        department="Team 2",
        avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=ThaoVu"
    )
    staff_team2.allowed_teams = [team_tags[1]]
    db.add(staff_team2)

    # Nhân viên Team 3 (username: duchoang / pass: 123456)
    staff_team3 = User(
        username="duchoang",
        full_name="Hoàng Minh Đức",
        position="Chuyên Viên Chạy Ads (Ads Specialist)",
        email="duc.hoang@phuongdong.vn",
        password_hash=default_pwd_hash,
        role="member",
        department="Team 3",
        avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=DucHoang"
    )
    staff_team3.allowed_teams = [team_tags[2]]
    db.add(staff_team3)

    db.commit()

    # 3. Khởi tạo Dự án Phương Đông
    proj1 = db.query(Project).first()
    if not proj1:
        proj1 = Project(
            name="Chiến Dịch Nâng Cao Sức Khỏe Cộng Đồng - BV Phương Đông",
            description="Quản lý toàn bộ công việc và phối hợp giữa các Team dịch vụ",
            color="#047857",
            status="active"
        )
        db.add(proj1)
        db.commit()

        stages_data = [
            {"name": "Cần làm (To Do)", "order_index": 1, "color": "#64748b", "is_done_stage": False},
            {"name": "Đang thực hiện (In Progress)", "order_index": 2, "color": "#2563eb", "is_done_stage": False},
            {"name": "Chờ duyệt (Review)", "order_index": 3, "color": "#d97706", "is_done_stage": False},
            {"name": "Đã hoàn thành (Done)", "order_index": 4, "color": "#16a34a", "is_done_stage": True},
        ]
        stages = []
        for s in stages_data:
            stage = Stage(project_id=proj1.id, **s)
            db.add(stage)
            stages.append(stage)
        db.commit()

        # 4. Khởi tạo Các Task Mẫu
        now = datetime.utcnow()

        t1 = Task(
            project_id=proj1.id,
            stage_id=stages[1].id,
            title="Triển khai gói khám sức khỏe tổng quát BV Phương Đông",
            description="Lên kế hoạch truyền thông và chạy quảng cáo gói khám tổng quát cho Team 1",
            priority="high",
            status="IN_PROGRESS",
            start_date=now - timedelta(days=2),
            due_date=now + timedelta(days=3),
            estimated_hours=16,
            progress=45,
            creator_id=admin_user.id,
            direct_assignee_id=staff_team1.id
        )
        t1.tags = [team_tags[0], service_tags[1]]
        db.add(t1)

        t2 = Task(
            project_id=proj1.id,
            stage_id=stages[1].id,
            title="Thiết kế bộ nhận diện và Poster chuyên khoa Sản - Nhi Phương Đông",
            description="Thiết kế poster, standee và bộ banner cho chuyên khoa Sản - Nhi",
            priority="urgent",
            status="IN_PROGRESS",
            start_date=now - timedelta(days=1),
            due_date=now + timedelta(days=2),
            estimated_hours=12,
            progress=60,
            creator_id=manager_123.id,
            direct_assignee_id=staff_team2.id
        )
        t2.tags = [team_tags[1], service_tags[2]]
        db.add(t2)

        t3 = Task(
            project_id=proj1.id,
            stage_id=stages[0].id,
            title="Biên soạn chuỗi 10 bài viết kiến thức y khoa chuyên sâu",
            description="Viết bài chuẩn y khoa về tim mạch và tiêu hóa đăng website BV Phương Đông",
            priority="medium",
            status="TODO",
            start_date=now,
            due_date=now + timedelta(days=5),
            estimated_hours=20,
            progress=10,
            creator_id=manager_123.id,
            direct_assignee_id=staff_team3.id
        )
        t3.tags = [team_tags[2], service_tags[3]]
        db.add(t3)

        db.commit()

        # Subtasks (Quy trình các khâu liên hoàn & Nghiệm thu kết quả)
        s1 = Subtask(
            task_id=t1.id,
            title="✍️ 1. Viết bài Content truyền thông & Khuyến mãi",
            assignee_id=staff_team1.id,
            status="DONE",
            is_completed=True,
            deliverable_link="https://docs.google.com/document/d/1Bao-Viet-Content-Kham-Tong-Quat",
            deliverable_note="Đã viết xong bài 800 từ, gửi kèm 3 mẫu tiêu đề A/B Testing.",
            order_index=1
        )
        s2 = Subtask(
            task_id=t1.id,
            title="🎨 2. Thiết kế 2 Banner vuông 1080x1080 & 1 Banner ngang 1200x628",
            assignee_id=staff_team2.id,
            status="IN_PROGRESS",
            is_completed=False,
            deliverable_link="https://drive.google.com/drive/folders/1Banner-Thiet-Ke-Phuong-Dong",
            deliverable_note="Đã lên xong layout phác thảo, đang render file chất lượng cao.",
            order_index=2
        )
        s3 = Subtask(
            task_id=t1.id,
            title="📊 3. Setup chiến dịch quảng cáo Facebook & Google Ads",
            assignee_id=staff_team3.id,
            status="TODO",
            is_completed=False,
            deliverable_link="",
            deliverable_note="Chờ Designer bàn giao file ảnh hoàn chỉnh để lên camp.",
            order_index=3
        )
        s4 = Subtask(
            task_id=t1.id,
            title="🎯 4. Theo dõi nghiệm thu số lead & Báo cáo CPL",
            assignee_id=manager_123.id,
            status="TODO",
            is_completed=False,
            deliverable_link="",
            deliverable_note="Đánh giá hiệu quả sau 3 ngày chạy.",
            order_index=4
        )
        db.add_all([s1, s2, s3, s4])

        # Comment
        c1 = Comment(task_id=t1.id, user_id=admin_user.id, content="Team 1 chú ý theo dõi sát chi phí quảng cáo và lượng đăng ký khám nhé!")
        db.add(c1)
        db.commit()

    db.close()
