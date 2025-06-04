# Backtester App - Technical Specification

## 1. System Architecture

### 1.1 Architecture Overview
Backtester App uses a layered architecture with division into functional modules. The main user interface is a web application built using Dash (a wrapper for React), while the business logic is implemented in Python.

```
             ┌─────────────────────────┐
             │       UI Layer          │
             │ (Dash Components & UI)  │
             └──────────┬──────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│            Application Layer                  │
│  (Controllers, Services, Callback Handlers)   │
└───┬───────────────────────┬──────────────┬────┘
    │                       │              │
    ▼                       ▼              ▼
┌─────────────┐    ┌─────────────────┐   ┌────────────────┐
│  Core Logic │    │ Strategy Layer  │   │ Portfolio Mgmt │
│  (Engine)   │    │                 │   │                │
└──────┬──────┘    └──────┬──────────┘   └───────┬────────┘
       │                  │                      │
       └──────────────────┼──────────────────────┘
                          │
                          ▼
                ┌───────────────────┐
                │     Data Layer    │
                │                   │
                └───────────────────┘
```

### 1.2 Component Responsibilities & Structure

#### 1.2.1 UI Layer (`src/ui/`)
- **Responsibility**: Present information, capture user input. No business logic. Interacts only with Application Layer. Uses `dcc.Store` for state management (e.g., backtest results).
- **Sub-components**:
    - `app_factory.py`: App setup, main layout, `dcc.Store` definitions.
    - `wizard/`: Strategy configuration wizard layout.
    - `layouts/`: Page layout components (e.g., results display).
    - `components/`: Reusable UI elements (cards, tooltips).
    - `callbacks/`: UI event handlers (Dash callbacks).

#### 1.2.2 Application Layer (`src/services/`)
- **Responsibility**: Orchestrate workflow between UI and business logic. Stateless where possible.
- **Key Services**:
    - `BacktestService`: Coordinates backtesting operations.
    - `DataService`: Manages data retrieval and transformation.
    - `VisualizationService`: Prepares data for visualization.

#### 1.2.3 Core Logic Layer (`src/core/`)
- **Responsibility**: Implement primary business logic (backtest engine, configuration). Independent of UI/Application layers.
- **Key Components**:
    - `backtest_manager.py`: Manages backtest execution process.
    - `engine.py`: Core backtest simulation logic.
    - `config.py`: Application configuration.
    - `constants.py`: System constants.
    - `exceptions.py`: Custom application exceptions.

#### 1.2.4 Strategy Layer (`src/strategies/`)
- **Responsibility**: Implement trading strategies and signal generation. Adheres to a common interface (`base.py`). Independent of UI/Visualization.
- **Components**: `base.py`, individual strategies (`moving_average.py`, `rsi.py`, `bollinger.py`), `validator.py`.

#### 1.2.5 Portfolio Management Layer (`src/portfolio/`)
- **Responsibility**: Manage portfolio state, positions, and risk controls.
- **Components**: `portfolio_manager.py`, `risk_manager.py`.

#### 1.2.6 Data Layer (`src/core/data.py`)
- **Responsibility**: Data access, transformation, caching. Abstracts data sources.
- **Note**: Currently integrated within `src/core/`, primarily in `data.py`.

#### 1.2.7 Visualization Layer (`src/visualization/`)
- **Responsibility**: Create graphical representations of backtest results. Separated from data processing.
- **Components**: `visualizer.py`, `chart_utils.py`.

### 1.3 Communication & Data Flow

- **UI → Application**: Callbacks invoke Service methods. UI updates/reacts to `dcc.Store` state changes.
- **Application → Core/Strategy/Portfolio**: Services coordinate requests.
- **Core/Strategy/Portfolio → Data**: Business logic requests data via abstractions (currently `DataService` or direct use of `DataLoader` within `core`).
- **Application → Visualization**: Services prepare data for `VisualizationService` or `visualizer.py`.

