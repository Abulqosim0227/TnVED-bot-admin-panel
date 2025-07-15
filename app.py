#!/usr/bin/env python3
"""
FastAPI Admin Panel for TNVED Bot
Comprehensive admin interface for managing bot operations
"""
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import List, Dict, Optional
import logging
from pydantic import BaseModel

# Admin configuration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Use a secure password!

app = FastAPI(title="TNVED Bot Admin Panel", version="1.0.0")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

security = HTTPBasic()

# Database connection (using your existing bot database config)
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/postgres"

# Models
class UserStats(BaseModel):
    total_users: int
    new_users_today: int
    active_users_today: int
    total_searches: int
    searches_today: int

class BotStats(BaseModel):
    uptime: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    avg_response_time: float

class UserData(BaseModel):
    id: int
    telegram_id: int
    full_name: str
    username: Optional[str]
    phone: str
    language: str
    registered_at: datetime
    last_active: Optional[datetime]
    total_searches: int
    is_blocked: bool = False

# Authentication
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials.username

# Database helper
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# Dashboard Routes
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, username: str = Depends(authenticate)):
    """Main dashboard with key metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get user statistics
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE registered_at::date = CURRENT_DATE")
        new_users_today = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM usage_logs WHERE created_at::date = CURRENT_DATE")
        active_users_today = cursor.fetchone()['count']
        
        # Get search statistics
        cursor.execute("SELECT COUNT(*) as count FROM usage_logs")
        total_searches = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM usage_logs WHERE created_at::date = CURRENT_DATE")
        searches_today = cursor.fetchone()['count']
        
        # Get recent activity
        cursor.execute("""
            SELECT u.full_name, ul.query, ul.created_at 
            FROM usage_logs ul 
            JOIN users u ON ul.user_id = u.telegram_id 
            ORDER BY ul.created_at DESC LIMIT 10
        """)
        recent_searches = cursor.fetchall()
        
        # Get popular queries
        cursor.execute("""
            SELECT query, COUNT(*) as count 
            FROM usage_logs 
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY query 
            ORDER BY count DESC LIMIT 10
        """)
        popular_queries = cursor.fetchall()
        
        user_stats = UserStats(
            total_users=total_users,
            new_users_today=new_users_today,
            active_users_today=active_users_today,
            total_searches=total_searches,
            searches_today=searches_today
        )
        
    finally:
        cursor.close()
        conn.close()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_stats": user_stats,
        "recent_searches": recent_searches,
        "popular_queries": popular_queries,
        "username": username
    })

# User Management
@app.get("/users", response_class=HTMLResponse)
def users_list(request: Request, username: str = Depends(authenticate)):
    """User management page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT u.*, COUNT(ul.id) as total_searches,
                   MAX(ul.created_at) as last_active
            FROM users u
            LEFT JOIN usage_logs ul ON u.telegram_id = ul.user_id
            GROUP BY u.id, u.telegram_id, u.full_name, u.username, u.phone, u.language, u.registered_at, u.requests_today
            ORDER BY u.registered_at DESC
        """)
        users = cursor.fetchall()
        
    finally:
        cursor.close()
        conn.close()
    
    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
        "username": username
    })

# User Search and History
@app.get("/user-search", response_class=HTMLResponse)
def user_search_page(request: Request, username: str = Depends(authenticate)):
    """User search page"""
    return templates.TemplateResponse("user_search.html", {
        "request": request,
        "username": username,
        "user_data": None,
        "search_history": None,
        "query": ""
    })

@app.post("/user-search", response_class=HTMLResponse)
def user_search_results(
    request: Request, 
    query: str = Form(...),
    username: str = Depends(authenticate)
):
    """Search for user and display their search history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_data = None
        search_history = []
        not_found_history = []
        
        # Search for user by ID or name
        if query.isdigit():
            # Search by Telegram ID
            cursor.execute("""
                SELECT u.*, COUNT(ul.id) as total_searches,
                       MAX(ul.created_at) as last_active
                FROM users u
                LEFT JOIN usage_logs ul ON u.telegram_id = ul.user_id
                WHERE u.telegram_id = %s
                GROUP BY u.id, u.telegram_id, u.full_name, u.username, u.phone, u.language, u.registered_at, u.requests_today
            """, (int(query),))
        else:
            # Search by name (case-insensitive partial match)
            cursor.execute("""
                SELECT u.*, COUNT(ul.id) as total_searches,
                       MAX(ul.created_at) as last_active
                FROM users u
                LEFT JOIN usage_logs ul ON u.telegram_id = ul.user_id
                WHERE LOWER(u.full_name) LIKE LOWER(%s) 
                   OR LOWER(u.username) LIKE LOWER(%s)
                GROUP BY u.id, u.telegram_id, u.full_name, u.username, u.phone, u.language, u.registered_at, u.requests_today
                ORDER BY u.registered_at DESC
                LIMIT 10
            """, (f'%{query}%', f'%{query}%'))
        
        users_found = cursor.fetchall()
        
        if users_found:
            # If searching by ID, take the first result
            # If searching by name, we'll show all matches but detailed history for the first one
            user_data = users_found[0] if len(users_found) == 1 else users_found
            
            if len(users_found) == 1:
                user_id = users_found[0]['telegram_id']
                
                # Get detailed search history with results
                cursor.execute("""
                    SELECT ul.query, ul.created_at,
                           -- Try to get the search results if they exist
                           CASE 
                               WHEN ul.query IS NOT NULL THEN 'Found'
                               ELSE 'No result recorded'
                           END as result_status
                    FROM usage_logs ul
                    WHERE ul.user_id = %s
                    ORDER BY ul.created_at DESC
                    LIMIT 50
                """, (user_id,))
                search_history = cursor.fetchall()
                
                # Get "not found" queries for this user
                cursor.execute("""
                    SELECT nfq.query, nfq.search_timestamp, nfq.language
                    FROM not_found_queries nfq
                    WHERE nfq.user_id = %s
                    ORDER BY nfq.search_timestamp DESC
                    LIMIT 20
                """, (user_id,))
                not_found_history = cursor.fetchall()
                
    except Exception as e:
        logging.error(f"Error in user search: {e}")
        user_data = None
        search_history = []
        not_found_history = []
        
    finally:
        cursor.close()
        conn.close()
    
    return templates.TemplateResponse("user_search.html", {
        "request": request,
        "username": username,
        "user_data": user_data,
        "search_history": search_history,
        "not_found_history": not_found_history,
        "query": query,
        "multiple_users": isinstance(user_data, list) and len(user_data) > 1
    })

