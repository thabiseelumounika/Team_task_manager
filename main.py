from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "secretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
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
# HOME
# =========================

@app.route('/')
def home():

    return redirect('/login')

# =========================
# SIGNUP
# =========================

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form['username']

        email = request.form['email']

        password = generate_password_hash(
            request.form['password']
        )

        role = request.form['role']

        existing_user = User.query.filter_by(
            email=email
        ).first()

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

# =========================
# FORGOT PASSWORD
# =========================
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = generate_password_hash(request.form['new_password'])

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = new_password
            db.session.commit()
            flash("Password basically updated. Please login.")
            return redirect('/login')
        else:
            flash("Email not found")
            return redirect('/forgot_password')

    return render_template('forgot_password.html')

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(user.password, password):

            session['user'] = user.username

            session['role'] = user.role

            return redirect('/dashboard')

        else:

            flash("Invalid Login")

    return render_template('login.html')

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:

        return redirect('/login')

    total_tasks = Task.query.count()

    completed_tasks = Task.query.filter_by(
        status='Completed'
    ).count()

    pending_tasks = Task.query.filter_by(
        status='Pending'
    ).count()

    tasks = Task.query.all()

    return render_template(
        'dashboard.html',
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        tasks=tasks
    )

# =========================
# MANAGE USERS
# =========================

@app.route('/manage_users')
def manage_users():
    if 'user' not in session:
        return redirect('/login')
    if session.get('role') != 'Admin':
        flash("Access Denied: Admin only")
        return redirect('/dashboard')
    
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    if 'user' not in session:
        return redirect('/login')
    if session.get('role') != 'Admin':
        flash("Access Denied: Admin only")
        return redirect('/dashboard')

    user = User.query.get(id)
    if user:
        if user.username == session['user']:
            flash("You cannot delete yourself!")
        else:
            db.session.delete(user)
            db.session.commit()
            flash("User Deleted Successfully")
    
    return redirect('/manage_users')

# =========================
# CREATE PROJECT
# =========================

@app.route('/create_project', methods=['GET', 'POST'])
def create_project():

    if 'user' not in session:

        return redirect('/login')

    if session.get('role') != 'Admin':
        flash("Access Denied: Admin only")
        return redirect('/dashboard')

    if request.method == 'POST':

        project_name = request.form['project_name']

        project = Project(
            project_name=project_name,
            created_by=session['user']
        )

        db.session.add(project)

        db.session.commit()

        flash("Project Created Successfully")

        return redirect('/dashboard')

    return render_template('create_project.html')

# =========================
# CREATE TASK
# =========================

@app.route('/create_task', methods=['GET', 'POST'])
def create_task():

    if 'user' not in session:

        return redirect('/login')

    if session.get('role') != 'Admin':
        flash("Access Denied: Admin only")
        return redirect('/dashboard')

    users = User.query.all()

    projects = Project.query.all()

    if request.method == 'POST':

        title = request.form.get('title')

        assigned_to = request.form.get('assigned_to')

        status = request.form.get('status')

        due_date = request.form.get('due_date')

        project_id = request.form.get('project_id')

        task = Task(
            title=title,
            assigned_to=assigned_to,
            status=status,
            due_date=due_date,
            project_id=project_id
        )

        db.session.add(task)

        db.session.commit()

        flash("Task Created Successfully")

        return redirect('/dashboard')

    return render_template(
        'create_task.html',
        users=users,
        projects=projects
    )

# =========================
# UPDATE TASK
# =========================

@app.route('/update_task/<int:id>', methods=['POST'])
def update_task(id):

    if 'user' not in session:

        return redirect('/login')

    task = Task.query.get(id)

    task.status = request.form['status']

    db.session.commit()

    flash("Task Updated Successfully")

    return redirect('/dashboard')

# =========================
# DELETE TASK
# =========================

@app.route('/delete_task/<int:id>', methods=['POST'])
def delete_task(id):

    if 'user' not in session:

        return redirect('/login')

    task = Task.query.get(id)

    db.session.delete(task)

    db.session.commit()

    flash("Task Deleted Successfully")

    return redirect('/dashboard')

# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.clear()
    flash("You are successfully logged out")

    return redirect('/login')

# =========================
# RUN APP
# =========================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

    app.run(host="0.0.0.0", port=5000)