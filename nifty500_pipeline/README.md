# NIFTY 500 Historical Data Pipeline

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Production-grade data pipeline for fetching, processing, and validating historical stock data for all NIFTY 500 companies.**

Built by the Quantitative Infrastructure Team for the **AlgoZen Algorithmic Trading Competition**.

---

## 🎯 Overview

This is a complete, self-contained Python project that automatically:

1. ✅ Fetches the current list of NIFTY 500 constituent companies
2. ✅ Downloads historical daily OHLCV data from 2000 to present using `yfinance`
3. ✅ Cleans and validates data with institutional-grade quality checks
4. ✅ Generates multiple output formats for analysis
5. ✅ Produces comprehensive reports and logs

**Key Features:**
- 🔒 **Self-contained**: Local Python virtual environment (no global installations)
- 🚀 **Production-ready**: Retry logic, error handling, logging, validation
- 📊 **Multiple outputs**: Master CSV, close prices, volumes, reports
- ⚡ **Scalable**: Handles 500+ tickers with progress tracking
- 🛡️ **Robust**: Handles missing data, duplicates, API failures

---

## 📁 Project Structure

```
nifty500_pipeline/
│
├── venv/                          # Python virtual environment (created during setup)
│
├── data/
│   ├── raw/                       # Raw downloaded data
│   │   ├── nifty500_tickers.csv
│   │   ├── nifty500_tickers.json
│   │   └── nifty500_raw_data.csv
│   │
│   ├── processed/                 # Cleaned and structured data
│   │   ├── nifty500_master.csv
│   │   ├── nifty500_close_prices.csv
│   │   └── nifty500_volumes.csv
│   │
│   └── reports/                   # Quality and download reports
│       ├── download_summary.json
│       ├── data_quality_report.json
│       └── failed_tickers.csv
│
├── logs/                          # Pipeline execution logs
│   ├── pipeline.log
│   ├── download.log
│   └── cleaning.log
│
├── scripts/                       # Core pipeline modules
│   ├── fetch_tickers.py          # Fetch NIFTY 500 constituents
│   ├── download_data.py          # Download historical data
│   └── clean_data.py             # Clean and validate data
│
├── main.py                        # Pipeline orchestrator
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.8+** installed on your system
- Internet connection for downloading data

### Step 1: Check Python Installation

```bash
# Windows
python --version

# Mac/Linux
python3 --version
```

If Python is not installed, download from [python.org](https://www.python.org/downloads/).

### Step 2: Navigate to Project Directory

```bash
cd e:\algozen new\nifty500_pipeline
```

### Step 3: Create Virtual Environment

```bash
# Windows
python -m venv venv

# Mac/Linux
python3 -m venv venv
```

### Step 4: Activate Virtual Environment

```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### Step 5: Upgrade pip and Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

### Step 6: Run the Pipeline

```bash
# Run complete pipeline (fetch + download + clean)
python main.py
```

**That's it!** The pipeline will automatically:
- Fetch NIFTY 500 tickers
- Download historical data from 2000-01-01
- Clean and validate the data
- Generate reports

---

## 📊 Usage Examples

### Run Full Pipeline (Default)

```bash
python main.py
```

### Custom Date Range

```bash
# Download data from 2010 onwards
python main.py --start-date 2010-01-01

# Specific date range
python main.py --start-date 2015-01-01 --end-date 2023-12-31
```

### Run Individual Stages

```bash
# Only fetch tickers
python main.py --stage fetch

# Only download data (requires tickers to be fetched first)
python main.py --stage download

# Only clean data (requires raw data to exist)
python main.py --stage clean
```

### Adjust Retry Logic

```bash
# Increase retries for unstable connections
python main.py --max-retries 5
```

---

## 📈 Output Files

### Processed Data

| File | Description | Use Case |
|------|-------------|----------|
| `nifty500_master.csv` | Complete dataset with all columns | Comprehensive analysis |
| `nifty500_close_prices.csv` | Only closing prices (wide format) | Quick time series analysis |
| `nifty500_volumes.csv` | Trading volumes (wide format) | Liquidity analysis |

