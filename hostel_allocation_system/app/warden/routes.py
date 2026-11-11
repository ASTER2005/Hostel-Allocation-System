"""Warden Portal routes: hostel supervision, check-in/out,
room occupancy monitoring, complaint resolution, and hostel-scoped live sheet editing.
"""
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.auth.decorators import role_required
from app.models import (
    Warden, Hostel, Room, Allocation, Student, Complaint, Announcement, ActivityLog
)
from app.forms import WardenComplaintForm, AnnouncementForm
from . import bp


def get_current_warden():
    """Retrieves the Warden record and assigned hostel for current_user."""
    warden = Warden.query.filter_by(user_id=current_user.id).first()
    if not warden:
        abort(404, description="Warden profile not found.")
    return warden


@bp.route("/")
@bp.route("/overview")
@login_required
@role_required("warden")
def overview():
    """Warden dashboard overview showing assigned hostel statistics and occupancy."""
    warden = get_current_warden()
    hostel = warden.hostel

    if not hostel:
        return render_template("warden/unassigned.html", warden=warden)

    rooms = hostel.rooms.all()
    total_rooms = len(rooms)
    total_capacity = sum(r.capacity for r in rooms)
    occupied_beds = sum(r.occupied_count for r in rooms)
    free_beds = max(0, total_capacity - occupied_beds)

    # Active allocations in warden's hostel
    active_allocs = Allocation.query.join(Room).filter(
        Room.hostel_id == hostel.id,
        Allocation.status.in_(["Allocated", "Checked-In"])
    ).all()
    checked_in_count = sum(1 for a in active_allocs if a.status == "Checked-In")
    pending_checkin_count = sum(1 for a in active_allocs if a.status == "Allocated")

    # Complaints for warden's hostel
    hostel_complaints = Complaint.query.filter_by(hostel_id=hostel.id)
    open_complaints = hostel_complaints.filter(Complaint.status.in_(["Open", "In Progress"])).count()
    recent_complaints = hostel_complaints.order_by(Complaint.complaint_date.desc()).limit(5).all()

    # Announcements
    announcements = Announcement.query.filter(
        (Announcement.hostel_id == None) | (Announcement.hostel_id == hostel.id)
    ).order_by(Announcement.created_at.desc()).limit(5).all()

    return render_template("warden/dashboard.html",
                           warden=warden,
                           hostel=hostel,
                           total_rooms=total_rooms,
                           total_capacity=total_capacity,
                           occupied_beds=occupied_beds,
                           free_beds=free_beds,
                           checked_in_count=checked_in_count,
                           pending_checkin_count=pending_checkin_count,
                           open_complaints=open_complaints,
                           recent_complaints=recent_complaints,
                           announcements=announcements)


@bp.route("/my-hostel")
@login_required
@role_required("warden")
def my_hostel():
    """Detailed view of the warden's assigned hostel, blocks, and rules."""
    warden = get_current_warden()
    hostel = warden.hostel
    if not hostel:
        return render_template("warden/unassigned.html", warden=warden)

    rooms = hostel.rooms.all()
    return render_template("warden/my_hostel.html", warden=warden, hostel=hostel, rooms=rooms)


@bp.route("/occupancy")
@login_required
@role_required("warden")
def occupancy():
    """Monitor room-by-room bed occupancy and student occupant lists."""
    warden = get_current_warden()
    hostel = warden.hostel
    if not hostel:
        return render_template("warden/unassigned.html", warden=warden)

    status_filter = request.args.get("status", "").strip()
    rooms_query = hostel.rooms
    if status_filter:
        rooms_query = rooms_query.filter(Room.status == status_filter)

    rooms = rooms_query.order_by(Room.room_number.asc()).all()

    # Pre-fetch occupants per room
    room_occupants = {}
    for r in rooms:
        allocs = r.allocations.filter(Allocation.status.in_(["Allocated", "Checked-In"])).all()
        room_occupants[r.id] = [a.student for a in allocs]

    return render_template("warden/occupancy.html", 
                           hostel=hostel, 
                           rooms=rooms, 
                           room_occupants=room_occupants, 
                           selected_status=status_filter)


@bp.route("/students")
@login_required
@role_required("warden")
def students():
    """Roster of allocated and resident students in this hostel."""
    warden = get_current_warden()
    hostel = warden.hostel
    if not hostel:
        return render_template("warden/unassigned.html", warden=warden)

    query = request.args.get("q", "").strip()
    allocs_query = Allocation.query.join(Room).filter(
        Room.hostel_id == hostel.id,
        Allocation.status.in_(["Allocated", "Checked-In"])
    )

    if query:
        search_filter = f"%{query}%"
        allocs_query = allocs_query.join(Student).join(User).filter(
            (User.name.ilike(search_filter)) |
            (Student.registration_number.ilike(search_filter)) |
            (Room.room_number.ilike(search_filter)) |
            (Student.department.ilike(search_filter))
        )

    allocations = allocs_query.order_by(Room.room_number.asc()).all()
    return render_template("warden/students.html", hostel=hostel, allocations=allocations, query=query)


