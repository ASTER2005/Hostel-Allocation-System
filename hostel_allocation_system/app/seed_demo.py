# Auto-seed the database with demo data if the users table is empty.
# This runs inside create_app() after db.create_all() so Vercel gets
# working credentials on first cold-start without any manual step.

import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash


def auto_seed_if_empty(app, db):
    """Seed demo data only when the database has no users yet."""
    with app.app_context():
        from app.models import (
            User, Student, Warden, Hostel, Room,
            Application, Allocation, Complaint, Announcement,
            ActivityLog, SystemSetting,
        )

        if User.query.count() > 0:
            return  # Already seeded — do nothing

        try:
            # ── Users ──────────────────────────────────────────────────────
            admin = User(name="Admin User", email="admin@college.edu",
                         password_hash=generate_password_hash("admin123"),
                         role="admin")

            w1 = User(name="Dr. Ramesh Kumar", email="warden1@college.edu",
                      password_hash=generate_password_hash("warden123"),
                      role="warden")
            w2 = User(name="Ms. Priya Singh", email="warden2@college.edu",
                      password_hash=generate_password_hash("warden123"),
                      role="warden")

            s_users = []
            for i, (name, email, gender) in enumerate([
                ("Rahul Sharma",   "CS2101@college.edu", "Male"),
                ("Amit Patel",     "ME2102@college.edu", "Male"),
                ("Aman Verma",     "CS2103@college.edu", "Male"),
                ("Ravi Gupta",     "EC2104@college.edu", "Male"),
                ("Ananya Sharma",  "BT2105@college.edu", "Female"),
                ("Nikhil Joshi",   "CE2106@college.edu", "Male"),
                ("Sneha Reddy",    "IT2107@college.edu", "Female"),
            ], 1):
                s_users.append(User(name=name, email=email,
                                    password_hash=generate_password_hash("student123"),
                                    role="student"))

            db.session.add_all([admin, w1, w2] + s_users)
            db.session.flush()

            # ── Hostels ────────────────────────────────────────────────────
            h1 = Hostel(hostel_name="Ashoka Hall", hostel_type="Boys",
                        address="North Campus Block A",
                        description="Premier boys' residential hall with air-conditioned rooms, 24-hour Wi-Fi, and a gym.")
            h2 = Hostel(hostel_name="Gargi Hall", hostel_type="Girls",
                        address="South Campus Block B",
                        description="Exclusively for female scholars with CCTV, biometric entry, and a common study lounge.")
            db.session.add_all([h1, h2])
            db.session.flush()

            # ── Wardens ────────────────────────────────────────────────────
            db.session.add_all([
                Warden(user_id=w1.id, phone="9810011010", assigned_hostel_id=h1.id),
                Warden(user_id=w2.id, phone="9810022020", assigned_hostel_id=h2.id),
            ])

            # ── Rooms ──────────────────────────────────────────────────────
            rooms_h1 = [
                Room(hostel_id=h1.id, room_number="101", room_type="Single",    capacity=1, occupied_count=1, status="Full"),
                Room(hostel_id=h1.id, room_number="102", room_type="Double",    capacity=2, occupied_count=1, status="Available"),
                Room(hostel_id=h1.id, room_number="103", room_type="Triple",    capacity=3, occupied_count=0, status="Available"),
                Room(hostel_id=h1.id, room_number="104", room_type="Dormitory", capacity=6, occupied_count=0, status="Available"),
                Room(hostel_id=h1.id, room_number="105", room_type="Single",    capacity=1, occupied_count=0, status="Available"),
                Room(hostel_id=h1.id, room_number="106", room_type="Double",    capacity=2, occupied_count=0, status="Available"),
            ]
            rooms_h2 = [
                Room(hostel_id=h2.id, room_number="201", room_type="Single",    capacity=1, occupied_count=0, status="Available"),
                Room(hostel_id=h2.id, room_number="202", room_type="Double",    capacity=2, occupied_count=1, status="Available"),
                Room(hostel_id=h2.id, room_number="203", room_type="Triple",    capacity=3, occupied_count=0, status="Available"),
                Room(hostel_id=h2.id, room_number="204", room_type="Double",    capacity=2, occupied_count=0, status="Available"),
            ]
            db.session.add_all(rooms_h1 + rooms_h2)
            db.session.flush()

            r101, r102, _, _, _, _ = rooms_h1
            _, r202, _, _ = rooms_h2

            # ── Students ───────────────────────────────────────────────────
            s_data = [
                ("CS2101", "9810011110", "Computer Science",    1, "Male",   "12 MG Road, Bengaluru"),
                ("ME2102", "9810022220", "Mechanical Engg",     2, "Male",   "5 Lake View, Hyderabad"),
                ("CS2103", "9810033330", "Computer Science",    2, "Male",   "22 Park Street, Kolkata"),
                ("EC2104", "9810044440", "Electronics & Comm",  3, "Male",   "8 Civil Lines, Jaipur"),
                ("BT2105", "9810055550", "Biotechnology",       1, "Female", "31 Linking Road, Mumbai"),
                ("CE2106", "9810066060", "Civil Engineering",   4, "Male",   "40 North Avenue, New Delhi"),
                ("IT2107", "9810077070", "Information Tech",    1, "Female", "14 MG Road, Pune"),
            ]
            students = [
                Student(user_id=s_users[i].id, registration_number=d[0],
                        phone=d[1], department=d[2], academic_year=d[3],
                        gender=d[4], address=d[5])
                for i, d in enumerate(s_data)
            ]
            db.session.add_all(students)
            db.session.flush()

            stu1, stu2, stu3, stu4, stu5, stu6, stu7 = students

            # ── Applications ───────────────────────────────────────────────
            apps = [
                Application(student_id=stu1.id, preferred_hostel_id=h1.id,
                            preferred_room_type="Single",
                            application_date=datetime.utcnow() - timedelta(days=2),
                            status="Pending"),
                Application(student_id=stu2.id, preferred_hostel_id=h1.id,
                            preferred_room_type="Double",
                            application_date=datetime.utcnow() - timedelta(days=5),
                            status="Approved", admin_remarks="Verified merit credentials."),
                Application(student_id=stu3.id, preferred_hostel_id=h1.id,
                            preferred_room_type="Single",
                            application_date=datetime.utcnow() - timedelta(days=15),
                            status="Allocated", admin_remarks="Approved."),
                Application(student_id=stu4.id, preferred_hostel_id=h1.id,
                            preferred_room_type="Double",
                            application_date=datetime.utcnow() - timedelta(days=12),
                            status="Allocated", admin_remarks="Approved."),
                Application(student_id=stu5.id, preferred_hostel_id=h2.id,
                            preferred_room_type="Double",
                            application_date=datetime.utcnow() - timedelta(days=20),
                            status="Allocated", admin_remarks="Approved."),
                Application(student_id=stu6.id, preferred_hostel_id=h1.id,
                            preferred_room_type="Single",
                            application_date=datetime.utcnow() - timedelta(days=7),
                            status="Rejected", admin_remarks="Single rooms fully booked."),
            ]
            db.session.add_all(apps)
            db.session.flush()

            app3, app4, app5 = apps[2], apps[3], apps[4]

            # ── Allocations ────────────────────────────────────────────────
            db.session.add_all([
                Allocation(student_id=stu3.id, room_id=r101.id, application_id=app3.id,
                           allocation_date=datetime.utcnow() - timedelta(days=14),
                           check_in_date=datetime.utcnow() - timedelta(days=13),
                           status="Checked-In"),
                Allocation(student_id=stu4.id, room_id=r102.id, application_id=app4.id,
                           allocation_date=datetime.utcnow() - timedelta(days=10),
                           status="Allocated"),
                Allocation(student_id=stu5.id, room_id=r202.id, application_id=app5.id,
                           allocation_date=datetime.utcnow() - timedelta(days=18),
                           check_in_date=datetime.utcnow() - timedelta(days=17),
                           status="Checked-In"),
            ])

            # ── Complaints ─────────────────────────────────────────────────
            db.session.add_all([
                Complaint(student_id=stu3.id, hostel_id=h1.id,
                          complaint_title="Water pressure low in washroom",
                          description="Shower pressure in washroom 1-B has been weak since yesterday.",
                          complaint_date=datetime.utcnow() - timedelta(days=1), status="Open"),
                Complaint(student_id=stu5.id, hostel_id=h2.id,
                          complaint_title="Wi-Fi connectivity drop on 2nd Floor",
                          description="Access point near room 202 disconnects intermittently.",
                          complaint_date=datetime.utcnow() - timedelta(days=3),
                          status="In Progress",
                          warden_remarks="Campus IT team contacted. Firmware update scheduled."),
                Complaint(student_id=stu4.id, hostel_id=h1.id,
                          complaint_title="Study table lamp fixture loose",
                          description="Built-in desk lamp bracket was loose.",
                          complaint_date=datetime.utcnow() - timedelta(days=6),
                          status="Resolved",
                          warden_remarks="Electrician replaced the mount on Wednesday."),
            ])

            # ── Announcements ──────────────────────────────────────────────
            db.session.add_all([
                Announcement(title="Hostel Allotment & Onboarding for Academic Term 2026-27",
                             description="Online accommodation applications are officially open for all registered scholars.",
                             hostel_id=None, created_by=admin.id,
                             created_at=datetime.utcnow() - timedelta(days=4)),
                Announcement(title="North Campus Infrastructure Maintenance Notice",
                             description="Routine maintenance of the transformer and generator this Saturday 10 AM – 1 PM.",
                             hostel_id=h1.id, created_by=w1.id,
                             created_at=datetime.utcnow() - timedelta(days=2)),
                Announcement(title="Extended Library & Study Lounge Hours during Mid-Sem",
                             description="Common study lounges in Gargi Hall will remain open until midnight during exam weeks.",
                             hostel_id=h2.id, created_by=w2.id,
                             created_at=datetime.utcnow() - timedelta(days=1)),
            ])

            # ── System Settings ────────────────────────────────────────────
            settings = [
                SystemSetting(key="institution_name",   value="National College of Engineering & Technology"),
                SystemSetting(key="academic_year",      value="2026-2027"),
                SystemSetting(key="intake_status",      value="Open"),
                SystemSetting(key="curfew_hours",       value="10:00 PM"),
                SystemSetting(key="contact_email",      value="residential@college.edu"),
                SystemSetting(key="emergency_phone",    value="+91 (080) 2855-4300 / Ext 412"),
                SystemSetting(key="complaint_sla_days", value="3"),
                SystemSetting(key="max_room_transfers", value="1"),
            ]
            db.session.add_all(settings)

            # ── Activity Logs ──────────────────────────────────────────────
            db.session.add_all([
                ActivityLog(user_id=admin.id, action="System Setup",
                            details="Auto-seeded demo data on first deployment"),
                ActivityLog(user_id=w1.id, action="Check-in",
                            details="Checked in CS2103 (Aman Verma) into Room 101"),
                ActivityLog(user_id=w2.id, action="Check-in",
                            details="Checked in BT2105 (Ananya Sharma) into Room 202"),
            ])

            db.session.commit()

        except Exception as exc:
            db.session.rollback()
            app.logger.warning(f"[auto_seed] Demo seeding failed (non-fatal): {exc}")

