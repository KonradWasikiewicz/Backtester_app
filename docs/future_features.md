# Future Features & Enhancements Roadmap

This document tracks potential features and improvements for the Backtester App, generated on May 4, 2025.

**Priority Legend:** (H) High, (M) Medium, (L) Low

## I. UI/UX Enhancements

-   [ ] **(H) Modernized Wizard:**
    -   [x] Visual Progress Indicator (Stepper)
        > Replace the simple `dbc.Progress` bar with a more interactive component (e.g., using `dbc.Nav` with `dbc.NavItem` or a custom component) showing distinct steps. This provides better context on the user's location in the process and could allow clicking back to completed steps. Involves changes in `src/ui/layouts/strategy_config.py` and `src/ui/callbacks/wizard_callbacks.py`.
    -   [ ] Real-time Input Validation
        > Implement immediate feedback within each step for invalid inputs (e.g., end date before start date, non-numeric capital) using Dash clientside callbacks (`assets/clientside.js`) or server-side callbacks triggered by individual fields. Display errors near the input using `dbc.FormFeedback`. Update callbacks in `src/ui/callbacks/wizard_callbacks.py` and potentially `strategy_callbacks.py`.
    -   [x] Collapsible Completed Steps
        > Modify the wizard callback (`src/ui/callbacks/wizard_callbacks.py`) controlling step visibility (`<step_id>-content`). Keep completed steps collapsed by default to reduce clutter, but allow users to expand them by clicking the header (`<step_id>-header`) for review or edits.

-   [ ] **(H) Enhanced Results Visualization:**
    -   [ ] Interactive Chart Controls (Toggles, Zoom, Scale)
        > Add controls like `dcc.Checklist`, `dbc.RadioItems`, or `dbc.Button` near charts (in `src/ui/layouts/results_display.py`) to allow users to toggle indicators (e.g., moving averages), switch between linear/log scales, or apply zoom presets. Update callbacks in `src/ui/callbacks/backtest_callbacks.py` to modify Plotly figures accordingly.
    -   [ ] Improved Heatmap/Table Features (Sort, Filter, Format)
        > Replace the basic `dbc.Table` for trades with `dash_table.DataTable` in `src/ui/layouts/results_display.py` to leverage built-in sorting and filtering. Enhance the monthly returns heatmap with options for color scales or normalization via callbacks in `src/ui/callbacks/backtest_callbacks.py`.
    -   [ ] Candlestick/OHLC Chart Option
        > Add a toggle (e.g., `dbc.RadioItems`) to the signals chart layout (`src/ui/layouts/results_display.py`). Update the corresponding callback in `src/ui/callbacks/backtest_callbacks.py` to generate either a line plot or a Plotly Candlestick/OHLC trace, requiring OHLC data from `src/services/visualization_service.py`.

-   [ ] **(M) Feedback & Responsiveness:**
    -   [ ] Granular Loading States (Skeletons/Spinners)
        > Wrap individual result components (charts, tables, metric cards in `src/ui/layouts/results_display.py`) with `dcc.Loading`. This provides visual feedback for each component loading data after a backtest run, improving perceived performance.
    -   [ ] User Notifications (Toasts)
        > Add a `dbc.Toast` container to the main layout (`src/ui/app_factory.py`). Modify key callbacks (e.g., in `src/ui/callbacks/backtest_callbacks.py` for backtest start/completion/error) to return new Toast components to this container, providing non-intrusive feedback.
    -   [ ] Mobile/Tablet Responsiveness Review
        > Use browser developer tools to test the UI on various screen sizes. Adjust `dbc.Col` responsive props (`width`, `lg`, `md`, `sm`) and potentially add CSS media queries in `assets/style.css` to ensure the wizard and results display are usable on smaller devices.

