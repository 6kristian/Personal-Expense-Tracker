from ast import Try
from pydoc import describe
from flask import Flask, render_template, request, redirect, url_for, flash, session,send_file,send_from_directory,jsonify

from flask_mail import Mail, Message
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import secrets
import numpy as np
import shutil
import os
import datetime
import pathlib, os



# Define the database file location
db_file = r"C:\Users\User\python projects 2024\Personal Expense Tracker\expenses.db"
pathlib.Path(db_file).parent.mkdir(parents=True, exist_ok=True)
# Function to get a database connection
def db():
    """Return a connection to the *one* database we use."""
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn
# Initialize Flask app
app = Flask(__name__)
# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'frrokuk2@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'dird fiyb xerf rtrx'   # Replace with your app password or email password
mail = Mail(app)

# Set a secret key for flash messages and session handling
app.secret_key = secrets.token_hex(16)  # Change to a secure random key

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row  # Access rows as dictionaries
    return conn

# Function to retrieve all expenses from the database
def get_expenses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    conn.close()
    return expenses

# Home route: Displays the dashboard after login
@app.route('/')


@app.route('/landing')
def landing_page():
    # Render the landing page HTML
    return render_template('landing_page.html')
@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/send-email', methods=['POST'])
def send_email():
    name = request.form['name']
    email = request.form['email']
    message_content = request.form['message']

    #create email
    msg = Message(subject=f"Message from {name}",sender=email,recipients=['frrokuk2@gmail.com'],body=message_content)

    #send the email
    mail.send(msg)
    return "Email sent Successfully!"
@app.route('/pricing', methods=['GET'])
def pricing_page():
    with db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name,price,features FROM plans")
        plans = cursor.fetchall()

        pricing_data = [
        {
            "name": "Free",
            "price": 0.0,
            "features": [
                "Track up to 50 expenses",
                "Basic reporting",
                "Email support"
            ]
        },
        {
            "name": "Premium",
            "price": 9.99,
            "features": [
                "Unlimited expenses",
                "Advanced reporting",
                "Priority email support",
                "Custom categories"
            ]
        },
        {
            "name": "Enterprise",
            "price": 49.99,
            "features": [
                "Unlimited expenses",
                "Team collaboration",
                "Custom reports & dashboards",
                "Dedicated account manager"
            ]
        }
    ]

           

        
    return render_template('pricing.html', pricing_data=pricing_page)

@app.route('/home')
def home():
    if 'username' not in session:  # Check if the user is logged in
        return redirect(url_for('login'))  # Redirect to login if not authenticated
    return render_template('home.html', username=session['username'])  # Pass username to the template


@app.route('/register', methods=['GET', 'POST'])

def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password'].strip()

        #validate input
        if not username or not password or not confirm_password:
            flash("All fields are required.", "error")
            return redirect(url_for('register'))

        # Check if password and confirm password match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        # Hash the password before storing it
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        
        # Connect to the database and check if the username already exists
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                flash("Username already exists. Please choose another.", "error")
                return redirect(url_for('register'))

        # If the username doesn't exist, insert the new user into the database
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))  # Redirect to login page after successful registration
        except sqlite3.Error as e:
            flash(f"Database error: {e}","error")
        finally:
            conn.close()

        return render_template('home.html')

    return render_template('register.html')  # Render the registration page if GET request

# Login route: Allows users to log in
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"Attempted login with username: {username} and password: {password}")

        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            # Fetch the password hash and user_id for the username
            cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user:
                user_id = user[0]  # The first element is the user_id
                stored_password_hash = user[1]  # The second element is the password_hash
                # Compare the entered password hash with the stored hash
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                print(f"Entered password hash: {hashed_password}")
                print(f"Stored password hash: {stored_password_hash}")

                if stored_password_hash == hashed_password:
                    print("Password matched!")
                    session['user_id'] = user_id  # Store the user_id in session
                    session['username'] = username  # Optionally store the username in session
                    return redirect(url_for('home'))  # Redirect to home page after successful login
                else:
                    print("Password did not match.")
                    flash("Invalid username or password", "error")
            else:
                print("Username not found.")
                flash("Invalid username or password", "error")

    return render_template('login.html')

