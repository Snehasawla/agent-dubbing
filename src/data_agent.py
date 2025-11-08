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
    
    def _make_json_serializable(self, obj):
        """Recursively convert numpy/pandas types to JSON-serializable primitives."""
        if isinstance(obj, dict):
            return {self._make_json_serializable(key): self._make_json_serializable(value) for key, value in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [self._make_json_serializable(item) for item in obj]
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    def validate_csv_structure(self, df, expected_columns=None, filename=""):
        """Validate CSV structure and data types"""
        issues = []
        
        # Check if empty
        if df.empty:
            raise DataValidationError(f"CSV file '{filename}' is empty")
        
        # Validate expected columns if provided (warn but don't fail)
        if expected_columns:
            missing = set(expected_columns) - set(df.columns)
            if missing:
                # Log warning but don't treat as error - allow processing to continue
                logger.warning(f"Expected columns not found: {', '.join(missing)}. Processing will continue with available columns.")
                # Don't add to issues list - just log a warning
        
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
                    df = self._normalize_headers(df)
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise DataValidationError(f"Could not read CSV with any of the attempted encodings: {encodings}")
            
            # Normalize headers
            df = self._normalize_headers(df)

            # Validate structure
            self.validate_csv_structure(df, expected_columns, file_path.name)
            
            # Log success
            logger.info(f"✅ Successfully loaded and validated CSV: {file_path.name} (encoding: {encoding_used})")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error loading CSV {file_path}: {str(e)}")
            raise
    
    def _clean_column_name(self, name, index):
        """Ensure column names are stripped, human-readable, and non-empty."""
        cleaned = str(name).strip() if name is not None else ''
        if not cleaned or cleaned.lower().startswith('unnamed'):
            cleaned = f'column_{index + 1}'
        return cleaned

    def _normalize_headers(self, df):
        """Normalize dataframe headers, handling cases where the first row contains actual column names."""
        if df.empty:
            return df

        unnamed_count = sum(str(col).startswith('Unnamed') or str(col).strip() == '' for col in df.columns)
        use_first_row_as_header = unnamed_count >= max(1, len(df.columns) // 2)

        if use_first_row_as_header:
            candidate_header = df.iloc[0].tolist()
            if any(str(value).strip() for value in candidate_header):
                new_columns = []
                seen = {}
                for idx, value in enumerate(candidate_header):
                    base_name = self._clean_column_name(value, idx)
                    name = base_name
                    counter = 1
                    while name in seen:
                        counter += 1
                        name = f"{base_name}_{counter}"
                    seen[name] = True
                    new_columns.append(name)
                df = df.iloc[1:].reset_index(drop=True)
                df.columns = new_columns
        else:
            df.columns = [self._clean_column_name(col, idx) for idx, col in enumerate(df.columns)]

        # Second pass to ensure no lingering blank or duplicate names
        seen_final = {}
        final_columns = []
        for idx, col in enumerate(df.columns):
            name = self._clean_column_name(col, idx)
            counter = 1
            base_name = name
            while name in seen_final:
                counter += 1
                name = f"{base_name}_{counter}"
            seen_final[name] = True
            final_columns.append(name)
        df.columns = final_columns

        return df
    
    def remove_nulls(self, df, row_threshold=0.5, col_threshold=0.5):
        """
        Remove nulls from the dataframe
        
        Args:
            df: DataFrame to clean
            row_threshold: Remove rows with more than this fraction of nulls (0.5 = 50%)
            col_threshold: Remove columns with more than this fraction of nulls (0.5 = 50%)
        
        Returns:
            Cleaned DataFrame and statistics about what was removed
        """
        df = df.copy()
        original_rows = len(df)
        original_cols = len(df.columns)
        
        stats = {
            'rows_removed': 0,
            'columns_removed': [],
            'nulls_filled': 0
        }
        
        # Remove columns with too many nulls
        null_percentage_per_col = df.isnull().sum() / len(df)
        cols_to_drop = null_percentage_per_col[null_percentage_per_col > col_threshold].index.tolist()
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            stats['columns_removed'] = cols_to_drop
            logger.info(f"🗑️ Removed {len(cols_to_drop)} columns with >{col_threshold*100}% nulls: {cols_to_drop}")
        
        # Remove rows with too many nulls
        null_percentage_per_row = df.isnull().sum(axis=1) / len(df.columns)
        rows_to_drop = null_percentage_per_row[null_percentage_per_row > row_threshold].index
        if len(rows_to_drop) > 0:
            df = df.drop(index=rows_to_drop)
            stats['rows_removed'] = len(rows_to_drop)
            logger.info(f"🗑️ Removed {len(rows_to_drop)} rows with >{row_threshold*100}% nulls")
        
        # Fill remaining nulls in numeric columns with median
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                median_val = df[col].median()
                if pd.notna(median_val):
                    df[col] = df[col].fillna(median_val)
                    stats['nulls_filled'] += null_count
                    logger.info(f"📊 Filled {null_count} nulls in '{col}' with median: {median_val}")
        
        # Fill remaining nulls in categorical columns with mode
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val[0])
                    stats['nulls_filled'] += null_count
                    logger.info(f"📊 Filled {null_count} nulls in '{col}' with mode: {mode_val[0]}")
                else:
                    # If no mode, fill with 'Unknown'
                    df[col] = df[col].fillna('Unknown')
                    stats['nulls_filled'] += null_count
                    logger.info(f"📊 Filled {null_count} nulls in '{col}' with 'Unknown'")
        
        logger.info(f"✅ Null removal complete: {original_rows - len(df)} rows removed, {original_cols - len(df.columns)} columns removed, {stats['nulls_filled']} nulls filled")
        return df, self._make_json_serializable(stats)
    
    def remove_outliers(self, df, method='iqr', threshold=3.0):
        """
        Remove outliers from numeric columns
        
        Args:
            df: DataFrame to clean
            method: 'iqr' (Interquartile Range) or 'zscore' (Z-score method)
            threshold: For IQR: multiplier (default 1.5), For Z-score: standard deviations (default 3.0)
        
        Returns:
            Cleaned DataFrame and statistics about outliers removed
        """
        df = df.copy()
        original_rows = len(df)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            logger.info("ℹ️ No numeric columns found, skipping outlier removal")
            return df, {'outliers_removed': 0, 'columns_processed': []}
        
        stats = {
            'outliers_removed': 0,
            'columns_processed': [],
            'outliers_per_column': {}
        }
        
        outlier_indices = set()
        
        for col in numeric_cols:
            if df[col].isna().all():
                continue
                
            if method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                if IQR == 0:  # Skip if no variance
                    continue
                
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                
                col_outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)].index
                
            elif method == 'zscore':
                mean = df[col].mean()
                std = df[col].std()
                
                if std == 0:  # Skip if no variance
                    continue
                
                z_scores = np.abs((df[col] - mean) / std)
                col_outliers = df[z_scores > threshold].index
            
            else:
                logger.warning(f"Unknown outlier detection method: {method}, skipping")
                continue
            
            if len(col_outliers) > 0:
                outlier_indices.update(col_outliers)
                stats['outliers_per_column'][col] = len(col_outliers)
                logger.info(f"🔍 Found {len(col_outliers)} outliers in '{col}' using {method} method")
        
        # Remove rows with outliers
        if outlier_indices:
            df = df.drop(index=list(outlier_indices))
            stats['outliers_removed'] = len(outlier_indices)
            stats['columns_processed'] = numeric_cols
            logger.info(f"🗑️ Removed {len(outlier_indices)} rows containing outliers")
        else:
            logger.info("✅ No outliers detected")
        
        logger.info(f"✅ Outlier removal complete: {original_rows - len(df)} rows removed")
        return df, self._make_json_serializable(stats)
    
    def clean_and_preprocess(self, df, dataset_type):
        """Clean and preprocess a dataset based on its type"""
        try:
            # Store original state hash
            original_hash = self.compute_data_hash(df)
            original_rows = len(df)
            original_cols = len(df.columns)
            
            # Basic cleaning for all datasets
            df = df.copy()
            
            # Step 1: Remove completely empty rows and columns
            df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
            
            # Step 2: Comprehensive null removal
            df, null_stats = self.remove_nulls(df, row_threshold=0.5, col_threshold=0.5)
            
            # Step 3: Remove outliers from numeric columns
            df, outlier_stats = self.remove_outliers(df, method='iqr', threshold=1.5)
            
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
                'rows_before': original_rows,
                'rows_after': len(df),
                'columns_before': original_cols,
                'columns_after': len(df.columns),
                'rows_removed': original_rows - len(df),
                'columns_removed': original_cols - len(df.columns),
                'null_removal_stats': null_stats,
                'outlier_removal_stats': outlier_stats,
                'original_hash': original_hash,
                'cleaned_hash': cleaned_hash
            }
            
            processing_record = self._make_json_serializable(processing_record)
            self.processing_history.append(processing_record)
            
            # Save processing record
            history_file = self.validation_dir / 'processing_history.json'
            with open(history_file, 'w') as f:
                json.dump(self.processing_history, f, indent=2)
            
            logger.info(f"✅ Successfully cleaned and preprocessed {dataset_type} dataset")
            return df, null_stats, outlier_stats
            
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
                    # Try to auto-detect by reading the CSV and checking columns
                    try:
                        df_temp = pd.read_csv(file_path, nrows=10)
                        df_temp = self._normalize_headers(df_temp)
                        columns_lower = [col.lower() for col in df_temp.columns]
                        
                        # Check for thesis-specific columns
                        thesis_indicators = ['section_title', 'level', 'estimated_pages', 'priority_for_extraction', 'difficulty_score']
                        # Check for papers-specific columns
                        papers_indicators = ['title', 'year', 'domain', 'citations', 'readability_score']
                        
                        thesis_match = sum(1 for ind in thesis_indicators if any(ind in col for col in columns_lower))
                        papers_match = sum(1 for ind in papers_indicators if any(ind in col for col in columns_lower))
                        
                        if thesis_match >= 2:
                            dataset_type = 'thesis'
                            logger.info(f"Auto-detected dataset type as 'thesis' based on columns")
                        elif papers_match >= 2:
                            dataset_type = 'papers'
                            logger.info(f"Auto-detected dataset type as 'papers' based on columns")
                        else:
                            # Default to thesis if we can't determine
                            dataset_type = 'thesis'
                            logger.warning(f"Could not determine dataset type, defaulting to 'thesis'. Columns found: {list(df_temp.columns)}")
                    except Exception as e:
                        logger.warning(f"Error during auto-detection: {e}, defaulting to 'thesis'")
                        dataset_type = 'thesis'
            
            # Expected columns based on type
            expected_columns = {
                'thesis': ['section_title', 'level', 'estimated_pages', 'priority_for_extraction'],
                'papers': ['title', 'year', 'domain', 'citations', 'readability_score']
            }.get(dataset_type, None)
            
            # Load and validate
            logger.info(f"🔄 Processing {dataset_type} data from {file_path}")
            df = self.load_and_validate_csv(file_path, expected_columns)
            
            # Store original dimensions before cleaning
            original_rows = len(df)
            original_cols = len(df.columns)
            
            # Clean and preprocess
            processed_df, null_stats, outlier_stats = self.clean_and_preprocess(df, dataset_type)
            
            # Export with metadata
            output_filename = f"{dataset_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            exported_path = self.export_data(processed_df, output_filename, include_metadata=True)
            
            # Generate summary
            self.processor.create_summary_statistics()
            
            cleaning_summary = {
                'status': 'success',
                'dataset_type': dataset_type,
                'input_file': str(file_path),
                'output_file': exported_path,
                'rows_processed': len(processed_df),
                'columns_processed': len(processed_df.columns),
                'cleaning_stats': {
                    'rows_before': original_rows,
                    'rows_after': len(processed_df),
                    'rows_removed': original_rows - len(processed_df),
                    'columns_before': original_cols,
                    'columns_after': len(processed_df.columns),
                    'columns_removed': original_cols - len(processed_df.columns),
                    'null_removal': null_stats,
                    'outlier_removal': outlier_stats
                }
            }
            
            return self._make_json_serializable(cleaning_summary)
            
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