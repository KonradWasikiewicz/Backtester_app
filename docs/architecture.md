# Backtester App - Architecture Guide

This document describes the architecture of the Backtester App project, focusing on the logical separation of functionality and the responsibilities of each component. Following these guidelines will help maintain a clean architecture and make changes more manageable.

## High-Level Architecture

The application follows a layered architecture with clear separation of concerns:

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

## Component Responsibilities

## 1. UI Layer

**Location**: `src/ui/`

**Primary Responsibility**: Present information and capture user input.

**Key Principles**:
- UI components should not contain business logic
- UI should only interact with the Application Layer, never directly with Core or Data
- Components should be reusable where possible

**Sub-components**:
- `app_factory.py`: App setup and entry point
- `wizard/`: Strategy configuration wizard layout and logic
- `layouts/`: Other page layout components (e.g., results display)
- `components/`: Reusable UI elements (cards, tooltips, etc.)
- `callbacks/`: UI event handlers registration

### 2. Application Layer

**Location**: `src/services/`

**Primary Responsibility**: Orchestrate workflow between UI and business logic.

**Key Principles**:
- Services should be stateless when possible
- Coordinate operations between UI, Core Logic, and Data access
- Handle user interactions received from UI callbacks
- Interface with Core components but not implement business logic itself

**Key Services**:
- `BacktestService`: Primary service that coordinates backtesting operations
- `DataService`: Manages data retrieval and transformation
- `VisualizationService`: Prepares data for visualization

### 3. Core Logic Layer

**Location**: `src/core/`

**Primary Responsibility**: Implement the primary business logic of the application.

**Key Principles**:
- Should not depend on UI or Application layers
- Implement core domain logic without knowledge of presentation concerns
- Focus on single-responsibility principle

**Key Components**:
- `BacktestManager`: Manages the backtest execution process
- `Engine`: Core backtest execution logic
- `Config`: Application configuration

### 4. Strategy Layer

**Location**: `src/strategies/`

**Primary Responsibility**: Implement trading strategies and signal generation.

**Key Principles**:
- Strategies should implement a common interface
- Strategy implementation should be independent of UI and visualization concerns
- Each strategy should be testable in isolation

**Components**:
- `base.py`: Base strategy class with common interface
- Individual strategies (MA, RSI, etc.)
- `validator.py`: Strategy parameter validation logic

### 5. Portfolio Management Layer

**Location**: `src/portfolio/`

**Primary Responsibility**: Manage portfolio state, positions, and risk controls.

**Key Principles**:
- Clear separation between portfolio tracking and risk management
- Portfolio operations should be atomic and well-defined
- Risk management should be configurable and independent

**Components**:
- `PortfolioManager`: Track positions and calculate performance
- `RiskManager`: Apply risk controls to trading decisions

### 6. Data Layer

**Location**: `src/core/data/` (formerly `src/data/`)

**Primary Responsibility**: Data access, transformation, and caching.

**Key Principles**:
- Abstract data sources to enable switching sources without affecting business logic
- Manage data caching and optimization
- Handle data preparation for both backtest execution and visualization

### 7. Visualization Layer

**Location**: `src/visualization/`

**Primary Responsibility**: Create graphical representations of backtest results.

**Key Principles**:
- Visualization should be separated from data processing
- Components should be reusable across different parts of the application
- Optimize for performance with large datasets

## Communication Flow

The communication between components should follow these rules:

1. **UI Layer** → **Application Layer**:
   - UI components trigger callbacks that invoke service methods
   - UI never skips directly to core or data layers

2. **Application Layer** → **Core/Strategy/Portfolio Layers**:
   - Services coordinate requests between these layers
   - Services apply transformations needed for cross-layer communication

3. **Core/Strategy/Portfolio Layers** → **Data Layer**:
   - Business logic requests data through data layer abstractions
   - Business logic should not directly handle file I/O or external APIs

4. **Application Layer** → **Visualization Layer**:
   - Services prepare data for visualization
   - Visualization components are provided with ready-to-render data

