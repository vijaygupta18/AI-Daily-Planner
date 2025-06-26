// Main Application Controller
class App {
    constructor() {
        this.currentDate = new Date().toISOString().split('T')[0];
        this.tasks = [];
        this.schedule = [];
        this.preferences = {};
        this.api = new API();
    }

    async init() {
        try {
            // Initialize storage
            await storage.init();
            
            // Load preferences
            this.preferences = await storage.getAllPreferences() || this.getDefaultPreferences();
            
            // Load current date tasks and schedule
            await this.loadDayData(this.currentDate);
            
            // Initialize UI
            this.initializeEventListeners();
            this.updateDateDisplay();
            this.updateAnalytics();
            
            // Clean old data periodically
            await storage.clearOldData(30);
            
            console.log('App initialized successfully');
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('Failed to initialize application');
        }
    }

    getDefaultPreferences() {
        return {
            work_start_hour: 8,
            work_end_hour: 20,
            lunch_duration: 60,
            break_duration: 15,
            theme: 'light',
            notifications_enabled: true
        };
    }

    initializeEventListeners() {
        // Task input
        document.getElementById('taskInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleAddTask();
            }
        });
        
        document.getElementById('addTaskBtn').addEventListener('click', () => {
            this.handleAddTask();
        });

        // Date navigation
        document.getElementById('prevDay').addEventListener('click', () => {
            this.navigateDate(-1);
        });

        document.getElementById('nextDay').addEventListener('click', () => {
            this.navigateDate(1);
        });

        document.getElementById('todayBtn').addEventListener('click', () => {
            this.currentDate = new Date().toISOString().split('T')[0];
            this.loadDayData(this.currentDate);
            this.updateDateDisplay();
        });

        document.getElementById('currentDate').addEventListener('change', (e) => {
            this.currentDate = e.target.value;
            this.loadDayData(this.currentDate);
        });

        // Actions
        document.getElementById('optimizeBtn').addEventListener('click', () => {
            this.optimizeSchedule();
        });

        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportToPDF();
        });

        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadDayData(this.currentDate);
        });

        // Settings
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.showSettings();
        });

        document.getElementById('closeSettings').addEventListener('click', () => {
            this.hideModal('settingsModal');
        });

        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });

        // Task edit modal
        document.getElementById('closeTaskEdit').addEventListener('click', () => {
            this.hideModal('taskEditModal');
        });

        document.getElementById('saveTaskEdit').addEventListener('click', () => {
            this.saveTaskEdit();
        });

        document.getElementById('cancelTaskEdit').addEventListener('click', () => {
            this.hideModal('taskEditModal');
        });

        // Integrations
        document.getElementById('googleCalBtn').addEventListener('click', () => {
            this.connectGoogleCalendar();
        });

        document.getElementById('notionBtn').addEventListener('click', () => {
            this.connectNotion();
        });

        document.getElementById('slackBtn').addEventListener('click', () => {
            this.connectSlack();
        });

        // Sync button
        document.getElementById('syncBtn').addEventListener('click', () => {
            this.syncWithCalendar();
        });
    }

    async handleAddTask() {
        const input = document.getElementById('taskInput');
        const text = input.value.trim();
        
        if (!text) return;

        try {
            this.showLoading();
            
            // Parse task using NLP
            const result = await this.api.parseTask(text);
            
            if (result.success) {
                // Add tasks to queue
                for (const task of result.tasks) {
                    task.date = this.currentDate;
                    await storage.saveTask(task);
                    this.tasks.push(task);
                }
                
                // Update UI
                this.renderTaskQueue();
                input.value = '';
                
                // Show success message
                this.showSuccess(`Added ${result.tasks.length} task(s) to queue`);
            } else {
                this.showError('Failed to parse task');
            }
        } catch (error) {
            console.error('Error adding task:', error);
            this.showError('Failed to add task');
        } finally {
            this.hideLoading();
        }
    }

    async optimizeSchedule() {
        if (this.tasks.length === 0) {
            this.showError('No tasks to schedule');
            return;
        }

        try {
            this.showLoading();
            
            // Call optimization API
            const result = await this.api.optimizeSchedule(
                this.tasks,
                this.currentDate,
                this.preferences
            );
            
            if (result.success) {
                // Save schedule
                await storage.saveSchedule(this.currentDate, result.schedule);
                this.schedule = result.schedule;
                
                // Update UI
                this.renderSchedule();
                this.updateAnalytics();
                
                this.showSuccess(`Scheduled ${result.scheduled_tasks} of ${result.total_tasks} tasks`);
            } else {
                this.showError('Failed to optimize schedule');
            }
        } catch (error) {
            console.error('Error optimizing schedule:', error);
            this.showError('Failed to optimize schedule');
        } finally {
            this.hideLoading();
        }
    }

    async loadDayData(date) {
        try {
            // Load from local storage first
            this.tasks = await storage.getTasks(date) || [];
            this.schedule = await storage.getSchedule(date) || [];
            
            // Try to sync with server
            try {
                const dailyStats = await this.api.getDailyReport(date);
                if (dailyStats.success) {
                    // Update analytics
                    await storage.saveAnalytics('daily_stats', dailyStats.report);
                }
            } catch (error) {
                console.log('Server sync failed, using local data');
            }
            
            // Update UI
            this.renderTaskQueue();
            this.renderSchedule();
            this.updateAnalytics();
            
        } catch (error) {
            console.error('Error loading day data:', error);
            this.showError('Failed to load data');
        }
    }

    renderTaskQueue() {
        const container = document.getElementById('taskQueue');
        container.innerHTML = '';
        
        // Show all tasks, both completed and uncompleted
        const allTasks = this.tasks.filter(task => {
            const isScheduled = this.schedule.some(slot => 
                slot.task && slot.task.id === task.id
            );
            return !isScheduled; // Show both completed and uncompleted unscheduled tasks
        });
        
        // Sort tasks: uncompleted first, then completed
        allTasks.sort((a, b) => {
            if (a.completed === b.completed) {
                return b.priority - a.priority; // Higher priority first within same completion status
            }
            return a.completed - b.completed; // Uncompleted (false) first
        });
        
        if (allTasks.length === 0) {
            container.innerHTML = '<p class="empty-message slide-in-up">No tasks in queue. Add some tasks to get started! 🚀</p>';
            return;
        }
        
        // Add section headers if we have both completed and uncompleted tasks
        const uncompletedTasks = allTasks.filter(task => !task.completed);
        const completedTasks = allTasks.filter(task => task.completed);
        
        let index = 0;
        
        // Render uncompleted tasks first
        if (uncompletedTasks.length > 0) {
            const uncompletedHeader = document.createElement('div');
            uncompletedHeader.className = 'task-section-header';
            uncompletedHeader.innerHTML = `
                <h4>
                    <i class="fas fa-list"></i> 
                    Pending Tasks (${uncompletedTasks.length})
                </h4>
            `;
            container.appendChild(uncompletedHeader);
            
            uncompletedTasks.forEach((task) => {
                const taskCard = this.createTaskCard(task);
                taskCard.classList.add('slide-in-left');
                taskCard.style.animationDelay = `${index * 0.1}s`;
                container.appendChild(taskCard);
                index++;
            });
        }
        
        // Render completed tasks
        if (completedTasks.length > 0) {
            const completedHeader = document.createElement('div');
            completedHeader.className = 'task-section-header';
            completedHeader.innerHTML = `
                <h4>
                    <i class="fas fa-check-circle"></i> 
                    Completed Tasks (${completedTasks.length})
                </h4>
            `;
            completedHeader.style.marginTop = uncompletedTasks.length > 0 ? '2rem' : '0';
            container.appendChild(completedHeader);
            
            completedTasks.forEach((task) => {
                const taskCard = this.createTaskCard(task);
                taskCard.classList.add('slide-in-left');
                taskCard.style.animationDelay = `${index * 0.1}s`;
                container.appendChild(taskCard);
                index++;
            });
        }
    }

    createTaskCard(task) {
        const card = document.createElement('div');
        card.className = `task-card ${task.completed ? 'completed' : ''}`;
        card.draggable = !task.completed; // Don't allow dragging completed tasks
        card.dataset.taskId = task.id;
        
        const priorityEmoji = task.priority >= 4 ? '🔥' : 
                             task.priority >= 3 ? '⭐' : '📝';
        
        card.innerHTML = `
            <div class="task-priority priority-${task.priority}"></div>
            <div class="task-info ${task.completed ? 'completed-task' : ''}">
                <div class="task-name">
                    ${task.completed ? '<i class="fas fa-check-circle task-completed-icon"></i>' : ''}
                    <span class="task-emoji">${priorityEmoji}</span>
                    <span class="${task.completed ? 'task-completed-text' : ''}">${this.escapeHtml(task.name)}</span>
                    ${task.completed ? '<span class="completed-badge">COMPLETED</span>' : ''}
                </div>
                <div class="task-meta ${task.completed ? 'task-completed-text' : ''}">
                    <span><i class="fas fa-clock"></i> ${task.duration} mins</span>
                    ${task.deadline ? `<span><i class="fas fa-calendar-alt"></i> ${new Date(task.deadline).toLocaleDateString()}</span>` : ''}
                    ${task.preferred_time ? `<span><i class="fas fa-sun"></i> ${task.preferred_time}</span>` : ''}
                </div>
            </div>
            <div class="task-actions">
                <button 
                    onclick="app.toggleTaskCompletion('${task.id}')" 
                    title="${task.completed ? 'Mark as Incomplete' : 'Mark as Complete'}"
                    class="task-toggle-btn ${task.completed ? 'mark-incomplete' : 'mark-complete'}"
                >
                    <i class="fas ${task.completed ? 'fa-undo' : 'fa-check'}"></i>
                    <span>${task.completed ? 'Undo' : 'Done'}</span>
                </button>
                <button onclick="app.editTask('${task.id}')" title="Edit" class="task-edit-btn">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="app.deleteTask('${task.id}')" title="Delete" class="task-delete-btn">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        // Add drag events only for uncompleted tasks
        if (!task.completed) {
            card.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('taskId', task.id);
                card.classList.add('dragging');
            });
            
            card.addEventListener('dragend', () => {
                card.classList.remove('dragging');
            });
        }
        
        return card;
    }

    renderSchedule() {
        const container = document.getElementById('scheduleTimeline');
        container.innerHTML = '';
        
        if (this.schedule.length === 0) {
            container.innerHTML = '<p class="empty-message slide-in-up">No schedule yet. Add tasks and click "Optimize Schedule" to generate one! 🎯</p>';
            return;
        }
        
        this.schedule.forEach((slot, index) => {
            const slotElement = this.createTimeSlot(slot);
            slotElement.classList.add('slide-in-up');
            slotElement.style.animationDelay = `${index * 0.1}s`;
            container.appendChild(slotElement);
        });
    }

    createTimeSlot(slot) {
        const slotDiv = document.createElement('div');
        slotDiv.className = 'time-slot';
        
        const startTime = new Date(slot.start_time).toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit'
        });
        
        const endTime = new Date(slot.end_time).toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit'
        });
        
        const timeLabel = document.createElement('div');
        timeLabel.className = 'time-label';
        timeLabel.textContent = startTime;
        
        const content = document.createElement('div');
        content.className = `slot-content ${slot.is_break ? 'break' : ''} ${slot.task?.completed ? 'completed' : ''}`;
        
        if (slot.is_break) {
            content.innerHTML = `
                <div class="slot-task-name">
                    <span class="task-emoji">☕</span>
                    Break Time
                </div>
                <div class="slot-duration">${startTime} - ${endTime}</div>
            `;
            slotDiv.classList.add('break');
        } else if (slot.task) {
            const priorityClass = slot.task.priority >= 4 ? 'high-priority' : 
                                 slot.task.priority >= 3 ? 'medium-priority' : 'low-priority';
            
            const priorityEmoji = slot.task.priority >= 4 ? '🔥' : 
                                 slot.task.priority >= 3 ? '⭐' : '📝';
            
            const priorityText = slot.task.priority >= 4 ? 'HIGH' : 
                                slot.task.priority >= 3 ? 'MED' : 'LOW';
            
            content.classList.add(priorityClass);
            
            content.innerHTML = `
                <div class="slot-task-name">
                    <span class="task-emoji">${priorityEmoji}</span>
                    <span class="${slot.task.completed ? 'task-completed-text' : ''}">${this.escapeHtml(slot.task.name)}</span>
                    ${slot.task.completed ? '<span class="completed-badge timeline-completed">COMPLETED</span>' : ''}
                </div>
                <div class="slot-duration ${slot.task.completed ? 'task-completed-text' : ''}">${startTime} - ${endTime}</div>
                <div class="slot-task-meta">
                    <div class="slot-priority ${slot.task.priority >= 4 ? 'high' : slot.task.priority >= 3 ? 'medium' : 'low'}">
                        ${priorityText}
                    </div>
                    <div class="slot-actions">
                        <button 
                            class="slot-action-btn ${slot.task.completed ? 'incomplete' : 'complete'}" 
                            onclick="app.toggleTaskCompletion('${slot.task.id}')" 
                            title="${slot.task.completed ? 'Mark as Incomplete' : 'Mark as Complete'}"
                        >
                            <i class="fas ${slot.task.completed ? 'fa-undo' : 'fa-check'}"></i>
                        </button>
                        <button class="slot-action-btn edit" onclick="app.editTask('${slot.task.id}')" title="Edit Task">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </div>
            `;
            
            if (slot.task.completed) {
                slotDiv.classList.add('completed');
                content.style.textDecoration = 'line-through';
                content.style.opacity = '0.7';
            }
        }
        
        slotDiv.appendChild(timeLabel);
        slotDiv.appendChild(content);
        
        return slotDiv;
    }

    async toggleTaskCompletion(taskId) {
        try {
            const task = this.tasks.find(t => t.id === taskId);
            if (!task) return;
            
            task.completed = !task.completed;
            
            // Update storage
            await storage.updateTaskStatus(taskId, task.completed);
            
            // Update server
            try {
                await this.api.completeTask(taskId, this.currentDate, task.completed);
            } catch (error) {
                console.log('Server update failed');
            }
            
            // Update UI
            this.renderSchedule();
            this.renderTaskQueue(); // Also update task queue to reflect completion status
            this.updateAnalytics();
            
            // Show success animation for completion
            if (task.completed) {
                this.showSuccess(`Great job! Task "${task.name}" completed!`);
                
                // Add celebration effect to the task card if visible
                const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
                if (taskCard) {
                    taskCard.classList.add('just-completed');
                    setTimeout(() => {
                        taskCard.classList.remove('just-completed');
                    }, 600);
                }
                
                // Add success glow effect
                const scheduleSection = document.querySelector('.schedule-section');
                scheduleSection.classList.add('success-glow');
                setTimeout(() => {
                    scheduleSection.classList.remove('success-glow');
                }, 2000);
            } else {
                this.showSuccess(`🔄 Task "${task.name}" marked as incomplete`);
            }
            
            // Update analytics
            await storage.saveAnalytics('task_completion', {
                taskId: taskId,
                completed: task.completed,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            console.error('Error toggling task completion:', error);
            this.showError('Failed to update task');
        }
    }

    async updateAnalytics() {
        const tasks = this.tasks;
        const completedTasks = tasks.filter(t => t.completed);
        const completionRate = tasks.length > 0 ? (completedTasks.length / tasks.length * 100).toFixed(0) : 0;
        
        // Calculate productive hours
        let productiveMinutes = 0;
        this.schedule.forEach(slot => {
            if (slot.task && slot.task.completed && !slot.is_break) {
                productiveMinutes += slot.task.duration;
            }
        });
        const productiveHours = (productiveMinutes / 60).toFixed(1);
        
        // Calculate priority score
        let priorityScore = 0;
        completedTasks.forEach(task => {
            priorityScore += task.priority * 10;
        });
        
        // Update UI
        document.getElementById('completionRate').textContent = `${completionRate}%`;
        document.getElementById('productiveHours').textContent = `${productiveHours}h`;
        document.getElementById('tasksCompleted').textContent = `${completedTasks.length}/${tasks.length}`;
        document.getElementById('priorityScore').textContent = priorityScore;
        
        // Update streak
        await this.updateStreak();
    }

    async updateStreak() {
        try {
            const weeklyStats = await this.api.getWeeklyReport(this.currentDate);
            if (weeklyStats.success && weeklyStats.report) {
                const streak = weeklyStats.report.current_streak || 0;
                document.getElementById('streakCount').textContent = streak;
            }
        } catch (error) {
            console.log('Failed to update streak');
        }
    }

    navigateDate(days) {
        const date = new Date(this.currentDate);
        date.setDate(date.getDate() + days);
        this.currentDate = date.toISOString().split('T')[0];
        this.loadDayData(this.currentDate);
        this.updateDateDisplay();
    }

    updateDateDisplay() {
        document.getElementById('currentDate').value = this.currentDate;
    }

    async editTask(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;
        
        // Populate modal
        document.getElementById('editTaskId').value = task.id;
        document.getElementById('editTaskName').value = task.name;
        document.getElementById('editTaskDuration').value = task.duration;
        document.getElementById('editTaskPriority').value = task.priority;
        
        this.showModal('taskEditModal');
    }

    async saveTaskEdit() {
        const taskId = document.getElementById('editTaskId').value;
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;
        
        // Update task
        task.name = document.getElementById('editTaskName').value;
        task.duration = parseInt(document.getElementById('editTaskDuration').value);
        task.priority = parseInt(document.getElementById('editTaskPriority').value);
        
        // Save to storage
        await storage.saveTask(task);
        
        // Update UI
        this.renderTaskQueue();
        this.hideModal('taskEditModal');
        
        this.showSuccess('Task updated successfully');
    }

    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) return;
        
        try {
            // Remove from storage
            await storage.deleteTask(taskId);
            
            // Remove from array
            this.tasks = this.tasks.filter(t => t.id !== taskId);
            
            // Update UI
            this.renderTaskQueue();
            
            this.showSuccess('Task deleted successfully');
        } catch (error) {
            console.error('Error deleting task:', error);
            this.showError('Failed to delete task');
        }
    }

    async showSettings() {
        // Ensure preferences are loaded with defaults
        if (!this.preferences || Object.keys(this.preferences).length === 0) {
            this.preferences = this.getDefaultPreferences();
        }
        
        // Load current preferences with fallbacks
        const workStart = this.preferences.work_start_hour || 8;
        const workEnd = this.preferences.work_end_hour || 20;
        const lunchDuration = this.preferences.lunch_duration || 60;
        const breakDuration = this.preferences.break_duration || 15;
        
        document.getElementById('workStart').value = `${workStart.toString().padStart(2, '0')}:00`;
        document.getElementById('workEnd').value = `${workEnd.toString().padStart(2, '0')}:00`;
        document.getElementById('lunchDuration').value = lunchDuration;
        document.getElementById('breakDuration').value = breakDuration;
        
        this.showModal('settingsModal');
    }

    async saveSettings() {
        // Get values
        const workStart = document.getElementById('workStart').value;
        const workEnd = document.getElementById('workEnd').value;
        const lunchDuration = parseInt(document.getElementById('lunchDuration').value);
        const breakDuration = parseInt(document.getElementById('breakDuration').value);
        
        // Update preferences
        this.preferences.work_start_hour = parseInt(workStart.split(':')[0]);
        this.preferences.work_end_hour = parseInt(workEnd.split(':')[0]);
        this.preferences.lunch_duration = lunchDuration;
        this.preferences.break_duration = breakDuration;
        
        // Save to storage
        for (const [key, value] of Object.entries(this.preferences)) {
            await storage.savePreference(key, value);
        }
        
        // Update server
        try {
            await this.api.updatePreferences(this.preferences);
        } catch (error) {
            console.log('Server update failed');
        }
        
        this.hideModal('settingsModal');
        this.showSuccess('Settings saved successfully');
    }

    async connectGoogleCalendar() {
        try {
            this.showLoading();
            const result = await this.api.authenticateCalendar();
            
            if (result.success) {
                this.showSuccess('Google Calendar connected successfully');
                // Update button state
                document.getElementById('googleCalBtn').innerHTML = '<i class="fab fa-google"></i> Connected';
            } else {
                this.showError('Failed to connect Google Calendar');
            }
        } catch (error) {
            console.error('Error connecting Google Calendar:', error);
            this.showError('Failed to connect Google Calendar');
        } finally {
            this.hideLoading();
        }
    }

    async syncWithCalendar() {
        if (this.schedule.length === 0) {
            this.showError('No schedule to sync');
            return;
        }
        
        try {
            this.showLoading();
            const result = await this.api.syncToCalendar(this.currentDate);
            
            if (result.success) {
                this.showSuccess(`Synced ${result.synced_count} events to calendar`);
            } else {
                this.showError('Failed to sync with calendar');
            }
        } catch (error) {
            console.error('Error syncing with calendar:', error);
            this.showError('Failed to sync with calendar');
        } finally {
            this.hideLoading();
        }
    }

    async exportToPDF() {
        try {
            this.showLoading();
            
            // Calculate date range for weekly report
            const endDate = new Date(this.currentDate);
            const startDate = new Date(this.currentDate);
            startDate.setDate(startDate.getDate() - 6);
            
            const result = await this.api.generatePDFReport(
                startDate.toISOString().split('T')[0],
                endDate.toISOString().split('T')[0]
            );
            
            if (result.success) {
                // Download PDF
                window.open(result.pdf_path, '_blank');
                this.showSuccess('Report generated successfully');
            } else {
                this.showError('Failed to generate report');
            }
        } catch (error) {
            console.error('Error generating PDF:', error);
            this.showError('Failed to generate report');
        } finally {
            this.hideLoading();
        }
    }

    // UI Helper methods
    showModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    hideModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    }

    showLoading() {
        document.getElementById('loadingOverlay').classList.add('active');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.remove('active');
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }
    
    showToast(message, type = 'info') {
        // Remove existing toasts
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} slide-in-up`;
        
        const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
        
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${icon}</span>
                <span class="toast-message">${message}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add toast styles if not exist
        if (!document.querySelector('#toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 10000;
                    min-width: 300px;
                    max-width: 500px;
                    border-radius: var(--radius-lg);
                    box-shadow: var(--shadow-xl);
                    overflow: hidden;
                }
                
                .toast-success {
                    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                    color: white;
                }
                
                .toast-error {
                    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                    color: white;
                }
                
                .toast-info {
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    color: white;
                }
                
                .toast-content {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 16px 20px;
                }
                
                .toast-icon {
                    font-size: 18px;
                }
                
                .toast-message {
                    flex: 1;
                    font-weight: 500;
                }
                
                .toast-close {
                    background: transparent;
                    border: none;
                    color: currentColor;
                    cursor: pointer;
                    opacity: 0.8;
                    padding: 4px;
                    border-radius: 4px;
                    transition: var(--transition);
                }
                
                .toast-close:hover {
                    opacity: 1;
                    background: rgba(255, 255, 255, 0.1);
                }
            `;
            document.head.appendChild(style);
        }
        
        // Add to page
        document.body.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Placeholder methods for future implementation
    async connectNotion() {
        this.showError('Notion integration coming soon!');
    }

    async connectSlack() {
        this.showError('Slack integration coming soon!');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    window.app = new App();
    await app.init();
}); 