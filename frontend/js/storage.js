// IndexedDB Storage Handler for Local Persistence
class LocalStorage {
    constructor() {
        this.dbName = 'AISchedulerDB';
        this.version = 1;
        this.db = null;
    }

    // Initialize IndexedDB
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = () => {
                reject(new Error('Failed to open IndexedDB'));
            };

            request.onsuccess = (event) => {
                this.db = event.target.result;
                console.log('IndexedDB initialized successfully');
                resolve();
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Create object stores
                if (!db.objectStoreNames.contains('tasks')) {
                    const taskStore = db.createObjectStore('tasks', { keyPath: 'id' });
                    taskStore.createIndex('date', 'date', { unique: false });
                    taskStore.createIndex('completed', 'completed', { unique: false });
                }

                if (!db.objectStoreNames.contains('schedules')) {
                    const scheduleStore = db.createObjectStore('schedules', { keyPath: 'date' });
                }

                if (!db.objectStoreNames.contains('preferences')) {
                    db.createObjectStore('preferences', { keyPath: 'key' });
                }

                if (!db.objectStoreNames.contains('analytics')) {
                    const analyticsStore = db.createObjectStore('analytics', { keyPath: 'id', autoIncrement: true });
                    analyticsStore.createIndex('date', 'date', { unique: false });
                    analyticsStore.createIndex('type', 'type', { unique: false });
                }
            };
        });
    }

    // Task operations
    async saveTask(task) {
        const transaction = this.db.transaction(['tasks'], 'readwrite');
        const store = transaction.objectStore('tasks');
        
        return new Promise((resolve, reject) => {
            const request = store.put(task);
            request.onsuccess = () => resolve(task);
            request.onerror = () => reject(new Error('Failed to save task'));
        });
    }

    async getTasks(date) {
        const transaction = this.db.transaction(['tasks'], 'readonly');
        const store = transaction.objectStore('tasks');
        const index = store.index('date');
        
        return new Promise((resolve, reject) => {
            const request = index.getAll(date);
            request.onsuccess = (event) => resolve(event.target.result);
            request.onerror = () => reject(new Error('Failed to get tasks'));
        });
    }

    async deleteTask(taskId) {
        const transaction = this.db.transaction(['tasks'], 'readwrite');
        const store = transaction.objectStore('tasks');
        
        return new Promise((resolve, reject) => {
            const request = store.delete(taskId);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(new Error('Failed to delete task'));
        });
    }

    async updateTaskStatus(taskId, completed) {
        const transaction = this.db.transaction(['tasks'], 'readwrite');
        const store = transaction.objectStore('tasks');
        
        return new Promise((resolve, reject) => {
            const getRequest = store.get(taskId);
            
            getRequest.onsuccess = (event) => {
                const task = event.target.result;
                if (task) {
                    task.completed = completed;
                    task.completedAt = completed ? new Date().toISOString() : null;
                    
                    const updateRequest = store.put(task);
                    updateRequest.onsuccess = () => resolve(task);
                    updateRequest.onerror = () => reject(new Error('Failed to update task'));
                } else {
                    reject(new Error('Task not found'));
                }
            };
            
            getRequest.onerror = () => reject(new Error('Failed to get task'));
        });
    }

    // Schedule operations
    async saveSchedule(date, schedule) {
        const transaction = this.db.transaction(['schedules'], 'readwrite');
        const store = transaction.objectStore('schedules');
        
        const scheduleData = {
            date: date,
            schedule: schedule,
            updatedAt: new Date().toISOString()
        };
        
        return new Promise((resolve, reject) => {
            const request = store.put(scheduleData);
            request.onsuccess = () => resolve(scheduleData);
            request.onerror = () => reject(new Error('Failed to save schedule'));
        });
    }

    async getSchedule(date) {
        const transaction = this.db.transaction(['schedules'], 'readonly');
        const store = transaction.objectStore('schedules');
        
        return new Promise((resolve, reject) => {
            const request = store.get(date);
            request.onsuccess = (event) => {
                const result = event.target.result;
                resolve(result ? result.schedule : null);
            };
            request.onerror = () => reject(new Error('Failed to get schedule'));
        });
    }

    // Preferences operations
    async savePreference(key, value) {
        const transaction = this.db.transaction(['preferences'], 'readwrite');
        const store = transaction.objectStore('preferences');
        
        const preferenceData = {
            key: key,
            value: value,
            updatedAt: new Date().toISOString()
        };
        
        return new Promise((resolve, reject) => {
            const request = store.put(preferenceData);
            request.onsuccess = () => resolve(preferenceData);
            request.onerror = () => reject(new Error('Failed to save preference'));
        });
    }

    async getPreference(key) {
        const transaction = this.db.transaction(['preferences'], 'readonly');
        const store = transaction.objectStore('preferences');
        
        return new Promise((resolve, reject) => {
            const request = store.get(key);
            request.onsuccess = (event) => {
                const result = event.target.result;
                resolve(result ? result.value : null);
            };
            request.onerror = () => reject(new Error('Failed to get preference'));
        });
    }

    async getAllPreferences() {
        const transaction = this.db.transaction(['preferences'], 'readonly');
        const store = transaction.objectStore('preferences');
        
        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = (event) => {
                const results = event.target.result;
                const preferences = {};
                results.forEach(pref => {
                    preferences[pref.key] = pref.value;
                });
                resolve(preferences);
            };
            request.onerror = () => reject(new Error('Failed to get preferences'));
        });
    }

    // Analytics operations
    async saveAnalytics(type, data) {
        const transaction = this.db.transaction(['analytics'], 'readwrite');
        const store = transaction.objectStore('analytics');
        
        const analyticsData = {
            date: new Date().toISOString().split('T')[0],
            type: type,
            data: data,
            timestamp: new Date().toISOString()
        };
        
        return new Promise((resolve, reject) => {
            const request = store.add(analyticsData);
            request.onsuccess = () => resolve(analyticsData);
            request.onerror = () => reject(new Error('Failed to save analytics'));
        });
    }

    async getAnalytics(date, type = null) {
        const transaction = this.db.transaction(['analytics'], 'readonly');
        const store = transaction.objectStore('analytics');
        const index = store.index('date');
        
        return new Promise((resolve, reject) => {
            const request = index.getAll(date);
            request.onsuccess = (event) => {
                let results = event.target.result;
                if (type) {
                    results = results.filter(item => item.type === type);
                }
                resolve(results);
            };
            request.onerror = () => reject(new Error('Failed to get analytics'));
        });
    }

    async getAnalyticsRange(startDate, endDate) {
        const transaction = this.db.transaction(['analytics'], 'readonly');
        const store = transaction.objectStore('analytics');
        const index = store.index('date');
        const range = IDBKeyRange.bound(startDate, endDate);
        
        return new Promise((resolve, reject) => {
            const request = index.getAll(range);
            request.onsuccess = (event) => resolve(event.target.result);
            request.onerror = () => reject(new Error('Failed to get analytics range'));
        });
    }

    // Utility methods
    async clearOldData(daysToKeep = 30) {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);
        const cutoffDateStr = cutoffDate.toISOString().split('T')[0];

        // Clear old tasks
        const taskTransaction = this.db.transaction(['tasks'], 'readwrite');
        const taskStore = taskTransaction.objectStore('tasks');
        const taskIndex = taskStore.index('date');
        const taskRange = IDBKeyRange.upperBound(cutoffDateStr);

        const taskRequest = taskIndex.openCursor(taskRange);
        taskRequest.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                cursor.delete();
                cursor.continue();
            }
        };

        // Clear old schedules
        const scheduleTransaction = this.db.transaction(['schedules'], 'readwrite');
        const scheduleStore = scheduleTransaction.objectStore('schedules');
        
        const scheduleRequest = scheduleStore.openCursor();
        scheduleRequest.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor && cursor.key < cutoffDateStr) {
                cursor.delete();
                cursor.continue();
            }
        };

        // Clear old analytics
        const analyticsTransaction = this.db.transaction(['analytics'], 'readwrite');
        const analyticsStore = analyticsTransaction.objectStore('analytics');
        const analyticsIndex = analyticsStore.index('date');
        const analyticsRange = IDBKeyRange.upperBound(cutoffDateStr);

        const analyticsRequest = analyticsIndex.openCursor(analyticsRange);
        analyticsRequest.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                cursor.delete();
                cursor.continue();
            }
        };
    }

    // Export data for backup
    async exportData() {
        const data = {
            tasks: [],
            schedules: [],
            preferences: [],
            analytics: [],
            exportDate: new Date().toISOString()
        };

        // Export tasks
        const taskTransaction = this.db.transaction(['tasks'], 'readonly');
        const taskStore = taskTransaction.objectStore('tasks');
        data.tasks = await new Promise((resolve, reject) => {
            const request = taskStore.getAll();
            request.onsuccess = (event) => resolve(event.target.result);
            request.onerror = () => reject(new Error('Failed to export tasks'));
        });

        // Export schedules
        const scheduleTransaction = this.db.transaction(['schedules'], 'readonly');
        const scheduleStore = scheduleTransaction.objectStore('schedules');
        data.schedules = await new Promise((resolve, reject) => {
            const request = scheduleStore.getAll();
            request.onsuccess = (event) => resolve(event.target.result);
            request.onerror = () => reject(new Error('Failed to export schedules'));
        });

        // Export preferences
        data.preferences = await this.getAllPreferences();

        // Export analytics
        const analyticsTransaction = this.db.transaction(['analytics'], 'readonly');
        const analyticsStore = analyticsTransaction.objectStore('analytics');
        data.analytics = await new Promise((resolve, reject) => {
            const request = analyticsStore.getAll();
            request.onsuccess = (event) => resolve(event.target.result);
            request.onerror = () => reject(new Error('Failed to export analytics'));
        });

        return data;
    }

    // Import data from backup
    async importData(data) {
        // Import tasks
        if (data.tasks) {
            for (const task of data.tasks) {
                await this.saveTask(task);
            }
        }

        // Import schedules
        if (data.schedules) {
            for (const schedule of data.schedules) {
                await this.saveSchedule(schedule.date, schedule.schedule);
            }
        }

        // Import preferences
        if (data.preferences) {
            for (const [key, value] of Object.entries(data.preferences)) {
                await this.savePreference(key, value);
            }
        }

        // Import analytics
        if (data.analytics) {
            for (const analytics of data.analytics) {
                await this.saveAnalytics(analytics.type, analytics.data);
            }
        }
    }
}

// Create global instance
const storage = new LocalStorage(); 