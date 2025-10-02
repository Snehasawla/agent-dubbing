/**
 * Multi-Agent System Management
 * Handles agent coordination, task distribution, and status updates
 */

class AgentManager {
    constructor() {
        this.agents = {
            data: new DataAgent(),
            analysis: new AnalysisAgent(),
            visualization: new VisualizationAgent(),
            report: new ReportAgent()
        };
        this.taskQueue = [];
        this.activeTasks = new Map();
        this.agentStatus = new Map();
        this.init();
    }

    init() {
        // Initialize agent statuses
        Object.keys(this.agents).forEach(agentId => {
            this.agentStatus.set(agentId, 'offline');
        });
        
        // Start agent monitoring
        this.startAgentMonitoring();
        
        // Initialize task queue
        this.initializeTaskQueue();
    }

    startAgentMonitoring() {
        setInterval(() => {
            this.updateAgentStatuses();
            this.processTaskQueue();
        }, 2000);
    }

    updateAgentStatuses() {
        Object.entries(this.agents).forEach(([agentId, agent]) => {
            const status = agent.getStatus();
            this.agentStatus.set(agentId, status);
            this.updateAgentUI(agentId, status);
        });
    }

    updateAgentUI(agentId, status) {
        const agentCard = document.querySelector(`[onclick="selectAgent('${agentId}')"]`);
        if (agentCard) {
            const statusIndicator = agentCard.querySelector('.agent-status');
            statusIndicator.className = `agent-status ${status}`;
        }
    }

    processTaskQueue() {
        if (this.taskQueue.length === 0) return;

        const availableAgents = Array.from(this.agentStatus.entries())
            .filter(([_, status]) => status === 'online')
            .map(([agentId, _]) => agentId);

        if (availableAgents.length === 0) return;

        const task = this.taskQueue.shift();
        const agentId = this.selectBestAgent(task, availableAgents);
        
        if (agentId) {
            this.assignTask(agentId, task);
        }
    }

    selectBestAgent(task, availableAgents) {
        // Simple round-robin selection
        // In a real system, this would consider agent capabilities, workload, etc.
        return availableAgents[Math.floor(Math.random() * availableAgents.length)];
    }

    assignTask(agentId, task) {
        const agent = this.agents[agentId];
        if (agent && agent.canHandleTask(task)) {
            this.activeTasks.set(task.id, { agentId, task, startTime: Date.now() });
            agent.executeTask(task);
            this.updateTaskQueueUI();
        }
    }

    addTask(task) {
        task.id = this.generateTaskId();
        this.taskQueue.push(task);
        this.updateTaskQueueUI();
    }

    generateTaskId() {
        return 'task_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    updateTaskQueueUI() {
        const queueContainer = document.getElementById('taskQueue');
        if (!queueContainer) return;

        queueContainer.innerHTML = '';
        
        // Add active tasks
        this.activeTasks.forEach((taskInfo, taskId) => {
            const taskElement = this.createTaskElement(taskInfo.task, 'In Progress', taskInfo.agentId);
            queueContainer.appendChild(taskElement);
        });

        // Add queued tasks
        this.taskQueue.forEach(task => {
            const taskElement = this.createTaskElement(task, 'Queued');
            queueContainer.appendChild(taskElement);
        });
    }

