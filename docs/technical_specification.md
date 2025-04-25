# Backtester App - Technical Specification

## 1. System Architecture

### 1.1 Architecture Overview
Backtester App uses a layered architecture with division into functional modules. The main user interface is a web application built using Dash (a wrapper for React), while the business logic is implemented in Python.

### 1.2 System Components

#### 1.2.1 Core
Contains the basic business logic of the application:
- `backtest_manager.py` - Management of the backtesting process
- `data.py` - Loading and processing historical data
- `config.py` - Application configuration
- `constants.py` - System constants
- `engine.py` - Simulation engine
- `exceptions.py` - Custom application exceptions

#### 1.2.2 Strategies
Implementations of trading strategies:
- `base.py` - Base class for all strategies
- `moving_average.py` - Moving average crossover strategy
- `rsi.py` - Strategy based on Relative Strength Index
- `bollinger.py` - Strategy using Bollinger Bands

#### 1.2.3 Portfolio
Management of portfolio and positions:
- `portfolio_manager.py` - Portfolio state management
- `risk_manager.py` - Risk management

#### 1.2.4 Analysis
Analysis of backtest results:
- `metrics.py` - Calculation of performance indicators (CAGR, Sharpe, etc.)

#### 1.2.5 UI
User interface:
- `app_factory.py` - Creating Dash application instances, includes main layout structure with `dcc.Store` for state management.
- `components.py` - Reusable UI components
- `callbacks/` - Dash callback implementations (now utilizing `dcc.Store` for results state)
- `layouts/` - Layout templates (including results display with loading indicators)

#### 1.2.6 Visualization
Generating visualizations:
- `visualizer.py` - Main class for creating visualizations
- `chart_utils.py` - Helper functions for creating charts

### 1.3 Data Flow Diagram

```
[Historical Data] --> [DataLoader] --> [BacktestManager] --> [Strategy] --> [PortfolioManager]
                                           |                                       |
                                           v                                       v
                                    [BacktestService] <-- [RiskManager] <-- [Positions/Trades]
                                           |
                                           v
                                    [Visualization] --> [UI]
```

### 1.4 Logging System

The application uses Python's built-in `logging` module with a simplified configuration:

- Centralized configuration in `app.py` and `app_factory.py`
- Console-only logging (no file handlers) for easier maintenance
- Structured log format with timestamps, level, module name, and line numbers
- External library log suppression to reduce noise
- Log levels:
  - DEBUG: Detailed information for troubleshooting
  - INFO: Confirmation that things are working
  - WARNING: Indication of potential issues
  - ERROR: Errors that allow the application to continue running
  - CRITICAL: Errors that prevent the application from functioning

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
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    # Limit external library logs
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("dash").setLevel(logging.WARNING)
```

## 2. Technologies and Libraries

### 2.1 Backend
- **Python 3.8+** - Programming language
- **pandas** - Data manipulation, analysis
- **numpy** - Numerical calculations
- **plotly** - Creating interactive charts

### 2.2 Frontend
- **Dash** - Framework for web applications in Python
- **Bootstrap** - CSS framework for responsive design
- **Plotly.js** - Chart library (used by Dash)

### 2.3 Developer Tools
- **Git** - Version control
- **SemVer** - Semantic versioning standard

## 3. Data Flow and Algorithms

### 3.1 Loading Data
```python
# Pseudocode
class DataLoader:
    def load_data(ticker):
        data = read_csv_file(f"data/{ticker}.csv")
        return process_data(data)
        
    def process_data(data):
        # Date conversion, sorting, cleaning
        return processed_data
```

### 3.2 Generating Signals
```python
# Pseudocode
class BaseStrategy:
    def generate_signals(self, data):
        # Implementation in derived classes
        pass
        
class MovingAverageStrategy(BaseStrategy):
    def generate_signals(self, data):
        fast_ma = calculate_ma(data, self.fast_period)
        slow_ma = calculate_ma(data, self.slow_period)
        
        buy_signals = fast_ma > slow_ma & fast_ma.shift() <= slow_ma.shift()
        sell_signals = fast_ma < slow_ma & fast_ma.shift() >= slow_ma.shift()
        
        return create_signal_series(buy_signals, sell_signals)
