"""Authentication routes for login, logout, registration and public landing pages."""
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Student, Hostel, Room, ActivityLog
from app.forms import LoginForm, StudentRegistrationForm
from . import bp


@bp.route("/")
def landing():
    """Public landing page showcasing campus hostels, 3D architectural viewer, and features."""
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.overview"))
        elif current_user.role == "warden":
            return redirect(url_for("warden.overview"))
        else:
            return redirect(url_for("student.overview"))

    hostels = Hostel.query.all()
    total_students = Student.query.count()
    total_rooms = Room.query.count()
    total_capacity = sum(r.capacity for r in Room.query.all()) if total_rooms else 0
    return render_template("auth/landing.html", 
                           hostels=hostels,
                           total_students=total_students,
                           total_rooms=total_rooms,
                           total_capacity=total_capacity)


@bp.route("/about")
def about():
    """About System page describing institutional policies, allocation procedure and rules."""
    return render_template("auth/about.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Unified secure sign in for Students, Wardens, and Administrators."""
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.overview"))
        elif current_user.role == "warden":
            return redirect(url_for("warden.overview"))
        else:
            return redirect(url_for("student.overview"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=form.remember_me.data)
            
            # Log successful login activity
            log = ActivityLog(user_id=user.id, action="User Login", details=f"Logged in as {user.role}")
            db.session.add(log)
            db.session.commit()

            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
                
            if user.role == "admin":
                return redirect(url_for("admin.overview"))
            elif user.role == "warden":
                return redirect(url_for("warden.overview"))
            else:
                return redirect(url_for("student.overview"))
        else:
            flash("Invalid email address or password. Please try again.", "danger")

    return render_template("auth/login.html", form=form)


@bp.route("/demo-login/<role>")
def demo_login(role):
    """Convenient one-click sign in for demonstration and academic assessment."""
    role_email_map = {
        "admin": "admin@college.edu",
        "warden": "warden1@college.edu",
        "warden2": "warden2@college.edu",
        "student": "student@college.edu",
        "student-approved": "priya@college.edu",
        "student-allocated": "aman@college.edu"
    }
    target_email = role_email_map.get(role.lower())
    if not target_email:
        flash("Unknown demo account role.", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=target_email).first()
    if user:
        login_user(user)
        flash(f"Signed in as Demo {user.role.capitalize()}: {user.name}", "info")
        if user.role == "admin":
            return redirect(url_for("admin.overview"))
        elif user.role == "warden":
            return redirect(url_for("warden.overview"))
        else:
            return redirect(url_for("student.overview"))
    else:
        flash("Demo account not found in database. Please run database seeding.", "danger")
        return redirect(url_for("auth.login"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Student registration route with full validation and password hashing."""
    if current_user.is_authenticated:
        return redirect(url_for("auth.landing"))

    form = StudentRegistrationForm()
    if form.validate_on_submit():
        try:
            # Create user credential record
            user = User(
                name=form.name.data.strip(),
                email=form.email.data.strip().lower(),
                role="student"
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()  # obtain user.id

            # Create linked student profile
            student = Student(
                user_id=user.id,
                registration_number=form.registration_number.data.strip().upper(),
                phone=form.phone.data.strip(),
                department=form.department.data.strip(),
                academic_year=form.academic_year.data,
                gender=form.gender.data,
                address=form.address.data.strip() if form.address.data else ""
            )
            db.session.add(student)

            # Log registration
            log = ActivityLog(user_id=user.id, action="Student Registration", 
                              details=f"New student account created: {student.registration_number}")
            db.session.add(log)
            db.session.commit()

            flash("Registration successful! You may now sign in with your credentials.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred during registration: {str(e)}", "danger")

    return render_template("auth/register.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    """Secure logout for active sessions."""
    log = ActivityLog(user_id=current_user.id, action="User Logout", details=f"{current_user.name} logged out")
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash("You have been signed out securely.", "info")
    return redirect(url_for("auth.login"))
