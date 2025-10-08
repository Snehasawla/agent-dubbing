"""
Data Agent Module
Handles CSV data loading, validation, cleaning, and processing with robust error handling
and validation checks.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json
import hashlib
from datetime import datetime
from data_processor import DataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass

class DataAgent:
    """
    Data Agent responsible for loading, validating, cleaning, and processing CSV data.
    Integrates with DataProcessor for core processing logic while adding validation
    and tracking capabilities.
    """
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = str(Path(__file__).parent.parent / 'data')
        logging.info(f"Initializing DataAgent with data directory: {data_dir}")
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.validation_dir = self.data_dir / "validation"
        
        # Create necessary directories
        for dir_path in [self.raw_dir, self.processed_dir, self.validation_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize processor with no initial data loading
        self.processor = DataProcessor(data_path=str(self.data_dir))
        self.processor.processed_data = {}
        
        # Track processing history
        self.processing_history = []
    
    def validate_csv_structure(self, df, expected_columns=None, filename=""):
        """Validate CSV structure and data types"""
        issues = []
        
        # Check if empty
        if df.empty:
            raise DataValidationError(f"CSV file '{filename}' is empty")
        
        # Validate expected columns if provided
        if expected_columns:
            missing = set(expected_columns) - set(df.columns)
            if missing:
                issues.append(f"Missing required columns: {', '.join(missing)}")
        
        # Check for completely empty columns
        empty_cols = [col for col in df.columns if df[col].isna().all()]
        if empty_cols:
            issues.append(f"Completely empty columns: {', '.join(empty_cols)}")
        
        # Check data types and basic constraints
        for col in df.columns:
            col_issues = []
            values = df[col].dropna()
            
            # Numeric validation
            if df[col].dtype in ['int64', 'float64']:
                if values.min() < 0 and not col.startswith(('diff_', 'delta_', 'change_')):
                    col_issues.append('contains negative values')
            
            # String validation
            elif df[col].dtype == 'object':
                # Check for obviously malformed values
                if values.str.contains(r'[^\x00-\x7F]+').any():  # non-ASCII
                    col_issues.append('contains non-ASCII characters')
                if values.str.contains(r'[\{\}\[\]]').any():  # probable JSON/list fragments
                    col_issues.append('contains possible malformed data structures')
            
            if col_issues:
                issues.append(f"Column '{col}': {', '.join(col_issues)}")
        
        if issues:
            raise DataValidationError("\n".join(issues))
        
        return True
    
    def compute_data_hash(self, df):
        """Compute a hash of the dataframe for tracking changes"""
        return hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()
    
    def load_and_validate_csv(self, file_path, expected_columns=None):
        """Load a CSV file and validate its structure"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")
            
            # Try to determine encoding
            encodings = ['utf-8', 'latin1', 'iso-8859-1']
            df = None
            encoding_used = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise DataValidationError(f"Could not read CSV with any of the attempted encodings: {encodings}")
            
            # Validate structure
            self.validate_csv_structure(df, expected_columns, file_path.name)
            
            # Log success
            logger.info(f"✅ Successfully loaded and validated CSV: {file_path.name} (encoding: {encoding_used})")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error loading CSV {file_path}: {str(e)}")
            raise
    
    def clean_and_preprocess(self, df, dataset_type):
        """Clean and preprocess a dataset based on its type"""
        try:
            # Store original state hash
            original_hash = self.compute_data_hash(df)
            
            # Basic cleaning for all datasets
            df = df.copy()
            
            # Remove completely empty rows and columns
            df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
            
            # Handle specific dataset types
            if dataset_type == 'thesis':
                self.processor.thesis_data = df
                self.processor.clean_thesis_data()
                df = self.processor.processed_data['thesis_clean']
                
            elif dataset_type == 'papers':
                self.processor.papers_data = df
                self.processor.clean_papers_data()
                df = self.processor.processed_data['papers_clean']
            
            # Compute change hash and log
            cleaned_hash = self.compute_data_hash(df)
            
            processing_record = {
                'timestamp': datetime.now().isoformat(),
                'dataset_type': dataset_type,
                'rows_before': len(df),
                'rows_after': len(df),
                'columns_before': len(df.columns),
                'columns_after': len(df.columns),
                'original_hash': original_hash,
                'cleaned_hash': cleaned_hash
            }
            
            self.processing_history.append(processing_record)
            
            # Save processing record
            history_file = self.validation_dir / 'processing_history.json'
            with open(history_file, 'w') as f:
                json.dump(self.processing_history, f, indent=2)
            
            logger.info(f"✅ Successfully cleaned and preprocessed {dataset_type} dataset")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error preprocessing {dataset_type} dataset: {str(e)}")
            raise
    
    def export_data(self, df, filename, include_metadata=True):
        """Export processed data with optional metadata"""
        try:
            output_path = self.processed_dir / filename
            
            # Add metadata if requested
            if include_metadata:
                metadata = {
                    'exported_at': datetime.now().isoformat(),
                    'rows': len(df),
                    'columns': len(df.columns),
                    'data_types': df.dtypes.astype(str).to_dict(),
                    'null_counts': df.isnull().sum().to_dict(),
                    'data_hash': self.compute_data_hash(df)
                }
                
                metadata_path = output_path.with_suffix('.meta.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            # Export data
            df.to_csv(output_path, index=False)
            logger.info(f"✅ Exported processed data to {output_path}")
            
            if include_metadata:
                logger.info(f"✅ Exported metadata to {metadata_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Error exporting data to {filename}: {str(e)}")
            raise
    
    def process_uploaded_csv(self, file_path, dataset_type=None):
        """
        Process a newly uploaded CSV file through the complete pipeline:
        load → validate → clean → process → export
        """
        try:
            # Determine dataset type if not provided
            if dataset_type is None:
                filename = Path(file_path).name.lower()
                if 'thesis' in filename or 'annotation' in filename:
                    dataset_type = 'thesis'
                elif 'paper' in filename or 'research' in filename:
                    dataset_type = 'papers'
                else:
                    raise ValueError("Could not determine dataset type from filename. Please specify explicitly.")
            
            # Expected columns based on type
            expected_columns = {
                'thesis': ['section_title', 'level', 'estimated_pages', 'priority_for_extraction'],
                'papers': ['title', 'year', 'domain', 'citations', 'readability_score']
            }.get(dataset_type, None)
            
            # Load and validate
            logger.info(f"🔄 Processing {dataset_type} data from {file_path}")
            df = self.load_and_validate_csv(file_path, expected_columns)
            
            # Clean and preprocess
            processed_df = self.clean_and_preprocess(df, dataset_type)
            
            # Export with metadata
            output_filename = f"{dataset_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            exported_path = self.export_data(processed_df, output_filename, include_metadata=True)
            
            # Generate summary
            self.processor.create_summary_statistics()
            
            return {
                'status': 'success',
                'dataset_type': dataset_type,
                'input_file': str(file_path),
                'output_file': exported_path,
                'rows_processed': len(processed_df),
                'columns_processed': len(processed_df.columns)
            }
            
        except Exception as e:
            logger.error(f"❌ Processing pipeline failed: {str(e)}")
            return {
                'status': 'error',
                'dataset_type': dataset_type,
                'input_file': str(file_path),
                'error': str(e)
            }

def main():
    """Test the DataAgent with sample data"""
    agent = DataAgent()
    
    # Process thesis data
    thesis_file = "../data/debugging_agents_synthetic_annotations.csv"
    result = agent.process_uploaded_csv(thesis_file, dataset_type='thesis')
    print("\n📊 Thesis Processing Result:")
    print(json.dumps(result, indent=2))
    
    # Process papers data
    papers_file = "../data/synthetic_pdf_papers_dataset.csv"
    result = agent.process_uploaded_csv(papers_file, dataset_type='papers')
    print("\n📚 Papers Processing Result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()