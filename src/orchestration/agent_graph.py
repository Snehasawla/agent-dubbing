"""LangGraph orchestration graph definition for the agent pipeline."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

try:
    from langgraph.graph import END, StateGraph
    from langgraph.graph.state import CompiledGraph
except (ModuleNotFoundError, Exception):  # pragma: no cover - optional dependency may be missing or incompatible
    StateGraph = None  # type: ignore
    END = None  # type: ignore
    CompiledGraph = None  # type: ignore

try:
    from langchain_core.runnables import RunnableLambda
except (ModuleNotFoundError, Exception):  # pragma: no cover - optional dependency may be missing or incompatible
    RunnableLambda = None  # type: ignore


graph_available: bool = StateGraph is not None
graph_execution_supported: bool = graph_available and RunnableLambda is not None


@dataclass
class AgentNodeInfo:
    """Metadata describing a node in the orchestration graph."""

    key: str
    label: str
    description: str
    agents: List[str] = field(default_factory=list)


@dataclass
class PipelineContext:
    """Holds runtime dependencies required by the LangGraph pipeline."""

    data_agent: Any
    thesis_analyzer: Any
    coordinator: Optional[Any] = None


_context: Optional[PipelineContext] = None
_compiled_graph: Optional[CompiledGraph] = None


def _make_json_serializable(obj: Any) -> Any:
    """Convert numpy/pandas types and NaN/Inf values into JSON-safe primitives."""
    if isinstance(obj, dict):
        return {str(k): _make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_make_json_serializable(item) for item in obj]
    try:
        import numpy as np  # local import to avoid enforcing dependency when unused

        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            value = float(obj)
            if pd.isna(value) or pd.isnull(value):  # type: ignore
                return None
            return value
        if isinstance(obj, np.ndarray):
            return [_make_json_serializable(item) for item in obj.tolist()]
        if isinstance(obj, np.bool_):
            return bool(obj)
    except ModuleNotFoundError:  # pragma: no cover - numpy already required elsewhere
        pass
    if isinstance(obj, float) and (pd.isna(obj) or pd.isnull(obj)):
        return None
    return obj


def configure_graph_runtime(
    data_agent: Optional[Any] = None,
    thesis_analyzer: Optional[Any] = None,
    coordinator: Optional[Any] = None,
) -> None:
    """Register runtime dependencies so the LangGraph pipeline can execute."""
    global _context, _compiled_graph

    if data_agent is None or thesis_analyzer is None:
        _context = None
        _compiled_graph = None
        return

    _context = PipelineContext(
        data_agent=data_agent,
        thesis_analyzer=thesis_analyzer,
        coordinator=coordinator,
    )

    if graph_execution_supported:
        _compiled_graph = _build_graph()
    else:
        _compiled_graph = None


def _append_log(state: Dict[str, Any], node: str, message: str) -> None:
    logs = state.setdefault('logs', [])
    try:
        loop = asyncio.get_running_loop()
        timestamp = loop.time()
    except RuntimeError:
        timestamp = None
    logs.append({
        'node': node,
        'message': message,
        'timestamp': timestamp,
    })


def _build_graph() -> Optional[CompiledGraph]:
    """Create and compile the LangGraph state graph if dependencies are available."""
    if not graph_execution_supported or _context is None:
        return None

    context = _context
    graph = StateGraph(dict)  # type: ignore[arg-type]

    async def data_node(state: Dict[str, Any]) -> Dict[str, Any]:
        new_state = dict(state)
        _append_log(new_state, 'data_agent', 'Starting data cleaning step')

        if new_state.get('cleaned_file'):
            _append_log(new_state, 'data_agent', 'Cleaned file already provided, skipping cleaning')
            return new_state

        input_file = new_state.get('input_file')
        if not input_file:
            raise ValueError('input_file is required for the data agent step')

        dataset_type = new_state.get('dataset_type')
        result = await asyncio.to_thread(
            context.data_agent.process_uploaded_csv,
            input_file,
            dataset_type,
        )

        if result.get('status') != 'success':
            raise RuntimeError(f"Data agent failed: {result.get('error', 'unknown error')}")

        new_state.update({
            'dataset_type': result.get('dataset_type', dataset_type),
            'cleaned_file': result.get('output_file'),
            'cleaning_stats': result.get('cleaning_stats', {}),
            'data_result': result,
        })
        _append_log(new_state, 'data_agent', 'Data cleaning completed successfully')

        if context.coordinator:
            context.coordinator.results['latest_cleaning'] = _make_json_serializable(result)

        return new_state

    async def analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
        new_state = dict(state)
        _append_log(new_state, 'analysis_agent', 'Starting statistical analysis')

        cleaned_file = new_state.get('cleaned_file')
        if not cleaned_file:
            raise ValueError('cleaned_file is required for analysis')

        dataset_type = new_state.get('dataset_type', 'thesis')
        analysis = await asyncio.to_thread(
            context.thesis_analyzer.analyze_uploaded_data,
            cleaned_file,
            dataset_type,
        )

        analysis = _make_json_serializable(analysis)
        new_state['analysis_result'] = analysis
        _append_log(new_state, 'analysis_agent', 'Analysis completed successfully')

        if context.coordinator:
            key = f"{dataset_type}_uploaded_analysis"
            context.coordinator.results[key] = analysis

        return new_state

    async def visualization_node(state: Dict[str, Any]) -> Dict[str, Any]:
        new_state = dict(state)
        _append_log(new_state, 'visualization_agent', 'Preparing visualization summary')

        cleaned_file = new_state.get('cleaned_file')
        if not cleaned_file:
            raise ValueError('cleaned_file is required for visualization')

        dataset_type = new_state.get('dataset_type', 'thesis')
        viz_summary: Dict[str, Any] = {
            'dataset_type': dataset_type,
            'source_file': cleaned_file,
        }

        cleaned_path = Path(cleaned_file)
        if cleaned_path.exists():
            df = await asyncio.to_thread(pd.read_csv, cleaned_path)
            viz_summary['columns'] = list(df.columns)
            viz_summary['row_count'] = len(df)
            viz_summary['preview_rows'] = df.head(5).to_dict(orient='records')
        else:
            viz_summary['message'] = 'Cleaned file not found on disk.'

        viz_summary = _make_json_serializable(viz_summary)
        new_state['visualization_summary'] = viz_summary
        _append_log(new_state, 'visualization_agent', 'Visualization summary prepared')

        if context.coordinator:
            key = f"{dataset_type}_visualization"
            context.coordinator.results[key] = viz_summary

        return new_state

    async def report_node(state: Dict[str, Any]) -> Dict[str, Any]:
        new_state = dict(state)
        _append_log(new_state, 'report_agent', 'Compiling final report summary')

        dataset_type = new_state.get('dataset_type', 'thesis')
        report_summary = {
            'dataset_type': dataset_type,
            'analysis': new_state.get('analysis_result', {}),
            'visualization': new_state.get('visualization_summary', {}),
        }
        report_summary = _make_json_serializable(report_summary)
        new_state['report_summary'] = report_summary
        new_state['status'] = 'completed'
        _append_log(new_state, 'report_agent', 'Report summary ready')

        if context.coordinator:
            key = f"{dataset_type}_report"
            context.coordinator.results[key] = report_summary

        return new_state

    graph.add_node('data_agent', RunnableLambda(data_node))  # type: ignore[arg-type]
    graph.add_node('analysis_agent', RunnableLambda(analysis_node))  # type: ignore[arg-type]
    graph.add_node('visualization_agent', RunnableLambda(visualization_node))  # type: ignore[arg-type]
    graph.add_node('report_agent', RunnableLambda(report_node))  # type: ignore[arg-type]

    graph.set_entry_point('data_agent')
    graph.add_edge('data_agent', 'analysis_agent')
    graph.add_edge('analysis_agent', 'visualization_agent')
    graph.add_edge('visualization_agent', 'report_agent')
    graph.add_edge('report_agent', END)

    return graph.compile()


def get_compiled_graph() -> Optional[CompiledGraph]:
    """Return the compiled graph, compiling it lazily if needed."""
    global _compiled_graph

    if _compiled_graph is None and graph_execution_supported and _context is not None:
        _compiled_graph = _build_graph()

    return _compiled_graph


def run_graph_pipeline(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the orchestration pipeline synchronously."""
    compiled = get_compiled_graph()
    if compiled is None:
        raise RuntimeError('LangGraph pipeline is not available. Ensure langgraph/langchain are installed and configured.')
    return asyncio.run(compiled.ainvoke(initial_state))


