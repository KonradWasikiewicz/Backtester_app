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
    STEPS_CONTAINER = "wizard-steps-container"
    STRATEGY_CONFIG_CONTAINER = "strategy-config-container"
    WIZARD_STEPPER = "wizard-stepper"
    PROGRESS_BAR = "wizard-progress-bar"
    PROGRESS_CONTAINER = "wizard-progress-container" # ADDED
      # Summary section IDs
    SUMMARY_STRATEGY_DETAILS = "summary-strategy-details"
    SUMMARY_STRATEGY_PARAMETERS = "summary-strategy-parameters"
    SUMMARY_DATES_DETAILS = "summary-dates-details"
    SUMMARY_TICKERS_DETAILS = "summary-tickers-details"
    SUMMARY_RISK_DETAILS = "summary-risk-details"
    SUMMARY_COSTS_DETAILS = "summary-costs-details"
    SUMMARY_REBALANCING_DETAILS = "summary-rebalancing-details"
    SUMMARY_OUTPUT_CONTAINER = "summary-output-container"
    
    # Store IDs
    RISK_MANAGEMENT_STORE_WIZARD = "risk-management-store-wizard"
    STRATEGY_PARAMS_STORE = "strategy-params-store"
    
    # Stepper Component IDs (NEW)
    @staticmethod
    def step_indicator(step_number):
        """Generate ID for a step indicator in the stepper."""
        return f"step-indicator-{step_number}"
    
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
    # RISK_MANAGEMENT_CONTAINER = "wizard-risk-management" # Unused
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

    # Risk Management Panels (NEW)
    RISK_PANEL_POSITION_SIZING = "wizard-risk-panel-position-sizing"
    RISK_PANEL_STOP_LOSS = "wizard-risk-panel-stop-loss"
    RISK_PANEL_TAKE_PROFIT = "wizard-risk-panel-take-profit"
    RISK_PANEL_RISK_PER_TRADE = "wizard-risk-panel-risk-per-trade"
    RISK_PANEL_MARKET_FILTER = "wizard-risk-panel-market-filter"
    RISK_PANEL_DRAWDOWN_PROTECTION = "wizard-risk-panel-drawdown-protection"
    
    # Step 5: Trading Costs
    # TRADING_COSTS_CONTAINER = "wizard-trading-costs" # Unused
    COMMISSION_INPUT = "wizard-commission-input"
    SLIPPAGE_INPUT = "wizard-slippage-input"
    CONFIRM_COSTS_BUTTON = "wizard-confirm-costs-button"
    
    # Step 6: Rebalancing
    # REBALANCING_CONTAINER = "wizard-rebalancing" # Unused
    REBALANCING_FREQUENCY_DROPDOWN = "wizard-rebalancing-frequency"
    REBALANCING_THRESHOLD_INPUT = "wizard-rebalancing-threshold"
    CONFIRM_REBALANCING_BUTTON = "confirm-rebalancing-button"
    RUN_BACKTEST_BUTTON_WIZARD = "run-backtest-button-wizard"
    RUN_BACKTEST_ERROR_MESSAGE = "run-backtest-error-message" # ADDED

    # Stores for wizard state
    ACTIVE_STEP_STORE = "active-step-store"
    CONFIRMED_STEPS_STORE = "wizard-confirmed-steps-store"
    ALL_STEPS_COMPLETED_STORE = "wizard-all-steps-completed-store"


