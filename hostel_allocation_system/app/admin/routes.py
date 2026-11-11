"""Admin Portal routes: full institutional control, room allocation,
live database sheet editing, and comprehensive analytics.
"""
from datetime import datetime
import csv
import io
from flask import render_template, redirect, url_for, flash, request, jsonify, make_response, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.auth.decorators import role_required
from app.models import (
    User, Student, Hostel, Room, Application, Allocation, Complaint, Announcement, Warden, ActivityLog, SystemSetting
)
from app.forms import (
    HostelForm, RoomForm, WardenForm, AnnouncementForm, AllocationForm, ApplicationDecisionForm, SettingsForm
)
from . import bp


@bp.route("/")
@bp.route("/overview")
@login_required
@role_required("admin")
def overview():
    """Admin dashboard overview with 10 database metrics and 3 Chart.js datasets."""
    total_students = Student.query.count()
    total_hostels = Hostel.query.count()
    all_rooms = Room.query.all()
    total_rooms = len(all_rooms)
    total_capacity = sum(r.capacity for r in all_rooms)
    occupied_beds = sum(r.occupied_count for r in all_rooms)
    available_beds = max(0, total_capacity - occupied_beds)

    pending_apps = Application.query.filter_by(status="Pending").count()
    approved_apps = Application.query.filter_by(status="Approved").count()
    rejected_apps = Application.query.filter_by(status="Rejected").count()
    allocated_apps = Application.query.filter_by(status="Allocated").count()

    open_complaints = Complaint.query.filter(Complaint.status.in_(["Open", "In Progress"])).count()
    total_wardens = Warden.query.count()

    # Chart 1: Hostel Occupancy
    hostels = Hostel.query.all()
    chart_hostels_labels = [h.hostel_name for h in hostels]
    chart_hostels_occupied = [h.total_occupied for h in hostels]
    chart_hostels_capacity = [h.total_capacity for h in hostels]

    # Chart 2: Application Breakdown
    chart_apps_data = [pending_apps, approved_apps, rejected_apps, allocated_apps]

    # Recent activity logs & pending applications
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()
    recent_pending_apps = Application.query.filter_by(status="Pending").order_by(Application.application_date.desc()).limit(5).all()

    return render_template("admin/dashboard.html",
                           total_students=total_students,
                           total_hostels=total_hostels,
                           total_rooms=total_rooms,
                           total_capacity=total_capacity,
                           occupied_beds=occupied_beds,
                           available_beds=available_beds,
                           pending_apps=pending_apps,
                           approved_apps=approved_apps,
                           rejected_apps=rejected_apps,
                           open_complaints=open_complaints,
                           total_wardens=total_wardens,
                           chart_hostels_labels=chart_hostels_labels,
                           chart_hostels_occupied=chart_hostels_occupied,
                           chart_hostels_capacity=chart_hostels_capacity,
                           chart_apps_data=chart_apps_data,
                           recent_logs=recent_logs,
                           recent_pending_apps=recent_pending_apps)


# =========================================================================
# STUDENTS MANAGEMENT
# =========================================================================

@bp.route("/students")
@login_required
@role_required("admin")
def students():
    """List, search and filter all registered students."""
    query = request.args.get("q", "").strip()
    dept = request.args.get("dept", "").strip()
    year = request.args.get("year", type=int)

    students_query = Student.query.join(User)
    if query:
        search_filter = f"%{query}%"
        students_query = students_query.filter(
            (User.name.ilike(search_filter)) |
            (Student.registration_number.ilike(search_filter)) |
            (User.email.ilike(search_filter)) |
            (Student.department.ilike(search_filter))
        )
    if dept:
        students_query = students_query.filter(Student.department == dept)
    if year:
        students_query = students_query.filter(Student.academic_year == year)

    all_students = students_query.order_by(Student.registration_number.asc()).all()
    departments = [d[0] for d in db.session.query(Student.department).distinct().all()]

    return render_template("admin/students.html", 
                           students=all_students, 
                           query=query, 
                           selected_dept=dept, 
                           selected_year=year,
                           departments=departments)


