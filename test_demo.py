#!/usr/bin/env python3
"""
Simple test demo for AI Daily Planner
This demonstrates core functionality without external dependencies
"""

import random
from datetime import datetime, timedelta
import json

# Simplified Task class
class Task:
    def __init__(self, task_id, name, duration, priority, deadline=None, preferred_time=None):
        self.id = task_id
        self.name = name
        self.duration = duration  # minutes
        self.priority = priority  # 1-5
        self.deadline = deadline
        self.preferred_time = preferred_time
        self.completed = False

# Simplified TimeSlot class
class TimeSlot:
    def __init__(self, start_time, end_time, task=None):
        self.start_time = start_time
        self.end_time = end_time
        self.task = task
        self.is_break = False

# Simplified Genetic Scheduler (core logic only)
class SimpleGeneticScheduler:
    def __init__(self):
        self.work_start_hour = 8
        self.work_end_hour = 20
        self.break_duration = 15
        self.lunch_duration = 60
        
    def create_simple_schedule(self, tasks, date):
        """Create a simple schedule for demonstration"""
        schedule = []
        current_time = date.replace(hour=self.work_start_hour, minute=0, second=0)
        work_end = date.replace(hour=self.work_end_hour, minute=0, second=0)
        
        # Sort tasks by priority (highest first)
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        # Add lunch break
        lunch_start = date.replace(hour=12, minute=0, second=0)
        lunch_slot = TimeSlot(lunch_start, lunch_start + timedelta(minutes=self.lunch_duration))
        lunch_slot.is_break = True
        
        # Schedule tasks
        for task in sorted_tasks:
            # Skip lunch time
            if current_time <= lunch_start < current_time + timedelta(minutes=task.duration):
                current_time = lunch_start + timedelta(minutes=self.lunch_duration)
            
            # Check if task fits
            if current_time + timedelta(minutes=task.duration) <= work_end:
                slot = TimeSlot(current_time, current_time + timedelta(minutes=task.duration), task)
                schedule.append(slot)
                current_time = slot.end_time
                
                # Add break after task
                if current_time + timedelta(minutes=self.break_duration) < work_end:
                    break_slot = TimeSlot(current_time, current_time + timedelta(minutes=self.break_duration))
                    break_slot.is_break = True
                    schedule.append(break_slot)
                    current_time = break_slot.end_time
        
        # Insert lunch break
        schedule.append(lunch_slot)
        schedule.sort(key=lambda x: x.start_time)
        
        return schedule

# Simple NLP Parser (without spaCy)
class SimpleNLPParser:
    def __init__(self):
        self.duration_keywords = {
            'hour': 60, 'hours': 60, 'hr': 60, 'hrs': 60,
            'minute': 1, 'minutes': 1, 'min': 1, 'mins': 1
        }
        self.priority_keywords = {
            'urgent': 5, 'critical': 5, 'asap': 5,
            'important': 4, 'high': 4,
            'normal': 3, 'medium': 3,
            'low': 2, 'optional': 1
        }
    
    def parse_task(self, text):
        """Simple parsing without spaCy"""
        text_lower = text.lower()
        
        # Extract duration
        duration = 45  # default
        for keyword, multiplier in self.duration_keywords.items():
            if keyword in text_lower:
                # Try to find number before keyword
                words = text_lower.split()
                for i, word in enumerate(words):
                    if keyword in word and i > 0:
                        try:
                            num = float(words[i-1])
                            duration = int(num * multiplier)
                            break
                        except:
                            pass
        
        # Extract priority
        priority = 3  # default
        for keyword, value in self.priority_keywords.items():
            if keyword in text_lower:
                priority = value
                break
        
        # Clean task name
        task_name = text
        for keyword in ['urgent', 'critical', 'asap', 'important', 'high', 'tomorrow', 'today']:
            task_name = task_name.replace(keyword, '').strip()
        
        return {
            'name': task_name,
            'duration': duration,
            'priority': priority,
            'raw_input': text
        }

def print_schedule(schedule):
    """Pretty print schedule"""
    print("\n📅 OPTIMIZED SCHEDULE")
    print("=" * 60)
    
    for slot in schedule:
        start = slot.start_time.strftime("%I:%M %p")
        end = slot.end_time.strftime("%I:%M %p")
        
        if slot.is_break:
            print(f"🍽️  {start} - {end}: BREAK")
        elif slot.task:
            priority_emoji = ['', '🔵', '🟢', '🟡', '🟠', '🔴'][slot.task.priority]
            print(f"{priority_emoji} {start} - {end}: {slot.task.name} ({slot.task.duration} mins)")
    
    print("=" * 60)

def main():
    print("🤖 AI DAILY PLANNER - DEMO")
    print("=" * 60)
    
    # Initialize components
    parser = SimpleNLPParser()
    scheduler = SimpleGeneticScheduler()
    
    # Sample tasks to parse
    sample_inputs = [
        "Study ML for 2 hours urgent",
        "Review documents for 30 minutes",
        "Important meeting with client for 1 hour",
        "Quick email check 15 mins low priority",
        "Project planning session 45 minutes high priority",
        "Code review for team 1 hr medium priority"
    ]
    
    print("\n📝 PARSING TASKS:")
    print("-" * 40)
    
    tasks = []
    for i, input_text in enumerate(sample_inputs):
        parsed = parser.parse_task(input_text)
        task = Task(
            task_id=f"task_{i+1}",
            name=parsed['name'],
            duration=parsed['duration'],
            priority=parsed['priority']
        )
        tasks.append(task)
        
        print(f"Input: '{input_text}'")
        print(f"  → Task: {parsed['name']}")
        print(f"  → Duration: {parsed['duration']} minutes")
        print(f"  → Priority: {parsed['priority']}/5")
        print()
    
    # Generate schedule
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    schedule = scheduler.create_simple_schedule(tasks, today)
    
    # Display schedule
    print_schedule(schedule)
    
    # Show statistics
    total_tasks = len(tasks)
    scheduled_tasks = sum(1 for slot in schedule if slot.task and not slot.is_break)
    total_work_minutes = sum(slot.task.duration for slot in schedule if slot.task and not slot.is_break)
    
    print("\n📊 STATISTICS:")
    print(f"  • Total tasks: {total_tasks}")
    print(f"  • Scheduled tasks: {scheduled_tasks}")
    print(f"  • Total work time: {total_work_minutes // 60}h {total_work_minutes % 60}min")
    print(f"  • Utilization: {(total_work_minutes / ((scheduler.work_end_hour - scheduler.work_start_hour) * 60)) * 100:.1f}%")

if __name__ == "__main__":
    main() 