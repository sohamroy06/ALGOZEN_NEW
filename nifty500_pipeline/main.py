"""
NIFTY 500 Data Pipeline - Main Orchestrator
===========================================
Production-grade orchestrator that runs the complete data pipeline.

Pipeline stages:
1. Fetch NIFTY 500 tickers
2. Download historical OHLCV data
3. Clean and validate data
4. Generate reports

Author: Quantitative Infrastructure Team
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import argparse

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

# Import pipeline modules
from fetch_tickers import NIFTY500Fetcher
from download_data import NIFTY500Downloader
from clean_data import NIFTY500DataCleaner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NIFTY500Pipeline:
    """
    Complete production pipeline for NIFTY 500 historical data.
    
    This pipeline:
    1. Fetches current NIFTY 500 constituents
    2. Downloads historical data from Yahoo Finance
    3. Cleans and validates the data
    4. Generates comprehensive reports
    
    WARNING: Data contains survivorship bias (only current constituents)
    """
    
    def __init__(self, start_date='2000-01-01', end_date=None, max_retries=3):
        """
        Initialize the pipeline.
        
        Args:
            start_date (str): Start date for historical data (YYYY-MM-DD)
            end_date (str): End date (defaults to today)
            max_retries (int): Max retry attempts for downloads
        """
        self.start_date = start_date
        self.end_date = end_date
        self.max_retries = max_retries
        
        # Ensure all directories exist
        self._setup_directories()
        
        # Pipeline state
        self.tickers = []
        self.raw_data = None
        self.clean_data = None
        
    def _setup_directories(self):
        """Create necessary directories."""
        directories = [
            'data/raw',
            'data/processed',
            'data/reports',
            'logs'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def run_stage_1_fetch_tickers(self):
        """
        Stage 1: Fetch NIFTY 500 constituent tickers.
        
        Returns:
            list: List of ticker symbols
        """
        logger.info("=" * 80)
        logger.info("STAGE 1: FETCHING NIFTY 500 TICKERS")
        logger.info("=" * 80)
        
        try:
            fetcher = NIFTY500Fetcher(output_dir='data/raw')
            self.tickers = fetcher.fetch_tickers()
            fetcher.save_tickers(self.tickers)
            
            logger.info(f"✓ Stage 1 completed: {len(self.tickers)} tickers fetched")
            return self.tickers
            
        except Exception as e:
            logger.error(f"✗ Stage 1 FAILED: {e}")
            raise
    
    def run_stage_2_download_data(self):
        """
        Stage 2: Download historical data for all tickers.
        
        Returns:
            pd.DataFrame: Raw downloaded data
        """
        logger.info("=" * 80)
        logger.info("STAGE 2: DOWNLOADING HISTORICAL DATA")
        logger.info("=" * 80)
        
        try:
            downloader = NIFTY500Downloader(
                start_date=self.start_date,
                end_date=self.end_date,
                max_retries=self.max_retries
            )
            
            # Load tickers from file
            tickers = downloader.load_tickers()
            
            # Download data
            self.raw_data = downloader.download_all(tickers)
            
            # Save and report
            downloader.save_raw_data(self.raw_data)
            downloader.save_download_report()
            downloader.print_summary()
            
            logger.info(f"✓ Stage 2 completed: {len(self.raw_data)} records downloaded")
            return self.raw_data
            
        except Exception as e:
            logger.error(f"✗ Stage 2 FAILED: {e}")
            raise
    
    def run_stage_3_clean_data(self):
        """
        Stage 3: Clean and validate downloaded data.
        
        Returns:
            pd.DataFrame: Cleaned data
        """
        logger.info("=" * 80)
        logger.info("STAGE 3: CLEANING AND VALIDATING DATA")
        logger.info("=" * 80)
        
        try:
            cleaner = NIFTY500DataCleaner()
            
            # Load raw data
            df = cleaner.load_raw_data()
            
            # Clean
            df = cleaner.remove_duplicates(df)
            df = cleaner.sort_data(df)
            df = cleaner.handle_missing_values(df)
            df = cleaner.validate_data(df)
            df = cleaner.add_metadata_columns(df)
            
            # Calculate stats and save
            cleaner.calculate_statistics(df)
            cleaner.save_processed_data(df)
            cleaner.save_quality_report()
            cleaner.print_summary()
            
            self.clean_data = df
            
            logger.info(f"✓ Stage 3 completed: {len(df)} records cleaned")
            return df
            
        except Exception as e:
            logger.error(f"✗ Stage 3 FAILED: {e}")
            raise
    
    def run_full_pipeline(self):
        """
        Execute the complete pipeline end-to-end.
        
        Returns:
            dict: Pipeline execution summary
        """
        pipeline_start = datetime.now()
        
        logger.info("=" * 80)
        logger.info("NIFTY 500 DATA PIPELINE - FULL EXECUTION")
        logger.info(f"Start Time: {pipeline_start.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Date Range: {self.start_date} to {self.end_date or 'TODAY'}")
        logger.info("=" * 80)
        
        try:
            # Stage 1: Fetch tickers
            self.run_stage_1_fetch_tickers()
            
            # Stage 2: Download data
            self.run_stage_2_download_data()
            
            # Stage 3: Clean data
            self.run_stage_3_clean_data()
            
            # Pipeline completed
            pipeline_end = datetime.now()
            duration = pipeline_end - pipeline_start
            
            # Final summary
            logger.info("=" * 80)
            logger.info("PIPELINE EXECUTION SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Status:               SUCCESS ✓")
            logger.info(f"Tickers fetched:      {len(self.tickers)}")
            logger.info(f"Records downloaded:   {len(self.raw_data):,}")
            logger.info(f"Records cleaned:      {len(self.clean_data):,}")
            logger.info(f"Start time:           {pipeline_start.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"End time:             {pipeline_end.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Total duration:       {duration}")
            logger.info("=" * 80)
            logger.info("")
            logger.info("OUTPUT FILES:")
            logger.info("  Processed Data:")
            logger.info("    - data/processed/nifty500_master.csv")
            logger.info("    - data/processed/nifty500_close_prices.csv")
            logger.info("    - data/processed/nifty500_volumes.csv")
            logger.info("  Reports:")
            logger.info("    - data/reports/download_summary.json")
            logger.info("    - data/reports/data_quality_report.json")
            logger.info("  Logs:")
            logger.info("    - logs/pipeline.log")
            logger.info("    - logs/download.log")
            logger.info("    - logs/cleaning.log")
            logger.info("=" * 80)
            
            return {
                'status': 'success',
                'tickers_count': len(self.tickers),
                'records_downloaded': len(self.raw_data),
                'records_cleaned': len(self.clean_data),
                'duration': str(duration)
            }
            
        except Exception as e:
            pipeline_end = datetime.now()
            duration = pipeline_end - pipeline_start
            
            logger.error("=" * 80)
            logger.error("PIPELINE EXECUTION FAILED")
            logger.error("=" * 80)
            logger.error(f"Error: {e}")
            logger.error(f"Duration before failure: {duration}")
            logger.error("=" * 80)
            
            raise


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='NIFTY 500 Historical Data Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with defaults (2000-01-01 to today)
  python main.py
  
  # Specify custom date range
  python main.py --start-date 2010-01-01 --end-date 2023-12-31
  
  # Run individual stages
  python main.py --stage fetch
  python main.py --stage download
  python main.py --stage clean
        """
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default='2000-01-01',
        help='Start date for historical data (YYYY-MM-DD). Default: 2000-01-01'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        help='End date for historical data (YYYY-MM-DD). Default: today'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts for failed downloads. Default: 3'
    )
    
    parser.add_argument(
        '--stage',
        type=str,
        choices=['fetch', 'download', 'clean', 'all'],
        default='all',
        help='Pipeline stage to run. Default: all'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()
    
    # Initialize pipeline
    pipeline = NIFTY500Pipeline(
        start_date=args.start_date,
        end_date=args.end_date,
        max_retries=args.max_retries
    )
    
    try:
        # Run selected stage(s)
        if args.stage == 'all':
            pipeline.run_full_pipeline()
        elif args.stage == 'fetch':
            pipeline.run_stage_1_fetch_tickers()
        elif args.stage == 'download':
            pipeline.run_stage_2_download_data()
        elif args.stage == 'clean':
            pipeline.run_stage_3_clean_data()
        
        return 0
        
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
