import plotly.graph_objs as go

CHART_THEME = {
    'paper_bgcolor': '#1e222d',
    'plot_bgcolor': '#1e222d',
    'font': {'color': '#e1e1e1'}
}

def get_base_layout(title):
    """Create base layout for charts"""
    return go.Layout(
        title=title,
        template="plotly_dark",
        hovermode='x unified',
        xaxis={
            "showgrid": True,
            "gridwidth": 1,
            "gridcolor": '#2a2e39'
        },
        yaxis={
            "showgrid": True,
            "gridwidth": 1,
            "gridcolor": '#2a2e39'
        },
        margin=dict(l=40, r=40, t=40, b=40),
        **CHART_THEME
    )

def create_empty_chart(title):
    """Create an empty chart with message"""
    layout = go.Layout(
        title=title,
        template="plotly_dark",
        annotations=[{
            "text": "No data available",
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 20}
        }],
        **CHART_THEME
    )
    return go.Figure(data=[], layout=layout)

def create_equity_curve(results):
    """Create equity curve chart"""
    trace = go.Scatter(
        x=results.index,
        y=results["Portfolio_Value"],
        mode="lines",
        name="Portfolio Value",
        line=dict(color="#17B897")
    )
    layout = get_base_layout("Equity Curve")
    return go.Figure(data=[trace], layout=layout)
