"""
Flask Backend for Debugging Agents Research Platform
Provides API endpoints for multi-agent coordination and data management
"""

from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import threading
import time
from pathlib import Path
import math

# Import our custom modules
import sys
sys.path.append('../src')
from data_processor import DataProcessor
from thesis_analyzer import ThesisAnalyzer
from data_agent import DataAgent
from orchestration import (
    graph_available as GRAPH_AVAILABLE,
    graph_execution_supported as GRAPH_EXECUTION_SUPPORTED,
    configure_graph_runtime,
    get_graph_metadata,
    run_graph_pipeline,
)

app = Flask(__name__)
# Allow all origins for every endpoint, and include common headers
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=False,
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-CSRFToken"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

# Configure upload settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'uploads')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global instances
data_processor = DataProcessor()
thesis_analyzer = ThesisAnalyzer()
data_agent = DataAgent()  # Create global data_agent instance
agent_status = {}
task_queue = []
completed_tasks = []

def make_serializable(obj):
    """Convert numpy/pandas types and NaN/Inf values into JSON-serializable primitives."""
    if isinstance(obj, dict):
        return {make_serializable(key): make_serializable(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [make_serializable(item) for item in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        value = float(obj)
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (np.ndarray,)):
        return [make_serializable(item) for item in obj.tolist()]
    return obj

class AgentCoordinator:
    """Coordinates multiple agents for the debugging agents research platform"""
    
    def __init__(self):
        self.agents = {
            'data_agent': DataAgentWrapper(),
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
    
    def get_task_status(self, task_id):
        """Get status of a specific task"""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            agent_id = task.get('assigned_agent')
            if agent_id and agent_id in self.agents:
                agent = self.agents[agent_id]
                return {
                    'task_id': task_id,
                    'status': task['status'],
                    'progress': agent.progress,
                    'assigned_agent': agent_id,
                    'agent_status': agent.status,
                    'created_at': task.get('created_at'),
                    'started_at': task.get('started_at')
                }
            return {
                'task_id': task_id,
                'status': task['status'],
                'created_at': task.get('created_at'),
                'started_at': task.get('started_at')
            }
        
        # Check completed tasks
        for task in completed_tasks:
            if task.get('id') == task_id:
                return {
                    'task_id': task_id,
                    'status': task.get('status', 'completed'),
                    'completed_at': task.get('completed_at'),
                    'created_at': task.get('created_at'),
                    'error': task.get('error')
                }
        
        # Check queued tasks
        for task in self.task_queue:
            if task.get('id') == task_id:
                return {
                    'task_id': task_id,
                    'status': 'queued',
                    'created_at': task.get('created_at')
                }
        
        return None

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

class DataAgentWrapper(BaseAgent):
    """Wrapper for DataAgent to integrate with the agent system"""
    
    def __init__(self):
        super().__init__('Data Agent', ['data_processing', 'data_cleaning', 'data_validation'])
        self.data_agent = data_agent  # Use the global data_agent instance
    
    def execute_task(self, task):
        """Execute data processing task"""
        super().execute_task(task)
        
        if task['type'] == 'data_processing':
            try:
                data_processor.process_all()
                self.log("Data processing completed successfully")
            except Exception as e:
                self.log(f"Data processing failed: {str(e)}", 'error')

class AnalysisAgent(BaseAgent):
    """Handles analysis tasks"""
    
    def __init__(self):
        super().__init__('Analysis Agent', ['statistical_analysis', 'trend_analysis', 'correlation_analysis'])
        self.current_analysis_task = None
    
    def execute_task(self, task):
        """Execute analysis task with progress tracking"""
        self.status = 'busy'
        self.current_task = task['id']
        self.current_analysis_task = task
        self.progress = 0
        
        # Run analysis in background thread
        threading.Thread(target=self._execute_analysis_task, args=(task,), daemon=True).start()
    
    def _execute_analysis_task(self, task):
        """Execute analysis task with progress updates"""
        try:
            self.log(f"Starting analysis task: {task['type']}")
            self.progress = 10
            
            if task['type'] == 'statistical_analysis':
                # Check if we have a cleaned file to analyze
                parameters = task.get('parameters', {})
                cleaned_file = parameters.get('output_file') or parameters.get('cleaned_file')
                
                if cleaned_file and os.path.exists(cleaned_file):
                    self.log(f"Loading cleaned data from: {cleaned_file}")
                    self.progress = 20
                    
                    # Analyze the cleaned uploaded data
                    dataset_type = parameters.get('dataset_type', 'thesis')
                    
                    self.log(f"Analyzing {dataset_type} dataset...")
                    self.progress = 30
                    
                    # Perform analysis with progress updates
                    analysis_result = thesis_analyzer.analyze_uploaded_data(cleaned_file, dataset_type)
                    analysis_result = make_serializable(analysis_result)
                    self.progress = 80
                    
                    # Store results
                    coordinator.results[f'{dataset_type}_uploaded_analysis'] = analysis_result
                    coordinator.results[f'{dataset_type}_uploaded_analysis_task_id'] = task['id']
                    coordinator.results[f'{dataset_type}_uploaded_analysis_timestamp'] = datetime.now().isoformat()
                    
                    self.progress = 100
                    self.log(f"Analysis completed for uploaded {dataset_type} data")
                    
                    # Automatically queue visualization task for the cleaned data
                    visualization_params = {
                        'cleaned_file': cleaned_file,
                        'dataset_type': dataset_type,
                        'analysis_task_id': task['id'],
                        'analysis_timestamp': coordinator.results.get(f'{dataset_type}_uploaded_analysis_timestamp')
                    }
                    viz_task_id = coordinator.add_task('chart_generation', visualization_params)
                    coordinator.results[f'{dataset_type}_uploaded_visualization_task_id'] = viz_task_id

                else:
                    self.log("No cleaned file found, performing default analysis...")
                    self.progress = 40
                    
                    # Fallback to default analysis
                    thesis_analysis = thesis_analyzer.analyze_thesis_structure()
                    thesis_analysis = make_serializable(thesis_analysis)
                    self.progress = 70
                    
                    trends_analysis = thesis_analyzer.analyze_research_trends()
                    trends_analysis = make_serializable(trends_analysis)
                    self.progress = 90
                    
                    coordinator.results['thesis_analysis'] = thesis_analysis
                    coordinator.results['trends_analysis'] = trends_analysis
                    
                    self.progress = 100
                    self.log("Statistical analysis completed")
            
            # Mark task as completed
            task['status'] = 'completed'
            task['completed_at'] = datetime.now().isoformat()
            completed_tasks.append(task)
            
            if task['id'] in coordinator.active_tasks:
                del coordinator.active_tasks[task['id']]
            
            self.status = 'idle'
            self.current_task = None
            self.current_analysis_task = None
            self.progress = 0
            
        except Exception as e:
            self.log(f"Analysis failed: {str(e)}", 'error')
            task['status'] = 'failed'
            task['error'] = str(e)
            self.status = 'idle'
            self.current_task = None
            self.current_analysis_task = None
            self.progress = 0

class VisualizationAgent(BaseAgent):
    """Handles visualization tasks"""
    
    def __init__(self):
        super().__init__('Visualization Agent', ['chart_generation', 'dashboard_update', 'interactive_plots'])
    
    def execute_task(self, task):
        """Execute visualization task"""
        super().execute_task(task)
        
        if task['type'] == 'chart_generation':
            try:
                cleaned_file = task.get('parameters', {}).get('cleaned_file')
                dataset_type = task.get('parameters', {}).get('dataset_type', 'thesis')
                viz_summary = {
                    'dataset_type': dataset_type,
                    'generated_at': datetime.now().isoformat()
                }

                if cleaned_file and os.path.exists(cleaned_file):
                    df = pd.read_csv(cleaned_file)
                    df_preview = df.head(5)
                    viz_summary['preview_rows'] = df_preview.to_dict(orient='records')
                    viz_summary['columns'] = list(df_preview.columns)
                    viz_summary['row_count'] = len(df)
                else:
                    viz_summary['message'] = 'Cleaned file not available for visualization summary.'

                coordinator.results[f'{dataset_type}_visualization'] = make_serializable(viz_summary)
                self.log(f"Visualization summary stored for {dataset_type} dataset")

                # Queue report generation task
                report_task_id = coordinator.add_task('report_generation', {
                    'dataset_type': dataset_type,
                    'cleaned_file': cleaned_file,
                    'visualization_task_id': task.get('id')
                })
                coordinator.results[f'{dataset_type}_report_task_id'] = report_task_id
                self.log("Report generation task queued")
            except Exception as e:
                self.log(f"Visualization task failed: {str(e)}", 'error')

class ReportAgent(BaseAgent):
    """Handles report generation tasks"""
    
    def __init__(self):
        super().__init__('Report Agent', ['report_generation', 'pdf_export', 'html_export'])
    
    def execute_task(self, task):
        """Execute report generation task"""
        super().execute_task(task)
        
        if task['type'] == 'report_generation':
            try:
                dataset_type = task.get('parameters', {}).get('dataset_type', 'thesis')
                analysis = coordinator.results.get(f'{dataset_type}_uploaded_analysis') or coordinator.results.get('thesis_analysis')
                visualization = coordinator.results.get(f'{dataset_type}_visualization')
                report_summary = {
                    'dataset_type': dataset_type,
                    'generated_at': datetime.now().isoformat(),
                    'analysis_summary': analysis or {},
                    'visualization_summary': visualization or {},
                    'insights': (analysis or {}).get('insights', [])
                }
                coordinator.results[f'{dataset_type}_report'] = make_serializable(report_summary)
                self.log("Report summary stored for dataset")
            except Exception as e:
                self.log(f"Report generation failed: {str(e)}", 'error')

# Initialize coordinator
coordinator = AgentCoordinator()

# Configure LangGraph runtime (if available) so the graph can run with live dependencies
configure_graph_runtime(
    data_agent=data_agent,
    thesis_analyzer=thesis_analyzer,
    coordinator=coordinator,
)

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

@app.route('/api/agents/analysis/progress')
def get_analysis_progress():
    """Get detailed progress of analysis agent"""
    analysis_agent = coordinator.agents.get('analysis_agent')
    if not analysis_agent:
        return jsonify({'error': 'Analysis agent not found'}), 404
    
    status = analysis_agent.get_status()
    
    # Get current task details if available
    task_details = None
    if analysis_agent.current_analysis_task:
        task_details = {
            'task_id': analysis_agent.current_analysis_task.get('id'),
            'task_type': analysis_agent.current_analysis_task.get('type'),
            'dataset_type': analysis_agent.current_analysis_task.get('parameters', {}).get('dataset_type'),
            'cleaned_file': analysis_agent.current_analysis_task.get('parameters', {}).get('cleaned_file'),
            'created_at': analysis_agent.current_analysis_task.get('created_at'),
            'started_at': analysis_agent.current_analysis_task.get('started_at')
        }
    
    # Get recent logs
    recent_logs = analysis_agent.logs[-10:] if analysis_agent.logs else []
    
    return jsonify({
        'agent_name': status['name'],
        'status': status['status'],
        'progress': status['progress'],
        'current_task': status['current_task'],
        'task_details': task_details,
        'recent_logs': recent_logs,
        'has_results': len(coordinator.results) > 0
    })

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
    
    # Handle CSV upload via JSON (from uploadCSV function)
    if task_type == 'data_processing' and 'csv' in parameters and 'filename' in parameters:
        try:
            # Save CSV content to a temporary file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{parameters['filename']}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure upload directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Write CSV content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(parameters['csv'])
            
            # Get dataset_type from parameters if provided, otherwise let it auto-detect
            dataset_type = parameters.get('dataset_type')
            
            # Process the uploaded CSV
            result = data_agent.process_uploaded_csv(file_path, dataset_type=dataset_type)
            
            # Update parameters with processing results
            if result['status'] == 'success':
                parameters['input_file'] = result['input_file']
                parameters['output_file'] = result['output_file']
                parameters['dataset_type'] = result['dataset_type']
                parameters['cleaned_file'] = result['output_file']  # Add cleaned_file for analysis agent
                parameters['cleaning_stats'] = result.get('cleaning_stats', {})
                
                # Automatically trigger analysis on the cleaned data
                analysis_task_id = coordinator.add_task('statistical_analysis', {
                    'cleaned_file': result['output_file'],
                    'dataset_type': result['dataset_type'],
                    'input_file': result['input_file'],
                    'cleaning_stats': result.get('cleaning_stats', {})
                })
                parameters['analysis_task_id'] = analysis_task_id
            else:
                return jsonify({
                    'error': f"CSV processing failed: {result.get('error', 'Unknown error')}",
                    'task_id': None,
                    'status': 'error'
                }), 400
            
        except Exception as e:
            return jsonify({
                'error': f"Error processing CSV: {str(e)}",
                'task_id': None,
                'status': 'error'
            }), 500
    
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

@app.route('/api/data/processed')
def list_processed_files():
    """List all processed data files"""
    try:
        processed_dir = Path(app.config['UPLOAD_FOLDER']).parent / 'processed'
        processed_dir.mkdir(exist_ok=True)
        
        files = []
        for file_path in sorted(processed_dir.glob('*.csv'), key=lambda x: x.stat().st_mtime, reverse=True):
            # Get metadata if available
            metadata_path = file_path.with_suffix('.meta.json')
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            file_info = {
                'filename': file_path.name,
                'path': str(file_path.relative_to(Path(app.config['UPLOAD_FOLDER']).parent)),
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                'rows': metadata.get('rows', 0),
                'columns': metadata.get('columns', 0),
                'exported_at': metadata.get('exported_at', ''),
                'has_metadata': metadata_path.exists()
            }
            files.append(file_info)
        
        return jsonify({
            'files': files,
            'count': len(files)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/processed/<filename>')
def get_processed_file(filename):
    """Get a specific processed data file"""
    try:
        processed_dir = Path(app.config['UPLOAD_FOLDER']).parent / 'processed'
        file_path = processed_dir / filename
        
        # Security check - ensure file is in processed directory
        if not file_path.exists() or not str(file_path).startswith(str(processed_dir)):
            return jsonify({'error': 'File not found'}), 404
        
        if not filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are supported'}), 400
        
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Return first 100 rows as preview
        preview_rows = min(100, len(df))
        return jsonify({
            'filename': filename,
            'total_rows': len(df),
            'columns': list(df.columns),
            'preview': df.head(preview_rows).to_dict('records'),
            'data_types': df.dtypes.astype(str).to_dict(),
            'null_counts': df.isnull().sum().to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/processed/<filename>/download')
def download_processed_file(filename):
    """Download a processed data file"""
    try:
        processed_dir = Path(app.config['UPLOAD_FOLDER']).parent / 'processed'
        file_path = processed_dir / filename
        
        # Security check
        if not file_path.exists() or not str(file_path).startswith(str(processed_dir)):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(str(file_path), as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/processed/<filename>/metadata')
def get_processed_metadata(filename):
    """Get metadata for a processed file"""
    try:
        processed_dir = Path(app.config['UPLOAD_FOLDER']).parent / 'processed'
        metadata_path = processed_dir / filename.replace('.csv', '.meta.json')
        
        if not metadata_path.exists():
            return jsonify({'error': 'Metadata not found'}), 404
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return jsonify(metadata)
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
    return jsonify(make_serializable(coordinator.results))

@app.route('/api/analysis/uploaded/<dataset_type>')
def get_uploaded_analysis(dataset_type):
    """Get analysis results for uploaded data"""
    result_key = f'{dataset_type}_uploaded_analysis'
    if result_key in coordinator.results:
        return jsonify(coordinator.results[result_key])
    else:
        return jsonify({'error': 'Analysis not found. Please upload and process a file first.'}), 404

@app.route('/api/tasks/<task_id>/status')
def get_task_status(task_id):
    """Get status of a specific task"""
    task_status = coordinator.get_task_status(task_id)
    if task_status:
        return jsonify(task_status)
    else:
        return jsonify({'error': 'Task not found'}), 404

@app.route('/api/logs/<agent_id>')
def get_agent_logs(agent_id):
    """Get logs for a specific agent"""
    if agent_id in coordinator.agents:
        return jsonify(coordinator.agents[agent_id].logs)
    return jsonify({'error': 'Agent not found'}), 404

@app.route('/api/graph/structure')
def get_orchestration_graph():
    """Return the LangGraph orchestration structure for visualization."""
    try:
        metadata = get_graph_metadata()
        return jsonify(make_serializable(metadata)), 200
    except Exception as exc:  # pragma: no cover - unexpected failure path
        return jsonify({'available': False, 'error': str(exc)}), 500

@app.route('/api/graph/run', methods=['POST'])
def run_orchestration_graph():
    """Execute the LangGraph pipeline if runtime support is available."""
    if not GRAPH_EXECUTION_SUPPORTED:
        return jsonify({
            'available': False,
            'message': 'LangGraph execution is not enabled. Install langgraph/langchain and restart the backend.'
        }), 501

    payload = request.get_json(silent=True) or {}
    input_file = payload.get('input_file')
    cleaned_file = payload.get('cleaned_file')

    if not input_file and not cleaned_file:
        return jsonify({'error': 'Provide either input_file (raw CSV) or cleaned_file to start the pipeline.'}), 400

    initial_state = {
        'input_file': input_file,
        'cleaned_file': cleaned_file,
        'dataset_type': payload.get('dataset_type'),
        'cleaning_stats': payload.get('cleaning_stats', {}),
    }

    try:
        result_state = run_graph_pipeline(initial_state)
        return jsonify(make_serializable(result_state)), 200
    except Exception as exc:  # pragma: no cover - runtime failures surfaced to caller
        return jsonify({'error': str(exc)}), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'status': 'error', 'message': 'Only CSV files are supported'}), 400
        
        # Create a secure filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure the upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save the uploaded file
        file.save(file_path)
        print(f"File saved to: {file_path}")  # Debug log
        
        # Process the file using DataAgent
        result = data_agent.process_uploaded_csv(file_path)
        print(f"Processing result: {result}")  # Debug log
        
        # Add task to the coordinator
        if result['status'] == 'success':
            task_id = coordinator.add_task('data_processing', {
                'input_file': result['input_file'],
                'output_file': result['output_file'],
                'dataset_type': result['dataset_type'],
                'cleaned_file': result['output_file'],
                'cleaning_stats': result.get('cleaning_stats', {})
            })
            
            # Automatically trigger analysis on the cleaned data
            analysis_task_id = coordinator.add_task('statistical_analysis', {
                'cleaned_file': result['output_file'],
                'dataset_type': result['dataset_type'],
                'input_file': result['input_file'],
                'cleaning_stats': result.get('cleaning_stats', {})
            })
            
            result['analysis_task_id'] = analysis_task_id
            result['message'] = 'Data processed and analysis queued'
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('../reports', exist_ok=True)
    os.makedirs('../data/processed', exist_ok=True)
    
    print("🚀 Starting Debugging Agents Research Platform...")
    print("📊 Multi-agent system initialized")
    print("🌐 Web interface available at http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
