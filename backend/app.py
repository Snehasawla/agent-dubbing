"""
Flask Backend for Debugging Agents Research Platform
Provides API endpoints for multi-agent coordination and data management
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import threading
import time
from pathlib import Path

# Import our custom modules
import sys
sys.path.append('../src')
from data_processor import DataProcessor
from thesis_analyzer import ThesisAnalyzer

app = Flask(__name__)
CORS(app)

# Global instances
data_processor = DataProcessor()
thesis_analyzer = ThesisAnalyzer()
agent_status = {}
task_queue = []
completed_tasks = []

class AgentCoordinator:
    """Coordinates multiple agents for the debugging agents research platform"""
    
    def __init__(self):
        self.agents = {
            'data_agent': DataAgent(),
            'analysis_agent': AnalysisAgent(),
            'visualization_agent': VisualizationAgent(),
            'report_agent': ReportAgent()
        }
        self.task_queue = []
        self.active_tasks = {}
        self.results = {}
        
    def add_task(self, task_type, parameters=None):
        """Add a new task to the queue"""
        task = {
            'id': f"task_{int(time.time())}_{len(self.task_queue)}",
            'type': task_type,
            'parameters': parameters or {},
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
            'assigned_agent': None
        }
        self.task_queue.append(task)
        return task['id']
    
    def process_tasks(self):
        """Process tasks in the queue"""
        for task in self.task_queue:
            if task['status'] == 'queued':
                # Find available agent
                available_agent = self.find_available_agent(task['type'])
                if available_agent:
                    self.assign_task(task, available_agent)
    
    def find_available_agent(self, task_type):
        """Find an available agent for the task type"""
        for agent_id, agent in self.agents.items():
            if agent.can_handle_task(task_type) and agent.is_available():
                return agent_id
        return None
    
    def assign_task(self, task, agent_id):
        """Assign a task to an agent"""
        task['status'] = 'in_progress'
        task['assigned_agent'] = agent_id
        task['started_at'] = datetime.now().isoformat()
        
        agent = self.agents[agent_id]
        agent.execute_task(task)
        
        self.active_tasks[task['id']] = task
    
    def get_status(self):
        """Get overall system status"""
        return {
            'agents': {agent_id: agent.get_status() for agent_id, agent in self.agents.items()},
            'task_queue': len(self.task_queue),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(completed_tasks)
        }

class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, name, capabilities):
        self.name = name
        self.capabilities = capabilities
        self.status = 'idle'
        self.current_task = None
        self.progress = 0
        self.logs = []
    
    def can_handle_task(self, task_type):
        """Check if agent can handle a task type"""
        return task_type in self.capabilities
    
    def is_available(self):
        """Check if agent is available"""
        return self.status == 'idle'
    
    def get_status(self):
        """Get agent status"""
        return {
            'name': self.name,
            'status': self.status,
            'progress': self.progress,
            'current_task': self.current_task,
            'capabilities': self.capabilities
        }
    
    def execute_task(self, task):
        """Execute a task (to be overridden by subclasses)"""
        self.status = 'busy'
        self.current_task = task['id']
        self.progress = 0
        
        # Simulate task execution
        threading.Thread(target=self._simulate_task, args=(task,)).start()
    
    def _simulate_task(self, task):
        """Simulate task execution"""
        try:
            self.log(f"Starting task: {task['type']}")
            
            # Simulate progress
            for i in range(0, 101, 10):
                self.progress = i
                time.sleep(0.5)
                self.log(f"Progress: {i}%")
            
            # Mark task as completed
            task['status'] = 'completed'
            task['completed_at'] = datetime.now().isoformat()
            completed_tasks.append(task)
            
            if task['id'] in coordinator.active_tasks:
                del coordinator.active_tasks[task['id']]
            
            self.status = 'idle'
            self.current_task = None
            self.progress = 0
            
            self.log(f"Completed task: {task['type']}")
            
        except Exception as e:
            self.log(f"Error in task {task['type']}: {str(e)}", 'error')
            task['status'] = 'failed'
            task['error'] = str(e)
            self.status = 'idle'
            self.current_task = None
    
    def log(self, message, level='info'):
        """Add a log entry"""
        self.logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        })

class DataAgent(BaseAgent):
    """Handles data processing tasks"""
    
    def __init__(self):
        super().__init__('Data Agent', ['data_processing', 'data_cleaning', 'data_validation'])
    
    def execute_task(self, task):
        """Execute data processing task"""
        super().execute_task(task)
        
        if task['type'] == 'data_processing':
            # Process the thesis data
            try:
                data_processor.process_all()
                self.log("Data processing completed successfully")
            except Exception as e:
                self.log(f"Data processing failed: {str(e)}", 'error')

class AnalysisAgent(BaseAgent):
    """Handles analysis tasks"""
    
    def __init__(self):
        super().__init__('Analysis Agent', ['statistical_analysis', 'trend_analysis', 'correlation_analysis'])
    
    def execute_task(self, task):
        """Execute analysis task"""
        super().execute_task(task)
        
        if task['type'] == 'statistical_analysis':
            try:
                # Perform analysis
                thesis_analysis = thesis_analyzer.analyze_thesis_structure()
                trends_analysis = thesis_analyzer.analyze_research_trends()
                
                coordinator.results['thesis_analysis'] = thesis_analysis
                coordinator.results['trends_analysis'] = trends_analysis
                
                self.log("Statistical analysis completed")
            except Exception as e:
                self.log(f"Analysis failed: {str(e)}", 'error')

class VisualizationAgent(BaseAgent):
    """Handles visualization tasks"""
    
    def __init__(self):
        super().__init__('Visualization Agent', ['chart_generation', 'dashboard_update', 'interactive_plots'])
    
    def execute_task(self, task):
        """Execute visualization task"""
        super().execute_task(task)
        
        if task['type'] == 'chart_generation':
            try:
                # Generate visualizations
                thesis_analyzer.create_visualizations()
                thesis_analyzer.generate_interactive_dashboard()
                
                self.log("Visualizations generated successfully")
            except Exception as e:
                self.log(f"Visualization generation failed: {str(e)}", 'error')

class ReportAgent(BaseAgent):
    """Handles report generation tasks"""
    
    def __init__(self):
        super().__init__('Report Agent', ['report_generation', 'pdf_export', 'html_export'])
    
    def execute_task(self, task):
        """Execute report generation task"""
        super().execute_task(task)
        
        if task['type'] == 'report_generation':
            try:
                # Generate comprehensive report
                thesis_analysis, trends_analysis = thesis_analyzer.generate_report()
                
                coordinator.results['final_report'] = {
                    'thesis_analysis': thesis_analysis,
                    'trends_analysis': trends_analysis,
                    'generated_at': datetime.now().isoformat()
                }
                
                self.log("Report generated successfully")
            except Exception as e:
                self.log(f"Report generation failed: {str(e)}", 'error')

# Initialize coordinator
coordinator = AgentCoordinator()

# Start background task processing
def background_task_processor():
    """Background thread to process tasks"""
    while True:
        coordinator.process_tasks()
        time.sleep(2)

threading.Thread(target=background_task_processor, daemon=True).start()

# API Routes
@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get overall system status"""
    return jsonify(coordinator.get_status())

