import sqlite3

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
        FOREIGN KEY (category) REFERENCES categories (id),
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

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    print("Empty database 'expenses.db' created with the necessary tables.")


def setup_pricing_table():
    with sqlite3.connect('expenses.db') as conn:
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            features TEXT NOT NULL

        );
        ''')

        cursor.execute('''
        INSERT INTO plans (name,price,features)
        VALUES 
            ('Free',0,'Track up to 50 expenses;Basic reporting;Email support'),
            ('Premium', 9.99, 'Unlimited expenses;Advanced reporting;Priority email support;Custom categories'),
            ('Enterprise', 49.99, 'Unlimited expenses;Team collaboration;Custom reports & dashboards;Dedicated account manager');
        ''')
        conn.commit()
# Run the function to create the database
if __name__ == "__main__":
    setup_database()
    setup_pricing_table()
