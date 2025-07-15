#!/usr/bin/env python3
"""
Beautiful Admin Panel for TNVED Bot - Modern UI/UX Version
"""
from fastapi import FastAPI, Depends, HTTPException, Request, Form, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import secrets
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta
from typing import Optional, List
import aiohttp
import asyncio
import json
import os
import pandas as pd
import tempfile
# Configuration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/postgres"
BOT_TOKEN = "8113438450:AAGn0efp6w-rwfpcNFCQ-22-3MXEkNHk058"  # Your bot token
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Setup logging (minimal logging)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Translation dictionaries
TRANSLATIONS = {
    'en': {
        # Dashboard
        'dashboard_title': 'Dashboard',
        'admin_panel': 'TNVED Bot Admin Panel',
        'beautiful_dashboard': 'Beautiful Dashboard',
        'welcome_back': 'Welcome back',
        'overview': 'Overview',
        'total_users': 'Total Users',
        'new_users_today': 'New Users Today',
        'active_users_today': 'Active Users Today',
        'total_searches': 'Total Searches',
        'searches_today': 'Searches Today',
        'recent_activity': 'Recent Activity',
        'recent_searches': 'Recent Searches',
        'popular_queries': 'Popular Queries (Last 7 Days)',
        'quick_actions': 'Quick Actions',
        'view_all_users': 'View All Users',
        'send_broadcast': 'Send Broadcast',
        'analytics': 'Analytics',
        'system_status': 'System Status',
        'content_management': 'Content Management',
        
        # Navigation
        'users': 'Users',
        'user_search': 'User Search',
        'search_results': 'Search Results',
        'broadcast': 'Broadcast',
        'content': 'Content',
        'system': 'System',
        'logout': 'Logout',
        'language': 'Language',
        
        # Users page
        'user_management': 'User Management',
        'manage_bot_users': 'Manage your bot users and view their activity',
        'user_id': 'User ID',
        'full_name': 'Full Name',
        'username': 'Username',
        'phone': 'Phone',
        'registration_date': 'Registration Date',
        'last_active': 'Last Active',
        'user_statistics': 'User Statistics',
        'registered_users': 'Registered Users',
        'active_this_week': 'Active This Week',
        'new_this_week': 'New This Week',
        'avg_searches_per_user': 'Avg Searches per User',
        
        # Broadcast page
        'broadcast_message': 'Broadcast Message',
        'send_messages_to_users': 'Send messages to your bot users',
        'message_title': 'Message Title',
        'message_content': 'Message Content',
        'target_audience': 'Target Audience',
        'all_users': 'All Users',
        'active_users': 'Active Users (Last 7 Days)',
        'new_users': 'New Users (Last 7 Days)',
        'by_language': 'By Language',
        'custom_selection': 'Custom Selection',
        'select_language': 'Select Language',
        'russian': 'Russian',
        'uzbek': 'Uzbek',
        'english': 'English',
        'send_message': 'Send Message',
        'preview_audience': 'Preview Audience',
        'broadcast_statistics': 'Broadcast Statistics',
        'messages_sent_today': 'Messages Sent Today',
        
        # Content Management
        'content_management_title': 'Content Management',
        'edit_bot_messages': 'Edit your bot\'s messages and translations',
        'message_keys': 'Message Keys',
        'languages': 'Languages',
        'last_updated': 'Last Updated',
        'changes': 'Changes',
        'message_editor': 'Message Editor',
        'save_all_changes': 'Save All Changes',
        'add_new_message': 'Add New Message',
        'export': 'Export',
        'import': 'Import',
        'search_messages': 'Search messages...',
        'all_categories': 'All Categories',
        'welcome_messages': 'Welcome Messages',
        'search_messages_cat': 'Search Messages',
        'error_messages': 'Error Messages',
        'help_messages': 'Help Messages',
        'other': 'Other',
        
        # System page
        'system_status_title': 'System Status',
        'all_systems_operational': 'All Systems Operational',
        'database': 'Database',
        'connected': 'Connected',
        'bot_api': 'Bot API',
        'active': 'Active',
        'monitoring': 'Monitoring',
        'setup_needed': 'Setup Needed',
        'advanced_monitoring': 'Advanced Monitoring Coming Soon:',
        'server_usage': 'Server resource usage',
        'health_checks': 'Real-time health checks',
        'performance_metrics': 'Performance metrics',
        'alert_notifications': 'Alert notifications',
        'system_logs': 'System logs viewer',
        
        # Common
        'back_to_dashboard': 'Back to Dashboard',
        'loading': 'Loading...',
        'error': 'Error',
        'success': 'Success',
        'cancel': 'Cancel',
        'save': 'Save',
        'delete': 'Delete',
        'edit': 'Edit',
        'view': 'View',
        'search': 'Search',
        'filter': 'Filter',
        'no_data': 'No data available',
        'never': 'Never',
        'just_loaded': 'Just loaded',
        'unauthorized': 'Unauthorized',
        'failed_to_load': 'Failed to load',
        
        # Export functions
        'export_all_users': 'Export All Users',
        'export_selected_users': 'Export Selected Users',
        'export_user_history': 'Export User History',
        'download_excel': 'Download Excel',
        'include_search_history': 'Include Search History',
        'user_ids_placeholder': 'Enter user IDs separated by commas (e.g., 123456, 789012)',
        'export_custom_users': 'Export Custom Users',
        
        # Search Results page
        'search_results_title': 'Detailed Search Results',
        'search_results_desc': 'View detailed bot search results with TNVED codes',
        'main_result': 'Main Result',
        'similar_results': 'Similar Results',
        'accuracy': 'Accuracy',
        'search_query': 'Search Query',
        'user': 'User',
        'timestamp': 'Timestamp',
        'tnved_code': 'TNVED Code',
        'description': 'Description',
        'no_search_results': 'No search results found',
        'view_details': 'View Details',
        
        # Analytics page
        'analytics_dashboard': 'Analytics Dashboard',
        'comprehensive_insights': 'Comprehensive insights and analytics for your TNVED bot',
        'growth_rate': 'Growth Rate',
        'last_30_days': 'Last 30 days',
        'avg_queries_user': 'Avg. Queries/User',
        'per_user_activity': 'Per user activity',
        'success_rate': 'Success Rate',
        'query_success': 'Query success',
        'peak_hour': 'Peak Hour',
        'most_active_time': 'Most active time',
        'user_growth_over_time': 'User Growth Over Time',
        'new_user_registrations': 'New user registrations over the last 30 days',
        'language_distribution': 'Language Distribution',
        'user_language_preferences': 'User language preferences',
        'search_activity_trends': 'Search Activity Trends',
        'daily_search_volume': 'Daily search volume',
        'usage_patterns_by_hour': 'Usage Patterns by Hour',
        'activity_distribution_day': 'Activity distribution throughout the day',
        'top_searched_terms': 'Top Searched Terms',
        'most_popular_queries': 'Most popular queries this month',
        'user_activity_insights': 'User Activity Insights',
        'user_engagement_metrics': 'User engagement metrics',
        'rank': 'Rank',
        'query': 'Query',
        'count': 'Count',
        'trend': 'Trend',
        'active_this_week': 'Active This Week',
        'avg_session_min': 'Avg Session (min)',
        'day_retention': '7-Day Retention',
        'quick_insights': 'Quick Insights'
    },
    'ru': {
        # Dashboard
        'dashboard_title': 'Панель управления',
        'admin_panel': 'Админ панель TNVED Бота',
        'beautiful_dashboard': 'Красивая панель управления',
        'welcome_back': 'Добро пожаловать',
        'overview': 'Обзор',
        'total_users': 'Всего пользователей',
        'new_users_today': 'Новых сегодня',
        'active_users_today': 'Активных сегодня',
        'total_searches': 'Всего поисков',
        'searches_today': 'Поисков сегодня',
        'recent_activity': 'Последняя активность',
        'recent_searches': 'Последние поиски',
        'popular_queries': 'Популярные запросы (за 7 дней)',
        'quick_actions': 'Быстрые действия',
        'view_all_users': 'Все пользователи',
        'send_broadcast': 'Отправить сообщение',
        'analytics': 'Аналитика',
        'system_status': 'Состояние системы',
        'content_management': 'Управление контентом',
        
        # Navigation
        'users': 'Пользователи',
        'user_search': 'Поиск пользователей',
        'search_results': 'Результаты поиска',
        'broadcast': 'Рассылка',
        'content': 'Контент',
        'system': 'Система',
        'logout': 'Выход',
        'language': 'Язык',
        
        # Users page
        'user_management': 'Управление пользователями',
        'manage_bot_users': 'Управляйте пользователями бота и просматривайте их активность',
        'user_id': 'ID пользователя',
        'full_name': 'Полное имя',
        'username': 'Имя пользователя',
        'phone': 'Телефон',
        'registration_date': 'Дата регистрации',
        'last_active': 'Последняя активность',
        'user_statistics': 'Статистика пользователей',
        'registered_users': 'Зарегистрированных',
        'active_this_week': 'Активных за неделю',
        'new_this_week': 'Новых за неделю',
        'avg_searches_per_user': 'Поисков на пользователя',
        
        # Broadcast page
        'broadcast_message': 'Рассылка сообщений',
        'send_messages_to_users': 'Отправляйте сообщения пользователям вашего бота',
        'message_title': 'Заголовок сообщения',
        'message_content': 'Содержание сообщения',
        'target_audience': 'Целевая аудитория',
        'all_users': 'Все пользователи',
        'active_users': 'Активные (за 7 дней)',
        'new_users': 'Новые (за 7 дней)',
        'by_language': 'По языку',
        'custom_selection': 'Выборочно',
        'select_language': 'Выберите язык',
        'russian': 'Русский',
        'uzbek': 'Узбекский',
        'english': 'Английский',
        'send_message': 'Отправить сообщение',
        'preview_audience': 'Предпросмотр аудитории',
        'broadcast_statistics': 'Статистика рассылки',
        'messages_sent_today': 'Сообщений отправлено сегодня',
        
        # Content Management
        'content_management_title': 'Управление контентом',
        'edit_bot_messages': 'Редактируйте сообщения и переводы вашего бота',
        'message_keys': 'Ключи сообщений',
        'languages': 'Языки',
        'last_updated': 'Обновлено',
        'changes': 'Изменения',
        'message_editor': 'Редактор сообщений',
        'save_all_changes': 'Сохранить все изменения',
        'add_new_message': 'Добавить сообщение',
        'export': 'Экспорт',
        'import': 'Импорт',
        'search_messages': 'Поиск сообщений...',
        'all_categories': 'Все категории',
        'welcome_messages': 'Приветственные сообщения',
        'search_messages_cat': 'Поисковые сообщения',
        'error_messages': 'Ошибки',
        'help_messages': 'Помощь',
        'other': 'Другое',
        
        # System page
        'system_status_title': 'Состояние системы',
        'all_systems_operational': 'Все системы работают',
        'database': 'База данных',
        'connected': 'Подключена',
        'bot_api': 'API бота',
        'active': 'Активно',
        'monitoring': 'Мониторинг',
        'setup_needed': 'Требует настройки',
        'advanced_monitoring': 'Расширенный мониторинг скоро:',
        'server_usage': 'Использование ресурсов сервера',
        'health_checks': 'Проверки состояния в реальном времени',
        'performance_metrics': 'Метрики производительности',
        'alert_notifications': 'Уведомления о проблемах',
        'system_logs': 'Просмотр системных логов',
        
        # Common
        'back_to_dashboard': 'Вернуться к панели',
        'loading': 'Загрузка...',
        'error': 'Ошибка',
        'success': 'Успешно',
        'cancel': 'Отмена',
        'save': 'Сохранить',
        'delete': 'Удалить',
        'edit': 'Редактировать',
        'view': 'Просмотр',
        'search': 'Поиск',
        'filter': 'Фильтр',
        'no_data': 'Нет данных',
        'never': 'Никогда',
        'just_loaded': 'Только что загружено',
        'unauthorized': 'Неавторизован',
        'failed_to_load': 'Не удалось загрузить',
        
        # Export functions
        'export_all_users': 'Экспорт всех пользователей',
        'export_selected_users': 'Экспорт выбранных',
        'export_user_history': 'Экспорт истории пользователя',
        'download_excel': 'Скачать Excel',
        'include_search_history': 'Включить историю поисков',
        'user_ids_placeholder': 'Введите ID пользователей через запятую (например: 123456, 789012)',
        'export_custom_users': 'Экспорт выборочно',
        
        # Search Results page
        'search_results_title': 'Детальные результаты поиска',
        'search_results_desc': 'Просмотр детальных результатов поиска бота с кодами ТН ВЭД',
        'main_result': 'Основной результат',
        'similar_results': 'Похожие результаты',
        'accuracy': 'Точность',
        'search_query': 'Поисковый запрос',
        'user': 'Пользователь',
        'timestamp': 'Время',
        'tnved_code': 'Код ТН ВЭД',
        'description': 'Описание',
        'no_search_results': 'Результаты поиска не найдены',
        'view_details': 'Подробности',
        
        # Analytics page
        'analytics_dashboard': 'Панель аналитики',
        'comprehensive_insights': 'Подробная аналитика и инсайты для вашего TNVED бота',
        'growth_rate': 'Скорость роста',
        'last_30_days': 'За последние 30 дней',
        'avg_queries_user': 'Среднее запросов/пользователь',
        'per_user_activity': 'Активность на пользователя',
        'success_rate': 'Успешность',
        'query_success': 'Успешность запросов',
        'peak_hour': 'Пиковый час',
        'most_active_time': 'Самое активное время',
        'user_growth_over_time': 'Рост пользователей во времени',
        'new_user_registrations': 'Регистрации новых пользователей за последние 30 дней',
        'language_distribution': 'Распределение языков',
        'user_language_preferences': 'Языковые предпочтения пользователей',
        'search_activity_trends': 'Тренды поисковой активности',
        'daily_search_volume': 'Ежедневный объем поисков',
        'usage_patterns_by_hour': 'Паттерны использования по часам',
        'activity_distribution_day': 'Распределение активности в течение дня',
        'top_searched_terms': 'Топ поисковых запросов',
        'most_popular_queries': 'Самые популярные запросы этого месяца',
        'user_activity_insights': 'Инсайты активности пользователей',
        'user_engagement_metrics': 'Метрики вовлеченности пользователей',
        'rank': 'Ранг',
        'query': 'Запрос',
        'count': 'Количество',
        'trend': 'Тренд',
        'active_this_week': 'Активных за неделю',
        'avg_session_min': 'Средняя сессия (мин)',
        'day_retention': '7-дневное удержание',
        'quick_insights': 'Быстрые инсайты'
    }
}

