"""Student Portal routes for dashboard, applications, profile, room details and complaints."""
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.auth.decorators import role_required
from app.models import Student, Hostel, Room, Application, Allocation, Complaint, Announcement, ActivityLog, SystemSetting
from app.forms import StudentProfileForm, HostelApplicationForm, ComplaintForm
from . import bp


def get_current_student():
    """Retrieves the Student record associated with current_user."""
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        abort(404, description="Student profile not found.")
    return student


@bp.route("/")
@bp.route("/overview")
@login_required
@role_required("student")
def overview():
    """Student dashboard overview with active status cards, room info and latest notices."""
    student = get_current_student()
    active_app = student.active_application
    latest_app = student.applications.order_by(Application.application_date.desc()).first()
    active_alloc = student.active_allocation
    active_complaints_count = student.complaints.filter(Complaint.status.in_(["Open", "In Progress"])).count()
    
    # Announcements visible to student: general (hostel_id is NULL) or for student's allocated/applied hostel
    assigned_hostel_id = active_alloc.room.hostel_id if active_alloc and active_alloc.room else None
    if not assigned_hostel_id and active_app:
        assigned_hostel_id = active_app.preferred_hostel_id

    announcements_query = Announcement.query.filter(
        (Announcement.hostel_id == None) | (Announcement.hostel_id == assigned_hostel_id)
    ).order_by(Announcement.created_at.desc()).limit(5)
    announcements = announcements_query.all()

    return render_template("student/dashboard.html",
                           student=student,
                           active_app=active_app,
                           latest_app=latest_app,
                           active_alloc=active_alloc,
                           active_complaints_count=active_complaints_count,
                           announcements=announcements)


@bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("student")
def profile():
    """View and update student personal information."""
    student = get_current_student()
    form = StudentProfileForm(obj=student)

    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        student.phone = form.phone.data.strip()
        student.department = form.department.data.strip()
        student.academic_year = form.academic_year.data
        student.address = form.address.data.strip() if form.address.data else ""

        log = ActivityLog(user_id=current_user.id, action="Update Profile", details="Updated personal details")
        db.session.add(log)
        db.session.commit()

        flash("Your profile information has been successfully updated.", "success")
        return redirect(url_for("student.profile"))

    # Initial form fill for user name
    if request.method == "GET":
        form.name.data = current_user.name

    return render_template("student/profile.html", student=student, form=form)


@bp.route("/apply", methods=["GET", "POST"])
@login_required
@role_required("student")
def apply():
    """Browse available hostels and submit an accommodation application."""
    student = get_current_student()
    active_app = student.active_application
    active_alloc = student.active_allocation

    # Hostels matching student gender or co-ed
    if student.gender == "Male":
        available_hostels = Hostel.query.filter(Hostel.hostel_type.in_(["Boys", "Co-ed"])).all()
    elif student.gender == "Female":
        available_hostels = Hostel.query.filter(Hostel.hostel_type.in_(["Girls", "Co-ed"])).all()
    else:
        available_hostels = Hostel.query.all()

    form = HostelApplicationForm()
    form.preferred_hostel_id.choices = [(h.id, f"{h.hostel_name} ({h.hostel_type} - {h.free_beds} beds free)") for h in available_hostels]
    intake_status = SystemSetting.get_val("intake_status", "Open")

    if form.validate_on_submit():
        if intake_status == "Closed":
            flash("Hostel accommodation applications are currently closed by the administration for this term.", "danger")
            return redirect(url_for("student.apply"))

        # Business logic checks
        if active_alloc:
            flash("You already have an active room allocation. Multiple allocations are prohibited.", "danger")
            return redirect(url_for("student.apply"))

        if active_app:
            flash(f"You already have an active application ({active_app.status}). Multiple active applications are prohibited.", "warning")
            return redirect(url_for("student.applications"))

        chosen_hostel = db.session.get(Hostel, form.preferred_hostel_id.data)
        if not chosen_hostel:
            flash("Selected hostel does not exist.", "danger")
            return redirect(url_for("student.apply"))

        # Verify gender eligibility
        if chosen_hostel.hostel_type == "Boys" and student.gender != "Male":
            flash("Selected hostel is reserved for male students only.", "danger")
            return redirect(url_for("student.apply"))
        if chosen_hostel.hostel_type == "Girls" and student.gender != "Female":
            flash("Selected hostel is reserved for female students only.", "danger")
            return redirect(url_for("student.apply"))

        new_app = Application(
            student_id=student.id,
            preferred_hostel_id=chosen_hostel.id,
            preferred_room_type=form.preferred_room_type.data,
            status="Pending"
        )
        db.session.add(new_app)
        
        log = ActivityLog(user_id=current_user.id, action="Hostel Application", 
                          details=f"Applied for {chosen_hostel.hostel_name} ({form.preferred_room_type.data})")
        db.session.add(log)
        db.session.commit()

        flash("Your hostel application has been submitted successfully! It is now pending administrative review.", "success")
        return redirect(url_for("student.applications"))

    return render_template("student/apply.html", 
                           student=student, 
                           available_hostels=available_hostels, 
                           active_app=active_app, 
                           active_alloc=active_alloc, 
                           intake_status=intake_status,
                           form=form)


