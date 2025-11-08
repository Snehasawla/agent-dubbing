"""
Thesis Structure Analyzer for Debugging Agents Research
Analyzes synthetic thesis data and generates comprehensive reports.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from pathlib import Path

class ThesisAnalyzer:
    def __init__(self, data_path="../data/"):
        self.data_path = Path(data_path)
        self.thesis_data = None
        self.papers_data = None
        self.load_data()
    
    def _make_serializable(self, obj):
        """Recursively convert numpy/pandas objects into JSON-serializable primitives."""
        if isinstance(obj, dict):
            return {self._make_serializable(key): self._make_serializable(value) for key, value in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [self._make_serializable(item) for item in obj]
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            # Preserve NaN as None so JSON serialization succeeds
            value = float(obj)
            return None if np.isnan(value) else value
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return [self._make_serializable(item) for item in obj.tolist()]
        return obj

    def load_data(self):
        """Load the synthetic datasets"""
        try:
            thesis_file = self.data_path / "debugging_agents_synthetic_annotations.csv"
            papers_file = self.data_path / "synthetic_pdf_papers_dataset.csv"
            
            if thesis_file.exists():
                self.thesis_data = pd.read_csv(thesis_file)
            if papers_file.exists():
                self.papers_data = pd.read_csv(papers_file)
            
            if self.thesis_data is not None or self.papers_data is not None:
                print("✅ Data loaded successfully")
                if self.thesis_data is not None:
                    print(f"Thesis sections: {len(self.thesis_data)}")
                if self.papers_data is not None:
                    print(f"Academic papers: {len(self.papers_data)}")
        except FileNotFoundError as e:
            print(f"❌ Error loading data: {e}")
    
    def analyze_uploaded_data(self, file_path, dataset_type='thesis'):
        """
        Analyze uploaded and cleaned data file
        
        Args:
            file_path: Path to the cleaned CSV file
            dataset_type: Type of dataset ('thesis' or 'papers')
        
        Returns:
            Dictionary with analysis results
        """
        try:
            # Load the cleaned data
            df = pd.read_csv(file_path)
            
            analysis_results = {
                'dataset_type': dataset_type,
                'file_path': str(file_path),
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'columns': list(df.columns),
                'data_types': df.dtypes.astype(str).to_dict(),
                'basic_statistics': {},
                'data_quality': {},
                'insights': []
            }
            
            # Basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                analysis_results['basic_statistics'] = df[numeric_cols].describe().to_dict()
            
            # Data quality metrics
            analysis_results['data_quality'] = {
                'null_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100) if len(df) > 0 else 0,
                'duplicate_rows': df.duplicated().sum(),
                'unique_values_per_column': {col: df[col].nunique() for col in df.columns}
            }
            
            # Dataset-specific analysis
            if dataset_type == 'thesis':
                analysis_results.update(self._analyze_thesis_data(df))
            elif dataset_type == 'papers':
                analysis_results.update(self._analyze_papers_data(df))
            else:
                # Generic analysis for unknown dataset types
                analysis_results.update(self._analyze_generic_data(df))
            
            return self._make_serializable(analysis_results)
            
        except Exception as e:
            return {
                'error': str(e),
                'dataset_type': dataset_type,
                'file_path': str(file_path)
            }
    
    def _analyze_thesis_data(self, df):
        """Analyze thesis-specific data"""
        analysis = {}
        
        if 'level' in df.columns:
            analysis['level_distribution'] = df['level'].value_counts().sort_index().to_dict()
        
        if 'priority_for_extraction' in df.columns:
            analysis['priority_distribution'] = df['priority_for_extraction'].value_counts().to_dict()
        
        if 'difficulty_score' in df.columns:
            analysis['difficulty_stats'] = df['difficulty_score'].describe().to_dict()
        
        if 'estimated_pages' in df.columns:
            analysis['total_pages'] = float(df['estimated_pages'].sum())
        
        return self._make_serializable(analysis)
    
    def _analyze_papers_data(self, df):
        """Analyze papers-specific data"""
        analysis = {}
        
        if 'year' in df.columns:
            analysis['year_distribution'] = df['year'].value_counts().sort_index().to_dict()
        
        if 'domain' in df.columns:
            analysis['domain_distribution'] = df['domain'].value_counts().to_dict()
        
        if 'citations' in df.columns:
            analysis['citation_stats'] = df['citations'].describe().to_dict()
        
        if 'readability_score' in df.columns:
            analysis['readability_stats'] = df['readability_score'].describe().to_dict()
        
        return self._make_serializable(analysis)
    
    def _analyze_generic_data(self, df):
        """Generic analysis for any dataset"""
        analysis = {
            'insights': []
        }
        
        # Find potential key columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        if len(numeric_cols) > 0:
            analysis['numeric_summary'] = df[numeric_cols].describe().to_dict()
            analysis['insights'].append(f"Dataset contains {len(numeric_cols)} numeric columns")
        
        if len(categorical_cols) > 0:
            analysis['categorical_summary'] = {
                col: {
                    'unique_count': df[col].nunique(),
                    'most_common': df[col].value_counts().head(5).to_dict()
                } for col in categorical_cols[:5]  # Limit to first 5 categorical columns
            }
            analysis['insights'].append(f"Dataset contains {len(categorical_cols)} categorical columns")
        
        return self._make_serializable(analysis)
    
    def analyze_thesis_structure(self):
        """Analyze thesis section structure and priorities"""
        if self.thesis_data is None:
            return None
        
        # Section level distribution
        level_dist = self.thesis_data['level'].value_counts().sort_index()
        
        # Priority analysis
        priority_dist = self.thesis_data['priority_for_extraction'].value_counts()
        
        # Difficulty analysis
        difficulty_stats = self.thesis_data['difficulty_score'].describe()
        
        # Content analysis
        content_analysis = {
            'total_pages': self.thesis_data['estimated_pages'].sum(),
            'total_figures': self.thesis_data['num_figures'].sum(),
            'total_tables': self.thesis_data['num_tables'].sum(),
            'total_equations': self.thesis_data['num_equations'].sum(),
            'sections_with_algorithms': self.thesis_data['has_algorithms'].sum(),
            'sections_with_case_studies': self.thesis_data['has_case_study'].sum(),
            'sections_with_limitations': self.thesis_data['has_limitations'].sum()
        }
        
        return self._make_serializable({
            'level_distribution': level_dist.to_dict(),
            'priority_distribution': priority_dist.to_dict(),
            'difficulty_stats': difficulty_stats.to_dict(),
            'content_analysis': content_analysis
        })
    
    def analyze_research_trends(self):
        """Analyze academic paper trends and patterns"""
        if self.papers_data is None:
            return None
        
        # Domain analysis
        domain_dist = self.papers_data['domain'].value_counts()
        
        # Year trends
        year_trends = self.papers_data.groupby('year').agg({
            'citations': 'mean',
            'pages': 'mean',
            'references_count': 'mean'
        }).round(2)
        
        # Readability analysis
        readability_by_domain = self.papers_data.groupby('domain')['readability_score'].agg(['mean', 'std']).round(2)
        
        # Code presence analysis
        code_analysis = self.papers_data.groupby('domain')['has_code'].mean().round(3)
        
        return self._make_serializable({
            'domain_distribution': domain_dist.to_dict(),
            'year_trends': year_trends.to_dict(),
            'readability_by_domain': readability_by_domain.to_dict(),
            'code_analysis': code_analysis.to_dict()
        })
    
    def create_visualizations(self):
        """Create comprehensive visualizations"""
        if self.thesis_data is None or self.papers_data is None:
            return
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Create output directory
        output_dir = Path("../reports")
        output_dir.mkdir(exist_ok=True)
        
        # 1. Thesis Structure Analysis
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Thesis Structure Analysis', fontsize=16, fontweight='bold')
        
        # Section levels
        level_counts = self.thesis_data['level'].value_counts().sort_index()
        axes[0,0].bar(level_counts.index, level_counts.values, color='skyblue')
        axes[0,0].set_title('Section Level Distribution')
        axes[0,0].set_xlabel('Level')
        axes[0,0].set_ylabel('Count')
        
        # Priority distribution
        priority_counts = self.thesis_data['priority_for_extraction'].value_counts()
        axes[0,1].pie(priority_counts.values, labels=priority_counts.index, autopct='%1.1f%%')
        axes[0,1].set_title('Priority for Extraction')
        
        # Difficulty scores
        axes[1,0].hist(self.thesis_data['difficulty_score'], bins=10, color='lightcoral', alpha=0.7)
        axes[1,0].set_title('Difficulty Score Distribution')
        axes[1,0].set_xlabel('Difficulty Score')
        axes[1,0].set_ylabel('Frequency')
        
        # Content types
        content_types = ['has_algorithms', 'has_case_study', 'has_limitations']
        content_counts = [self.thesis_data[col].sum() for col in content_types]
        axes[1,1].bar(content_types, content_counts, color='lightgreen')
        axes[1,1].set_title('Content Type Distribution')
        axes[1,1].set_ylabel('Count')
        axes[1,1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'thesis_structure_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # 2. Research Trends Analysis
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Research Trends Analysis', fontsize=16, fontweight='bold')
        
        # Domain distribution
        domain_counts = self.papers_data['domain'].value_counts()
        axes[0,0].barh(domain_counts.index, domain_counts.values, color='lightblue')
        axes[0,0].set_title('Research Domain Distribution')
        axes[0,0].set_xlabel('Number of Papers')
        
        # Year trends
        year_data = self.papers_data.groupby('year').size()
        axes[0,1].plot(year_data.index, year_data.values, marker='o', linewidth=2, markersize=8)
        axes[0,1].set_title('Papers Published by Year')
        axes[0,1].set_xlabel('Year')
        axes[0,1].set_ylabel('Number of Papers')
        axes[0,1].grid(True, alpha=0.3)
        
        # Readability by domain
        readability_data = self.papers_data.groupby('domain')['readability_score'].mean().sort_values()
        axes[1,0].barh(readability_data.index, readability_data.values, color='lightcoral')
        axes[1,0].set_title('Average Readability by Domain')
        axes[1,0].set_xlabel('Readability Score')
        
        # Citations vs Pages
        scatter = axes[1,1].scatter(self.papers_data['pages'], self.papers_data['citations'], 
                                   c=self.papers_data['year'], cmap='viridis', alpha=0.6)
        axes[1,1].set_title('Citations vs Pages (colored by year)')
        axes[1,1].set_xlabel('Pages')
        axes[1,1].set_ylabel('Citations')
        plt.colorbar(scatter, ax=axes[1,1], label='Year')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'research_trends_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_interactive_dashboard(self):
        """Generate interactive Plotly dashboard"""
        if self.thesis_data is None or self.papers_data is None:
            return
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Thesis Section Priorities', 'Research Domain Trends', 
                          'Difficulty vs Priority', 'Paper Metrics Over Time'),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "scatter"}]]
        )
        
        # 1. Thesis priorities pie chart
        priority_counts = self.thesis_data['priority_for_extraction'].value_counts()
        fig.add_trace(
            go.Pie(labels=priority_counts.index, values=priority_counts.values, name="Priorities"),
            row=1, col=1
        )
        
        # 2. Domain distribution
        domain_counts = self.papers_data['domain'].value_counts()
        fig.add_trace(
            go.Bar(x=domain_counts.index, y=domain_counts.values, name="Domains"),
            row=1, col=2
        )
        
        # 3. Difficulty vs Priority scatter
        fig.add_trace(
            go.Scatter(x=self.thesis_data['difficulty_score'], 
                      y=self.thesis_data['priority_for_extraction'],
                      mode='markers', name="Sections",
                      text=self.thesis_data['section_title'],
                      hovertemplate='<b>%{text}</b><br>Difficulty: %{x}<br>Priority: %{y}<extra></extra>'),
            row=2, col=1
        )
        
        # 4. Citations over time
        year_citations = self.papers_data.groupby('year')['citations'].mean()
        fig.add_trace(
            go.Scatter(x=year_citations.index, y=year_citations.values,
                      mode='lines+markers', name="Avg Citations"),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="Debugging Agents Research Dashboard",
            showlegend=True,
            height=800
        )
        
        # Save interactive HTML
        output_dir = Path("../reports")
        output_dir.mkdir(exist_ok=True)
        fig.write_html(output_dir / "interactive_dashboard.html")
        
        return fig
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("🔍 Analyzing thesis structure...")
        thesis_analysis = self.analyze_thesis_structure()
        
        print("📊 Analyzing research trends...")
        trends_analysis = self.analyze_research_trends()
        
        print("📈 Creating visualizations...")
        self.create_visualizations()
        
        print("🎯 Generating interactive dashboard...")
        self.generate_interactive_dashboard()
        
        # Generate text report
        report_content = f"""