```

### 3.3 Portfolio Management
```python
# Pseudocode
class PortfolioManager:
    def process_signals(self, signals, prices):
        for date, signal in signals.items():
            if signal > 0 and self.cash > 0:
                # Buy logic
                self.open_position(date, price, shares)
            elif signal < 0 and has open positions():
                # Sell logic
                self.close_position(date, price)
```

### 3.4 Visualizing Results
```python
# Pseudocode
class BacktestVisualizer:
    def create_equity_curve(self, portfolio_values):
        fig = create_line_chart(portfolio_values)
        return fig
        
    def create_monthly returns heatmap(self, returns):
        monthly_returns = convert_to_monthly(returns)
        fig = create_heatmap(monthly_returns)
        return fig
```

## 4. User Interface Structure

### 4.1 Main Layout
- Side panel (strategy configuration)
- Main panel (results and charts)
- Header (app name, version)
- Footer (information, links)

### 4.2 Strategy Configuration Panel
- Strategy selector (dropdown)
- Strategy parameters (dynamic fields)
- Instrument selector (multi-checkbox)
- Date range (slider + date picker)
- Risk management (expandable panel)
- "Run Backtest" button

### 4.3 Results Panel
- Summary metrics (cards)
- Portfolio chart
- Monthly returns heatmap
- Trades table
- Signals chart

## 5. Application State Management

### 5.1 Callback Flow
In Dash, data flow between components occurs via callbacks that react to user events. Main callbacks:

1. Updating strategy parameters based on selected strategy
2. Filtering available instruments based on search
3. Updating date range based on slider/pickers
4. Running backtest: This callback now triggers an update to a central `dcc.Store` component (`backtest-results-store`) upon completion or failure.
5. Updating results display (metrics, charts, tables): These callbacks are now triggered by changes in the `backtest-results-store` data, ensuring they update only when new results are available.
6. Individual loading states for result components are managed, and a main overlay loader is controlled based on the combined state of these components.

### 5.2 Callback Division in the Project
Callbacks are grouped by functionality:
- `strategy_callbacks.py` - Callbacks related to strategy configuration
- `backtest_callbacks.py` - Callbacks related to running the backtest and updating all result components (triggered by `dcc.Store`).
- `risk_management_callbacks.py` - Callbacks for managing risk settings

## 6. Version Management and Migrations

### 6.1 Versioning
The project uses SemVer (Semantic Versioning) for clear version marking:
- **MAJOR** - changes breaking backward compatibility
- **MINOR** - new features (backward compatible)
- **PATCH** - bug fixes (backward compatible)

### 6.2 New Version Deployment Process
1. Development in the `develop` branch
2. Testing and stabilization
3. Updating version and changelog
4. Merge to `main` branch
5. Creating version tag

### 6.3 Reverting to Previous Versions
Process for restoring a previous application version:
```bash
# Example Git commands
git checkout tags/v1.0.0
```

### 6.4 Dependency Management
Dependencies are frozen for each version:
```bash
pip freeze > requirements.txt
```

Restoring dependencies for a specific version:
```bash
pip install -r requirements.txt
```

## 7. Known Issues and Technical Limitations

### 7.1 Dash Callback Issues
- **Previous Issue (Resolved/Mitigated):** The application previously used advanced monkey-patching techniques to solve problems with duplicate callbacks. 
- **Current Approach:** The refactoring to use `dcc.Store` for managing the backtest results state has simplified the callback structure for the results section, reducing the complexity and potential for duplicate output issues in that area. While this specific issue is largely addressed for results display, careful callback design remains important throughout the application.

### 7.2 Backtest Performance
For large datasets or complex strategies, backtest execution time can be long. Optimization for performance is necessary, potentially using parallel processing.

*Documentation version: 1.3*