@bp.route("/checkin")
@login_required
@role_required("warden")
def checkin():
    """Check-in and Check-out management for residents."""
    warden = get_current_warden()
    hostel = warden.hostel
    if not hostel:
        return render_template("warden/unassigned.html", warden=warden)

    active_allocs = Allocation.query.join(Room).filter(
        Room.hostel_id == hostel.id,
        Allocation.status.in_(["Allocated", "Checked-In"])
    ).order_by(Allocation.status.asc(), Room.room_number.asc()).all()

    recent_checkouts = Allocation.query.join(Room).filter(
        Room.hostel_id == hostel.id,
        Allocation.status == "Checked-Out"
    ).order_by(Allocation.check_out_date.desc()).limit(10).all()

    return render_template("warden/checkin.html", 
                           hostel=hostel, 
                           allocations=active_allocs, 
                           recent_checkouts=recent_checkouts)


@bp.route("/checkin/<int:alloc_id>/action", methods=["POST"])
@login_required
@role_required("warden")
def process_checkin_checkout(alloc_id):
    """Process physical arrival (Check-in) or departure (Check-out releasing bed capacity)."""
    warden = get_current_warden()
    alloc = db.get_or_404(Allocation, alloc_id)

    # Security check: verify allocation belongs to warden's hostel
    if alloc.room.hostel_id != warden.assigned_hostel_id:
        abort(403, description="Access forbidden: allocation not in your assigned hostel.")

    action = request.form.get("action")
    try:
        if action == "checkin":
            alloc.status = "Checked-In"
            alloc.check_in_date = datetime.utcnow()
            log_desc = f"Checked in student {alloc.student.registration_number} into Room {alloc.room.room_number}"
            flash(f"Student {alloc.student.user.name} checked in successfully.", "success")

        elif action == "checkout":
            alloc.status = "Checked-Out"
            alloc.check_out_date = datetime.utcnow()
            
            # Release bed capacity immediately
            room = alloc.room
            room.occupied_count = max(0, room.occupied_count - 1)
            if room.status == "Full":
                room.status = "Available"

            log_desc = f"Checked out student {alloc.student.registration_number} from Room {alloc.room.room_number}. Bed released."
            flash(f"Student {alloc.student.user.name} checked out. Room {room.room_number} bed capacity released.", "info")
        else:
            flash("Invalid check-in/out action.", "danger")
            return redirect(url_for("warden.checkin"))

        log = ActivityLog(user_id=current_user.id, action="Warden Check-in/out", details=log_desc)
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Transaction failed: {str(e)}", "danger")

    return redirect(url_for("warden.checkin"))


@bp.route("/complaints")
@login_required
@role_required("warden")
def complaints():
    """Handle and resolve complaints filed by students in this hostel."""
    warden = get_current_warden()
    hostel = warden.hostel
    if not hostel:
        return render_template("warden/unassigned.html", warden=warden)

    status_filter = request.args.get("status", "").strip()
    comps_query = Complaint.query.filter_by(hostel_id=hostel.id)
    if status_filter:
        comps_query = comps_query.filter(Complaint.status == status_filter)

    all_comps = comps_query.order_by(Complaint.complaint_date.desc()).all()
    form = WardenComplaintForm()

    return render_template("warden/complaints.html", 
                           hostel=hostel, 
                           complaints=all_comps, 
                           form=form, 
                           selected_status=status_filter)


@bp.route("/complaints/<int:complaint_id>/update", methods=["POST"])
@login_required
@role_required("warden")
def update_complaint(complaint_id):
    """Update complaint status and provide warden remarks."""
    warden = get_current_warden()
    comp = db.get_or_404(Complaint, complaint_id)

    # Security check: must match warden's hostel
    if comp.hostel_id != warden.assigned_hostel_id:
        abort(403, description="Cannot update complaints outside your assigned hostel.")

    new_status = request.form.get("status")
    remarks = request.form.get("warden_remarks", "").strip()

    if new_status in ["Open", "In Progress", "Resolved", "Closed"]:
        comp.status = new_status
    if remarks:
        comp.warden_remarks = remarks

    log = ActivityLog(user_id=current_user.id, action="Update Complaint", 
                      details=f"Warden updated complaint #{comp.id} to {comp.status}")
    db.session.add(log)
    db.session.commit()

    flash(f"Complaint #{comp.id} updated successfully.", "success")
    return redirect(url_for("warden.complaints"))


