"""
Centralized ID management for Dash components.
This file serves as the single source of truth for all component IDs,
preventing conflicts and making refactoring easier.
"""

class WizardIDs:
    """IDs for components in the wizard interface."""
    
    # Step 1: Initial Capital & Strategy
    INITIAL_CAPITAL_INPUT = "wizard-initial-capital-input"
    STRATEGY_DROPDOWN = "wizard-strategy-dropdown"
    STRATEGY_DESCRIPTION_OUTPUT = "wizard-strategy-description-output"
    STRATEGY_PARAM_INPUTS_CONTAINER = "wizard-strategy-param-inputs"
    CONFIRM_STRATEGY_BUTTON = "wizard-confirm-strategy"
    
    # Wizard Progress & Main Containers
    PROGRESS_BAR = "wizard-progress"
    STEPS_CONTAINER = "wizard-steps-container"
    STRATEGY_CONFIG_CONTAINER = "strategy-config-container"
    
    # Step Headers and Contents (by pattern)
    @staticmethod
    def step_header(step_id):
        """Generate ID for a step header."""
        return f"{step_id}-header"
    
    @staticmethod
    def step_content(step_id):
        """Generate ID for step content."""
        return f"{step_id}-content"
    
    # Step 2: Date Range
    DATE_RANGE_START_PICKER = "wizard-date-start-picker"
    DATE_RANGE_END_PICKER = "wizard-date-end-picker"
    CONFIRM_DATES_BUTTON = "wizard-confirm-dates-button"
    
    # Step 3: Ticker Selection
    TICKER_SELECTION_CONTAINER = "wizard-ticker-selection"
    TICKER_DROPDOWN = "wizard-ticker-dropdown"
    TICKER_LIST_CONTAINER = "wizard-selected-tickers"
    CONFIRM_TICKERS_BUTTON = "wizard-confirm-tickers-button"
    
    # Step 4: Risk Management
    RISK_MANAGEMENT_CONTAINER = "wizard-risk-management"
    MAX_DRAWDOWN_INPUT = "wizard-max-drawdown-input"
    STOP_LOSS_INPUT = "wizard-stop-loss-input"
    TAKE_PROFIT_INPUT = "wizard-take-profit-input"
    CONFIRM_RISK_BUTTON = "wizard-confirm-risk-button"
    
    # Step 5: Trading Costs
    TRADING_COSTS_CONTAINER = "wizard-trading-costs"
    COMMISSION_INPUT = "wizard-commission-input"
    SLIPPAGE_INPUT = "wizard-slippage-input"
    CONFIRM_COSTS_BUTTON = "wizard-confirm-costs-button"
    
    # Step 6: Rebalancing
    REBALANCING_CONTAINER = "wizard-rebalancing"
    REBALANCING_FREQUENCY_DROPDOWN = "wizard-rebalancing-frequency"
    REBALANCING_THRESHOLD_INPUT = "wizard-rebalancing-threshold"
    CONFIRM_REBALANCING_BUTTON = "wizard-confirm-rebalancing-button"
    
    # Step 7: Summary & Run
    SUMMARY_CONTAINER = "wizard-summary"
    SUMMARY_STRATEGY_NAME = "wizard-summary-strategy-name"
    SUMMARY_INITIAL_CAPITAL = "wizard-summary-initial-capital"
    SUMMARY_OUTPUT_CONTAINER = "wizard-summary-output"
    RUN_BACKTEST_BUTTON_WIZARD = "wizard-run-backtest-button"


class LayoutIDs:
    """IDs for main layout components."""
    
    MAIN_CONTAINER = "main-content-container"
    SIDEBAR = "sidebar"
    CONTENT_AREA = "content-area"
    TAB_CONTAINER = "tabs-container"


class ResultsIDs:
    """IDs for results display components."""
    
    RESULTS_CONTAINER = "results-container"
    PERFORMANCE_METRICS_TABLE = "performance-metrics-table"
    EQUITY_CURVE_GRAPH = "equity-curve-graph"
    DRAWDOWN_GRAPH = "drawdown-graph"
    MONTHLY_RETURNS_HEATMAP = "monthly-returns-heatmap"
    TRADES_TABLE = "trades-table"


class StrategyConfigIDs:
    """IDs for strategy configuration components outside the wizard."""
    
    CONFIG_CONTAINER = "strategy-config-container-main"
    STRATEGY_SELECTOR = "strategy-selector-main"
    PARAMS_CONTAINER = "strategy-params-container"