### Reports

| File | Description |
|------|-------------|
| `download_summary.json` | Download statistics, success rate, failed tickers |
| `data_quality_report.json` | Data quality metrics, cleaning stats |
| `failed_tickers.csv` | List of tickers that failed to download |

### Logs

| File | Description |
|------|-------------|
| `pipeline.log` | Overall pipeline execution log |
| `download.log` | Detailed download progress and errors |
| `cleaning.log` | Data cleaning and validation log |

---

## ⚙️ Configuration

### Modifying Data Sources

Edit `scripts/fetch_tickers.py` to:
- Add alternative ticker sources
- Modify the hardcoded fallback list

### Adjusting Cleaning Logic

Edit `scripts/clean_data.py` to:
- Change missing value handling strategy
- Modify data validation rules
- Add custom metadata columns

### Transaction Costs

Default transaction cost is **3 basis points (0.03%)**. Modify in `scripts/clean_data.py`:

```python
df['TransactionCostBps'] = 3.0  # Institutional
# df['TransactionCostBps'] = 10.0  # Retail
```

---

## ⚠️ Important Notes

### 1. **Survivorship Bias**

> ⚠️ This dataset contains **survivorship bias** as it only includes current NIFTY 500 constituents. Companies that were delisted or removed from the index are not included.

For academic research or backtesting, consider this bias in your analysis.

### 2. **Yahoo Finance Limitations**

- **Rate Limiting**: Yahoo Finance may throttle requests. The pipeline includes delays to mitigate this.
- **Data Quality**: Some older data may be missing or incomplete.
- **API Changes**: Yahoo Finance API is unofficial and may change without notice.

### 3. **Data Coverage**

Not all stocks have data going back to 2000. Actual coverage depends on:
- When the stock was listed
- Data availability on Yahoo Finance

Check `data_quality_report.json` for average years of data per ticker.

---

## 🔧 Troubleshooting

### Issue: `pip install` failing

**Solution:** Upgrade pip first
```bash
python -m pip install --upgrade pip
```

### Issue: Virtual environment not activating

**Windows PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

### Issue: Yahoo Finance download fails

**Solutions:**
1. Check internet connection
2. Increase `--max-retries`
3. Run pipeline at different times (avoid peak hours)
4. Check logs in `logs/download.log` for specific errors

### Issue: Missing tickers

- Some tickers may fail due to delisting or data unavailability
- Check `data/reports/failed_tickers.csv` for the list
- Review `logs/download.log` for specific error messages

---



### Next Steps:

1. ✅ **Data Ready**: Use `nifty500_master.csv` or `nifty500_close_prices.csv`
2. 🧠 **Strategy Development**: Build your trading algorithm
3. 📉 **Backtesting**: Test strategies using the historical data
4. 📊 **Risk Management**: Implement position sizing and stop-losses
5. 📋 **Documentation**: Prepare your presentation for Round 3

### Performance Optimization Tips:

- Use `nifty500_close_prices.csv` for faster loading (wide format)
- Filter by liquidity using `nifty500_volumes.csv`
- Leverage the `TransactionCostBps` column for realistic backtests

---

## 📚 Dependencies

All dependencies are specified in `requirements.txt`:

```
pandas>=2.0.0
numpy>=1.24.0
yfinance>=0.2.28
requests>=2.31.0
tqdm>=4.65.0
matplotlib>=3.7.0
seaborn>=0.12.0
scikit-learn>=1.3.0
openpyxl>=3.1.0
```

---

## 🤝 Contributing

This project was built for the AlgoZen competition. Feel free to:
- Fork and modify for your own strategies
- Report issues or suggest improvements
- Extend with additional data sources

---

## 📄 License

MIT License - feel free to use for educational and competition purposes.

---

## 👨‍💻 Authors

**Quantitative Infrastructure Team**  
Built for AlgoZen: Algorithmic Trading Competition

---


