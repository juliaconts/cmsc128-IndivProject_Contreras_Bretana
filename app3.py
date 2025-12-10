from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages 
import sqlite3, hashlib
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = "your_secret_key"
DB_path = "tasks.db"

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

def init_db():
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) NOT NULL UNIQUE,
            username VARCHAR(255) NOT NULL UNIQUE,
            fullname TEXT NOT NULL,
            password VARCHAR(255) NOT NULL,
            sec_question TEXT,
            sec_answer TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            priority INTEGER NOT NULL,
            label TEXT NOT NULL,
            task_name TEXT NOT NULL,
            date TEXT,
            time TEXT,
            task_desc TEXT,
            sub_todo TEXT,
            created_at TEXT,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES Accounts(id)
        )
    ''')
    conn.commit()
    conn.close()

# -----------------
# Account Helpers
# -----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_id(id):
    with sqlite3.connect(DB_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Accounts WHERE id = ?", (id,))
        return cursor.fetchone()
    
def get_user_email(email):
    with sqlite3.connect(DB_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Accounts WHERE email = ?", (email,))
        return cursor.fetchone()
    
def edit_profile(id, username, fullname, password):
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    if password:
        password = hash_password(password)
        cursor.execute('''
            UPDATE Accounts
            SET username = ?, fullname = ?, password = ?
            WHERE id = ?
        ''', (username, fullname, password, id))
    else:
        cursor.execute('''
            UPDATE Accounts
            SET username = ?, fullname = ?
            WHERE id = ?
        ''', (username, fullname, id))

    conn.commit()
    conn.close()

def get_manila_now():
    if ZoneInfo:
        try:
            return datetime.now(ZoneInfo("Asia/Manila"))
        except:
            return datetime.now(timezone(timedelta(hours=8)))
    else:
        return datetime.now(timezone(timedelta(hours=8)))

#--------------------- 
# Task Helpers
# --------------------
def get_tasks(user_id, sort_by=None):
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()

    query = "SELECT * FROM Tasks WHERE user_id=?"

    if sort_by == "priority":
        query += " ORDER BY CAST(priority AS INTEGER) ASC"
    elif sort_by == "due":
        query += " ORDER BY date ASC, time ASC"
    elif sort_by == "timestamp":
        query += " ORDER BY datetime(created_at) DESC"

    cursor.execute(query, (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def add_task(user_id, priority, label, task_name, date, time, task_desc, sub_todo):
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    created_at = get_manila_now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO Tasks (user_id, priority, label, task_name, date, time, task_desc, sub_todo, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, priority, label, task_name, date, time, task_desc, sub_todo, created_at))
    conn.commit()
    conn.close()

def edit_task(task_id, user_id, priority, label, task_name, date, time, task_desc, sub_todo):
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Tasks
        SET priority = ?, label = ?, task_name = ?, date = ?, time = ?, task_desc = ?, sub_todo = ?
        WHERE id = ? AND user_id = ?
    ''', (priority, label, task_name, date, time, task_desc, sub_todo, task_id, user_id))
    conn.commit()
    conn.close()

