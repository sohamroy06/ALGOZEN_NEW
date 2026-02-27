"""
NIFTY 500 Ticker Fetcher
========================
Automatically fetches the list of NIFTY 500 constituent companies.

This module scrapes the NSE India website or uses a fallback API
to retrieve the current list of NIFTY 500 stocks and formats
them with the .NS suffix for Yahoo Finance compatibility.

Author: Quantitative Infrastructure Team
"""

import pandas as pd
import requests
import logging
from pathlib import Path
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NIFTY500Fetcher:
    """Fetches NIFTY 500 constituent tickers from multiple sources."""
    
    def __init__(self, output_dir='data/raw'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tickers = []
        
    def fetch_from_nse_api(self):
        """
        Attempt to fetch NIFTY 500 constituents from NSE India API.
        
        Returns:
            list: List of ticker symbols or empty list if failed
        """
        try:
            logger.info("Attempting to fetch NIFTY 500 from NSE API...")
            
            # NSE API endpoint for NIFTY 500 constituents
            url = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            # Extract symbols
            if 'Symbol' in df.columns:
                tickers = df['Symbol'].dropna().unique().tolist()
                logger.info(f"Successfully fetched {len(tickers)} tickers from NSE API")
                return tickers
            else:
                logger.warning("'Symbol' column not found in NSE data")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch from NSE API: {e}")
            return []
    
    def fetch_from_wikipedia(self):
        """
        Fallback: Fetch NIFTY 500 list from Wikipedia.
        
        Returns:
            list: List of ticker symbols or empty list if failed
        """
        try:
            logger.info("Attempting to fetch NIFTY 500 from Wikipedia...")
            
            url = "https://en.wikipedia.org/wiki/NIFTY_500"
            tables = pd.read_html(url)
            
            # Find table with stock symbols
            for table in tables:
                if 'Symbol' in table.columns or 'Company' in table.columns:
                    if 'Symbol' in table.columns:
                        tickers = table['Symbol'].dropna().unique().tolist()
                    else:
                        # Try to extract symbols from company names
                        tickers = table['Company'].dropna().unique().tolist()
                    
                    logger.info(f"Successfully fetched {len(tickers)} tickers from Wikipedia")
                    return tickers
            
            logger.warning("Could not find ticker table in Wikipedia")
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch from Wikipedia: {e}")
            return []
    
    def use_hardcoded_list(self):
        """
        Last resort: Use a hardcoded list of major NIFTY 500 companies.
        
        Returns:
            list: Hardcoded list of major NIFTY 500 tickers
        """
        logger.warning("Using hardcoded fallback list of major NIFTY 500 stocks")
        
        # Top 100 NIFTY 500 companies (representative sample)
        major_stocks = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC', 
            'SBIN', 'BHARTIARTL', 'BAJFINANCE', 'KOTAKBANK', 'LT', 'ASIANPAINT', 
            'HCLTECH', 'AXISBANK', 'MARUTI', 'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 
            'NESTLEIND', 'WIPRO', 'ADANIENT', 'ONGC', 'NTPC', 'POWERGRID', 'TATAMOTORS',
            'BAJAJFINSV', 'JSWSTEEL', 'M&M', 'TECHM', 'INDUSINDBK', 'TATASTEEL',
            'ADANIPORTS', 'HINDALCO', 'COALINDIA', 'GRASIM', 'BRITANNIA', 'SHREECEM',
            'EICHERMOT', 'CIPLA', 'DRREDDY', 'DIVISLAB', 'APOLLOHOSP', 'BPCL',
            'HEROMOTOCO', 'SBILIFE', 'HDFCLIFE', 'BAJAJ-AUTO', 'TATACONSUM',
            'DABUR', 'GODREJCP', 'MARICO', 'PIDILITIND', 'BERGEPAINT', 'COLPAL',
            'HAVELLS', 'VOLTAS', 'WHIRLPOOL', 'VBL', 'MCDOWELL-N', 'JUBLFOOD',
            'PAGEIND', 'DIXON', 'POLYCAB', 'CROMPTON', 'VGUARD', 'BATAINDIA',
            'RELAXO', 'TRENT', 'ABFRL', 'VEDL', 'SAIL', 'NMDC', 'MOIL',
            'ACC', 'AMBUJACEM', 'RAMCOCEM', 'JKCEMENT', 'HEIDELBERG', 'BANKBARODA',
            'PNB', 'CANBK', 'UNIONBANK', 'IDFCFIRSTB', 'FEDERALBNK', 'RBLBANK',
            'BANDHANBNK', 'PFC', 'RECLTD', 'IRCTC', 'IRFC', 'CONCOR', 'GMRINFRA',
            'ADANIGREEN', 'ADANITRANS', 'TATAPOWER', 'TORNTPOWER', 'CESC', 'NHPC'
        ]
        
        return major_stocks
    
    def fetch_tickers(self):
        """
        Main method to fetch NIFTY 500 tickers with fallback logic.
        
        Returns:
            list: List of ticker symbols formatted for Yahoo Finance (.NS suffix)
        """
        # Try NSE API first
        self.tickers = self.fetch_from_nse_api()
        
        # Fallback to Wikipedia if NSE fails
        if not self.tickers:
            time.sleep(2)  # Rate limiting
            self.tickers = self.fetch_from_wikipedia()
        
        # Last resort: hardcoded list
        if not self.tickers:
            self.tickers = self.use_hardcoded_list()
        
        if not self.tickers:
            raise ValueError("Failed to fetch NIFTY 500 tickers from all sources")
        
        # Format tickers with .NS suffix for Yahoo Finance
        formatted_tickers = [f"{ticker}.NS" for ticker in self.tickers]
        
        logger.info(f"Total tickers formatted: {len(formatted_tickers)}")
        
        return formatted_tickers
    
    def save_tickers(self, tickers):
        """
        Save fetched tickers to CSV and JSON files.
        
        Args:
            tickers (list): List of formatted ticker symbols
        """
        # Save to CSV
        csv_path = self.output_dir / 'nifty500_tickers.csv'
        df = pd.DataFrame({'ticker': tickers})
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved {len(tickers)} tickers to {csv_path}")
        
        # Save to JSON
        json_path = self.output_dir / 'nifty500_tickers.json'
        with open(json_path, 'w') as f:
            json.dump({'tickers': tickers, 'count': len(tickers)}, f, indent=2)
        logger.info(f"Saved ticker metadata to {json_path}")
        
        return csv_path


def main():
    """Main execution function."""
    logger.info("=" * 70)
    logger.info("NIFTY 500 TICKER FETCHER")
    logger.info("=" * 70)
    
    fetcher = NIFTY500Fetcher()
    
    try:
        # Fetch tickers
        tickers = fetcher.fetch_tickers()
        
        # Save to files
        csv_path = fetcher.save_tickers(tickers)
        
        logger.info("=" * 70)
        logger.info(f"SUCCESS: Fetched and saved {len(tickers)} NIFTY 500 tickers")
        logger.info(f"Output: {csv_path}")
        logger.info("=" * 70)
        
        return tickers
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
