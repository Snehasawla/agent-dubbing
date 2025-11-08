/**
 * Multi-Agent System Management
 * Handles agent coordination, task distribution, and status updates
 */

const API_BASE_URL = 'http://localhost:5000';

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

            // Start tracking task progress so UI stays in sync
            this.trackTaskProgress(task.id, agentId);
        }
    }

    addTask(task) {
        task.id = this.generateTaskId();
        this.taskQueue.push(task);
        this.updateTaskQueueUI();
        this.showNotification(`Task added: ${task.name || task.type}`, 'info');
        this.processTaskQueue();
    }

    generateTaskId() {
        return 'task_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    trackTaskProgress(taskId, agentId) {
        const agent = this.agents[agentId];
        if (!agent) return;

        const interval = setInterval(() => {
            const statusInfo = this.agentStatus.get(agentId);
            const taskInfo = this.activeTasks.get(taskId);

            if (!statusInfo || !taskInfo) {
                clearInterval(interval);
                this.updateTaskQueueUI();
                return;
            }

            // Update task progress if available
            taskInfo.task.progress = statusInfo.progress || 0;
            this.updateTaskQueueUI();

            if (statusInfo.status === 'idle' || statusInfo.progress === 100) {
                clearInterval(interval);
                this.activeTasks.delete(taskId);
                taskInfo.task.status = 'Completed';
                this.updateTaskQueueUI();
                this.showNotification(`Task completed: ${taskInfo.task.name || taskInfo.task.type}`, 'success');

                // Inform user that backend queues visualization automatically
                if (taskInfo.task.type === 'statistical_analysis' && taskInfo.task.parameters?.cleaned_file) {
                    this.showNotification('Visualization task queued automatically by backend.', 'info');
                }

                if (taskInfo.task.type === 'statistical_analysis') {
                    if (typeof window.showSection === 'function') {
                        window.showSection('analysis');
                    }
                    if (window.appController) {
                        // Give the UI a moment to switch sections before loading data
                        setTimeout(() => {
                            if (window.appController.refreshAnalysis) {
                                window.appController.refreshAnalysis();
                            } else {
                                window.appController.loadAnalysisData();
                            }
                        }, 300);
                    }
                }
            }
        }, 1000);
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
        
        // Auto-remove after 5 seconds (except for progress notifications)
        if (type !== 'progress') {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 5000);
        }
        
        return notification;
    }

    async monitorAnalysisProgress(taskId, filename) {
        /**Monitor analysis progress and update UI*/
        let progressCheckInterval = null;
        let progressNotification = null;
        
        const checkProgress = async () => {
            try {
                // Check task status
                const taskResp = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/status`);
                if (taskResp.ok) {
                    const taskStatus = await taskResp.json();
                    
                    // Update or create progress notification
                    if (!progressNotification) {
                        progressNotification = this.showNotification(
                            `Analyzing ${filename}... 0%`, 
                            'info'
                        );
                        progressNotification.classList.add('progress-notification');
                    }
                    
                    const progress = taskStatus.progress || 0;
                    const status = taskStatus.status || 'unknown';
                    
                    // Update notification
                    const message = status === 'completed' 
                        ? `✅ Analysis completed for ${filename}!`
                        : status === 'failed'
                        ? `❌ Analysis failed for ${filename}`
                        : `Analyzing ${filename}... ${progress}%`;
                    
                    progressNotification.innerHTML = `
                        ${message}
                        ${status === 'in_progress' ? `<div class="progress mt-2" style="height: 5px;">
                            <div class="progress-bar" role="progressbar" style="width: ${progress}%"></div>
                        </div>` : ''}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    
                    // Stop monitoring if completed or failed
                    if (status === 'completed' || status === 'failed') {
                        if (progressCheckInterval) {
                            clearInterval(progressCheckInterval);
                        }
                        
                        // Remove progress notification after 10 seconds
                        setTimeout(() => {
                            if (progressNotification && progressNotification.parentNode) {
                                progressNotification.parentNode.removeChild(progressNotification);
                            }
                        }, 10000);
                        
                        // If completed, show success and offer to view results
                        if (status === 'completed') {
                            this.showNotification(
                                `Analysis completed! Click here to view results.`, 
                                'success'
                            );

                            // Automatically navigate to analysis view and refresh data
                            if (typeof window.showSection === 'function') {
                                window.showSection('analysis');
                            }
                            if (window.appController) {
                                // Give the UI a moment to switch sections before loading data
                                setTimeout(() => {
                                    if (window.appController.refreshAnalysis) {
                                        window.appController.refreshAnalysis();
                                    } else {
                                        window.appController.loadAnalysisData();
                                    }
                                }, 300);
                            }
                        }
                    }
                }
                
                // Also check analysis agent progress
                const agentResp = await fetch(`${API_BASE_URL}/api/agents/analysis/progress`);
                if (agentResp.ok) {
                    const agentProgress = await agentResp.json();
                    console.log('Analysis Agent Progress:', agentProgress);
                }
                
            } catch (error) {
                console.error('Error checking progress:', error);
            }
        };
        
        // Check progress every 2 seconds
        progressCheckInterval = setInterval(checkProgress, 2000);
        
        // Initial check
        checkProgress();
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
        this.setupFileUpload();
    }

    setupFileUpload() {
        // Add file upload UI if not exists
        if (!document.getElementById('fileUpload')) {
            const uploadDiv = document.createElement('div');
            uploadDiv.className = 'file-upload-section mt-3';
            uploadDiv.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Upload CSV File</h5>
                        <input type="file" id="fileUpload" class="form-control" accept=".csv" />
                        <div class="progress mt-2 d-none">
                            <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                        </div>
                        <div id="uploadStatus" class="mt-2"></div>
                    </div>
                </div>
            `;
            document.querySelector('.agent-workspace').appendChild(uploadDiv);
            
            // Add event listener
            document.getElementById('fileUpload').addEventListener('change', (e) => this.handleFileUpload(e));
        }
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        if (!file.name.endsWith('.csv')) {
            this.showUploadStatus('Error: Please select a CSV file', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            this.showUploadStatus('Uploading file...', 'info');
            this.updateProgress(10);

            const response = await fetch(`${API_BASE_URL}/api/upload`, {
                method: 'POST',
                body: formData,
                mode: 'cors'
            });

            this.updateProgress(50);
            const result = await response.json();

            if (result.status === 'success') {
                this.showUploadStatus('File processed successfully!', 'success');
                this.updateProgress(100);
                this.log(`Successfully processed ${file.name}`);
                this.status = 'processing';
            } else {
                this.showUploadStatus(`Error: ${result.message}`, 'error');
                this.updateProgress(0);
                this.log(`Error processing ${file.name}: ${result.message}`);
            }
        } catch (error) {
            this.showUploadStatus('Error uploading file', 'error');
            this.updateProgress(0);
            this.log(`Error uploading file: ${error.message}`);
        }
    }

    showUploadStatus(message, type) {
        const statusDiv = document.getElementById('uploadStatus');
        if (statusDiv) {
            statusDiv.className = `alert alert-${type === 'error' ? 'danger' : type}`;
            statusDiv.textContent = message;
        }
    }

    updateProgress(percent) {
        const progressBar = document.querySelector('.progress');
        const progressBarInner = document.querySelector('.progress-bar');
        if (progressBar && progressBarInner) {
            progressBar.classList.remove('d-none');
            progressBarInner.style.width = `${percent}%`;
            progressBarInner.setAttribute('aria-valuenow', percent);
        }
    }

    async performTask(task) {
        if (task.type === 'data_processing') {
            await this.processData(task);
        }
    }

    async processData(task) {
        this.log(`Processing data from ${task.input_file}`);
        this.status = 'processing';
        
        try {
            for (let i = 0; i <= 100; i += 20) {
                this.progress = i;
                await this.delay(500);
                this.log(`Processing ${task.dataset_type} data... ${i}%`);
            }
            
            this.log(`Data processing complete. Output saved to ${task.output_file}`);
            this.status = 'online';
        } catch (error) {
            this.log(`Error processing data: ${error.message}`);
            this.status = 'error';
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

    // If user selects the analysis agent from the Agents screen,
    // immediately switch to the analysis section and refresh the data.
    if (agentId === 'analysis' || agentId === 'analysis_agent') {
        if (typeof window.showSection === 'function') {
            window.showSection('analysis');
        }
        if (window.appController) {
            // Give the UI a tiny delay to switch sections before loading data
            setTimeout(() => {
                if (window.appController.refreshAnalysis) {
                    window.appController.refreshAnalysis();
                } else if (window.appController.loadAnalysisData) {
                    window.appController.loadAnalysisData();
                }
            }, 200);
        }
    }
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

// Upload CSV file and trigger data processing task on backend
function uploadCSV() {
    alert('Please select a CSV file to upload for data processing.');
    // create a hidden file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv,text/csv';
    input.style.display = 'none';

    input.addEventListener('change', async (event) => {
        const file = event.target.files && event.target.files[0];
        if (!file) return;

        // simple file size guard (e.g., 10 MB)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            alert('Selected file is too large. Please upload a file smaller than 10 MB.');
            return;
        }

        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const text = e.target.result;

                // Show a quick UI notification
                if (agentManager) agentManager.showNotification('Uploading CSV and queuing data processing...', 'info');

                // POST to backend as a data_processing task with CSV content in parameters
                // Backend currently accepts /api/tasks JSON; we include csv text in parameters
                const payload = {
                    type: 'data_processing',
                    parameters: {
                        filename: file.name,
                        csv: text
                    }
                };

                const resp = await fetch(`${API_BASE_URL}/api/tasks`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!resp.ok) {
                    const body = await resp.text();
                    throw new Error(`Upload failed: ${resp.status} ${body}`);
                }

                const data = await resp.json();

                // Optionally reflect in the local task queue
                if (agentManager) {
                    agentManager.addTask({ name: `Upload: ${file.name}`, type: 'data_processing', parameters: { filename: file.name } });
                    
                    // Show success message
                    if (data.status === 'success') {
                        agentManager.showNotification('CSV uploaded and processing started!', 'success');
                        
                        // If analysis task ID is available, monitor its progress
                        if (data.analysis_task_id) {
                            agentManager.monitorAnalysisProgress(data.analysis_task_id, file.name);
                        }
                    } else {
                        agentManager.showNotification('CSV uploaded and task queued (backend id: ' + (data.task_id || '?') + ')', 'success');
                    }
                    
                    agentManager.updateTaskQueueUI();
                } else {
                    alert('CSV uploaded and task queued.');
                }

            } catch (err) {
                console.error('uploadCSV error', err);
                if (agentManager) agentManager.showNotification('CSV upload failed: ' + err.message, 'danger');
                else alert('CSV upload failed: ' + err.message);
            }
        };

        reader.onerror = (err) => {
            console.error('FileReader error', err);
            if (agentManager) agentManager.showNotification('Failed to read file', 'danger');
        };

        reader.readAsText(file);
    });

    // attach and click
    document.body.appendChild(input);
    input.click();

    // cleanup after a short delay
    setTimeout(() => {
        document.body.removeChild(input);
    }, 2000);
}
