from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime, timedelta
import uuid
from typing import Dict, List

# Import our modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_service.genetic_scheduler import GeneticScheduler, Task
from ai_service.nlp_parser import NLPTaskParser
from utils.calendar_sync import GoogleCalendarSync
from models.database import Database
from utils.report_generator import ReportGenerator

app = Flask(__name__)
CORS(app)

# Initialize components
db = Database('planner.db')
scheduler = GeneticScheduler()
parser = NLPTaskParser()
calendar_sync = GoogleCalendarSync()
report_gen = ReportGenerator()

# Ensure database is initialized
db.init_db()

def _parse_deadline(deadline_str):
    """Parse deadline string from various formats"""
    if not deadline_str:
        return None
    
    try:
        # Try ISO format first
        return datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Try GMT format
            return datetime.strptime(deadline_str, '%a, %d %b %Y %H:%M:%S %Z')
        except ValueError:
            try:
                # Try simple ISO format
                return datetime.fromisoformat(deadline_str)
            except ValueError:
                # Return None if all parsing fails
                return None

@app.route('/')
def index():
    """Serve the main HTML file"""
    return send_from_directory('../../frontend', 'index.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files"""
    return send_from_directory('../../frontend/css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files"""
    return send_from_directory('../../frontend/js', filename)

@app.route('/favicon.ico')
def serve_favicon():
    """Serve favicon"""
    return send_from_directory('../../frontend', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/api/parse-task', methods=['POST'])
def parse_task():
    """Parse natural language task input"""
    try:
        data = request.json
        input_text = data.get('text', '')
        
        # Parse single or multiple tasks
        if ',' in input_text or ' and ' in input_text.lower():
            tasks = parser.parse_multiple_tasks(input_text)
        else:
            tasks = [parser.parse_task(input_text)]
        
        # Add unique IDs
        for task in tasks:
            task['id'] = str(uuid.uuid4())
        
        return jsonify({
            'success': True,
            'tasks': tasks
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/schedule/optimize', methods=['POST'])
def optimize_schedule():
    """Generate optimized schedule using genetic algorithm"""
    try:
        data = request.json
        tasks_data = data.get('tasks', [])
        date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        preferences = data.get('preferences', {})
        
        # Convert to Task objects
        tasks = []
        for task_data in tasks_data:
            task = Task(
                task_id=task_data.get('id', str(uuid.uuid4())),
                name=task_data['name'],
                duration=task_data['duration'],
                priority=task_data.get('priority', 3),
                deadline=_parse_deadline(task_data.get('deadline')) if task_data.get('deadline') else None,
                preferred_time=task_data.get('preferred_time')
            )
            tasks.append(task)
        
        # Apply user preferences to scheduler
        if preferences:
            scheduler.work_start_hour = preferences.get('work_start_hour', 8)
            scheduler.work_end_hour = preferences.get('work_end_hour', 20)
            scheduler.lunch_duration = preferences.get('lunch_duration', 60)
            scheduler.break_duration = preferences.get('break_duration', 15)
        
        # Optimize schedule
        schedule_date = datetime.strptime(date_str, '%Y-%m-%d')
        optimized = scheduler.optimize_schedule(tasks, schedule_date)
        
        # Convert to JSON-serializable format
        schedule_data = []
        for slot in optimized:
            slot_data = {
                'start_time': slot.start_time.isoformat(),
                'end_time': slot.end_time.isoformat(),
                'is_break': slot.is_break
            }
            
            if slot.task:
                slot_data['task'] = {
                    'id': slot.task.id,
                    'name': slot.task.name,
                    'duration': slot.task.duration,
                    'priority': slot.task.priority,
                    'completed': slot.task.completed
                }
            
            schedule_data.append(slot_data)
        
        # Save to database
        db.save_schedule(date_str, schedule_data)
        
        return jsonify({
            'success': True,
            'schedule': schedule_data,
            'total_tasks': len(tasks),
            'scheduled_tasks': len([s for s in schedule_data if s.get('task') and not s['is_break']])
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/schedule/reschedule', methods=['POST'])
def reschedule_tasks():
    """Reschedule unfinished tasks with new tasks"""
    try:
        data = request.json
        current_date = data.get('current_date')
        new_date = data.get('new_date', datetime.now().strftime('%Y-%m-%d'))
        new_tasks_data = data.get('new_tasks', [])
        
        # Get current schedule from database
        current_schedule_data = db.get_schedule(current_date)
        if not current_schedule_data:
            return jsonify({
                'success': False,
                'error': 'No schedule found for current date'
            }), 404
        
        # Convert to TimeSlot objects
        current_slots = []
        for slot_data in current_schedule_data:
            # Implementation details...
            pass
        
        # Convert new tasks
        new_tasks = []
        for task_data in new_tasks_data:
            task = Task(
                task_id=task_data.get('id', str(uuid.uuid4())),
                name=task_data['name'],
                duration=task_data['duration'],
                priority=task_data.get('priority', 3)
            )
            new_tasks.append(task)
        
        # Reschedule
        rescheduled = scheduler.reschedule_unfinished_tasks(
            current_slots,
            new_tasks,
            datetime.strptime(new_date, '%Y-%m-%d')
        )
        
        # Convert and save
        # ... (similar to optimize_schedule)
        
        return jsonify({
            'success': True,
            'schedule': []  # Converted schedule data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/tasks/complete', methods=['POST'])
def complete_task():
    """Mark a task as completed"""
    try:
        data = request.json
        task_id = data.get('task_id')
        date = data.get('date')
        completed = data.get('completed', True)
        
        # Update in database
        db.update_task_status(date, task_id, completed)
        
        # Update in Google Calendar if synced
        if 'calendar_event_id' in data:
            calendar_sync.update_event_completion(
                data['calendar_event_id'],
                completed
            )
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'completed': completed
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/calendar/auth', methods=['GET'])
def calendar_auth():
    """Initiate Google Calendar authentication"""
    try:
        # This would typically redirect to OAuth flow
        success = calendar_sync.authenticate()
        
        return jsonify({
            'success': success,
            'message': 'Authentication successful' if success else 'Authentication failed'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/calendar/sync', methods=['POST'])
def sync_to_calendar():
    """Sync schedule to Google Calendar"""
    try:
        data = request.json
        date = data.get('date')
        calendar_id = data.get('calendar_id', 'primary')
        clear_existing = data.get('clear_existing', False)
        
        # Get schedule from database
        schedule_data = db.get_schedule(date)
        if not schedule_data:
            return jsonify({
                'success': False,
                'error': 'No schedule found for date'
            }), 404
        
        # Convert to TimeSlot objects for sync
        # ... (conversion logic)
        
        # Sync to calendar
        sync_map = calendar_sync.sync_schedule_to_calendar(
            [],  # Converted slots
            calendar_id,
            clear_existing
        )
        
        return jsonify({
            'success': True,
            'synced_count': len(sync_map),
            'sync_map': sync_map
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/reports/daily', methods=['GET'])
def get_daily_report():
    """Get daily completion metrics"""
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        report = db.get_daily_stats(date)
        
        return jsonify({
            'success': True,
            'report': report
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/reports/weekly', methods=['GET'])
def get_weekly_report():
    """Get weekly performance report"""
    try:
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Calculate start date (7 days ago)
        end = datetime.strptime(end_date, '%Y-%m-%d')
        start = end - timedelta(days=6)
        
        report = db.get_weekly_stats(
            start.strftime('%Y-%m-%d'),
            end.strftime('%Y-%m-%d')
        )
        
        return jsonify({
            'success': True,
            'report': report
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/reports/pdf', methods=['POST'])
def generate_pdf_report():
    """Generate PDF report for a date range"""
    try:
        data = request.json
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # Get data from database
        stats = db.get_date_range_stats(start_date, end_date)
        
        # Generate PDF
        pdf_path = report_gen.generate_weekly_report(stats, start_date, end_date)
        
        return jsonify({
            'success': True,
            'pdf_path': pdf_path
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/preferences', methods=['GET', 'POST'])
def handle_preferences():
    """Get or update user preferences"""
    try:
        if request.method == 'GET':
            prefs = db.get_preferences()
            return jsonify({
                'success': True,
                'preferences': prefs
            })
        
        else:  # POST
            data = request.json
            db.save_preferences(data)
            
            return jsonify({
                'success': True,
                'preferences': data
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0') 