"""Flask-WTF Forms for Hostel Allocation and Management System."""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SelectField,
    TextAreaField, IntegerField, SubmitField, HiddenField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional
)
from app.models import User, Student, Hostel, Room


class LoginForm(FlaskForm):
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class StudentRegistrationForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=3, max=100)])
    registration_number = StringField("Registration Number", validators=[DataRequired(), Length(min=4, max=30)])
    email = StringField("College Email", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=15)])
    department = StringField("Department", validators=[DataRequired(), Length(max=100)])
    academic_year = SelectField("Academic Year", choices=[
        ("1", "1st Year"), ("2", "2nd Year"), ("3", "3rd Year"), ("4", "4th Year")
    ], coerce=int, validators=[DataRequired()])
    gender = SelectField("Gender", choices=[
        ("Male", "Male"), ("Female", "Female"), ("Other", "Other")
    ], validators=[DataRequired()])
    address = TextAreaField("Permanent Address", validators=[Optional(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters.")])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(), EqualTo("password", message="Passwords must match.")
    ])
    submit = SubmitField("Register Account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("An account with this email address already exists.")

    def validate_registration_number(self, field):
        if Student.query.filter_by(registration_number=field.data.strip().upper()).first():
            raise ValidationError("This registration number is already registered.")


class StudentProfileForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=3, max=100)])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=15)])
    department = StringField("Department", validators=[DataRequired(), Length(max=100)])
    academic_year = SelectField("Academic Year", choices=[
        ("1", "1st Year"), ("2", "2nd Year"), ("3", "3rd Year"), ("4", "4th Year")
    ], coerce=int, validators=[DataRequired()])
    address = TextAreaField("Address", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Update Profile")


class HostelApplicationForm(FlaskForm):
    preferred_hostel_id = SelectField("Preferred Hostel", coerce=int, validators=[DataRequired()])
    preferred_room_type = SelectField("Preferred Room Type", choices=[
        ("Single", "Single Room (1 Bed)"),
        ("Double", "Double Sharing (2 Beds)"),
        ("Triple", "Triple Sharing (3 Beds)"),
        ("Dormitory", "Dormitory (4-6 Beds)")
    ], validators=[DataRequired()])
    submit = SubmitField("Submit Accommodation Application")


class ComplaintForm(FlaskForm):
    complaint_title = StringField("Complaint Subject", validators=[DataRequired(), Length(min=5, max=150)])
    description = TextAreaField("Detailed Description", validators=[DataRequired(), Length(min=10)])
    hostel_id = SelectField("Hostel", coerce=int, validators=[Optional()])
    submit = SubmitField("Submit Complaint")


class WardenComplaintForm(FlaskForm):
    status = SelectField("Resolution Status", choices=[
        ("Open", "Open"),
        ("In Progress", "In Progress"),
        ("Resolved", "Resolved"),
        ("Closed", "Closed")
    ], validators=[DataRequired()])
    warden_remarks = TextAreaField("Warden Remarks / Action Taken", validators=[Length(max=255)])
    submit = SubmitField("Update Complaint")


class HostelForm(FlaskForm):
    hostel_name = StringField("Hostel Name", validators=[DataRequired(), Length(max=100)])
    hostel_type = SelectField("Hostel Type", choices=[
        ("Boys", "Boys Hostel"),
        ("Girls", "Girls Hostel"),
        ("Co-ed", "Co-ed / Post Graduate")
    ], validators=[DataRequired()])
    address = StringField("Campus Location / Address", validators=[DataRequired(), Length(max=255)])
    description = TextAreaField("Hostel Description & Facilities", validators=[Optional()])
    submit = SubmitField("Save Hostel")


class RoomForm(FlaskForm):
    hostel_id = SelectField("Hostel", coerce=int, validators=[DataRequired()])
    room_number = StringField("Room Number", validators=[DataRequired(), Length(max=10)])
    room_type = SelectField("Room Type", choices=[
        ("Single", "Single"),
        ("Double", "Double"),
        ("Triple", "Triple"),
        ("Dormitory", "Dormitory")
    ], validators=[DataRequired()])
    capacity = IntegerField("Bed Capacity", validators=[DataRequired(), NumberRange(min=1, max=12)])
    status = SelectField("Room Status", choices=[
        ("Available", "Available"),
        ("Maintenance", "Under Maintenance")
    ], validators=[DataRequired()])
    submit = SubmitField("Save Room")


class WardenForm(FlaskForm):
    name = StringField("Warden Full Name", validators=[DataRequired(), Length(min=3, max=100)])
    email = StringField("Email Address", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField("Password", validators=[Optional(), Length(min=6)])
    assigned_hostel_id = SelectField("Assigned Hostel", coerce=int, validators=[Optional()])
    submit = SubmitField("Save Warden")


class AnnouncementForm(FlaskForm):
    title = StringField("Announcement Title", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("Announcement Details", validators=[DataRequired()])
    hostel_id = SelectField("Audience / Hostel", coerce=int, validators=[Optional()])
    submit = SubmitField("Publish Announcement")


class AllocationForm(FlaskForm):
    application_id = HiddenField("Application ID", validators=[DataRequired()])
    room_id = SelectField("Select Room", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Allocate Room")


class ApplicationDecisionForm(FlaskForm):
    status = SelectField("Decision", choices=[
        ("Approved", "Approve Application"),
        ("Rejected", "Reject Application")
    ], validators=[DataRequired()])
    admin_remarks = TextAreaField("Admin Remarks / Reason", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Submit Decision")


class SettingsForm(FlaskForm):
    institution_name = StringField("Institution Name", validators=[DataRequired(), Length(max=150)])
    academic_year = StringField("Academic Year", validators=[DataRequired(), Length(max=20)])
    intake_status = SelectField("Hostel Intake Status", choices=[
        ("Open", "Open for Applications"),
        ("Closed", "Intake Closed")
    ], validators=[DataRequired()])
    curfew_hours = StringField("Curfew / Gate Closing Time", validators=[DataRequired(), Length(max=20)])
    contact_email = StringField("Administrative Contact Email", validators=[DataRequired(), Email(), Length(max=120)])
    emergency_phone = StringField("Emergency / Warden Helpdesk Phone", validators=[DataRequired(), Length(max=30)])
    complaint_sla_days = IntegerField("Complaint Resolution SLA (Days)", validators=[DataRequired(), NumberRange(min=1, max=30)])
    max_room_transfers = IntegerField("Max Room Transfers Allowed", validators=[DataRequired(), NumberRange(min=0, max=5)])
    submit = SubmitField("Save Institutional Settings")


