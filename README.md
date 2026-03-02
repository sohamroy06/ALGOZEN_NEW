# NIFTY 500 Institutional Systematic Equity Strategy
### Regime-Aware | OHLCV-Only | Walk-Forward Validated | AlgoZen Competition

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Competition](https://img.shields.io/badge/AlgoZen-2026-orange)

---

## Overview

This repository contains a **production-grade institutional systematic equity strategy** built for the AlgoZen Algorithmic Trading Competition. The strategy operates exclusively on daily OHLCV data across the NIFTY 500 universe, using a regime-aware architecture to deliver consistent risk-adjusted returns across all market environments.

The system is designed around two core principles: **robustness over raw performance** and **capital preservation over return maximization**. Every parameter is either fixed at a theoretically motivated value or bounded within a tight range optimized by a genetic algorithm — never fit to noise.

### Target Performance

| Metric | Target |
|--------|--------|
| Sharpe Ratio (net of costs) | > 1.0 |
| CAGR (net) | 14 – 18% |
| Maximum Drawdown | < 15% |
| Sortino Ratio | > 1.3 |
| Calmar Ratio | > 1.0 |
| Annual Turnover (one-way) | < 180% |
| Transaction Cost Assumption | 30 bps/trade |

---

## Repository Structure

```
algozen_new/
│
├── nifty500_pipeline/                  # Data pipeline
│   ├── data/
│   │   ├── raw/
│   │   │   ├── nifty500_tickers.csv
│   │   │   ├── nifty500_tickers.json
│   │   │   └── nifty500_raw_data.csv
│   │   ├── processed/
│   │   │   ├── nifty500_master.csv         # Full OHLCV master dataset
│   │   │   ├── nifty500_close_prices.csv   # Wide-format close prices
│   │   │   └── nifty500_volumes.csv        # Wide-format volumes
│   │   └── reports/
│   │       ├── download_summary.json
│   │       ├── data_quality_report.json
│   │       └── failed_tickers.csv
│   ├── logs/
│   │   ├── pipeline.log
│   │   ├── download.log
│   │   └── cleaning.log
│   ├── scripts/
│   │   ├── fetch_tickers.py
│   │   ├── download_data.py
│   │   └── clean_data.py
│   ├── main.py
│   └── requirements.txt
│
└── NIFTY500_Strategy_Training.ipynb    # Main strategy notebook
```

---

## Architecture

The strategy is built in six layers, each with documented parameters and design rationale.

### 1. Universe Construction
The NIFTY 500 is filtered monthly through three screens before any signal is computed:

- **Liquidity Screen** — 30-day Average Daily Turnover ≥ ₹25 Crore. Calibrated to a ₹1,500 crore strategy size. Removes ~80–100 illiquid small caps, leaving a working universe of ~380–420 stocks.
- **Price Integrity Screen** — Excludes stocks with more than 3 circuit events (upper or lower) in the preceding 90 trading days. Circuit-affected price series produce unreliable momentum and volatility signals.
- **Position Size Cap** — No single position may exceed 10% of a stock's 30-day Average Daily Volume. Enforced at portfolio construction time, independent of the 3% NAV position limit.

### 2. Regime Detection
Regime is classified using two orthogonal signals computed on the equal-weight NIFTY 500 index:

- **Signal 1: Price vs MA200** — If index > MA200, the market is Bull-candidate. If below, it is Bear or Sideways candidate. The 200-day MA is fixed permanently and never optimized.
- **Signal 2: Realized Volatility Ratio** — When index is below MA200, the 21-day realized vol is compared to its 252-day median. Above median → Bear regime. Below median → Sideways regime.
- **5-Day Confirmation Delay** — A raw signal must persist for 5 consecutive trading days before the system acts on it. This eliminates false transitions caused by single-day spikes.

| Regime | Condition | Action |
|--------|-----------|--------|
| BULL | Index > MA200 (confirmed 5 days) | Full momentum portfolio, up to 100% gross |
| SIDEWAYS | Index < MA200 + RV < median | Reduced momentum (25 stocks), 70% gross cap |
| BEAR | Index < MA200 + RV > median | Low vol + trend filter (30 stocks), 60% gross cap |
| CASH | Circuit breaker active | All positions liquidated |

### 3. Signal Generation (Regime-Specific)

**Bull Regime — Risk-Adjusted Momentum**
- Signal: 12-1 month return ÷ 21-day realized volatility (stock-level historical Sharpe ratio)
- 52-Week High Filter: any stock trading more than 10% below its 52W high is excluded
- Selects top 40 stocks by risk-adjusted momentum rank

**Bear Regime — Low Volatility + Trend Filter**
- Signal: 21-day realized volatility (ascending — lowest vol ranked first)
- Trend Filter: 50-day MA must be above 100-day MA (eliminates downtrending low-vol names)
- Selects top 30 stocks passing both filters
- Hard 60% gross exposure cap — 40% minimum cash at all times

**Sideways Regime — Reduced Momentum**
- Same signal as Bull (risk-adjusted momentum)
- Reduced selection (25 stocks) and reduced gross cap (70%)
- Pairs trading deliberately excluded — cointegration in Indian equities has insufficient statistical reliability on OHLCV data

### 4. Portfolio Construction
Three hard constraints applied in sequence after stock selection:

- **Max Position Size**: 3% of NAV per stock (hard cap)
- **Sector Exposure Cap**: 25% of gross exposure per sector (prevents IT/Financial concentration)
- **Equal Weighting**: Within selected stocks, all weights are equal — no optimization of individual weights

### 5. Sizing Engine
- **Volatility Targeting**: Targets 12% annualized portfolio volatility. Daily scaling factor = (vol_target / 21d realized vol) × size_multiplier, capped at 1.5x
- **ATR Stop Losses**: 2× ATR(14) from entry price, trailing upward only, updated weekly to reduce stop-hunting exposure
- **Monthly Rebalancing**: Hard cap of 30% one-way monthly turnover

### 6. Circuit Breakers (Never Optimized)
- **Drawdown Halt**: If NAV falls >12% from its 60-day rolling peak, all positions are liquidated immediately. Strategy re-engages only after 10 consecutive Bull confirmation days AND full drawdown recovery.
- **Momentum Crash Override**: If 5-day portfolio return < -2.5% in Bull regime, all positions are immediately scaled to 50%. Restored gradually over 10 trading days.

---

## ML Ensemble Layer

On top of the systematic rules, an ensemble machine learning layer provides an additional signal overlay:

| Model | Type | Purpose |
|-------|------|---------|
| XGBoost | Classifier | Probability of positive 21-day forward return |
| LightGBM | Classifier | Probability of positive 21-day forward return |
| Random Forest | Classifier | Probability of positive 21-day forward return |
| LightGBM | Regressor | Forward return magnitude estimation |

The ensemble probability (average of 3 classifiers) is used to tilt position weights at monthly rebalancing — higher ML confidence increases allocation within the systematic constraints. All models use `TimeSeriesSplit` for validation with zero lookahead.

**Key features used**: risk-adjusted momentum, realized volatility ratios, MA crossovers, 52-week high proximity, volume ratios, regime encoding, ATR.

---

## Genetic Algorithm — Walk-Forward Optimization

The GA optimizes **exactly 2 parameters**. Everything else is fixed.

| Parameter | Range | Status |
|-----------|-------|--------|
| `vol_target` | 10% – 18% | GA Optimizes |
| `size_multiplier` | 0.80 – 1.20 | GA Optimizes |
| MA200 lookback | 200 days | FIXED |
| Momentum lookback | 252 days | FIXED |
| Stop loss multiplier | 2× ATR | FIXED |
| Regime confirmation | 5 days | FIXED |
| Sector cap | 25% gross | FIXED |
| Position cap | 3% NAV | FIXED |
| Bear gross cap | 60% | FIXED |
| Circuit breaker DD | 12% | FIXED |

**Walk-Forward Process:**
- 5-year training window → 1-year out-of-sample test window
- Rolls forward annually
- Population: 30 candidate sets × 20 generations
- Fitness function: Sharpe ratio net of transaction costs
- **Adoption gate**: New parameters are only deployed if they outperform current parameters by +0.10 Sharpe on the out-of-sample window

---

## Validation Framework — 7 Tests

The notebook runs all 7 institutional validation tests before results are considered complete:

1. **Subsample Stability** — Sharpe ratio must not vary by more than 0.5 across four equal time periods
2. **Parameter Sensitivity** — Strategy Sharpe must remain stable as vol target varies ±30% from chosen value
3. **Regime Attribution** — P&L attributed separately to Bull, Bear, Sideways, and Cash periods
4. **Transaction Cost Stress** — Strategy must remain Sharpe-positive at 3× baseline transaction costs
5. **Monte Carlo Regime Permutation** — True Sharpe must rank in top 5% of 500 shuffled-regime runs
6. **Pure Out-of-Sample Window** — Last 3 years of data held out from all parameter decisions
7. **Drawdown Recovery Analysis** — Every drawdown >5% reported with depth and time-to-recovery

---

## Quick Start

### Step 1: Run the Data Pipeline

```bash
cd nifty500_pipeline

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run full pipeline (downloads all NIFTY 500 data from 2000)
python main.py
```

This generates three files in `data/processed/`:
- `nifty500_master.csv` — Full OHLCV dataset (long format)
- `nifty500_close_prices.csv` — Close prices (wide format, one column per ticker)
- `nifty500_volumes.csv` — Daily volumes (wide format)

### Step 2: Configure the Notebook

Open `NIFTY500_Strategy_Training.ipynb` and update the data path in the config cell:

```python
CFG = {
    "DATA_DIR": r"C:\path\to\nifty500_pipeline\data\processed",  # ← update this
    ...
}
```

Also set your output directory:

```python
OUTPUT_DIR = r"C:\path\to\your\outputs"   # ← update this
```

### Step 3: Run the Notebook

Run all cells top to bottom. The notebook will:

1. Load and validate all three data files
2. Apply the 3-filter universe screen
3. Compute regime labels (MA200 + RV ratio with 5-day confirmation)
4. Generate regime-specific signals
5. Train the XGBoost + LightGBM + Random Forest ensemble
6. Run the full backtest (2000 – present)
7. Execute all 7 validation tests
8. Run the GA walk-forward optimization
9. Re-run the final backtest with optimized parameters
10. Save all outputs and charts

---

## Dependencies

```
pandas >= 2.0.0
numpy >= 1.24.0
scikit-learn >= 1.3.0
xgboost >= 1.7.0
lightgbm >= 3.3.0
matplotlib >= 3.7.0
seaborn >= 0.12.0
scipy >= 1.10.0
yfinance >= 0.2.28
tqdm >= 4.65.0
joblib >= 1.3.0
requests >= 2.31.0
openpyxl >= 3.1.0
```

Install all at once:
```bash
pip install -r requirements.txt
```

---

## Output Files

After running the notebook, the following files are saved to `OUTPUT_DIR`:

| File | Description |
|------|-------------|
| `strategy_nav.csv` | Daily NAV series |
| `strategy_returns.csv` | Daily portfolio returns |
| `walkforward_results.csv` | GA walk-forward window results |
| `regime_labels.csv` | Daily regime classification |
| `feature_importance.csv` | ML ensemble feature importances |
| `performance_summary.json` | Key performance metrics |
| `regime_detection.png` | EW index with regime shading |
| `feature_importance.png` | Top 20 feature importance chart |
| `performance_dashboard.png` | Full 6-panel performance dashboard |
| `walkforward_results.png` | GA walk-forward OOS Sharpe chart |

---

## Important Notes

### Survivorship Bias
This dataset contains survivorship bias — it includes only current NIFTY 500 constituents. Companies delisted or removed from the index are not included. The backtested results should be interpreted with this limitation in mind.

### Transaction Costs
All backtests use a realistic 30 bps round-trip cost model reflecting Indian equity market conditions (STT 10 bps + exchange charges 3-4 bps + brokerage 3-5 bps + market impact 10-15 bps). Do not reduce this assumption.

### Yahoo Finance
The data pipeline uses `yfinance`, which is an unofficial API. Some historical data may be missing or incomplete, particularly for stocks listed after 2010. Check `data/reports/data_quality_report.json` for coverage statistics.

### Python Version
Tested on Python 3.11. The `pandas >= 2.0` breaking changes (deprecated `method='ffill'` in `.fillna()`, `'M'` → `'ME'` resample alias) are already handled in the notebook.

---

## What Was Deliberately Excluded

| Approach | Reason Excluded |
|----------|----------------|
| HMM Regime Detection | Assumes stationarity that Indian markets don't exhibit; single point of failure |
| Pairs Trading | Cointegration half-life in Indian equities averages 6–18 months; not reliably detectable on OHLCV data |
| Kelly Criterion Sizing | Requires accurate edge estimate; systematically biased in regime-switching strategies |
| >2 GA Parameters | With 4–6 historical Bear regime instances, optimizing more than 2 parameters is textbook overfitting |
| Optimized Stop Losses | Fit velocity profile of past drawdowns; fails on structurally different future crises |
| Optimized Rebalance Frequency | Fits autocorrelation structure of training data; no predictive value out-of-sample |

---

## Authors

**Quantitative Infrastructure Team**  
Built for the AlgoZen Algorithmic Trading Competition — TECHNEX'26

---

## License

MIT License — free to use for educational and competition purposes.
