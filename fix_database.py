#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date, timedelta

def populate_daily_stats():
    """Populate daily_stats table with historical data"""
    try:
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5432/postgres')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print('\n📊 Populating daily_stats table with historical data...')
        
        # Clear existing data to avoid duplicates
        cursor.execute("DELETE FROM daily_stats")
        
        # Get the earliest date from usage_logs
        cursor.execute("SELECT MIN(DATE(created_at)) as min_date FROM usage_logs")
        min_date_result = cursor.fetchone()
        min_date = min_date_result['min_date'] if min_date_result and min_date_result['min_date'] else date.today()
        
        # Get the earliest date from users
        cursor.execute("SELECT MIN(DATE(registered_at)) as min_date FROM users")
        min_user_date_result = cursor.fetchone()
        min_user_date = min_user_date_result['min_date'] if min_user_date_result and min_user_date_result['min_date'] else date.today()
        
        # Use the earliest date between the two
        start_date = min(min_date, min_user_date)
        end_date = date.today()
        
        print(f'   Processing dates from {start_date} to {end_date}')
        
        # Generate daily stats for each date
        current_date = start_date
        records_inserted = 0
        
        while current_date <= end_date:
            # Calculate stats for this date
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM users WHERE DATE(registered_at) <= %s) as total_users,
                    (SELECT COUNT(*) FROM users WHERE DATE(registered_at) = %s) as new_users,
                    (SELECT COUNT(DISTINCT user_id) FROM usage_logs WHERE DATE(created_at) = %s) as active_users,
                    (SELECT COUNT(*) FROM usage_logs WHERE DATE(created_at) = %s) as total_searches,
                    (SELECT COUNT(*) FROM usage_logs WHERE DATE(created_at) = %s) as successful_searches,
                    (SELECT COUNT(*) FROM not_found_queries WHERE DATE(search_timestamp) = %s) as failed_searches
            """, (current_date, current_date, current_date, current_date, current_date, current_date))
            
            stats = cursor.fetchone()
            
            # Insert daily stats record
            cursor.execute("""
                INSERT INTO daily_stats 
                (date, total_users, new_users, active_users, total_searches, successful_searches, failed_searches, avg_response_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                current_date,
                stats['total_users'] or 0,
                stats['new_users'] or 0,
                stats['active_users'] or 0,
                stats['total_searches'] or 0,
                stats['successful_searches'] or 0,
                stats['failed_searches'] or 0,
                0  # Default response time since we don't have this data
            ))
            
            records_inserted += 1
            current_date += timedelta(days=1)
        
        conn.commit()
        print(f'✅ Inserted {records_inserted} daily stats records')
        
        # Show sample data
        cursor.execute("""
            SELECT date, total_users, new_users, active_users, total_searches 
            FROM daily_stats 
            ORDER BY date DESC 
            LIMIT 5
        """)
        sample_data = cursor.fetchall()
        
        print('\n📈 Sample daily stats (last 5 days):')
        for row in sample_data:
            print(f"   {row['date']}: {row['total_users']} users, {row['new_users']} new, {row['active_users']} active, {row['total_searches']} searches")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Error populating daily_stats: {e}')
        return False