-   [ ] **(M) Comparative Analysis:**
    -   [ ] Allow pinning/saving results
        > Add a "Pin Result" button. On click, store key data from `backtest-results-store` (metrics, equity curve) into another `dcc.Store` (e.g., `pinned-results-store`, perhaps a list).
    -   [ ] Side-by-side comparison view (Equity Curve, Key Metrics)
        > Create a new layout section or modal triggered by a "Compare" button. This view would fetch data from the current `backtest-results-store` and the `pinned-results-store` to display metrics and equity curves side-by-side or overlaid. Requires new layout components and callbacks.

-   [ ] **(M) Personalization & Theming:**
    -   [ ] Light/Dark Mode Toggle
        > Add a toggle switch (e.g., `dbc.Switch`) to the header (`src/ui/app_factory.py`). Use a clientside callback (`assets/clientside.js`) to toggle a theme class (e.g., `light-theme`) on the `body` or main container. Define corresponding light theme styles in `assets/style.css`.
    -   [ ] User Preferences (Save Defaults - e.g., capital, date range)
        > Utilize a `dcc.Store` with `storage_type='local'` to persist user settings like theme choice or default wizard inputs. Update callbacks that set initial values (e.g., in `src/ui/layouts/strategy_config.py`) to read from this store first.

-   [ ] **(L) Customizable Dashboard:**
    -   [ ] Allow users to add/remove/rearrange result widgets
        > Explore libraries like `dash-draggable` or `dash-grid-layout` to create a dynamic results dashboard where users can customize the layout of charts and metrics defined in `src/ui/layouts/results_display.py`. This is a significant architectural change.

-   [ ] **(L) Export Results:**
    -   [ ] Export key metrics and trades table to CSV
        > Add "Export CSV" buttons. Implement server-side callbacks using `dcc.send_data_frame` to convert relevant data from `backtest-results-store` into a CSV format for download.
    -   [ ] Export charts as images (PNG/SVG)
        > Add "Export Image" buttons near charts. Implement callbacks using Plotly's `fig.to_image()` (requires `kaleido`) or `fig.to_json()` and a client-side library to generate downloadable images. May require background callbacks for larger charts.
    -   [ ] Generate PDF report (more complex)
        > Use libraries like `reportlab` or `xhtml2pdf` in a background callback. Create a report template, populate it with data and chart images/data from the results store, generate the PDF, and return it via `dcc.send_file`.

-   [ ] **(L) Keyboard Shortcuts:**
    -   [ ] Shortcuts for navigating wizard steps or running backtest.
        > Implement using clientside callbacks (`assets/clientside.js`) listening for `keydown` events. Trigger `n_clicks` on corresponding buttons (e.g., wizard confirm buttons, run backtest) based on specific key combinations (e.g., Ctrl+Enter).

## II. Core Functionality & Strategy

-   [ ] **(H) Strategy/Parameter Optimization UI:**
    -   [ ] Integrate `optimizer.py` into UI
        > Create a new UI section/modal for optimization setup. Include inputs for selecting the strategy, parameters to optimize, defining ranges (min, max, step), and choosing the target metric (e.g., Sharpe Ratio).
    -   [ ] Define Parameter Ranges & Target Metric
        > Ensure the UI allows clear definition of which parameters to optimize and their constraints. The target metric selection should drive the optimization process.
    -   [ ] Display Optimization Results (Table, Parallel Coordinates Plot)
        > Add a "Run Optimization" button triggering a background callback that uses `strategies/optimizer.py`. Display results in a `dash_table.DataTable` (parameter sets vs. metric values) and potentially a Plotly parallel coordinates plot for visualizing trade-offs. Update `src/ui/layouts/` and `src/ui/callbacks/`.

-   [ ] **(H) Advanced Metrics & Analysis:**
    -   [ ] Add metrics (Sortino, Calmar, Omega, VaR, CVaR)
        > Implement the calculation logic for these metrics in `src/analysis/metrics.py`. Ensure they are computed and returned by the backtesting engine/service (`src/core/engine.py`, `src/services/backtest_service.py`).
    -   [ ] Add rolling metric plots (e.g., Rolling Sharpe)
        > Create new chart components in `src/ui/layouts/results_display.py`. Add logic to `src/services/visualization_service.py` to calculate rolling metrics (e.g., using `pandas.rolling().apply()`) and generate corresponding Plotly figures. Update `src/ui/callbacks/backtest_callbacks.py` to display them.

