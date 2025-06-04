import plotly.graph_objects as go
from typing import Dict, Any, Union, List
import logging

try:
    from src.core.constants import VISUALIZATION_CONFIG as VIZ_CFG
except ImportError:
    logging.getLogger(__name__).warning(
        "Could not import VISUALIZATION_CONFIG. Using default visualization settings.")
    VIZ_CFG = {
        "chart_height": 400,
        "dark_theme": True,
        "template": "plotly_dark",
        "colors": {
            "portfolio": "#17B897",
            "benchmark": "#FF6B6B",
            "profit": "#28a745",
            "loss": "#dc3545",
            "primary": "#0d6efd",
            "secondary": "#6c757d",
            "background": "#131722",
            "card_background": "#1e222d",
            "grid_color": "#2a2e39",
            "text_color": "#dee2e6",
            "text_muted": "#6c757d",
        },
    }

CHART_TEMPLATE = VIZ_CFG.get("template", "plotly_dark")
PLOT_BGCOLOR = VIZ_CFG["colors"]["card_background"]
PAPER_BGCOLOR = VIZ_CFG["colors"]["background"]
GRID_COLOR = VIZ_CFG["colors"]["grid_color"]
TEXT_COLOR = VIZ_CFG["colors"]["text_color"]
DEFAULT_HEIGHT = VIZ_CFG.get("chart_height", 400)

logger = logging.getLogger(__name__)


def _create_base_layout(title: str = "", height: int = DEFAULT_HEIGHT, **kwargs) -> go.Layout:
    """Create a basic themed layout for charts."""
    layout = go.Layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=16, color=TEXT_COLOR)),
        height=height,
        template=CHART_TEMPLATE,
        paper_bgcolor=PAPER_BGCOLOR,
        plot_bgcolor=PLOT_BGCOLOR,
        font=dict(color=TEXT_COLOR, family="Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"),
        xaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zeroline=False, automargin=True),
        yaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zeroline=False, automargin=True),
        margin=dict(t=50, l=50, r=20, b=40),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=VIZ_CFG["colors"]["card_background"],
            bordercolor=GRID_COLOR,
            font=dict(color=TEXT_COLOR),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
        ),
    )
    layout.update(**kwargs)
    return layout


def add_shapes_to_chart(fig: go.Figure, shapes: List[Dict[str, Any]]) -> go.Figure:
    """Add shape annotations like lines or rectangles to a Plotly figure."""
    if not shapes:
        return fig

    for shape in shapes:
        shape_type = shape.get("type", "line")
        if shape_type == "line" and "line_color" not in shape:
            shape["line_color"] = VIZ_CFG["colors"]["primary"]
        elif "fillcolor" not in shape and shape_type in ["rect", "circle"]:
            shape["fillcolor"] = (
                f"rgba({int(VIZ_CFG['colors']['primary'][1:3], 16)},"
                f" {int(VIZ_CFG['colors']['primary'][3:5], 16)},"
                f" {int(VIZ_CFG['colors']['primary'][5:7], 16)}, 0.3)"
            )

        if "opacity" not in shape and shape_type in ["rect", "circle"]:
            shape["opacity"] = 0.3

        if "line" not in shape:
            shape["line"] = dict(
                color=shape.get("line_color", VIZ_CFG["colors"]["primary"]),
                width=shape.get("line_width", 1),
                dash=shape.get("line_dash", None),
            )

        fig.add_shape(
            type=shape_type,
            x0=shape.get("x0"),
            y0=shape.get("y0"),
            x1=shape.get("x1"),
            y1=shape.get("y1"),
            line=shape.get("line"),
            fillcolor=shape.get("fillcolor"),
            opacity=shape.get("opacity"),
            layer=shape.get("layer", "above"),
            name=shape.get("name", ""),
        )

        if shape.get("text"):
            fig.add_annotation(
                x=shape.get("x1", shape.get("x0")),
                y=shape.get("y1", shape.get("y0")),
                text=shape["text"],
                showarrow=shape.get("showarrow", False),
                arrowhead=shape.get("arrowhead", 1),
                arrowcolor=shape.get("arrowcolor", shape.get("line", {}).get("color", VIZ_CFG["colors"]["primary"])),
                ax=shape.get("ax", 0),
                ay=shape.get("ay", -40),
                font=dict(color=shape.get("text_color", TEXT_COLOR), size=shape.get("text_size", 12)),
                bgcolor=shape.get("text_bgcolor", "rgba(0,0,0,0.5)"),
                bordercolor=shape.get("text_bordercolor", "rgba(0,0,0,0)"),
                borderwidth=shape.get("text_borderwidth", 0),
                borderpad=shape.get("text_borderpad", 4),
            )
    return fig


def format_currency(value: Union[float, int]) -> str:
    """Return a numeric value formatted as US currency."""
    return f"${value:,.2f}" if value is not None else "$0.00"

__all__ = [
    "_create_base_layout",
    "add_shapes_to_chart",
    "format_currency",
]