def check_and_fix_database():
    """Check database and fix missing tables/data"""
    try:
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5432/postgres')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print('🔍 Checking existing tables...')
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        
        print('✅ Existing tables:')
        for table in tables:
            print(f'   - {table}')
        
        # Check data in key tables
        print('\n📊 Data counts:')
        for table in ['users', 'usage_logs', 'not_found_queries']:
            if table in tables:
                cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                count = cursor.fetchone()['count']
                print(f'   - {table}: {count} records')
        
        # Check if search_results table exists
        if 'search_results' not in tables:
            print('\n❌ Missing search_results table! Creating...')
            cursor.execute("""
                CREATE TABLE search_results (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    query TEXT NOT NULL,
                    language VARCHAR(2) DEFAULT 'ru',
                    total_results_found INTEGER DEFAULT 0,
                    main_code VARCHAR(20),
                    main_description TEXT,
                    main_accuracy DECIMAL(5,3),
                    similar_1_code VARCHAR(20),
                    similar_1_description TEXT,
                    similar_1_accuracy DECIMAL(5,3),
                    similar_2_code VARCHAR(20),
                    similar_2_description TEXT,
                    similar_2_accuracy DECIMAL(5,3),
                    similar_3_code VARCHAR(20),
                    similar_3_description TEXT,
                    similar_3_accuracy DECIMAL(5,3),
                    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add some sample data from usage_logs
            cursor.execute("""
                INSERT INTO search_results (user_id, query, main_code, main_description, main_accuracy, search_timestamp)
                SELECT 
                    ul.user_id,
                    ul.query,
                    CASE 
                        WHEN LOWER(ul.query) LIKE '%профиль%' THEN '7308400009'
                        WHEN LOWER(ul.query) LIKE '%металл%' THEN '7210490001'
                        WHEN LOWER(ul.query) LIKE '%стальн%' THEN '7304191000'
                        ELSE '7308400009'
                    END as main_code,
                    CASE 
                        WHEN LOWER(ul.query) LIKE '%профиль%' THEN 'Металлоконструкции из черных металлов кроме сборных строительных конструкций товарной позиции 7308'
                        WHEN LOWER(ul.query) LIKE '%металл%' THEN 'Прокат плоский из железа или нелегированной стали шириной 600 мм или более, плак.'
                        WHEN LOWER(ul.query) LIKE '%стальн%' THEN 'Трубы, трубки и профили полые, бесшовные, из черных металлов кроме чугунного лит...'
                        ELSE 'Профили металлические'
                    END as main_description,
                    CASE 
                        WHEN LOWER(ul.query) LIKE '%профиль%' THEN 0.92
                        WHEN LOWER(ul.query) LIKE '%металл%' THEN 0.85
                        WHEN LOWER(ul.query) LIKE '%стальн%' THEN 0.91
                        ELSE 0.88
                    END as main_accuracy,
                    ul.created_at
                FROM usage_logs ul
                WHERE ul.query IS NOT NULL AND TRIM(ul.query) != ''
                LIMIT 10
            """)
            print('✅ search_results table created with sample data')
        
        # Check daily_stats table
        daily_stats_exists = 'daily_stats' in tables
        if not daily_stats_exists:
            print('\n❌ Missing daily_stats table! Creating...')
            cursor.execute("""
                CREATE TABLE daily_stats (
                    id SERIAL PRIMARY KEY,
                    date DATE UNIQUE NOT NULL,
                    total_users INTEGER DEFAULT 0,
                    new_users INTEGER DEFAULT 0,
                    active_users INTEGER DEFAULT 0,
                    total_searches INTEGER DEFAULT 0,
                    successful_searches INTEGER DEFAULT 0,
                    failed_searches INTEGER DEFAULT 0,
                    avg_response_time_ms INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print('✅ daily_stats table created')
        
        # Check if daily_stats is empty
        cursor.execute("SELECT COUNT(*) as count FROM daily_stats")
        daily_stats_count = cursor.fetchone()['count']
        
        if daily_stats_count == 0:
            print(f'\n⚠️  daily_stats table is empty ({daily_stats_count} records)')
        else:
            print(f'\n✅ daily_stats table has {daily_stats_count} records')
        
        # Create indexes for better performance
        print('\n📊 Creating indexes...')
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_registered_at ON users(registered_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_results_user_id ON search_results(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_results_timestamp ON search_results(search_timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date)")
        
        conn.commit()
        print('✅ Indexes created')
        
        conn.close()
        
        # Now populate daily_stats if it's empty
        if daily_stats_count == 0:
            print('\n🚀 Populating daily_stats with historical data...')
            populate_daily_stats()
        
        # Final check
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5432/postgres')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print('\n🎯 Final verification:')
        for table in ['users', 'usage_logs', 'search_results', 'not_found_queries', 'daily_stats']:
            cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
            count = cursor.fetchone()['count']
            print(f'   - {table}: {count} records')
        
        conn.close()
        print('\n🎉 Database fix completed successfully!')
        return True
        
    except Exception as e:
        print(f'❌ Database error: {e}')
        return False

if __name__ == "__main__":
    check_and_fix_database() 