-   [ ] **(M) Portfolio-Level Backtesting:**
    -   [ ] Enhance engine for portfolio allocation rules (Equal Weight, etc.)
        > Modify `src/core/engine.py` to handle multiple tickers simultaneously, applying allocation rules (e.g., equal weight, risk parity) and rebalancing logic defined in `src/portfolio/portfolio_manager.py`. This changes how signals translate to trades across the portfolio.
    -   [ ] Leverage `portfolio_manager.py`
        > Ensure the portfolio manager handles position sizing, cash management, and rebalancing across all assets based on the chosen rules. Update UI to select these rules and display portfolio-level results.

-   [ ] **(M) Strategy Saving/Loading:**
    -   [ ] UI to save/name strategy configurations (params, risk, costs)
        > Add "Save Strategy" and "Load Strategy" buttons/dropdowns. Save could trigger a modal asking for a name. Load would list saved strategies.
    -   [ ] UI to load saved configurations
        > Implement callbacks to save the current configuration from `strategy-config-store` (potentially to browser local storage, a server file, or DB) and to load a selected configuration back into the wizard inputs and the store.

-   [ ] **(M) More Built-in Indicators/Strategies:**
    -   [ ] Add common indicators (MACD, Stochastic, ADX etc.)
        > Leverage `pandas-ta` or implement indicator calculations directly. Ensure they are accessible within the strategy execution context.
    -   [ ] Add corresponding example strategies
        > Create new strategy classes in `src/strategies/` inheriting from `BaseStrategy`, implement `generate_signals` using the new indicators, register them in `src/core/constants.py`, and add default parameters/descriptions.

-   [ ] **(M) Handling Corporate Actions:**
    -   [ ] Adjust prices/shares for stock splits
        > Requires a data source providing split information. Modify `DataLoader` to fetch/store this. Modify `src/core/engine.py` to check for splits on each date and adjust position sizes/cash accordingly before processing signals.
    -   [ ] Option to reinvest dividends
        > Requires dividend data. Modify `DataLoader`. Modify `src/core/engine.py` to add dividend amounts to cash based on holdings on the ex-dividend date. Add UI options to enable/disable these adjustments.

-   [ ] **(L) Walk-Forward Analysis:**
    -   [ ] Implement Walk-Forward Testing/Optimization Logic
        > Implement the walk-forward loop, likely in `src/services/backtest_service.py` or a dedicated module. Define rolling training/testing periods, run optimization (if enabled) on training data, backtest on testing data, and aggregate results.
    -   [ ] UI for configuring Walk-Forward runs
        > Add UI elements to configure walk-forward parameters (window sizes, step size, optimization settings). Display aggregated results. Requires significant changes to backtesting flow and results handling.

-   [ ] **(L) Custom Indicator Support:**
    -   [ ] Allow users to define custom indicators (e.g., via simple formula input or uploaded Python code - complex)
        > Formula input requires parsing and safe evaluation. Python code upload requires careful sandboxing for security. A very advanced feature involving significant complexity and risk if not implemented carefully.

-   [ ] **(L) Advanced Order Types:**
    -   [ ] Simulate Limit Orders, Stop-Limit Orders
        > Modify the `src/core/engine.py` order execution logic. Instead of only market orders, simulate limit/stop orders by checking if price conditions are met in subsequent ticks/bars. May require more granular data or assumptions about intra-bar price movement.

-   [ ] **(L) Short Selling Simulation:**
    -   [ ] Option to allow short positions in strategies.
        > Add a UI option. Modify `src/core/engine.py` and `src/portfolio/portfolio_manager.py` to handle negative positions, potentially including margin requirements and short-selling costs.

## III. Data & Performance