@bp.route("/applications")
@login_required
@role_required("student")
def applications():
    """List of all submitted hostel applications and their statuses."""
    student = get_current_student()
    all_apps = student.applications.order_by(Application.application_date.desc()).all()
    return render_template("student/applications.html", student=student, applications=all_apps)


@bp.route("/room")
@login_required
@role_required("student")
def room():
    """Detailed view of allocated hostel room, roommates, facilities, and 3D interior."""
    student = get_current_student()
    active_alloc = student.active_allocation

    roommates = []
    warden = None
    if active_alloc and active_alloc.room:
        # Find roommates in the same room
        other_allocs = Allocation.query.filter(
            Allocation.room_id == active_alloc.room_id,
            Allocation.status.in_(["Allocated", "Checked-In"]),
            Allocation.student_id != student.id
        ).all()
        roommates = [a.student for a in other_allocs]

        # Hostel warden
        warden = Warden.query.filter_by(assigned_hostel_id=active_alloc.room.hostel_id).first()

    return render_template("student/room.html", 
                           student=student, 
                           allocation=active_alloc, 
                           roommates=roommates, 
                           warden=warden)


@bp.route("/complaints", methods=["GET", "POST"])
@login_required
@role_required("student")
def complaints():
    """View and lodge maintenance/hostel complaints."""
    student = get_current_student()
    form = ComplaintForm()

    # Prepopulate hostel choices
    hostels = Hostel.query.all()
    form.hostel_id.choices = [(0, "Select Related Hostel (Optional)")] + [(h.id, h.hostel_name) for h in hostels]

    active_alloc = student.active_allocation
    if request.method == "GET" and active_alloc and active_alloc.room:
        form.hostel_id.data = active_alloc.room.hostel_id

    if form.validate_on_submit():
        hostel_id = form.hostel_id.data if form.hostel_id.data != 0 else None
        if not hostel_id and active_alloc and active_alloc.room:
            hostel_id = active_alloc.room.hostel_id

        complaint = Complaint(
            student_id=student.id,
            hostel_id=hostel_id,
            complaint_title=form.complaint_title.data.strip(),
            description=form.description.data.strip(),
            status="Open"
        )
        db.session.add(complaint)

        log = ActivityLog(user_id=current_user.id, action="File Complaint", details=f"Lodged complaint: {complaint.complaint_title[:40]}")
        db.session.add(log)
        db.session.commit()

        flash("Your complaint has been submitted. The warden has been notified.", "success")
        return redirect(url_for("student.complaints"))

    my_complaints = student.complaints.order_by(Complaint.complaint_date.desc()).all()
    return render_template("student/complaints.html", student=student, complaints=my_complaints, form=form)


@bp.route("/announcements")
@login_required
@role_required("student")
def announcements():
    """Hostel and college-wide announcements."""
    student = get_current_student()
    active_alloc = student.active_allocation
    active_app = student.active_application

    assigned_hostel_id = active_alloc.room.hostel_id if active_alloc and active_alloc.room else None
    if not assigned_hostel_id and active_app:
        assigned_hostel_id = active_app.preferred_hostel_id

    announcements_list = Announcement.query.filter(
        (Announcement.hostel_id == None) | (Announcement.hostel_id == assigned_hostel_id)
    ).order_by(Announcement.created_at.desc()).all()

    return render_template("student/announcements.html", announcements=announcements_list)