**Data Flow Diagram:**
```
[Historical Data] --> [DataService/DataLoader] --> [BacktestManager] --> [Strategy] --> [PortfolioManager]
                                     |                                       |
                                     v                                       v
                              [BacktestService] <-- [RiskManager] <-- [Positions/Trades]
                                     |
                                     v
                              [VisualizationService/Visualizer] --> [UI]
```

### 1.4 Logging System

The application uses Python's built-in `logging` module with a simplified configuration:

- Centralized configuration in `app.py` and `app_factory.py`.
- Console-only logging (no file handlers).
- Structured log format: `%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s`.
- External library log suppression (e.g., werkzeug, urllib3, dash set to WARNING).
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.

Client-side JavaScript errors are sent via POST requests to the
`/log-client-errors` route. This endpoint logs received errors, warnings and
messages on the server for easier debugging.

Example log configuration from `app_factory.py`:
```python
def configure_logging(log_level=logging.INFO) -> None:
    # Check if root logger already has handlers to prevent duplicate setup
    if not logging.getLogger().hasHandlers():
        log_format = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # Configure root logger with console output only
        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.StreamHandler(sys.stdout) # Use sys.stdout for compatibility
            ]
        )

    # Limit external library logs
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("dash").setLevel(logging.WARNING)
```

## 2. Technologies and Libraries

### 2.1 Backend
- **Python 3.8+**
- **pandas**: Data manipulation, analysis
- **numpy**: Numerical calculations
- **plotly**: Creating interactive charts

### 2.2 Frontend
- **Dash**: Framework for web applications in Python
- **Bootstrap**: CSS framework for responsive design
- **Plotly.js**: Chart library (used by Dash)

### 2.3 Developer Tools
- **Git**: Version control
- **SemVer**: Semantic versioning standard
- **StrategyTemplateGenerator**: Generates boilerplate code for new strategies

## 3. Key Algorithms (Pseudocode Examples)

### 3.1 Loading Data
```python
# Pseudocode (Illustrative - Actual implementation uses DataService/DataLoader)
class DataService:
    def load_data(ticker, start_date, end_date):
        # Reads from cache or source (e.g., CSV)
        data = read_source(f"data/{ticker}.csv")
        data = filter_by_date(data, start_date, end_date)
        return process_data(data) # Cleaning, date conversion, etc.

    def process_data(data):
        # Date conversion, sorting, cleaning, feature engineering
        return processed_data
```

### 3.2 Generating Signals
```python
# Pseudocode
class BaseStrategy:
    def generate_signals(self, ticker, data):
        # Implementation in derived classes
        pass

class MovingAverageStrategy(BaseStrategy):
    def generate_signals(self, ticker, data):
        fast_ma = calculate_ma(data['Close'], self.fast_period)
        slow_ma = calculate_ma(data['Close'], self.slow_period)

        buy_signals = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        sell_signals = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))

        signals = pd.Series(0, index=data.index)
        signals[buy_signals] = 1
        signals[sell_signals] = -1
        return pd.DataFrame({'Signal': signals})
```

### 3.3 Portfolio Management
```python
# Pseudocode (Illustrative - Actual implementation in PortfolioManager/Engine)
class PortfolioManager:
    def update_portfolio(self, date, ticker, signal, price, available_cash, current_holdings):
        if signal > 0 and available_cash > 0:
            # Apply position sizing logic
            shares_to_buy = calculate_shares(available_cash, price, risk_settings)
            # Apply risk checks (e.g., max position size)
            if check_risk(shares_to_buy):
                # Execute buy: update cash, update holdings
                self.execute_trade(date, ticker, 'BUY', shares_to_buy, price)
        elif signal < 0 and ticker in current_holdings:
            # Apply risk checks (e.g., stop-loss)
            shares_to_sell = current_holdings[ticker]['shares']
            if check_risk_on_sell():
                # Execute sell: update cash, update holdings
                self.execute_trade(date, ticker, 'SELL', shares_to_sell, price)
```

