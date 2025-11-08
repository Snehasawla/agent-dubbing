/**
 * Main Application Controller
 * Handles navigation, UI interactions, and overall application flow
 */

const MAIN_API_BASE_URL = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://localhost:5000';

class AppController {
    constructor() {
        this.currentSection = 'dashboard';
        this.agentManager = null;
        this.dashboardManager = null;
        this.analysisProgressInterval = null;
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
            const response = await fetch(`${MAIN_API_BASE_URL}/api/status`);
            const status = await response.json();
            this.updateSystemStatus(status);
        } catch (error) {
            console.error('Error loading system status:', error);
        }
    }

    async loadAgentStatus() {
        try {
            const response = await fetch(`${MAIN_API_BASE_URL}/api/agents`);
            const agents = await response.json();
            this.updateAgentStatus(agents);
        } catch (error) {
            console.error('Error loading agent status:', error);
        }
    }

    async loadTaskQueue() {
        try {
            const response = await fetch(`${MAIN_API_BASE_URL}/api/tasks`);
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

        if (sectionName === 'analysis') {
            this.startAnalysisProgressPolling();
            // Small delay to ensure section is visible before loading charts
            setTimeout(() => {
                this.loadAnalysisData();
            }, 100);
        } else {
            this.stopAnalysisProgressPolling();
        }
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
        // Load analysis data - prioritize uploaded analysis results
        try {
            // First, try to get uploaded analysis results
            const resultsResponse = await fetch(`${MAIN_API_BASE_URL}/api/results`);
            const allResults = await resultsResponse.json();

            // Check for uploaded analysis results (thesis or papers)
            let uploadedAnalysis = null;
            let datasetType = null;

            if (allResults.thesis_uploaded_analysis) {
                uploadedAnalysis = allResults.thesis_uploaded_analysis;
                datasetType = 'thesis';
            } else if (allResults.papers_uploaded_analysis) {
                uploadedAnalysis = allResults.papers_uploaded_analysis;
                datasetType = 'papers';
            }

            if (uploadedAnalysis && !uploadedAnalysis.error) {
                // Display uploaded analysis results
                this.displayUploadedAnalysis(uploadedAnalysis, datasetType);
            } else {
                // Fallback to default analysis
                const [thesisResponse, trendsResponse] = await Promise.all([
                    fetch(`${MAIN_API_BASE_URL}/api/analysis/thesis`),
                    fetch(`${MAIN_API_BASE_URL}/api/analysis/trends`)
                ]);

                const thesisData = await thesisResponse.json();
                const trendsData = await trendsResponse.json();

                this.displayAnalysisData(thesisData, trendsData);
            }

            this.loadAnalysisProgress();
        } catch (error) {
            console.error('Error loading analysis data:', error);
            this.showAnalysisError(error);
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

    displayUploadedAnalysis(analysisData, datasetType) {
        const container = document.getElementById('analysisCharts');
        if (!container) return;

        // Create comprehensive analysis display
        container.innerHTML = `
            <div class="row mb-4">
                <div class="col-md-12">
                    <div class="card bg-dark">
                        <div class="card-header">
                            <h5><i class="fas fa-info-circle me-2"></i>Dataset Overview</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="metric-card">
                                        <div class="metric-value">${analysisData.total_rows || 0}</div>
                                        <div>Total Rows</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="metric-card">
                                        <div class="metric-value">${analysisData.total_columns || 0}</div>
                                        <div>Total Columns</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="metric-card">
                                        <div class="metric-value">${datasetType || 'Unknown'}</div>
                                        <div>Dataset Type</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="metric-card">
                                        <div class="metric-value">${(analysisData.data_quality?.null_percentage || 0).toFixed(2)}%</div>
                                        <div>Null Percentage</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card bg-dark">
                        <div class="card-header">
                            <h5><i class="fas fa-chart-line me-2"></i>Data Quality Metrics</h5>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li class="mb-2">
                                    <strong>Null Percentage:</strong> 
                                    <span class="badge ${(analysisData.data_quality?.null_percentage || 0) < 5 ? 'bg-success' : 'bg-warning'}">
                                        ${(analysisData.data_quality?.null_percentage || 0).toFixed(2)}%
                                    </span>
                                </li>
                                <li class="mb-2">
                                    <strong>Duplicate Rows:</strong> 
                                    <span class="badge ${(analysisData.data_quality?.duplicate_rows || 0) === 0 ? 'bg-success' : 'bg-warning'}">
                                        ${analysisData.data_quality?.duplicate_rows || 0}
                                    </span>
                                </li>
                                <li class="mb-2">
                                    <strong>Columns:</strong> ${analysisData.columns?.length || 0}
                                </li>
                            </ul>
                            ${analysisData.data_quality?.unique_values_per_column ? `
                                <h6 class="mt-3">Unique Values per Column:</h6>
                                <div class="table-responsive" style="max-height: 200px; overflow-y: auto;">
                                    <table class="table table-sm table-dark">
                                        <thead>
                                            <tr>
                                                <th>Column</th>
                                                <th>Unique Values</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${Object.entries(analysisData.data_quality.unique_values_per_column).slice(0, 10).map(([col, count]) => `
                                                <tr>
                                                    <td>${col}</td>
                                                    <td>${count}</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card bg-dark">
                        <div class="card-header">
                            <h5><i class="fas fa-table me-2"></i>Column Information</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive" style="max-height: 300px; overflow-y: auto;">
                                <table class="table table-sm table-dark">
                                    <thead>
                                        <tr>
                                            <th>Column Name</th>
                                            <th>Data Type</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${analysisData.columns?.map(col => `
                                            <tr>
                                                <td>${col}</td>
                                                <td><span class="badge bg-info">${analysisData.data_types?.[col] || 'unknown'}</span></td>
                                            </tr>
                                        `).join('') || '<tr><td colspan="2">No columns found</td></tr>'}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            ${analysisData.basic_statistics && Object.keys(analysisData.basic_statistics).length > 0 ? `
                <div class="row mb-4">
                    <div class="col-md-12">
                        <div class="card bg-dark">
                            <div class="card-header">
                                <h5><i class="fas fa-calculator me-2"></i>Basic Statistics (Numeric Columns)</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-sm table-dark">
                                        <thead>
                                            <tr>
                                                <th>Column</th>
                                                <th>Count</th>
                                                <th>Mean</th>
                                                <th>Std</th>
                                                <th>Min</th>
                                                <th>25%</th>
                                                <th>50%</th>
                                                <th>75%</th>
                                                <th>Max</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${Object.entries(analysisData.basic_statistics).map(([col, stats]) => `
                                                <tr>
                                                    <td><strong>${col}</strong></td>
                                                    <td>${stats.count?.toFixed(0) || 'N/A'}</td>
                                                    <td>${stats.mean?.toFixed(2) || 'N/A'}</td>
                                                    <td>${stats.std?.toFixed(2) || 'N/A'}</td>
                                                    <td>${stats.min?.toFixed(2) || 'N/A'}</td>
                                                    <td>${stats['25%']?.toFixed(2) || 'N/A'}</td>
                                                    <td>${stats['50%']?.toFixed(2) || 'N/A'}</td>
                                                    <td>${stats['75%']?.toFixed(2) || 'N/A'}</td>
                                                    <td>${stats.max?.toFixed(2) || 'N/A'}</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            ` : ''}

            ${this.getDatasetSpecificAnalysis(analysisData, datasetType)}

            ${analysisData.insights && analysisData.insights.length > 0 ? `
                <div class="row mb-4">
                    <div class="col-md-12">
                        <div class="card bg-dark">
                            <div class="card-header">
                                <h5><i class="fas fa-lightbulb me-2"></i>Insights</h5>
                            </div>
                            <div class="card-body">
                                <ul class="list-group list-group-flush">
                                    ${analysisData.insights.map(insight => `
                                        <li class="list-group-item bg-dark text-light">${insight}</li>
                                    `).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            ` : ''}

            <div class="row">
                <div class="col-md-12">
                    <div class="card bg-dark">
                        <div class="card-header">
                            <h5><i class="fas fa-file-alt me-2"></i>Analysis Details</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>File Path:</strong> ${analysisData.file_path || 'N/A'}</p>
                            <p><strong>Dataset Type:</strong> <span class="badge bg-primary">${analysisData.dataset_type || 'Unknown'}</span></p>
                            <button class="btn btn-primary mt-2" onclick="window.appController.refreshAnalysis()">
                                <i class="fas fa-sync-alt me-2"></i>Refresh Analysis
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Create charts if we have distribution data
        this.createAnalysisCharts(analysisData, datasetType);
    }

    getDatasetSpecificAnalysis(analysisData, datasetType) {
        if (datasetType === 'thesis') {
            return `
                ${analysisData.level_distribution ? `
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <div class="card bg-dark">
                                <div class="card-header">
                                    <h5><i class="fas fa-layer-group me-2"></i>Level Distribution</h5>
                                </div>
                                <div class="card-body">
                                    <div id="levelDistributionChart" style="height: 300px;"></div>
                                </div>
                            </div>
                        </div>
                ` : ''}
                ${analysisData.priority_distribution ? `
                        <div class="col-md-6">
                            <div class="card bg-dark">
                                <div class="card-header">
                                    <h5><i class="fas fa-star me-2"></i>Priority Distribution</h5>
                                </div>
                                <div class="card-body">
                                    <div id="priorityDistributionChart" style="height: 300px;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                ` : ''}
                ${analysisData.difficulty_stats ? `
                    <div class="row mb-4">
                        <div class="col-md-12">
                            <div class="card bg-dark">
                                <div class="card-header">
                                    <h5><i class="fas fa-chart-bar me-2"></i>Difficulty Statistics</h5>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <strong>Mean:</strong> ${analysisData.difficulty_stats.mean?.toFixed(2) || 'N/A'}
                                        </div>
                                        <div class="col-md-3">
                                            <strong>Median:</strong> ${analysisData.difficulty_stats['50%']?.toFixed(2) || 'N/A'}
                                        </div>
                                        <div class="col-md-3">
                                            <strong>Min:</strong> ${analysisData.difficulty_stats.min?.toFixed(2) || 'N/A'}
                                        </div>
                                        <div class="col-md-3">
                                            <strong>Max:</strong> ${analysisData.difficulty_stats.max?.toFixed(2) || 'N/A'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                ` : ''}
            `;
        } else if (datasetType === 'papers') {
            return `
                ${analysisData.year_distribution ? `
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <div class="card bg-dark">
                                <div class="card-header">
                                    <h5><i class="fas fa-calendar me-2"></i>Year Distribution</h5>
                                </div>
                                <div class="card-body">
                                    <div id="yearDistributionChart" style="height: 300px;"></div>
                                </div>
                            </div>
                        </div>
                ` : ''}
                ${analysisData.domain_distribution ? `
                        <div class="col-md-6">
                            <div class="card bg-dark">
                                <div class="card-header">
                                    <h5><i class="fas fa-tags me-2"></i>Domain Distribution</h5>
                                </div>
                                <div class="card-body">
                                    <div id="domainDistributionChart" style="height: 300px;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                ` : ''}
            `;
        }
        return '';
    }

    createAnalysisCharts(analysisData, datasetType) {
        // Create charts using Plotly if available
        if (typeof Plotly === 'undefined') {
            console.warn('Plotly not available, skipping charts');
            return;
        }

        // Level distribution chart
        if (analysisData.level_distribution) {
            const levelData = [{
                x: Object.keys(analysisData.level_distribution),
                y: Object.values(analysisData.level_distribution),
                type: 'bar',
                marker: { color: '#3498db' }
            }];
            const levelLayout = {
                title: 'Level Distribution',
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#ecf0f1' }
            };
            Plotly.newPlot('levelDistributionChart', levelData, levelLayout, {responsive: true});
        }

        // Priority distribution chart
        if (analysisData.priority_distribution) {
            const priorityData = [{
                labels: Object.keys(analysisData.priority_distribution),
                values: Object.values(analysisData.priority_distribution),
                type: 'pie',
                marker: { colors: ['#e74c3c', '#f39c12', '#27ae60'] }
            }];
            const priorityLayout = {
                title: 'Priority Distribution',
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#ecf0f1' }
            };
            Plotly.newPlot('priorityDistributionChart', priorityData, priorityLayout, {responsive: true});
        }

        // Year distribution chart
        if (analysisData.year_distribution) {
            const yearData = [{
                x: Object.keys(analysisData.year_distribution).sort(),
                y: Object.keys(analysisData.year_distribution).sort().map(k => analysisData.year_distribution[k]),
                type: 'bar',
                marker: { color: '#3498db' }
            }];
            const yearLayout = {
                title: 'Year Distribution',
                xaxis: { title: 'Year' },
                yaxis: { title: 'Count' },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#ecf0f1' }
            };
            Plotly.newPlot('yearDistributionChart', yearData, yearLayout, {responsive: true});
        }

        // Domain distribution chart
        if (analysisData.domain_distribution) {
            const domainData = [{
                x: Object.values(analysisData.domain_distribution),
                y: Object.keys(analysisData.domain_distribution),
                type: 'bar',
                orientation: 'h',
                marker: { color: '#3498db' }
            }];
            const domainLayout = {
                title: 'Domain Distribution',
                xaxis: { title: 'Count' },
                yaxis: { title: 'Domain' },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#ecf0f1' }
            };
            Plotly.newPlot('domainDistributionChart', domainData, domainLayout, {responsive: true});
        }
    }

    showAnalysisError(error) {
        const container = document.getElementById('analysisCharts');
        if (!container) return;

        container.innerHTML = `
            <div class="alert alert-danger">
                <h5><i class="fas fa-exclamation-triangle me-2"></i>Error Loading Analysis</h5>
                <p>${error.message || 'Failed to load analysis data. Please try uploading a file first.'}</p>
                <button class="btn btn-primary" onclick="window.appController.loadAnalysisData()">
                    <i class="fas fa-redo me-2"></i>Retry
                </button>
            </div>
        `;
    }

    refreshAnalysis() {
        this.loadAnalysisData();
        this.startAnalysisProgressPolling();
    }

    async loadReportsData() {
        // Load reports data
        try {
            const response = await fetch(`${MAIN_API_BASE_URL}/api/results`);
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
        this.stopAnalysisProgressPolling();
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
            const response = await fetch(`${MAIN_API_BASE_URL}/api/workflow/start`, {
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
            const response = await fetch(`${MAIN_API_BASE_URL}/api/tasks`, {
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

    async loadAnalysisProgress() {
        const agentContainer = document.getElementById('analysisAgentStatus');
        if (!agentContainer) return;

        try {
            const [agentResp, tasksResp, graphResp] = await Promise.all([
                fetch(`${MAIN_API_BASE_URL}/api/agents/analysis/progress`),
                fetch(`${MAIN_API_BASE_URL}/api/tasks`),
                fetch(`${MAIN_API_BASE_URL}/api/graph/structure`).catch(error => {
                    console.warn('Graph inspection endpoint unavailable:', error);
                    return null;
                })
            ]);

            const agentData = agentResp?.ok ? await agentResp.json() : null;
            const taskData = tasksResp?.ok ? await tasksResp.json() : null;
            const graphData = graphResp && graphResp.ok ? await graphResp.json() : null;

            this.renderAnalysisAgentStatus(agentData);
            this.renderAnalysisTaskList(taskData);
            this.renderAnalysisLogs(agentData?.recent_logs || []);
            this.renderAgentGraph(graphData);
        } catch (error) {
            console.error('Error loading analysis progress:', error);
            this.renderAnalysisAgentStatus({ error: error.message });
            this.renderAgentGraph(null);
        }
    }

    renderAnalysisAgentStatus(agentData) {
        const container = document.getElementById('analysisAgentStatus');
        const badge = document.getElementById('analysisAgentStatusBadge');
        if (!container) return;

        if (!agentData || agentData.error) {
            container.innerHTML = `<p class="text-warning mb-0">${agentData?.error || 'Unable to load analysis agent status.'}</p>`;
            if (badge) {
                badge.className = 'badge bg-secondary';
                badge.textContent = 'UNKNOWN';
            }
            return;
        }

        const status = (agentData.status || 'idle').toLowerCase();
        const progress = agentData.progress ?? 0;
        const currentTask = agentData.task_details?.task_type || agentData.current_task || 'N/A';
        const datasetType = agentData.task_details?.dataset_type || '—';
        const cleanedFile = agentData.task_details?.cleaned_file || '—';

        const statusClass = status === 'busy' ? 'bg-info'
            : status === 'idle' ? 'bg-success'
            : status === 'error' ? 'bg-danger'
            : 'bg-secondary';

        if (badge) {
            badge.className = `badge ${statusClass}`;
            badge.textContent = status.toUpperCase();
        }

        container.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <div>
                    <h6 class="mb-1">${agentData.agent_name || 'Analysis Agent'}</h6>
                    <small class="text-muted">Task: ${currentTask}</small>
                </div>
                <div class="text-end">
                    <small class="text-muted">Progress</small>
                    <div class="progress" style="width: 140px; height: 6px;">
                        <div class="progress-bar" role="progressbar" style="width: ${progress}%"></div>
                    </div>
                    <small class="text-muted">${progress}%</small>
                </div>
            </div>
            <dl class="row mb-0">
                <dt class="col-5 text-muted">Dataset</dt>
                <dd class="col-7">${datasetType}</dd>
                <dt class="col-5 text-muted">Cleaned File</dt>
                <dd class="col-7 text-truncate" title="${cleanedFile}">${cleanedFile}</dd>
                <dt class="col-5 text-muted">Started</dt>
                <dd class="col-7">${agentData.task_details?.started_at ? new Date(agentData.task_details.started_at).toLocaleString() : '—'}</dd>
            </dl>
        `;
    }

    renderAnalysisTaskList(taskData) {
        const container = document.getElementById('analysisTaskList');
        if (!container) return;

        if (!taskData) {
            container.innerHTML = '<p class="text-warning mb-0">Unable to load task queue.</p>';
            return;
        }

        const activeTasks = (taskData.active || []).filter(task => ['statistical_analysis', 'chart_generation'].includes(task.type));
        const queuedTasks = (taskData.queued || []).filter(task => ['statistical_analysis', 'chart_generation'].includes(task.type));
        const completedTasks = (taskData.completed || [])
            .filter(task => ['statistical_analysis', 'chart_generation'].includes(task.type))
            .slice(-5)
            .reverse();

        const renderTask = (task, statusLabel, badgeClass) => {
            const datasetLabel = task.parameters?.dataset_type ? `<span class="badge bg-secondary ms-2">${task.parameters.dataset_type}</span>` : '';
            const description = task.parameters?.cleaned_file || task.parameters?.input_file || task.id;
            return `
                <li class="list-group-item bg-dark d-flex justify-content-between align-items-start">
                    <div class="me-3">
                        <div><strong>${task.type}</strong>${datasetLabel}</div>
                        <small class="text-muted">${description}</small>
                    </div>
                    <span class="badge ${badgeClass}">${statusLabel}</span>
                </li>
            `;
        };

        const sections = [];

        if (activeTasks.length) {
            sections.push(`
                <h6 class="text-info">Active</h6>
                <ul class="list-group list-group-flush mb-3">
                    ${activeTasks.map(task => renderTask(task, 'In Progress', 'bg-info')).join('')}
                </ul>
            `);
        }

        if (queuedTasks.length) {
            sections.push(`
                <h6 class="text-warning">Queued</h6>
                <ul class="list-group list-group-flush mb-3">
                    ${queuedTasks.slice(0, 5).map(task => renderTask(task, 'Queued', 'bg-warning text-dark')).join('')}
                </ul>
            `);
        }

        if (completedTasks.length) {
            sections.push(`
                <h6 class="text-success">Recently Completed</h6>
                <ul class="list-group list-group-flush">
                    ${completedTasks.map(task => renderTask(task, 'Done', 'bg-success')).join('')}
                </ul>
            `);
        }

        container.innerHTML = sections.length ? sections.join('') : '<p class="text-muted mb-0">No analysis tasks at the moment.</p>';
    }

    renderAnalysisLogs(logs) {
        const container = document.getElementById('analysisLogs');
        if (!container) return;

        if (!logs || !logs.length) {
            container.innerHTML = '<p class="text-muted mb-0">No recent logs.</p>';
            return;
        }

        const levelClass = level => {
            switch ((level || 'info').toLowerCase()) {
                case 'error':
                    return 'text-danger';
                case 'warning':
                    return 'text-warning';
                case 'success':
                    return 'text-success';
                default:
                    return 'text-info';
            }
        };

        container.innerHTML = `
            <ul class="list-unstyled mb-0">
                ${logs.slice(-10).reverse().map(log => `
                    <li class="mb-2">
                        <div class="d-flex justify-content-between">
                            <small class="text-muted">${new Date(log.timestamp).toLocaleTimeString()}</small>
                            <small class="${levelClass(log.level)}">${(log.level || 'info').toUpperCase()}</small>
                        </div>
                        <div>${log.message}</div>
                    </li>
                `).join('')}
            </ul>
        `;
    }

    renderAgentGraph(graphData) {
        const messageEl = document.getElementById('agentGraphMessage');
        const badgeEl = document.getElementById('agentGraphStatusBadge');
        const mermaidContainer = document.getElementById('agentGraphMermaid');

        if (!messageEl || !badgeEl || !mermaidContainer) {
            return;
        }

        if (!graphData) {
            badgeEl.className = 'badge bg-warning text-dark';
            badgeEl.textContent = 'Unavailable';
            messageEl.className = 'text-warning';
            messageEl.textContent = 'Unable to load orchestration graph metadata.';
            mermaidContainer.innerHTML = '';
            return;
        }

        const isActive = Boolean(graphData.available);
        const hasMermaid = Boolean(graphData.mermaid);

        if (!isActive && !hasMermaid) {
            badgeEl.className = 'badge bg-secondary';
            badgeEl.textContent = 'Disabled';
            messageEl.className = 'text-muted';
            messageEl.textContent = graphData.message || 'Install LangGraph to enable orchestration visualization.';
            mermaidContainer.innerHTML = '';
            return;
        }

        if (!isActive && hasMermaid) {
            badgeEl.className = 'badge bg-info';
            badgeEl.textContent = 'Fallback';
            messageEl.className = 'text-muted';
            const summary = graphData.graph_summary || {};
            messageEl.textContent = `${graphData.message || 'Static pipeline preview.'} Nodes: ${summary.total_nodes ?? graphData.nodes?.length ?? 0} · Edges: ${summary.total_edges ?? graphData.edges?.length ?? 0}`;
        } else {
            badgeEl.className = 'badge bg-success';
            badgeEl.textContent = 'Active';
            messageEl.className = 'text-muted';
            const summary = graphData.graph_summary || {};
            messageEl.textContent = `Nodes: ${summary.total_nodes ?? graphData.nodes?.length ?? 0} · Edges: ${summary.total_edges ?? graphData.edges?.length ?? 0}`;
        }

        if (graphData.mermaid && window.mermaid) {
            mermaidContainer.innerHTML = `<div class="mermaid">${graphData.mermaid}</div>`;
            try {
                window.mermaid.init(undefined, mermaidContainer.querySelectorAll('.mermaid'));
            } catch (err) {
                console.error('Failed to render mermaid diagram:', err);
                messageEl.className = 'text-warning';
                messageEl.textContent = 'Graph metadata loaded, but rendering failed.';
            }
        } else {
            const nodesList = (graphData.nodes || []).map(node => `${node.label} (${node.key})`).join(', ');
            mermaidContainer.innerHTML = `<code>${nodesList || 'No nodes defined.'}</code>`;
        }
    }

    selectNode(nodeId) {
        // Implement node selection logic
        console.log('Selected node:', nodeId);
    }

    selectEdge(sourceId, targetId) {
        // Implement edge selection logic
        console.log('Selected edge:', sourceId, '->', targetId);
    }

    startAnalysisProgressPolling() {
        if (this.analysisProgressInterval) return;
        this.loadAnalysisProgress();
        this.analysisProgressInterval = setInterval(() => this.loadAnalysisProgress(), 5000);
    }

    stopAnalysisProgressPolling() {
        if (this.analysisProgressInterval) {
            clearInterval(this.analysisProgressInterval);
            this.analysisProgressInterval = null;
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

function refreshAnalysis() {
    if (window.appController) {
        window.appController.refreshAnalysis();
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
    window.refreshAnalysis = refreshAnalysis;
    window.toggleFullscreen = toggleFullscreen;
});

// Export for use in other modules
window.AppController = AppController;
