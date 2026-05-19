# DCA Simulator & Market Impact Analysis

**Author:** Devak Sangar  
**Stack:** Python · PySide6 · NumPy · Pandas · Matplotlib · SciPy

An agent-based stock market simulator built to study how Dollar Cost Averaging (DCA) investors affect market dynamics. The simulator models random traders and DCA investors interacting through a shared order book, with a desktop GUI for configuration and data export. A companion Jupyter notebook conducts full statistical analysis on the exported results.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Experimental Design](#experimental-design)
- [Key Findings](#key-findings)
- [Getting Started](#getting-started)

---

## Overview

The core question: **does the presence of systematic DCA buyers measurably improve market outcomes for all participants?**

To answer it, random agent count was held constant at 100 while DCA agent count was varied across 7 configurations (0–100 DCA agents). Each configuration ran 50 Monte Carlo simulations of 1000 ticks, producing price histories that were then analyzed for return distribution, volatility, drawdown, and tail risk metrics.

---

## Project Structure

```
DCA-Simulator-Analysis/
├── main.py              # PySide6 desktop GUI
├── src/
│   ├── agents.py        # RandomAgent and DCAAgent implementations
│   ├── orderbook.py     # Order book and price matching logic
│   └── simulation.py    # Simulation runners and Monte Carlo engine
├── data/                # Exported CSVs and charts from simulation runs
└── requirements.txt
```

---

## How It Works

### Agents

| Agent | Behavior |
|---|---|
| **RandomAgent** | Buys, sells, or holds each tick. Transaction prices follow a lognormal distribution. |
| **DCAAgent** | Buys every 30 ticks at a slight premium above the last traded price, regardless of market conditions. |

### Order Book

A simplified order book collects all agent orders each tick, matches them, and updates the last traded price. Price history is recorded across all ticks and exported to CSV.

### Simulation Modes

- **Single run** — one simulation with configurable agent counts, tick length, and optional seed.
- **Monte Carlo** — runs the simulation *n* times and plots all runs alongside the mean price path.

### GUI

Built with PySide6. Configure agent counts, tick length, seed, and Monte Carlo run count, then export results as PNG and CSV directly from the interface.

### Analysis

A Jupyter notebook (`analysis.ipynb`) performs full statistical analysis on exported CSVs. Metrics computed:

- Log returns and rolling volatility
- Autocorrelation function (ACF)
- Max drawdown
- VaR 5% and CVaR 5% (expected shortfall)
- P(gain) — probability final price exceeds initial price
- 95th percentile return

---

## Experimental Design

Random agent count held constant at 100. DCA agent count varied across 7 configurations:

| DCA Agents | Total Agents | DCA Participation |
|---|---|---|
| 0   | 100 | 0%  |
| 10  | 110 | 9%  |
| 20  | 120 | 17% |
| 30  | 130 | 23% |
| 40  | 140 | 29% |
| 50  | 150 | 33% |
| 100 | 200 | 50% |

50 Monte Carlo runs per configuration · 1000 ticks per run

---

## Key Findings

### 1. Critical threshold at 10–17% DCA participation

P(gain) jumps from 44% to 88% between 9% and 17% DCA penetration — a 44pp increase in a single step. Above 17%, the market almost always ends in profit. This points to a threshold effect where a small minority of systematic buyers tips the market from uncertain to reliably profitable.

| DCA Participation | P(gain) |
|---|---|
| 0%  | 44%  |
| 9%  | 64%  |
| 17% | 88%  |
| 23% | 92%  |
| 33% | 100% |

### 2. Tail risk nearly eliminated by 33% DCA

VaR 5% improves from -18.11% to +17.07% as DCA penetration increases from 0% to 33%. CVaR (expected shortfall) follows the same trend. Above 33% penetration, even the worst 5% of outcomes are profitable — catastrophic loss scenarios cease to exist.

| DCA Participation | VaR 5%  | CVaR 5%  |
|---|---|---|
| 0%  | -18.11% | -23.10% |
| 17% | -3.80%  | -7.98%  |
| 29% | +7.51%  | -0.99%  |
| 33% | +17.07% | +15.74% |

### 3. Asymmetric distribution shift

DCA does not simply compress the return distribution — it shifts it rightward while simultaneously expanding the right tail. The 95th percentile return grows from 16% to 78% as DCA penetration increases from 0% to 50%, while worst-case losses are reduced at the same time.

### 4. Worst-case drawdown cut by 67%

Mean max drawdown falls monotonically from 13.2% to 5.6% across the sweep. Worst-case drawdown drops from 29.0% to 9.6%. DCA buyers act as a price floor — scheduled buying absorbs selling pressure during dips regardless of market conditions.

### 5. Volatility-stability tradeoff

Rolling volatility increases 316% from 0% to 50% DCA penetration. This reflects the periodic buying signal injected by DCA agents every 30 ticks rather than increased market instability — confirmed by the simultaneous reduction in drawdown and tail risk across the same range.

---

## Getting Started

**Clone and install dependencies:**

```bash
git clone https://github.com/SANGQR/DCA-Simulator-Analysis
cd DCA-Simulator-Analysis
pip install -r requirements.txt
```

**Launch the simulator:**

```bash
python main.py
```

**Run the analysis** (after exporting CSVs from the GUI):

```bash
jupyter notebook analysis.ipynb
```

---

## Requirements

```
numpy
pandas
matplotlib
scipy
pyside6
jupyter
```