class ResultsIDs:
    """IDs for results display components."""

    # Store
    BACKTEST_RESULTS_STORE = "backtest-results-store"

    # Buttons
    PORTFOLIO_VALUE_BUTTON = "btn-chart-value"
    PORTFOLIO_RETURNS_BUTTON = "btn-chart-returns"
    # ADDED NEW IDs for currency/percentage toggle
    PORTFOLIO_VALUE_CURRENCY_USD = "portfolio-value-currency-usd" # UNCOMMENTED
    PORTFOLIO_VALUE_CURRENCY_PERCENT = "portfolio-value-currency-percent" # UNCOMMENTED

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
    TRADES_TABLE_CONTAINER = "trades-table-container" # UNCOMMENTED
    TRADES_TABLE_LOADING = "trades-table-loading" # UNCOMMENTED

    # Metrics Containers
    PERFORMANCE_METRICS_CONTAINER = "performance-metrics-container" # UNCOMMENTED
    TRADE_METRICS_CONTAINER = "trade-metrics-container" # UNCOMMENTED

    # Status and Progress
    BACKTEST_STATUS_MESSAGE = "backtest-status"
    BACKTEST_PROGRESS_BAR = "backtesting_progress_bar"
    BACKTEST_PROGRESS_BAR_CONTAINER = "backtesting_progress_bar_container"
    BACKTEST_PROGRESS_LABEL_TEXT = "backtest-progress-label-text"
    BACKTEST_ANIMATED_TEXT = "backtest-animated-text"
    BACKTEST_PROGRESS_DETAIL_TEXT = "backtest-progress-detail-text"
    BACKTEST_ANIMATION_INTERVAL = "backtest-animation-interval"

    # Layout Wrappers / Areas
    RESULTS_AREA_WRAPPER = "actual-results-area" # UNCOMMENTED

    # These might be better in LayoutIDs if they define major page structure columns
    # For now, keeping them here as they are directly related to results visibility in callbacks
    CENTER_PANEL_COLUMN = "center-panel-col" # UNCOMMENTED
    RIGHT_PANEL_COLUMN = "right-panel-col" # UNCOMMENTED


class StrategyConfigIDs:
    """IDs for strategy configuration components outside the wizard (main page)."""
    
    CONFIG_CONTAINER = "strategy-config-container-main"
    STRATEGY_SELECTOR = "strategy-selector-main" # Main strategy dropdown
    PARAMS_CONTAINER = "strategy-params-container-main" # Main strategy parameters container
    
    # Basic Config
    INITIAL_CAPITAL_INPUT_MAIN = "initial-capital-input-main"
    TICKER_INPUT_MAIN = "ticker-input-main"
    START_DATE_PICKER_MAIN = "backtest-start-date-main"
    END_DATE_PICKER_MAIN = "backtest-end-date-main"
    
    # Run Button
    RUN_BACKTEST_BUTTON_MAIN = "run-backtest-button-main"
    
    # Risk Management (Main Page)
    RISK_FEATURES_CHECKLIST_MAIN = "risk-features-checklist-main"
    MAX_POSITION_SIZE_INPUT_MAIN = "max-position-size-main"
    STOP_LOSS_TYPE_SELECT_MAIN = "stop-loss-type-main"
    STOP_LOSS_INPUT_MAIN = "stop-loss-value-main" # Input for stop loss value
    TAKE_PROFIT_TYPE_SELECT_MAIN = "take-profit-type-main"
    TAKE_PROFIT_INPUT_MAIN = "take-profit-value-main" # Input for take profit value
    MAX_RISK_PER_TRADE_INPUT_MAIN = "max-risk-per-trade-main"
    MARKET_TREND_LOOKBACK_INPUT_MAIN = "market-trend-lookback-main"
    MAX_DRAWDOWN_INPUT_MAIN = "max-drawdown-main"
    MAX_DAILY_LOSS_INPUT_MAIN = "max-daily-loss-main"
    
    # Trading Costs (Main Page)
    COMMISSION_INPUT_MAIN = "commission-input-main"
    SLIPPAGE_INPUT_MAIN = "slippage-input-main"
    
    # Rebalancing (Main Page)
    REBALANCING_FREQUENCY_DROPDOWN_MAIN = "rebalancing-frequency-main"
    REBALANCING_THRESHOLD_INPUT_MAIN = "rebalancing-threshold-main"

    # Store for configuration if used by main page components
    STRATEGY_CONFIG_STORE_MAIN = "strategy-config-store-main" # Distinct from wizard's potential store

    # IDs from src/ui/layouts/risk_management.py, potentially for a non-wizard main page context
    RISK_FEATURES_CHECKLIST_ALT = "risk-features-checklist" # WizardIDs.RISK_FEATURES_CHECKLIST exists
    POSITION_SIZING_PANEL_ALT = "position_sizing-panel"
    STOP_LOSS_PANEL_ALT = "stop_loss-panel"
    TAKE_PROFIT_PANEL_ALT = "take_profit-panel"
    RISK_PER_TRADE_PANEL_ALT = "risk_per_trade-panel"
    MARKET_FILTER_PANEL_ALT = "market_filter-panel"
    DRAWDOWN_PROTECTION_PANEL_ALT = "drawdown_protection-panel"

    POSITION_SIZING_CHECKBOX_ALT = "position_sizing-checkbox"
    STOP_LOSS_CHECKBOX_ALT = "stop_loss-checkbox"
    TAKE_PROFIT_CHECKBOX_ALT = "take_profit-checkbox"
    RISK_PER_TRADE_CHECKBOX_ALT = "risk_per_trade-checkbox"
    MARKET_FILTER_CHECKBOX_ALT = "market_filter-checkbox"
    DRAWDOWN_PROTECTION_CHECKBOX_ALT = "drawdown_protection-checkbox"
    CONTINUE_ITERATE_CHECKBOX_ALT = "continue-iterate-checkbox"

    RISK_MANAGEMENT_STORE_ALT = "risk-management-store" # WizardIDs.RISK_MANAGEMENT_STORE_WIZARD exists

    # Inputs from src/ui/layouts/risk_management.py (alternative context)
    MAX_POSITION_SIZE_ALT = "max-position-size" # WizardIDs.MAX_POSITION_SIZE_INPUT exists
    MAX_PORTFOLIO_RISK_ALT = "max-portfolio-risk"
    STOP_LOSS_TYPE_ALT = "stop-loss-type" # WizardIDs.STOP_LOSS_TYPE_SELECT exists
    STOP_LOSS_VALUE_ALT = "stop-loss-value" # WizardIDs.STOP_LOSS_INPUT exists
    TAKE_PROFIT_TYPE_ALT = "take-profit-type" # WizardIDs.TAKE_PROFIT_TYPE_SELECT exists
    TAKE_PROFIT_VALUE_ALT = "take-profit-value" # WizardIDs.TAKE_PROFIT_INPUT exists
    MAX_RISK_PER_TRADE_ALT = "max-risk-per-trade" # WizardIDs.MAX_RISK_PER_TRADE_INPUT exists
    RISK_REWARD_RATIO_ALT = "risk-reward-ratio"
    MARKET_TREND_LOOKBACK_ALT = "market-trend-lookback" # WizardIDs.MARKET_TREND_LOOKBACK_INPUT exists
    MAX_DRAWDOWN_ALT = "max-drawdown" # WizardIDs.MAX_DRAWDOWN_INPUT exists
    MAX_DAILY_LOSS_ALT = "max-daily-loss" # WizardIDs.MAX_DAILY_LOSS_INPUT exists

    # IDs from src/ui/layouts/strategy_config.py (non-wizard parts, e.g. old main page elements)
    TICKER_INPUT_LEGACY = "ticker-input" # WizardIDs.TICKER_DROPDOWN and StrategyConfigIDs.TICKER_INPUT_MAIN exist
    BACKTEST_START_DATE_LEGACY = "backtest-start-date" # WizardIDs.DATE_RANGE_START_PICKER and StrategyConfigIDs.START_DATE_PICKER_MAIN exist
    BACKTEST_END_DATE_LEGACY = "backtest-end-date" # WizardIDs.DATE_RANGE_END_PICKER and StrategyConfigIDs.END_DATE_PICKER_MAIN exist