@bp.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_student(student_id):
    """Deletes student record, cascade removes applications and releases allocated beds."""
    student = db.get_or_404(Student, student_id)
    try:
        # Release room capacity if active allocation exists
        active_alloc = student.active_allocation
        if active_alloc and active_alloc.room:
            active_alloc.room.occupied_count = max(0, active_alloc.room.occupied_count - 1)
            if active_alloc.room.status == "Full":
                active_alloc.room.status = "Available"

        user = student.user
        reg_no = student.registration_number
        db.session.delete(user)  # Cascades to student, apps, allocs, complaints

        log = ActivityLog(user_id=current_user.id, action="Delete Student", details=f"Deleted student {reg_no}")
        db.session.add(log)
        db.session.commit()

        flash(f"Student record {reg_no} and related allocations deleted.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting student: {str(e)}", "danger")

    return redirect(url_for("admin.students"))


# =========================================================================
# HOSTELS MANAGEMENT
# =========================================================================

@bp.route("/hostels", methods=["GET", "POST"])
@login_required
@role_required("admin")
def hostels():
    """List, add and edit hostels."""
    form = HostelForm()
    if form.validate_on_submit():
        existing = Hostel.query.filter_by(hostel_name=form.hostel_name.data.strip()).first()
        if existing:
            flash("A hostel with this name already exists.", "danger")
        else:
            hostel = Hostel(
                hostel_name=form.hostel_name.data.strip(),
                hostel_type=form.hostel_type.data,
                address=form.address.data.strip(),
                description=form.description.data.strip() if form.description.data else ""
            )
            db.session.add(hostel)
            log = ActivityLog(user_id=current_user.id, action="Add Hostel", details=f"Created hostel: {hostel.hostel_name}")
            db.session.add(log)
            db.session.commit()
            flash(f"Hostel '{hostel.hostel_name}' has been added successfully.", "success")
            return redirect(url_for("admin.hostels"))

    all_hostels = Hostel.query.order_by(Hostel.hostel_name.asc()).all()
    return render_template("admin/hostels.html", hostels=all_hostels, form=form)


@bp.route("/hostels/<int:hostel_id>/edit", methods=["POST"])
@login_required
@role_required("admin")
def edit_hostel(hostel_id):
    """Update existing hostel properties."""
    hostel = db.get_or_404(Hostel, hostel_id)
    hostel_name = request.form.get("hostel_name", "").strip()
    hostel_type = request.form.get("hostel_type")
    address = request.form.get("address", "").strip()
    description = request.form.get("description", "").strip()

    if not hostel_name or not address:
        flash("Hostel name and address are required.", "danger")
        return redirect(url_for("admin.hostels"))

    # Check unique name conflict
    existing = Hostel.query.filter(Hostel.hostel_name == hostel_name, Hostel.id != hostel_id).first()
    if existing:
        flash("Another hostel with this name already exists.", "danger")
        return redirect(url_for("admin.hostels"))

    hostel.hostel_name = hostel_name
    hostel.hostel_type = hostel_type
    hostel.address = address
    hostel.description = description

    log = ActivityLog(user_id=current_user.id, action="Edit Hostel", details=f"Updated hostel {hostel.hostel_name}")
    db.session.add(log)
    db.session.commit()

    flash(f"Hostel '{hostel.hostel_name}' updated successfully.", "success")
    return redirect(url_for("admin.hostels"))