# Add expense route: Allows users to add a new expense
@app.route('/add-expenses', methods=['GET', 'POST'])
def add_expense():
    if 'username' not in session:  # Ensure user is logged in
        return redirect(url_for('login'))

    # Define available categories (you can also pull this from the database or another source)
    categories = [
    'Housing',
    'Transportation',
    'Food',
    'Clothing',
    'Medical',
    'Healthcare',
    'Insurance',
    'Household Items/Supplies',
    'Personal',
    'Debt',
    'Retirement',
    'Education',
    'Savings',
    'Gifts/Donations',
    'Entertainment'
]



    if request.method == 'POST':
        category = request.form['category']
        amount = request.form['amount']
        date = request.form['date']
        description = request.form['description']

        # Validate fields

        if not category or not amount or not date:
           flash('Please fill in all fields!', 'error')
           return render_template('add_expenses.html', categories=categories)  # Re-render with categories



        user_id = session.get('user_id')  # Ensure 'user_id' is set in the session during login
        if not user_id:
            flash("User not logged in. Please log in to add an expense.", "error")
            return redirect(url_for('login'))

        # Insert the expense into the database
        try:
            with db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO expenses (category, amount, date, description, user_id) VALUES (?, ?, ?, ?, ?)",
                    (category, amount, date, description, user_id),
                )
                conn.commit()

            flash('Expense added successfully!', 'success')
            return redirect(url_for('home'))
        except sqlite3.IntegrityError as e:
            flash(f"Database error: {e}", "error")

    return render_template('add_expenses.html',categories=categories)

# Delete expense route: Allows users to delete an expense by its ID
@app.route('/delete_expense/<int:id>')
def delete_expense(id):
    if 'username' not in session:  # Ensure user is logged in
        return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (id,))
        conn.commit()
        flash("Expense deleted successfully!", "success")
    except sqlite3.Error as e:
        flash(f"Error deleting expense: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for('view_expenses'))

@app.route('/edit_expenses/<int:id>', methods=['GET', 'POST'])
def edit_expenses(id):
    if 'username' not in session:
        flash("You need to log in to edit expenses.", "error")
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    with db() as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            # Retrieve data from the form
            category = request.form['category']
            amount = request.form['amount']
            date = request.form['date']
            description = request.form['description']

            # Update the expense in the database
            cursor.execute('''
                UPDATE expenses
                SET category = ?, amount = ?, date = ?, description = ?
                WHERE id = ? AND user_id = ?
            ''', (category, amount, date, description, id, user_id))
            conn.commit()

            flash('Expense updated successfully!', 'success')
            return redirect(url_for('view_expenses'))  # Redirect to the view expenses page

        # Fetch the expense to pre-fill the edit form
        cursor.execute('SELECT * FROM expenses WHERE id = ? AND user_id = ?', (id, user_id))
        expense = cursor.fetchone()

        if not expense:
            flash("Expense not found or you don't have access to this expense.", "error")
            return redirect(url_for('view_expenses'))

    return render_template('edit_expense.html', expense=expense)




@app.route('/view-expenses')
def view_expenses():
    user_id = session.get('user_id')
    if not user_id:
        flash("User not logged in. Please log in to view expenses.", "error")
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE user_id = ?", (user_id,))
    expenses = cursor.fetchall()
    conn.close()
    return render_template('view_expenses.html', expenses=expenses)
    return redirect(url_for('view_expenses'))


@app.route('/summarize-expenses')
def summarize_expenses():
    if 'username' not in session:
        return redirect(url_for('login'))



    user_id = session.get('user_id')
    if not user_id:
        flash("User not logged in.Please log in to view summaries","error")
        return redirect(url_for('login'))



    with db() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        #fetch total spending per category
        cursor.execute('''
        SELECT category, SUM(amount) as total_amount
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total_amount DESC
        ''',(user_id,))
        summary = cursor.fetchall()

        #extract data for AI processing
        categories = [row['category'] for row in summary]
        totals = [row['total_amount'] for row in summary]

        total_spending = sum(totals)
        percentages = [(category,total / total_spending * 100) for category, total in zip(categories, totals)]

        # Detect high-spending categories using AI
        mean_spending = np.mean(totals)
        std_dev_spending = np.std(totals)
        high_spending = [
            category for category, total in zip(categories,totals)
            if total > mean_spending + std_dev_spending
        ]


        #recommendations
        recommendations = []
        if high_spending:
            recommendations.append(
                f"Consider reviewing your spending in the following  high-expense categories:{', '.join(high_spending)}."
            )
        else:
            recommendations.append("Your spending seems balanced across all categories!")


    return render_template(
        'summarize_expenses.html',
        summary=summary,
        percentages=percentages,
        recommendations=recommendations
    )




@app.route('/backup', methods=['POST'])
def backup():
    if 'username' not in session:
        flash("Please log in to back up your data.", "error")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    if not user_id:
        flash("User not logged in. Please log in to back up your data.", "error")
        return redirect(url_for('login'))

    # Define paths
    db_path = 'expenses.db'  # Path to your main database file
    user_folder = os.path.join('backups', str(user_id))
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)# Folder where backups will be stored
    os.makedirs(user_folder, exist_ok=True)  # Create backup folder if it doesn't exist

    # Backup filename with user ID and timestamp
    backup_filename = f"{user_id}_expenses_backup_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"
    backup_path = os.path.join(user_folder, backup_filename)

    try:
        # Check if the main database file exists
        if not os.path.exists(db_path):
            flash("The database file does not exist.", "error")
            return redirect(url_for('home'))

        print(f"Creating backup at: {backup_path}")

        # Copy the database to the backup folder
        shutil.copy(db_path, backup_path)
        flash("Backup successful!", "success")
        print(f"Backup created at: {backup_path}")  # Debugging print

    except Exception as e:
        flash(f"Error creating backup: {str(e)}", "error")
        print(f"Error creating backup: {str(e)}")  # Debugging print

    return redirect(url_for('home'))





