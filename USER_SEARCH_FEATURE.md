# 🔍 User Search Feature - Admin Panel

## Overview
New feature added to the TNVED Bot Admin Panel that allows administrators to search for users and view their complete search history.

## Features

### 🔎 User Search
- **Search by Telegram ID**: Enter exact Telegram ID (numbers only)
- **Search by Name**: Search by full name or username (partial matches supported)
- **Multiple Results**: Shows all matching users when searching by name

### 📊 User Details Display
- **Basic Information**: Telegram ID, Full Name, Username, Phone, Language
- **Activity Stats**: Registration date, Last activity, Total searches
- **Real-time Data**: All information pulled directly from database

### 📋 Search History
- **Complete History**: Shows up to 50 most recent searches per user
- **Timestamps**: Exact date and time of each search
- **Query Details**: Full search terms used by the user
- **Status Tracking**: Success/failure status for each search

### ❌ Failed Searches
- **Failed Queries**: Shows searches that returned no results
- **Separate Tracking**: Failed searches are tracked in `not_found_queries` table
- **Language Context**: Shows which language was used for the search

## How to Use

### 1. Access the Feature
- Navigate to Admin Panel
- Click **"User Search"** in the left sidebar
- Or go directly to `/user-search`

### 2. Search for Users
- **By ID**: Enter Telegram ID (e.g., `123456789`)
- **By Name**: Enter full name or part of it (e.g., `John` or `John Doe`)

### 3. View Results
- **Single User**: Shows detailed information and complete history
- **Multiple Users**: Shows summary table with "View Details" buttons

### 4. Analyze User Activity
- Review all search queries made by the user
- Check failed searches to understand user needs
- Monitor user activity patterns

## API Endpoints

### GET `/user-search`
- Display the search form

### POST `/user-search`
- Process search query and display results
- **Parameters**: `query` (string) - User ID or name to search

### GET `/api/user-search-details/{user_id}`
- Get detailed JSON data for a specific user
- **Returns**: User info, search history, failed searches, statistics

## Database Tables Used

### `users`
- Main user information table
- Fields: telegram_id, full_name, username, phone, language, registered_at

### `usage_logs`
- Tracks all successful search queries
- Fields: user_id, query, created_at

### `not_found_queries`
- Tracks failed/not found searches
- Fields: user_id, query, search_timestamp, language

## Benefits for Administrators

### 🎯 **User Support**
- Quickly find specific users having issues
- Review their search history to understand problems
- Provide targeted assistance

### 📈 **Usage Analysis**
- Monitor most active users
- Identify common search patterns
- Understand user behavior

### 🐛 **Troubleshooting**
- Review failed searches to improve search algorithm
- Identify missing products in database
- Track user feedback patterns

### 📊 **Business Intelligence**
- User engagement metrics
- Popular search terms per user
- Success/failure rates

## Security

- **Authentication Required**: Only authenticated admin users can access
- **Read-Only**: Feature only displays data, does not modify user information
- **Privacy Compliant**: Shows only necessary business data

## Technical Implementation

- **Backend**: FastAPI with PostgreSQL
- **Frontend**: Bootstrap 5 with responsive design
- **Authentication**: HTTP Basic Auth
- **Performance**: Optimized queries with proper indexing

## Screenshots & Examples

### Search Form
- Clean, simple interface
- Auto-focus on search input
- Clear instructions for ID vs name search

### User Details
- Professional table layout
- Color-coded badges for status
- Responsive design for all screen sizes

### Search History
- Scrollable table with sticky headers
- Date/time formatting
- Status indicators

## Future Enhancements

- **Export Functionality**: Download user data as CSV/Excel
- **Advanced Filters**: Filter by date range, search success/failure
- **User Activity Charts**: Visual representation of user activity
- **Bulk Operations**: Search multiple users at once
- **Real-time Updates**: Live refresh of user activity

---

**Status**: ✅ **COMPLETED AND READY FOR USE**

**Added Files**:
- `templates/user_search.html` - Main search interface
- Updated `app.py` - Backend logic and API endpoints
- Updated `base.html` - Navigation menu item

**Tested**: Basic functionality verified
**Performance**: Optimized database queries
**UI/UX**: Responsive, professional design 