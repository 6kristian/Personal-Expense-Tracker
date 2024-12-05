import sqlite3
import hashlib
import matplotlib.pyplot as plt
import datetime
import fpdf
import csv
import os
import json
import schedule
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from werkzeug.security import generate_password_hash






SCOPES = ['https://www.googleapis.com/auth/drive.file'] 


# Database setup
def setup_database():
    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
    )
    ''')

    # Create expenses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category INTEGER,
        amount REAL,
        date TEXT,
        description TEXT,
        user_id INTEGER,
        FOREIGN KEY (category_id) REFERENCES categories (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    #Create budget table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS budget (
        user_id INTEGER PRIMARY KEY,
        amount REAL NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')


    conn.commit()
    conn.close()



# User registration
def register_user():
    """
    Registers a new user by asking for a username and password,
    hashing the password, and storing the data in the database.
    """
    # Prompt the user for input
    username = input("Enter a new username: ").strip()
    password = input("Enter a new password: ").strip()

    # Validate inputs
    if not username or not password:
        print("Error: Username and password cannot be empty.")
        return

    # Hash the password for secure storage
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        # Open a database connection
        with sqlite3.connect('expenses.db') as conn:
            cursor = conn.cursor()

            # Insert the new user into the database
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                (username, password_hash)
            )
            conn.commit()  # Save the changes
            print("Registration successful!")
    
    except sqlite3.IntegrityError:
        # Handle the case where the username already exists
        print("Error: Username already exists. Please try a different one.")
    
    except sqlite3.Error as e:
        # Catch any other SQLite-related errors
        print(f"Database error: {e}")


# User login
def login_user():
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, password_hash))
        user = cursor.fetchone()
        

    if user:
        print("Login successful!")
        return user[0]  # Return user ID
    else:
        print("Invalid username or password.")
        return None


# Add expense
def add_expenses(user_id):
    date = input("Enter Date (YYYY-MM-DD): ")
    category = input("Enter Category (e.g., Food, Travel): ")
    amount = float(input("Enter Amount: "))

    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (user_id, date, category, amount) VALUES (?, ?, ?, ?)",
                       (user_id, date, category, amount))
        conn.commit()
    print("Expense added successfully!")


# View expenses
def view_expenses(user_id):
    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date, category, amount FROM expenses WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()

    if not rows:
        print("\nNo expenses found!")
    else:
        print("\nYour Expenses:")
        for row in rows:
            print(f"Date: {row[0]}, Category: {row[1]}, Amount: {row[2]:.2f}")


# Summarize expenses
def summarize_expenses(user_id):
    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category", (user_id,))
        data = cursor.fetchall()
        

    if not data:
        print("\nNo expenses to summarize!")
        return

    categories = [row[0] for row in data]
    totals = [row[1] for row in data]

    # Plot summary
    plt.figure(figsize=(8, 5))
    plt.bar(categories, totals, color='skyblue')
    plt.title("Expenses Summary by Category")
    plt.xlabel("Category")
    plt.ylabel("Total Amount")
    plt.show()



#edit expenses
def edit_expenses(user_id):
    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id,date,category,amount FROM expenses WHERE user_id = ?",(user_id,))
        rows = cursor.fetchall()

    if not rows:
        print("\nNo Expenses Found!")
        return

    print("\nYour Expenses: ")
    for row in rows:
        print(f"ID: {row[0]}, Date: {row[1]}, Category: {row[2]}, Amount: {row[3]:.2f}")
        

    try:
        expense_id = int(input("\nEnter the ID of the expenses you want to edit: "))
        cursor.execute("SELECT * FROM expenses WHERE id = ? and user_id = ?",(expense_id,user_id))
        expense = cursor.fetchone()

        if expense:
            new_date = input(f"Enter new date(YYYY-MM-DD) [Current: {expense[2]}]: ") or expense[2]
            new_category = input(f"Enter new category [Current: {expense[3]}]: ") or expense[3]
            new_amount = input(f"Enter new amount [Current: {expense[4]:.2f}]: ") or expense[4]
            cursor.execute(
                "UPDATE expenses SET date = ?, category = ?, amount = ? WHERE id = ? and user_id = ?",
                (new_date,new_category,float(new_amount),expense_id,user_id)
             )
            conn.commit()
            print("Expense updated successfully!")
        else:
            print("Expense ID not found.")
    except ValueError:
        print("Invalid input,please put a valid input")
   


    #delete expenese
def delete_expenses(user_id):
    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()
    cursor.execute("SELECT id, date, category, amount FROM expenses WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()

    if not rows:
        print("\nNo expenses found!")
        return

    print("\nYour Expenses:")
    for row in rows:
        print(f"ID: {row[0]}, Date: {row[1]}, Category: {row[2]}, Amount: {row[3]:.2f}")

    try:
        expense_id = int(input("\nEnter the ID of the expense you want to delete: "))
        cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
        if cursor.rowcount > 0:
            conn.commit()
            print("Expense deleted successfully!")
        else:
            print("Expense ID not found!")
    except ValueError:
        print("Invalid input. Please enter a valid number.")
    



def add_recurrence_column():
    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()

    # Disable foreign key checks temporarily
    cursor.execute("PRAGMA foreign_keys=off;")
    try:
        cursor.execute("ALTER TABLE expenses ADD COLUMN recurrence TEXT;")
        print("Recurrence column added successfully.")
    except sqlite3.OperationalError:
        print("Recurrence column already exists.")
    finally:
        cursor.execute("PRAGMA foreign_keys=on;")  # Re-enable foreign key checks
    conn.close()




    add_recurrence_column() 



def process_recurring_expenses(user_id):
    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()

    #Fetch recurring expenses for the user
    cursor.execute("SELECT id,date,category,amount,recurrence FROM expenses WHERE user_id = ? and recurrence  IS NOT NULL",(user_id,))
    recurring_expenses = cursor.fetchall()

    if not recurring_expenses:
        print("\nNo recurring expenses to process.")
        return

    today = datetime.date.today()

    for expense in recurring_expenses:
        expense_id, last_date, category,amount, recurrence = expense
        last_date = datetime.datetime.strptime(last_date, "%Y-%m-%d").date()

        next_date = None
        #calculate next  date for  recurrence
        if recurrence == "Monthly":
            next_date = last_date +datetime.timedelta(days = 30)
        elif recurrence == "Weekly":
            next_date = last_date + datetime.timedelta(days= 7)
        


        if next_date is None:
            print(f"Skipping invalid recurrence type for expense {expense_id}: {category} ({recurrence})")
            continue


                # Add the recurring expense if it's due
        if next_date <= today:
            cursor.execute("INSERT INTO expenses (user_id,date,category,amount,recurrence) VALUES (?,?,?,?,?)",
                           (user_id, next_date.strftime("%Y-%m-%d"),category,amount,recurrence))
            cursor.execute("UPDATE expenses SET date = ? WHERE id = ?", (next_date.strftime("%Y-%m-%d"), expense_id))
            print(f"Processed recurring expense: {category} ({recurrence}) for {next_date.strftime('%Y-%m-%d')}.")

    conn.commit()
  


def set_budget(user_id):
    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()
        try:
            amount = float(input("Enter your monthly budget: "))
            cursor.execute("INSERT OR REPLACE INTO budget (user_id, amount) VALUES (?,?)",(user_id,amount))
            conn.commit()
            print(f"Monthly budget set to {amount:.2f}!")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            
    

def check_budget(user_id):
    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()

            # Get current month's total expenses

        today = datetime.date.today()
        month_start = today.replace(day = 1).strftime('%Y-%m-%d')
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date >= ?", (user_id, month_start))
        total_expenses = cursor.fetchone()[0] or 0.0

        #get budget

        cursor.execute("SELECT amount FROM budget WHERE user_id = ?",(user_id,))
        budget = cursor.fetchone()

        if budget:
            budget_amount = budget[0]
            print(f"\nYour Budget: {budget_amount:.2f}")
            print(f"Total Expenses for {today.strftime('%B')}: {total_expenses:.2f}")

            if total_expenses > budget_amount:
                print("⚠️ You have exceeded your budget!")
            elif total_expenses > 0.9 * budget_amount:
                print("⚠️ You are close to exceeding your budget.")
            else:
                print("✅ You are within your budget.")
        else:
            print("No budget set. Use the 'Set Budget' option to define one.")      


def search_and_filter_expenses(user_id):
    print("\nSearch and Filter Expenses")
    print("Filter options:")
    print("1. By Date Range")
    print("2. By Category")
    print("3. By Amount Range")
    print("4. Combine Filters (e.g., Date + Category)")
    print("5. Exit")

    choice = input("Enter your choice: ")

    query = "SELECT date, category, amount FROM expenses WHERE user_id = ?"

    filters = [user_id]

    if choice == "1":
        start_date = input("Enter start date (YYYY-MM-DD): ")
        end_date = input("Enter end date (YYYY-MM-DD): ")
        query += " AND date BETWEEN ? AND ?"
        filters.extend([start_date,end_date])
    elif choice == "2":
        category = input("Put category:")
        query += " AND category = ?"

        filters.append(category)
    elif choice == "3":
        min_amount = float(input("Enter minimum amount: "))
        max_amount = float(input("Enter maximum amount: "))
        query += " AND amount BETWEEN ? AND ?"
        filters.extend([min_amount, max_amount])
    elif choice == "4":
        start_date = input("Enter start date (YYYY-MM-DD): ")
        end_date = input("Enter end date (YYYY-MM-DD): ")
        category= input("Enter category: ")
        query += " AND date BETWEEN ? AND ? AND category = ?"

        filters.extend([start_date,end_date,category])
    elif choice == "5":
        print("Exiting filter menu.")
        return
    else:
        print("Invalid choice!Please try again!")


        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute(query, filters)
        results = cursor.fetchall()


        if not results:
            print("\nNo expenses found matching the criteria.")
        else:
            print("\nFiltered Expenses:")
            for row in results:
                print(f"Date: {row[0]}, Category: {row[1]}, Amount: {row[2]:.2f}")

#reports
def generate_report(user_id):
    print("\nGenerate Report")
    start_date = input("Enter start date (YYYY-MM-DD)")
    end_date = input("Enter end date (YYYY-MM-DD)")
    print("Select report format")
    print("1. CSV")
    print("2. PDF")
    print("3. BOTH")
    format_choice =input("Enter your choice: ")

    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT date,category,amount FROM expenses WHERE user_id = ? AND date  BETWEEN ? AND ?",
            (user_id, start_date, end_date))
        expenses = cursor.fetchall()

        if not expenses:
            print("\nNo expenses found for the selected period.")
            return

        if format_choice in ['1', '3']:  # CSV
            export_to_csv(user_id, expenses, start_date, end_date)

        if format_choice in ['2', '3']:  # PDF
            export_to_pdf(user_id, expenses, start_date, end_date)
            



            #export to CSV
def export_to_csv(user_id,expenses,start_date,end_date):
    filename = f"user_{user_id}_report_{start_date}_to_{end_date}.csv"
    with open(filename,mode = 'w',newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date","Category","Amount"])
        writer.writerows(expenses)
    print(f"\nCSV report generated: {filename}")


    #export to PDF
def export_to_pdf(user_id, expenses, start_date, end_date):
    filename = f"user_{user_id}_report_{start_date}_to_{end_date}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []

    data = [["Date", "Category", "Amount"]] + expenses
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    doc.build(elements)

    print(f"\nPDF report generated: {filename}")



#back up to google drive


def backup_to_google_drive():
    try:
        # Load credentials from token.json
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        service = build("drive", "v3", credentials=creds)

        # Metadata for the uploaded file
        file_metadata = {"name": "expenses_backup.db"}
        media = MediaFileUpload("expenses.db", mimetype="application/x-sqlite3")

        # Upload to Google Drive
        file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        print(f"Backup uploaded successfully! File ID: {file.get('id')}")

    except FileNotFoundError:
        print("Error: token.json file not found. Run the authorization flow to generate it.")
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")


def restore_from_google_drive():
    try:
        # Load credentials from token.json
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        service = build("drive", "v3", credentials=creds)

        # Search for backup file in Google Drive
        query = "name = 'expenses_backup.db'"
        results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
        items = results.get("files", [])

        if not items:
            print("No backup found on your drive.")
            return

        # Download the file
        file_id = items[0]["id"]
        request = service.files().get_media(fileId=file_id)
        with open("expenses.db", "wb") as f:
            f.write(request.execute())
        print("Database restored successfully from Google Drive!")

    except FileNotFoundError:
        print("Error: token.json file not found. Run the authorization flow to generate it.")
    except Exception as e:
        print(f"Error restoring from Google Drive: {e}")




# User menu
def user_menu(user_id):
    while True:
        print("\nPersonal Expense Tracker")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Summarize Expenses")
        print("4. Edit Expense")
        print("5. Delete Expense")
        print("6. Process Recurring Expenses")
        print("7. Set Monthly Budget")
        print("8. Check Budget Status")
        print("9. Generate report")
        print("10. Search and Filter Expenses")
        print("11. Backup to Google Drive")
        print("12. Restore with Google Drive")
        print("0. Logout")

        choice = input("Enter your choice: ")
        if choice == "1":
            add_expenses(user_id)
        elif choice == "2":
            view_expenses(user_id)
        elif choice == "3":
            summarize_expenses(user_id)
        elif choice == "4":
            edit_expenses(user_id)
        elif choice == "5":
            delete_expenses(user_id)
        elif choice == "6":
            process_recurring_expenses(user_id)
        elif choice == "7":
            set_budget(user_id)
        elif choice == "8":
            check_budget(user_id)
        elif choice == "9":
            generate_report(user_id)
        elif choice == "10":
            search_and_filter_expenses(user_id)
        elif choice == "11":
            backup_to_google_drive()
        elif choice == "12":
            restore_from_google_drive()
        elif choice == "0":
            print("Logging out...")
            break
        else:
            print("Invalid choice, please try again!")


# Main program
def main():
    setup_database()
    print("Welcome to the Personal Expense Tracker!")

    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter your choice: ")
        if choice == "1":
            register_user()
        elif choice == "2":
            user_id = login_user()
            if user_id:
                user_menu(user_id)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please try again!")


if __name__ == "__main__":
    main()
