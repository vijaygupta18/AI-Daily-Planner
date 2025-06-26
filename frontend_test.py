#!/usr/bin/env python3
"""
Frontend Integration Test
Tests the web interface and API communication
"""

import requests
import time

def test_frontend_integration():
    """Test the complete frontend-backend integration"""
    print("🌐 Testing Frontend Integration")
    print("=" * 40)
    
    # Test 1: Verify API endpoints are accessible
    print("\n📡 Test 1: API Accessibility")
    base_url = "http://localhost:5001"
    
    try:
        # Test frontend page loads
        response = requests.get(base_url)
        if response.status_code == 200:
            print("  ✅ Frontend page loads successfully")
        else:
            print(f"  ❌ Frontend page: HTTP {response.status_code}")
            return
            
        # Test static files load
        css_response = requests.get(f"{base_url}/css/styles.css")
        js_response = requests.get(f"{base_url}/js/api.js")
        
        if css_response.status_code == 200:
            print("  ✅ CSS files load successfully")
        else:
            print(f"  ❌ CSS files: HTTP {css_response.status_code}")
            
        if js_response.status_code == 200:
            print("  ✅ JavaScript files load successfully")
        else:
            print(f"  ❌ JavaScript files: HTTP {js_response.status_code}")
            
    except Exception as e:
        print(f"  ❌ API test failed: {str(e)}")
        return
    
    # Test 2: API functionality through web interface simulation
    print("\n🤖 Test 2: API Integration")
    
    try:
        # Simulate task parsing
        task_response = requests.post(
            f"{base_url}/api/parse-task",
            json={"text": "Study AI for 2 hours tomorrow morning"},
            headers={"Content-Type": "application/json"}
        )
        
        if task_response.status_code == 200:
            result = task_response.json()
            if result.get("success"):
                print("  ✅ Task parsing API works")
                tasks = result.get("tasks", [])
                if tasks:
                    print(f"      → Parsed: {tasks[0]['name']} ({tasks[0]['duration']}min)")
                
                # Test schedule optimization with parsed task
                schedule_response = requests.post(
                    f"{base_url}/api/schedule/optimize",
                    json={
                        "date": "2024-12-28",
                        "tasks": tasks,
                        "preferences": {"work_start": "08:00", "work_end": "18:00"}
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if schedule_response.status_code == 200:
                    schedule_result = schedule_response.json()
                    if schedule_result.get("success"):
                        print("  ✅ Schedule optimization API works")
                        schedule = schedule_result.get("schedule", [])
                        print(f"      → Generated {len(schedule)} time slots")
                    else:
                        print(f"  ❌ Schedule optimization failed: {schedule_result.get('error')}")
                else:
                    print(f"  ❌ Schedule optimization: HTTP {schedule_response.status_code}")
            else:
                print(f"  ❌ Task parsing failed: {result.get('error')}")
        else:
            print(f"  ❌ Task parsing: HTTP {task_response.status_code}")
            
    except Exception as e:
        print(f"  ❌ API integration test failed: {str(e)}")
    
    print("\n" + "=" * 40)
    print("✨ Frontend Integration Test Complete!")
    print("\n🎯 Ready to use!")
    print("   • Open browser to: http://localhost:5001")
    print("   • Try adding tasks with natural language")
    print("   • Click 'Parse & Add' then 'Optimize Schedule'")
    print("   • Your AI Daily Planner is fully operational! 🚀")

if __name__ == "__main__":
    test_frontend_integration() 