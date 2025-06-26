import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os

class Database:
    """SQLite database handler for local storage"""
    
    def __init__(self, db_path: str = 'planner.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Create database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                schedule_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tasks table for tracking completion
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                name TEXT NOT NULL,
                duration INTEGER NOT NULL,
                priority INTEGER DEFAULT 3,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_value REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sync mapping table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_mapping (
                task_id TEXT PRIMARY KEY,
                calendar_event_id TEXT,
                notion_page_id TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        self.close()
    
    def save_schedule(self, date: str, schedule_data: List[Dict]):
        """Save or update schedule for a date"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Convert schedule data to JSON
        schedule_json = json.dumps(schedule_data)
        
        # Upsert schedule
        cursor.execute('''
            INSERT OR REPLACE INTO schedules (date, schedule_data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (date, schedule_json))
        
        # Extract and save tasks
        for slot in schedule_data:
            if slot.get('task') and not slot.get('is_break'):
                task = slot['task']
                cursor.execute('''
                    INSERT OR REPLACE INTO tasks (id, date, name, duration, priority, completed)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    task['id'],
                    date,
                    task['name'],
                    task['duration'],
                    task.get('priority', 3),
                    task.get('completed', False)
                ))
        
        conn.commit()
        self.close()
    
    def get_schedule(self, date: str) -> Optional[List[Dict]]:
        """Get schedule for a specific date"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT schedule_data FROM schedules WHERE date = ?
        ''', (date,))
        
        row = cursor.fetchone()
        self.close()
        
        if row:
            return json.loads(row['schedule_data'])
        return None
    
    def update_task_status(self, date: str, task_id: str, completed: bool):
        """Update task completion status"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks 
            SET completed = ?, completed_at = ?
            WHERE id = ? AND date = ?
        ''', (
            completed,
            datetime.now() if completed else None,
            task_id,
            date
        ))
        
        # Update analytics
        if completed:
            self._update_completion_analytics(date, cursor)
        
        conn.commit()
        self.close()
    
    def _update_completion_analytics(self, date: str, cursor):
        """Update completion analytics for a date"""
        # Calculate completion rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
            FROM tasks
            WHERE date = ?
        ''', (date,))
        
        row = cursor.fetchone()
        if row and row['total'] > 0:
            completion_rate = (row['completed'] / row['total']) * 100
            
            cursor.execute('''
                INSERT OR REPLACE INTO analytics (date, metric_type, metric_value)
                VALUES (?, 'completion_rate', ?)
            ''', (date, completion_rate))
    
    def get_daily_stats(self, date: str) -> Dict:
        """Get daily statistics"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get task stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_tasks,
                SUM(duration) as total_minutes,
                SUM(CASE WHEN completed = 1 THEN duration ELSE 0 END) as completed_minutes
            FROM tasks
            WHERE date = ?
        ''', (date,))
        
        task_stats = dict(cursor.fetchone())
        
        # Calculate completion rate
        if task_stats['total_tasks'] > 0:
            task_stats['completion_rate'] = (task_stats['completed_tasks'] / task_stats['total_tasks']) * 100
        else:
            task_stats['completion_rate'] = 0
        
        # Get priority breakdown
        cursor.execute('''
            SELECT 
                priority,
                COUNT(*) as count,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
            FROM tasks
            WHERE date = ?
            GROUP BY priority
        ''', (date,))
        
        priority_breakdown = []
        for row in cursor.fetchall():
            priority_breakdown.append(dict(row))
        
        self.close()
        
        return {
            'date': date,
            'task_stats': task_stats,
            'priority_breakdown': priority_breakdown
        }
    
    def get_weekly_stats(self, start_date: str, end_date: str) -> Dict:
        """Get weekly statistics"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get daily completion rates
        cursor.execute('''
            SELECT 
                date,
                COUNT(*) as total_tasks,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_tasks
            FROM tasks
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        ''', (start_date, end_date))
        
        daily_stats = []
        total_completed = 0
        total_tasks = 0
        
        for row in cursor.fetchall():
            stats = dict(row)
            stats['completion_rate'] = (stats['completed_tasks'] / stats['total_tasks'] * 100) if stats['total_tasks'] > 0 else 0
            daily_stats.append(stats)
            total_completed += stats['completed_tasks']
            total_tasks += stats['total_tasks']
        
        # Get streak information
        streak = self._calculate_streak(cursor, end_date)
        
        # Get most productive day
        cursor.execute('''
            SELECT 
                date,
                SUM(CASE WHEN completed = 1 THEN duration ELSE 0 END) as productive_minutes
            FROM tasks
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY productive_minutes DESC
            LIMIT 1
        ''', (start_date, end_date))
        
        most_productive = cursor.fetchone()
        
        self.close()
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'daily_stats': daily_stats,
            'overall_completion_rate': (total_completed / total_tasks * 100) if total_tasks > 0 else 0,
            'total_tasks': total_tasks,
            'completed_tasks': total_completed,
            'current_streak': streak,
            'most_productive_day': dict(most_productive) if most_productive else None
        }
    
    def _calculate_streak(self, cursor, end_date: str) -> int:
        """Calculate current completion streak"""
        cursor.execute('''
            SELECT DISTINCT date
            FROM tasks
            WHERE date <= ?
            ORDER BY date DESC
        ''', (end_date,))
        
        dates = [row['date'] for row in cursor.fetchall()]
        
        if not dates:
            return 0
        
        streak = 0
        last_date = datetime.strptime(dates[0], '%Y-%m-%d')
        
        for date_str in dates:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Check if this date has >80% completion
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
                FROM tasks
                WHERE date = ?
            ''', (date_str,))
            
            row = cursor.fetchone()
            if row['total'] > 0 and (row['completed'] / row['total']) >= 0.8:
                if (last_date - date).days <= 1:
                    streak += 1
                    last_date = date
                else:
                    break
            else:
                break
        
        return streak
    
    def get_preferences(self) -> Dict:
        """Get all user preferences"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT key, value FROM preferences')
        
        prefs = {}
        for row in cursor.fetchall():
            try:
                prefs[row['key']] = json.loads(row['value'])
            except:
                prefs[row['key']] = row['value']
        
        self.close()
        
        # Return defaults if no preferences
        return prefs or {
            'work_start_hour': 8,
            'work_end_hour': 20,
            'lunch_duration': 60,
            'break_duration': 15,
            'theme': 'light',
            'notifications_enabled': True
        }
    
    def save_preferences(self, preferences: Dict):
        """Save user preferences"""
        conn = self.connect()
        cursor = conn.cursor()
        
        for key, value in preferences.items():
            value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            cursor.execute('''
                INSERT OR REPLACE INTO preferences (key, value)
                VALUES (?, ?)
            ''', (key, value_str))
        
        conn.commit()
        self.close()
    
    def get_date_range_stats(self, start_date: str, end_date: str) -> List[Dict]:
        """Get statistics for a date range (for PDF reports)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                t.date,
                t.name,
                t.duration,
                t.priority,
                t.completed,
                t.completed_at,
                s.schedule_data
            FROM tasks t
            LEFT JOIN schedules s ON t.date = s.date
            WHERE t.date BETWEEN ? AND ?
            ORDER BY t.date, t.created_at
        ''', (start_date, end_date))
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(row))
        
        self.close()
        return results 