@bp.route("/hostels/<int:hostel_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_hostel(hostel_id):
    """Delete a hostel if no occupied rooms remain."""
    hostel = db.get_or_404(Hostel, hostel_id)
    occupied_count = hostel.total_occupied
    if occupied_count > 0:
        flash(f"Cannot delete '{hostel.hostel_name}'. {occupied_count} students are currently allocated in its rooms.", "danger")
        return redirect(url_for("admin.hostels"))

    h_name = hostel.hostel_name
    db.session.delete(hostel)
    log = ActivityLog(user_id=current_user.id, action="Delete Hostel", details=f"Deleted hostel {h_name}")
    db.session.add(log)
    db.session.commit()

    flash(f"Hostel '{h_name}' and its rooms have been deleted.", "info")
    return redirect(url_for("admin.hostels"))


# =========================================================================
# ROOMS MANAGEMENT
# =========================================================================

@bp.route("/rooms", methods=["GET", "POST"])
@login_required
@role_required("admin")
def rooms():
    """List, search, filter and create rooms."""
    hostel_id = request.args.get("hostel_id", type=int)
    room_type = request.args.get("room_type", "").strip()
    status = request.args.get("status", "").strip()

    hostels = Hostel.query.order_by(Hostel.hostel_name.asc()).all()
    form = RoomForm()
    form.hostel_id.choices = [(h.id, h.hostel_name) for h in hostels]

    if form.validate_on_submit():
        h_id = form.hostel_id.data
        r_no = form.room_number.data.strip()

        # Check for unique room number per hostel
        existing = Room.query.filter_by(hostel_id=h_id, room_number=r_no).first()
        if existing:
            flash(f"Room number {r_no} already exists in this hostel.", "danger")
        else:
            room = Room(
                hostel_id=h_id,
                room_number=r_no,
                room_type=form.room_type.data,
                capacity=form.capacity.data,
                occupied_count=0,
                status=form.status.data
            )
            db.session.add(room)
            # Increment hostel total_rooms
            hostel = db.session.get(Hostel, h_id)
            if hostel:
                hostel.total_rooms += 1

            log = ActivityLog(user_id=current_user.id, action="Add Room", details=f"Added room {r_no} to {hostel.hostel_name}")
            db.session.add(log)
            db.session.commit()

            flash(f"Room {r_no} added successfully to {hostel.hostel_name}.", "success")
            return redirect(url_for("admin.rooms", hostel_id=h_id))

    rooms_query = Room.query.join(Hostel)
    if hostel_id:
        rooms_query = rooms_query.filter(Room.hostel_id == hostel_id)
    if room_type:
        rooms_query = rooms_query.filter(Room.room_type == room_type)
    if status:
        rooms_query = rooms_query.filter(Room.status == status)

    all_rooms = rooms_query.order_by(Hostel.hostel_name.asc(), Room.room_number.asc()).all()
    return render_template("admin/rooms.html", 
                           rooms=all_rooms, 
                           hostels=hostels, 
                           form=form,
                           selected_hostel=hostel_id,
                           selected_type=room_type,
                           selected_status=status)


@bp.route("/rooms/<int:room_id>/edit", methods=["POST"])
@login_required
@role_required("admin")
def edit_room(room_id):
    """Edit room details."""
    room = db.get_or_404(Room, room_id)
    room_number = request.form.get("room_number", "").strip()
    room_type = request.form.get("room_type")
    capacity = int(request.form.get("capacity", room.capacity))
    status = request.form.get("status")

    if capacity < room.occupied_count:
        flash(f"Capacity cannot be reduced below current occupancy ({room.occupied_count} beds).", "danger")
        return redirect(url_for("admin.rooms"))

    # Uniqueness check
    conflict = Room.query.filter(
        Room.hostel_id == room.hostel_id,
        Room.room_number == room_number,
        Room.id != room.id
    ).first()
    if conflict:
        flash(f"Room {room_number} already exists in this hostel.", "danger")
        return redirect(url_for("admin.rooms"))

    room.room_number = room_number
    room.room_type = room_type
    room.capacity = capacity
    # If capacity is fully occupied, set Full automatically
    if room.occupied_count >= room.capacity:
        room.status = "Full"
    else:
        room.status = status

    db.session.commit()
    flash(f"Room {room.room_number} updated successfully.", "success")
    return redirect(url_for("admin.rooms"))


@bp.route("/rooms/<int:room_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_room(room_id):
    """Delete room if unoccupied."""
    room = db.get_or_404(Room, room_id)
    if room.occupied_count > 0:
        flash(f"Cannot delete Room {room.room_number}: it currently has {room.occupied_count} allocated student(s).", "danger")
        return redirect(url_for("admin.rooms"))

    hostel = room.hostel
    if hostel and hostel.total_rooms > 0:
        hostel.total_rooms -= 1

    r_no = room.room_number
    db.session.delete(room)
    log = ActivityLog(user_id=current_user.id, action="Delete Room", details=f"Deleted room {r_no} from {hostel.hostel_name}")
    db.session.add(log)
    db.session.commit()

    flash(f"Room {r_no} deleted.", "info")
    return redirect(url_for("admin.rooms"))


# =========================================================================
# APPLICATIONS MANAGEMENT
# =========================================================================

@bp.route("/applications")
@login_required
@role_required("admin")
def applications():
    """Review, search and filter all hostel accommodation applications."""
    status_filter = request.args.get("status", "").strip()
    hostel_id = request.args.get("hostel_id", type=int)

    apps_query = Application.query.join(Student).join(User)
    if status_filter:
        apps_query = apps_query.filter(Application.status == status_filter)
    if hostel_id:
        apps_query = apps_query.filter(Application.preferred_hostel_id == hostel_id)

    all_apps = apps_query.order_by(Application.application_date.desc()).all()
    hostels = Hostel.query.all()
    decision_form = ApplicationDecisionForm()

    return render_template("admin/applications.html", 
                           applications=all_apps, 
                           hostels=hostels, 
                           selected_status=status_filter,
                           selected_hostel=hostel_id,
                           decision_form=decision_form)


@bp.route("/applications/<int:app_id>/decide", methods=["POST"])
@login_required
@role_required("admin")
def decide_application(app_id):
    """Approve or reject a student's accommodation application."""
    app_obj = db.get_or_404(Application, app_id)
    new_status = request.form.get("status")
    admin_remarks = request.form.get("admin_remarks", "").strip()

    if new_status not in ["Approved", "Rejected"]:
        flash("Invalid decision status.", "danger")
        return redirect(url_for("admin.applications"))

    if app_obj.status == "Allocated":
        flash("Cannot alter decision: this application is already allocated to a room.", "danger")
        return redirect(url_for("admin.applications"))

    app_obj.status = new_status
    app_obj.admin_remarks = admin_remarks

    log = ActivityLog(user_id=current_user.id, action="Application Decision", 
                      details=f"Application #{app_id} for {app_obj.student.registration_number} set to {new_status}")
    db.session.add(log)
    db.session.commit()

    flash(f"Application #{app_id} has been marked as '{new_status}'.", "success")
    return redirect(url_for("admin.applications"))


# =========================================================================
# ROOM ALLOCATION
# =========================================================================

@bp.route("/allocations", methods=["GET", "POST"])
@login_required
@role_required("admin")
def allocations():
    """Allocate rooms to approved students and manage active allocations."""
    # Approved applications awaiting room allocation
    approved_apps = Application.query.filter_by(status="Approved").order_by(Application.application_date.asc()).all()

    # Active allocations
    active_allocations = Allocation.query.filter(Allocation.status.in_(["Allocated", "Checked-In"]))\
        .order_by(Allocation.allocation_date.desc()).all()

    # Available rooms list (rooms with free beds and not in maintenance)
    available_rooms = Room.query.filter(
        Room.status != "Maintenance",
        Room.occupied_count < Room.capacity
    ).order_by(Room.hostel_id.asc(), Room.room_number.asc()).all()

    return render_template("admin/allocations.html",
                           approved_apps=approved_apps,
                           active_allocations=active_allocations,
                           available_rooms=available_rooms)


@bp.route("/allocations/allocate", methods=["POST"])
@login_required
@role_required("admin")
def allocate_room():
    """Executes atomic room allocation for an approved application."""
    app_id = request.form.get("application_id", type=int)
    room_id = request.form.get("room_id", type=int)

    if not app_id or not room_id:
        flash("Application ID and Room selection are required.", "danger")
        return redirect(url_for("admin.allocations"))

    # Database transaction with nested session for atomicity
    try:
        app_obj = db.get_or_404(Application, app_id)
        room = db.get_or_404(Room, room_id)
        student = app_obj.student

        # 1. Rule: Only approved applications can be allocated
        if app_obj.status != "Approved":
            flash("Only applications with 'Approved' status can be allocated a room.", "danger")
            return redirect(url_for("admin.allocations"))

        # 2. Rule: Student cannot have multiple active allocations
        if student.active_allocation:
            flash(f"Student {student.registration_number} already has an active allocation.", "danger")
            return redirect(url_for("admin.allocations"))

        # 3. Rule: Room capacity check
        if room.status == "Maintenance":
            flash(f"Room {room.room_number} is currently under maintenance.", "danger")
            return redirect(url_for("admin.allocations"))

        if room.occupied_count >= room.capacity:
            flash(f"Room {room.room_number} in {room.hostel.hostel_name} is already full.", "danger")
            return redirect(url_for("admin.allocations"))

        # 4. Perform atomic update
        room.occupied_count += 1
        if room.occupied_count >= room.capacity:
            room.status = "Full"

        app_obj.status = "Allocated"

        allocation = Allocation(
            student_id=student.id,
            room_id=room.id,
            application_id=app_obj.id,
            allocation_date=datetime.utcnow(),
            status="Allocated"
        )
        db.session.add(allocation)

        log = ActivityLog(
            user_id=current_user.id,
            action="Room Allocation",
            details=f"Allocated {student.registration_number} to {room.hostel.hostel_name} - Room {room.room_number}"
        )
        db.session.add(log)
        db.session.commit()

        flash(f"Room {room.room_number} ({room.hostel.hostel_name}) successfully allocated to {student.user.name} ({student.registration_number}).", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Transaction failed: {str(e)}", "danger")

    return redirect(url_for("admin.allocations"))


@bp.route("/allocations/<int:alloc_id>/cancel", methods=["POST"])
@login_required
@role_required("admin")
def cancel_allocation(alloc_id):
    """Cancels an active room allocation and releases the bed capacity."""
    alloc = db.get_or_404(Allocation, alloc_id)
    if alloc.status not in ["Allocated", "Checked-In"]:
        flash("Allocation is already inactive.", "warning")
        return redirect(url_for("admin.allocations"))

    try:
        room = alloc.room
        if room:
            room.occupied_count = max(0, room.occupied_count - 1)
            if room.status == "Full":
                room.status = "Available"

        alloc.status = "Cancelled"
        alloc.check_out_date = datetime.utcnow()

        if alloc.application:
            alloc.application.status = "Approved"  # revert to approved so it can be reallocated if needed

        log = ActivityLog(user_id=current_user.id, action="Cancel Allocation", 
                          details=f"Cancelled allocation #{alloc_id} for student {alloc.student.registration_number}")
        db.session.add(log)
        db.session.commit()

        flash("Allocation cancelled successfully and bed capacity released.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error cancelling allocation: {str(e)}", "danger")

    return redirect(url_for("admin.allocations"))


# =========================================================================
# WARDENS MANAGEMENT
# =========================================================================

@bp.route("/wardens", methods=["GET", "POST"])
@login_required
@role_required("admin")
def wardens():
    """List, create and assign wardens to hostels."""
    form = WardenForm()
    hostels = Hostel.query.all()
    form.assigned_hostel_id.choices = [(0, "Unassigned")] + [(h.id, h.hostel_name) for h in hostels]

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if existing_user:
            flash("A user with this email address already exists.", "danger")
        else:
            try:
                user = User(
                    name=form.name.data.strip(),
                    email=form.email.data.strip().lower(),
                    role="warden"
                )
                password = form.password.data if form.password.data else "warden123"
                user.set_password(password)
                db.session.add(user)
                db.session.flush()

                h_id = form.assigned_hostel_id.data if form.assigned_hostel_id.data != 0 else None
                warden = Warden(
                    user_id=user.id,
                    phone=form.phone.data.strip(),
                    assigned_hostel_id=h_id
                )
                db.session.add(warden)

                log = ActivityLog(user_id=current_user.id, action="Create Warden", details=f"Created warden {user.name}")
                db.session.add(log)
                db.session.commit()

                flash(f"Warden account created for {user.name}.", "success")
                return redirect(url_for("admin.wardens"))
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating warden: {str(e)}", "danger")

    all_wardens = Warden.query.all()
    return render_template("admin/wardens.html", wardens=all_wardens, hostels=hostels, form=form)


@bp.route("/wardens/<int:warden_id>/edit", methods=["POST"])
@login_required
@role_required("admin")
def edit_warden(warden_id):
    """Update warden assignment and details."""
    warden = db.get_or_404(Warden, warden_id)
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    h_id = request.form.get("assigned_hostel_id", type=int)

    if name:
        warden.user.name = name
    if phone:
        warden.phone = phone
    warden.assigned_hostel_id = h_id if h_id != 0 else None

    db.session.commit()
    flash(f"Warden {warden.user.name} details updated.", "success")
    return redirect(url_for("admin.wardens"))


@bp.route("/wardens/<int:warden_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_warden(warden_id):
    """Delete warden account."""
    warden = db.get_or_404(Warden, warden_id)
    user = warden.user
    db.session.delete(user)
    db.session.commit()
    flash("Warden account removed.", "info")
    return redirect(url_for("admin.wardens"))


# =========================================================================
# COMPLAINTS MANAGEMENT
# =========================================================================

@bp.route("/complaints")
@login_required
@role_required("admin")
def complaints():
    """View and oversee all student complaints across campus."""
    status_filter = request.args.get("status", "").strip()
    hostel_id = request.args.get("hostel_id", type=int)

    comps_query = Complaint.query.join(Student)
    if status_filter:
        comps_query = comps_query.filter(Complaint.status == status_filter)
    if hostel_id:
        comps_query = comps_query.filter(Complaint.hostel_id == hostel_id)

    all_comps = comps_query.order_by(Complaint.complaint_date.desc()).all()
    hostels = Hostel.query.all()
    return render_template("admin/complaints.html", 
                           complaints=all_comps, 
                           hostels=hostels,
                           selected_status=status_filter,
                           selected_hostel=hostel_id)


@bp.route("/complaints/<int:complaint_id>/update", methods=["POST"])
@login_required
@role_required("admin")
def update_complaint(complaint_id):
    """Admin update on complaint status and remarks."""
    comp = db.get_or_404(Complaint, complaint_id)
    new_status = request.form.get("status")
    remarks = request.form.get("warden_remarks", "").strip()

    if new_status in ["Open", "In Progress", "Resolved", "Closed"]:
        comp.status = new_status
    if remarks:
        comp.warden_remarks = remarks

    db.session.commit()
    flash(f"Complaint #{complaint_id} updated.", "success")
    return redirect(url_for("admin.complaints"))


# =========================================================================
# ANNOUNCEMENTS MANAGEMENT
# =========================================================================

@bp.route("/announcements", methods=["GET", "POST"])
@login_required
@role_required("admin")
def announcements():
    """Publish and manage announcements."""
    form = AnnouncementForm()
    hostels = Hostel.query.all()
    form.hostel_id.choices = [(0, "All Hostels (Campus-wide)")] + [(h.id, h.hostel_name) for h in hostels]

    if form.validate_on_submit():
        h_id = form.hostel_id.data if form.hostel_id.data != 0 else None
        ann = Announcement(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            hostel_id=h_id,
            created_by=current_user.id
        )
        db.session.add(ann)
        db.session.commit()
        flash("Announcement published successfully.", "success")
        return redirect(url_for("admin.announcements"))

    all_anns = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template("admin/announcements.html", announcements=all_anns, hostels=hostels, form=form)


@bp.route("/announcements/<int:ann_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_announcement(ann_id):
    """Remove published announcement."""
    ann = db.get_or_404(Announcement, ann_id)
    db.session.delete(ann)
    db.session.commit()
    flash("Announcement deleted.", "info")
    return redirect(url_for("admin.announcements"))


# =========================================================================
# REPORTS & ANALYTICS
# =========================================================================

@bp.route("/reports")
@login_required
@role_required("admin")
def reports():
    """Generate institutional reports, occupancy summaries, and CSV exports."""
    hostels = Hostel.query.all()
    all_rooms = Room.query.all()
    allocations = Allocation.query.filter(Allocation.status.in_(["Allocated", "Checked-In"])).all()
    complaints = Complaint.query.all()
    
    return render_template("admin/reports.html", 
                           hostels=hostels, 
                           rooms=all_rooms, 
                           allocations=allocations,
                           complaints=complaints)


@bp.route("/reports/export/<report_type>")
@login_required
@role_required("admin")
def export_csv(report_type):
    """Download system data as CSV spreadsheets."""
    si = io.StringIO()
    writer = csv.writer(si)

    if report_type == "occupancy":
        writer.writerow(["Hostel Name", "Hostel Type", "Total Rooms", "Total Capacity", "Occupied Beds", "Available Beds", "Occupancy Rate %"])
        for h in Hostel.query.all():
            rate = round((h.total_occupied / h.total_capacity * 100), 1) if h.total_capacity > 0 else 0
            writer.writerow([h.hostel_name, h.hostel_type, h.total_rooms, h.total_capacity, h.total_occupied, h.free_beds, f"{rate}%"])
        filename = f"hostel_occupancy_report_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    elif report_type == "students":
        writer.writerow(["Registration No", "Full Name", "Email", "Phone", "Department", "Year", "Gender", "Allocated Hostel", "Room No", "Status"])
        for s in Student.query.all():
            alloc = s.active_allocation
            h_name = alloc.room.hostel.hostel_name if alloc and alloc.room else "Unallocated"
            r_no = alloc.room.room_number if alloc and alloc.room else "-"
            st = alloc.status if alloc else "Not Allocated"
            writer.writerow([s.registration_number, s.user.name, s.user.email, s.phone, s.department, s.academic_year, s.gender, h_name, r_no, st])
        filename = f"student_allocations_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    elif report_type == "rooms":
        writer.writerow(["Hostel", "Room Number", "Room Type", "Bed Capacity", "Occupied Beds", "Free Beds", "Status"])
        for r in Room.query.join(Hostel).all():
            writer.writerow([r.hostel.hostel_name, r.room_number, r.room_type, r.capacity, r.occupied_count, r.free_beds, r.status])
        filename = f"room_inventory_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    else:
        abort(404)

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output


@bp.route("/settings", methods=["GET", "POST"])
@login_required
@role_required("admin")
def settings():
    """Institutional system settings and audit configuration."""
    form = SettingsForm()

    default_settings = {
        "institution_name": "National College of Engineering & Technology",
        "academic_year": "2026-2027",
        "intake_status": "Open",
        "curfew_hours": "10:00 PM",
        "contact_email": "residential@college.edu",
        "emergency_phone": "+91 (080) 2855-4300 / Ext 412",
        "complaint_sla_days": "3",
        "max_room_transfers": "1",
    }

    if request.method == "GET":
        form.institution_name.data = SystemSetting.get_val("institution_name", default_settings["institution_name"])
        form.academic_year.data = SystemSetting.get_val("academic_year", default_settings["academic_year"])
        form.intake_status.data = SystemSetting.get_val("intake_status", default_settings["intake_status"])
        form.curfew_hours.data = SystemSetting.get_val("curfew_hours", default_settings["curfew_hours"])
        form.contact_email.data = SystemSetting.get_val("contact_email", default_settings["contact_email"])
        form.emergency_phone.data = SystemSetting.get_val("emergency_phone", default_settings["emergency_phone"])
        form.complaint_sla_days.data = int(SystemSetting.get_val("complaint_sla_days", default_settings["complaint_sla_days"]))
        form.max_room_transfers.data = int(SystemSetting.get_val("max_room_transfers", default_settings["max_room_transfers"]))

    if form.validate_on_submit():
        SystemSetting.set_val("institution_name", form.institution_name.data.strip())
        SystemSetting.set_val("academic_year", form.academic_year.data.strip())
        SystemSetting.set_val("intake_status", form.intake_status.data)
        SystemSetting.set_val("curfew_hours", form.curfew_hours.data.strip())
        SystemSetting.set_val("contact_email", form.contact_email.data.strip())
        SystemSetting.set_val("emergency_phone", form.emergency_phone.data.strip())
        SystemSetting.set_val("complaint_sla_days", str(form.complaint_sla_days.data))
        SystemSetting.set_val("max_room_transfers", str(form.max_room_transfers.data))

        log = ActivityLog(user_id=current_user.id, action="Settings Updated",
                          details=f"Institutional preferences updated (Term {form.academic_year.data}, Intake {form.intake_status.data})")
        db.session.add(log)
        db.session.commit()
        flash("Institutional system settings have been saved successfully.", "success")
        return redirect(url_for("admin.settings"))

    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(12).all()
    stats = {
        "users": User.query.count(),
        "students": Student.query.count(),
        "wardens": Warden.query.count(),
        "hostels": Hostel.query.count(),
        "rooms": Room.query.count(),
        "applications": Application.query.count(),
        "allocations": Allocation.query.count(),
        "complaints": Complaint.query.count(),
        "announcements": Announcement.query.count()
    }
    db_engine = db.engine.name.upper()

    return render_template("admin/settings.html", form=form, recent_logs=recent_logs, stats=stats, db_engine=db_engine)


# =========================================================================
# LIVE DATABASE SHEET INTERFACE & API (ADMIN - FULL ACCESS)
# =========================================================================

@bp.route("/sheets")
@login_required
@role_required("admin")
def sheets():
    """Live interactive spreadsheet view where all database information is visible and editable."""
    return render_template("admin/sheets.html")


@bp.route("/api/sheet/data")
@login_required
@role_required("admin")
def sheet_data():
    """Returns live JSON records for all database tables."""
    return jsonify({
        "students": [s.to_dict() for s in Student.query.join(User).all()],
        "hostels": [h.to_dict() for h in Hostel.query.all()],
        "rooms": [r.to_dict() for r in Room.query.join(Hostel).all()],
        "applications": [a.to_dict() for a in Application.query.all()],
        "allocations": [al.to_dict() for al in Allocation.query.all()],
        "complaints": [c.to_dict() for c in Complaint.query.all()],
        "wardens": [w.to_dict() for w in Warden.query.all()]
    })


@bp.route("/api/sheet/update", methods=["POST"])
@login_required
@role_required("admin")
def sheet_update():
    """Inline cell update endpoint for the live administrative database sheet."""
    data = request.get_json() or {}
    table = data.get("table")
    record_id = data.get("id")
    field = data.get("field")
    value = data.get("value")

    if not table or not record_id or not field:
        return jsonify({"success": False, "error": "Missing required update parameters."}), 400

    try:
        if table == "students":
            student = db.session.get(Student, record_id)
            if not student:
                return jsonify({"success": False, "error": "Student record not found."}), 404
            
            if field == "name":
                student.user.name = str(value).strip()
            elif field == "phone":
                student.phone = str(value).strip()
            elif field == "department":
                student.department = str(value).strip()
            elif field == "academic_year":
                student.academic_year = int(value)
            elif field == "gender":
                student.gender = str(value)
            elif field == "address":
                student.address = str(value).strip()
            elif field == "registration_number":
                student.registration_number = str(value).strip().upper()

        elif table == "hostels":
            hostel = db.session.get(Hostel, record_id)
            if not hostel:
                return jsonify({"success": False, "error": "Hostel not found."}), 404
            if field == "hostel_name":
                hostel.hostel_name = str(value).strip()
            elif field == "hostel_type":
                hostel.hostel_type = str(value)
            elif field == "address":
                hostel.address = str(value).strip()
            elif field == "description":
                hostel.description = str(value).strip()

        elif table == "rooms":
            room = db.session.get(Room, record_id)
            if not room:
                return jsonify({"success": False, "error": "Room not found."}), 404
            if field == "room_number":
                room.room_number = str(value).strip()
            elif field == "room_type":
                room.room_type = str(value)
            elif field == "capacity":
                val = int(value)
                if val < room.occupied_count:
                    return jsonify({"success": False, "error": "Capacity cannot be less than current occupancy."}), 400
                room.capacity = val
                if room.occupied_count >= room.capacity:
                    room.status = "Full"
            elif field == "status":
                room.status = str(value)

        elif table == "complaints":
            comp = db.session.get(Complaint, record_id)
            if not comp:
                return jsonify({"success": False, "error": "Complaint not found."}), 404
            if field == "status":
                comp.status = str(value)
            elif field == "warden_remarks":
                comp.warden_remarks = str(value).strip()

        elif table == "applications":
            app_obj = db.session.get(Application, record_id)
            if not app_obj:
                return jsonify({"success": False, "error": "Application not found."}), 404
            if field == "status":
                app_obj.status = str(value)
            elif field == "admin_remarks":
                app_obj.admin_remarks = str(value).strip()

        else:
            return jsonify({"success": False, "error": f"Table '{table}' is not editable via live sheet."}), 400

        db.session.commit()
        return jsonify({"success": True, "message": "Updated successfully."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