def get_language(request: Request) -> str:
    """Get user's language preference from cookie or default to English"""
    return request.cookies.get("admin_language", "en")

def get_translations(request: Request) -> dict:
    """Get translations for user's language"""
    language = get_language(request)
    return TRANSLATIONS.get(language, TRANSLATIONS['en'])

# Initialize FastAPI app
app = FastAPI(
    title="TNVED Bot Admin Panel", 
    version="2.0.0",
    description="Beautiful Admin Dashboard for TNVED Bot"
)

# Security
security = HTTPBasic()

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Authentication function
def authenticate(request: Request) -> Optional[str]:
    """Check if user is authenticated via HTTP Basic Auth"""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        return None
    
    try:
        import base64
        encoded_credentials = auth_header.split(" ", 1)[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded_credentials.split(":", 1)
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return username
    except Exception:
        pass
    
    return None

# Database helper
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# Telegram Bot Functions
async def send_telegram_message(chat_id: int, message: str, parse_mode: str = "HTML") -> bool:
    """Send a message to a Telegram user"""
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            async with session.post(f"{TELEGRAM_API_URL}/sendMessage", data=data) as response:
                result = await response.json()
                return result.get('ok', False)
    except Exception as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")
        return False

async def get_user_list(target_audience: str, language: str = None, selected_users: str = None) -> List[int]:
    """Get list of user IDs based on targeting criteria"""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if target_audience == "custom" and selected_users:
                    # Custom user selection
                    selected_user_ids = json.loads(selected_users)
                    if selected_user_ids:
                        user_ids_str = ','.join(map(str, selected_user_ids))
                        cursor.execute(f"""
                            SELECT telegram_id FROM users 
                            WHERE telegram_id IN ({user_ids_str}) 
                            AND telegram_id IS NOT NULL
                        """)
                    else:
                        return []
                elif target_audience == "all":
                    cursor.execute("SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL")
                elif target_audience == "active":
                    cursor.execute("""
                        SELECT DISTINCT u.telegram_id FROM users u
                        JOIN usage_logs ul ON u.telegram_id = ul.user_id
                        WHERE ul.created_at >= CURRENT_DATE - INTERVAL '7 days'
                        AND u.telegram_id IS NOT NULL
                    """)
                elif target_audience == "new":
                    cursor.execute("""
                        SELECT telegram_id FROM users 
                        WHERE registered_at >= CURRENT_DATE - INTERVAL '7 days'
                        AND telegram_id IS NOT NULL
                    """)
                elif target_audience == "language" and language:
                    cursor.execute("""
                        SELECT telegram_id FROM users 
                        WHERE language = %s AND telegram_id IS NOT NULL
                    """, (language,))
                else:
                    cursor.execute("SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL")
                
                users = cursor.fetchall()
                return [user['telegram_id'] for user in users if user['telegram_id']]
    except Exception as e:
        logger.error(f"Error getting user list: {e}")
        return []

async def send_broadcast(title: str, message: str, target_audience: str, language: str = None, selected_users: str = None) -> dict:
    """Send broadcast message to targeted users"""
    try:
        # Get target user list
        user_ids = await get_user_list(target_audience, language, selected_users)
        
        if not user_ids:
            return {"success": False, "message": "No users found for the selected criteria"}
        
        # Format message for Telegram
        formatted_message = f"<b>{title}</b>\n\n{message}"
        
        # Send messages
        successful_sends = 0
        failed_sends = 0
        
        # Send in batches to avoid rate limiting
        batch_size = 30  # Telegram rate limit is 30 messages per second
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]
            tasks = [send_telegram_message(user_id, formatted_message) for user_id in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if result is True:
                    successful_sends += 1
                else:
                    failed_sends += 1
            
            # Wait 1 second between batches to respect rate limits
            if i + batch_size < len(user_ids):
                await asyncio.sleep(1)
        
        # Log broadcast to database (optional) - create table if it doesn't exist
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Create table if it doesn't exist
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS broadcast_history (
                            id SERIAL PRIMARY KEY,
                            title VARCHAR(500),
                            message TEXT,
                            target_audience VARCHAR(100),
                            total_sent INTEGER,
                            successful_sends INTEGER,
                            failed_sends INTEGER,
                            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            sent_by VARCHAR(100) DEFAULT 'admin'
                        )
                    """)
                    
                    # Insert broadcast history
                    cursor.execute("""
                        INSERT INTO broadcast_history (title, message, target_audience, 
                                                     total_sent, successful_sends, failed_sends, sent_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (title, message, target_audience, len(user_ids), successful_sends, failed_sends, datetime.now()))
                    conn.commit()
                    # logger.info(f"Broadcast logged: {successful_sends}/{len(user_ids)} sent successfully")
        except Exception as e:
            logger.warning(f"Failed to log broadcast history: {e}")
        
        return {
            "success": True,
            "message": f"Broadcast sent successfully!",
            "total_users": len(user_ids),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends
        }
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        return {"success": False, "message": f"Broadcast failed: {str(e)}"}

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Beautiful Dashboard with comprehensive user tracking statistics"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - TNVED Bot Admin</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                body {
                    font-family: 'Inter', sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                .login-box {
                    background: white;
                    padding: 3rem;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
                    text-align: center;
                    max-width: 400px;
                    width: 90%;
                }
                .login-box h2 {
                    color: #333;
                    margin-bottom: 1rem;
                    font-weight: 600;
                }
                .login-box p {
                    color: #666;
                    margin-bottom: 2rem;
                }
                .credentials {
                    background: #f8f9fa;
                    padding: 1rem;
                    border-radius: 10px;
                    margin-top: 1rem;
                    font-size: 0.9rem;
                    color: #495057;
                }
                .icon {
                    font-size: 3rem;
                    color: #667eea;
                    margin-bottom: 1rem;
                }
            </style>
        </head>
        <body>
            <div class="login-box">
                <div class="icon">🤖</div>
                <h2>TNVED Bot Admin</h2>
                <p>Please authenticate to access the admin panel</p>
                <div class="credentials">
                    <strong>Username:</strong> admin<br>
                    <strong>Password:</strong> admin123
                </div>
            </div>
        </body>
        </html>
        """, status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    try:
        # Get comprehensive statistics with enhanced daily/weekly/monthly tracking
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Basic user statistics
                cursor.execute("SELECT COUNT(*) as count FROM users")
                total_users = cursor.fetchone()['count']
                
                # New users today
                cursor.execute("""
                    SELECT COUNT(*) as count FROM users 
                    WHERE DATE(registered_at) = CURRENT_DATE
                """)
                new_users_today = cursor.fetchone()['count']
                
                # New users this week
                cursor.execute("""
                    SELECT COUNT(*) as count FROM users 
                    WHERE registered_at >= DATE_TRUNC('week', CURRENT_DATE)
                """)
                new_users_this_week = cursor.fetchone()['count']
                
                # New users this month
                cursor.execute("""
                    SELECT COUNT(*) as count FROM users 
                    WHERE registered_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                new_users_this_month = cursor.fetchone()['count']
                
                # Active users today (users who made queries today)
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as count FROM usage_logs 
                    WHERE DATE(created_at) = CURRENT_DATE
                """)
                active_users_today = cursor.fetchone()['count']
                
                # Active users this week
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as count FROM usage_logs 
                    WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)
                """)
                active_users_this_week = cursor.fetchone()['count']
                
                # Active users this month
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as count FROM usage_logs 
                    WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                active_users_this_month = cursor.fetchone()['count']
                
                # Total searches
                cursor.execute("SELECT COUNT(*) as count FROM usage_logs")
                total_searches = cursor.fetchone()['count']
                
                # Searches today
                cursor.execute("""
                    SELECT COUNT(*) as count FROM usage_logs 
                    WHERE DATE(created_at) = CURRENT_DATE
                """)
                searches_today = cursor.fetchone()['count']
                
                # Searches this week
                cursor.execute("""
                    SELECT COUNT(*) as count FROM usage_logs 
                    WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)
                """)
                searches_this_week = cursor.fetchone()['count']
                
                # Searches this month
                cursor.execute("""
                    SELECT COUNT(*) as count FROM usage_logs 
                    WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                searches_this_month = cursor.fetchone()['count']
                
                # Average searches per user per day
                cursor.execute("""
                    SELECT 
                        COALESCE(AVG(daily_searches), 0) as avg_daily_searches
                    FROM (
                        SELECT 
                            user_id,
                            DATE(created_at) as search_date,
                            COUNT(*) as daily_searches
                        FROM usage_logs
                        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY user_id, DATE(created_at)
                    ) user_daily_stats
                """)
                avg_daily_searches_per_user = cursor.fetchone()['avg_daily_searches'] or 0
                
                # Most active users today
                cursor.execute("""
                    SELECT 
                        u.full_name, 
                        u.telegram_id,
                        COUNT(ul.id) as search_count
                    FROM users u
                    JOIN usage_logs ul ON u.telegram_id = ul.user_id
                    WHERE DATE(ul.created_at) = CURRENT_DATE
                    GROUP BY u.telegram_id, u.full_name
                    ORDER BY search_count DESC
                    LIMIT 5
                """)
                most_active_users_today = cursor.fetchall()
                
                # Daily statistics for the past 7 days
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as searches,
                        COUNT(DISTINCT user_id) as active_users
                    FROM usage_logs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """)
                daily_stats_week = cursor.fetchall()
                
                # Weekly registration trends (last 4 weeks)
                cursor.execute("""
                    SELECT 
                        DATE_TRUNC('week', registered_at) as week_start,
                        COUNT(*) as new_users
                    FROM users
                    WHERE registered_at >= CURRENT_DATE - INTERVAL '4 weeks'
                    GROUP BY DATE_TRUNC('week', registered_at)
                    ORDER BY week_start DESC
                """)
                weekly_registration_trends = cursor.fetchall()
                
                # Monthly registration trends (last 6 months)
                cursor.execute("""
                    SELECT 
                        DATE_TRUNC('month', registered_at) as month_start,
                        COUNT(*) as new_users
                    FROM users
                    WHERE registered_at >= CURRENT_DATE - INTERVAL '6 months'
                    GROUP BY DATE_TRUNC('month', registered_at)
                    ORDER BY month_start DESC
                """)
                monthly_registration_trends = cursor.fetchall()
                
                # User retention rate (users who returned after first day)
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT returning_users.user_id) as returning_users,
                        COUNT(DISTINCT all_users.user_id) as total_users
                    FROM (
                        SELECT DISTINCT user_id
                        FROM usage_logs
                        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    ) all_users
                    LEFT JOIN (
                        SELECT user_id
                        FROM usage_logs ul1
                        WHERE ul1.created_at >= CURRENT_DATE - INTERVAL '30 days'
                        AND EXISTS (
                            SELECT 1 FROM usage_logs ul2
                            WHERE ul2.user_id = ul1.user_id
                            AND DATE(ul2.created_at) > DATE(ul1.created_at)
                        )
                        GROUP BY user_id
                    ) returning_users ON all_users.user_id = returning_users.user_id
                """)
                retention_data = cursor.fetchone()
                retention_rate = 0
                if retention_data and retention_data['total_users'] > 0:
                    retention_rate = round((retention_data['returning_users'] / retention_data['total_users']) * 100, 1)
                
                # Recent searches (last 10 with user info)
                cursor.execute("""
                    SELECT u.full_name, ul.query, ul.created_at
                    FROM usage_logs ul
                    LEFT JOIN users u ON ul.user_id = u.telegram_id
                    WHERE ul.query IS NOT NULL AND ul.query != '' AND TRIM(ul.query) != ''
                    ORDER BY ul.created_at DESC
                    LIMIT 10
                """)
                recent_searches = cursor.fetchall()
                
                # Popular queries (last 7 days)
                cursor.execute("""
                    SELECT query, COUNT(*) as count
                    FROM usage_logs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                      AND query IS NOT NULL AND query != '' AND TRIM(query) != ''
                    GROUP BY query
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC
                    LIMIT 5
                """)
                popular_queries = cursor.fetchall()
                
                # Initialize default values for new variables
                recent_not_found = []
                recent_search_results = []
                failed_stats = {'failed_today': 0, 'failed_week': 0, 'failed_total': 0}
                common_not_found = []
                popular_codes = []
                
                # Try to get additional data, but don't fail if tables don't exist
                try:
                    # Recent not found queries (last 10)
                    cursor.execute("""
                        SELECT nfq.query, nfq.search_timestamp, u.full_name, nfq.language
                        FROM not_found_queries nfq
                        LEFT JOIN users u ON nfq.user_id = u.telegram_id
                        WHERE nfq.query IS NOT NULL AND TRIM(nfq.query) != ''
                        ORDER BY nfq.search_timestamp DESC
                        LIMIT 10
                    """)
                    recent_not_found = cursor.fetchall()
                except Exception as e:
                    logger.warning(f"Could not fetch not_found_queries: {e}")
                
                try:
                    # Recent successful search results with TNVED codes (last 10)
                    cursor.execute("""
                        SELECT sr.query, sr.main_code, sr.main_description, sr.main_accuracy, 
                               sr.search_timestamp, u.full_name
                        FROM search_results sr
                        LEFT JOIN users u ON sr.user_id = u.telegram_id
                        WHERE sr.main_code IS NOT NULL
                        ORDER BY sr.search_timestamp DESC
                        LIMIT 10
                    """)
                    recent_search_results = cursor.fetchall()
                except Exception as e:
                    logger.warning(f"Could not fetch search_results: {e}")
                
                try:
                    # Failed queries statistics (today and this week)
                    cursor.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM not_found_queries WHERE DATE(search_timestamp) = CURRENT_DATE) as failed_today,
                            (SELECT COUNT(*) FROM not_found_queries WHERE search_timestamp >= CURRENT_DATE - INTERVAL '7 days') as failed_week,
                            (SELECT COUNT(*) FROM not_found_queries) as failed_total
                    """)
                    failed_stats_result = cursor.fetchone()
                    if failed_stats_result:
                        failed_stats = failed_stats_result
                except Exception as e:
                    logger.warning(f"Could not fetch failed stats: {e}")
                
                try:
                    # Most common not found queries
                    cursor.execute("""
                        SELECT query, COUNT(*) as count
                        FROM not_found_queries
                        WHERE search_timestamp >= CURRENT_DATE - INTERVAL '7 days'
                          AND query IS NOT NULL AND TRIM(query) != ''
                        GROUP BY query
                        ORDER BY count DESC
                        LIMIT 5
                    """)
                    common_not_found = cursor.fetchall()
                except Exception as e:
                    logger.warning(f"Could not fetch common not found queries: {e}")
                
                try:
                    # Most popular TNVED codes found
                    cursor.execute("""
                        SELECT main_code, COUNT(*) as frequency, 
                               MAX(main_description) as description
                        FROM search_results
                        WHERE search_timestamp >= CURRENT_DATE - INTERVAL '7 days'
                          AND main_code IS NOT NULL
                        GROUP BY main_code
                        ORDER BY frequency DESC
                        LIMIT 5
                    """)
                    popular_codes = cursor.fetchall()
                except Exception as e:
                    logger.warning(f"Could not fetch popular codes: {e}")
        
        # Enhanced user statistics with comprehensive tracking
        user_stats = {
            'total_users': total_users or 0,
            'new_users_today': new_users_today or 0,
            'new_users_this_week': new_users_this_week or 0,
            'new_users_this_month': new_users_this_month or 0,
            'active_users_today': active_users_today or 0,
            'active_users_this_week': active_users_this_week or 0,
            'active_users_this_month': active_users_this_month or 0,
            'total_searches': total_searches or 0,
            'searches_today': searches_today or 0,
            'searches_this_week': searches_this_week or 0,
            'searches_this_month': searches_this_month or 0,
            'avg_daily_searches_per_user': round(float(avg_daily_searches_per_user or 0), 2),
            'retention_rate': retention_rate or 0,
            'most_active_users_today': most_active_users_today or [],
            'daily_stats_week': daily_stats_week or [],
            'weekly_registration_trends': weekly_registration_trends or [],
            'monthly_registration_trends': monthly_registration_trends or []
        }
        
        # Debug: Log the user stats (disabled)
        # logger.info(f"Dashboard user_stats: {user_stats}")
        
        # Render the enhanced dashboard
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "username": username,
            "user_stats": user_stats,
            "recent_searches": recent_searches,
            "popular_queries": popular_queries,
            "recent_not_found": recent_not_found,
            "recent_search_results": recent_search_results,
            "failed_stats": failed_stats,
            "common_not_found": common_not_found,
            "popular_codes": popular_codes,
            "t": get_translations(request),
            "current_language": get_language(request)
        })
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard Error</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Inter', sans-serif; padding: 2rem; background: #f8f9fa; }}
                .error-container {{ max-width: 600px; margin: 0 auto; background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
                .error-title {{ color: #e74c3c; font-size: 1.5rem; margin-bottom: 1rem; }}
                .error-message {{ color: #666; margin-bottom: 1rem; }}
                .error-details {{ background: #f8f9fa; padding: 1rem; border-radius: 8px; color: #495057; font-family: monospace; }}
                .btn {{ display: inline-block; padding: 0.75rem 1.5rem; background: #007bff; color: white; text-decoration: none; border-radius: 8px; margin-top: 1rem; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h2 class="error-title">⚠️ Dashboard Error</h2>
                <p class="error-message">Unable to load dashboard data. Please check your database connection.</p>
                <div class="error-details">Error: {str(e)}</div>
                <a href="/test-db" class="btn">Test Database Connection</a>
            </div>
        </body>
        </html>
        """)

def convert_decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    from decimal import Decimal
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    return obj

@app.get("/api/dashboard-data")
async def get_dashboard_data(request: Request):
    """Enhanced API endpoint for dashboard data with comprehensive user tracking"""
    username = authenticate(request)
    if not username:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        # Get comprehensive statistics with enhanced daily/weekly/monthly tracking
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Basic user statistics
                cursor.execute("SELECT COUNT(*) as count FROM users")
                total_users = cursor.fetchone()['count']
                
                # New users today
                cursor.execute("""
                    SELECT COUNT(*) as count FROM users 
                    WHERE DATE(registered_at) = CURRENT_DATE
                """)
                new_users_today = cursor.fetchone()['count']
                
                # New users this week
                cursor.execute("""
                    SELECT COUNT(*) as count FROM users 
                    WHERE registered_at >= DATE_TRUNC('week', CURRENT_DATE)
                """)
                new_users_this_week = cursor.fetchone()['count']
                
                # New users this month
                cursor.execute("""
                    SELECT COUNT(*) as count FROM users 
                    WHERE registered_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                new_users_this_month = cursor.fetchone()['count']
                
                # Active users today (users who made queries today)
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as count FROM usage_logs 
                    WHERE DATE(created_at) = CURRENT_DATE
                """)
                active_users_today = cursor.fetchone()['count']
                
                # Active users this week
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as count FROM usage_logs 
                    WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)
                """)
                active_users_this_week = cursor.fetchone()['count']
                
                # Active users this month
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as count FROM usage_logs 
                    WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                active_users_this_month = cursor.fetchone()['count']
                
                # Total searches
                cursor.execute("SELECT COUNT(*) as count FROM usage_logs")
                total_searches = cursor.fetchone()['count']
                
                # Searches today
                cursor.execute("""
                    SELECT COUNT(*) as count FROM usage_logs 
                    WHERE DATE(created_at) = CURRENT_DATE
                """)
                searches_today = cursor.fetchone()['count']
                
                # Searches this week
                cursor.execute("""
                    SELECT COUNT(*) as count FROM usage_logs 
                    WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)
                """)
                searches_this_week = cursor.fetchone()['count']
                
                # Searches this month
                cursor.execute("""
                    SELECT COUNT(*) as count FROM usage_logs 
                    WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                searches_this_month = cursor.fetchone()['count']
                
                # Average searches per user per day
                cursor.execute("""
                    SELECT 
                        COALESCE(AVG(daily_searches), 0) as avg_daily_searches
                    FROM (
                        SELECT 
                            user_id,
                            DATE(created_at) as search_date,
                            COUNT(*) as daily_searches
                        FROM usage_logs
                        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                        GROUP BY user_id, DATE(created_at)
                    ) user_daily_stats
                """)
                avg_daily_searches_per_user = cursor.fetchone()['avg_daily_searches'] or 0
                
                # Recent searches (last 10 with user info)
                cursor.execute("""
                    SELECT u.full_name, ul.query, ul.created_at
                    FROM usage_logs ul
                    LEFT JOIN users u ON ul.user_id = u.telegram_id
                    WHERE ul.query IS NOT NULL AND ul.query != '' AND TRIM(ul.query) != ''
                    ORDER BY ul.created_at DESC
                    LIMIT 10
                """)
                recent_searches = cursor.fetchall()
                
                # Popular queries (last 7 days)
                cursor.execute("""
                    SELECT query, COUNT(*) as count
                    FROM usage_logs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                      AND query IS NOT NULL AND query != '' AND TRIM(query) != ''
                    GROUP BY query
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC
                    LIMIT 5
                """)
                popular_queries = cursor.fetchall()
                
                # Initialize default values for API
                recent_not_found_api = []
                recent_search_results_api = []
                failed_stats_api = {'failed_today': 0, 'failed_week': 0}
                
                # Try to get additional data for API, but don't fail if tables don't exist
                try:
                    # Recent not found queries (for API)
                    cursor.execute("""
                        SELECT nfq.query, nfq.search_timestamp, u.full_name, nfq.language
                        FROM not_found_queries nfq
                        LEFT JOIN users u ON nfq.user_id = u.telegram_id
                        WHERE nfq.query IS NOT NULL AND TRIM(nfq.query) != ''
                        ORDER BY nfq.search_timestamp DESC
                        LIMIT 5
                    """)
                    recent_not_found_api = cursor.fetchall()
                except Exception as e:
                    logger.warning(f"API: Could not fetch not_found_queries: {e}")
                
                try:
                    # Recent search results (for API)
                    cursor.execute("""
                        SELECT sr.query, sr.main_code, sr.main_accuracy, 
                               sr.search_timestamp, u.full_name
                        FROM search_results sr
                        LEFT JOIN users u ON sr.user_id = u.telegram_id
                        WHERE sr.main_code IS NOT NULL
                        ORDER BY sr.search_timestamp DESC
                        LIMIT 5
                    """)
                    recent_search_results_api = cursor.fetchall()
                except Exception as e:
                    logger.warning(f"API: Could not fetch search_results: {e}")
                
                try:
                    # Failed stats for API
                    cursor.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM not_found_queries WHERE DATE(search_timestamp) = CURRENT_DATE) as failed_today,
                            (SELECT COUNT(*) FROM not_found_queries WHERE search_timestamp >= CURRENT_DATE - INTERVAL '7 days') as failed_week
                    """)
                    failed_stats_api_result = cursor.fetchone()
                    if failed_stats_api_result:
                        failed_stats_api = failed_stats_api_result
                except Exception as e:
                    logger.warning(f"API: Could not fetch failed stats: {e}")
                
                # Format datetime objects for JSON serialization
                for search in recent_searches:
                    if search['created_at']:
                        search['created_at'] = search['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                for failed in recent_not_found_api:
                    if failed['search_timestamp']:
                        failed['search_timestamp'] = failed['search_timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                
                for result in recent_search_results_api:
                    if result['search_timestamp']:
                        result['search_timestamp'] = result['search_timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepare response data and convert Decimal objects to float
        response_data = {
            "success": True,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "user_stats": {
                'total_users': total_users or 0,
                'new_users_today': new_users_today or 0,
                'new_users_this_week': new_users_this_week or 0,
                'new_users_this_month': new_users_this_month or 0,
                'active_users_today': active_users_today or 0,
                'active_users_this_week': active_users_this_week or 0,
                'active_users_this_month': active_users_this_month or 0,
                'total_searches': total_searches or 0,
                'searches_today': searches_today or 0,
                'searches_this_week': searches_this_week or 0,
                'searches_this_month': searches_this_month or 0,
                'avg_daily_searches_per_user': round(float(avg_daily_searches_per_user or 0), 2)
            },
            "recent_searches": [dict(search) for search in (recent_searches or [])],
            "popular_queries": [dict(query) for query in (popular_queries or [])],
            "recent_not_found": [dict(failed) for failed in (recent_not_found_api or [])],
            "recent_search_results": [dict(result) for result in (recent_search_results_api or [])],
            "failed_stats": dict(failed_stats_api) if failed_stats_api else {"failed_today": 0, "failed_week": 0}
        }
        
        # Convert any Decimal objects to float
        response_data = convert_decimal_to_float(response_data)
        
        return JSONResponse(response_data)
        
    except Exception as e:
        logger.error(f"Dashboard API error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/test-db", response_class=HTMLResponse)
async def test_database(request: Request):
    """Test database connection with beautiful UI"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get user count
                cursor.execute("SELECT COUNT(*) as count FROM users")
                user_count = cursor.fetchone()['count']
                
                # Get recent activity
                cursor.execute("SELECT COUNT(*) as count FROM usage_logs WHERE DATE(created_at) = CURRENT_DATE")
                today_activity = cursor.fetchone()['count']
                
                # Get table list
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = [row['table_name'] for row in cursor.fetchall()]
        
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Test - TNVED Bot Admin</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                body {{ font-family: 'Inter', sans-serif; padding: 2rem; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .card {{ background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 2rem; }}
                .success {{ color: #28a745; }}
                .header {{ text-align: center; margin-bottom: 2rem; }}
                .stat {{ display: inline-block; margin: 0 2rem; text-align: center; }}
                .stat h3 {{ color: #007bff; margin: 0; }}
                .tables {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }}
                .table-item {{ background: #f8f9fa; padding: 1rem; border-radius: 8px; text-align: center; }}
                .btn {{ display: inline-block; padding: 0.75rem 1.5rem; background: #007bff; color: white; text-decoration: none; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <div class="header">
                        <h1>🗄️ Database Connection Test</h1>
                        <p class="success"><i class="fas fa-check-circle"></i> Connection successful!</p>
                    </div>
                    
                    <div style="text-align: center; margin-bottom: 2rem;">
                        <div class="stat">
                            <h3>{user_count}</h3>
                            <p>Total Users</p>
                        </div>
                        <div class="stat">
                            <h3>{today_activity}</h3>
                            <p>Today's Activity</p>
                        </div>
                        <div class="stat">
                            <h3>{len(tables)}</h3>
                            <p>Database Tables</p>
                        </div>
                    </div>
                    
                    <h3>Available Tables:</h3>
                    <div class="tables">
                        {''.join([f'<div class="table-item"><i class="fas fa-table"></i><br>{table}</div>' for table in tables])}
                    </div>
                    
                    <div style="text-align: center; margin-top: 2rem;">
                        <a href="/" class="btn"><i class="fas fa-arrow-left"></i> Back to Dashboard</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Error</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Inter', sans-serif; padding: 2rem; background: #f8f9fa; }}
                .error {{ max-width: 600px; margin: 0 auto; background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            </style>
        </head>
        <body>
            <div class="error">
                <h2 style="color: #e74c3c;">❌ Database Connection Failed</h2>
                <p>Error: {str(e)}</p>
                <a href="/" style="color: #007bff;">← Back to Dashboard</a>
            </div>
        </body>
        </html>
        """)

@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """Users management page with beautiful UI"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT u.telegram_id, u.full_name, u.username, u.phone, u.language, 
                           u.registered_at, MAX(ul.created_at) as last_active 
                    FROM users u
                    LEFT JOIN usage_logs ul ON u.telegram_id = ul.user_id
                    GROUP BY u.telegram_id, u.full_name, u.username, u.phone, u.language, u.registered_at
                    ORDER BY u.registered_at DESC 
                    LIMIT 50
                """)
                users = cursor.fetchall()
        
        return templates.TemplateResponse("users.html", {
            "request": request,
            "username": username,
            "users": users,
            "t": get_translations(request),
            "current_language": get_language(request)
        })
        
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading users: {str(e)}</h1>")

# User Search Feature
@app.get("/user-search", response_class=HTMLResponse)
async def user_search_page(request: Request):
    """User search page"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    return templates.TemplateResponse("user_search.html", {
        "request": request,
        "username": username,
        "current_language": get_language(request),
        "t": get_translations(request),
        "user_data": None,
        "search_history": None,
        "query": ""
    })

@app.post("/user-search", response_class=HTMLResponse)
async def user_search_results(request: Request, query: str = Form(...)):
    """Search for user and display their search history"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                user_data = None
                search_history = []
                not_found_history = []
                
                # Search for user by ID or name
                if query.isdigit():
                    # Search by Telegram ID
                    cursor.execute("""
                        SELECT u.telegram_id, u.full_name, u.username, u.phone, u.language, 
                               u.registered_at, u.requests_today, COUNT(ul.id) as total_searches,
                               MAX(ul.created_at) as last_active
                        FROM users u
                        LEFT JOIN usage_logs ul ON u.telegram_id = ul.user_id
                        WHERE u.telegram_id = %s
                        GROUP BY u.telegram_id, u.full_name, u.username, u.phone, u.language, u.registered_at, u.requests_today
                    """, (int(query),))
                else:
                    # Search by name (case-insensitive partial match)
                    cursor.execute("""
                        SELECT u.telegram_id, u.full_name, u.username, u.phone, u.language, 
                               u.registered_at, u.requests_today, COUNT(ul.id) as total_searches,
                               MAX(ul.created_at) as last_active
                        FROM users u
                        LEFT JOIN usage_logs ul ON u.telegram_id = ul.user_id
                        WHERE LOWER(u.full_name) LIKE LOWER(%s) 
                           OR LOWER(u.username) LIKE LOWER(%s)
                        GROUP BY u.telegram_id, u.full_name, u.username, u.phone, u.language, u.registered_at, u.requests_today
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
                                   'Found' as result_status
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
        logger.error(f"Error in user search: {e}")
        user_data = None
        search_history = []
        not_found_history = []
    
    return templates.TemplateResponse("user_search.html", {
        "request": request,
        "username": username,
        "current_language": get_language(request),
        "t": get_translations(request),
        "user_data": user_data,
        "search_history": search_history,
        "not_found_history": not_found_history,
        "query": query,
        "multiple_users": isinstance(user_data, list) and len(user_data) > 1
    })

# Search Results page - NEW FEATURE
@app.get("/search-results", response_class=HTMLResponse)
async def search_results_detailed_page(request: Request):
    """Detailed search results page with comprehensive TNVED code analysis"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get recent search results with user info (default: last 7 days)
                cursor.execute("""
                    SELECT sr.*, u.full_name, u.username
                    FROM search_results sr
                    LEFT JOIN users u ON sr.user_id = u.telegram_id
                    WHERE sr.search_timestamp >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY sr.search_timestamp DESC
                    LIMIT 100
                """)
                search_results = cursor.fetchall()
                
                # Get comprehensive statistics
                cursor.execute("SELECT COUNT(*) as total FROM search_results")
                total_results = cursor.fetchone()['total']
                
                cursor.execute("""
                    SELECT COUNT(*) as week_results 
                    FROM search_results 
                    WHERE search_timestamp >= CURRENT_DATE - INTERVAL '7 days'
                """)
                week_results = cursor.fetchone()['week_results']
                
                cursor.execute("""
                    SELECT COUNT(DISTINCT main_code) as unique_codes
                    FROM search_results
                    WHERE main_code IS NOT NULL
                """)
                unique_codes = cursor.fetchone()['unique_codes']
                
                cursor.execute("""
                    SELECT AVG(main_accuracy) as avg_accuracy
                    FROM search_results
                    WHERE main_accuracy IS NOT NULL
                """)
                avg_accuracy_result = cursor.fetchone()['avg_accuracy']
                avg_accuracy = f"{float(avg_accuracy_result):.3f}" if avg_accuracy_result else "0.000"
                
        return templates.TemplateResponse("search_results_detailed.html", {
            "request": request,
            "username": username,
            "current_language": get_language(request),
            "t": get_translations(request),
            "search_results": search_results,
            "total_results": total_results,
            "week_results": week_results,
            "unique_codes": unique_codes,
            "avg_accuracy": avg_accuracy
        })
        
    except Exception as e:
        logger.error(f"Error loading search results: {e}")
        return HTMLResponse(f"<h1>Error loading search results: {str(e)}</h1>", status_code=500)

@app.get("/api/search-results-data")
async def get_search_results_data(request: Request):
    """API endpoint for filtered search results data"""
    username = authenticate(request)
    if not username:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        # Get filter parameters
        date_filter = request.query_params.get('date_filter', 'today')
        language_filter = request.query_params.get('language_filter', 'all')
        accuracy_filter = request.query_params.get('accuracy_filter', 'all')
        query_search = request.query_params.get('query_search', '')
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build WHERE clause based on filters
                where_conditions = []
                params = []
                
                # Date filter
                if date_filter == 'today':
                    where_conditions.append("DATE(sr.search_timestamp) = CURRENT_DATE")
                elif date_filter == 'week':
                    where_conditions.append("sr.search_timestamp >= CURRENT_DATE - INTERVAL '7 days'")
                elif date_filter == 'month':
                    where_conditions.append("sr.search_timestamp >= CURRENT_DATE - INTERVAL '30 days'")
                
                # Language filter
                if language_filter != 'all':
                    where_conditions.append("sr.language = %s")
                    params.append(language_filter)
                
                # Accuracy filter
                if accuracy_filter == 'high':
                    where_conditions.append("sr.main_accuracy >= 0.9")
                elif accuracy_filter == 'medium':
                    where_conditions.append("sr.main_accuracy >= 0.7 AND sr.main_accuracy < 0.9")
                elif accuracy_filter == 'low':
                    where_conditions.append("sr.main_accuracy < 0.7")
                
                # Query search
                if query_search:
                    where_conditions.append("LOWER(sr.query) LIKE LOWER(%s)")
                    params.append(f'%{query_search}%')
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # Get filtered results
                cursor.execute(f"""
                    SELECT sr.*, u.full_name, u.username
                    FROM search_results sr
                    LEFT JOIN users u ON sr.user_id = u.telegram_id
                    WHERE {where_clause}
                    ORDER BY sr.search_timestamp DESC
                    LIMIT 200
                """, params)
                
                search_results = cursor.fetchall()
                
                # Convert to list of dicts for JSON serialization
                results_list = []
                for result in search_results:
                    result_dict = dict(result)
                    # Format timestamp for JSON
                    if result_dict['search_timestamp']:
                        result_dict['search_timestamp'] = result_dict['search_timestamp'].isoformat()
                    results_list.append(result_dict)
                
                # Get statistics for filtered data
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_results,
                        COUNT(CASE WHEN DATE(sr.search_timestamp) = CURRENT_DATE THEN 1 END) as today_results,
                        COUNT(DISTINCT sr.main_code) as unique_codes,
                        AVG(sr.main_accuracy) as avg_accuracy
                    FROM search_results sr
                    LEFT JOIN users u ON sr.user_id = u.telegram_id
                    WHERE {where_clause}
                """, params)
                
                stats = cursor.fetchone()
                formatted_stats = {
                    'total_results': stats['total_results'] or 0,
                    'today_results': stats['today_results'] or 0,
                    'unique_codes': stats['unique_codes'] or 0,
                    'avg_accuracy': f"{float(stats['avg_accuracy']):.3f}" if stats['avg_accuracy'] else "0.000"
                }
                
        # Prepare response data and convert any Decimal objects to float
        response_data = {
            "success": True,
            "results": results_list,
            "stats": formatted_stats,
            "filters_applied": {
                "date_filter": date_filter,
                "language_filter": language_filter,
                "accuracy_filter": accuracy_filter,
                "query_search": query_search
            }
        }
        
        # Convert any Decimal objects to float
        response_data = convert_decimal_to_float(response_data)
        
        return JSONResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error getting search results data: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/search-result-detail/{result_id}")
async def get_search_result_detail(request: Request, result_id: int):
    """API endpoint for single search result details"""
    username = authenticate(request)
    if not username:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT sr.*, u.full_name, u.username
                    FROM search_results sr
                    LEFT JOIN users u ON sr.user_id = u.telegram_id
                    WHERE sr.id = %s
                """, (result_id,))
                
                result = cursor.fetchone()
                
                if not result:
                    return JSONResponse({"error": "Result not found"}, status_code=404)
                
                # Convert to dict and format timestamp
                result_dict = dict(result)
                if result_dict['search_timestamp']:
                    result_dict['search_timestamp'] = result_dict['search_timestamp'].isoformat()
                
                # Convert any Decimal objects to float
                result_dict = convert_decimal_to_float(result_dict)
                
                return JSONResponse(result_dict)
                
    except Exception as e:
        logger.error(f"Error getting search result detail: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/export-search-results")
async def export_search_results(request: Request):
    """Export search results to Excel"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT sr.*, u.full_name, u.username
                    FROM search_results sr
                    LEFT JOIN users u ON sr.user_id = u.telegram_id
                    ORDER BY sr.search_timestamp DESC
                """)
                search_results = cursor.fetchall()
                
                # Convert to list of dicts
                results_data = [dict(result) for result in search_results]
        
        # Create Excel file using pandas
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_file.close()
        
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            # Create DataFrame
            df = pd.DataFrame(results_data)
            
            # Format datetime columns
            if 'search_timestamp' in df.columns:
                df['search_timestamp'] = pd.to_datetime(df['search_timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Rename columns for better readability
            column_mapping = {
                'user_id': 'User ID',
                'query': 'Search Query',
                'search_timestamp': 'Search Timestamp',
                'main_code': 'Main TNVED Code',
                'main_description': 'Main Description',
                'main_accuracy': 'Main Accuracy',
                'similar_1_code': 'Similar 1 Code',
                'similar_1_description': 'Similar 1 Description',
                'similar_1_accuracy': 'Similar 1 Accuracy',
                'similar_2_code': 'Similar 2 Code',
                'similar_2_description': 'Similar 2 Description',
                'similar_2_accuracy': 'Similar 2 Accuracy',
                'similar_3_code': 'Similar 3 Code',
                'similar_3_description': 'Similar 3 Description',
                'similar_3_accuracy': 'Similar 3 Accuracy',
                'language': 'Language',
                'total_results_found': 'Total Results Found',
                'full_name': 'User Name',
                'username': 'Username'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Write to Excel
            df.to_excel(writer, sheet_name='Search Results', index=False)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tnved_search_results_{timestamp}.xlsx"
        
        return FileResponse(
            path=temp_file.name,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error exporting search results: {e}")
        return HTMLResponse(f"<h1>Error exporting search results: {str(e)}</h1>", status_code=500)

# Excel Export Functions
def create_users_excel(users_data: list, search_history_data: dict = None) -> str:
    """Create Excel file with users data and return file path"""
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_file.close()
        
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            # Main users sheet
            users_df = pd.DataFrame(users_data)
            
            # Format datetime columns
            if 'registered_at' in users_df.columns:
                users_df['registered_at'] = pd.to_datetime(users_df['registered_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
            if 'last_active' in users_df.columns:
                users_df['last_active'] = pd.to_datetime(users_df['last_active']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Rename columns for better readability
            column_mapping = {
                'telegram_id': 'Telegram ID',
                'full_name': 'Full Name',
                'username': 'Username',
                'phone': 'Phone',
                'language': 'Language',
                'registered_at': 'Registration Date',
                'last_active': 'Last Active',
                'total_searches': 'Total Searches',
                'requests_today': 'Requests Today'
            }
            users_df = users_df.rename(columns=column_mapping)
            
            # Write users data
            users_df.to_excel(writer, sheet_name='Users', index=False)
            
            # Add search history if provided
            if search_history_data:
                for user_id, searches in search_history_data.items():
                    if searches:
                        history_df = pd.DataFrame(searches)
                        if 'created_at' in history_df.columns:
                            history_df['created_at'] = pd.to_datetime(history_df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Rename columns
                        history_mapping = {
                            'query': 'Search Query',
                            'created_at': 'Search Date',
                            'result_status': 'Status'
                        }
                        history_df = history_df.rename(columns=history_mapping)
                        
                        # Create sheet name (limit to 31 chars for Excel)
                        sheet_name = f"User_{user_id}_History"[:31]
                        history_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Add summary sheet
            summary_data = {
                'Metric': [
                    'Total Users',
                    'Total Searches',
                    'Average Searches per User',
                    'Export Date',
                    'Export Time'
                ],
                'Value': [
                    len(users_data),
                    sum([user.get('total_searches', 0) for user in users_data]),
                    round(sum([user.get('total_searches', 0) for user in users_data]) / max(len(users_data), 1), 2),
                    datetime.now().strftime('%Y-%m-%d'),
                    datetime.now().strftime('%H:%M:%S')
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        return temp_file.name
        
    except Exception as e:
        logger.error(f"Error creating Excel file: {e}")
        raise e

@app.get("/export-users")
async def export_all_users(request: Request):
    """Export all users to Excel file"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get all users with their statistics (FIXED QUERY)
                cursor.execute("""
                    SELECT u.telegram_id, u.full_name, u.username, u.phone, u.language, 
                           u.registered_at, u.requests_today,
                           COALESCE(search_stats.total_searches, 0) as total_searches,
                           search_stats.last_active
                    FROM users u
                    LEFT JOIN (
                        SELECT user_id, COUNT(*) as total_searches, MAX(created_at) as last_active
                        FROM usage_logs
                        GROUP BY user_id
                    ) search_stats ON u.telegram_id = search_stats.user_id
                    ORDER BY u.registered_at DESC
                """)
                users = cursor.fetchall()
                
                # Convert to list of dicts
                users_data = [dict(user) for user in users]
        
        # Create Excel file
        excel_file_path = create_users_excel(users_data)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tnved_bot_users_{timestamp}.xlsx"
        
        # logger.info(f"All users exported by {username}: {len(users_data)} users")
        
        return FileResponse(
            path=excel_file_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error exporting users: {e}")
        return HTMLResponse(f"<h1>Error exporting users: {str(e)}</h1>", status_code=500)

@app.post("/export-users-custom")
async def export_custom_users(request: Request, user_ids: str = Form(...), include_history: str = Form("false")):
    """Export selected users to Excel file"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    try:
        # Parse user IDs
        try:
            selected_ids = [int(id.strip()) for id in user_ids.split(',') if id.strip().isdigit()]
        except:
            return HTMLResponse("<h1>Error: Invalid user IDs format</h1>", status_code=400)
        
        if not selected_ids:
            return HTMLResponse("<h1>Error: No valid user IDs provided</h1>", status_code=400)
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get selected users (FIXED QUERY)
                ids_placeholder = ','.join(['%s'] * len(selected_ids))
                cursor.execute(f"""
                    SELECT u.telegram_id, u.full_name, u.username, u.phone, u.language, 
                           u.registered_at, u.requests_today,
                           COALESCE(search_stats.total_searches, 0) as total_searches,
                           search_stats.last_active
                    FROM users u
                    LEFT JOIN (
                        SELECT user_id, COUNT(*) as total_searches, MAX(created_at) as last_active
                        FROM usage_logs
                        GROUP BY user_id
                    ) search_stats ON u.telegram_id = search_stats.user_id
                    WHERE u.telegram_id IN ({ids_placeholder})
                    ORDER BY u.registered_at DESC
                """, selected_ids)
                users = cursor.fetchall()
                
                # Convert to list of dicts
                users_data = [dict(user) for user in users]
                
                # Get search history if requested
                search_history_data = {}
                if include_history == "true":
                    for user_id in selected_ids:
                        cursor.execute("""
                            SELECT ul.query, ul.created_at, 'Found' as result_status
                            FROM usage_logs ul
                            WHERE ul.user_id = %s
                            ORDER BY ul.created_at DESC
                            LIMIT 100
                        """, (user_id,))
                        history = cursor.fetchall()
                        if history:
                            search_history_data[user_id] = [dict(h) for h in history]
        
        # Create Excel file
        excel_file_path = create_users_excel(users_data, search_history_data)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tnved_bot_users_custom_{timestamp}.xlsx"
        
        # logger.info(f"Custom users exported by {username}: {len(users_data)} users")
        
        return FileResponse(
            path=excel_file_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error exporting custom users: {e}")
        return HTMLResponse(f"<h1>Error exporting users: {str(e)}</h1>", status_code=500)

@app.get("/export-user-history/{user_id}")
async def export_user_history(request: Request, user_id: int):
    """Export specific user's complete history to Excel"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get user info (FIXED QUERY)
                cursor.execute("""
                    SELECT u.telegram_id, u.full_name, u.username, u.phone, u.language, 
                           u.registered_at, u.requests_today,
                           COALESCE(search_stats.total_searches, 0) as total_searches,
                           search_stats.last_active
                    FROM users u
                    LEFT JOIN (
                        SELECT user_id, COUNT(*) as total_searches, MAX(created_at) as last_active
                        FROM usage_logs
                        GROUP BY user_id
                    ) search_stats ON u.telegram_id = search_stats.user_id
                    WHERE u.telegram_id = %s
                """, (user_id,))
                user = cursor.fetchone()
                
                if not user:
                    return HTMLResponse("<h1>User not found</h1>", status_code=404)
                
                # Get search history
                cursor.execute("""
                    SELECT ul.query, ul.created_at, 'Found' as result_status
                    FROM usage_logs ul
                    WHERE ul.user_id = %s
                    ORDER BY ul.created_at DESC
                """, (user_id,))
                search_history = cursor.fetchall()
                
                # Get failed searches
                cursor.execute("""
                    SELECT nfq.query, nfq.search_timestamp as created_at, nfq.language, 'Not Found' as result_status
                    FROM not_found_queries nfq
                    WHERE nfq.user_id = %s
                    ORDER BY nfq.search_timestamp DESC
                """, (user_id,))
                failed_searches = cursor.fetchall()
        
        # Create comprehensive Excel file
        users_data = [dict(user)]
        history_data = {user_id: [dict(h) for h in search_history + failed_searches]}
        
        excel_file_path = create_users_excel(users_data, history_data)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        user_name = user['full_name'] or f"User_{user_id}"
        safe_name = "".join(c for c in user_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"tnved_bot_{safe_name}_{timestamp}.xlsx"
        
        # logger.info(f"User history exported by {username}: User {user_id}")
        
        return FileResponse(
            path=excel_file_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error exporting user history: {e}")
        return HTMLResponse(f"<h1>Error exporting user history: {str(e)}</h1>", status_code=500)

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Enhanced Analytics page with comprehensive daily, weekly, and monthly user tracking"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Basic stats
                cursor.execute("SELECT COUNT(*) as total FROM users")
                total_users = cursor.fetchone()['total']
                
                cursor.execute("SELECT COUNT(*) as total FROM usage_logs")
                total_searches = cursor.fetchone()['total']
                
                # Simplified analytics to avoid complex queries
                
                # Growth rate (new users last 30 days)
                cursor.execute("""
                    SELECT COUNT(*) as new_users FROM users 
                    WHERE registered_at >= CURRENT_DATE - INTERVAL '30 days'
                """)
                new_users_month = cursor.fetchone()['new_users']
                growth_rate = round((new_users_month / max(total_users, 1)) * 100, 1) if total_users > 0 else 0
                
                # Success rate
                cursor.execute("SELECT COUNT(*) as found FROM usage_logs")
                found_searches = cursor.fetchone()['found']
                cursor.execute("SELECT COUNT(*) as not_found FROM not_found_queries")  
                not_found_searches = cursor.fetchone()['not_found']
                total_all = found_searches + not_found_searches
                success_rate = round((found_searches / max(total_all, 1)) * 100, 1) if total_all > 0 else 100
                
                # Average queries per user
                avg_queries_per_user = round(total_searches / max(total_users, 1), 1) if total_users > 0 else 0
                
                # Peak hour (simplified)
                cursor.execute("""
                    SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as count
                    FROM usage_logs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY EXTRACT(HOUR FROM created_at)
                    ORDER BY count DESC
                    LIMIT 1
                """)
                peak_data = cursor.fetchone()
                peak_hour = int(peak_data['hour']) if peak_data else 14
                
                # Active users this week
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as active FROM usage_logs 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                """)
                active_users_week = cursor.fetchone()['active']
                
                # Language distribution
                cursor.execute("""
                    SELECT 
                        COALESCE(language, 'Unknown') as language,
                        COUNT(*) as count
                    FROM users 
                    GROUP BY language 
                    ORDER BY count DESC
                    LIMIT 4
                """)
                language_stats = cursor.fetchall()
                
                # Top queries
                cursor.execute("""
                    SELECT query, COUNT(*) as count, 0 as trend
                    FROM usage_logs 
                    WHERE query IS NOT NULL AND TRIM(query) != ''
                    AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY query 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                top_queries = cursor.fetchall()
                
                # User growth data (last 30 days)
                cursor.execute("""
                    SELECT 
                        DATE(registered_at) as date,
                        COUNT(*) as new_users
                    FROM users
                    WHERE registered_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(registered_at)
                    ORDER BY date
                """)
                growth_data_raw = cursor.fetchall()
                
                # Search trends (last 7 days) 
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as searches
                    FROM usage_logs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """)
                search_trends_raw = cursor.fetchall()
                
                # Hourly usage (simplified)
                cursor.execute("""
                    SELECT 
                        EXTRACT(HOUR FROM created_at) as hour,
                        COUNT(*) as count
                    FROM usage_logs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY EXTRACT(HOUR FROM created_at)
                    ORDER BY hour
                """)
                hourly_data_raw = cursor.fetchall()
                
                # Format data for charts
                growth_labels = [item['date'].strftime('%m/%d') for item in growth_data_raw[-30:]]
                growth_data = [item['new_users'] for item in growth_data_raw[-30:]]
                
                search_trend_labels = [item['date'].strftime('%m/%d') for item in search_trends_raw[-7:]]
                search_trend_data = [item['searches'] for item in search_trends_raw[-7:]]
                
                hourly_labels = [f"{int(item['hour']):02d}:00" for item in hourly_data_raw]
                hourly_data = [item['count'] for item in hourly_data_raw]
                
                language_labels = [lang['language'] for lang in language_stats]
                language_data = [lang['count'] for lang in language_stats]
                
                # Insights
                avg_session_length = 5  # Placeholder
                retention_rate = round((active_users_week / max(total_users, 1)) * 100, 1) if total_users > 0 else 0
                
                insight_1 = f"Peak usage at {peak_hour}:00 with highest activity"
                insight_2 = f"User retention: {retention_rate}% of users active weekly"  
                insight_3 = f"Growth: {new_users_month} new users this month ({growth_rate}% growth)"
                
        # Ensure we have default data for charts even if database is empty
        if not growth_labels:
            growth_labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
            growth_data = [5, 8, 12, new_users_month]
            
        if not search_trend_labels:
            search_trend_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            search_trend_data = [45, 52, 38, 65, 42, 28, 35]
            
        if not hourly_labels:
            hourly_labels = ['00:00', '06:00', '12:00', '18:00']
            hourly_data = [5, 15, 35, 25]
            
        if not language_labels:
            language_labels = ['Russian', 'Uzbek', 'English']
            language_data = [total_users * 0.7, total_users * 0.25, total_users * 0.05]
        
        # Return comprehensive analytics data
        return templates.TemplateResponse("analytics.html", {
            "request": request,
            "username": username,
            "growth_rate": growth_rate,
            "avg_queries_per_user": avg_queries_per_user, 
            "success_rate": success_rate,
            "peak_hour": peak_hour,
            "active_users_week": active_users_week,
            "avg_session_length": avg_session_length,
            "retention_rate": retention_rate,
            "top_queries": top_queries,
            "language_stats": language_stats,
            "insight_1": insight_1,
            "insight_2": insight_2,
            "insight_3": insight_3,
            "growth_labels": json.dumps(growth_labels),
            "growth_data": json.dumps(growth_data),
            "search_trend_labels": json.dumps(search_trend_labels),
            "search_trend_data": json.dumps(search_trend_data),
            "hourly_labels": json.dumps(hourly_labels),
            "hourly_data": json.dumps(hourly_data),
            "language_labels": json.dumps(language_labels),
            "language_data": json.dumps(language_data),
            "t": get_translations(request),
            "current_language": get_language(request)
        })
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return HTMLResponse(f"<h1>Error loading analytics: {str(e)}</h1>")

@app.get("/api/analytics-data")
async def get_analytics_data(request: Request):
    """Enhanced API endpoint for analytics data with comprehensive tracking"""
    username = authenticate(request)
    if not username:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Daily statistics for the last 7 days
                cursor.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as searches,
                        COUNT(DISTINCT user_id) as active_users
                    FROM usage_logs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """)
                daily_stats = cursor.fetchall()
                
                # Weekly statistics for the last 4 weeks
                cursor.execute("""
                    SELECT 
                        DATE_TRUNC('week', created_at) as week_start,
                        COUNT(*) as searches,
                        COUNT(DISTINCT user_id) as active_users
                    FROM usage_logs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '4 weeks'
                    GROUP BY DATE_TRUNC('week', created_at)
                    ORDER BY week_start
                """)
                weekly_stats = cursor.fetchall()
                
                # Monthly statistics for the last 6 months
                cursor.execute("""
                    SELECT 
                        DATE_TRUNC('month', created_at) as month_start,
                        COUNT(*) as searches,
                        COUNT(DISTINCT user_id) as active_users
                    FROM usage_logs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
                    GROUP BY DATE_TRUNC('month', created_at)
                    ORDER BY month_start
                """)
                monthly_stats = cursor.fetchall()
                
                # User registration statistics
                cursor.execute("""
                    SELECT 
                        'today' as period,
                        COUNT(*) as new_users
                    FROM users 
                    WHERE DATE(registered_at) = CURRENT_DATE
                    UNION ALL
                    SELECT 
                        'this_week' as period,
                        COUNT(*) as new_users
                    FROM users 
                    WHERE registered_at >= DATE_TRUNC('week', CURRENT_DATE)
                    UNION ALL
                    SELECT 
                        'this_month' as period,
                        COUNT(*) as new_users
                    FROM users 
                    WHERE registered_at >= DATE_TRUNC('month', CURRENT_DATE)
                """)
                registration_stats = cursor.fetchall()
                
                # Format data for JSON response
                formatted_daily = []
                for stat in daily_stats:
                    formatted_daily.append({
                        'date': stat['date'].strftime('%Y-%m-%d'),
                        'searches': stat['searches'],
                        'active_users': stat['active_users']
                    })
                
                formatted_weekly = []
                for stat in weekly_stats:
                    formatted_weekly.append({
                        'week_start': stat['week_start'].strftime('%Y-%m-%d'),
                        'searches': stat['searches'],
                        'active_users': stat['active_users']
                    })
                
                formatted_monthly = []
                for stat in monthly_stats:
                    formatted_monthly.append({
                        'month_start': stat['month_start'].strftime('%Y-%m-%d'),
                        'searches': stat['searches'],
                        'active_users': stat['active_users']
                    })
                
                registration_data = {stat['period']: stat['new_users'] for stat in registration_stats}
                
        return JSONResponse({
            "success": True,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "daily_stats": formatted_daily,
            "weekly_stats": formatted_weekly,
            "monthly_stats": formatted_monthly,
            "registration_stats": registration_data
        })
        
    except Exception as e:
        logger.error(f"Analytics API error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/broadcast", response_class=HTMLResponse)
async def broadcast_page(request: Request):
    """Enhanced Broadcast message page with comprehensive user targeting statistics"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get comprehensive user statistics for targeting
                cursor.execute("SELECT COUNT(*) as total FROM users")
                total_users = cursor.fetchone()['total']
                
                # Active users by different time periods
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as active FROM usage_logs 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
                """)
                active_users_today = cursor.fetchone()['active']
                
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as active FROM usage_logs 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                """)
                active_users_week = cursor.fetchone()['active']
                
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as active FROM usage_logs 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                """)
                active_users_month = cursor.fetchone()['active']
                
                # New users by different time periods
                cursor.execute("""
                    SELECT COUNT(*) as new_users FROM users 
                    WHERE registered_at >= CURRENT_DATE
                """)
                new_users_today = cursor.fetchone()['new_users']
                
                cursor.execute("""
                    SELECT COUNT(*) as new_users FROM users 
                    WHERE registered_at >= CURRENT_DATE - INTERVAL '7 days'
                """)
                new_users_week = cursor.fetchone()['new_users']
                
                cursor.execute("""
                    SELECT COUNT(*) as new_users FROM users 
                    WHERE registered_at >= CURRENT_DATE - INTERVAL '30 days'
                """)
                new_users_month = cursor.fetchone()['new_users']
                
                # Language distribution for targeting
                cursor.execute("""
                    SELECT 
                        COALESCE(language, 'unknown') as language, 
                        COUNT(*) as user_count
                    FROM users 
                    GROUP BY language 
                    ORDER BY user_count DESC
                """)
                language_data = cursor.fetchall()
                
                # Format language stats for template
                language_stats = []
                for lang in language_data:
                    language_stats.append({
                        'code': lang['language'] or 'unknown',
                        'count': lang['user_count']
                    })
                
                # User engagement levels for targeting
                cursor.execute("""
                    SELECT 
                        engagement_level,
                        COUNT(*) as user_count
                    FROM (
                        SELECT 
                            u.telegram_id,
                            CASE 
                                WHEN search_count IS NULL OR search_count = 0 THEN 'Inactive'
                                WHEN search_count BETWEEN 1 AND 5 THEN 'Low Activity'
                                WHEN search_count BETWEEN 6 AND 20 THEN 'Medium Activity'
                                WHEN search_count > 20 THEN 'High Activity'
                            END as engagement_level
                        FROM users u
                        LEFT JOIN (
                            SELECT user_id, COUNT(*) as search_count
                            FROM usage_logs
                            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                            GROUP BY user_id
                        ) ul ON u.telegram_id = ul.user_id
                    ) user_engagement
                    GROUP BY engagement_level
                """)
                engagement_stats = cursor.fetchall()
                
        enhanced_broadcast_data = {
            'total_users': total_users,
            'active_users_today': active_users_today,
            'active_users_week': active_users_week,
            'active_users_month': active_users_month,
            'new_users_today': new_users_today,
            'new_users_week': new_users_week,
            'new_users_month': new_users_month,
            'messages_sent_today': 0,  # Would track actual sent messages from a broadcasts table
            'language_stats': language_stats,
            'engagement_stats': engagement_stats
        }
        
        return templates.TemplateResponse("broadcast.html", {
            "request": request,
            "username": username,
            "total_users": enhanced_broadcast_data['total_users'],
            "active_users": enhanced_broadcast_data['active_users_week'],
            "new_users_week": enhanced_broadcast_data['new_users_week'],
            "messages_sent_today": enhanced_broadcast_data['messages_sent_today'],
            "language_stats": enhanced_broadcast_data['language_stats'],
            "t": get_translations(request),
            "current_language": get_language(request)
        })
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        return HTMLResponse(f"<h1>Error loading broadcast page: {str(e)}</h1>")

@app.post("/api/send-broadcast")
async def send_broadcast_api(
    request: Request,
    title: str = Form(...),
    message: str = Form(...),
    target_audience: str = Form(...),
    language: str = Form(None),
    selected_users: str = Form(None)
):
    """API endpoint to send broadcast messages"""
    username = authenticate(request)
    if not username:
        return JSONResponse({"success": False, "message": "Unauthorized"}, status_code=401)
    
    try:
        # Send the broadcast with custom selection support
        result = await send_broadcast(title, message, target_audience, language, selected_users)
        
        if result["success"]:
            # logger.info(f"Broadcast sent by {username}: {result}")
            return JSONResponse(result)
        else:
            logger.error(f"Broadcast failed: {result['message']}")
            return JSONResponse(result, status_code=400)
            
    except Exception as e:
        logger.error(f"Broadcast API error: {e}")
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)

@app.get("/api/users-for-broadcast")
async def get_users_for_broadcast(request: Request):
    """Get all users for broadcast selection"""
    username = authenticate(request)
    if not username:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get all users
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
                
                # Get activity data - users who made queries in last 7 days
                cursor.execute("""
                    SELECT DISTINCT user_id
                    FROM usage_logs
                    WHERE created_at > NOW() - INTERVAL '7 days'
                """)
                active_user_ids = {row['user_id'] for row in cursor.fetchall()}
                
                # Get total searches per user
                cursor.execute("""
                    SELECT user_id, COUNT(*) as search_count
                    FROM usage_logs
                    GROUP BY user_id
                """)
                search_counts = {row['user_id']: row['search_count'] for row in cursor.fetchall()}
                
                # Convert to list of dictionaries
                users_list = []
                for user in users:
                    telegram_id = user['telegram_id']
                    users_list.append({
                        'telegram_id': telegram_id,
                        'full_name': user['full_name'] or 'Unknown User',
                        'username': user['username'],
                        'phone': user['phone'],
                        'language': user['language'] or 'en',
                        'registered_at': user['registered_at'].isoformat() if user['registered_at'] else None,
                        'is_blocked': False,
                        'is_active': telegram_id in active_user_ids,
                        'total_searches': search_counts.get(telegram_id, 0),
                        'requests_today': user['requests_today'] or 0
                    })
                
                # logger.info(f"Successfully loaded {len(users_list)} users for broadcast selection")
                return JSONResponse(users_list)
                
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/preview-audience")
async def preview_audience(request: Request, target: str, language: str = None, selected_users: str = None):
    """Preview how many users will receive the broadcast"""
    username = authenticate(request)
    if not username:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        user_ids = await get_user_list(target, language, selected_users)
        return JSONResponse({"count": len(user_ids), "users": len(user_ids)})
    except Exception as e:
        logger.error(f"Preview audience error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/system", response_class=HTMLResponse)
async def system_page(request: Request):
    """System status page with translations"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    return templates.TemplateResponse("system.html", {
        "request": request,
        "username": username,
        "t": get_translations(request),
        "current_language": get_language(request)
    })

@app.get("/content", response_class=HTMLResponse)
async def content_page(request: Request):
    """Content management page with real editor"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    return templates.TemplateResponse("content.html", {
        "request": request,
        "username": username,
        "t": get_translations(request),
        "current_language": get_language(request)
    })

@app.get("/api/bot-messages")
async def get_bot_messages(request: Request):
    """Get current bot messages from user.py file"""
    username = authenticate(request)
    if not username:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        import ast
        import os
        
        # Try to find the user.py file
        possible_paths = [
            "bot/handlers/user.py",
            "../bot/handlers/user.py",
            "TNVED/bot/handlers/user.py",
            "../TNVED/bot/handlers/user.py"
        ]
        
        user_py_path = None
        for path in possible_paths:
            if os.path.exists(path):
                user_py_path = path
                break
        
        if not user_py_path:
            return JSONResponse({"error": "Could not find user.py file"}, status_code=404)
        
        # Read and parse the user.py file to extract MESSAGES
        with open(user_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST to find MESSAGES dictionary
        tree = ast.parse(content)
        messages_dict = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'MESSAGES':
                        # Convert AST back to string and evaluate
                        messages_dict = ast.literal_eval(node.value)
                        break
        
        if messages_dict:
            return JSONResponse({
                "success": True,
                "messages": messages_dict,
                "file_path": user_py_path
            })
        else:
            return JSONResponse({"error": "Could not find MESSAGES dictionary"}, status_code=404)
            
    except Exception as e:
        logger.error(f"Error reading bot messages: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/bot-messages")
async def update_bot_messages(request: Request):
    """Update bot messages in user.py file"""
    username = authenticate(request)
    if not username:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        data = await request.json()
        messages = data.get('messages', {})
        file_path = data.get('file_path', 'bot/handlers/user.py')
        
        if not os.path.exists(file_path):
            return JSONResponse({"error": "File not found"}, status_code=404)
        
        # Read current file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create backup
        backup_path = f"{file_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Replace MESSAGES dictionary
        import ast
        import re
        
        # Find the MESSAGES dictionary and replace it
        # This is a simple approach - find the start and end of MESSAGES dict
        start_pattern = r'MESSAGES\s*=\s*{'
        
        # Find the start of MESSAGES
        start_match = re.search(start_pattern, content)
        if not start_match:
            return JSONResponse({"error": "Could not find MESSAGES dictionary"}, status_code=404)
        
        start_pos = start_match.start()
        
        # Find the matching closing brace
        brace_count = 0
        end_pos = start_pos
        in_messages = False
        
        for i, char in enumerate(content[start_pos:], start_pos):
            if char == '{':
                brace_count += 1
                in_messages = True
            elif char == '}' and in_messages:
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
        
        # Format the new MESSAGES dictionary
        formatted_messages = json.dumps(messages, indent=4, ensure_ascii=False)
        new_messages_code = f"MESSAGES = {formatted_messages}"
        
        # Replace the old MESSAGES with new one
        new_content = content[:start_pos] + new_messages_code + content[end_pos:]
        
        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # logger.info(f"Bot messages updated by {username}")
        return JSONResponse({
            "success": True,
            "message": "Messages updated successfully",
            "backup_created": backup_path
        })
        
    except Exception as e:
        logger.error(f"Error updating bot messages: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/set-language/{language}")
async def set_language(language: str, request: Request):
    """Set admin panel language"""
    username = authenticate(request)
    if not username:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    if language not in ['en', 'ru']:
        return JSONResponse({"error": "Unsupported language"}, status_code=400)
    
    # Redirect back to dashboard with language cookie
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="admin_language", value=language, max_age=365*24*3600)  # 1 year
    return response

@app.get("/api/key-metrics")
async def get_key_metrics(request: Request):
    """API endpoint for key metrics summary - used for dashboard widgets"""
    username = authenticate(request)
    if not username:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Key metrics for today
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM users) as total_users,
                        (SELECT COUNT(*) FROM users WHERE DATE(registered_at) = CURRENT_DATE) as new_users_today,
                        (SELECT COUNT(DISTINCT user_id) FROM usage_logs WHERE DATE(created_at) = CURRENT_DATE) as active_users_today,
                        (SELECT COUNT(*) FROM usage_logs WHERE DATE(created_at) = CURRENT_DATE) as searches_today,
                        (SELECT COUNT(*) FROM usage_logs) as total_searches
                """)
                today_metrics = cursor.fetchone()
                
                # Key metrics for this week
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM users WHERE registered_at >= DATE_TRUNC('week', CURRENT_DATE)) as new_users_this_week,
                        (SELECT COUNT(DISTINCT user_id) FROM usage_logs WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)) as active_users_this_week,
                        (SELECT COUNT(*) FROM usage_logs WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)) as searches_this_week
                """)
                week_metrics = cursor.fetchone()
                
                # Key metrics for this month
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM users WHERE registered_at >= DATE_TRUNC('month', CURRENT_DATE)) as new_users_this_month,
                        (SELECT COUNT(DISTINCT user_id) FROM usage_logs WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)) as active_users_this_month,
                        (SELECT COUNT(*) FROM usage_logs WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)) as searches_this_month
                """)
                month_metrics = cursor.fetchone()
                
                # Growth rates
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM users WHERE registered_at >= CURRENT_DATE - INTERVAL '30 days') as users_last_30_days,
                        (SELECT COUNT(*) FROM usage_logs WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as searches_last_30_days
                """)
                growth_data = cursor.fetchone()
                
                # Calculate growth rates
                total_users = today_metrics['total_users']
                user_growth_rate = round((growth_data['users_last_30_days'] / max(total_users, 1)) * 100, 1) if total_users > 0 else 0
                
                # Success rate
                cursor.execute("SELECT COUNT(*) as found FROM usage_logs")
                found_searches = cursor.fetchone()['found']
                
                cursor.execute("SELECT COUNT(*) as not_found FROM not_found_queries")
                not_found_searches = cursor.fetchone()['not_found']
                
                total_all = found_searches + not_found_searches
                success_rate = round((found_searches / max(total_all, 1)) * 100, 1) if total_all > 0 else 0
                
                # Average searches per user
                avg_searches_per_user = round(today_metrics['total_searches'] / max(total_users, 1), 2) if total_users > 0 else 0
                
        return JSONResponse({
            "success": True,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "metrics": {
                # Today
                "total_users": today_metrics['total_users'],
                "new_users_today": today_metrics['new_users_today'],
                "active_users_today": today_metrics['active_users_today'],
                "searches_today": today_metrics['searches_today'],
                "total_searches": today_metrics['total_searches'],
                
                # This Week
                "new_users_this_week": week_metrics['new_users_this_week'],
                "active_users_this_week": week_metrics['active_users_this_week'],
                "searches_this_week": week_metrics['searches_this_week'],
                
                # This Month
                "new_users_this_month": month_metrics['new_users_this_month'],
                "active_users_this_month": month_metrics['active_users_this_month'],
                "searches_this_month": month_metrics['searches_this_month'],
                
                # Calculated Metrics
                "user_growth_rate": user_growth_rate,
                "success_rate": success_rate,
                "avg_searches_per_user": avg_searches_per_user,
                "users_last_30_days": growth_data['users_last_30_days'],
                "searches_last_30_days": growth_data['searches_last_30_days']
            }
        })
        
    except Exception as e:
        logger.error(f"Key metrics API error: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

# Database initialization functions
def init_database_tables():
    """Initialize required database tables for enhanced statistics tracking"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Ensure users table exists with all required columns
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        telegram_id BIGINT UNIQUE NOT NULL,
                        full_name VARCHAR(255) NOT NULL,
                        username VARCHAR(100),
                        phone VARCHAR(20),
                        language VARCHAR(2) DEFAULT 'ru',
                        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        requests_today INTEGER DEFAULT 0,
                        last_active TIMESTAMP,
                        is_blocked BOOLEAN DEFAULT FALSE
                    )
                """)
                
                # Ensure usage_logs table exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usage_logs (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        query TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        response_time_ms INTEGER
                    )
                """)
                
                # Ensure not_found_queries table exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS not_found_queries (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        query TEXT NOT NULL,
                        language VARCHAR(2) DEFAULT 'ru',
                        search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        search_source VARCHAR(50) DEFAULT 'bot'
                    )
                """)
                
                # Create search_results table for detailed tracking
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_results (
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
                
                # Create daily_stats table for aggregated daily statistics
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_stats (
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
                
                # Create broadcasts table for tracking sent messages
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS broadcasts (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        message TEXT NOT NULL,
                        target_audience VARCHAR(50) NOT NULL,
                        target_language VARCHAR(2),
                        total_recipients INTEGER DEFAULT 0,
                        successful_sends INTEGER DEFAULT 0,
                        failed_sends INTEGER DEFAULT 0,
                        sent_by VARCHAR(100) NOT NULL,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_registered_at ON users(registered_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_not_found_user_id ON not_found_queries(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_not_found_timestamp ON not_found_queries(search_timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_results_user_id ON search_results(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_results_timestamp ON search_results(search_timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date)")
                
                conn.commit()
                print("✅ Database tables initialized successfully")
                return True
                
    except Exception as e:
        print(f"❌ Error initializing database tables: {e}")
        logger.error(f"❌ Error initializing database tables: {e}")
        return False

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    print("🚀 Starting TNVED Bot Admin Panel...")
    init_database_tables()
    print("✅ Admin Panel ready!")
    yield

@app.get("/init-db", response_class=HTMLResponse)
async def init_database_endpoint(request: Request):
    """Manual database initialization endpoint"""
    username = authenticate(request)
    if not username:
        return HTMLResponse("Unauthorized", status_code=401, headers={"WWW-Authenticate": "Basic"})
    
    success = init_database_tables()
    
    if success:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Initialized</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                body { font-family: 'Inter', sans-serif; padding: 2rem; background: #f8f9fa; }
                .success { max-width: 600px; margin: 0 auto; background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
                .btn { display: inline-block; padding: 0.75rem 1.5rem; background: #007bff; color: white; text-decoration: none; border-radius: 8px; margin-top: 1rem; }
            </style>
        </head>
        <body>
            <div class="success">
                <h2 style="color: #28a745;">✅ Database Initialized Successfully</h2>
                <p>All required tables and indexes have been created for enhanced user tracking and statistics.</p>
                <a href="/" class="btn">← Back to Dashboard</a>
            </div>
        </body>
        </html>
        """)
    else:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Error</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                body { font-family: 'Inter', sans-serif; padding: 2rem; background: #f8f9fa; }
                .error { max-width: 600px; margin: 0 auto; background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
                .btn { display: inline-block; padding: 0.75rem 1.5rem; background: #007bff; color: white; text-decoration: none; border-radius: 8px; margin-top: 1rem; }
            </style>
        </head>
        <body>
            <div class="error">
                <h2 style="color: #e74c3c;">❌ Database Initialization Failed</h2>
                <p>There was an error creating the required database tables. Please check the logs for more details.</p>
                <a href="/" class="btn">← Back to Dashboard</a>
            </div>
        </body>
        </html>
        """)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Beautiful TNVED Bot Admin Panel...")
    print("🎨 Modern UI/UX Dashboard")
    print("📊 Access at: http://localhost:8001")
    print("🔐 Username: admin")
    print("🔑 Password: admin123")
    uvicorn.run(app, host="0.0.0.0", port=8001) 