@bp.route("/announcements", methods=["GET", "POST"])
@login_required
@role_required("warden")
def announcements():
    """View campus notices and publish announcements for this hostel."""
    warden = get_current_warden()
    hostel = warden.hostel
    if not hostel:
        return render_template("warden/unassigned.html", warden=warden)

    form = AnnouncementForm()
    # Lock audience to warden's hostel
    form.hostel_id.choices = [(hostel.id, f"{hostel.hostel_name} (My Hostel)")]

    if form.validate_on_submit():
        ann = Announcement(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            hostel_id=hostel.id,
            created_by=current_user.id
        )
        db.session.add(ann)
        db.session.commit()
        flash(f"Announcement published for {hostel.hostel_name}.", "success")
        return redirect(url_for("warden.announcements"))

    all_anns = Announcement.query.filter(
        (Announcement.hostel_id == None) | (Announcement.hostel_id == hostel.id)
    ).order_by(Announcement.created_at.desc()).all()

    return render_template("warden/announcements.html", hostel=hostel, announcements=all_anns, form=form)


# =========================================================================
# WARDEN LIVE DATABASE SHEET (SCOPED STRICTLY TO ASSIGNED HOSTEL)
# =========================================================================

@bp.route("/sheets")
@login_required
@role_required("warden")
def sheets():
    """Live interactive spreadsheet view restricted strictly to the warden's assigned hostel."""
    warden = get_current_warden()
    hostel = warden.hostel
    if not hostel:
        return render_template("warden/unassigned.html", warden=warden)
    return render_template("warden/sheets.html", hostel=hostel)


@bp.route("/api/sheet/data")
@login_required
@role_required("warden")
def sheet_data():
    """Returns live JSON records scoped strictly to warden's assigned hostel."""
    warden = get_current_warden()
    hostel = warden.hostel
    if not hostel:
        return jsonify({"error": "No hostel assigned."}), 400

    rooms = Room.query.filter_by(hostel_id=hostel.id).order_by(Room.room_number.asc()).all()
    allocs = Allocation.query.join(Room).filter(
        Room.hostel_id == hostel.id,
        Allocation.status.in_(["Allocated", "Checked-In", "Checked-Out"])
    ).all()
    comps = Complaint.query.filter_by(hostel_id=hostel.id).order_by(Complaint.complaint_date.desc()).all()

    return jsonify({
        "hostel_name": hostel.hostel_name,
        "rooms": [r.to_dict() for r in rooms],
        "allocations": [a.to_dict() for a in allocs],
        "complaints": [c.to_dict() for c in comps]
    })


@bp.route("/api/sheet/update", methods=["POST"])
@login_required
@role_required("warden")
def sheet_update():
    """Warden inline update endpoint with strict authorization check on assigned hostel."""
    warden = get_current_warden()
    hostel = warden.hostel
    if not hostel:
        return jsonify({"success": False, "error": "No hostel assigned."}), 403

    data = request.get_json() or {}
    table = data.get("table")
    record_id = data.get("id")
    field = data.get("field")
    value = data.get("value")

    try:
        if table == "rooms":
            room = db.session.get(Room, record_id)
            if not room or room.hostel_id != hostel.id:
                return jsonify({"success": False, "error": "Access denied: Room is outside your assigned hostel."}), 403

            if field == "status":
                room.status = str(value)
            elif field == "capacity":
                val = int(value)
                if val < room.occupied_count:
                    return jsonify({"success": False, "error": "Capacity cannot be less than current occupancy."}), 400
                room.capacity = val
                if room.occupied_count >= room.capacity:
                    room.status = "Full"
            else:
                return jsonify({"success": False, "error": "Field not editable by warden."}), 403

        elif table == "complaints":
            comp = db.session.get(Complaint, record_id)
            if not comp or comp.hostel_id != hostel.id:
                return jsonify({"success": False, "error": "Access denied: Complaint is outside your assigned hostel."}), 403

            if field == "status":
                comp.status = str(value)
            elif field == "warden_remarks":
                comp.warden_remarks = str(value).strip()

        elif table == "allocations":
            alloc = db.session.get(Allocation, record_id)
            if not alloc or alloc.room.hostel_id != hostel.id:
                return jsonify({"success": False, "error": "Access denied: Allocation is outside your assigned hostel."}), 403

            if field == "status":
                new_status = str(value)
                if new_status == "Checked-In" and alloc.status == "Allocated":
                    alloc.status = "Checked-In"
                    alloc.check_in_date = datetime.utcnow()
                elif new_status == "Checked-Out" and alloc.status in ["Allocated", "Checked-In"]:
                    alloc.status = "Checked-Out"
                    alloc.check_out_date = datetime.utcnow()
                    alloc.room.occupied_count = max(0, alloc.room.occupied_count - 1)
                    if alloc.room.status == "Full":
                        alloc.room.status = "Available"
                else:
                    return jsonify({"success": False, "error": "Invalid allocation status transition."}), 400

        else:
            return jsonify({"success": False, "error": "Table not accessible."}), 403

        db.session.commit()
        return jsonify({"success": True, "message": "Updated successfully."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
