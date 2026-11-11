-- Hostel Allocation and Management System - MySQL 8.0.16+ schema
CREATE DATABASE IF NOT EXISTS hostel_db CHARACTER SET utf8mb4;
USE hostel_db;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('student','warden','admin') NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hostels (
  id INT AUTO_INCREMENT PRIMARY KEY,
  hostel_name VARCHAR(100) NOT NULL UNIQUE,
  hostel_type ENUM('Boys','Girls','Co-ed') NOT NULL,
  address VARCHAR(255) NOT NULL,
  total_rooms INT NOT NULL DEFAULT 0,
  description TEXT
);

CREATE TABLE students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  registration_number VARCHAR(30) NOT NULL UNIQUE,
  phone VARCHAR(15) NOT NULL,
  department VARCHAR(100) NOT NULL,
  academic_year TINYINT NOT NULL,
  gender ENUM('Male','Female','Other') NOT NULL,
  address VARCHAR(255),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE wardens (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  phone VARCHAR(15) NOT NULL,
  assigned_hostel_id INT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (assigned_hostel_id) REFERENCES hostels(id) ON DELETE SET NULL
);

CREATE TABLE rooms (
  id INT AUTO_INCREMENT PRIMARY KEY,
  hostel_id INT NOT NULL,
  room_number VARCHAR(10) NOT NULL,
  room_type ENUM('Single','Double','Triple','Dormitory') NOT NULL,
  capacity TINYINT NOT NULL,
  occupied_count TINYINT NOT NULL DEFAULT 0,
  status ENUM('Available','Full','Maintenance') NOT NULL DEFAULT 'Available',
  UNIQUE (hostel_id, room_number),                      -- no duplicate rooms
  CHECK (capacity > 0),
  CHECK (occupied_count >= 0 AND occupied_count <= capacity), -- never exceed capacity
  FOREIGN KEY (hostel_id) REFERENCES hostels(id) ON DELETE CASCADE
);

CREATE TABLE applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  preferred_hostel_id INT NOT NULL,
  preferred_room_type ENUM('Single','Double','Triple','Dormitory') NOT NULL,
  application_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status ENUM('Pending','Approved','Rejected','Allocated','Cancelled') NOT NULL DEFAULT 'Pending',
  admin_remarks VARCHAR(255),
  -- Generated column: holds student_id only while the application is "active".
  -- UNIQUE on it => the DATABASE itself blocks two active applications per student.
  active_student_id INT GENERATED ALWAYS AS
    (CASE WHEN status IN ('Pending','Approved') THEN student_id END) STORED,
  UNIQUE (active_student_id),
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  FOREIGN KEY (preferred_hostel_id) REFERENCES hostels(id)
);

CREATE TABLE allocations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  room_id INT NOT NULL,
  application_id INT NULL,
  allocation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  check_in_date DATETIME NULL,
  check_out_date DATETIME NULL,
  status ENUM('Allocated','Checked-In','Checked-Out','Cancelled') NOT NULL DEFAULT 'Allocated',
  -- Same trick: only one active allocation per student, enforced by MySQL.
  active_student_id INT GENERATED ALWAYS AS
    (CASE WHEN status IN ('Allocated','Checked-In') THEN student_id END) STORED,
  UNIQUE (active_student_id),
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  FOREIGN KEY (room_id) REFERENCES rooms(id),
  FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE SET NULL
);

CREATE TABLE complaints (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  hostel_id INT NULL,                 -- extra: lets wardens see only their hostel's complaints
  complaint_title VARCHAR(150) NOT NULL,
  description TEXT NOT NULL,
  complaint_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status ENUM('Open','In Progress','Resolved','Closed') NOT NULL DEFAULT 'Open',
  warden_remarks VARCHAR(255),
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  FOREIGN KEY (hostel_id) REFERENCES hostels(id) ON DELETE SET NULL
);

CREATE TABLE announcements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(150) NOT NULL,
  description TEXT NOT NULL,
  hostel_id INT NULL,                 -- extra: NULL = visible to everyone
  created_by INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id),
  FOREIGN KEY (hostel_id) REFERENCES hostels(id) ON DELETE CASCADE
);

-- Extra table: audit trail of who did what (useful for viva + reports)
CREATE TABLE activity_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NULL,
  action VARCHAR(100) NOT NULL,
  details VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Extra table: key-value system settings
CREATE TABLE system_settings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  `key` VARCHAR(50) NOT NULL UNIQUE,
  `value` VARCHAR(255) NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_rooms_status ON rooms(status);
CREATE INDEX idx_complaints_status ON complaints(status);
