/**
 * Main Application Controller
 * Handles navigation, UI interactions, and overall application flow
 */

class AppController {
    constructor() {
        this.currentSection = 'dashboard';
        this.agentManager = null;
        this.dashboardManager = null;
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupEventListeners();
        this.initializeComponents();
        this.loadInitialData();
    }

    setupNavigation() {
        // Handle navigation clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('[onclick^="showSection"]')) {
                const section = e.target.getAttribute('onclick').match(/'([^']+)'/)[1];
                this.showSection(section);
            }
        });
    }

    setupEventListeners() {
        // Global event listeners
        document.addEventListener('keydown', (e) => {
            // Keyboard shortcuts
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case '1':
                        e.preventDefault();
                        this.showSection('dashboard');
                        break;
                    case '2':
                        e.preventDefault();
                        this.showSection('agents');
                        break;
                    case '3':
                        e.preventDefault();
                        this.showSection('analysis');
                        break;
                    case '4':
                        e.preventDefault();
                        this.showSection('reports');
                        break;
                    case 'r':
                        e.preventDefault();
                        this.refreshAll();
                        break;
                }
            }
        });

        // Window resize handler
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // Before unload handler
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }

    initializeComponents() {
        // Initialize agent manager
        if (typeof AgentManager !== 'undefined') {
            this.agentManager = new AgentManager();
        }

        // Initialize dashboard manager
        if (typeof DashboardManager !== 'undefined') {
            this.dashboardManager = new DashboardManager();
        }

        // Initialize other components
        this.initializeTooltips();
        this.initializeModals();
    }

    initializeTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    initializeModals() {
        // Initialize Bootstrap modals
        const modalTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="modal"]'));
        modalTriggerList.map(function (modalTriggerEl) {
            return new bootstrap.Modal(modalTriggerEl);
        });
    }

    loadInitialData() {
        // Load initial data for the dashboard
        this.loadSystemStatus();
        this.loadAgentStatus();
        this.loadTaskQueue();
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            this.updateSystemStatus(status);
        } catch (error) {
            console.error('Error loading system status:', error);
        }
    }

    async loadAgentStatus() {
        try {
            const response = await fetch('/api/agents');
            const agents = await response.json();
            this.updateAgentStatus(agents);
        } catch (error) {
            console.error('Error loading agent status:', error);
        }
    }

    async loadTaskQueue() {
        try {
            const response = await fetch('/api/tasks');
            const tasks = await response.json();
            this.updateTaskQueue(tasks);
        } catch (error) {
            console.error('Error loading task queue:', error);
        }
    }

    updateSystemStatus(status) {
        // Update system status indicators
        const indicators = {
            'totalSections': status.agents ? Object.keys(status.agents).length : 0,
            'totalPapers': status.completed_tasks || 0,
            'activeAgents': status.active_tasks || 0,
            'completedTasks': status.completed_tasks || 0
        };

        Object.entries(indicators).forEach(([key, value]) => {
            const element = document.getElementById(key);
            if (element) {
                element.textContent = value;
            }
        });
    }

    updateAgentStatus(agents) {
        // Update agent status in the UI
        Object.entries(agents).forEach(([agentId, agent]) => {
            const agentCard = document.querySelector(`[onclick="selectAgent('${agentId}')"]`);
            if (agentCard) {
                const statusIndicator = agentCard.querySelector('.agent-status');
                if (statusIndicator) {
                    statusIndicator.className = `agent-status ${agent.status}`;
                }

                // Update progress if available
                const progressElement = agentCard.querySelector('.progress-ring circle:last-child');
                if (progressElement && agent.progress !== undefined) {
                    const circumference = 2 * Math.PI * 25; // radius = 25
                    const offset = circumference - (agent.progress / 100) * circumference;
                    progressElement.style.strokeDashoffset = offset;
                }
            }
        });
    }

    updateTaskQueue(tasks) {
        const queueContainer = document.getElementById('taskQueue');
        if (!queueContainer) return;

        queueContainer.innerHTML = '';

        // Add active tasks
        if (tasks.active) {
            tasks.active.forEach(task => {
                const taskElement = this.createTaskElement(task, 'In Progress');
                queueContainer.appendChild(taskElement);
            });
        }

        // Add queued tasks
        if (tasks.queued) {
            tasks.queued.forEach(task => {
                const taskElement = this.createTaskElement(task, 'Queued');
                queueContainer.appendChild(taskElement);
            });
        }

        // Add completed tasks (last 5)
        if (tasks.completed) {
            tasks.completed.slice(-5).forEach(task => {
                const taskElement = this.createTaskElement(task, 'Completed');
                queueContainer.appendChild(taskElement);
            });
        }
    }

    createTaskElement(task, status) {
        const div = document.createElement('div');
        div.className = 'task-item';
        
        const statusClass = {
            'In Progress': 'bg-primary',
            'Queued': 'bg-warning',
            'Completed': 'bg-success',
            'Failed': 'bg-danger'
        }[status] || 'bg-secondary';

        div.innerHTML = `
            <div class="d-flex justify-content-between">
                <span>${task.type || 'Unknown Task'}</span>
                <span class="badge ${statusClass}">${status}</span>
            </div>
            ${task.assigned_agent ? `<small class="text-muted">Agent: ${task.assigned_agent}</small>` : ''}
        `;
        
        return div;
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.style.display = 'none';
        });

        // Show selected section
        const targetSection = document.getElementById(sectionName);
        if (targetSection) {
            targetSection.style.display = 'block';
            this.currentSection = sectionName;
        }

        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        const activeLink = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    loadSectionData(sectionName) {
        switch(sectionName) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'agents':
                this.loadAgentsData();
                break;
            case 'analysis':
                this.loadAnalysisData();
                break;
            case 'reports':
                this.loadReportsData();
                break;
            case 'settings':
                this.loadSettingsData();
                break;
        }
    }

    async loadDashboardData() {
        // Load dashboard-specific data
        if (this.dashboardManager) {
            await this.dashboardManager.loadThesisAnalysis();
            await this.dashboardManager.loadTrendsAnalysis();
        }
    }

    async loadAgentsData() {
        // Load agent-specific data
        await this.loadAgentStatus();
    }

    async loadAnalysisData() {
        // Load analysis data
        try {
            const [thesisResponse, trendsResponse] = await Promise.all([
                fetch('/api/analysis/thesis'),
                fetch('/api/analysis/trends')
            ]);

            const thesisData = await thesisResponse.json();
            const trendsData = await trendsResponse.json();

            this.displayAnalysisData(thesisData, trendsData);
        } catch (error) {
            console.error('Error loading analysis data:', error);
        }
    }

    displayAnalysisData(thesisData, trendsData) {
        const container = document.getElementById('analysisCharts');
        if (!container) return;

        // Create analysis charts container
        container.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div id="thesisStructureChart" style="height: 400px;"></div>
                </div>
                <div class="col-md-6">
                    <div id="domainDistributionChart" style="height: 400px;"></div>
                </div>
            </div>
            <div class="row mt-4">
                <div class="col-md-12">
                    <div id="difficultyAnalysisChart" style="height: 400px;"></div>
                </div>
            </div>
        `;

        // Initialize charts with real data
        if (this.dashboardManager) {
            this.dashboardManager.updateThesisCharts(thesisData);
            this.dashboardManager.updateTrendsCharts(trendsData);
        }
    }

    async loadReportsData() {
        // Load reports data
        try {
            const response = await fetch('/api/results');
            const results = await response.json();
            this.displayReportsData(results);
        } catch (error) {
            console.error('Error loading reports data:', error);
        }
    }

    displayReportsData(results) {
        // Display available reports
        console.log('Reports data:', results);
    }

    loadSettingsData() {
        // Load settings data
        console.log('Loading settings data...');
    }

    refreshAll() {
        // Refresh all data
        this.loadSystemStatus();
        this.loadAgentStatus();
        this.loadTaskQueue();
        
        if (this.dashboardManager) {
            this.dashboardManager.updateDashboardData();
        }

        this.showNotification('All data refreshed', 'success');
    }

    handleResize() {
        // Handle window resize
        if (this.dashboardManager) {
            // Redraw charts on resize
            setTimeout(() => {
                this.dashboardManager.updateCharts();
            }, 100);
        }
    }

    cleanup() {
        // Cleanup resources
        if (this.dashboardManager) {
            this.dashboardManager.destroy();
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    // API methods
    async startWorkflow() {
        try {
            const response = await fetch('/api/workflow/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                this.showNotification('Workflow started successfully', 'success');
                // Refresh task queue
                this.loadTaskQueue();
            } else {
                this.showNotification('Failed to start workflow', 'error');
            }
        } catch (error) {
            console.error('Error starting workflow:', error);
            this.showNotification('Error starting workflow', 'error');
        }
    }

    async createTask(taskType, parameters = {}) {
        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    type: taskType,
                    parameters: parameters
                })
            });

            const result = await response.json();
            
            if (result.task_id) {
                this.showNotification(`Task created: ${taskType}`, 'success');
                this.loadTaskQueue();
            } else {
                this.showNotification('Failed to create task', 'error');
            }
        } catch (error) {
            console.error('Error creating task:', error);
            this.showNotification('Error creating task', 'error');
        }
    }
}

// Global functions for UI interaction
function showSection(sectionName) {
    if (window.appController) {
        window.appController.showSection(sectionName);
    }
}

function selectAgent(agentId) {
    if (window.appController && window.appController.agentManager) {
        window.appController.agentManager.selectAgent(agentId);
    }
}

function startAgentWorkflow() {
    if (window.appController) {
        window.appController.startWorkflow();
    }
}

function refreshDashboard() {
    if (window.appController) {
        window.appController.refreshAll();
    }
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.appController = new AppController();
    
    // Make functions globally available
    window.showSection = showSection;
    window.selectAgent = selectAgent;
    window.startAgentWorkflow = startAgentWorkflow;
    window.refreshDashboard = refreshDashboard;
    window.toggleFullscreen = toggleFullscreen;
});

// Export for use in other modules
window.AppController = AppController;
