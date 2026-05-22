from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import traceback

app = Flask(__name__)

# =========================
# CONFIG
# =========================

app.secret_key = "secretkey"

# Railway-safe database path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.getcwd(), 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# DATABASE TABLES
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(200))
    created_by = db.Column(db.String(100))


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    status = db.Column(db.String(50))
    assigned_to = db.Column(db.String(100))
    due_date = db.Column(db.String(100))
    project_id = db.Column(db.Integer)

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


# =========================
# ERROR HANDLER
# =========================

@app.errorhandler(500)
def internal_error(e):
    print(traceback.format_exc())
    return "Server Error", 500


# =========================
# RUN (LOCAL ONLY)
# =========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)