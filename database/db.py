import sqlite3

conn = sqlite3.connect("data/lms.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_code TEXT,
    full_name TEXT,
    class_name TEXT,
    status TEXT
)
""")

conn.commit()
conn.close()

print("Database created")