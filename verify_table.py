import sqlite3

# Use a raw string for the database file path
db_file = r"C:\Users\User\python projects 2024\Personal Expense Tracker\expenses.db"

# Connect to the SQLite database
conn = sqlite3.connect(db_file)

# Verify if the "expenses" table exists
cursor = conn.cursor()
cursor.execute("""
    SELECT name FROM sqlite_master WHERE type='table' AND name='expenses';
""")
table_exists = cursor.fetchone()

if table_exists:
    print("Table 'expenses' exists in the database.")
else:
    print("Table 'expenses' does not exist in the database. You may need to create it.")

# Close the connection
conn.close()
