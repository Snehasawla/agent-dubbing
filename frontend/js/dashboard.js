/**
 * Dashboard Management and Real-time Updates
 * Handles dashboard visualizations and real-time data updates
 */

class DashboardManager {
    constructor() {
        this.charts = {};
        this.updateInterval = null;
        this.isRealTimeEnabled = true;
        this.init();
    }

    init() {
        this.initializeCharts();
        this.startRealTimeUpdates();
        this.setupEventListeners();
    }

    initializeCharts() {
        // Initialize agent performance chart
        this.createAgentPerformanceChart();
        
        // Initialize research trends chart
        this.createResearchTrendsChart();
        
        // Initialize analysis charts
        this.createAnalysisCharts();
    }

    createAgentPerformanceChart() {
        const data = [
            {
                x: ['Data Agent', 'Analysis Agent', 'Visualization Agent', 'Report Agent'],
                y: [85, 72, 90, 45],
                type: 'bar',
                marker: {
                    color: ['#3498db', '#e74c3c', '#27ae60', '#f39c12']
                },
                text: ['85%', '72%', '90%', '45%'],
                textposition: 'auto'
            }
        ];

        const layout = {
            title: 'Agent Performance Metrics',
            xaxis: { title: 'Agents' },
            yaxis: { title: 'Performance (%)' },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#ecf0f1' }
        };

        Plotly.newPlot('agentPerformanceChart', data, layout, {responsive: true});
    }

    createResearchTrendsChart() {
        const years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023];
        const papers = [2, 3, 4, 5, 6, 7, 8, 9, 10];
        const citations = [50, 75, 100, 125, 150, 175, 200, 225, 250];

        const data = [
            {
                x: years,
                y: papers,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Papers Published',
                line: { color: '#3498db', width: 3 },
                marker: { size: 8 }
            },
            {
                x: years,
                y: citations,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Total Citations',
                yaxis: 'y2',
                line: { color: '#e74c3c', width: 3 },
                marker: { size: 8 }
            }
        ];

        const layout = {
            title: 'Research Trends Over Time',
            xaxis: { title: 'Year' },
            yaxis: { title: 'Papers Published', side: 'left' },
            yaxis2: { title: 'Total Citations', side: 'right', overlaying: 'y' },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#ecf0f1' },
            legend: { x: 0, y: 1 }
        };

