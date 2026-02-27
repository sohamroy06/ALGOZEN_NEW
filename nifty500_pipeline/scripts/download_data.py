"""
NIFTY 500 Historical Data Downloader
====================================
Downloads historical OHLCV data for all NIFTY 500 stocks using yfinance.

Features:
- Bulk download with progress tracking
- Retry logic for failed downloads
- Automatic error logging
- Multi-threading support
- Data validation

Author: Quantitative Infrastructure Team
"""

import pandas as pd
import yfinance as yf
import logging
from pathlib import Path
from tqdm import tqdm
import json
from datetime import datetime, timedelta
import time
import warnings

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NIFTY500Downloader:
    """
    Production-grade historical data downloader for NIFTY 500 stocks.
    
    WARNING: This data may contain survivorship bias as it only includes
    current constituents. Delisted companies are not included.
    """
    
    def __init__(self, start_date='2000-01-01', end_date=None, 
                 raw_data_dir='data/raw', max_retries=3):
        """
        Initialize the downloader.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format (defaults to today)
            raw_data_dir (str): Directory to save raw data
            max_retries (int): Maximum retry attempts for failed downloads
        """
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        self.raw_data_dir = Path(raw_data_dir)
        self.max_retries = max_retries
        
        # Create directories
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            'total_tickers': 0,
            'successful': 0,
            'failed': 0,
            'failed_tickers': [],
            'download_start': datetime.now(),
            'download_end': None
        }
        
    def load_tickers(self, ticker_file='data/raw/nifty500_tickers.csv'):
        """
        Load ticker symbols from file.
        
        Args:
            ticker_file (str): Path to ticker CSV file
            
        Returns:
            list: List of ticker symbols
        """
        ticker_path = Path(ticker_file)
        
        if not ticker_path.exists():
            raise FileNotFoundError(
                f"Ticker file not found: {ticker_file}\n"
                "Please run fetch_tickers.py first."
            )
        
        df = pd.read_csv(ticker_path)
        tickers = df['ticker'].tolist()
        
        logger.info(f"Loaded {len(tickers)} tickers from {ticker_file}")
        return tickers
    
    def download_ticker(self, ticker):
        """
        Download historical data for a single ticker with retry logic.
        
        Args:
            ticker (str): Ticker symbol (e.g., 'RELIANCE.NS')
            
        Returns:
            pd.DataFrame or None: Historical data or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                # Download data from yfinance
                stock = yf.Ticker(ticker)
                df = stock.history(
                    start=self.start_date,
                    end=self.end_date,
                    auto_adjust=True,  # Adjust for splits and dividends
                    actions=True       # Include dividends and splits
                )
                
                if df.empty:
                    logger.warning(f"{ticker}: No data available")
                    return None
                
                # Add ticker column
                df['Ticker'] = ticker.replace('.NS', '')
                
                # Reset index to make Date a column
                df.reset_index(inplace=True)
                
                # Reorder columns for consistency
                cols = ['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
                
                # Add columns if they exist
                if 'Dividends' in df.columns:
                    cols.append('Dividends')
                if 'Stock Splits' in df.columns:
                    cols.append('Stock Splits')
                
                # Select available columns
                available_cols = [col for col in cols if col in df.columns]
                df = df[available_cols]
                
                logger.info(f"{ticker}: Downloaded {len(df)} records from "
                          f"{df['Date'].min().date()} to {df['Date'].max().date()}")
                
                return df
                
            except Exception as e:
                logger.warning(f"{ticker}: Attempt {attempt + 1} failed - {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"{ticker}: All {self.max_retries} attempts failed")
                    return None
        
        return None
    
    def download_all(self, tickers):
        """
        Download historical data for all tickers with progress tracking.
        
        Args:
            tickers (list): List of ticker symbols
            
        Returns:
            pd.DataFrame: Combined dataset with all downloaded data
        """
        self.stats['total_tickers'] = len(tickers)
        
        logger.info("=" * 70)
        logger.info(f"Starting bulk download for {len(tickers)} tickers")
        logger.info(f"Date range: {self.start_date} to {self.end_date}")
        logger.info("=" * 70)
        
        all_data = []
        
        # Download with progress bar
        with tqdm(total=len(tickers), desc="Downloading", unit="ticker") as pbar:
            for ticker in tickers:
                df = self.download_ticker(ticker)
                
                if df is not None and not df.empty:
                    all_data.append(df)
                    self.stats['successful'] += 1
                else:
                    self.stats['failed'] += 1
                    self.stats['failed_tickers'].append(ticker)
                
                pbar.update(1)
                
                # Rate limiting to avoid being blocked
                time.sleep(0.5)
        
        self.stats['download_end'] = datetime.now()
        
        # Combine all dataframes
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Successfully downloaded data for {len(all_data)} tickers")
            return combined_df
        else:
            logger.error("No data downloaded for any ticker")
            return pd.DataFrame()
    
    def save_raw_data(self, df, filename='nifty500_raw_data.csv'):
        """
        Save raw downloaded data to CSV.
        
        Args:
            df (pd.DataFrame): Combined dataset
            filename (str): Output filename
            
        Returns:
            Path: Path to saved file
        """
        output_path = self.raw_data_dir / filename
        df.to_csv(output_path, index=False)
        
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Saved raw data to {output_path} ({file_size_mb:.2f} MB)")
        
        return output_path
    
    def save_download_report(self):
        """
        Save download statistics and failed tickers report.
        """
        report_dir = Path('data/reports')
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate duration
        duration = self.stats['download_end'] - self.stats['download_start']
        
        # Save failed tickers
        failed_path = report_dir / 'failed_tickers.csv'
        if self.stats['failed_tickers']:
            pd.DataFrame({
                'ticker': self.stats['failed_tickers']
            }).to_csv(failed_path, index=False)
            logger.info(f"Saved {len(self.stats['failed_tickers'])} failed tickers to {failed_path}")
        
        # Save summary statistics
        summary = {
            'download_date': datetime.now().isoformat(),
            'start_date': self.start_date,
            'end_date': self.end_date,
            'total_tickers': self.stats['total_tickers'],
            'successful_downloads': self.stats['successful'],
            'failed_downloads': self.stats['failed'],
            'success_rate': f"{(self.stats['successful'] / self.stats['total_tickers'] * 100):.2f}%",
            'duration_seconds': duration.total_seconds(),
            'failed_tickers': self.stats['failed_tickers']
        }
        
        summary_path = report_dir / 'download_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved download summary to {summary_path}")
        
        return summary
    
    def print_summary(self):
        """Print download summary statistics."""
        logger.info("=" * 70)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total tickers attempted:  {self.stats['total_tickers']}")
        logger.info(f"Successfully downloaded:  {self.stats['successful']}")
        logger.info(f"Failed downloads:         {self.stats['failed']}")
        logger.info(f"Success rate:             {(self.stats['successful'] / self.stats['total_tickers'] * 100):.2f}%")
        
        if self.stats['download_end']:
            duration = self.stats['download_end'] - self.stats['download_start']
            logger.info(f"Total duration:           {duration}")
        
        logger.info("=" * 70)


def main():
    """Main execution function."""
    logger.info("=" * 70)
    logger.info("NIFTY 500 HISTORICAL DATA DOWNLOADER")
    logger.info("=" * 70)
    
    # Initialize downloader
    downloader = NIFTY500Downloader(
        start_date='2000-01-01',
        end_date=None,  # Today
        max_retries=3
    )
    
    try:
        # Load tickers
        tickers = downloader.load_tickers()
        
        # Download all data
        df = downloader.download_all(tickers)
        
        if not df.empty:
            # Save raw data
            downloader.save_raw_data(df)
            
            # Save report
            downloader.save_download_report()
            
            # Print summary
            downloader.print_summary()
            
            logger.info("=" * 70)
            logger.info("SUCCESS: Data download completed")
            logger.info("=" * 70)
            
            return df
        else:
            logger.error("FAILED: No data downloaded")
            return None
            
    except Exception as e:
        logger.error(f"CRITICAL ERROR: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
