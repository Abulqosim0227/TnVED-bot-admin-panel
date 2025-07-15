#!/usr/bin/env python3
"""
Daily Stats Update Script
Run this script daily (e.g., via cron job) to update the daily_stats table
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_stats_update.log'),
        logging.StreamHandler()
    ]
)

def update_daily_stats():
    """Update daily_stats table with today's data"""
    try:
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5432/postgres')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        logging.info(f"🔄 Updating daily stats for {yesterday} and {today}")
        
        # Update stats for yesterday (final) and today (current)
        for target_date in [yesterday, today]:
            logging.info(f"   Processing {target_date}")
            
            # Calculate stats for this date
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM users WHERE DATE(registered_at) <= %s) as total_users,
                    (SELECT COUNT(*) FROM users WHERE DATE(registered_at) = %s) as new_users,
                    (SELECT COUNT(DISTINCT user_id) FROM usage_logs WHERE DATE(created_at) = %s) as active_users,
                    (SELECT COUNT(*) FROM usage_logs WHERE DATE(created_at) = %s) as total_searches,
                    (SELECT COUNT(*) FROM usage_logs WHERE DATE(created_at) = %s) as successful_searches,
                    (SELECT COUNT(*) FROM not_found_queries WHERE DATE(search_timestamp) = %s) as failed_searches
            """, (target_date, target_date, target_date, target_date, target_date, target_date))
            
            stats = cursor.fetchone()
            
            # Insert or update daily stats record
            cursor.execute("""
                INSERT INTO daily_stats 
                (date, total_users, new_users, active_users, total_searches, successful_searches, failed_searches, avg_response_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    total_users = EXCLUDED.total_users,
                    new_users = EXCLUDED.new_users,
                    active_users = EXCLUDED.active_users,
                    total_searches = EXCLUDED.total_searches,
                    successful_searches = EXCLUDED.successful_searches,
                    failed_searches = EXCLUDED.failed_searches,
                    avg_response_time_ms = EXCLUDED.avg_response_time_ms,
                    created_at = CURRENT_TIMESTAMP
            """, (
                target_date,
                stats['total_users'] or 0,
                stats['new_users'] or 0,
                stats['active_users'] or 0,
                stats['total_searches'] or 0,
                stats['successful_searches'] or 0,
                stats['failed_searches'] or 0,
                0  # Default response time since we don't have this data
            ))
            
            logging.info(f"   ✅ Updated stats for {target_date}: {stats['total_users']} users, {stats['new_users']} new, {stats['active_users']} active, {stats['total_searches']} searches")
        
        conn.commit()
        
        # Show recent stats
        cursor.execute("""
            SELECT date, total_users, new_users, active_users, total_searches 
            FROM daily_stats 
            ORDER BY date DESC 
            LIMIT 7
        """)
        recent_stats = cursor.fetchall()
        
        logging.info("📈 Recent daily stats (last 7 days):")
        for row in recent_stats:
            logging.info(f"   {row['date']}: {row['total_users']} users, {row['new_users']} new, {row['active_users']} active, {row['total_searches']} searches")
        
        conn.close()
        logging.info("✅ Daily stats update completed successfully!")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error updating daily stats: {e}")
        return False

def cleanup_old_stats(days_to_keep=90):
    """Clean up old daily stats records (keep last N days)"""
    try:
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5432/postgres')
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        cursor.execute("DELETE FROM daily_stats WHERE date < %s", (cutoff_date,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logging.info(f"🧹 Cleaned up {deleted_count} old daily stats records (older than {cutoff_date})")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error cleaning up old stats: {e}")
        return False

if __name__ == "__main__":
    logging.info("🚀 Starting daily stats update...")
    
    # Update daily stats
    if update_daily_stats():
        # Clean up old records (keep last 90 days)
        cleanup_old_stats(90)
        logging.info("🎉 Daily stats update process completed!")
    else:
        logging.error("❌ Daily stats update failed!") 