class SharedComponentIDs:
    """IDs for components shared or used across different UI modules."""
    LOADING_OVERLAY = "loading-overlay"
    RUN_BACKTEST_TRIGGER_STORE = "run-backtest-trigger-store"
    STATUS_AND_PROGRESS_BAR_DIV = "status-and-progress-bar-div"


class AppStructureIDs:
    """IDs for main application structural elements, modals, and global stores."""
    APP_STATE_STORE = "app-state"

    # Main layout columns
    LEFT_PANEL_COL = "left-panel-col"

    # Modals
    CHANGELOG_MODAL = "changelog-modal"
    CHANGELOG_CONTENT = "changelog-content"
    CHANGELOG_CLOSE_BUTTON = "close-changelog"

    IMPORT_TICKERS_MODAL = "import-tickers-modal"
    IMPORT_TICKERS_TEXT_INPUT = "import-tickers-text"
    IMPORT_TICKERS_SUBMIT_BUTTON = "import-tickers-submit"
    IMPORT_TICKERS_FILE_UPLOAD = "import-tickers-file"
    IMPORT_TICKERS_FILE_OUTPUT = "import-tickers-file-output"
    IMPORT_TICKERS_CLOSE_BUTTON = "import-tickers-close"

    # Other UI elements
    VERSION_BADGE = "version-badge"
    FOOTER_VERSION_LINK = "footer-version"