@app.route('/api/agents')
def get_agents():
    """Get all agents status"""
    return jsonify({agent_id: agent.get_status() for agent_id, agent in coordinator.agents.items()})

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    return jsonify({
        'queued': coordinator.task_queue,
        'active': list(coordinator.active_tasks.values()),
        'completed': completed_tasks[-10:]  # Last 10 completed tasks
    })

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    data = request.get_json()
    task_type = data.get('type')
    parameters = data.get('parameters', {})
    
    if not task_type:
        return jsonify({'error': 'Task type is required'}), 400
    
    task_id = coordinator.add_task(task_type, parameters)
    return jsonify({'task_id': task_id, 'status': 'queued'})

@app.route('/api/analysis/thesis')
def get_thesis_analysis():
    """Get thesis structure analysis"""
    try:
        analysis = thesis_analyzer.analyze_thesis_structure()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/trends')
def get_trends_analysis():
    """Get research trends analysis"""
    try:
        analysis = thesis_analyzer.analyze_research_trends()
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/summary')
def get_data_summary():
    """Get data summary statistics"""
    try:
        summary = data_processor.create_summary_statistics()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflow/start', methods=['POST'])
def start_workflow():
    """Start a comprehensive analysis workflow"""
    try:
        # Add multiple tasks to the queue
        tasks = [
            ('data_processing', {}),
            ('statistical_analysis', {}),
            ('chart_generation', {}),
            ('report_generation', {})
        ]
        
        task_ids = []
        for task_type, params in tasks:
            task_id = coordinator.add_task(task_type, params)
            task_ids.append(task_id)
        
        return jsonify({
            'message': 'Workflow started',
            'task_ids': task_ids,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results')
def get_results():
    """Get analysis results"""
    return jsonify(coordinator.results)

@app.route('/api/logs/<agent_id>')
def get_agent_logs(agent_id):
    """Get logs for a specific agent"""
    if agent_id in coordinator.agents:
        return jsonify(coordinator.agents[agent_id].logs)
    return jsonify({'error': 'Agent not found'}), 404

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('../reports', exist_ok=True)
    os.makedirs('../data/processed', exist_ok=True)
    
    print("🚀 Starting Debugging Agents Research Platform...")
    print("📊 Multi-agent system initialized")
    print("🌐 Web interface available at http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