# Debugging Agents Research Analysis Report

## Executive Summary
This report analyzes synthetic data for debugging agents research, including thesis structure and academic paper trends.

## Thesis Structure Analysis
- **Total Sections**: {len(self.thesis_data)}
- **Total Estimated Pages**: {thesis_analysis['content_analysis']['total_pages']}
- **Sections with Algorithms**: {thesis_analysis['content_analysis']['sections_with_algorithms']}
- **Sections with Case Studies**: {thesis_analysis['content_analysis']['sections_with_case_studies']}

## Research Trends Analysis
- **Total Papers Analyzed**: {len(self.papers_data)}
- **Research Domains**: {len(trends_analysis['domain_distribution'])}
- **Year Range**: {self.papers_data['year'].min()} - {self.papers_data['year'].max()}

## Key Insights
1. **High Priority Sections**: Focus on Methodology, System Architecture, and Results
2. **Research Growth**: Steady increase in debugging agents research over time
3. **Domain Diversity**: Strong representation across Software Engineering, ML, and AI Systems
4. **Content Distribution**: Balanced mix of theoretical and practical sections

## Recommendations
1. Prioritize extraction of high-difficulty, high-priority sections
2. Focus on sections with algorithms and case studies for implementation
3. Consider domain-specific analysis for targeted insights
4. Use interactive dashboard for exploratory analysis

## Files Generated
- thesis_structure_analysis.png
- research_trends_analysis.png
- interactive_dashboard.html
"""
        
        # Save report
        output_dir = Path("../reports")
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / "analysis_report.md", "w") as f:
            f.write(report_content)
        
        print("✅ Analysis complete! Check the reports/ directory for outputs.")
        return thesis_analysis, trends_analysis

def main():
    """Main execution function"""
    print("🚀 Starting Debugging Agents Research Analysis...")
    
    # Initialize analyzer
    analyzer = ThesisAnalyzer()
    
    # Generate comprehensive report
    thesis_analysis, trends_analysis = analyzer.generate_report()
    
    print("\n📋 Summary:")
    print(f"- Analyzed {len(analyzer.thesis_data)} thesis sections")
    print(f"- Analyzed {len(analyzer.papers_data)} academic papers")
    print("- Generated visualizations and interactive dashboard")
    print("- Created comprehensive analysis report")

if __name__ == "__main__":
    main()
