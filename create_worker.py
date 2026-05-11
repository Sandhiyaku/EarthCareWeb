import sqlite3
conn = sqlite3.connect('earthcare.db')
cursor = conn.cursor()

# Replace 'sam' with a username you have already registered
username_to_promote = 'sam' 

cursor.execute("UPDATE users SET role = 'worker' WHERE username = ?", (username_to_promote,))
conn.commit()
conn.close()
print(f"User {username_to_promote} is now a Worker!")