from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import traceback

app = Flask(__name__)

# =========================
# CONFIG
# =========================

app.secret_key = os.environ.get("SECRET_KEY", "secretkey")

# Use PostgreSQL on Railway (DATABASE_URL), fallback to SQLite for local dev
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Railway's PostgreSQL URL starts with postgres://, SQLAlchemy needs postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# DATABASE MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(200))
    created_by = db.Column(db.String(100))


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    status = db.Column(db.String(50), default="Pending")
    assigned_to = db.Column(db.String(100))
    due_date = db.Column(db.String(100))
    project_id = db.Column(db.Integer)

# =========================
# CREATE TABLES ON STARTUP
# =========================

with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

# =========================
# ROUTES
# =========================

@app.route('/')
def home():
    return redirect('/login')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists")
            return redirect('/signup')

        new_user = User(
            username=username,
            email=email,
            password=password,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Signup Successful")
        return redirect('/login')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            session['role'] = user.role
            return redirect('/dashboard')
        else:
            flash("Invalid Login")

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='Completed').count()
    pending_tasks = Task.query.filter_by(status='Pending').count()
    tasks = Task.query.all()

    return render_template(
        'dashboard.html',
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        tasks=tasks
    )


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out")
    return redirect('/login')


@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    if 'user' not in session:
        return redirect('/login')
    if session.get('role') != 'Admin':
        flash("Access denied. Admins only.")
        return redirect('/dashboard')

    if request.method == 'POST':
        project_name = request.form['project_name']
        new_project = Project(
            project_name=project_name,
            created_by=session['user']
        )
        db.session.add(new_project)
        db.session.commit()
        flash("Project created successfully!")
        return redirect('/dashboard')

    return render_template('create_project.html')


@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    if 'user' not in session:
        return redirect('/login')
    if session.get('role') != 'Admin':
        flash("Access denied. Admins only.")
        return redirect('/dashboard')

    users = User.query.all()
    projects = Project.query.all()

    if request.method == 'POST':
        title = request.form['title']
        assigned_to = request.form['assigned_to']
        status = request.form['status']
        due_date = request.form['due_date']
        project_id = request.form['project_id']

        new_task = Task(
            title=title,
            assigned_to=assigned_to,
            status=status,
            due_date=due_date,
            project_id=project_id
        )
        db.session.add(new_task)
        db.session.commit()
        flash("Task created successfully!")
        return redirect('/dashboard')

    return render_template('create_task.html', users=users, projects=projects)


@app.route('/manage_users')
def manage_users():
    if 'user' not in session:
        return redirect('/login')
    if session.get('role') != 'Admin':
        flash("Access denied. Admins only.")
        return redirect('/dashboard')

    users = User.query.all()
    return render_template('manage_users.html', users=users)


@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user' not in session:
        return redirect('/login')
    if session.get('role') != 'Admin':
        flash("Access denied. Admins only.")
        return redirect('/dashboard')

    user = User.query.get(user_id)
    if user:
        if user.username == session['user']:
            flash("You cannot delete your own account.")
        else:
            db.session.delete(user)
            db.session.commit()
            flash(f"User '{user.username}' deleted successfully.")
    else:
        flash("User not found.")

    return redirect('/manage_users')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash("Password reset successful! Please login.")
            return redirect('/login')
        else:
            flash("Email not found.")

    return render_template('forgot_password.html')


@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    if 'user' not in session:
        return redirect('/login')

    task = Task.query.get(task_id)
    if task:
        task.status = request.form['status']
        db.session.commit()
        flash("Task updated successfully!")
    else:
        flash("Task not found.")

    return redirect('/dashboard')


@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user' not in session:
        return redirect('/login')
    if session.get('role') != 'Admin':
        flash("Access denied. Admins only.")
        return redirect('/dashboard')

    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully!")
    else:
        flash("Task not found.")

    return redirect('/dashboard')


# =========================
# ERROR HANDLERS
# =========================

@app.errorhandler(404)
def not_found_error(e):
    return redirect('/login')

@app.errorhandler(500)
def internal_error(e):
    print(traceback.format_exc())
    return "Server Error", 500


# =========================
# RUN (RAILWAY READY)
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)