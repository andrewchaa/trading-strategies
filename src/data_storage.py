"""
Data Storage Module

This module handles saving and loading historical forex data in CSV format
with organized directory structure and metadata tracking.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import pytz


class DataStorage:
    """
    Manage storage and retrieval of historical forex data in CSV format.
    
    Provides organized file structure, metadata tracking, and data integrity
    validation for historical candle data.
    
    Attributes:
        base_path (Path): Base directory for data storage
        logger (logging.Logger): Logger instance
    """
    
    def __init__(self, base_path: str = 'data/historical'):
        """
        Initialize the data storage handler.
        
        Args:
            base_path: Base directory path for storing CSV files
        """
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(__name__)
        
        # Create base directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Data storage initialized at: {self.base_path.absolute()}")
    
    def save_to_csv(
        self,
        df: pd.DataFrame,
        instrument: str,
        granularity: str,
        from_date: str,
        to_date: str,
        overwrite: bool = True
    ) -> str:
        """
        Save DataFrame to CSV file with metadata.
        
        Args:
            df: DataFrame with candle data
            instrument: Instrument name (e.g., 'EUR_USD')
            granularity: Candle granularity (e.g., 'H1')
            from_date: Start date of data
            to_date: End date of data
            overwrite: Whether to overwrite existing file
            
        Returns:
            Path to saved CSV file
            
        Raises:
            ValueError: If DataFrame is empty or missing required columns
            FileExistsError: If file exists and overwrite=False
        """
        if df.empty:
            raise ValueError("Cannot save empty DataFrame")
        
        required_columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"DataFrame missing required columns: {missing_columns}")
        
        # Create instrument directory
        instrument_dir = self.base_path / instrument
        instrument_dir.mkdir(exist_ok=True)
        
        # Generate filename
        from_date_str = self._format_date_for_filename(from_date)
        to_date_str = self._format_date_for_filename(to_date)
        filename = f"{instrument}_{granularity}_{from_date_str}_{to_date_str}.csv"
        file_path = instrument_dir / filename
        
        # Check if file exists
        if file_path.exists() and not overwrite:
            raise FileExistsError(
                f"File already exists: {file_path}\n"
                f"Set overwrite=True to replace it or use append_to_existing()"
            )
        
        # Prepare metadata
        metadata = self._generate_metadata(df, instrument, granularity, from_date, to_date)
        
        # Write to CSV with metadata as comments
        with open(file_path, 'w') as f:
            # Write metadata as comments
            for line in metadata:
                f.write(f"# {line}\n")
            
            # Write data
            df.to_csv(f, index=False)
        
        self.logger.info(f"Saved {len(df)} records to: {file_path}")
        return str(file_path)
    
    def load_from_csv(self, file_path: str, skip_metadata: bool = True) -> pd.DataFrame:
        """
        Load DataFrame from CSV file.
        
        Args:
            file_path: Path to CSV file
            skip_metadata: Whether to skip metadata comment lines
            
        Returns:
            DataFrame with candle data
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read CSV, skipping comment lines
        df = pd.read_csv(file_path, comment='#' if skip_metadata else None)
        
        # Convert time column to datetime
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        
        self.logger.info(f"Loaded {len(df)} records from: {file_path}")
        return df
    
    def append_to_existing(
        self,
        df: pd.DataFrame,
        file_path: str,
        remove_duplicates: bool = True
    ) -> str:
        """
        Append data to existing CSV file.
        
        Args:
            df: DataFrame with new candle data
            file_path: Path to existing CSV file
            remove_duplicates: Whether to remove duplicate timestamps
            
        Returns:
            Path to updated CSV file
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(
                f"File not found: {file_path}\n"
                f"Use save_to_csv() to create a new file"
            )
        
        # Load existing data
        existing_df = self.load_from_csv(file_path)
        
        # Combine with new data
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        
        # Remove duplicates if requested
        if remove_duplicates:
            original_len = len(combined_df)
            combined_df = combined_df.drop_duplicates(subset=['time'], keep='last')
            removed = original_len - len(combined_df)
            if removed > 0:
                self.logger.info(f"Removed {removed} duplicate records")
        
        # Sort by time
        combined_df = combined_df.sort_values('time').reset_index(drop=True)
        
        # Save back to file (extract metadata from filename)
        parts = Path(file_path).stem.split('_')
        if len(parts) >= 4:
            instrument = '_'.join(parts[:-3])
            granularity = parts[-3]
            from_date = parts[-2]
            to_date = parts[-1]
            
            return self.save_to_csv(
                df=combined_df,
                instrument=instrument,
                granularity=granularity,
                from_date=from_date,
                to_date=to_date,
                overwrite=True
            )
        else:
            # Fallback: just overwrite the file
            combined_df.to_csv(file_path, index=False)
            self.logger.info(f"Updated {file_path} with {len(combined_df)} records")
            return str(file_path)
    
    def get_existing_data_range(self, file_path: str) -> Tuple[datetime, datetime]:
        """
        Get the date range of existing data in a CSV file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Tuple of (start_datetime, end_datetime)
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        df = self.load_from_csv(file_path)
        
        if df.empty or 'time' not in df.columns:
            raise ValueError(f"File {file_path} has no valid time data")
        
        start_time = df['time'].min()
        end_time = df['time'].max()
        
        return (start_time, end_time)
    
    def list_available_data(self, instrument: Optional[str] = None) -> pd.DataFrame:
        """
        List all available CSV files with their metadata.
        
        Args:
            instrument: Optional instrument filter
            
        Returns:
            DataFrame with columns: instrument, granularity, from_date, to_date, 
                                    file_path, record_count
        """
        files_info = []
        
        # Determine which directories to scan
        if instrument:
            search_dirs = [self.base_path / instrument]
        else:
            search_dirs = [d for d in self.base_path.iterdir() if d.is_dir()]
        
        for dir_path in search_dirs:
            if not dir_path.exists():
                continue
            
            for csv_file in dir_path.glob('*.csv'):
                try:
                    # Parse filename
                    parts = csv_file.stem.split('_')
                    if len(parts) >= 4:
                        instr = '_'.join(parts[:-3])
                        gran = parts[-3]
                        from_d = parts[-2]
                        to_d = parts[-1]
                        
                        # Count records (quick way)
                        df = self.load_from_csv(str(csv_file))
                        
                        files_info.append({
                            'instrument': instr,
                            'granularity': gran,
                            'from_date': from_d,
                            'to_date': to_d,
                            'file_path': str(csv_file),
                            'record_count': len(df)
                        })
                except Exception as e:
                    self.logger.warning(f"Error reading {csv_file}: {str(e)}")
                    continue
        
        return pd.DataFrame(files_info)
    
    def _format_date_for_filename(self, date_str: str) -> str:
        """
        Format date string for use in filename.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Date string in YYYYMMDD format
        """
        try:
            # Try parsing as datetime
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%Y%m%d')
        except:
            # If parsing fails, try to extract YYYYMMDD pattern
            import re
            match = re.search(r'(\d{4})-?(\d{2})-?(\d{2})', date_str)
            if match:
                return ''.join(match.groups())
            return date_str.replace('-', '').replace(':', '')[:8]
    
    def _generate_metadata(
        self,
        df: pd.DataFrame,
        instrument: str,
        granularity: str,
        from_date: str,
        to_date: str
    ) -> list:
        """
        Generate metadata lines for CSV file header.
        
        Returns:
            List of metadata strings
        """
        now = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')
        
        metadata = [
            f"Instrument: {instrument}",
            f"Granularity: {granularity}",
            f"Date Range: {from_date} to {to_date}",
            f"Records: {len(df)}",
            f"Retrieved: {now}",
            f"Columns: {', '.join(df.columns)}"
        ]
        
        return metadata
