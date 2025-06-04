# Backtester App

An application for testing investment strategies on historical data.

## About the Project

Backtester App is a tool for testing and analyzing trading strategies using historical market data. It enables configuration of various strategies, risk management, and visualization of results through interactive charts and tables.

## Features

- Testing predefined strategies (Moving Average Crossover, RSI, Bollinger Bands)
- Strategy parameter configuration
- Risk management with multiple options (position sizing, stop-loss, take-profit)
- Result analysis with key metrics (CAGR, Sharpe Ratio, max drawdown)
- Interactive visualizations (equity charts, returns heatmap, signal charts)
- Intuitive wizard interface with visual stepper navigation
- Import tickers via modal (paste text or upload file)
- `StrategyTemplateGenerator` utility for creating new strategy templates


## Installation

1. Make sure you have Python 3.8 or newer installed
2. Clone the repository
   ```
   git clone https://github.com/KonradWasikiewicz/Backtester_app.git
   cd Backtester_app
   ```
3. Install required dependencies
   ```
   pip install -r requirements.txt
   # This installs all required packages, including pandas-ta.
   # pandas-ta currently fails with numpy 2.x, so numpy is pinned below 2.0.
   # If you see "ImportError: cannot import name 'NaN' from 'numpy'",
   # reinstall numpy<2.0 to resolve the issue.
   ```

## Running the Application

```
python app.py
```

By default the app uses host `127.0.0.1` and port `8050`. You can override these
values:

```
python app.py --host 0.0.0.0 --port 8060
```

The application will then be available at the provided address.


## Configuration via Environment Variables
Several settings can be customized before running the app:

- `BACKTESTER_DATA_PATH` - path to the historical prices CSV
- `BACKTESTER_BENCHMARK` - ticker symbol used as the benchmark
- `BACKTESTER_START_DATE` - backtest start date (YYYY-MM-DD)
- `BACKTESTER_END_DATE` - backtest end date (YYYY-MM-DD)
- `BACKTESTER_CAPITAL` - starting capital for simulations

Example usage:
```bash
export BACKTESTER_START_DATE=2019-01-01
export BACKTESTER_END_DATE=2019-12-31
python app.py
```

## Client-Side Error Logging

Errors from the browser are sent to the `/log-client-errors` endpoint. The
frontend JavaScript captures uncaught errors and posts them to this route so
they can be logged by the server.

## Versioning System

The project uses **Semantic Versioning (SemVer)** in MAJOR.MINOR.PATCH format:
- **MAJOR**: Breaking changes to backward compatibility
- **MINOR**: New features maintaining backward compatibility
- **PATCH**: Bug fixes maintaining backward compatibility

## Version Management

The project uses a unified version management system via `scripts/version_manager.py` that follows Semantic Versioning (MAJOR.MINOR.PATCH). See the [Workflow Guide](docs/workflow_guide.md) for detailed usage.

### Key Commands

```bash
# Display current version
python scripts/version_manager.py info

# Update version (e.g., patch)
python scripts/version_manager.py update patch --changes "Description of changes"

# Create and push git tag
python scripts/version_manager.py tag --push

# Restore a previous version
python scripts/version_manager.py restore --version vX.Y.Z
```

## Project Structure

Key directories and files:

```
app.py                 # Main application entry point
requirements.txt       # Project dependencies
assets/                # CSS and JavaScript files
data/                  # Historical data files
docs/                  # Project documentation
logs/                  # Log files
scripts/               # Utility and management scripts
  version_manager.py   # Script for version control
src/
  __init__.py
  version.py           # Stores current version
  analysis/            # Performance metrics calculation
  core/                # Core backtesting logic, data handling
  portfolio/           # Portfolio and risk management
  services/            # Application layer services
  strategies/          # Trading strategy implementations
  ui/                  # User Interface (Dash)
    app_factory.py     # Creates the Dash app instance
    components.py      # Reusable UI components
    callbacks/         # Dash callback definitions
    layouts/           # UI layout definitions
    wizard/            # Multi-step configuration wizard UI
  visualization/       # Charting and visualization logic
```

## Documentation

Detailed documentation is available in the `docs/` directory:
- [Project Context](docs/project_context.md)
- [Architecture Guide](docs/technical_specification.md)
- [Product Design Specification](docs/product_design_specification.md)
- [Technical Specification](docs/technical_specification.md)
- [Aesthetics Guidelines](docs/aesthetics_guidelines.md)
- [Workflow Guide](docs/workflow_guide.md)
- [Stepper Implementation](docs/stepper_implementation.md)

## License

[License information]

## Contact

[Contact information]
