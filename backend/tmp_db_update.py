from config import get_db_connection

def update_schema():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            print("❌ DB connection failed")
            return
        cursor = conn.cursor()
        
        print("🛠️  Adding UNIQUE constraint on bus_id in live_locations...")
        # First, we might need to remove duplicates before adding the constraint
        # But for 'live' data, we can just clear it or let the user decide.
        # Let's just try to add the constraint. If it fails due to existing duplicates,
        # we'll handle it.
        try:
            cursor.execute("ALTER TABLE live_locations ADD UNIQUE (bus_id);")
            conn.commit()
            print("✅ UNIQUE constraint added successfully")
        except Exception as e:
            if "Duplicate entry" in str(e):
                print("⚠️  Duplicates found. Cleaning up live_locations first...")
                # Keep only the latest entry per bus
                cursor.execute("""
                    DELETE FROM live_locations 
                    WHERE id NOT IN (
                        SELECT id FROM (
                            SELECT MAX(id) as id FROM live_locations GROUP BY bus_id
                        ) as tmp
                    )
                """)
                cursor.execute("ALTER TABLE live_locations ADD UNIQUE (bus_id);")
                conn.commit()
                print("✅ Cleaned up and added UNIQUE constraint")
            else:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Error connecting to DB: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == "__main__":
    update_schema()