async def run_graph_pipeline_async(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the orchestration pipeline asynchronously."""
    compiled = get_compiled_graph()
    if compiled is None:
        raise RuntimeError('LangGraph pipeline is not available. Ensure langgraph/langchain are installed and configured.')
    return await compiled.ainvoke(initial_state)


def get_graph_metadata() -> Dict[str, Any]:
    """Return a structured description of the orchestration graph."""
    nodes = [
        AgentNodeInfo(
            key='data_agent',
            label='Data Agent',
            description='Cleans and preprocesses uploaded datasets',
            agents=['DataAgent']
        ),
        AgentNodeInfo(
            key='analysis_agent',
            label='Analysis Agent',
            description='Performs statistical analysis on cleaned data',
            agents=['AnalysisAgent']
        ),
        AgentNodeInfo(
            key='visualization_agent',
            label='Visualization Agent',
            description='Generates dashboard-ready visualizations',
            agents=['VisualizationAgent']
        ),
        AgentNodeInfo(
            key='report_agent',
            label='Report Agent',
            description='Compiles final summaries and reports',
            agents=['ReportAgent']
        ),
    ]

    compiled = get_compiled_graph()
    if not graph_execution_supported or compiled is None:
        fallback_edges = [
            {'source': 'data_agent', 'target': 'analysis_agent'},
            {'source': 'analysis_agent', 'target': 'visualization_agent'},
            {'source': 'visualization_agent', 'target': 'report_agent'}
        ]
        mermaid_diagram = """stateDiagram-v2\n    data_agent: Data Agent\n    analysis_agent: Analysis Agent\n    visualization_agent: Visualization Agent\n    report_agent: Report Agent\n\n    [*] --> data_agent\n    data_agent --> analysis_agent\n    analysis_agent --> visualization_agent\n    visualization_agent --> report_agent\n    report_agent --> [*]\n"""
        return {
            'available': False,
            'message': 'LangGraph execution pipeline is not active. Install langgraph/langchain and restart the backend to enable live orchestration.',
            'mode': 'fallback',
            'nodes': [
                {
                    'key': node.key,
                    'label': node.label,
                    'description': node.description,
                    'agents': node.agents
                }
                for node in nodes
            ],
            'edges': fallback_edges,
            'mermaid': mermaid_diagram,
            'graph_summary': {
                'total_nodes': len(nodes),
                'total_edges': len(fallback_edges) + 2  # include start/end transitions
            }
        }

    graph_view = compiled.get_graph()

    edges = [
        {'source': edge[0], 'target': edge[1]}
        for edge in getattr(graph_view, 'edges', [])
    ]

    mermaid_diagram: Optional[str] = None
    if hasattr(graph_view, 'draw_mermaid'):
        mermaid_diagram = graph_view.draw_mermaid()

    return {
        'available': True,
        'nodes': [
            {
                'key': node.key,
                'label': node.label,
                'description': node.description,
                'agents': node.agents
            }
            for node in nodes
        ],
        'edges': edges,
        'mermaid': mermaid_diagram,
        'graph_summary': {
            'total_nodes': len(nodes),
            'total_edges': len(edges)
        }
    }
