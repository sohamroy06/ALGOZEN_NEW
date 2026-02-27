"""
NIFTY 500 Data Cleaning and Validation Module
==============================================
Cleans, validates, and structures historical stock data for analysis.

Features:
- Removes duplicates
- Sorts data chronologically
- Handles missing values intelligently
- Validates data quality
- Creates multiple output formats
- Generates data quality reports

Author: Quantitative Infrastructure Team
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cleaning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NIFTY500DataCleaner:
    """
    Production-grade data cleaning and validation for NIFTY 500 datasets.
    """
    
    def __init__(self, raw_data_path='data/raw/nifty500_raw_data.csv',
                 processed_dir='data/processed', reports_dir='data/reports'):
        """
        Initialize the data cleaner.
        
        Args:
            raw_data_path (str): Path to raw data CSV
            processed_dir (str): Directory for processed data
            reports_dir (str): Directory for quality reports
        """
        self.raw_data_path = Path(raw_data_path)
        self.processed_dir = Path(processed_dir)
        self.reports_dir = Path(reports_dir)
        
        # Create directories
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
        
        # Data quality metrics
        self.quality_metrics = {
            'initial_rows': 0,
            'final_rows': 0,
            'duplicates_removed': 0,
            'missing_values_filled': 0,
            'tickers_processed': 0,
            'date_range': {},
            'data_quality_score': 0.0
        }
    
    def load_raw_data(self):
        """
        Load raw data from CSV file.
        
        Returns:
            pd.DataFrame: Raw dataset
        """
        if not self.raw_data_path.exists():
            raise FileNotFoundError(
                f"Raw data file not found: {self.raw_data_path}\n"
                "Please run download_data.py first."
            )
        
        logger.info(f"Loading raw data from {self.raw_data_path}")
        df = pd.read_csv(self.raw_data_path, parse_dates=['Date'])
        
        self.quality_metrics['initial_rows'] = len(df)
        logger.info(f"Loaded {len(df):,} rows, {df['Ticker'].nunique()} unique tickers")
        
        return df
    
    def remove_duplicates(self, df):
        """
        Remove duplicate records based on Date and Ticker.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: Deduplicated dataframe
        """
        initial_count = len(df)
        
        # Remove duplicates, keeping the last occurrence (most recent data)
        df = df.drop_duplicates(subset=['Date', 'Ticker'], keep='last')
        
        duplicates_removed = initial_count - len(df)
        self.quality_metrics['duplicates_removed'] = duplicates_removed
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed:,} duplicate records")
        else:
            logger.info("No duplicates found")
        
        return df
    
    def sort_data(self, df):
        """
        Sort data chronologically by Ticker and Date.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: Sorted dataframe
        """
        logger.info("Sorting data by Ticker and Date")
        df = df.sort_values(['Ticker', 'Date']).reset_index(drop=True)
        return df
    
    def handle_missing_values(self, df):
        """
        Handle missing values intelligently.
        
        Strategy:
        - OHLC: Forward fill within ticker (assumption: market didn't trade)
        - Volume: Fill with 0 (no trading volume)
        - Price columns: Never backward fill (prevents look-ahead bias)
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: Cleaned dataframe
        """
        logger.info("Handling missing values")
        
        initial_nulls = df.isnull().sum().sum()
        
        # Sort by ticker and date first
        df = df.sort_values(['Ticker', 'Date'])
        
        # Group by ticker for proper forward filling
        price_columns = ['Open', 'High', 'Low', 'Close']
        
        for col in price_columns:
            if col in df.columns:
                # Forward fill within each ticker group
                df[col] = df.groupby('Ticker')[col].ffill()
        
        # Fill remaining Volume nulls with 0
        if 'Volume' in df.columns:
            df['Volume'] = df['Volume'].fillna(0)
        
        # Drop rows where Close price is still null (beginning of series)
        if 'Close' in df.columns:
            df = df.dropna(subset=['Close'])
        
        final_nulls = df.isnull().sum().sum()
        filled = initial_nulls - final_nulls
        
        self.quality_metrics['missing_values_filled'] = filled
        logger.info(f"Handled {filled} missing values")
        
        return df
    
    def validate_data(self, df):
        """
        Validate data quality and log warnings.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: Validated dataframe
        """
        logger.info("Validating data quality")
        
        issues = []
        
        # Check for negative prices
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            if col in df.columns:
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    issues.append(f"{col}: {negative_count} negative values")
                    # Remove negative prices
                    df = df[df[col] >= 0]
        
        # Check for negative volumes
        if 'Volume' in df.columns:
            negative_vol = (df['Volume'] < 0).sum()
            if negative_vol > 0:
                issues.append(f"Volume: {negative_vol} negative values")
                df.loc[df['Volume'] < 0, 'Volume'] = 0
        
        # Check for High < Low (impossible)
        if 'High' in df.columns and 'Low' in df.columns:
            invalid_hl = (df['High'] < df['Low']).sum()
            if invalid_hl > 0:
                issues.append(f"{invalid_hl} rows where High < Low")
                # Swap High and Low
                mask = df['High'] < df['Low']
                df.loc[mask, ['High', 'Low']] = df.loc[mask, ['Low', 'High']].values
        
        # Check for Close outside High-Low range
        if all(col in df.columns for col in ['Close', 'High', 'Low']):
            outside_range = ((df['Close'] > df['High']) | (df['Close'] < df['Low'])).sum()
            if outside_range > 0:
                issues.append(f"{outside_range} rows where Close outside High-Low range")
        
        if issues:
            logger.warning("Data quality issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("No data quality issues detected")
        
        return df
    
    def add_metadata_columns(self, df):
        """
        Add useful metadata columns for trading strategies.
        
        Args:
            df (pd.DataFrame): Input dataframe
            
        Returns:
            pd.DataFrame: Enhanced dataframe
        """
        logger.info("Adding metadata columns")
        
        # Add trading day of week (for seasonality analysis)
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        
        # Add year and month for grouping
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        
        # Add placeholder for transaction costs (to be configured per strategy)
        # Typical values: 0.0003 (0.03%) for institutional, 0.001 (0.1%) for retail
        df['TransactionCostBps'] = 3.0  # 3 basis points = 0.03%
        
        logger.info("Added metadata columns: DayOfWeek, Year, Month, TransactionCostBps")
        
        return df
    
    def calculate_statistics(self, df):
        """
        Calculate dataset statistics.
        
        Args:
            df (pd.DataFrame): Cleaned dataframe
        """
        self.quality_metrics['final_rows'] = len(df)
        self.quality_metrics['tickers_processed'] = df['Ticker'].nunique()
        
        # Date range statistics
        self.quality_metrics['date_range'] = {
            'earliest': df['Date'].min().strftime('%Y-%m-%d'),
            'latest': df['Date'].max().strftime('%Y-%m-%d'),
            'total_days': (df['Date'].max() - df['Date'].min()).days,
            'trading_days': df['Date'].nunique()
        }
        
        # Calculate average years of data per ticker
        ticker_stats = df.groupby('Ticker').agg({
            'Date': ['min', 'max', 'count']
        })
        ticker_stats.columns = ['min_date', 'max_date', 'records']
        ticker_stats['years'] = (ticker_stats['max_date'] - ticker_stats['min_date']).dt.days / 365.25
        
        avg_years = ticker_stats['years'].mean()
        
        # Data quality score (0-100)
        retention_rate = self.quality_metrics['final_rows'] / max(self.quality_metrics['initial_rows'], 1)
        completeness = 1 - (self.quality_metrics['missing_values_filled'] / max(self.quality_metrics['initial_rows'], 1))
        quality_score = (retention_rate * 0.5 + completeness * 0.5) * 100
        
        self.quality_metrics['data_quality_score'] = round(quality_score, 2)
        self.quality_metrics['average_years_of_data'] = round(avg_years, 2)
        
    def save_processed_data(self, df):
        """
        Save processed data in multiple formats.
        
        Args:
            df (pd.DataFrame): Cleaned dataframe
            
        Returns:
            dict: Paths to saved files
        """
        logger.info("Saving processed data")
        
        saved_files = {}
        
        # 1. Save complete dataset (Multi-index format: Date x Ticker)
        master_path = self.processed_dir / 'nifty500_master.csv'
        df.to_csv(master_path, index=False)
        saved_files['master'] = master_path
        logger.info(f"Saved master dataset to {master_path}")
        
        # 2. Save close prices only (wide format for quick analysis)
        close_pivot = df.pivot(index='Date', columns='Ticker', values='Close')
        close_path = self.processed_dir / 'nifty500_close_prices.csv'
        close_pivot.to_csv(close_path)
        saved_files['close_prices'] = close_path
        logger.info(f"Saved close prices to {close_path}")
        
        # 3. Save volume data (for liquidity analysis)
        if 'Volume' in df.columns:
            volume_pivot = df.pivot(index='Date', columns='Ticker', values='Volume')
            volume_path = self.processed_dir / 'nifty500_volumes.csv'
            volume_pivot.to_csv(volume_path)
            saved_files['volumes'] = volume_path
            logger.info(f"Saved volumes to {volume_path}")
        
        return saved_files
    
    def convert_to_native_types(self, obj):
        """
        Convert numpy/pandas types to native Python types for JSON serialization.
        
        Args:
            obj: Object to convert (dict, list, numpy type, etc.)
            
        Returns:
            Object with all numpy/pandas types converted to native Python types
        """
        if isinstance(obj, dict):
            return {key: self.convert_to_native_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_to_native_types(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def save_quality_report(self):
        """
        Save data quality report.
        """
        report_path = self.reports_dir / 'data_quality_report.json'
        
        report = {
            'report_date': datetime.now().isoformat(),
            'metrics': self.quality_metrics
        }
        
        # Convert numpy types to native Python types for JSON serialization
        report = self.convert_to_native_types(report)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Saved quality report to {report_path}")
        
        return report_path
    
    def print_summary(self):
        """Print cleaning summary statistics."""
        logger.info("=" * 70)
        logger.info("DATA CLEANING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Initial rows:             {self.quality_metrics['initial_rows']:,}")
        logger.info(f"Final rows:               {self.quality_metrics['final_rows']:,}")
        logger.info(f"Duplicates removed:       {self.quality_metrics['duplicates_removed']:,}")
        logger.info(f"Missing values handled:   {self.quality_metrics['missing_values_filled']:,}")
        logger.info(f"Tickers processed:        {self.quality_metrics['tickers_processed']}")
        logger.info(f"Average years of data:    {self.quality_metrics['average_years_of_data']}")
        logger.info(f"Earliest date:            {self.quality_metrics['date_range']['earliest']}")
        logger.info(f"Latest date:              {self.quality_metrics['date_range']['latest']}")
        logger.info(f"Data quality score:       {self.quality_metrics['data_quality_score']}/100")
        logger.info("=" * 70)


def main():
    """Main execution function."""
    logger.info("=" * 70)
    logger.info("NIFTY 500 DATA CLEANING AND VALIDATION")
    logger.info("=" * 70)
    
    cleaner = NIFTY500DataCleaner()
    
    try:
        # Load raw data
        df = cleaner.load_raw_data()
        
        # Clean data
        df = cleaner.remove_duplicates(df)
        df = cleaner.sort_data(df)
        df = cleaner.handle_missing_values(df)
        df = cleaner.validate_data(df)
        df = cleaner.add_metadata_columns(df)
        
        # Calculate statistics
        cleaner.calculate_statistics(df)
        
        # Save processed data
        saved_files = cleaner.save_processed_data(df)
        
        # Save quality report
        cleaner.save_quality_report()
        
        # Print summary
        cleaner.print_summary()
        
        logger.info("=" * 70)
        logger.info("SUCCESS: Data cleaning completed")
        logger.info("=" * 70)
        
        return df
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
