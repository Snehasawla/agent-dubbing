# Debugging Agents Research Platform - User Guide

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge)
- 4GB RAM minimum (8GB recommended)
- 1GB free disk space

### Installation

1. **Clone or Download the Project**
   ```bash
   # If using git
   git clone <repository-url>
   cd debugging_agents_project
   
   # Or simply extract the project folder
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python run.py
   ```

4. **Access the Platform**
   - Open your web browser
   - Navigate to `http://localhost:8080`
   - The application will automatically open in your default browser

## User Interface Overview

### Main Dashboard

The main dashboard provides an overview of the system status and key metrics:

- **System Metrics**: Total sections, papers, active agents, completed tasks
- **Agent Performance Chart**: Visual representation of agent efficiency
- **Research Trends Chart**: Analysis of academic paper trends over time
- **Agent Activity Log**: Real-time log of agent activities

### Navigation

The left sidebar provides access to different sections:

- **Dashboard** (Ctrl+1): Main overview and metrics
- **Agents** (Ctrl+2): Multi-agent system management
- **Analysis** (Ctrl+3): Detailed analysis results
- **Reports** (Ctrl+4): Generated reports and exports
- **Settings** (Ctrl+5): System configuration

## Multi-Agent System

### Agent Types

#### 1. Data Agent
- **Purpose**: Processes and cleans research data
- **Capabilities**: Data validation, cleaning, preprocessing
- **Status Indicators**: 
  - 🟢 Online: Ready to process data
  - 🟡 Busy: Currently processing
  - 🔴 Offline: Unavailable

#### 2. Analysis Agent
- **Purpose**: Performs statistical analysis and generates insights
- **Capabilities**: Statistical analysis, trend analysis, correlation analysis
- **Status Indicators**: Same as Data Agent

#### 3. Visualization Agent
- **Purpose**: Creates interactive charts and visualizations
- **Capabilities**: Chart generation, dashboard updates, interactive plots
- **Status Indicators**: Same as Data Agent

#### 4. Report Agent
- **Purpose**: Generates comprehensive reports and documentation
- **Capabilities**: Report generation, PDF export, HTML export
- **Status Indicators**: Same as Data Agent

### Task Queue Management

The task queue shows all pending, active, and completed tasks:

- **Queued Tasks**: Waiting to be assigned to an agent
- **Active Tasks**: Currently being processed by an agent
- **Completed Tasks**: Successfully finished tasks

### Agent Interaction

1. **Select an Agent**: Click on any agent card to view details
2. **Monitor Progress**: Real-time progress bars show task completion
3. **View Logs**: Check agent activity logs for detailed information

## Data Analysis Features

### Thesis Structure Analysis

The platform analyzes thesis sections with the following metrics:

- **Section Levels**: Hierarchical organization (1-3 levels)
- **Priority Distribution**: High, Medium, Low priority sections
- **Difficulty Scores**: Complexity assessment (1-5 scale)
- **Content Analysis**: Figures, tables, equations, algorithms

### Research Trends Analysis

Academic paper analysis includes:

- **Domain Distribution**: Research areas and their representation
- **Year Trends**: Publication patterns over time
- **Citation Analysis**: Impact and influence metrics
- **Readability Scores**: Content accessibility assessment

### Interactive Visualizations

1. **Agent Performance Chart**
   - Bar chart showing agent efficiency
   - Real-time updates
   - Color-coded performance levels

2. **Research Trends Chart**
   - Dual-axis chart (papers vs citations)
   - Time series analysis
   - Interactive hover details

3. **Section Analysis Charts**
   - Pie charts for priority distribution
   - Scatter plots for difficulty vs priority
   - Bar charts for domain distribution

## Workflow Management

### Starting an Analysis Workflow

1. **Quick Start**: Click the "Start Analysis" button (floating action button)
2. **Manual Task Creation**: Use the API to create specific tasks
3. **Scheduled Analysis**: Configure automatic analysis intervals

### Workflow Steps

1. **Data Processing**: Raw data ingestion and cleaning
2. **Statistical Analysis**: Generate insights and trends
3. **Visualization Creation**: Build interactive charts
4. **Report Generation**: Create comprehensive reports

### Monitoring Progress

- **Real-time Updates**: Dashboard refreshes automatically
- **Progress Indicators**: Visual progress bars for each agent
- **Status Notifications**: Pop-up notifications for important events
- **Activity Logs**: Detailed log of all system activities

