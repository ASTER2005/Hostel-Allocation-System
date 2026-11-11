-- Sample Seed Data for MySQL 8.0+
USE hostel_db;

-- 1. Users (Passwords hashed with Werkzeug pbkdf2/scrypt, plaintext 'admin123' / 'warden123' / 'student123')
INSERT INTO users (id, name, email, password_hash, role, created_at) VALUES
(1, 'Dean of Student Affairs', 'admin@college.edu', 'scrypt:32768:8:1$uH3d5t3u$71d79da933ba2133b3d9dca437e735492d6e4df914041d5f3083cf453b34ff441f3e7eb9aa4a8b792ff42c8d5c4c23db2e5c8e100f913d28994bb2e1ad15ba37', 'admin', NOW()),
(2, 'Dr. Rajeshwar Sen', 'warden1@college.edu', 'scrypt:32768:8:1$uH3d5t3u$71d79da933ba2133b3d9dca437e735492d6e4df914041d5f3083cf453b34ff441f3e7eb9aa4a8b792ff42c8d5c4c23db2e5c8e100f913d28994bb2e1ad15ba37', 'warden', NOW()),
(3, 'Prof. Arundhati Das', 'warden2@college.edu', 'scrypt:32768:8:1$uH3d5t3u$71d79da933ba2133b3d9dca437e735492d6e4df914041d5f3083cf453b34ff441f3e7eb9aa4a8b792ff42c8d5c4c23db2e5c8e100f913d28994bb2e1ad15ba37', 'warden', NOW()),
(4, 'Rahul Mehta', 'student@college.edu', 'scrypt:32768:8:1$uH3d5t3u$71d79da933ba2133b3d9dca437e735492d6e4df914041d5f3083cf453b34ff441f3e7eb9aa4a8b792ff42c8d5c4c23db2e5c8e100f913d28994bb2e1ad15ba37', 'student', NOW()),
(5, 'Priya Nair', 'priya@college.edu', 'scrypt:32768:8:1$uH3d5t3u$71d79da933ba2133b3d9dca437e735492d6e4df914041d5f3083cf453b34ff441f3e7eb9aa4a8b792ff42c8d5c4c23db2e5c8e100f913d28994bb2e1ad15ba37', 'student', NOW()),
(6, 'Aman Verma', 'aman@college.edu', 'scrypt:32768:8:1$uH3d5t3u$71d79da933ba2133b3d9dca437e735492d6e4df914041d5f3083cf453b34ff441f3e7eb9aa4a8b792ff42c8d5c4c23db2e5c8e100f913d28994bb2e1ad15ba37', 'student', NOW()),
(7, 'Kiran Rao', 'kiran@college.edu', 'scrypt:32768:8:1$uH3d5t3u$71d79da933ba2133b3d9dca437e735492d6e4df914041d5f3083cf453b34ff441f3e7eb9aa4a8b792ff42c8d5c4c23db2e5c8e100f913d28994bb2e1ad15ba37', 'student', NOW()),
(8, 'Ananya Sharma', 'ananya@college.edu', 'scrypt:32768:8:1$uH3d5t3u$71d79da933ba2133b3d9dca437e735492d6e4df914041d5f3083cf453b34ff441f3e7eb9aa4a8b792ff42c8d5c4c23db2e5c8e100f913d28994bb2e1ad15ba37', 'student', NOW()),
(9, 'Rohan Gupta', 'rohan@college.edu', 'scrypt:32768:8:1$uH3d5t3u$71d79da933ba2133b3d9dca437e735492d6e4df914041d5f3083cf453b34ff441f3e7eb9aa4a8b792ff42c8d5c4c23db2e5c8e100f913d28994bb2e1ad15ba37', 'student', NOW()),
(10, 'Sneha Patel', 'sneha@college.edu', 'scrypt:32768:8:1$uH3d5t3u$71d79da933ba2133b3d9dca437e735492d6e4df914041d5f3083cf453b34ff441f3e7eb9aa4a8b792ff42c8d5c4c23db2e5c8e100f913d28994bb2e1ad15ba37', 'student', NOW());

-- 2. Hostels
INSERT INTO hostels (id, hostel_name, hostel_type, address, total_rooms, description) VALUES
(1, 'Ashoka Hall', 'Boys', 'North Campus, Gate 2', 6, 'Boys residence with courtyard and sports grounds.'),
(2, 'Gargi Hall', 'Girls', 'South Campus, Promenade Way', 5, 'Girls residence with modern reading lounges and 24/7 security.'),
(3, 'Tagore Hall', 'Co-ed', 'East Campus, Innovation Quadrangle', 4, 'Postgraduate and international scholars residence.');

-- 3. Wardens
INSERT INTO wardens (id, user_id, phone, assigned_hostel_id) VALUES
(1, 2, '9800011223', 1),
(2, 3, '9800044556', 2);

