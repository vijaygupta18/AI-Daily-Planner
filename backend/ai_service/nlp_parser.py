import spacy
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Tuple
import dateutil.parser
from dateutil.relativedelta import relativedelta

class NLPTaskParser:
    """Natural Language Parser for extracting task information from user input"""
    
    def __init__(self):
        # Load spaCy model (download with: python -m spacy download en_core_web_sm)
        self.nlp = spacy.load("en_core_web_sm")
        
        # Time patterns
        self.duration_patterns = {
            r'(\d+)\s*(?:hours?|hrs?)': lambda x: int(x) * 60,
            r'(\d+)\s*(?:minutes?|mins?)': lambda x: int(x),
            r'(\d+)\s*h(?:ours?)?\s*(\d+)\s*m(?:ins?)?': lambda h, m: int(h) * 60 + int(m),
            r'(\d+):(\d+)': lambda h, m: int(h) * 60 + int(m),
        }
        
        # Priority keywords
        self.priority_keywords = {
            5: ['urgent', 'critical', 'asap', 'immediately', 'emergency'],
            4: ['important', 'high priority', 'soon'],
            3: ['normal', 'regular', 'medium'],
            2: ['low priority', 'when possible', 'eventually'],
            1: ['someday', 'maybe', 'optional']
        }
        
        # Time preference keywords
        self.time_preferences = {
            'morning': ['morning', 'am', 'early', 'before noon'],
            'afternoon': ['afternoon', 'pm', 'after lunch', 'midday'],
            'evening': ['evening', 'night', 'late', 'after work']
        }
        
        # Common task categories (for auto-detection of breaks)
        self.break_keywords = ['lunch', 'break', 'rest', 'meal', 'eat', 'coffee', 'tea']
        
    def parse_task(self, input_text: str) -> Dict:
        """Parse natural language input into structured task data"""
        doc = self.nlp(input_text.lower())
        
        task_info = {
            'name': self._extract_task_name(input_text, doc),
            'duration': self._extract_duration(input_text, doc),
            'priority': self._extract_priority(doc),
            'deadline': self._extract_deadline(input_text, doc),
            'preferred_time': self._extract_time_preference(doc),
            'is_break': self._detect_break(doc),
            'raw_input': input_text
        }
        
        return task_info
    
    def _extract_task_name(self, original_text: str, doc) -> str:
        """Extract the main task description"""
        # Remove time-related phrases to get clean task name
        task_name = original_text
        
        # Remove duration mentions
        duration_removals = [
            r'for\s+\d+\s*(?:hours?|hrs?|minutes?|mins?)',
            r'\d+\s*(?:hours?|hrs?|minutes?|mins?)',
            r'\d+:\d+',
        ]
        
        for pattern in duration_removals:
            task_name = re.sub(pattern, '', task_name, flags=re.IGNORECASE)
        
        # Remove deadline mentions
        deadline_removals = [
            r'by\s+(?:tomorrow|today|tonight|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'before\s+\d+(?::\d+)?(?:\s*(?:am|pm))?',
            r'until\s+\d+(?::\d+)?(?:\s*(?:am|pm))?',
            r'(?:tomorrow|today|tonight)',
        ]
        
        for pattern in deadline_removals:
            task_name = re.sub(pattern, '', task_name, flags=re.IGNORECASE)
        
        # Remove priority mentions
        priority_removals = ['urgent', 'asap', 'important', 'high priority', 'low priority']
        for word in priority_removals:
            task_name = task_name.replace(word, '')
        
        # Clean up extra spaces
        task_name = ' '.join(task_name.split())
        
        # If task name is too short or empty, use verb + object from original
        if len(task_name.strip()) < 3:
            # Find main verb and its object
            for token in doc:
                if token.pos_ == "VERB":
                    verb_phrase = token.text
                    for child in token.children:
                        if child.dep_ in ["dobj", "prep"]:
                            verb_phrase += " " + child.text
                            for grandchild in child.children:
                                verb_phrase += " " + grandchild.text
                    return verb_phrase.strip()
            
            # Fallback to original without time markers
            return original_text[:50]  # Limit length
        
        return task_name.strip()
    
    def _extract_duration(self, text: str, doc) -> int:
        """Extract task duration in minutes"""
        # Check each duration pattern
        for pattern, converter in self.duration_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 1:
                        return converter(match.group(1))
                    else:
                        return converter(*match.groups())
                except:
                    continue
        
        # Default durations based on task type
        task_lower = text.lower()
        if any(word in task_lower for word in ['meeting', 'call']):
            return 60  # 1 hour for meetings
        elif any(word in task_lower for word in ['review', 'read']):
            return 30  # 30 mins for reviews
        elif any(word in task_lower for word in ['quick', 'brief']):
            return 15  # 15 mins for quick tasks
        else:
            return 45  # Default 45 minutes
    
    def _extract_priority(self, doc) -> int:
        """Extract priority level from text"""
        text_lower = doc.text.lower()
        
        for priority, keywords in self.priority_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return priority
        
        # Default priority
        return 3
    
    def _extract_deadline(self, text: str, doc) -> Optional[datetime]:
        """Extract deadline from text"""
        now = datetime.now()
        text_lower = text.lower()
        
        # Relative dates
        if 'tomorrow' in text_lower:
            return now.replace(hour=23, minute=59) + timedelta(days=1)
        elif 'today' in text_lower or 'tonight' in text_lower:
            return now.replace(hour=23, minute=59)
        elif 'next week' in text_lower:
            return now.replace(hour=23, minute=59) + timedelta(weeks=1)
        
        # Day names
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(days):
            if day in text_lower:
                days_ahead = (i - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week
                return now + timedelta(days=days_ahead)
        
        # Try to parse with dateutil
        try:
            # Look for patterns like "by 5pm", "before 3:30pm"
            time_match = re.search(r'(?:by|before|until)\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)', text_lower)
            if time_match:
                time_str = time_match.group(1)
                parsed_time = dateutil.parser.parse(time_str)
                # Combine with today's date
                deadline = now.replace(hour=parsed_time.hour, minute=parsed_time.minute)
                if deadline < now:
                    deadline += timedelta(days=1)  # Must be tomorrow
                return deadline
        except:
            pass
        
        # Look for date entities using spaCy
        for ent in doc.ents:
            if ent.label_ in ["DATE", "TIME"]:
                try:
                    parsed = dateutil.parser.parse(ent.text, fuzzy=True)
                    if parsed.date() < now.date():
                        # Assume next year if date has passed
                        parsed = parsed.replace(year=parsed.year + 1)
                    return parsed
                except:
                    continue
        
        return None
    
    def _extract_time_preference(self, doc) -> Optional[str]:
        """Extract preferred time of day for the task"""
        text_lower = doc.text.lower()
        
        for preference, keywords in self.time_preferences.items():
            if any(keyword in text_lower for keyword in keywords):
                return preference
        
        # Infer from time mentions
        time_match = re.search(r'(\d{1,2})(?::\d{2})?\s*([ap]m)', text_lower)
        if time_match:
            hour = int(time_match.group(1))
            period = time_match.group(2)
            
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            
            if hour < 12:
                return 'morning'
            elif hour < 17:
                return 'afternoon'
            else:
                return 'evening'
        
        return None
    
    def _detect_break(self, doc) -> bool:
        """Detect if the task is actually a break/meal"""
        text_lower = doc.text.lower()
        return any(keyword in text_lower for keyword in self.break_keywords)
    
    def parse_multiple_tasks(self, input_text: str) -> List[Dict]:
        """Parse multiple tasks from a single input (separated by commas or 'and')"""
        # Split by common separators
        task_texts = re.split(r'[,;]|\sand\s', input_text)
        
        tasks = []
        for task_text in task_texts:
            task_text = task_text.strip()
            if task_text:
                task_info = self.parse_task(task_text)
                tasks.append(task_info)
        
        return tasks
    
    def extract_context_from_schedule(self, schedule_text: str) -> Dict:
        """Extract context about user's schedule preferences from a longer description"""
        doc = self.nlp(schedule_text.lower())
        
        context = {
            'work_start': None,
            'work_end': None,
            'lunch_time': None,
            'break_frequency': None,
            'preferred_task_order': []
        }
        
        # Extract work hours
        work_pattern = r'work(?:ing)?\s+(?:from\s+)?(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)\s+to\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)'
        work_match = re.search(work_pattern, schedule_text, re.IGNORECASE)
        if work_match:
            try:
                context['work_start'] = dateutil.parser.parse(work_match.group(1)).time()
                context['work_end'] = dateutil.parser.parse(work_match.group(2)).time()
            except:
                pass
        
        # Extract lunch preferences
        lunch_pattern = r'lunch\s+(?:at\s+)?(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)'
        lunch_match = re.search(lunch_pattern, schedule_text, re.IGNORECASE)
        if lunch_match:
            try:
                context['lunch_time'] = dateutil.parser.parse(lunch_match.group(1)).time()
            except:
                pass
        
        # Extract break preferences
        if 'break every hour' in schedule_text.lower():
            context['break_frequency'] = 60
        elif 'break every 2 hours' in schedule_text.lower():
            context['break_frequency'] = 120
        
        return context 