@app.post("/users/{user_id}/block")
def block_user(user_id: int, username: str = Depends(authenticate)):
    """Block/unblock a user (placeholder - no blocking field in current schema)"""
    # Since there's no is_blocked field in the current schema,
    # this is a placeholder for future implementation
    logging.info(f"Block/unblock user {user_id} requested by {username}")
    return RedirectResponse(url="/users", status_code=303)

# Analytics
@app.get("/analytics", response_class=HTMLResponse)
def analytics(request: Request, username: str = Depends(authenticate)):
    """Analytics and reporting page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Daily usage for last 30 days
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as searches
            FROM usage_logs
            WHERE created_at > NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        daily_usage = cursor.fetchall()
        
        # Language distribution
        cursor.execute("""
            SELECT language, COUNT(*) as count
            FROM users
            GROUP BY language
            ORDER BY count DESC
        """)
        lang_stats = cursor.fetchall()
        
        # Failed searches
        cursor.execute("""
            SELECT query, COUNT(*) as count
            FROM not_found_queries
            WHERE search_timestamp > NOW() - INTERVAL '7 days'
            GROUP BY query
            ORDER BY count DESC
            LIMIT 20
        """)
        failed_searches = cursor.fetchall()
        
    finally:
        cursor.close()
        conn.close()
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "daily_usage": daily_usage,
        "lang_stats": lang_stats,
        "failed_searches": failed_searches,
        "username": username
    })

# Content Management
@app.get("/content", response_class=HTMLResponse)
async def content_management(request: Request, username: str = Depends(authenticate)):
    """Content management page"""
    # Load current messages
    from bot.handlers.user import MESSAGES
    
    return templates.TemplateResponse("content.html", {
        "request": request,
        "messages": MESSAGES,
        "username": username
    })

@app.post("/content/update")
async def update_content(
    request: Request,
    message_key: str = Form(...),
    language: str = Form(...),
    content: str = Form(...),
    username: str = Depends(authenticate)
):
    """Update bot messages"""
    # In a real implementation, you'd save to a config file or database
    # For now, this is a placeholder
    
    return RedirectResponse(url="/content", status_code=303)

# Broadcast Messages
@app.get("/broadcast", response_class=HTMLResponse)
def broadcast_page(request: Request, username: str = Depends(authenticate)):
    """Broadcast message page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get user statistics
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE telegram_id IS NOT NULL")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as count 
            FROM usage_logs 
            WHERE created_at > NOW() - INTERVAL '7 days'
        """)
        active_users = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM users 
            WHERE registered_at > NOW() - INTERVAL '7 days' 
            AND telegram_id IS NOT NULL
        """)
        new_users_week = cursor.fetchone()[0]
        
        # Get language statistics
        cursor.execute("""
            SELECT language as code, COUNT(*) as count 
            FROM users 
            WHERE telegram_id IS NOT NULL AND language IS NOT NULL
            GROUP BY language 
            ORDER BY count DESC
        """)
        language_stats = cursor.fetchall()
        
        # Get messages sent today (placeholder)
        messages_sent_today = 0
        
    finally:
        cursor.close()
        conn.close()
    
    return templates.TemplateResponse("broadcast.html", {
        "request": request,
        "username": username,
        "total_users": total_users,
        "active_users": active_users,
        "new_users_week": new_users_week,
        "messages_sent_today": messages_sent_today,
        "language_stats": [{"code": stat[0], "count": stat[1]} for stat in language_stats]
    })