## File Structure

```
src/
  ├── analysis/         # Analysis utilities and performance metrics
  ├── core/             # Core business logic and data access
  │   ├── data/         # Data loader and transformer
  │   │   ├── data.py    # Data loading operations
  │   │   └── ...
  │   ├── engine.py     # Backtest execution engine
  │   ├── config.py     # Configuration management
  │   ├── constants.py  # Application constants
  │   └── exceptions.py # Custom exception types
  ├── portfolio/        # Portfolio and position management
  │   ├── portfolio_manager.py # Portfolio tracking
  │   └── risk_manager.py      # Risk management
  ├── services/         # Application services layer
  │   ├── backtest_service.py # Main service for backtesting
  │   └── data_service.py     # Data access service
  ├── strategies/       # Trading strategies
  │   ├── base.py       # Base strategy class
  │   ├── moving_average.py # MA strategy implementation
  │   └── rsi.py        # RSI strategy implementation
  ├── ui/               # User interface components
  │   ├── app_factory.py      # Dash app creation and setup
  │   ├── components.py       # Common UI components (can be split further)
  │   ├── wizard/             # Strategy wizard layout and callbacks
  │   │   ├── layout.py
  │   │   └── ... wizard subpackage files
  │   ├── layouts/            # Page layout modules
  │   │   ├── results_display.py
  │   ├── callbacks/          # Dash callbacks for UI interactions
  │   │   ├── strategy_callbacks.py
  │   │   ├── wizard_callbacks.py
  │   │   ├── backtest_callbacks.py
  │   │   └── risk_management_callbacks.py
  ├── visualization/    # Data visualization
  │   ├── visualizer.py # Main visualization class
  │   └── chart_utils.py # Chart creation utilities
  └── version.py        # Version information
```

## Dependency Rules

To maintain a clean architecture, dependencies should flow in one direction:

```
UI → Application → (Core/Strategy/Portfolio) → Data
```

This means:
- UI components can depend on Application services, but not on Core, Strategy, or Data
- Application services can depend on Core, Strategy, Portfolio, and Data
- Core, Strategy, and Portfolio can depend on Data
- Lower layers NEVER depend on higher layers

## Testing Strategy

Each layer should be testable in isolation:

1. **UI Tests**: Test UI components with mocked Application services
2. **Service Tests**: Test Application services with mocked Core/Strategy/Portfolio
3. **Unit Tests**: Test Core/Strategy/Portfolio with mocked Data
4. **Integration Tests**: Test complete flows across layers

## Extension Points

The architecture is designed to be extended in the following areas:

1. **New Strategies**: Add new files to `src/strategies/` implementing the base strategy interface
2. **Data Sources**: Extend the Data layer with new source adapters
3. **Visualization**: Add new visualization components to `src/visualization/`
4. **Risk Management**: Extend risk management functionality in `src/portfolio/risk_manager.py`

## Guidelines for Common Changes

### Adding a New Strategy
1. Create a new file in `src/strategies/`
2. Implement the base strategy interface
3. Register the strategy in `src/core/constants.py`
4. Add any specific UI components needed for strategy configuration

### Changing Risk Management Features
1. Modify the `src/portfolio/risk_manager.py` to implement new risk logic
2. Update the UI component in `src/ui/layouts/risk_management.py`
3. Connect the UI to the risk manager via the application service

### Adding New Visualization Components
1. Create visualization functions in `src/visualization/chart_utils.py`
2. Update the visualizer class in `src/visualization/visualizer.py`
3. Create UI components that use the visualizer

### Modifying the Backtest Engine
1. Make changes to `src/core/engine.py`
2. Ensure the BacktestManager interface remains stable
3. Update tests to verify new behavior

## Version Control Recommendations

When making changes:
1. Group commits by architectural layer
2. Tag versions using SemVer after significant changes
3. Document API changes in commit messages

## References

- [Product Design Specification](product_design_specification.md)
- [Technical Specification](technical_specification.md)
*Last updated: April 24, 2025*