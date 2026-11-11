"""Database seed script: initializes schema and populates rich academic demo dataset."""
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import (
    User, Student, Hostel, Room, Application, Allocation, Complaint, Announcement, Warden, ActivityLog
)

app = create_app()

def seed_database():
    with app.app_context():
        print("Creating database tables...")
        db.create_all()

        # Check if database already has users
        if User.query.first():
            print("Database already contains data. Clearing existing records for clean seeding...")
            db.drop_all()
            db.create_all()

        print("Seeding Users...")
        # 1. Administrator
        admin = User(name="Dean of Student Affairs", email="admin@college.edu", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

        # 2. Wardens
        warden_user1 = User(name="Dr. Rajeshwar Sen", email="warden1@college.edu", role="warden")
        warden_user1.set_password("warden123")
        db.session.add(warden_user1)

        warden_user2 = User(name="Prof. Arundhati Das", email="warden2@college.edu", role="warden")
        warden_user2.set_password("warden123")
        db.session.add(warden_user2)

        # 3. Students
        s_users = [
            ("Rahul Mehta", "student@college.edu", "student123"),
            ("Priya Nair", "priya@college.edu", "student123"),
            ("Aman Verma", "aman@college.edu", "student123"),
            ("Kiran Rao", "kiran@college.edu", "student123"),
            ("Ananya Sharma", "ananya@college.edu", "student123"),
            ("Rohan Gupta", "rohan@college.edu", "student123"),
            ("Sneha Patel", "sneha@college.edu", "student123")
        ]
        created_s_users = []
        for name, email, pw in s_users:
            u = User(name=name, email=email, role="student")
            u.set_password(pw)
            db.session.add(u)
            created_s_users.append(u)

        db.session.flush()

        print("Seeding Hostels...")
        h1 = Hostel(
            hostel_name="Ashoka Hall",
            hostel_type="Boys",
            address="North Campus, Gate 2, Academic Boulevard",
            total_rooms=6,
            description="Premium residential hall for undergraduate male scholars featuring high-speed optical fiber, solar hot water, and landscaped study courtyards."
        )
        h2 = Hostel(
            hostel_name="Gargi Hall",
            hostel_type="Girls",
            address="South Campus, Promenade Way",
            total_rooms=5,
            description="State-of-the-art secure residential hall for female engineers and researchers with 24/7 security, gym, music room, and reading lounges."
        )
        h3 = Hostel(
            hostel_name="Tagore Hall",
            hostel_type="Co-ed",
            address="East Campus, Innovation Quadrangle",
            total_rooms=4,
            description="Postgraduate and international scholars residence hall with quiet research zones and collaborative group work spaces."
        )
        db.session.add_all([h1, h2, h3])
        db.session.flush()

        # Link Wardens to Hostels
        w1 = Warden(user_id=warden_user1.id, phone="9800011223", assigned_hostel_id=h1.id)
        w2 = Warden(user_id=warden_user2.id, phone="9800044556", assigned_hostel_id=h2.id)
        db.session.add_all([w1, w2])

        print("Seeding Rooms...")
        # Ashoka Hall Rooms
        r101 = Room(hostel_id=h1.id, room_number="101", room_type="Single", capacity=1, occupied_count=1, status="Full")
        r102 = Room(hostel_id=h1.id, room_number="102", room_type="Double", capacity=2, occupied_count=1, status="Available")
        r103 = Room(hostel_id=h1.id, room_number="103", room_type="Double", capacity=2, occupied_count=0, status="Available")
        r104 = Room(hostel_id=h1.id, room_number="104", room_type="Triple", capacity=3, occupied_count=0, status="Available")
        r105 = Room(hostel_id=h1.id, room_number="105", room_type="Triple", capacity=3, occupied_count=0, status="Available")
        r106 = Room(hostel_id=h1.id, room_number="106", room_type="Dormitory", capacity=6, occupied_count=0, status="Available")

        # Gargi Hall Rooms
        r201 = Room(hostel_id=h2.id, room_number="201", room_type="Single", capacity=1, occupied_count=0, status="Available")
        r202 = Room(hostel_id=h2.id, room_number="202", room_type="Double", capacity=2, occupied_count=1, status="Available")
        r203 = Room(hostel_id=h2.id, room_number="203", room_type="Double", capacity=2, occupied_count=0, status="Available")
        r204 = Room(hostel_id=h2.id, room_number="204", room_type="Triple", capacity=3, occupied_count=0, status="Available")
        r205 = Room(hostel_id=h2.id, room_number="205", room_type="Dormitory", capacity=6, occupied_count=0, status="Maintenance")

        # Tagore Hall Rooms
        r301 = Room(hostel_id=h3.id, room_number="301", room_type="Single", capacity=1, occupied_count=0, status="Available")
        r302 = Room(hostel_id=h3.id, room_number="302", room_type="Double", capacity=2, occupied_count=0, status="Available")
        r303 = Room(hostel_id=h3.id, room_number="303", room_type="Triple", capacity=3, occupied_count=0, status="Available")
        r304 = Room(hostel_id=h3.id, room_number="304", room_type="Double", capacity=2, occupied_count=0, status="Available")

        all_rooms = [r101, r102, r103, r104, r105, r106, r201, r202, r203, r204, r205, r301, r302, r303, r304]
        db.session.add_all(all_rooms)
        db.session.flush()

        print("Seeding Students...")
        stu1 = Student(user_id=created_s_users[0].id, registration_number="CS2101", phone="9810011010",
                       department="Computer Science & Engineering", academic_year=2, gender="Male",
                       address="Flat 4B, Green Glen Layout, Bengaluru")
        stu2 = Student(user_id=created_s_users[1].id, registration_number="EC2102", phone="9810022020",
                       department="Electronics & Communication", academic_year=3, gender="Female",
                       address="12 Palm Meadows, Kochi, Kerala")
        stu3 = Student(user_id=created_s_users[2].id, registration_number="ME2103", phone="9810033030",
                       department="Mechanical Engineering", academic_year=3, gender="Male",
                       address="78 Civil Lines, Jaipur, Rajasthan")
        stu4 = Student(user_id=created_s_users[3].id, registration_number="CS2104", phone="9810044040",
                       department="Computer Science & Engineering", academic_year=1, gender="Male",
                       address="93 Lakeview Heights, Hyderabad")
        stu5 = Student(user_id=created_s_users[4].id, registration_number="BT2105", phone="9810055050",
                       department="Biotechnology", academic_year=2, gender="Female",
                       address="52 Park Street, Kolkata, West Bengal")
        stu6 = Student(user_id=created_s_users[5].id, registration_number="CE2106", phone="9810066060",
                       department="Civil Engineering", academic_year=4, gender="Male",
                       address="40 North Avenue, New Delhi")
        stu7 = Student(user_id=created_s_users[6].id, registration_number="IT2107", phone="9810077070",
                       department="Information Technology", academic_year=1, gender="Female",
                       address="14 MG Road, Pune, Maharashtra")

        students = [stu1, stu2, stu3, stu4, stu5, stu6, stu7]
        db.session.add_all(students)
        db.session.flush()

        print("Seeding Applications...")
        # 1. Rahul: Pending application
        app1 = Application(student_id=stu1.id, preferred_hostel_id=h1.id, preferred_room_type="Single",
                           application_date=datetime.utcnow() - timedelta(days=2), status="Pending")
        # 2. Priya: Approved application (Ready to allocate!)
        app2 = Application(student_id=stu2.id, preferred_hostel_id=h2.id, preferred_room_type="Double",
                           application_date=datetime.utcnow() - timedelta(days=5), status="Approved",
                           admin_remarks="Documents and merit ranking verified. Recommended for allocation.")
        # 3. Aman: Allocated to Ashoka Hall Single
        app3 = Application(student_id=stu3.id, preferred_hostel_id=h1.id, preferred_room_type="Single",
                           application_date=datetime.utcnow() - timedelta(days=15), status="Allocated",
                           admin_remarks="Approved.")
        # 4. Kiran: Allocated to Ashoka Hall Double
        app4 = Application(student_id=stu4.id, preferred_hostel_id=h1.id, preferred_room_type="Double",
                           application_date=datetime.utcnow() - timedelta(days=12), status="Allocated",
                           admin_remarks="Approved.")
        # 5. Ananya: Allocated to Gargi Hall Double
        app5 = Application(student_id=stu5.id, preferred_hostel_id=h2.id, preferred_room_type="Double",
                           application_date=datetime.utcnow() - timedelta(days=20), status="Allocated",
                           admin_remarks="Approved.")
        # 6. Rohan: Rejected application
        app6 = Application(student_id=stu6.id, preferred_hostel_id=h1.id, preferred_room_type="Single",
                           application_date=datetime.utcnow() - timedelta(days=7), status="Rejected",
                           admin_remarks="Single rooms in preferred block are fully occupied. Please reapply for Double or Triple sharing.")

        db.session.add_all([app1, app2, app3, app4, app5, app6])
        db.session.flush()

        print("Seeding Allocations...")
        # Aman: Checked-In in Ashoka 101
        alloc1 = Allocation(student_id=stu3.id, room_id=r101.id, application_id=app3.id,
                            allocation_date=datetime.utcnow() - timedelta(days=14),
                            check_in_date=datetime.utcnow() - timedelta(days=13),
                            status="Checked-In")
        # Kiran: Allocated in Ashoka 102 (Awaiting physical check-in)
        alloc2 = Allocation(student_id=stu4.id, room_id=r102.id, application_id=app4.id,
                            allocation_date=datetime.utcnow() - timedelta(days=10),
                            status="Allocated")
        # Ananya: Checked-In in Gargi 202
        alloc3 = Allocation(student_id=stu5.id, room_id=r202.id, application_id=app5.id,
                            allocation_date=datetime.utcnow() - timedelta(days=18),
                            check_in_date=datetime.utcnow() - timedelta(days=17),
                            status="Checked-In")

        db.session.add_all([alloc1, alloc2, alloc3])

        print("Seeding Complaints...")
        comp1 = Complaint(student_id=stu3.id, hostel_id=h1.id,
                          complaint_title="Water pressure low in washroom",
                          description="The shower and sink water pressure in washroom 1-B on 1st floor has been weak since yesterday morning.",
                          complaint_date=datetime.utcnow() - timedelta(days=1), status="Open")

        comp2 = Complaint(student_id=stu5.id, hostel_id=h2.id,
                          complaint_title="Wi-Fi connectivity drop on 2nd Floor",
                          description="The wireless access point near room 202 disconnects intermittently between 8:00 PM and 10:00 PM.",
                          complaint_date=datetime.utcnow() - timedelta(days=3), status="In Progress",
                          warden_remarks="Campus IT team contacted. Firmware update scheduled for tonight.")

        comp3 = Complaint(student_id=stu4.id, hostel_id=h1.id,
                          complaint_title="Study table lamp fixture loose",
                          description="The built-in study desk lamp fixture in room 102 required screw tightening.",
                          complaint_date=datetime.utcnow() - timedelta(days=6), status="Resolved",
                          warden_remarks="Hostel maintenance electrician replaced the mount on Wednesday.")

        db.session.add_all([comp1, comp2, comp3])

        print("Seeding Announcements...")
        ann1 = Announcement(
            title="Hostel Allotment & Onboarding for Academic Term 2026-27",
            description="Online accommodation applications are officially open for all registered undergraduate and postgraduate scholars. Students must ensure their department registration is active prior to applying.",
            hostel_id=None, created_by=admin.id, created_at=datetime.utcnow() - timedelta(days=4)
        )
        ann2 = Announcement(
            title="North Campus Infrastructure Maintenance Notice",
            description="Routine maintenance of the high-tension transformer and backup diesel generator will occur this Saturday between 10:00 AM and 1:00 PM. Power backups in common areas will remain functional.",
            hostel_id=h1.id, created_by=warden_user1.id, created_at=datetime.utcnow() - timedelta(days=2)
        )
        ann3 = Announcement(
            title="Extended Library and Study Lounge Hours during Mid-Sem",
            description="The central reading room and common study lounges in Gargi Hall will remain open until midnight during the forthcoming examination weeks.",
            hostel_id=h2.id, created_by=warden_user2.id, created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.session.add_all([ann1, ann2, ann3])

        print("Seeding Activity Logs...")
        logs = [
            ActivityLog(user_id=admin.id, action="System Setup", details="Initial database migration and configuration completed"),
            ActivityLog(user_id=admin.id, action="Hostel Created", details="Configured Ashoka Hall and Gargi Hall blocks"),
            ActivityLog(user_id=warden_user1.id, action="Check-in", details="Checked in student CS2103 (Aman Verma) into Room 101"),
            ActivityLog(user_id=warden_user2.id, action="Check-in", details="Checked in student BT2105 (Ananya Sharma) into Room 202"),
        ]
        db.session.add_all(logs)

        db.session.commit()
        print("Database seeded successfully with all roles, hostels, rooms, and allocations!")

if __name__ == "__main__":
    seed_database()
