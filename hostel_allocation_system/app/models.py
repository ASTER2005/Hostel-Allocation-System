"""SQLAlchemy models for Hostel Allocation and Management System.
Mirrors database/schema.sql and provides helper methods for live sheet APIs,
business logic validations, and dashboard analytics.
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("student", "warden", "admin", name="user_roles"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student = db.relationship("Student", backref="user", uselist=False, cascade="all, delete-orphan")
    warden = db.relationship("Warden", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class Hostel(db.Model):
    __tablename__ = "hostels"

    id = db.Column(db.Integer, primary_key=True)
    hostel_name = db.Column(db.String(100), unique=True, nullable=False)
    hostel_type = db.Column(db.Enum("Boys", "Girls", "Co-ed", name="hostel_types"), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    total_rooms = db.Column(db.Integer, default=0, nullable=False)
    description = db.Column(db.Text)

    rooms = db.relationship("Room", backref="hostel", cascade="all, delete-orphan", lazy="dynamic")
    wardens = db.relationship("Warden", backref="hostel", lazy="dynamic")
    complaints = db.relationship("Complaint", backref="hostel", lazy="dynamic")
    announcements = db.relationship("Announcement", backref="hostel", lazy="dynamic")

    @property
    def total_capacity(self):
        return sum(room.capacity for room in self.rooms)

    @property
    def total_occupied(self):
        return sum(room.occupied_count for room in self.rooms)

    @property
    def free_beds(self):
        return max(0, self.total_capacity - self.total_occupied)

    def to_dict(self):
        return {
            "id": self.id,
            "hostel_name": self.hostel_name,
            "hostel_type": self.hostel_type,
            "address": self.address,
            "total_rooms": self.total_rooms,
            "description": self.description or "",
            "total_capacity": self.total_capacity,
            "total_occupied": self.total_occupied,
            "free_beds": self.free_beds
        }


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    registration_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    academic_year = db.Column(db.SmallInteger, nullable=False)
    gender = db.Column(db.Enum("Male", "Female", "Other", name="genders"), nullable=False)
    address = db.Column(db.String(255))

    applications = db.relationship("Application", backref="student", cascade="all, delete-orphan", lazy="dynamic")
    allocations = db.relationship("Allocation", backref="student", cascade="all, delete-orphan", lazy="dynamic")
    complaints = db.relationship("Complaint", backref="student", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def active_allocation(self):
        return self.allocations.filter(Allocation.status.in_(["Allocated", "Checked-In"])).first()

    @property
    def active_application(self):
        return self.applications.filter(Application.status.in_(["Pending", "Approved"])).first()

    def to_dict(self):
        alloc = self.active_allocation
        alloc_str = f"{alloc.room.hostel.hostel_name} - {alloc.room.room_number}" if alloc and alloc.room else "None"
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.user.name if self.user else "",
            "email": self.user.email if self.user else "",
            "registration_number": self.registration_number,
            "phone": self.phone,
            "department": self.department,
            "academic_year": self.academic_year,
            "gender": self.gender,
            "address": self.address or "",
            "active_allocation": alloc_str,
            "allocation_status": alloc.status if alloc else "Unallocated"
        }


class Warden(db.Model):
    __tablename__ = "wardens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    assigned_hostel_id = db.Column(db.Integer, db.ForeignKey("hostels.id", ondelete="SET NULL"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.user.name if self.user else "",
            "email": self.user.email if self.user else "",
            "phone": self.phone,
            "assigned_hostel_id": self.assigned_hostel_id,
            "assigned_hostel_name": self.hostel.hostel_name if self.hostel else "Unassigned"
        }


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    hostel_id = db.Column(db.Integer, db.ForeignKey("hostels.id", ondelete="CASCADE"), nullable=False)
    room_number = db.Column(db.String(10), nullable=False)
    room_type = db.Column(db.Enum("Single", "Double", "Triple", "Dormitory", name="room_types"), nullable=False)
    capacity = db.Column(db.SmallInteger, nullable=False)
    occupied_count = db.Column(db.SmallInteger, default=0, nullable=False)
    status = db.Column(db.Enum("Available", "Full", "Maintenance", name="room_status"), default="Available", nullable=False)

    __table_args__ = (
        db.UniqueConstraint("hostel_id", "room_number", name="uq_hostel_room_no"),
    )

    allocations = db.relationship("Allocation", backref="room", lazy="dynamic")

    @property
    def free_beds(self):
        return max(0, self.capacity - self.occupied_count)

    def to_dict(self):
        return {
            "id": self.id,
            "hostel_id": self.hostel_id,
            "hostel_name": self.hostel.hostel_name if self.hostel else "",
            "room_number": self.room_number,
            "room_type": self.room_type,
            "capacity": self.capacity,
            "occupied_count": self.occupied_count,
            "free_beds": self.free_beds,
            "status": self.status
        }


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    preferred_hostel_id = db.Column(db.Integer, db.ForeignKey("hostels.id"), nullable=False)
    preferred_room_type = db.Column(db.Enum("Single", "Double", "Triple", "Dormitory", name="pref_room_types"), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Enum("Pending", "Approved", "Rejected", "Allocated", "Cancelled", name="app_status"), default="Pending", nullable=False)
    admin_remarks = db.Column(db.String(255))

    preferred_hostel = db.relationship("Hostel")
    allocations = db.relationship("Allocation", backref="application", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.user.name if self.student and self.student.user else "",
            "reg_no": self.student.registration_number if self.student else "",
            "preferred_hostel_id": self.preferred_hostel_id,
            "preferred_hostel_name": self.preferred_hostel.hostel_name if self.preferred_hostel else "",
            "preferred_room_type": self.preferred_room_type,
            "application_date": self.application_date.strftime("%Y-%m-%d") if self.application_date else "",
            "status": self.status,
            "admin_remarks": self.admin_remarks or ""
        }


class Allocation(db.Model):
    __tablename__ = "allocations"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    allocation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    check_in_date = db.Column(db.DateTime, nullable=True)
    check_out_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum("Allocated", "Checked-In", "Checked-Out", "Cancelled", name="alloc_status"), default="Allocated", nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.user.name if self.student and self.student.user else "",
            "reg_no": self.student.registration_number if self.student else "",
            "room_id": self.room_id,
            "room_number": self.room.room_number if self.room else "",
            "hostel_name": self.room.hostel.hostel_name if self.room and self.room.hostel else "",
            "application_id": self.application_id,
            "allocation_date": self.allocation_date.strftime("%Y-%m-%d") if self.allocation_date else "",
            "check_in_date": self.check_in_date.strftime("%Y-%m-%d") if self.check_in_date else None,
            "check_out_date": self.check_out_date.strftime("%Y-%m-%d") if self.check_out_date else None,
            "status": self.status
        }


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    hostel_id = db.Column(db.Integer, db.ForeignKey("hostels.id", ondelete="SET NULL"), nullable=True)
    complaint_title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    complaint_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Enum("Open", "In Progress", "Resolved", "Closed", name="complaint_status"), default="Open", nullable=False)
    warden_remarks = db.Column(db.String(255))

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.user.name if self.student and self.student.user else "",
            "hostel_id": self.hostel_id,
            "hostel_name": self.hostel.hostel_name if self.hostel else "General",
            "complaint_title": self.complaint_title,
            "description": self.description,
            "complaint_date": self.complaint_date.strftime("%Y-%m-%d") if self.complaint_date else "",
            "status": self.status,
            "warden_remarks": self.warden_remarks or ""
        }


class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    hostel_id = db.Column(db.Integer, db.ForeignKey("hostels.id", ondelete="CASCADE"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    creator = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "hostel_id": self.hostel_id,
            "hostel_name": self.hostel.hostel_name if self.hostel else "All Hostels",
            "created_by": self.creator.name if self.creator else "Admin",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else ""
        }


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "System",
            "action": self.action,
            "details": self.details or "",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""
        }


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_val(cls, key, default=""):
        item = cls.query.filter_by(key=key).first()
        return item.value if item else default

    @classmethod
    def set_val(cls, key, value):
        item = cls.query.filter_by(key=key).first()
        if not item:
            item = cls(key=key, value=str(value))
            db.session.add(item)
        else:
            item.value = str(value)
        db.session.commit()

