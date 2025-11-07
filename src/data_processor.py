"""
Data Processing Module for Debugging Agents Research
Handles data loading, cleaning, and preprocessing operations.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Handles data processing operations for the debugging agents project"""
    
    def __init__(self, data_path="../data/"):
        self.data_path = Path(data_path)
        self.thesis_data = None
        self.papers_data = None
        self.processed_data = {}
        logger.info(f"📂 Initialized DataProcessor with data path: {self.data_path}")
    
    def load_raw_data(self):
        """Load raw datasets from CSV files if they exist"""
        # Load thesis annotations if available
        thesis_file = self.data_path / "debugging_agents_synthetic_annotations.csv"
        if thesis_file.exists():
            self.thesis_data = pd.read_csv(thesis_file)
            logger.info(f"✅ Loaded thesis data: {len(self.thesis_data)} sections")
        
        # Load papers metadata if available
        papers_file = self.data_path / "synthetic_pdf_papers_dataset.csv"
        if papers_file.exists():
            self.papers_data = pd.read_csv(papers_file)
            logger.info(f"✅ Loaded papers data: {len(self.papers_data)} papers")
        
        logger.info("✅ Raw data loading complete")
    
    def clean_thesis_data(self):
        """Clean and preprocess thesis data"""
        if self.thesis_data is None:
            logger.warning("⚠️ No thesis data to clean")
            return
        
        # Create a copy for processing
        df = self.thesis_data.copy()
        
        # Handle missing values - only for columns that exist
        fillna_dict = {}
        numeric_columns = ['estimated_pages', 'num_figures', 'num_tables', 'num_equations']
        for col in numeric_columns:
            if col in df.columns:
                fillna_dict[col] = 0
        
        if 'difficulty_score' in df.columns:
            fillna_dict['difficulty_score'] = df['difficulty_score'].median() if not df['difficulty_score'].isna().all() else 0
        
        if fillna_dict:
            df = df.fillna(fillna_dict)
        
        # Convert boolean columns to int for consistency
        bool_columns = ['has_algorithms', 'has_case_study', 'has_limitations']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].astype(int)
        
        # Create derived features - only if required columns exist
        if all(col in df.columns for col in ['num_figures', 'num_tables', 'num_equations', 'estimated_pages']):
            df['content_density'] = (df['num_figures'] + df['num_tables'] + df['num_equations']) / df['estimated_pages'].clip(lower=1)
            if 'difficulty_score' in df.columns:
                df['complexity_score'] = df['difficulty_score'] * df['content_density']
        elif 'difficulty_score' in df.columns:
            # If we have difficulty_score but not the other columns, just use difficulty_score
            df['complexity_score'] = df['difficulty_score']
        
        # Categorize sections by type
        def categorize_section(title):
            title_lower = title.lower()
            if any(word in title_lower for word in ['method', 'approach', 'algorithm']):
                return 'Methodology'
            elif any(word in title_lower for word in ['result', 'experiment', 'evaluation']):
                return 'Results'
            elif any(word in title_lower for word in ['related', 'background', 'literature']):
                return 'Background'
            elif any(word in title_lower for word in ['conclusion', 'future', 'discussion']):
                return 'Conclusion'
            else:
                return 'Other'
        
        # Categorize sections by type - only if section_title exists
        if 'section_title' in df.columns:
            df['section_type'] = df['section_title'].apply(categorize_section)
        else:
            logger.warning("⚠️ 'section_title' column not found, skipping section categorization")
        
        self.processed_data['thesis_clean'] = df
        logger.info("✅ Thesis data cleaned and processed")
    
    def clean_papers_data(self):
        """Clean and preprocess papers data"""
        if self.papers_data is None:
            logger.warning("⚠️ No papers data to clean")
            return
        
        # Create a copy for processing
        df = self.papers_data.copy()
        
        # Handle missing values - only for columns that exist
        fillna_dict = {}
        if 'pages' in df.columns:
            fillna_dict['pages'] = df['pages'].median() if not df['pages'].isna().all() else 0
        if 'references_count' in df.columns:
            fillna_dict['references_count'] = df['references_count'].median() if not df['references_count'].isna().all() else 0
        if 'citations' in df.columns:
            fillna_dict['citations'] = 0
        if 'readability_score' in df.columns:
            fillna_dict['readability_score'] = df['readability_score'].median() if not df['readability_score'].isna().all() else 0
        
        if fillna_dict:
            df = df.fillna(fillna_dict)
        
        # Convert boolean columns
        bool_columns = ['has_code', 'has_appendix', 'has_acknowledgements']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].astype(int)
        
        # Create derived features - only if required columns exist
        if 'citations' in df.columns and 'year' in df.columns:
            df['citations_per_year'] = df['citations'] / (2024 - df['year'] + 1)
        if 'references_count' in df.columns and 'pages' in df.columns:
            df['references_per_page'] = df['references_count'] / df['pages']
        if all(col in df.columns for col in ['sections', 'subsections', 'pages']):
            df['complexity_index'] = (df['sections'] + df['subsections']) / df['pages']
        
        # Categorize papers by impact - only if citations column exists
        if 'citations' in df.columns:
            def categorize_impact(citations):
                if citations >= 200:
                    return 'High Impact'
                elif citations >= 50:
                    return 'Medium Impact'
                else:
                    return 'Low Impact'
            df['impact_category'] = df['citations'].apply(categorize_impact)
        
        # Categorize by readability - only if readability_score exists
        if 'readability_score' in df.columns:
            def categorize_readability(score):
                if score >= 50:
                    return 'High Readability'
                elif score >= 40:
                    return 'Medium Readability'
                else:
                    return 'Low Readability'
            df['readability_category'] = df['readability_score'].apply(categorize_readability)
        
        self.processed_data['papers_clean'] = df
        logger.info("✅ Papers data cleaned and processed")
    
    def create_summary_statistics(self):
        """Create summary statistics for both datasets"""
        summary = {}
        
        if 'thesis_clean' in self.processed_data:
            thesis_df = self.processed_data['thesis_clean']
            summary['thesis'] = {
                'total_sections': len(thesis_df),
                'total_pages': thesis_df['estimated_pages'].sum() if 'estimated_pages' in thesis_df.columns else 0,
                'avg_difficulty': thesis_df['difficulty_score'].mean() if 'difficulty_score' in thesis_df.columns else None,
                'sections_with_algorithms': thesis_df['has_algorithms'].sum() if 'has_algorithms' in thesis_df.columns else 0,
                'sections_with_case_studies': thesis_df['has_case_study'].sum() if 'has_case_study' in thesis_df.columns else 0,
                'high_priority_sections': len(thesis_df[thesis_df['priority_for_extraction'] == 'High']) if 'priority_for_extraction' in thesis_df.columns else 0,
                'section_types': thesis_df['section_type'].value_counts().to_dict() if 'section_type' in thesis_df.columns else {}
            }
        
        if 'papers_clean' in self.processed_data:
            papers_df = self.processed_data['papers_clean']
            summary['papers'] = {
                'total_papers': len(papers_df),
                'year_range': f"{papers_df['year'].min()}-{papers_df['year'].max()}",
                'domains': papers_df['domain'].nunique(),
                'avg_citations': papers_df['citations'].mean(),
                'avg_readability': papers_df['readability_score'].mean(),
                'papers_with_code': papers_df['has_code'].sum(),
                'impact_distribution': papers_df['impact_category'].value_counts().to_dict(),
                'readability_distribution': papers_df['readability_category'].value_counts().to_dict()
            }
        
        self.processed_data['summary'] = summary
        logger.info("✅ Summary statistics created")
        return summary
    
    def export_processed_data(self, output_path="../data/processed/"):
        """Export processed data to CSV files"""
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True)
        
        if 'thesis_clean' in self.processed_data:
            thesis_file = output_dir / "thesis_processed.csv"
            self.processed_data['thesis_clean'].to_csv(thesis_file, index=False)
            logger.info(f"✅ Exported thesis data to {thesis_file}")
        
        if 'papers_clean' in self.processed_data:
            papers_file = output_dir / "papers_processed.csv"
            self.processed_data['papers_clean'].to_csv(papers_file, index=False)
            logger.info(f"✅ Exported papers data to {papers_file}")
        
        if 'summary' in self.processed_data:
            import json
            summary_file = output_dir / "summary_statistics.json"
            with open(summary_file, 'w') as f:
                json.dump(self.processed_data['summary'], f, indent=2)
            logger.info(f"✅ Exported summary statistics to {summary_file}")
    
    def get_high_priority_sections(self):
        """Get sections marked as high priority for extraction"""
        if 'thesis_clean' not in self.processed_data:
            return None
        
        thesis_df = self.processed_data['thesis_clean']
        
        # Check if required columns exist
        if 'priority_for_extraction' not in thesis_df.columns:
            logger.warning("⚠️ 'priority_for_extraction' column not found")
            return None
        
        high_priority = thesis_df[thesis_df['priority_for_extraction'] == 'High'].copy()
        
        # Sort by difficulty_score if it exists, otherwise just return
        if 'difficulty_score' in high_priority.columns:
            high_priority = high_priority.sort_values('difficulty_score', ascending=False)
        
        # Return only columns that exist
        available_cols = ['section_title', 'level', 'difficulty_score', 'section_type', 'has_algorithms']
        return_cols = [col for col in available_cols if col in high_priority.columns]
        
        if return_cols:
            return high_priority[return_cols]
        else:
            return high_priority
    
    def get_domain_insights(self):
        """Get insights by research domain"""
        if 'papers_clean' not in self.processed_data:
            return None
        
        papers_df = self.processed_data['papers_clean']
        domain_insights = papers_df.groupby('domain').agg({
            'citations': ['mean', 'std', 'count'],
            'readability_score': ['mean', 'std'],
            'pages': 'mean',
            'has_code': 'mean',
            'year': ['min', 'max']
        }).round(2)
        
        # Flatten column names
        domain_insights.columns = ['_'.join(col).strip() for col in domain_insights.columns]
        
        return domain_insights
    
    def process_all(self):
        """Run complete data processing pipeline"""
        logger.info("🚀 Starting data processing pipeline...")
        
        # Load raw data
        self.load_raw_data()
        
        # Clean data
        self.clean_thesis_data()
        self.clean_papers_data()
        
        # Create summaries
        summary = self.create_summary_statistics()
        
        # Export processed data
        self.export_processed_data()
        
        logger.info("✅ Data processing pipeline completed")
        return summary

def main():
    """Main execution function for data processing"""
    processor = DataProcessor()
    summary = processor.process_all()
    
    print("\n📊 Processing Summary:")
    if 'thesis' in summary:
        print(f"Thesis: {summary['thesis']['total_sections']} sections, {summary['thesis']['total_pages']} pages")
    if 'papers' in summary:
        print(f"Papers: {summary['papers']['total_papers']} papers, {summary['papers']['domains']} domains")
    
    # Show high priority sections
    high_priority = processor.get_high_priority_sections()
    if high_priority is not None:
        print("\n🎯 High Priority Sections:")
        print(high_priority.to_string(index=False))

if __name__ == "__main__":
    main()