-   [ ] **(H) Asynchronous Operations:**
    -   [ ] Use background callbacks or task queue for long tasks (Backtesting, Optimization, Data Fetching)
        > Identify long-running callbacks (e.g., `run_backtest`). Convert them using `background=True`. Update outputs for progress indication (`dcc.Progress`) and handle cancellation. Requires a backend store (Redis, Celery) for robust background task management beyond simple cases.

-   [ ] **(M) Data Source Management:**
    -   [ ] UI to select/configure data sources (CSV, APIs - Alpha Vantage, etc.)
        > Add a UI section/modal for managing data sources (type, path, API keys).
    -   [ ] More robust data fetching & caching
        > Refactor `src/core/data.py` (`DataLoader`) to support different fetching methods. Implement caching (e.g., `joblib.Memory`, database) to avoid redundant downloads/processing.

-   [ ] **(M) Database Integration:**
    -   [ ] Store historical data, configs, results in DB (SQLite/Postgres)
        > Choose DB (SQLite via `sqlite3` is simplest). Define schema. Modify `DataLoader` to read/write price data. Modify `backtest_service.py` to save results. Modify strategy save/load to use the DB. Enables persistence and easier querying.

-   [ ] **(L) Data Cleaning/Handling:**
    -   [ ] Options for handling missing data (forward fill, interpolation)
        > Add UI options (e.g., dropdown) for handling `NaN` values. Apply the selected method (e.g., `fillna()`, `interpolate()`) in `DataLoader` after loading raw data.
    -   [ ] Basic data validation checks
        > Add checks in `DataLoader` for common issues like non-numeric data or unexpected columns.

-   [ ] **(L) Futures/Options Data Support:**
    -   [ ] Adapt data loading and engine for derivative data (significant effort).
        > Requires major changes to `DataLoader` for new data formats (expiry, strike) and `src/core/engine.py` for derivative contract logic, margin, and P&L calculations.

-   [ ] **(L) Fundamental Data Integration:**
    -   [ ] Allow strategies to use basic fundamental data (e.g., P/E ratio - requires new data source).
        > Integrate a fundamental data source. Modify `DataLoader` to fetch and merge this data (aligning dates). Allow strategies in `src/strategies/` to access the merged data.

## IV. Professionalism & Maintainability

-   [ ] **(H) Enhanced Error Handling:**
    -   [ ] More user-friendly error messages in UI
        > Catch exceptions in callbacks (`try...except`). Return user-friendly messages via `dbc.Alert` or `dbc.Toast` instead of generic errors. Use custom exceptions from `src/core/exceptions.py`.
    -   [ ] Clearer logging for debugging
        > Review logging levels and messages. Ensure tracebacks are logged for unexpected errors. Configure file logging (`app.py`, `app_factory.py`) effectively.

-   [ ] **(H) Testing:**
    -   [ ] Increase unit/integration test coverage for core logic and strategies.
        > Write more `pytest` tests for `src/analysis/metrics.py`, `src/core/engine.py`, individual strategies, and services. Cover different scenarios and edge cases to improve reliability.

-   [ ] **(M) Configuration Management:**
    -   [ ] Centralize configuration settings (paths, defaults, API keys if added).
        > Create a central config file (e.g., `config.yaml`, `settings.py`) or use environment variables. Load settings via `src/core/config.py` and use them application-wide instead of hardcoding values.

-   [ ] **(L) Dockerization:**
    -   [ ] Create Dockerfile for easier setup and deployment.
        > Create a `Dockerfile` specifying base image, dependencies (`requirements.txt`), copying files, and the run command (`python app.py`). Add `.dockerignore`. Simplifies deployment and environment consistency.

-   [ ] **(L) Performance Profiling:**
    -   [ ] Identify and optimize bottlenecks in backtesting engine or data loading.
        > Use profiling tools (`cProfile`, `snakeviz`, `py-spy`) to analyze `src/core/engine.py` execution time. Identify slow functions/operations and optimize them (e.g., using vectorized pandas/numpy operations).

