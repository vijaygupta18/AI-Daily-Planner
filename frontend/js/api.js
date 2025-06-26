// API Client for Backend Communication
class API {
    constructor() {
        this.baseURL = 'http://localhost:5000/api';
        this.headers = {
            'Content-Type': 'application/json'
        };
    }

    async request(endpoint, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: this.headers,
            mode: 'cors'
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, options);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Request failed');
            }
            
            return result;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Task-related endpoints
    async parseTask(text) {
        return this.request('/parse-task', 'POST', { text });
    }

    async completeTask(taskId, date, completed) {
        return this.request('/tasks/complete', 'POST', {
            task_id: taskId,
            date: date,
            completed: completed
        });
    }

    // Schedule-related endpoints
    async optimizeSchedule(tasks, date, preferences) {
        return this.request('/schedule/optimize', 'POST', {
            tasks: tasks,
            date: date,
            preferences: preferences
        });
    }

    async rescheduleUnfinished(currentDate, newDate, newTasks) {
        return this.request('/schedule/reschedule', 'POST', {
            current_date: currentDate,
            new_date: newDate,
            new_tasks: newTasks
        });
    }

    // Analytics endpoints
    async getDailyReport(date) {
        return this.request(`/reports/daily?date=${date}`);
    }

    async getWeeklyReport(endDate) {
        return this.request(`/reports/weekly?end_date=${endDate}`);
    }

    async generatePDFReport(startDate, endDate) {
        return this.request('/reports/pdf', 'POST', {
            start_date: startDate,
            end_date: endDate
        });
    }

    // Preferences endpoints
    async getPreferences() {
        return this.request('/preferences');
    }

    async updatePreferences(preferences) {
        return this.request('/preferences', 'POST', preferences);
    }

    // Calendar integration endpoints
    async authenticateCalendar() {
        return this.request('/calendar/auth');
    }

    async syncToCalendar(date, calendarId = 'primary', clearExisting = false) {
        return this.request('/calendar/sync', 'POST', {
            date: date,
            calendar_id: calendarId,
            clear_existing: clearExisting
        });
    }

    // Notion integration endpoints (placeholder)
    async connectNotion(apiKey) {
        return this.request('/notion/connect', 'POST', { api_key: apiKey });
    }

    async syncWithNotion(date) {
        return this.request('/notion/sync', 'POST', { date: date });
    }

    // Slack integration endpoints (placeholder)
    async connectSlack(webhookUrl) {
        return this.request('/slack/connect', 'POST', { webhook_url: webhookUrl });
    }

    async sendSlackNotification(message) {
        return this.request('/slack/notify', 'POST', { message: message });
    }
} 