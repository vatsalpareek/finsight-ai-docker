# FinSight AI — Autonomous Financial Intelligence System

> **A 22-Module Autonomous Research Desk for Retail Investors**
>
> *Powered by the Web-Slinger Pipeline, Live yfinance Data, and Dynamic Investor Constraints.*

---

## 🌟 Executive Overview

**FinSight AI** is a production-grade application that behaves like a miniature hedge-fund research team operating autonomously for retail investors. 

We have completely upgraded the system from a basic 4-agent hackathon demo into the **Web-Slinger Research Pipeline**—a robust 22-module DAG (Directed Acyclic Graph) architecture. The system pulls **live real-time data from Yahoo Finance**, analyzes fundamentals and technicals mathematically, and runs the conclusions against dynamic user portfolio constraints to generate highly personalized Buy/Hold/Sell decisions.

---

## 🚀 Key Features & Architectural Highlights

### 1. The 22-Module Web-Slinger Pipeline
FinSight now orchestrates 22 sequential and parallel modules to reach a decision, including:
- **Data Orchestrator**: Fetches live candles and balance sheet fundamentals via `yfinance`.
- **4 Autonomous Desks**: Technical, Fundamental, Market, and Sentiment desks evaluate the raw data independently.
- **Consensus & Critic Engines**: Identifies conflicts between desks (e.g., Technicals are Bearish but Fundamentals are Bullish) and mathematically weights them to form an unbiased consensus.
- **Scenario Engine**: Generates 3 probabilistic price-target scenarios ("Thesis plays out", "Muddle through", "Thesis breaks") based on historical annualized volatility.

### 2. Live Market Data (yfinance Integration)
No more hardcoded or fake prices. The backend uses the `yfinance` library to dynamically pull:
- **Real-Time Prices**: Instant last-traded prices.
- **Historical Candles**: Daily OHLCV data to compute SMA, MACD, RSI, drawdowns, and volatility internally using pure Python math.
- **Fundamentals**: P/E ratios, Debt-to-Equity, Net Margins, and Revenue Growth ratios.

### 3. Dynamic Portfolio Integration
Users aren't just generic risk profiles. The system connects to a real SQLite/SQLAlchemy database containing user portfolios (**Peter Parker** - Conservative, **Green Goblin** - Moderate, **Gwen Stacy** - Aggressive). 
- Every recommendation simulates the **Action Impact** (e.g., buying 10% more RELIANCE). 
- If an action breaches a user's cash floor or maximum sector concentration limit, the engine actively **blocks** the trade and downgrades it to a "HOLD".

### 4. Interactive Comic-Style UI
The frontend has been completely swapped to the Web-Slinger architecture—a beautiful, dynamic comic-ink SVG interface that visually traces the pipeline's execution, maps the spider-web of desk consensus, and explicitly lists constraint breaches.

### 5. Resilient Degradation Engine
Includes checkboxes to intentionally "kill" a data feed (like Fundamentals or Market). The Orchestrator safely degrades the pipeline, forcing the AI to synthesize a thesis with partial data, exactly simulating real-world API outages.

---

## 🛠️ System Architecture

```text
                                  USER INTERFACE (Web-Slinger HTML/JS)
                                                    |
                                          API LAYER (FastAPI)
                                                    |
                                    22-MODULE RESEARCH ORCHESTRATOR
                                                    |
    +-------------------+-------------------+-------------------+-------------------+
    |                   |                   |                   |                   |
Data Fetching       Desk Analysis     Consensus/Critic       Scenarios       Decision/Impacts
(yfinance live)   (Tech/Fund/Mkt/Sent) (Conflict resolution) (Target Prices)  (Portfolio Constraints)
```

---

## 💻 Tech Stack

- **Frontend**: Vite (serving static HTML/JS/CSS), SVG visualizations
- **Backend**: Python 3.10+, FastAPI, yfinance, SQLAlchemy, Pydantic v2
- **Database**: SQLite (User Profiles, Portfolios, Session History)

---

## 🏁 Quick Start & Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Start FastAPI Backend (Port 8080)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8080
```
Backend API Health: `http://localhost:8080/api/health`

### 2. Start Vite Frontend (Port 5173)
```bash
cd frontend
npm install
npm run dev
```
Access Web Terminal: `http://localhost:5173`

---

## 📄 Safety & Compliance Disclaimer

*FinSight AI is an autonomous investment intelligence and research platform designed for educational and demonstration purposes. It does not issue guaranteed price targets or execute trading orders. AI-generated investment intelligence. Not financial advice.*
