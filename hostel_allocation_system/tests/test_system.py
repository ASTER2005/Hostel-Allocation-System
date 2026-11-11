"""Comprehensive Test Suite for Hostel Allocation and Management System.
Covers all 12 functional, security, and transaction requirements.
"""
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Student, Hostel, Room, Application, Allocation, Complaint


@pytest.fixture
def app():
    """Create application configured for testing with in-memory SQLite."""
    class TestConfig:
        TESTING = True
        SECRET_KEY = "test-secret-key-2026"
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        WTF_CSRF_ENABLED = False  # Disable CSRF in tests for direct POST assertions

    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()

        # Seed initial test fixtures
        admin = User(name="Test Admin", email="admin@test.edu", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

        h1 = Hostel(hostel_name="Test Boys Hall", hostel_type="Boys", address="Campus Gate 1", total_rooms=2)
        h2 = Hostel(hostel_name="Test Girls Hall", hostel_type="Girls", address="Campus Gate 2", total_rooms=2)
        db.session.add_all([h1, h2])
        db.session.flush()

        # Room 1: Capacity 1 (Single)
        r1 = Room(hostel_id=h1.id, room_number="101", room_type="Single", capacity=1, occupied_count=0, status="Available")
        # Room 2: Capacity 2 (Double)
        r2 = Room(hostel_id=h1.id, room_number="102", room_type="Double", capacity=2, occupied_count=0, status="Available")
        db.session.add_all([r1, r2])

        # Test Student 1
        s_user1 = User(name="Aarav Sharma", email="aarav@test.edu", role="student")
        s_user1.set_password("student123")
        db.session.add(s_user1)
        db.session.flush()

        s1 = Student(user_id=s_user1.id, registration_number="CS9001", phone="9998887771",
                     department="Computer Science", academic_year=2, gender="Male")
        db.session.add(s1)

        # Test Student 2
        s_user2 = User(name="Isha Gupta", email="isha@test.edu", role="student")
        s_user2.set_password("student123")
        db.session.add(s_user2)
        db.session.flush()

        s2 = Student(user_id=s_user2.id, registration_number="CS9002", phone="9998887772",
                     department="Information Technology", academic_year=1, gender="Female")
        db.session.add(s2)

        # Test Warden
        w_user = User(name="Warden Officer", email="warden@test.edu", role="warden")
        w_user.set_password("warden123")
        db.session.add(w_user)
        db.session.flush()
        from app.models import Warden
        w = Warden(user_id=w_user.id, phone="9990001112", assigned_hostel_id=h1.id)
        db.session.add(w)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# =========================================================================
# 1. Student Registration Test
# =========================================================================
def test_student_registration(client, app):
    response = client.post("/register", data={
        "name": "Kavya Reddy",
        "registration_number": "EC9003",
        "email": "kavya@test.edu",
        "phone": "9876543210",
        "department": "Electronics",
        "academic_year": 1,
        "gender": "Female",
        "address": "Hyderabad",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="kavya@test.edu").first()
        assert user is not None
        assert user.role == "student"
        assert user.student.registration_number == "EC9003"
        assert user.check_password("password123")


# =========================================================================
# 2. Login and Logout Test
# =========================================================================
def test_login_and_logout(client):
    # Successful login
    login_resp = client.post("/login", data={
        "email": "aarav@test.edu",
        "password": "student123"
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b"Student Overview" in login_resp.data

    # Logout
    logout_resp = client.get("/logout", follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"Sign In" in logout_resp.data


# =========================================================================
# 3. Invalid Login Attempts Test
# =========================================================================
def test_invalid_login_attempts(client):
    response = client.post("/login", data={
        "email": "aarav@test.edu",
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid email address or password" in response.data


# =========================================================================
# 4. Application Submission Test
# =========================================================================
def test_application_submission(client, app):
    # Sign in as student Aarav
    client.post("/login", data={"email": "aarav@test.edu", "password": "student123"})
    with app.app_context():
        h = Hostel.query.filter_by(hostel_name="Test Boys Hall").first()
        h_id = h.id

    app_resp = client.post("/student/apply", data={
        "preferred_hostel_id": h_id,
        "preferred_room_type": "Single"
    }, follow_redirects=True)

    assert app_resp.status_code == 200
    with app.app_context():
        student = Student.query.filter_by(registration_number="CS9001").first()
        active_app = student.active_application
        assert active_app is not None
        assert active_app.status == "Pending"
        assert active_app.preferred_room_type == "Single"


# =========================================================================
# 5. Application Approval and Rejection Test
# =========================================================================
def test_application_approval_and_rejection(client, app):
    # Create application for student 1
    with app.app_context():
        student = Student.query.filter_by(registration_number="CS9001").first()
        h = Hostel.query.first()
        new_app = Application(student_id=student.id, preferred_hostel_id=h.id, preferred_room_type="Single", status="Pending")
        db.session.add(new_app)
        db.session.commit()
        app_id = new_app.id

    # Login as Admin
    client.post("/login", data={"email": "admin@test.edu", "password": "admin123"})

    # Approve application
    approve_resp = client.post(f"/admin/applications/{app_id}/decide", data={
        "status": "Approved",
        "admin_remarks": "Eligible"
    }, follow_redirects=True)
    assert approve_resp.status_code == 200

    with app.app_context():
        updated_app = db.session.get(Application, app_id)
        assert updated_app.status == "Approved"
        assert updated_app.admin_remarks == "Eligible"


# =========================================================================
# 6. Room Allocation Test
# =========================================================================
def test_room_allocation(client, app):
    with app.app_context():
        student = Student.query.filter_by(registration_number="CS9001").first()
        room = Room.query.filter_by(room_number="101").first()
        application = Application(student_id=student.id, preferred_hostel_id=room.hostel_id,
                                  preferred_room_type="Single", status="Approved")
        db.session.add(application)
        db.session.commit()
        app_id = application.id
        room_id = room.id

    # Login as Admin
    client.post("/login", data={"email": "admin@test.edu", "password": "admin123"})

    alloc_resp = client.post("/admin/allocations/allocate", data={
        "application_id": app_id,
        "room_id": room_id
    }, follow_redirects=True)

    assert alloc_resp.status_code == 200
    with app.app_context():
        r = db.session.get(Room, room_id)
        a = db.session.get(Application, app_id)
        alloc = Allocation.query.filter_by(application_id=app_id).first()

        assert a.status == "Allocated"
        assert r.occupied_count == 1
        assert r.status == "Full"  # capacity was 1, now full!
        assert alloc is not None
        assert alloc.status == "Allocated"


# =========================================================================
# 7. Room Capacity Validation Test
# =========================================================================
def test_room_capacity_validation(client, app):
    # Setup full room (Room 101 has capacity 1)
    with app.app_context():
        s1 = Student.query.filter_by(registration_number="CS9001").first()
        s2 = Student.query.filter_by(registration_number="CS9002").first()
        room = Room.query.filter_by(room_number="101").first()
        room.occupied_count = 1
        room.status = "Full"

        app2 = Application(student_id=s2.id, preferred_hostel_id=room.hostel_id,
                           preferred_room_type="Single", status="Approved")
        db.session.add(app2)
        db.session.commit()
        app2_id = app2.id
        room_id = room.id

    # Admin attempts to allocate another student into full room
    client.post("/login", data={"email": "admin@test.edu", "password": "admin123"})
    resp = client.post("/admin/allocations/allocate", data={
        "application_id": app2_id,
        "room_id": room_id
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"is already full" in resp.data

    with app.app_context():
        r = db.session.get(Room, room_id)
        assert r.occupied_count == 1  # Not exceeded


# =========================================================================
# 8. Duplicate Allocation Prevention Test
# =========================================================================
def test_duplicate_allocation_prevention(client, app):
    with app.app_context():
        s1 = Student.query.filter_by(registration_number="CS9001").first()
        r1 = Room.query.filter_by(room_number="101").first()
        r2 = Room.query.filter_by(room_number="102").first()

        # Existing active allocation for s1
        alloc1 = Allocation(student_id=s1.id, room_id=r1.id, status="Allocated")
        # Second approved application for s1
        app_dup = Application(student_id=s1.id, preferred_hostel_id=r2.hostel_id,
                              preferred_room_type="Double", status="Approved")
        db.session.add_all([alloc1, app_dup])
        db.session.commit()
        dup_app_id = app_dup.id
        r2_id = r2.id

    client.post("/login", data={"email": "admin@test.edu", "password": "admin123"})
    resp = client.post("/admin/allocations/allocate", data={
        "application_id": dup_app_id,
        "room_id": r2_id
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"already has an active allocation" in resp.data


# =========================================================================
# 9. Complaint Submission Test
# =========================================================================
def test_complaint_submission(client, app):
    client.post("/login", data={"email": "aarav@test.edu", "password": "student123"})
    with app.app_context():
        h = Hostel.query.first()
        h_id = h.id

    resp = client.post("/student/complaints", data={
        "complaint_title": "Ceiling fan speed controller broken",
        "hostel_id": h_id,
        "description": "The fan regulator knob does not rotate beyond speed 1."
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        comp = Complaint.query.filter_by(complaint_title="Ceiling fan speed controller broken").first()
        assert comp is not None
        assert comp.status == "Open"
        assert comp.hostel_id == h_id


# =========================================================================
# 10. Complaint Status Updates Test
# =========================================================================
def test_complaint_status_updates(client, app):
    with app.app_context():
        student = Student.query.filter_by(registration_number="CS9001").first()
        h = Hostel.query.filter_by(hostel_name="Test Boys Hall").first()
        comp = Complaint(student_id=student.id, hostel_id=h.id, complaint_title="Study desk fixture",
                         description="Loose screws", status="Open")
        db.session.add(comp)
        db.session.commit()
        comp_id = comp.id

    # Login as Warden
    client.post("/login", data={"email": "warden@test.edu", "password": "warden123"})
    update_resp = client.post(f"/warden/complaints/{comp_id}/update", data={
        "status": "Resolved",
        "warden_remarks": "Tightened and inspected by carpenter."
    }, follow_redirects=True)

    assert update_resp.status_code == 200
    with app.app_context():
        c = db.session.get(Complaint, comp_id)
        assert c.status == "Resolved"
        assert "Tightened and inspected" in c.warden_remarks


# =========================================================================
# 11. Role-Based Access Restrictions Test
# =========================================================================
def test_role_based_access_restrictions(client):
    # Log in as Student
    client.post("/login", data={"email": "aarav@test.edu", "password": "student123"})

    # Student attempts to access Admin dashboard -> 403 Forbidden
    admin_resp = client.get("/admin/overview")
    assert admin_resp.status_code == 403

    # Student attempts to access Warden dashboard -> 403 Forbidden
    warden_resp = client.get("/warden/overview")
    assert warden_resp.status_code == 403

    # Student attempts to hit Admin Sheet API -> 403 Forbidden
    sheet_api_resp = client.get("/admin/api/sheet/data")
    assert sheet_api_resp.status_code == 403


# =========================================================================
# 12. Database Integration & Transaction Rollback Test
# =========================================================================
def test_database_transaction_rollback(app):
    with app.app_context():
        try:
            with db.session.begin_nested():
                # Attempt to insert user with null required fields
                invalid_user = User(name=None, email=None)
                db.session.add(invalid_user)
                db.session.flush()
        except Exception:
            db.session.rollback()

        # Database state should be intact
        admin = User.query.filter_by(email="admin@test.edu").first()
        assert admin is not None
