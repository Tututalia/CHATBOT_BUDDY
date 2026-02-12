"""
Script to clean up duplicate payload entries
Keeps the latest entry for each customer_id
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "chat_history.db")

def cleanup_duplicates():
    """Remove duplicate customer entries, keeping only the latest one"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Checking for duplicates...")
    
    # Find customers with multiple entries
    cursor.execute("""
        SELECT customer_id, COUNT(*) as count 
        FROM payload 
        GROUP BY customer_id 
        HAVING count > 1
    """)
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"\nFound {len(duplicates)} customers with duplicate entries:")
        for customer_id, count in duplicates:
            print(f"  - {customer_id}: {count} entries")
        
        # For each customer with duplicates, keep only the one with data, or the last rowid
        for customer_id, _ in duplicates:
            cursor.execute("""
                SELECT rowid, payload 
                FROM payload 
                WHERE customer_id = ? 
                ORDER BY rowid DESC
            """, (customer_id,))
            
            all_entries = cursor.fetchall()
            
            # Find the first entry with non-NULL payload, or keep the last one
            keep_rowid = None
            for rowid, payload in all_entries:
                if payload and payload != 'null' and payload != 'NULL':
                    keep_rowid = rowid
                    break
            
            # If no entry has payload, keep the last one
            if not keep_rowid:
                keep_rowid = all_entries[0][0]
            
            # Delete all other entries for this customer
            cursor.execute("""
                DELETE FROM payload 
                WHERE customer_id = ? AND rowid != ?
            """, (customer_id, keep_rowid))
            
            print(f"  ✓ Cleaned up {customer_id}, kept rowid {keep_rowid}")
        
        conn.commit()
        print(f"\n✅ Cleanup complete! Removed duplicates.")
    else:
        print("✓ No duplicates found!")
    
    # Show current state
    print("\nCurrent payload table state:")
    cursor.execute("SELECT customer_id, payload FROM payload ORDER BY customer_id")
    rows = cursor.fetchall()
    
    for customer_id, payload in rows:
        has_data = "✓ HAS DATA" if payload and payload != 'NULL' else "✗ NULL"
        print(f"  {customer_id}: {has_data}")
    
    conn.close()

if __name__ == "__main__":
    print("="*60)
    print("Payload Duplicate Cleanup Script")
    print("="*60)
    cleanup_duplicates()
    print("\n" + "="*60)
