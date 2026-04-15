from config import get_db_connection

def migrate():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            print("❌ DB connection failed")
            return
        cursor = conn.cursor()
        
        print("Updating 'buses' table schema...")
        
        # Add columns if they don't exist
        try:
            cursor.execute("ALTER TABLE buses ADD COLUMN latitude DECIMAL(10,8);")
            print("Added 'latitude' column")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("'latitude' column already exists")
            else:
                print(f"Error adding 'latitude': {e}")

        try:
            cursor.execute("ALTER TABLE buses ADD COLUMN longitude DECIMAL(11,8);")
            print("Added 'longitude' column")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("'longitude' column already exists")
            else:
                print(f"Error adding 'longitude': {e}")

        try:
            cursor.execute("ALTER TABLE buses ADD COLUMN status VARCHAR(20) DEFAULT 'idle';")
            print("Added 'status' column")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("'status' column already exists")
            else:
                print(f"Error adding 'status': {e}")
        
        # Ensure buses 101, 102, 103 exist
        print("Ensuring demo buses exist...")
        demo_buses = [
            (101, 'RIT-101', 1, '1234'),
            (102, 'RIT-102', 2, '1234'),
            (103, 'RIT-103', 3, '1234')
        ]
        for bid, bnum, rid, pwd in demo_buses:
            cursor.execute("""
                INSERT INTO buses (bus_id, bus_number, route_id, password) 
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE bus_number = VALUES(bus_number)
            """, (bid, bnum, rid, pwd))
        
        conn.commit()
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == "__main__":
    migrate()
