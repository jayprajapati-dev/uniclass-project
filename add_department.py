import sqlite3
import os

def add_department_column():
    # Get the database path
    db_path = os.path.join('instance', 'uniclass.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add the department column
        cursor.execute('ALTER TABLE user ADD COLUMN department VARCHAR(100)')
        conn.commit()
        print("Successfully added department column")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
        print("Trying alternative approach...")
        
        # Create a new table with the updated schema
        cursor.execute('''
            CREATE TABLE user_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(128),
                role VARCHAR(20) DEFAULT 'student',
                department VARCHAR(100)
            )
        ''')
        
        # Copy data from old table to new table
        cursor.execute('''
            INSERT INTO user_new (id, username, email, password_hash, role)
            SELECT id, username, email, password_hash, role FROM user
        ''')
        
        # Drop the old table
        cursor.execute('DROP TABLE user')
        
        # Rename the new table to user
        cursor.execute('ALTER TABLE user_new RENAME TO user')
        
        conn.commit()
        print("Successfully recreated user table with department column")
    
    finally:
        conn.close()

if __name__ == '__main__':
    add_department_column() 