    createTaskElement(task, status, agentId = null) {
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
                <span>${task.name}</span>
                <span class="badge ${statusClass}">${status}</span>
            </div>
            ${agentId ? `<small class="text-muted">Agent: ${agentId}</small>` : ''}
        `;
        
        return div;
    }

    initializeTaskQueue() {
        // Add some initial tasks
        this.addTask({
            name: 'Process Thesis Data',
            type: 'data_processing',
            priority: 'high'
        });
        
        this.addTask({
            name: 'Generate Visualizations',
            type: 'visualization',
            priority: 'medium'
        });
        
        this.addTask({
            name: 'Create Analysis Report',
            type: 'report_generation',
            priority: 'low'
        });
    }

    startAgentWorkflow() {
        // Start a comprehensive analysis workflow
        this.addTask({
            name: 'Initialize Data Pipeline',
            type: 'data_processing',
            priority: 'high'
        });
        
        this.addTask({
            name: 'Perform Statistical Analysis',
            type: 'analysis',
            priority: 'high'
        });
        
        this.addTask({
            name: 'Create Interactive Dashboard',
            type: 'visualization',
            priority: 'medium'
        });
        
        this.addTask({
            name: 'Generate Final Report',
            type: 'report_generation',
            priority: 'medium'
        });

        this.showNotification('Agent workflow started!', 'success');
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
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// Base Agent Class
class BaseAgent {
    constructor(name, capabilities = []) {
        this.name = name;
        this.capabilities = capabilities;
        this.status = 'offline';
        this.currentTask = null;
        this.progress = 0;
        this.logs = [];
    }

    getStatus() {
        return this.status;
    }

    canHandleTask(task) {
        return this.capabilities.includes(task.type) && this.status === 'online';
    }

    async executeTask(task) {
        this.status = 'busy';
        this.currentTask = task;
        this.progress = 0;
        
        this.log(`Starting task: ${task.name}`);
        
        try {
            await this.performTask(task);
            this.log(`Completed task: ${task.name}`);
            this.status = 'online';
            this.progress = 100;
        } catch (error) {
            this.log(`Failed task: ${task.name} - ${error.message}`, 'error');
            this.status = 'online';
            this.progress = 0;
        }
        
        this.currentTask = null;
    }

    log(message, level = 'info') {
        const timestamp = new Date().toLocaleString();
        this.logs.push({ timestamp, message, level });
        this.updateAgentLogUI();
    }

    updateAgentLogUI() {
        const logContainer = document.getElementById('agentLog');
        if (!logContainer) return;

        const recentLogs = this.logs.slice(-10);
        logContainer.innerHTML = recentLogs.map(log => `
            <div class="log-entry log-${log.level}">
                <span class="text-muted">[${log.timestamp}]</span>
                ${this.name}: ${log.message}
            </div>
        `).join('');
    }

    async performTask(task) {
        // Override in subclasses
        throw new Error('performTask not implemented');
    }
}

// Data Agent
class DataAgent extends BaseAgent {
    constructor() {
        super('DataAgent', ['data_processing', 'data_cleaning', 'data_validation']);
        this.status = 'online';
    }

    async performTask(task) {
        if (task.type === 'data_processing') {
            await this.processData();
        }
    }

    async processData() {
        // Simulate data processing
        for (let i = 0; i <= 100; i += 10) {
            this.progress = i;
            await this.delay(500);
            this.log(`Processing data... ${i}%`);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Analysis Agent
class AnalysisAgent extends BaseAgent {
    constructor() {
        super('AnalysisAgent', ['analysis', 'statistical_analysis', 'trend_analysis']);
        this.status = 'online';
    }

    async performTask(task) {
        if (task.type === 'analysis') {
            await this.performAnalysis();
        }
    }

    async performAnalysis() {
        // Simulate analysis
        for (let i = 0; i <= 100; i += 15) {
            this.progress = i;
            await this.delay(800);
            this.log(`Analyzing data... ${i}%`);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Visualization Agent
class VisualizationAgent extends BaseAgent {
    constructor() {
        super('VisualizationAgent', ['visualization', 'chart_generation', 'dashboard_update']);
        this.status = 'online';
    }

    async performTask(task) {
        if (task.type === 'visualization') {
            await this.createVisualizations();
        }
    }

    async createVisualizations() {
        // Simulate visualization creation
        for (let i = 0; i <= 100; i += 20) {
            this.progress = i;
            await this.delay(600);
            this.log(`Creating visualizations... ${i}%`);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Report Agent
class ReportAgent extends BaseAgent {
    constructor() {
        super('ReportAgent', ['report_generation', 'document_creation', 'export']);
        this.status = 'offline';
    }

    async performTask(task) {
        if (task.type === 'report_generation') {
            await this.generateReport();
        }
    }

    async generateReport() {
        // Simulate report generation
        for (let i = 0; i <= 100; i += 25) {
            this.progress = i;
            await this.delay(1000);
            this.log(`Generating report... ${i}%`);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Global agent manager instance
let agentManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    agentManager = new AgentManager();
});

// Global functions for UI interaction
function selectAgent(agentId) {
    // Remove active class from all agent cards
    document.querySelectorAll('.agent-card').forEach(card => {
        card.classList.remove('active');
    });
    
    // Add active class to selected agent
    const selectedCard = document.querySelector(`[onclick="selectAgent('${agentId}')"]`);
    if (selectedCard) {
        selectedCard.classList.add('active');
    }
    
    // Show agent details
    showAgentDetails(agentId);
}

function showAgentDetails(agentId) {
    const detailsPanel = document.getElementById('agentDetails');
    const titleElement = document.getElementById('agentDetailsTitle');
    const contentElement = document.getElementById('agentDetailsContent');
    
    if (!detailsPanel || !titleElement || !contentElement) return;
    
    const agent = agentManager.agents[agentId];
    if (!agent) return;
    
    titleElement.textContent = `${agent.name} Details`;
    
    contentElement.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>Status</h6>
                <p class="badge bg-${agent.status === 'online' ? 'success' : agent.status === 'busy' ? 'warning' : 'secondary'}">${agent.status.toUpperCase()}</p>
                
                <h6>Capabilities</h6>
                <ul>
                    ${agent.capabilities.map(cap => `<li>${cap}</li>`).join('')}
                </ul>
            </div>
            <div class="col-md-6">
                <h6>Current Task</h6>
                <p>${agent.currentTask ? agent.currentTask.name : 'None'}</p>
                
                <h6>Progress</h6>
                <div class="progress">
                    <div class="progress-bar" style="width: ${agent.progress}%">${agent.progress}%</div>
                </div>
            </div>
        </div>
    `;
    
    detailsPanel.style.display = 'block';
}

function startAgentWorkflow() {
    if (agentManager) {
        agentManager.startAgentWorkflow();
    }
}

function refreshDashboard() {
    // Refresh dashboard data
    if (agentManager) {
        agentManager.updateAgentStatuses();
        agentManager.updateTaskQueueUI();
    }
    
    // Update metrics
    updateDashboardMetrics();
}

function updateDashboardMetrics() {
    // Update dashboard metrics with real-time data
    const metrics = {
        totalSections: 24,
        totalPapers: 40,
        activeAgents: Object.values(agentManager.agents).filter(agent => agent.status === 'online').length,
        completedTasks: Math.floor(Math.random() * 20) + 10
    };
    
    Object.entries(metrics).forEach(([key, value]) => {
        const element = document.getElementById(key);
        if (element) {
            element.textContent = value;
        }
    });
}