@app.route('/restore-backup', methods=['GET', 'POST'])
def restore_backup():
    if 'username' not in session:
        flash("Please log in to restore backup.", "error")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    if not user_id:
        flash("User not logged in. Please log in to restore backup.", "error")
        return redirect(url_for('login'))

    user_folder = os.path.join('backups', str(user_id))

    if not os.path.exists(user_folder):
        flash("No backups found for this user","error")
        return redirect(url_for('home'))
    # List all available backups for the user
    try:
        backups = [f for f in os.listdir(user_folder) if f.endswith('.db')]
        print(f"Checking backups in: {user_folder}")

        if not backups:
            flash("No backups available to restore.", "error")
    except Exception as e:
        flash(f"Error reading backup folder: {str(e)}", "error")
        backups = []

    if request.method == 'POST':
        # Get the selected backup from the form
        selected_backup = request.form.get('backup_file')
        if not selected_backup:
            flash("No backup selected.", "error")
            return redirect(url_for('restore_backup'))

        backup_path = os.path.join(user_folder, selected_backup)
        user_db_path = 'expenses.db'  # Replace with the correct path for the user's database

        # Check if the backup file exists
        if not os.path.exists(backup_path):
            flash(f"Backup file not found: {backup_path}", "error")
            return redirect(url_for('restore_backup'))

        try:
            # Copy the selected backup to the user's database
            shutil.copy(backup_path, user_db_path)
            flash(f"Backup restored successfully from: {backup_path}", "success")
        except Exception as e:
            flash(f"Error restoring backup: {str(e)}", "error")
        return redirect(url_for('home'))
    print(f"Backup files found: {backups}")
    backups = [f for f in os.listdir(user_folder) if f.endswith('.db')]
    print(f"Backup files found with .db extension: {backups}")

    return render_template('restore_backup.html', backups=backups)





@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

# Run the Flask app
if __name__ == "__main__":
     app.run(host='0.0.0.0', port=5000,debug=True)
      