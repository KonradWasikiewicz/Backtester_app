# Future Features & Enhancements Roadmap

This document tracks potential features and improvements for the Backtester App, generated on May 4, 2025.

**Priority Legend:** (H) High, (M) Medium, (L) Low

## I. UI/UX Enhancements

-   [ ] **(H) Modernized Wizard:**
    -   [ ] Visual Progress Indicator (Stepper)
    -   [ ] Real-time Input Validation
    -   [ ] Collapsible Completed Steps
-   [ ] **(H) Enhanced Results Visualization:**
    -   [ ] Interactive Chart Controls (Toggles, Zoom, Scale)
    -   [ ] Improved Heatmap/Table Features (Sort, Filter, Format)
    -   [ ] Candlestick/OHLC Chart Option
-   [ ] **(M) Feedback & Responsiveness:**
    -   [ ] Granular Loading States (Skeletons/Spinners)
    -   [ ] User Notifications (Toasts)
    -   [ ] Mobile/Tablet Responsiveness Review
-   [ ] **(M) Comparative Analysis:**
    -   [ ] Allow pinning/saving results
    -   [ ] Side-by-side comparison view (Equity Curve, Key Metrics)
-   [ ] **(M) Personalization & Theming:**
    -   [ ] Light/Dark Mode Toggle
    -   [ ] User Preferences (Save Defaults - e.g., capital, date range)
-   [ ] **(L) Customizable Dashboard:**
    -   [ ] Allow users to add/remove/rearrange result widgets
-   [ ] **(L) Export Results:**
    -   [ ] Export key metrics and trades table to CSV
    -   [ ] Export charts as images (PNG/SVG)
    -   [ ] Generate PDF report (more complex)
-   [ ] **(L) Keyboard Shortcuts:**
    -   [ ] Shortcuts for navigating wizard steps or running backtest.

## II. Core Functionality & Strategy

-   [ ] **(H) Strategy/Parameter Optimization UI:**
    -   [ ] Integrate `optimizer.py` into UI
    -   [ ] Define Parameter Ranges & Target Metric
    -   [ ] Display Optimization Results (Table, Parallel Coordinates Plot)
-   [ ] **(H) Advanced Metrics & Analysis:**
    -   [ ] Add metrics (Sortino, Calmar, Omega, VaR, CVaR)
    -   [ ] Add rolling metric plots (e.g., Rolling Sharpe)
-   [ ] **(M) Portfolio-Level Backtesting:**
    -   [ ] Enhance engine for portfolio allocation rules (Equal Weight, etc.)
    -   [ ] Leverage `portfolio_manager.py`
-   [ ] **(M) Strategy Saving/Loading:**
    -   [ ] UI to save/name strategy configurations (params, risk, costs)
    -   [ ] UI to load saved configurations
-   [ ] **(M) More Built-in Indicators/Strategies:**
    -   [ ] Add common indicators (MACD, Stochastic, ADX etc.)
    -   [ ] Add corresponding example strategies
-   [ ] **(M) Handling Corporate Actions:**
    -   [ ] Adjust prices/shares for stock splits
    -   [ ] Option to reinvest dividends
-   [ ] **(L) Walk-Forward Analysis:**
    -   [ ] Implement Walk-Forward Testing/Optimization Logic
    -   [ ] UI for configuring Walk-Forward runs
-   [ ] **(L) Custom Indicator Support:**
    -   [ ] Allow users to define custom indicators (e.g., via simple formula input or uploaded Python code - complex)
-   [ ] **(L) Advanced Order Types:**
    -   [ ] Simulate Limit Orders, Stop-Limit Orders
-   [ ] **(L) Short Selling Simulation:**
    -   [ ] Option to allow short positions in strategies.

## III. Data & Performance

-   [ ] **(H) Asynchronous Operations:**
    -   [ ] Use background callbacks or task queue for long tasks (Backtesting, Optimization, Data Fetching)
-   [ ] **(M) Data Source Management:**
    -   [ ] UI to select/configure data sources (CSV, APIs - Alpha Vantage, etc.)
    -   [ ] More robust data fetching & caching
-   [ ] **(M) Database Integration:**
    -   [ ] Store historical data, configs, results in DB (SQLite/Postgres)
-   [ ] **(L) Data Cleaning/Handling:**
    -   [ ] Options for handling missing data (forward fill, interpolation)
    -   [ ] Basic data validation checks
-   [ ] **(L) Futures/Options Data Support:**
    -   [ ] Adapt data loading and engine for derivative data (significant effort).
-   [ ] **(L) Fundamental Data Integration:**
    -   [ ] Allow strategies to use basic fundamental data (e.g., P/E ratio - requires new data source).

## IV. Professionalism & Maintainability

-   [ ] **(H) Enhanced Error Handling:**
    -   [ ] More user-friendly error messages in UI
    -   [ ] Clearer logging for debugging
-   [ ] **(H) Testing:**
    -   [ ] Increase unit/integration test coverage for core logic and strategies.
-   [ ] **(M) Configuration Management:**
    -   [ ] Centralize configuration settings (paths, defaults, API keys if added).
-   [ ] **(L) Dockerization:**
    -   [ ] Create Dockerfile for easier setup and deployment.
-   [ ] **(L) Performance Profiling:**
    -   [ ] Identify and optimize bottlenecks in backtesting engine or data loading.
