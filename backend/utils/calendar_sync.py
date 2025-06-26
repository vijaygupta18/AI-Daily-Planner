import os
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pytz

class GoogleCalendarSync:
    """Handles synchronization with Google Calendar"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_file: str = 'credentials.json', 
                 token_file: str = 'token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.local_tz = pytz.timezone('UTC')  # Will be updated based on user location
        
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Token file stores the user's access and refresh tokens
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
        return True
    
    def get_calendars(self) -> List[Dict]:
        """Get list of calendars accessible to the user"""
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        calendars_result = self.service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        
        return [{
            'id': cal['id'],
            'summary': cal['summary'],
            'primary': cal.get('primary', False),
            'backgroundColor': cal.get('backgroundColor', '#1a73e8')
        } for cal in calendars]
    
    def sync_schedule_to_calendar(self, schedule_slots: List, calendar_id: str = 'primary',
                                 clear_existing: bool = False) -> Dict[str, str]:
        """Sync the optimized schedule to Google Calendar"""
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        # Map to store local_task_id -> google_event_id
        sync_map = {}
        
        # Get the date range for the schedule
        if not schedule_slots:
            return sync_map
            
        schedule_date = schedule_slots[0].start_time.date()
        start_datetime = datetime.combine(schedule_date, datetime.min.time())
        end_datetime = datetime.combine(schedule_date, datetime.max.time())
        
        # Clear existing events for the day if requested
        if clear_existing:
            self._clear_day_events(calendar_id, start_datetime, end_datetime)
        
        # Create events for each scheduled task
        for slot in schedule_slots:
            if slot.task and not slot.is_break:
                event = self._create_event_from_slot(slot)
                
                try:
                    created_event = self.service.events().insert(
                        calendarId=calendar_id,
                        body=event
                    ).execute()
                    
                    sync_map[slot.task.id] = created_event['id']
                    
                except Exception as e:
                    print(f"Error creating event for task {slot.task.name}: {str(e)}")
        
        return sync_map
    
    def _create_event_from_slot(self, slot) -> Dict:
        """Convert a TimeSlot to Google Calendar event format"""
        # Format datetime for Google Calendar
        start_time = slot.start_time.isoformat()
        end_time = slot.end_time.isoformat()
        
        event = {
            'summary': slot.task.name,
            'description': f"Priority: {slot.task.priority}/5\nAuto-scheduled by AI Planner",
            'start': {
                'dateTime': start_time,
                'timeZone': str(self.local_tz),
            },
            'end': {
                'dateTime': end_time,
                'timeZone': str(self.local_tz),
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        
        # Add color based on priority
        color_map = {
            5: '11',  # Red (highest priority)
            4: '5',   # Yellow
            3: '7',   # Blue
            2: '2',   # Green
            1: '8'    # Grey (lowest priority)
        }
        
        event['colorId'] = color_map.get(slot.task.priority, '7')
        
        return event
    
    def _clear_day_events(self, calendar_id: str, start_datetime: datetime, 
                         end_datetime: datetime):
        """Clear all events for a specific day"""
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=start_datetime.isoformat() + 'Z',
            timeMax=end_datetime.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        for event in events:
            # Only delete events created by this app (check description)
            if 'description' in event and 'Auto-scheduled by AI Planner' in event['description']:
                self.service.events().delete(
                    calendarId=calendar_id,
                    eventId=event['id']
                ).execute()
    
    def get_events_for_day(self, date: datetime, calendar_id: str = 'primary') -> List[Dict]:
        """Retrieve all events for a specific day"""
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        start_datetime = datetime.combine(date.date(), datetime.min.time())
        end_datetime = datetime.combine(date.date(), datetime.max.time())
        
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=start_datetime.isoformat() + 'Z',
            timeMax=end_datetime.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        return [{
            'id': event['id'],
            'summary': event.get('summary', 'No title'),
            'start': event['start'].get('dateTime', event['start'].get('date')),
            'end': event['end'].get('dateTime', event['end'].get('date')),
            'description': event.get('description', ''),
            'colorId': event.get('colorId', '7')
        } for event in events]
    
    def update_event_completion(self, event_id: str, completed: bool, 
                              calendar_id: str = 'primary'):
        """Update an event to mark it as completed"""
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            # Get the current event
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Update the summary to indicate completion
            if completed:
                if not event['summary'].startswith('✓ '):
                    event['summary'] = '✓ ' + event['summary']
            else:
                event['summary'] = event['summary'].replace('✓ ', '')
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            return updated_event
            
        except Exception as e:
            print(f"Error updating event {event_id}: {str(e)}")
            return None
    
    def import_calendar_events(self, date: datetime, calendar_id: str = 'primary') -> List[Dict]:
        """Import existing calendar events as tasks"""
        events = self.get_events_for_day(date, calendar_id)
        
        tasks = []
        for event in events:
            # Skip events created by this app
            if 'Auto-scheduled by AI Planner' in event.get('description', ''):
                continue
            
            # Parse event times
            start = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(event['end'].replace('Z', '+00:00'))
            duration = int((end - start).total_seconds() / 60)
            
            task = {
                'name': event['summary'],
                'duration': duration,
                'priority': 3,  # Default medium priority
                'calendar_event_id': event['id'],
                'start_time': start,
                'end_time': end
            }
            
            tasks.append(task)
        
        return tasks
    
    def batch_update_events(self, updates: List[Dict], calendar_id: str = 'primary'):
        """Batch update multiple events for efficiency"""
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        batch = self.service.new_batch_http_request()
        
        for update in updates:
            event_id = update['event_id']
            changes = update['changes']
            
            # Get current event and apply changes
            def update_callback(request_id, response, exception):
                if exception:
                    print(f"Error updating event {request_id}: {exception}")
            
            batch.add(
                self.service.events().patch(
                    calendarId=calendar_id,
                    eventId=event_id,
                    body=changes
                ),
                callback=update_callback
            )
        
        batch.execute() 