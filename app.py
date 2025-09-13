# --------------  app.py  --------------
import pathlib
import sqlite3
import os
import secrets
import datetime
import shutil
import numpy as np

from flask import (Flask, render_template, request, redirect,
                   url_for, flash, session, jsonify)
from flask_mail import Mail, Message

# -------------------------------------------------
# 1.  ONE PLACE TO STORE THE DATABASE FILE
# -------------------------------------------------
BASE_DIR      = pathlib.Path(__file__).resolve().parent
DB_FILE       = BASE_DIR / 'expenses.db'          # <─ same file always
BACKUP_FOLDER = BASE_DIR / 'backups'

# create folder if missing
DB_FILE.parent.mkdir(parents=True, exist_ok=True)
BACKUP_FOLDER.mkdir(exist_ok=True)

# -------------------------------------------------
# 2.  FLASK-MAIL CONFIG
# -------------------------------------------------
app = Flask(__name__)
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_DEFAULT_SENDER'] = 'frrokuk2@gmail.com'
app.config['MAIL_USERNAME'] = 'frrokuk2@gmail.com'
app.config['MAIL_PASSWORD'] = 'xxxxxxxxxxxxxxxxx'   # 16digit app password
mail = Mail(app)

app.secret_key = secrets.token_hex(16)

# -------------------------------------------------
# 3.  DATABASE HELPERS
# -------------------------------------------------
def get_conn():
    """Return a sqlite connection with Row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they do not exist yet."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT        NOT NULL
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category    TEXT  NOT NULL,
                amount      REAL  NOT NULL,
                date        TEXT  NOT NULL,
                description TEXT,
                user_id     INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS plans (
                name     TEXT PRIMARY KEY,
                price    REAL,
                features TEXT
            );

            INSERT OR IGNORE INTO plans(name, price, features) VALUES
            ('Free',       0.0,  'Track up to 50 expenses,Basic reporting,Email support'),
            ('Premium',    9.99, 'Unlimited expenses,Advanced reporting,Priority email support,Custom categories'),
            ('Enterprise', 49.99,'Unlimited expenses,Team collaboration,Custom reports & dashboards,Dedicated account manager');
        """)
init_db()          # <─ runs once every start-up (safe: IF NOT EXISTS)

# Add email column to users table if missing
with get_conn() as conn:
    try:
        conn.execute("ALTER TABLE users ADD COLUMN email TEXT;")
    except sqlite3.OperationalError:
        pass  # column already exists – ignore
# -------------------------------------------------
# 4.  ROUTES
# -------------------------------------------------
@app.route('/')
def index():
    return redirect(url_for('landing_page'))

@app.route('/landing')
def landing_page():
    return render_template('landing_page.html')

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/send-email', methods=['POST'])
def send_email():
    name    = request.form['name']
    email   = request.form['email']
    message = request.form['message']
    msg = Message(subject=f"Message from {name}",
                  sender=email,
                  recipients=['frrokuk2@gmail.com'],
                  body=message)
    mail.send(msg)
    return "Email sent successfully!"

@app.route('/pricing')
def pricing_page():
    with get_conn() as conn:
        plans = conn.execute("SELECT name, price, features FROM plans").fetchall()
    # build same structure as before
    pricing_data = [
        {"name": p["name"],
         "price": p["price"],
         "features": p["features"].split(",")}
        for p in plans
    ]
    return render_template('pricing.html', pricing_data=pricing_data)

