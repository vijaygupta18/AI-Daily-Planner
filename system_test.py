#!/usr/bin/env python3
"""
Comprehensive System Test for AI Daily Planner
Tests the complete workflow from task parsing to schedule optimization
"""

import requests
import json
from datetime import datetime, timedelta

def test_system():
    """Test the complete system workflow"""
    base_url = "http://localhost:5001/api"
    
    print("🚀 Starting AI Daily Planner System Test")
    print("=" * 50)
    
    # Test 1: Parse multiple natural language tasks
    print("\n📝 Test 1: Natural Language Task Parsing")
    test_inputs = [
        "Study machine learning for 2 hours in the morning, high priority",
        "Team meeting at 3pm for 45 minutes urgent",
        "Quick email check 15 minutes low priority",
        "Lunch break 1 hour at noon",
        "Code review session 90 minutes afternoon",
        "Workout 30 minutes evening"
    ]
    
    all_tasks = []
    for i, task_text in enumerate(test_inputs, 1):
        try:
            response = requests.post(
                f"{base_url}/parse-task",
                json={"text": task_text},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    tasks = result["tasks"]
                    all_tasks.extend(tasks)
                    print(f"  ✅ Task {i}: '{task_text[:30]}...'")
                    for task in tasks:
                        print(f"     → {task['name']} ({task['duration']}min, priority: {task['priority']})")
                else:
                    print(f"  ❌ Task {i}: Failed to parse - {result.get('error', 'Unknown error')}")
            else:
                print(f"  ❌ Task {i}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Task {i}: Exception - {str(e)}")
    
    print(f"\n📊 Parsed {len(all_tasks)} tasks total")
    
    # Test 2: Schedule Optimization
    print("\n🧠 Test 2: AI Schedule Optimization")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    try:
        response = requests.post(
            f"{base_url}/schedule/optimize",
            json={
                "date": tomorrow,
                "tasks": all_tasks,
                "preferences": {
                    "work_start": "08:00",
                    "work_end": "18:00",
                    "lunch_duration": 60,
                    "break_duration": 15
                }
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                schedule = result["schedule"]
                print(f"  ✅ Schedule optimized successfully!")
                print(f"  📈 Scheduled {result['scheduled_tasks']}/{result['total_tasks']} tasks")
                print(f"  📅 Generated {len(schedule)} time slots")
                
                # Display the schedule
                print("\n🗓️  Optimized Schedule:")
                print("   " + "-" * 45)
                for slot in schedule:
                    start = slot['start_time'].split('T')[1][:5]  # Extract HH:MM
                    end = slot['end_time'].split('T')[1][:5]
                    
                    if slot.get('is_break', False):
                        print(f"   ☕ {start}-{end} | Break")
                    else:
                        task = slot['task']
                        priority_emoji = "🔥" if task['priority'] >= 4 else "⭐" if task['priority'] >= 3 else "📝"
                        print(f"   {priority_emoji} {start}-{end} | {task['name']} (P{task['priority']})")
                
                # Calculate efficiency metrics
                total_task_time = sum(slot.get('task', {}).get('duration', 0) for slot in schedule if not slot.get('is_break', False))
                work_hours = 10 * 60  # 8 AM to 6 PM = 10 hours
                efficiency = (total_task_time / work_hours) * 100
                
                print(f"\n📊 Schedule Metrics:")
                print(f"   • Total productive time: {total_task_time} minutes")
                print(f"   • Work day efficiency: {efficiency:.1f}%")
                print(f"   • Tasks scheduled: {result['scheduled_tasks']}/{result['total_tasks']}")
                
            else:
                print(f"  ❌ Schedule optimization failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"  ❌ HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"  ❌ Exception during optimization: {str(e)}")
    
    # Test 3: System Performance
    print("\n⚡ Test 3: Performance Test")
    simple_tasks = [
        {"id": "perf1", "name": "Quick task 1", "duration": 30, "priority": 3},
        {"id": "perf2", "name": "Quick task 2", "duration": 45, "priority": 2},
        {"id": "perf3", "name": "Quick task 3", "duration": 60, "priority": 4}
    ]
    
    start_time = datetime.now()
    try:
        response = requests.post(
            f"{base_url}/schedule/optimize",
            json={"date": tomorrow, "tasks": simple_tasks},
            headers={"Content-Type": "application/json"}
        )
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds
        
        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print(f"  ✅ Performance test passed!")
                print(f"  ⚡ Response time: {response_time:.1f}ms")
                
                if response_time < 50:
                    print("  🎯 Excellent: Response time < 50ms target!")
                elif response_time < 100:
                    print("  ✅ Good: Response time < 100ms")
                else:
                    print("  ⚠️  Warning: Response time > 100ms")
            else:
                print(f"  ❌ Performance test failed: {result.get('error')}")
        else:
            print(f"  ❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Exception during performance test: {str(e)}")
    
    # Test 4: API Health Check
    print("\n🏥 Test 4: API Health Check")
    try:
        # Test root endpoint
        response = requests.get("http://localhost:5001/")
        if response.status_code == 200:
            print("  ✅ Root endpoint responding")
        else:
            print(f"  ❌ Root endpoint: HTTP {response.status_code}")
            
        # Test a few key endpoints
        endpoints = ["/parse-task", "/schedule/optimize"]
        for endpoint in endpoints:
            try:
                # Just test if endpoint exists (will return 405 for GET on POST endpoint)
                response = requests.get(f"{base_url}{endpoint}")
                if response.status_code in [200, 405, 400]:  # 405 = Method Not Allowed is expected
                    print(f"  ✅ Endpoint {endpoint} available")
                else:
                    print(f"  ❌ Endpoint {endpoint}: HTTP {response.status_code}")
            except:
                print(f"  ❌ Endpoint {endpoint}: Not reachable")
                
    except Exception as e:
        print(f"  ❌ Health check failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 System Test Complete!")
    print("\n💡 To use the app:")
    print("   1. Open browser to: http://localhost:5001")
    print("   2. Type natural language tasks like:")
    print("      'Study Python for 2 hours tomorrow morning'")
    print("   3. Click 'Parse & Add' then 'Optimize Schedule'")
    print("   4. View your AI-optimized daily schedule!")

if __name__ == "__main__":
    test_system() 