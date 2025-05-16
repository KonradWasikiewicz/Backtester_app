"""
This module defines the loading overlay component to be placed in the app's layout.
It will cover the entire main content area when a backtest is running.
"""
import dash_bootstrap_components as dbc
from dash import html, dcc  # Import dcc for Interval component
import logging

# Import centralized IDs
from src.ui.ids.ids import SharedComponentIDs, ResultsIDs

logger = logging.getLogger(__name__)

def create_loading_overlay():
    """
    Creates a loading overlay component that covers the entire app when visible.
    This component includes the progress bar and status messages for backtesting.
    The overlay is absolutely positioned, initially hidden (display: none), 
    and has z-index to appear above other components.
    """
    logger.debug("Creating global loading overlay.")
    return html.Div(
        id=SharedComponentIDs.LOADING_OVERLAY,  # Global loading overlay ID
        children=[
            # Status and progress elements
            html.Div([
                # Outer text: "Running backtest..." with animation and percentage
                html.Div(
                    id=ResultsIDs.BACKTEST_ANIMATED_TEXT,
                    children=["Running backtest...", html.Span(id="progress-bar-percentage-span", className="progress-bar-percentage")],
                    className="text-center mb-1 progress-bar-text",
                    style={
                        "fontSize": "var(--font-size-sm)",
                        "color": "white"
                    }
                ),
                # Container for the progress bar itself (for width control and collapse)
                html.Div(
                    className="w-100",
                    children=[
                        dbc.Collapse(
                            id=ResultsIDs.BACKTEST_PROGRESS_BAR_CONTAINER,
                            is_open=False,  # Initially hidden
                            className="w-100",
                            children=[
                                # Relative container for positioning the inner text
                                html.Div(
                                    style={"position": "relative", "height": "20px"},
                                    children=[
                                        dbc.Progress(
                                            id=ResultsIDs.BACKTEST_PROGRESS_BAR,
                                            value=0,
                                            striped=True,
                                            className="mb-3",
                                            style={"height": "20px"}
                                        ),
                                        # Inner text: Detailed progress message, overlaid on the bar
                                        html.Div(
                                            id=ResultsIDs.BACKTEST_PROGRESS_LABEL_TEXT,
                                            children="",  # Initial empty text
                                            className="progress-bar-text",
                                            style={
                                                "position": "absolute",
                                                "top": "50%",
                                                "left": "50%",
                                                "transform": "translate(-50%, -50%)",
                                                "color": "white",
                                                "whiteSpace": "nowrap",
                                                "overflow": "hidden",
                                                "textOverflow": "ellipsis",
                                                "maxWidth": "calc(100% - 20px)",
                                                "textAlign": "center",
                                                "zIndex": "10"
                                            }
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                ),
                dcc.Interval(
                    id=ResultsIDs.BACKTEST_ANIMATION_INTERVAL,
                    interval=300,  # Milliseconds
                    n_intervals=0,
                    disabled=True  # Initially disabled
                )
            ],
            id=SharedComponentIDs.STATUS_AND_PROGRESS_BAR_DIV,
            className="status-progress-container mb-3",
            style={"width": "60%"}  # Width of the progress elements inside overlay
            )
        ],        style={  # Style for the overlay
            "display": "none",  # Initially hidden
            "position": "fixed",  # Fixed position to cover entire viewport
            "top": "0",
            "left": "0",
            "right": "0",
            "bottom": "0",
            "backgroundColor": "rgba(18, 18, 18, 0.95)",  # Very dark, almost opaque background
            "zIndex": "1050",  # High z-index to be on top of other content
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center"
        }
    )
