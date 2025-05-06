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
    SELECT_ALL_TICKERS_BUTTON = "wizard-select-all-tickers-button"
    DESELECT_ALL_TICKERS_BUTTON = "wizard-deselect-all-tickers-button"
    
    # Step 4: Risk Management
    RISK_MANAGEMENT_CONTAINER = "wizard-risk-management"
    RISK_FEATURES_CHECKLIST = "wizard-risk-features-checklist"
    MAX_POSITION_SIZE_INPUT = "wizard-max-position-size-input"
    STOP_LOSS_TYPE_SELECT = "wizard-stop-loss-type-select"
    STOP_LOSS_INPUT = "wizard-stop-loss-input" # Existing, intended for stop loss value
    TAKE_PROFIT_TYPE_SELECT = "wizard-take-profit-type-select"
    TAKE_PROFIT_INPUT = "wizard-take-profit-input" # Existing, intended for take profit value
    MAX_RISK_PER_TRADE_INPUT = "wizard-max-risk-per-trade-input"
    MARKET_TREND_LOOKBACK_INPUT = "wizard-market-trend-lookback-input"
    MAX_DRAWDOWN_INPUT = "wizard-max-drawdown-input" # Existing
    MAX_DAILY_LOSS_INPUT = "wizard-max-daily-loss-input"
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

    # Store
    BACKTEST_RESULTS_STORE = "backtest-results-store"

    # Buttons
    PORTFOLIO_VALUE_BUTTON = "btn-chart-value"
    PORTFOLIO_RETURNS_BUTTON = "btn-chart-returns"

    # Charts & Their Loaders
    PORTFOLIO_CHART = "portfolio-chart"
    PORTFOLIO_CHART_LOADING = "portfolio-chart-loading"

    DRAWDOWN_CHART = "drawdown-chart"
    DRAWDOWN_CHART_LOADING = "drawdown-chart-loading"

    MONTHLY_RETURNS_HEATMAP = "monthly-returns-heatmap"
    MONTHLY_RETURNS_HEATMAP_LOADING = "heatmap-chart-loading" # as per layout

    SIGNALS_CHART = "signals-chart"
    SIGNALS_CHART_LOADING = "signals-chart-loading"
    SIGNALS_TICKER_SELECTOR = "ticker-selector" # For signals chart

    # Tables & Their Loaders/Containers
    TRADES_TABLE_CONTAINER = "trades-table-container"
    TRADES_TABLE_LOADING = "trades-table-loading"

    # Metrics Containers
    PERFORMANCE_METRICS_CONTAINER = "performance-metrics-container"
    TRADE_METRICS_CONTAINER = "trade-metrics-container"

    # Status and Progress
    BACKTEST_STATUS_MESSAGE = "backtest-status"
    BACKTEST_PROGRESS_BAR = "backtesting_progress_bar"
    BACKTEST_PROGRESS_BAR_CONTAINER = "backtesting_progress_bar_container"

    # Layout Wrappers / Areas
    RESULTS_AREA_WRAPPER = "actual-results-area" # The div that's initially hidden

    # These might be better in LayoutIDs if they define major page structure columns
    # For now, keeping them here as they are directly related to results visibility in callbacks
    CENTER_PANEL_COLUMN = "center-panel-col"
    RIGHT_PANEL_COLUMN = "right-panel-col"


class StrategyConfigIDs:
    """IDs for strategy configuration components outside the wizard."""
    
    CONFIG_CONTAINER = "strategy-config-container-main"
    STRATEGY_SELECTOR = "strategy-selector-main"
    PARAMS_CONTAINER = "strategy-params-container"