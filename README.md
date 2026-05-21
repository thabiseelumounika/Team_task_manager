Team Task Manager

A full-stack, role-based Team Task Management web application built using Python (Flask), SQLite, and HTML/CSS (Jinja2 templates).
It provides secure authentication, role-based access control, and efficient task tracking for teams.

✨ Features
🔐 Authentication & Security
Secure Signup & Login system
Passwords hashed using werkzeug.security
Role-based access: Admin / Member
Forgot password flow integrated into login system

👨‍💼 Admin Features
Create and manage Projects
Create tasks and assign them to users
Manage team members (view & delete users)
Delete or manage tasks from dashboard

👩‍💻 Member Features
Personal dashboard with task overview
Update task status:
Pending
In Progress
Completed
View only assigned tasks (restricted access)

📊 Dashboard
Total tasks
Completed tasks
Pending tasks
Overdue task tracking

*Tech Stack*
Backend: Python, Flask
Database: SQLite (SQL-based lightweight DB)
Frontend: HTML5, CSS3, Jinja2 Templates
Security: Werkzeug password hashing