# ---------------- AUTH ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username   = request.form['username'].strip()
        password   = request.form['password']
        confirm    = request.form['confirm_password'].strip()

        if not username or not password or not confirm:
            flash("All fields required.", "error")
            return redirect(url_for('register'))
        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for('register'))

        pwd_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            with get_conn() as conn:
                if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
                    flash("Username already exists.", "error")
                    return redirect(url_for('register'))
                conn.execute("INSERT INTO users (username, password_hash) VALUES (?,?)",
                             (username, pwd_hash))
                conn.commit()
            flash("Registration successful – please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            flash(f"DB error: {e}", "error")
    return render_template('register.html')

import hashlib

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()

        with get_conn() as conn:
            user = conn.execute("SELECT id, password_hash FROM users WHERE username = ?",
                                (username,)).fetchone()
            if user and user["password_hash"] == pwd_hash:
                session['user_id']   = user["id"]
                session['username']  = username
                return redirect(url_for('home'))
            flash("Invalid username or password.", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

# ---------------- EXPENSES ----------------
CATEGORIES = [
    'Housing', 'Transportation', 'Food', 'Clothing', 'Medical', 'Healthcare',
    'Insurance', 'Household Items/Supplies', 'Personal', 'Debt', 'Retirement',
    'Education', 'Savings', 'Gifts/Donations', 'Entertainment'
]

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'])

@app.route('/add-expenses', methods=['GET', 'POST'])
def add_expense():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        cat   = request.form['category']
        amt   = request.form['amount']
        date  = request.form['date']
        desc  = request.form['description']
        if not cat or not amt or not date:
            flash("Please fill all required fields.", "error")
            return render_template('add_expenses.html', categories=CATEGORIES)
        user_id = session['user_id']
        with get_conn() as conn:
            conn.execute("INSERT INTO expenses (category,amount,date,description,user_id) VALUES (?,?,?,?,?)",
                         (cat, amt, date, desc, user_id))
            conn.commit()
        flash("Expense added.", "success")
        return redirect(url_for('home'))
    return render_template('add_expenses.html', categories=CATEGORIES)

@app.route('/view-expenses')
def view_expenses():
    uid = session.get('user_id')
    if not uid:
        flash("Please log in.", "error")
        return redirect(url_for('login'))
    with get_conn() as conn:
        expenses = conn.execute("SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC", (uid,)).fetchall()
    return render_template('view_expenses.html', expenses=expenses)

@app.route('/delete_expense/<int:eid>')
def delete_expense(eid):
    uid = session.get('user_id')
    if not uid:
        return redirect(url_for('login'))
    with get_conn() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (eid, uid))
        conn.commit()
    flash("Expense deleted.", "success")
    return redirect(url_for('view_expenses'))

@app.route('/edit_expenses/<int:eid>', methods=['GET', 'POST'])
def edit_expense(eid):
    uid = session.get('user_id')
    if not uid:
        return redirect(url_for('login'))
    with get_conn() as conn:
        if request.method == 'POST':
            cat, amt, date, desc = (request.form[k] for k in ('category','amount','date','description'))
            conn.execute("""UPDATE expenses
                              SET category = ?, amount = ?, date = ?, description = ?
                            WHERE id = ? AND user_id = ?""",
                         (cat, amt, date, desc, eid, uid))
            conn.commit()
            flash("Expense updated.", "success")
            return redirect(url_for('view_expenses'))
        expense = conn.execute("SELECT * FROM expenses WHERE id = ? AND user_id = ?", (eid, uid)).fetchone()
        if not expense:
            flash("Expense not found.", "error")
            return redirect(url_for('view_expenses'))
    return render_template('edit_expense.html', expense=expense, categories=CATEGORIES)

@app.route('/summarize-expenses')
def summarize_expenses():
    uid = session.get('user_id')
    if not uid:
        flash("Please log in.", "error")
        return redirect(url_for('login'))
    with get_conn() as conn:
        summary = conn.execute("""SELECT category, SUM(amount) AS total
                                    FROM expenses
                                   WHERE user_id = ?
                                   GROUP BY category
                                   ORDER BY total DESC""", (uid,)).fetchall()
        totals = [r["total"] for r in summary]
        total_spending = sum(totals) if totals else 0
        percentages = [(r["category"], r["total"] / total_spending * 100) for r in summary]

        mean = np.mean(totals) if totals else 0
        std  = np.std(totals)  if totals else 0
        high = [r["category"] for r in summary if r["total"] > mean + std]

        recommendations = []
        if high:
            recommendations.append(f"Review high-spending categories: {', '.join(high)}.")
        else:
            recommendations.append("Your spending looks balanced.")

    return render_template('summarize_expenses.html',
                           summary=summary,
                           percentages=percentages,
                           recommendations=recommendations)

# ---------------- BACKUP / RESTORE ----------------
@app.route('/backup', methods=['POST'])
def backup():
    uid = session.get('user_id')
    if not uid:
        flash("Please log in.", "error")
        return redirect(url_for('login'))
    user_folder = BACKUP_FOLDER / str(uid)
    user_folder.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = user_folder / f"{uid}_expenses_backup_{stamp}.db"
    try:
        shutil.copy(DB_FILE, backup_path)
        flash("Backup created.", "success")
    except Exception as e:
        flash(f"Backup error: {e}", "error")
    return redirect(url_for('home'))

@app.route('/restore-backup', methods=['GET', 'POST'])
def restore_backup():
    uid = session.get('user_id')
    if not uid:
        return redirect(url_for('login'))
    user_folder = BACKUP_FOLDER / str(uid)
    if not user_folder.exists():
        flash("No backups found.", "error")
        return redirect(url_for('home'))
    backups = [f for f in user_folder.glob("*.db")]
    if request.method == 'POST':
        fname = request.form.get('backup_file')
        if not fname:
            flash("No file selected.", "error")
            return redirect(url_for('restore_backup'))
        src = user_folder / fname
        if not src.exists():
            flash("File not found.", "error")
            return redirect(url_for('restore_backup'))
        try:
            shutil.copy(src, DB_FILE)
            flash("Database restored.", "success")
        except Exception as e:
            flash(f"Restore error: {e}", "error")
        return redirect(url_for('home'))
    return render_template('restore_backup.html', backups=[b.name for b in backups])

# ---------------- RUN ----------------
if __name__ == "__main__":
    #app.run(debug=True)          # local dev
    app.run()              # production mode