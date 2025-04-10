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
   ```

## Running the Application

```
python app.py
```

The application will be available at http://127.0.0.1:8050/ in your browser.

## Versioning System

The project uses **Semantic Versioning (SemVer)** in MAJOR.MINOR.PATCH format:
- **MAJOR**: Breaking changes to backward compatibility
- **MINOR**: New features maintaining backward compatibility
- **PATCH**: Bug fixes maintaining backward compatibility

## Version Management

The project includes a set of scripts for version management that facilitate working with SemVer and Git:

### Updating Versions

```
python scripts/update_version.py --minor --changes "Added new strategy" "Fixed interface bugs"
```

Available options:
- `--major`: Increases major version (MAJOR)
- `--minor`: Increases minor version (MINOR)
- `--patch`: Increases patch version (PATCH)
- `--pre`: Adds pre-release label (e.g., alpha, beta, rc)
- `--pre-num`: Pre-release version number (e.g., for beta.1)
- `--build`: Build metadata
- `--changes`: List of changes to add to the changelog

### Tagging Versions in Git Repository

```
python scripts/tag_version.py
```

The script automatically:
1. Gets the current version from `src/version.py`
2. Creates a Git tag with "v" prefix (e.g., v1.2.3)
3. Adds changelog information to the tag description
4. Optionally publishes the tag to the remote repository

### Restoring Previous Versions

```
python scripts/restore_version.py --list
python scripts/restore_version.py --version v1.0.0 --deps
```

Available options:
- `--list`: Displays list of available versions
- `--version`: Specifies version to restore
- `--deps`: Installs dependencies for the restored version
- `--force`: Forces checkout (discards local changes)

Without specifying a version, the script will display an interactive selection menu.

## Documentation

More detailed documentation is available in the `docs/` directory:
- [Product Design Specification](docs/product_design_specification.md)
- [Technical Specification](docs/technical_specification.md)

## License

[License information]

## Contact

[Contact information]