## V. ID Management & Code Cohesion (Generated from Roadmap)

**Phase 1 Status: Substantially Completed. Unused IDs have been commented out in `src/ui/ids/ids.py`. The main structure for ID management is in place.**

-   [x] **(M) Complete Risk Management UI Integration:**
    -   The Risk Management step (Step 4) in the wizard uses IDs from `src/ui/ids/ids.py`.
    -   **ID Usage Status (WizardIDs - Risk Management):**
        -   ~`WizardIDs.RISK_MANAGEMENT_CONTAINER`~: **Commented out (unused).**
        -   `WizardIDs.TRADING_COSTS_CONTAINER`: **Commented out (unused).** (Related to Step 5 but listed here for wizard containers)
        -   `WizardIDs.REBALANCING_CONTAINER`: **Commented out (unused).** (Related to Step 6 but listed here for wizard containers)
        -   `WizardIDs.SUMMARY_STRATEGY_NAME`: **Commented out (unused).**
        -   `WizardIDs.SUMMARY_INITIAL_CAPITAL`: **Commented out (unused).**
        -   The following IDs are **confirmed to be in use** for Risk Management and other wizard steps:
            -   `WizardIDs.RISK_FEATURES_CHECKLIST`
            -   `WizardIDs.MAX_POSITION_SIZE_INPUT`
            -   `WizardIDs.STOP_LOSS_TYPE_SELECT`
            -   `WizardIDs.STOP_LOSS_INPUT`
            -   `WizardIDs.TAKE_PROFIT_TYPE_SELECT`
            -   `WizardIDs.TAKE_PROFIT_INPUT`
            -   `WizardIDs.MAX_RISK_PER_TRADE_INPUT`
            -   `WizardIDs.MARKET_TREND_LOOKBACK_INPUT`
            -   `WizardIDs.MAX_DRAWDOWN_INPUT`
            -   `WizardIDs.MAX_DAILY_LOSS_INPUT`
            -   `WizardIDs.CONFIRM_RISK_BUTTON`
            -   `WizardIDs.RISK_PANEL_POSITION_SIZING`
            -   `WizardIDs.RISK_PANEL_STOP_LOSS`
            -   `WizardIDs.RISK_PANEL_TAKE_PROFIT`
            -   `WizardIDs.RISK_PANEL_RISK_PER_TRADE`
            -   `WizardIDs.RISK_PANEL_MARKET_FILTER`
            -   `WizardIDs.RISK_PANEL_DRAWDOWN_PROTECTION`
            -   `WizardIDs.RISK_MANAGEMENT_STORE_WIZARD`
            -   Other wizard step IDs (strategy selection, dates, tickers, costs, rebalancing inputs, summary structure) are also in use.
    -   **Action:** Future development for Step 4 should ensure all necessary components are implemented and use existing defined IDs where appropriate, or new IDs are added to `ids.py`. The commented-out container IDs can be reinstated if a specific container component is added to the layout for these steps.