### 3.4 Visualizing Results
```python
# Pseudocode (Illustrative - Actual implementation in VisualizationService/Visualizer)
class VisualizationService:
    def create_equity_curve(self, portfolio_history):
        # Use plotly to create line chart of portfolio value over time
        fig = create_line_chart(portfolio_history['timestamp'], portfolio_history['total_value'])
        return fig

    def create_monthly_returns_heatmap(self, daily_returns):
        monthly_returns = aggregate_to_monthly(daily_returns)
        # Use plotly to create heatmap
        fig = create_heatmap(monthly_returns)
        return fig
```

## 4. User Interface Structure

### 4.1 Main Layout
- **Header**: App name, version.
- **Sidebar/Configuration Panel**: Strategy selection, parameters, instruments, date range, risk settings, run button (potentially using a wizard structure).
- **Main Content Panel**: Backtest results (summary metrics, charts, tables).
- **Footer**: Information, links.

### 4.2 Strategy Configuration Panel (Wizard Example)
- **Step 1**: Initial Capital, Strategy Selection & Parameters.
- **Step 2**: Date Range Selection.
- **Step 3**: Ticker Selection.
- **Step 4**: Risk Management Configuration (expandable/conditional sections).
- **Step 5**: Trading Costs (Commission, Slippage).
- **Step 6**: Rebalancing Rules.
- **Step 7**: Summary & Run Backtest Button.

### 4.3 Results Panel
- **Summary Metrics**: Cards displaying key performance indicators (KPIs) like CAGR, Sharpe Ratio, Win Rate, etc. (Uses `create_metric_card_with_tooltip`).
- **Charts**: Equity Curve, Monthly Returns Heatmap, Drawdown Chart, Signals on Price Chart.
- **Tables**: List of executed trades, potentially performance breakdown by ticker.

## 5. Application State Management

### 5.1 Callback Flow
- User interactions trigger Dash callbacks (defined in `src/ui/callbacks/`).
- Callbacks primarily interact with methods in the **Application Layer** (`src/services/`).
- **Backtest Results Handling**:
    1. The "Run Backtest" button callback triggers the `BacktestService`.
    2. Upon completion (success or failure), the service updates the `backtest-results-store` (`dcc.Store` component defined in `app_factory.py`).
    3. Callbacks responsible for displaying results (metrics, charts, tables) are triggered *only* by changes to `backtest-results-store`.
    4. Loading indicators (`dcc.Loading`) wrap result components, managed by the state of the callbacks updating them.

### 5.2 Callback Grouping
Callbacks are organized into modules within `src/ui/callbacks/` based on functionality:
- `strategy_callbacks.py`: Strategy selection, parameter updates.
- `wizard_callbacks.py`: Logic for navigating the multi-step configuration wizard.
- `risk_management_callbacks.py`: Handling risk feature selection and parameter inputs.
- `backtest_callbacks.py`: Initiating the backtest and updating all result components based on `backtest-results-store`.

## 6. Version Management and Deployment

### 6.1 Versioning
- Uses SemVer (MAJOR.MINOR.PATCH) via `src/version.py`.
- Managed by `scripts/version_manager.py`.
- Automated version bumps via git hooks possible (see `workflow_guide.md`).

### 6.2 Deployment Process (Conceptual)
1. Development in feature branches or `develop`.
2. Testing and stabilization.
3. Update version and changelog (`scripts/version_manager.py update ...`).
4. Merge to `main` branch.
5. Create git tag (`scripts/version_manager.py tag --push`).
6. (Future) Build/deploy application package.

### 6.3 Dependency Management
- Dependencies listed in `requirements.txt`.
- Use `pip freeze > requirements.txt` to update.
- Install with `pip install -r requirements.txt`.

## 7. Known Issues and Technical Limitations

### 7.1 Dash Callback Complexity
- **Mitigation**: Using `dcc.Store` for results state significantly simplifies the callback graph for the results section, reducing potential duplicate output issues. Careful design is still needed for other complex interactions (e.g., wizard).

### 7.2 Backtest Performance
- Execution time can be long for large datasets or complex strategies.
- **Potential Optimizations**: Vectorization (NumPy/Pandas), caching intermediate results, parallel processing (requires careful state management).

---
*Documentation version: 1.4 (Merged Architecture)*
*Last updated: May 5, 2025*