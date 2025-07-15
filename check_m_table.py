#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

def check_m_classifier():
    try:
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5432/postgres')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("Checking m_classifier_hs1 table...")
        
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'm_classifier_hs1'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("\nTable structure:")
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']}")
        
        # Count total records
        cursor.execute("SELECT COUNT(*) as count FROM m_classifier_hs1")
        total = cursor.fetchone()['count']
        print(f"\nTotal records: {total}")
        
        # Search for construction/metal profile codes
        print("\nSearching for construction/profile related codes...")
        cursor.execute("""
            SELECT cs_code, cs_fullname 
            FROM m_classifier_hs1 
            WHERE LOWER(cs_fullname) LIKE '%профил%' 
            OR LOWER(cs_fullname) LIKE '%оцинков%'
            OR LOWER(cs_fullname) LIKE '%гипсокартон%'
            OR LOWER(cs_fullname) LIKE '%металл%'
            OR cs_code LIKE '72%'
            OR cs_code LIKE '73%'
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        print(f"Found {len(results)} construction-related codes:")
        for row in results:
            print(f"  {row['cs_code']} -> {row['cs_fullname'][:80]}...")
        
        # Check what's causing potato codes to appear
        print("\nChecking codes starting with 07 (should be agriculture)...")
        cursor.execute("""
            SELECT cs_code, cs_fullname 
            FROM m_classifier_hs1 
            WHERE cs_code LIKE '07%'
            LIMIT 5
        """)
        
        agri_results = cursor.fetchall()
        for row in agri_results:
            print(f"  {row['cs_code']} -> {row['cs_fullname'][:60]}...")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_m_classifier() 