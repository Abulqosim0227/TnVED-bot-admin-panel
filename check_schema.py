#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor

def check_table_schema(table_name):
    try:
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5432/postgres')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print(f'\n=== {table_name.upper()} TABLE SCHEMA ===')
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cursor.fetchall()
        if not columns:
            print(f"❌ Table '{table_name}' not found!")
            return
            
        for row in columns:
            print(f"  {row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
        
        print(f'\n=== SAMPLE DATA FROM {table_name.upper()} ===')
        cursor.execute(f'SELECT * FROM {table_name} LIMIT 3')
        sample = cursor.fetchall()
        
        if sample:
            for i, row in enumerate(sample, 1):
                print(f"Row {i}: {dict(row)}")
        else:
            print("No data in table")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking {table_name}: {e}")

if __name__ == "__main__":
    print("🔍 Checking Database Schema...")
    
    tables_to_check = ['users', 'usage_logs', 'not_found_queries']
    
    # Find classifier table
    print("\n🔍 Looking for classifier tables...")
    conn = psycopg2.connect('postgresql://postgres:123456@localhost:5432/postgres')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%classifier%' OR table_name LIKE 'm_classifier%')
        ORDER BY table_name
    """)
    classifier_tables = cursor.fetchall()
    if classifier_tables:
        print("Found classifier tables:")
        for table in classifier_tables:
            print(f"  - {table[0]}")
            tables_to_check.append(table[0])
    else:
        print("No classifier tables found. Checking for any tables with 'hs' or 'code'...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE '%hs%' OR table_name LIKE '%code%')
            ORDER BY table_name
        """)
        code_tables = cursor.fetchall()
        for table in code_tables:
            print(f"  - {table[0]}")
            tables_to_check.append(table[0])
    
    cursor.close()
    conn.close()
    
    for table in tables_to_check:
        check_table_schema(table)
        print("-" * 60) 