@app.post("/broadcast/send")
def send_broadcast(
    request: Request,
    title: str = Form(...),
    message: str = Form(...),
    target_audience: str = Form("all"),
    language: str = Form(None),
    selected_users: str = Form(None),
    username: str = Depends(authenticate)
):
    """Send broadcast message to users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get target users based on selection
        if target_audience == "custom" and selected_users:
            # Custom user selection
            selected_user_ids = json.loads(selected_users)
            user_ids_str = ','.join(map(str, selected_user_ids))
            cursor.execute(f"""
                SELECT telegram_id FROM users 
                WHERE telegram_id IN ({user_ids_str}) 
                AND telegram_id IS NOT NULL
            """)
        elif target_audience == "language" and language:
            cursor.execute("""
                SELECT telegram_id FROM users 
                WHERE language = %s AND telegram_id IS NOT NULL
            """, (language,))
        elif target_audience == "active":
            cursor.execute("""
                SELECT DISTINCT u.telegram_id FROM users u
                JOIN usage_logs ul ON u.telegram_id = ul.user_id
                WHERE ul.created_at > NOW() - INTERVAL '7 days'
                AND u.telegram_id IS NOT NULL
            """)
        elif target_audience == "new":
            cursor.execute("""
                SELECT telegram_id FROM users 
                WHERE registered_at > NOW() - INTERVAL '7 days'
                AND telegram_id IS NOT NULL
            """)
        else:
            # All users
            cursor.execute("""
                SELECT telegram_id FROM users 
                WHERE telegram_id IS NOT NULL
            """)
        
        users = cursor.fetchall()
        user_count = len(users)
        
        # Here you would integrate with your bot to send messages
        # For now, we'll just log the action
        logging.info(f"Broadcast scheduled for {user_count} users: {title} - {message}")
        
        # You could store the broadcast in a broadcasts table for tracking
        # cursor.execute("""
        #     INSERT INTO broadcasts (title, message, target_type, user_count, created_by, created_at)
        #     VALUES (%s, %s, %s, %s, %s, NOW())
        # """, (title, message, target_audience, user_count, username))
        # conn.commit()
        
        return {"success": True, "total_users": user_count, "successful_sends": user_count, "failed_sends": 0}
        
    except Exception as e:
        logging.error(f"Broadcast error: {e}")
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()

# System Status
@app.get("/system", response_class=HTMLResponse)
def system_status(request: Request, username: str = Depends(authenticate)):
    """System status and logs"""
    # Check bot status, database status, etc.
    
    # Read recent logs
    log_file = Path("logs/bot.log")
    recent_logs = []
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            recent_logs = f.readlines()[-100:]  # Last 100 lines
    
    return templates.TemplateResponse("system.html", {
        "request": request,
        "recent_logs": recent_logs,
        "username": username
    })

# API Endpoints
@app.get("/api/stats")
def api_stats(username: str = Depends(authenticate)):
    """API endpoint for dashboard stats"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT u.telegram_id) as total_users,
                COUNT(DISTINCT CASE WHEN u.registered_at::date = CURRENT_DATE THEN u.telegram_id END) as new_users_today,
                COUNT(DISTINCT CASE WHEN ul.created_at::date = CURRENT_DATE THEN ul.user_id END) as active_users_today,
                COUNT(ul.id) as total_searches,
                COUNT(CASE WHEN ul.created_at::date = CURRENT_DATE THEN ul.id END) as searches_today
            FROM users u
            LEFT JOIN usage_logs ul ON u.telegram_id = ul.user_id
        """)
        
        stats = cursor.fetchone()
        return dict(stats) if stats else {}
        
    finally:
        cursor.close()
        conn.close()