        Plotly.newPlot('researchTrendsChart', data, layout, {responsive: true});
    }

    createAnalysisCharts() {
        // Create multiple analysis charts
        this.createThesisStructureChart();
        this.createDomainDistributionChart();
        this.createDifficultyAnalysisChart();
    }

    createThesisStructureChart() {
        const data = [
            {
                labels: ['High Priority', 'Medium Priority', 'Low Priority'],
                values: [8, 12, 4],
                type: 'pie',
                marker: {
                    colors: ['#e74c3c', '#f39c12', '#27ae60']
                }
            }
        ];

        const layout = {
            title: 'Thesis Section Priorities',
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#ecf0f1' }
        };

        Plotly.newPlot('thesisStructureChart', data, layout, {responsive: true});
    }

    createDomainDistributionChart() {
        const domains = ['Software Engineering', 'Machine Learning', 'AI Systems', 'Programming Languages', 'Security', 'HCI', 'NLP', 'Systems'];
        const counts = [8, 6, 4, 3, 3, 3, 3, 2];

        const data = [
            {
                x: counts,
                y: domains,
                type: 'bar',
                orientation: 'h',
                marker: {
                    color: '#3498db'
                }
            }
        ];

        const layout = {
            title: 'Research Domain Distribution',
            xaxis: { title: 'Number of Papers' },
            yaxis: { title: 'Domains' },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#ecf0f1' }
        };

        Plotly.newPlot('domainDistributionChart', data, layout, {responsive: true});
    }

    createDifficultyAnalysisChart() {
        const sections = ['Abstract', 'Introduction', 'Methodology', 'Results', 'Discussion', 'Conclusion'];
        const difficulty = [2, 3, 5, 4, 3, 2];
        const priority = [2, 4, 5, 5, 4, 3];

        const data = [
            {
                x: difficulty,
                y: priority,
                mode: 'markers+text',
                type: 'scatter',
                text: sections,
                textposition: 'top center',
                marker: {
                    size: 15,
                    color: difficulty,
                    colorscale: 'Viridis',
                    showscale: true,
                    colorbar: { title: 'Difficulty Score' }
                }
            }
        ];

        const layout = {
            title: 'Section Difficulty vs Priority Analysis',
            xaxis: { title: 'Difficulty Score' },
            yaxis: { title: 'Priority Level' },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#ecf0f1' }
        };

        Plotly.newPlot('difficultyAnalysisChart', data, layout, {responsive: true});
    }

    startRealTimeUpdates() {
        if (this.isRealTimeEnabled) {
            this.updateInterval = setInterval(() => {
                this.updateDashboardData();
            }, 5000); // Update every 5 seconds
        }
    }

    stopRealTimeUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    updateDashboardData() {
        // Update metrics
        this.updateMetrics();
        
        // Update charts with new data
        this.updateCharts();
        
        // Update agent status
        this.updateAgentStatus();
    }

    updateMetrics() {
        // Simulate real-time metric updates
        const metrics = {
            totalSections: 24 + Math.floor(Math.random() * 5),
            totalPapers: 40 + Math.floor(Math.random() * 10),
            activeAgents: Math.floor(Math.random() * 4) + 1,
            completedTasks: 12 + Math.floor(Math.random() * 8)
        };

        Object.entries(metrics).forEach(([key, value]) => {
            const element = document.getElementById(key);
            if (element) {
                // Animate the number change
                this.animateNumber(element, parseInt(element.textContent) || 0, value);
            }
        });
    }

    animateNumber(element, start, end) {
        const duration = 1000;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = Math.floor(start + (end - start) * progress);
            element.textContent = current;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    updateCharts() {
        // Update agent performance chart with new data
        this.updateAgentPerformanceChart();
        
        // Update research trends chart
        this.updateResearchTrendsChart();
    }

    updateAgentPerformanceChart() {
        // Generate new performance data
        const newData = [
            {
                x: ['Data Agent', 'Analysis Agent', 'Visualization Agent', 'Report Agent'],
                y: [
                    80 + Math.random() * 20,
                    70 + Math.random() * 20,
                    85 + Math.random() * 15,
                    40 + Math.random() * 30
                ],
                type: 'bar',
                marker: {
                    color: ['#3498db', '#e74c3c', '#27ae60', '#f39c12']
                }
            }
        ];

        Plotly.react('agentPerformanceChart', newData, {}, {responsive: true});
    }

    updateResearchTrendsChart() {
        // Generate new trend data
        const years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023];
        const papers = years.map(() => Math.floor(Math.random() * 5) + 5);
        const citations = years.map(() => Math.floor(Math.random() * 100) + 100);

        const newData = [
            {
                x: years,
                y: papers,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Papers Published',
                line: { color: '#3498db', width: 3 }
            },
            {
                x: years,
                y: citations,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Total Citations',
                yaxis: 'y2',
                line: { color: '#e74c3c', width: 3 }
            }
        ];

        Plotly.react('researchTrendsChart', newData, {}, {responsive: true});
    }

    updateAgentStatus() {
        // Update agent status indicators
        const agents = ['data', 'analysis', 'visualization', 'report'];
        agents.forEach(agentId => {
            const statusElement = document.querySelector(`[onclick="selectAgent('${agentId}')"] .agent-status`);
            if (statusElement) {
                const statuses = ['online', 'busy', 'offline'];
                const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
                statusElement.className = `agent-status ${randomStatus}`;
            }
        });
    }

    setupEventListeners() {
        // Add event listeners for dashboard controls
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="toggle-realtime"]')) {
                this.toggleRealTimeUpdates();
            }
        });
    }

    toggleRealTimeUpdates() {
        this.isRealTimeEnabled = !this.isRealTimeEnabled;
        
        if (this.isRealTimeEnabled) {
            this.startRealTimeUpdates();
            this.showNotification('Real-time updates enabled', 'success');
        } else {
            this.stopRealTimeUpdates();
            this.showNotification('Real-time updates disabled', 'warning');
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

    // API Integration methods
    async fetchData(endpoint) {
        try {
            const response = await fetch(`/api/${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error fetching data from ${endpoint}:`, error);
            return null;
        }
    }

    async loadThesisAnalysis() {
        const data = await this.fetchData('analysis/thesis');
        if (data) {
            this.updateThesisCharts(data);
        }
    }

    async loadTrendsAnalysis() {
        const data = await this.fetchData('analysis/trends');
        if (data) {
            this.updateTrendsCharts(data);
        }
    }

    updateThesisCharts(data) {
        // Update thesis-specific charts with real data
        if (data.level_distribution) {
            this.updateLevelDistributionChart(data.level_distribution);
        }
        
        if (data.priority_distribution) {
            this.updatePriorityDistributionChart(data.priority_distribution);
        }
    }

    updateTrendsCharts(data) {
        // Update trends charts with real data
        if (data.domain_distribution) {
            this.updateDomainDistributionChart(data.domain_distribution);
        }
    }

    updateLevelDistributionChart(levelData) {
        const data = [{
            x: Object.keys(levelData),
            y: Object.values(levelData),
            type: 'bar',
            marker: { color: '#3498db' }
        }];

        const layout = {
            title: 'Thesis Section Level Distribution',
            xaxis: { title: 'Level' },
            yaxis: { title: 'Count' },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#ecf0f1' }
        };

        Plotly.newPlot('levelDistributionChart', data, layout, {responsive: true});
    }

    updatePriorityDistributionChart(priorityData) {
        const data = [{
            labels: Object.keys(priorityData),
            values: Object.values(priorityData),
            type: 'pie',
            marker: {
                colors: ['#e74c3c', '#f39c12', '#27ae60']
            }
        }];

        const layout = {
            title: 'Section Priority Distribution',
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#ecf0f1' }
        };

        Plotly.newPlot('priorityDistributionChart', data, layout, {responsive: true});
    }

    updateDomainDistributionChart(domainData) {
        const data = [{
            x: Object.values(domainData),
            y: Object.keys(domainData),
            type: 'bar',
            orientation: 'h',
            marker: { color: '#3498db' }
        }];

        const layout = {
            title: 'Research Domain Distribution',
            xaxis: { title: 'Number of Papers' },
            yaxis: { title: 'Domains' },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#ecf0f1' }
        };

        Plotly.newPlot('domainDistributionChart', data, layout, {responsive: true});
    }

    // Cleanup method
    destroy() {
        this.stopRealTimeUpdates();
    }
}

// Global dashboard manager instance
let dashboardManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    dashboardManager = new DashboardManager();
});

// Global functions for UI interaction
function refreshDashboard() {
    if (dashboardManager) {
        dashboardManager.updateDashboardData();
        dashboardManager.showNotification('Dashboard refreshed', 'info');
    }
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}

// Export for use in other modules
window.DashboardManager = DashboardManager;