-- 4. Rooms
INSERT INTO rooms (id, hostel_id, room_number, room_type, capacity, occupied_count, status) VALUES
(1, 1, '101', 'Single', 1, 1, 'Full'),
(2, 1, '102', 'Double', 2, 1, 'Available'),
(3, 1, '103', 'Double', 2, 0, 'Available'),
(4, 1, '104', 'Triple', 3, 0, 'Available'),
(5, 1, '105', 'Triple', 3, 0, 'Available'),
(6, 1, '106', 'Dormitory', 6, 0, 'Available'),
(7, 2, '201', 'Single', 1, 0, 'Available'),
(8, 2, '202', 'Double', 2, 1, 'Available'),
(9, 2, '203', 'Double', 2, 0, 'Available'),
(10, 2, '204', 'Triple', 3, 0, 'Available'),
(11, 2, '205', 'Dormitory', 6, 0, 'Maintenance'),
(12, 3, '301', 'Single', 1, 0, 'Available'),
(13, 3, '302', 'Double', 2, 0, 'Available'),
(14, 3, '303', 'Triple', 3, 0, 'Available'),
(15, 3, '304', 'Double', 2, 0, 'Available');

-- 5. Students
INSERT INTO students (id, user_id, registration_number, phone, department, academic_year, gender, address) VALUES
(1, 4, 'CS2101', '9810011010', 'Computer Science & Engineering', 2, 'Male', 'Flat 4B, Bengaluru'),
(2, 5, 'EC2102', '9810022020', 'Electronics & Communication', 3, 'Female', '12 Palm Meadows, Kochi'),
(3, 6, 'ME2103', '9810033030', 'Mechanical Engineering', 3, 'Male', '78 Civil Lines, Jaipur'),
(4, 7, 'CS2104', '9810044040', 'Computer Science & Engineering', 1, 'Male', '93 Lakeview Heights, Hyderabad'),
(5, 8, 'BT2105', '9810055050', 'Biotechnology', 2, 'Female', '52 Park Street, Kolkata'),
(6, 9, 'CE2106', '9810066060', 'Civil Engineering', 4, 'Male', '40 North Avenue, New Delhi'),
(7, 10, 'IT2107', '9810077070', 'Information Technology', 1, 'Female', '14 MG Road, Pune');

-- 6. Applications
INSERT INTO applications (id, student_id, preferred_hostel_id, preferred_room_type, application_date, status, admin_remarks) VALUES
(1, 1, 1, 'Single', DATE_SUB(NOW(), INTERVAL 2 DAY), 'Pending', NULL),
(2, 2, 2, 'Double', DATE_SUB(NOW(), INTERVAL 5 DAY), 'Approved', 'Verified merit credentials.'),
(3, 3, 1, 'Single', DATE_SUB(NOW(), INTERVAL 15 DAY), 'Allocated', 'Approved.'),
(4, 4, 1, 'Double', DATE_SUB(NOW(), INTERVAL 12 DAY), 'Allocated', 'Approved.'),
(5, 5, 2, 'Double', DATE_SUB(NOW(), INTERVAL 20 DAY), 'Allocated', 'Approved.'),
(6, 6, 1, 'Single', DATE_SUB(NOW(), INTERVAL 7 DAY), 'Rejected', 'Single rooms fully booked.');

-- 7. Allocations
INSERT INTO allocations (id, student_id, room_id, application_id, allocation_date, check_in_date, status) VALUES
(1, 3, 1, 3, DATE_SUB(NOW(), INTERVAL 14 DAY), DATE_SUB(NOW(), INTERVAL 13 DAY), 'Checked-In'),
(2, 4, 2, 4, DATE_SUB(NOW(), INTERVAL 10 DAY), NULL, 'Allocated'),
(3, 5, 8, 5, DATE_SUB(NOW(), INTERVAL 18 DAY), DATE_SUB(NOW(), INTERVAL 17 DAY), 'Checked-In');

-- 8. Complaints
INSERT INTO complaints (id, student_id, hostel_id, complaint_title, description, complaint_date, status, warden_remarks) VALUES
(1, 3, 1, 'Water pressure low in washroom', 'Shower and tap pressure in washroom 1-B on 1st floor has been weak.', DATE_SUB(NOW(), INTERVAL 1 DAY), 'Open', NULL),
(2, 5, 2, 'Wi-Fi connectivity drop on 2nd Floor', 'The access point near room 202 disconnects intermittently.', DATE_SUB(NOW(), INTERVAL 3 DAY), 'In Progress', 'Campus IT investigating router firmware.'),
(3, 4, 1, 'Study table lamp fixture loose', 'Study table fixture was loose.', DATE_SUB(NOW(), INTERVAL 6 DAY), 'Resolved', 'Electrician replaced the bracket on Wednesday.');

-- 9. Announcements
INSERT INTO announcements (id, title, description, hostel_id, created_by, created_at) VALUES
(1, 'Hostel Allotment & Onboarding for Academic Term 2026-27', 'Online accommodation applications are officially open for all registered undergraduate and postgraduate scholars.', NULL, 1, DATE_SUB(NOW(), INTERVAL 4 DAY)),
(2, 'North Campus Infrastructure Maintenance Notice', 'Routine maintenance of the high-tension transformer and backup diesel generator will occur this Saturday between 10:00 AM and 1:00 PM.', 1, 2, DATE_SUB(NOW(), INTERVAL 2 DAY)),
(3, 'Extended Library and Study Lounge Hours during Mid-Sem', 'The central reading room and common study lounges in Gargi Hall will remain open until midnight.', 2, 3, DATE_SUB(NOW(), INTERVAL 1 DAY));