## Reports and Exports

### Available Reports

1. **Thesis Structure Report**
   - Section analysis and recommendations
   - Priority-based extraction guidelines
   - Content distribution insights

2. **Research Trends Report**
   - Domain analysis and trends
   - Citation impact assessment
   - Future research directions

3. **Agent Performance Report**
   - Multi-agent system efficiency
   - Task completion statistics
   - System optimization recommendations

### Export Formats

- **PDF Reports**: Professional formatted documents
- **HTML Dashboards**: Interactive web-based reports
- **CSV Data**: Raw analysis results
- **JSON API**: Programmatic access to results

## Settings and Configuration

### Agent Configuration

- **Processing Intervals**: Set data processing frequency
- **Update Frequency**: Configure visualization refresh rates
- **Resource Limits**: Set memory and CPU usage limits

### System Preferences

- **Real-time Updates**: Enable/disable live data updates
- **Auto-save**: Automatic report saving
- **Notifications**: Email and browser notifications
- **Theme**: Dark/light mode selection

### Data Management

- **Data Sources**: Configure input data locations
- **Output Directories**: Set report and export locations
- **Backup Settings**: Automatic data backup configuration

## Keyboard Shortcuts

- **Ctrl+1**: Switch to Dashboard
- **Ctrl+2**: Switch to Agents
- **Ctrl+3**: Switch to Analysis
- **Ctrl+4**: Switch to Reports
- **Ctrl+5**: Switch to Settings
- **Ctrl+R**: Refresh all data
- **F11**: Toggle fullscreen mode

## Troubleshooting

### Common Issues

#### 1. Application Won't Start
- **Check Python version**: Ensure Python 3.8+ is installed
- **Install dependencies**: Run `pip install -r requirements.txt`
- **Check port availability**: Ensure ports 5000 and 8080 are free

#### 2. Agents Not Responding
- **Check agent status**: Look for error indicators
- **Restart application**: Stop and restart the platform
- **Check logs**: Review agent activity logs for errors

#### 3. Data Not Loading
- **Verify data files**: Ensure CSV files are in the data directory
- **Check file permissions**: Ensure read access to data files
- **Validate data format**: Check CSV file structure

#### 4. Visualizations Not Displaying
- **Check browser compatibility**: Use modern browser
- **Enable JavaScript**: Ensure JavaScript is enabled
- **Clear browser cache**: Clear cache and reload

### Performance Optimization

1. **System Resources**
   - Close unnecessary applications
   - Ensure adequate RAM (8GB+ recommended)
   - Use SSD storage for better performance

2. **Browser Settings**
   - Enable hardware acceleration
   - Disable unnecessary extensions
   - Clear browser cache regularly

3. **Data Management**
   - Limit dataset size for better performance
   - Use processed data when possible
   - Regular cleanup of temporary files

## Support and Help

### Getting Help

1. **Documentation**: Check this user guide and architecture docs
2. **Logs**: Review system and agent logs for error details
3. **Console**: Check browser developer console for frontend errors

### Reporting Issues

When reporting issues, please include:

1. **System Information**: OS, Python version, browser
2. **Error Messages**: Complete error text and stack traces
3. **Steps to Reproduce**: Detailed steps that led to the issue
4. **Logs**: Relevant log files and console output

### Feature Requests

For new features or improvements:

1. **Describe the Feature**: Clear description of desired functionality
2. **Use Case**: Explain how it would benefit your workflow
3. **Priority**: Indicate importance level (Low/Medium/High)

## Best Practices

### Data Management

1. **Regular Backups**: Backup your data files regularly
2. **Data Validation**: Verify data quality before processing
3. **Incremental Updates**: Process data in manageable chunks

### Agent Usage

1. **Monitor Status**: Keep an eye on agent status and progress
2. **Resource Management**: Don't overload agents with too many tasks
3. **Error Handling**: Address agent errors promptly

### Analysis Workflow

1. **Start Small**: Begin with small datasets to test functionality
2. **Iterative Approach**: Refine analysis parameters iteratively
3. **Document Results**: Keep track of analysis results and insights

### System Maintenance

1. **Regular Updates**: Keep dependencies updated
2. **Log Monitoring**: Regularly check system logs
3. **Performance Monitoring**: Monitor system resource usage
