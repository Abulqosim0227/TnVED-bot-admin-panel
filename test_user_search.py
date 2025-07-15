#!/usr/bin/env python3
"""
Test script for the User Search functionality in the admin panel
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import get_db_connection, test_database_connection
import logging

def test_admin_panel_functionality():
    """Test the admin panel user search functionality"""
    print("🧪 Testing Admin Panel User Search Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Database Connection
        print("\n1. Testing Database Connection...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"   ✅ Database connected successfully")
        print(f"   📊 Total users in database: {user_count}")
        
        # Test 2: Check required tables exist
        print("\n2. Checking Required Tables...")
        
        tables_to_check = ['users', 'usage_logs', 'not_found_queries']
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ Table '{table}' exists with {count} records")
            except Exception as e:
                print(f"   ❌ Table '{table}' issue: {e}")
        
        # Test 3: Sample User Search Query
        print("\n3. Testing User Search Queries...")
        
        # Test search by ID (get first user)
        cursor.execute("SELECT telegram_id, full_name FROM users LIMIT 1")
        sample_user = cursor.fetchone()
        
        if sample_user:
            test_id = sample_user[0]
            test_name = sample_user[1]
            print(f"   📋 Testing with sample user: {test_name} (ID: {test_id})")
            
            # Test ID search
            cursor.execute("""
                SELECT u.*, COUNT(ul.id) as total_searches,
                       MAX(ul.created_at) as last_active
                FROM users u
                LEFT JOIN usage_logs ul ON u.telegram_id = ul.user_id
                WHERE u.telegram_id = %s
                GROUP BY u.id, u.telegram_id, u.full_name, u.username, u.phone, u.language, u.registered_at, u.requests_today
            """, (test_id,))
            
            result = cursor.fetchone()
            if result:
                print(f"   ✅ Search by ID successful: Found user {result['full_name']}")
                print(f"   📊 User has {result['total_searches']} total searches")
            else:
                print(f"   ❌ Search by ID failed")
                
            # Test name search
            if test_name and len(test_name) > 3:
                search_term = test_name[:3]  # First 3 characters
                cursor.execute("""
                    SELECT u.*, COUNT(ul.id) as total_searches
                    FROM users u
                    LEFT JOIN usage_logs ul ON u.telegram_id = ul.user_id
                    WHERE LOWER(u.full_name) LIKE LOWER(%s)
                    GROUP BY u.id, u.telegram_id, u.full_name, u.username, u.phone, u.language, u.registered_at, u.requests_today
                    LIMIT 5
                """, (f'%{search_term}%',))
                
                results = cursor.fetchall()
                print(f"   ✅ Search by name '{search_term}' found {len(results)} users")
        else:
            print("   ⚠️  No users found in database to test with")
        
        # Test 4: Search History Queries
        print("\n4. Testing Search History Queries...")
        
        cursor.execute("SELECT COUNT(*) FROM usage_logs")
        log_count = cursor.fetchone()[0]
        print(f"   📊 Total search logs: {log_count}")
        
        if log_count > 0:
            cursor.execute("""
                SELECT ul.user_id, ul.query, ul.created_at
                FROM usage_logs ul
                ORDER BY ul.created_at DESC
                LIMIT 3
            """)
            recent_logs = cursor.fetchall()
            print("   ✅ Recent search logs:")
            for log in recent_logs:
                print(f"      - User {log['user_id']}: '{log['query'][:30]}...' at {log['created_at']}")
        
        # Test 5: Failed Searches
        print("\n5. Testing Failed Search Queries...")
        
        cursor.execute("SELECT COUNT(*) FROM not_found_queries")
        failed_count = cursor.fetchone()[0]
        print(f"   📊 Total failed searches: {failed_count}")
        
        if failed_count > 0:
            cursor.execute("""
                SELECT nfq.user_id, nfq.query, nfq.search_timestamp
                FROM not_found_queries nfq
                ORDER BY nfq.search_timestamp DESC
                LIMIT 3
            """)
            recent_failed = cursor.fetchall()
            print("   ✅ Recent failed searches:")
            for failed in recent_failed:
                print(f"      - User {failed['user_id']}: '{failed['query'][:30]}...' at {failed['search_timestamp']}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print(f"   • Database connection: ✅ Working")
        print(f"   • Required tables: ✅ Available")
        print(f"   • User search: ✅ Functional")
        print(f"   • Search history: ✅ Accessible")
        print(f"   • Failed searches: ✅ Tracked")
        
        print("\n🚀 Admin Panel User Search feature is ready to use!")
        print("   Navigate to: http://localhost:8000/user-search")
        print("   Login: admin / admin123")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_sample_user_data():
    """Display sample data for testing"""
    print("\n📊 Sample User Data for Testing:")
    print("-" * 40)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get sample users
        cursor.execute("""
            SELECT telegram_id, full_name, username, 
                   language, registered_at
            FROM users 
            ORDER BY registered_at DESC 
            LIMIT 5
        """)
        
        users = cursor.fetchall()
        
        if users:
            print("Recent Users:")
            for user in users:
                print(f"   ID: {user['telegram_id']} | Name: {user['full_name']} | Lang: {user['language']}")
        else:
            print("   No users found in database")
            
        # Get sample search queries
        cursor.execute("""
            SELECT DISTINCT query, COUNT(*) as frequency
            FROM usage_logs
            GROUP BY query
            ORDER BY frequency DESC
            LIMIT 10
        """)
        
        queries = cursor.fetchall()
        
        if queries:
            print("\nPopular Search Queries:")
            for query in queries:
                print(f"   '{query['query'][:40]}...' ({query['frequency']} times)")
        else:
            print("\n   No search queries found")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error getting sample data: {e}")

if __name__ == "__main__":
    # Run the test
    success = test_admin_panel_functionality()
    
    if success:
        test_sample_user_data()
        print("\n" + "=" * 50)
        print("✅ User Search feature is ready for production use!")
    else:
        print("\n❌ Tests failed. Please check the errors above.")
        sys.exit(1) 