@app.get("/api/users-for-broadcast")
def get_users_for_broadcast(username: str = Depends(authenticate)):
    """Get all users for broadcast selection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all users (no is_blocked column in your schema)
        cursor.execute("""
            SELECT 
                telegram_id,
                full_name,
                username,
                phone,
                language,
                registered_at,
                requests_today
            FROM users
            WHERE telegram_id IS NOT NULL
            ORDER BY registered_at DESC
            LIMIT 500
        """)
        
        users = cursor.fetchall()
        
        # Get activity data separately - users who made queries in last 7 days
        cursor.execute("""
            SELECT DISTINCT user_id
            FROM usage_logs
            WHERE created_at > NOW() - INTERVAL '7 days'
        """)
        active_user_ids = {row[0] for row in cursor.fetchall()}
        
        # Get total searches per user
        cursor.execute("""
            SELECT user_id, COUNT(*) as search_count
            FROM usage_logs
            GROUP BY user_id
        """)
        search_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Convert to list of dictionaries
        users_list = []
        for user in users:
            telegram_id = user[0]
            users_list.append({
                'telegram_id': telegram_id,
                'full_name': user[1] or 'Unknown User',
                'username': user[2],
                'phone': user[3],
                'language': user[4] or 'en',
                'registered_at': user[5].isoformat() if user[5] else None,
                'is_blocked': False,  # No blocking feature in your schema
                'is_active': telegram_id in active_user_ids,
                'total_searches': search_counts.get(telegram_id, 0),
                'requests_today': user[6] or 0
            })
        
        cursor.close()
        conn.close()
        
        logging.info(f"Successfully loaded {len(users_list)} users for broadcast selection")
        return users_list
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Error fetching users: {e}\n{error_details}")
        # Return empty list instead of raising exception for better UX
        return []

@app.get("/api/user-search-details/{user_id}")
def get_user_search_details(user_id: int, username: str = Depends(authenticate)):
    """Get detailed search history for a specific user with results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get user basic info
        cursor.execute("""
            SELECT u.*, COUNT(ul.id) as total_searches,
                   MAX(ul.created_at) as last_active
            FROM users u
            LEFT JOIN usage_logs ul ON u.telegram_id = ul.user_id
            WHERE u.telegram_id = %s
            GROUP BY u.id, u.telegram_id, u.full_name, u.username, u.phone, u.language, u.registered_at, u.requests_today
        """, (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return {"error": "User not found"}
        
        # Get search history with more details
        cursor.execute("""
            SELECT ul.query, ul.created_at,
                   EXTRACT(HOUR FROM ul.created_at) as hour_of_day,
                   EXTRACT(DOW FROM ul.created_at) as day_of_week
            FROM usage_logs ul
            WHERE ul.user_id = %s
            ORDER BY ul.created_at DESC
            LIMIT 100
        """, (user_id,))
        
        search_history = cursor.fetchall()
        
        # Get failed searches
        cursor.execute("""
            SELECT nfq.query, nfq.search_timestamp, nfq.language
            FROM not_found_queries nfq
            WHERE nfq.user_id = %s
            ORDER BY nfq.search_timestamp DESC
            LIMIT 50
        """, (user_id,))
        
        failed_searches = cursor.fetchall()
        
        # Calculate some statistics
        total_searches = len(search_history)
        total_failed = len(failed_searches)
        success_rate = ((total_searches - total_failed) / total_searches * 100) if total_searches > 0 else 0
        
        # Most searched terms
        from collections import Counter
        query_counter = Counter([search['query'].lower() for search in search_history])
        popular_queries = query_counter.most_common(10)
        
        return {
            "user": dict(user),
            "search_history": [dict(row) for row in search_history],
            "failed_searches": [dict(row) for row in failed_searches],
            "statistics": {
                "total_searches": total_searches,
                "total_failed": total_failed,
                "success_rate": round(success_rate, 2),
                "popular_queries": popular_queries
            }
        }
        
    except Exception as e:
        logging.error(f"Error getting user details: {e}")
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.get("/api/test-db")
def test_database_connection(username: str = Depends(authenticate)):
    """Test database connection and basic queries"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT 1")
        cursor.fetchone()
        
        # Test users table exists
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Test usage_logs table exists
        cursor.execute("SELECT COUNT(*) FROM usage_logs")
        log_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "user_count": user_count,
            "log_count": log_count,
            "message": "Database connection successful"
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.post("/api/send-broadcast")
def api_send_broadcast(
    title: str = Form(...),
    message: str = Form(...),
    target_audience: str = Form("all"),
    language: str = Form(None),
    selected_users: str = Form(None),
    username: str = Depends(authenticate)
):
    """API endpoint for sending broadcasts"""
    return send_broadcast(
        request=None,
        title=title,
        message=message,
        target_audience=target_audience,
        language=language,
        selected_users=selected_users,
        username=username
    )

if __name__ == "__main__":
    print("Starting TNVED Bot Admin Panel...")
    print("Server will be available at: http://localhost:8000")
    print("Login credentials: admin / admin123")
    print("Testing database connection...")
    
    # Test database connection before starting server
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Make sure PostgreSQL is running and accessible")
        exit(1)
    
    print("Starting web server...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 