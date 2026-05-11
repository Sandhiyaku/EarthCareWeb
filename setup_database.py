import sqlite3

def create_connection():
    # Connects to (or creates) the database file
    conn = sqlite3.connect('earthcare.db')
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    # 1. Users Table (Stores User, Admin, and Worker logins)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,  -- 'user', 'admin', or 'worker'
            phone TEXT,
            address TEXT
        )
    ''')

    # 2. Bookings Table (Stores the waste collection requests)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            worker_id INTEGER,
            booking_date TEXT,
            time_slot TEXT,
            waste_type TEXT,
            status TEXT DEFAULT 'Pending', -- 'Pending', 'Assigned', 'Completed'
            address TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(worker_id) REFERENCES users(id)
        )
    ''')

    # Optional: Insert a dummy Admin so you can log in later
    # Password is 'admin123' (In a real app, always hash passwords!)
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
        print("Dummy Admin account created.")
    except sqlite3.IntegrityError:
        print("Admin account already exists.")

    conn.commit()
    conn.close()
    print("Database and Tables created successfully!")

if __name__ == '__main__':
    create_tables()