def delete_task_db(task_id, user_id):
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    deleted = cursor.fetchone()
    if deleted:
        cursor.execute("DELETE FROM Tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()
    return deleted

def restore_task(task_data):
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Tasks (id, user_id, priority, label, task_name, date, time, task_desc, sub_todo, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', task_data)
    conn.commit()
    conn.close()

# ------------------
# Account Routes
# ------------------
@app.route('/')  
def home():
    if 'id' in session:
        return redirect(url_for("tasks_page"))
    else:
        return redirect(url_for("login"))
    

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        fullname = request.form["fullname"]
        password = request.form["password"]
        hashed_password = hash_password(request.form["password"]) 
        sec_question = request.form["sec_question"]
        sec_answer_raw = request.form["sec_answer"]
        sec_answer = hash_password(sec_answer_raw)

        conn = sqlite3.connect(DB_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Accounts WHERE username = ? OR email = ?", (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Username or email already exists.", "error")
            return redirect(url_for("login"))
        else:
            cursor.execute("INSERT INTO Accounts (email, username, fullname, password, sec_question, sec_answer) VALUES (?, ?, ?, ?, ?, ?)",
                        (email, username, fullname, hashed_password, sec_question, sec_answer))
            
        conn.commit()

        user_id = cursor.lastrowid
        conn.close()

        session["id"] = user_id
        session["email"] = email

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("homepage.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if 'id' in session:
        return redirect(url_for("tasks_page"))
    
    get_flashed_messages()
    if request.method == "POST":
        email = request.form["email"]
        password = hash_password(request.form.get("password", ""))

        user = get_user_email(email)
        if not user:
            # Email not found
            flash("No account found with that email.", "error")
            return render_template("login.html")

        # hashed_password = hash_password(password)
        if user[4] != password:
            # Wrong password
            flash("Incorrect password.", "error")
            return render_template("login.html")

        # Correct login
        session["id"] = user[0]
        session["email"] = user[1]
        flash("Login successful!", "success")
        return redirect(url_for("tasks_page"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route('/edit/<int:id>', methods=['GET'])
def edit_account(id):
    username = request.form.get("username", "").strip()
    fullname = request.form.get("fullname", "").strip()
    password = request.form.get("password", "").strip()

    edit_profile(id, username, fullname, password)
    flash("Profile updated successfully!", "success")
    return redirect(url_for("profile"))

@app.route("/recover", methods=["GET", "POST"])
def recover():
    stage = "email"   # email → question → reset
    message = None
    error = None
    question = None
    reset_mode = False
    open_recovery = True 

    if request.method == "POST":
        stage = request.form.get("action")

        if stage == "check_email":
            email = request.form["email"]  

            conn = sqlite3.connect(DB_path)
            cur = conn.cursor()
            cur.execute("SELECT * FROM Accounts WHERE email = ?", (email,))
            user = cur.fetchone()
            conn.close()

            if user:
                message = f"Email verified: {email}"
                session["recover_email"] = email

                question = user[5]   # security question
                stage = "question"   # go to security question stage
            else:
                flash("No account found with that email. Please try again.", "error") 
                stage = "email"

        elif stage == "check_answer":
            email = session.get("recover_email")
            answer = request.form["sec_answer"]

            user = get_user_email(email)

            if not user:
                error = "Session expired. Please try again."
                stage = "email"
            else:
                stored_answer = user[6]  # stored hash

                if stored_answer != hash_password(answer):
                    error = "Incorrect answer. Please try again."
                    question = user[5]
                    stage = "question"
                else:
                    # Correct answer, show password reset fields
                    reset_mode = True
                    stage = "reset"

        elif stage == "reset_password":
            new_password = request.form["new_password"]
            confirm_password = request.form["confirm_password"]
            email = session.get("recover_email")

            if not email:
                error = "Session expired. Please verify your email again."
                stage = "email"
            elif new_password != confirm_password:
                error = "Passwords do not match."
                stage = "reset"
                reset_mode = True
            else:
                hashed = hashlib.sha256(new_password.encode()).hexdigest()

                conn = sqlite3.connect(DB_path)
                cur = conn.cursor()
                cur.execute(
                    "UPDATE Accounts SET password = ? WHERE email = ?",
                    (hashed, email)
                )
                conn.commit()
                conn.close()

                session.pop("recover_email", None)
                flash("Password successfully reset! You can now log in.", "success")
                return redirect(url_for("login"))

    return render_template(
        "login.html",
        stage=stage,
        question=question,
        message=message,
        error=error,
        reset_mode=reset_mode,
        open_recovery=open_recovery
    )

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    user_id = session["id"]
    user = get_user_id(user_id)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        fullname = request.form.get("fullname", "").strip()
        password = request.form.get("password", "").strip()

        edit_profile(user_id, username, fullname, password)
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("homepage.html", user=user)

# ----------------------
# Tasks Routes
# ----------------------
@app.route("/tasks")
def tasks_page():
    if "id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    user_id = session["id"]
    sort = request.args.get("sort")

    if sort not in ("priority", "due", "timestamp"):
        sort = None

    user = get_user_id(user_id)  # [email, username, fullname] etc.
    tasks = get_tasks(user_id, sort)
    return render_template("homepage.html", user=user, tasks=tasks, sort=sort, email=session.get("email"))

@app.route("/add", methods=["POST"])
def add():
    if "id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["id"]
    try:
        priority = int(request.form.get("priority", 3))
    except ValueError:
        priority = 3

    label = request.form.get("label", "").strip()
    task_name = request.form.get("task_name", "").strip()
    date = request.form.get("date", "")
    time = request.form.get("time", "")
    task_desc = request.form.get("task_desc", "")
    sub_todo = request.form.get("sub_todo", "")

    add_task(user_id, priority, label, task_name, date, time, task_desc, sub_todo)
    flash("Task added successfully!", "success")
    return redirect(url_for("tasks_page"))

@app.route("/edit/<int:task_id>", methods=["POST"])
def edit(task_id):
    if "id" not in session:
        return redirect(url_for("login"))

    user_id = session["id"]
    priority = int(request.form.get("priority", 3))
    label = request.form.get("label", "").strip()
    task_name = request.form.get("task_name", "").strip()
    date = request.form.get("date", "")
    time = request.form.get("time", "")
    task_desc = request.form.get("task_desc", "")
    sub_todo = request.form.get("sub_todo", "")

    edit_task(task_id, user_id, priority, label, task_name, date, time, task_desc, sub_todo)
    flash("Task updated successfully!", "success")
    return redirect(url_for("tasks_page"))

@app.route("/delete/<int:task_id>")
def delete(task_id):
    if "id" not in session:
        return redirect(url_for("login"))

    user_id = session["id"]
    deleted_task = delete_task_db(task_id, user_id)
    if deleted_task:
        session["last_deleted"] = deleted_task
        flash("Task deleted.", "warning")
    return redirect(url_for("tasks_page"))

@app.route("/undo_delete")
def undo_delete():
    if "last_deleted" in session:
        restore_task(session["last_deleted"])
        session.pop("last_deleted")
        flash("Task restored.", "success")
    return redirect(url_for("tasks_page"))

@app.route("/complete_task/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    if "id" not in session:
        return "Unauthorized", 403
    
    user_id = session["id"]
    completed = int(request.form["completed"])

    conn = sqlite3.connect(DB_path)
    cur = conn.cursor()
    cur.execute("UPDATE Tasks SET completed=? WHERE id=? AND user_id=?", (completed, task_id, user_id))
    conn.commit()
    conn.close()

    return "OK"

# ---------------------
# Template Filters
# ---------------------
@app.template_filter("format_date")
def format_date(value, format="%B %d, %Y"):
    try:
        date_obj = datetime.strptime(value, "%Y-%m-%d")
        return date_obj.strftime(format)
    except Exception:
        return value

# --- time filter ---
@app.template_filter("format_time")
def format_time(value, format="%I:%M %p"):
    try:
        return datetime.strptime(value, "%H:%M").strftime(format)
    except Exception:
        return value

# --- timestamp filter ---
@app.template_filter("format_timestamp")
def format_timestamp(value, format="%m-%d-%Y | %I:%M %p"):
    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return dt.strftime(format)
    except Exception as e:
        print("Timestamp parse error:", e, value)
        return value

if __name__ == "__main__":
    init_db()
    app.run(debug=True)