-   [x] **(M) Review Unused ResultsIDs:**
    -   The following IDs within the `ResultsIDs` class were found to be unused and have been **commented out** in `src/ui/ids/ids.py`:
        -   ~`ResultsIDs.PORTFOLIO_VALUE_BUTTON`~
        -   ~`ResultsIDs.PORTFOLIO_RETURNS_BUTTON`~
        -   ~`ResultsIDs.PORTFOLIO_VALUE_CURRENCY_USD`~
        -   ~`ResultsIDs.PORTFOLIO_VALUE_CURRENCY_PERCENT`~
        -   ~`ResultsIDs.TRADES_TABLE_CONTAINER`~
        -   ~`ResultsIDs.TRADES_TABLE_LOADING`~
        -   ~`ResultsIDs.PERFORMANCE_METRICS_CONTAINER`~
        -   ~`ResultsIDs.TRADE_METRICS_CONTAINER`~
        -   ~`ResultsIDs.BACKTEST_STATUS_MESSAGE`~
        -   ~`ResultsIDs.BACKTEST_PROGRESS_BAR`~
        -   ~`ResultsIDs.BACKTEST_PROGRESS_BAR_CONTAINER`~
        -   ~`ResultsIDs.BACKTEST_PROGRESS_LABEL_TEXT`~
        -   ~`ResultsIDs.BACKTEST_ANIMATED_TEXT`~
        -   ~`ResultsIDs.BACKTEST_PROGRESS_DETAIL_TEXT`~
        -   ~`ResultsIDs.BACKTEST_ANIMATION_INTERVAL`~
        -   ~`ResultsIDs.RESULTS_AREA_WRAPPER`~
        -   ~`ResultsIDs.CENTER_PANEL_COLUMN`~
        -   ~`ResultsIDs.RIGHT_PANEL_COLUMN`~
    -   **Action:** If these features/components are planned, the corresponding IDs can be uncommented and implemented. Otherwise, they can be permanently removed later.

-   [x] **(M) Address StrategyConfigIDs Discrepancies and Unused IDs:**
    -   **Discrepancy Resolution:**
        -   `WizardIDs.STRATEGY_CONFIG_CONTAINER` is used in `src/ui/wizard/layout.py` for the wizard's main container.
        -   `StrategyConfigIDs.CONFIG_CONTAINER` ("strategy-config-container-main") remains defined in `ids.py` and is intended for a potential non-wizard "main page" configuration area, which is not yet implemented.
    -   **Unused `StrategyConfigIDs` (for main page):** A significant number of IDs in `StrategyConfigIDs` (intended for a main page configuration separate from the wizard) are defined but not yet used in any layout. These include most `_MAIN` suffixed IDs (e.g., `STRATEGY_SELECTOR_MAIN`, `INITIAL_CAPITAL_INPUT_MAIN`, etc.) and the `_ALT` suffixed IDs.
    -   **IDs in Use (StrategyConfigIDs):**
        -   `StrategyConfigIDs.RUN_BACKTEST_BUTTON_MAIN` (used in `app_factory.py`)
        -   `StrategyConfigIDs.STRATEGY_CONFIG_STORE_MAIN` (used in `app_factory.py`)
        -   The `_LEGACY` suffixed IDs (e.g., `TICKER_INPUT_LEGACY`) were used in `strategy_config.py` after refactoring.
    -   **Action:**
        1.  The distinction between `WizardIDs.STRATEGY_CONFIG_CONTAINER` (for wizard) and `StrategyConfigIDs.CONFIG_CONTAINER` (for potential main page) is now clear.
        2.  The list of unused `StrategyConfigIDs` for the main page remains as a reference for future development of that interface. They are not considered obsolete at this stage but represent unimplemented features.

-   [x] **(COMPLETED - Initial Pass) Identify IDs Used in Layout/Callback Files NOT Defined in ids.py:**
    -   Systematic search across UI files (`src/ui/layouts/`, `src/ui/callbacks/`, `src/ui/components/`, `src/ui/wizard/`, `src/ui/app_factory.py`) was performed.
    -   Identified hardcoded IDs were centralized into `src/ui/ids/ids.py`.
    -   **Action:** This task is complete for the initial refactoring. Ongoing vigilance will be needed as new components are developed.

-   [x] **(COMPLETED - Initial Pass) Enforce Consistent ID Naming and Usage:**
    -   Corrections were applied to ensure `ids.py` is the single source of truth and that IDs are used as defined within the refactored files.
    -   **Action:** This task is complete for the initial refactoring. Future code should adhere to this standard.

**Summary of Phase 1 (ID Management):**
The primary goals of auditing, centralizing, and refactoring UI component IDs have been met. Hardcoded IDs have been moved to `src/ui/ids/ids.py`, and relevant files have been updated to use these centralized IDs. Unused IDs identified during the audit have been commented out for future review or potential removal. The codebase is now in a better state for managing UI component IDs.
