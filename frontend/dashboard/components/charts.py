"""Standardized Plotly chart wrappers with consistent styling."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .styles import (
    CHART_LAYOUT,
    CHART_MARGIN_MAP,
    HEATMAP_SCALE,
    HISTORICAL_BLUE,
    FORECAST_PURPLE,
    LYFT_PINK,
    TEXT_PRIMARY,
    apply_layout,
)


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    color_map: dict | None = None,
    title: str = "",
    height: int = 400,
    **kwargs,
) -> go.Figure:
    labels = {x: "", y: y.replace("_", " ").title()}
    labels.update(kwargs.pop("labels", {}))
    fig = px.line(
        df, x=x, y=y, color=color,
        color_discrete_map=color_map,
        labels=labels,
        **kwargs,
    )
    return apply_layout(fig, height=height, title=title)


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    color_map: dict | None = None,
    orientation: str = "v",
    title: str = "",
    height: int = 400,
    **kwargs,
) -> go.Figure:
    fig = px.bar(
        df, x=x, y=y, color=color, orientation=orientation,
        color_discrete_map=color_map,
        **kwargs,
    )
    return apply_layout(fig, height=height, title=title)


def donut_chart(
    labels: list,
    values: list,
    colors: list,
    title: str = "",
    height: int = 360,
) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors),
        textinfo="percent+label", showlegend=False,
    ))
    return apply_layout(fig, height=height, title=title)


def dual_donut(
    labels1, values1, colors1, subtitle1,
    labels2, values2, colors2, subtitle2,
    height: int = 360,
) -> go.Figure:
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "domain"}]],
        subplot_titles=(subtitle1, subtitle2),
    )
    fig.add_trace(go.Pie(
        labels=labels1, values=values1, hole=0.55,
        marker=dict(colors=colors1), textinfo="percent+label", showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Pie(
        labels=labels2, values=values2, hole=0.55,
        marker=dict(colors=colors2), textinfo="percent+label", showlegend=False,
    ), row=1, col=2)
    return apply_layout(fig, height=height)


def scatter_map_chart(
    df: pd.DataFrame,
    lat: str = "lat",
    lon: str = "lon",
    size: str = "marker_size",
    color: str | None = None,
    hover_name: str = "station_name",
    color_map: dict | None = None,
    zoom: float = 10.5,
    center: tuple = (40.7306, -73.9866),
    height: int = 480,
    **kwargs,
) -> go.Figure:
    fig = px.scatter_map(
        df, lat=lat, lon=lon, size=size, color=color,
        hover_name=hover_name,
        color_discrete_map=color_map,
        zoom=zoom,
        center={"lat": center[0], "lon": center[1]},
        map_style="carto-positron",
        **kwargs,
    )
    fig.update_layout(
        height=height,
        margin=CHART_MARGIN_MAP,
        legend_title_text="",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def forecast_chart(
    historical_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    hist_x: str = "date",
    hist_y: str = "trips",
    fc_x: str = "date",
    fc_y: str = "forecast",
    lower: str = "lower",
    upper: str = "upper",
    title: str = "",
    height: int = 420,
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=historical_df[hist_x], y=historical_df[hist_y],
        name="Historical", line=dict(color="#94A3B8", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df[fc_x], forecast_df[fc_x][::-1]]),
        y=pd.concat([forecast_df[upper], forecast_df[lower][::-1]]),
        fill="toself", fillcolor=f"rgba(124,58,237,.12)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip", name="Confidence band",
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df[fc_x], y=forecast_df[fc_y],
        name="Forecast", line=dict(color=FORECAST_PURPLE, width=3),
    ))
    return apply_layout(fig, height=height, title=title, xaxis_title="", yaxis_title="Trips")


def heatmap(
    z, x_labels, y_labels,
    title: str = "",
    height: int = 500,
    show_rush_hours: bool = True,
) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=z, x=x_labels, y=y_labels,
        colorscale=HEATMAP_SCALE, xgap=2, ygap=2,
        colorbar=dict(
            title=dict(text="Avg Hourly Trips", font=dict(color=HISTORICAL_BLUE)),
            tickfont=dict(color=HISTORICAL_BLUE),
        ),
        hovertemplate="%{x}, %{y}:00<br>%{z:,.0f} avg trips<extra></extra>",
    ))
    if show_rush_hours:
        # Weekdays and weekends peak at different times of day, so shade/mark
        # each block separately: weekday commute rush vs. weekend
        # mid-afternoon peak.
        weekday_labels = [d for d in x_labels if d not in ("Saturday", "Sunday")]
        weekend_labels = [d for d in x_labels if d in ("Saturday", "Sunday")]
        weekday_x1 = len(weekday_labels) - 0.5
        weekend_x0 = weekday_x1
        weekend_x1 = len(x_labels) - 0.5

        peak_bands = []
        if weekday_labels:
            peak_bands.append((-0.5, weekday_x1, 6.5, 9.5))
            peak_bands.append((-0.5, weekday_x1, 16.5, 19.5))
        if weekend_labels:
            peak_bands.append((weekend_x0, weekend_x1, 12.5, 15.5))

        for x0, x1, y0, y1 in peak_bands:
            fig.add_shape(
                type="rect", xref="x", yref="y",
                x0=x0, x1=x1, y0=y0, y1=y1,
                fillcolor=LYFT_PINK, opacity=0.15, line_width=0, layer="above",
            )
            for y in (y0, y1):
                fig.add_shape(
                    type="line", xref="x", yref="y",
                    x0=x0, x1=x1, y0=y, y1=y,
                    line=dict(color=LYFT_PINK, dash="dash", width=2.5),
                    opacity=0.9,
                )

        if weekday_labels and weekend_labels:
            fig.add_shape(
                type="line", xref="x", yref="paper",
                x0=weekday_x1, x1=weekday_x1, y0=0, y1=1,
                line=dict(color=HISTORICAL_BLUE, width=2),
            )

        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="lines",
            line=dict(color=LYFT_PINK, dash="dash", width=2.5),
            name="Peak Hours",
        ))
    fig.update_yaxes(
        title="Hour of day", autorange="reversed",
        tickmode="array", tickvals=list(range(0, 24, 2)),
        tickfont=dict(color=HISTORICAL_BLUE), showgrid=False,
    )
    fig.update_xaxes(tickfont=dict(color=HISTORICAL_BLUE))
    return apply_layout(
        fig, height=height, title=title,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=show_rush_hours,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(color=HISTORICAL_BLUE)),
    )


def opportunity_scatter(
    df: pd.DataFrame,
    x: str = "mta_daily_riders",
    y: str = "bike_daily_trips",
    size: str = "transit_opportunity_score",
    color: str = "transit_opportunity_score",
    hover_name: str = "neighborhood",
    title: str = "",
    height: int = 440,
) -> go.Figure:
    fig = px.scatter(
        df, x=x, y=y, size=size, color=color,
        hover_name=hover_name,
        hover_data={
            "station_name": True,
            "mta_daily_riders": ":,.0f",
            "mta_delay_rate": ":.1%",
            "bike_daily_trips": ":,.0f",
            "transit_opportunity_score": ":.1f",
        },
        color_continuous_scale=["#CBD5E1", "#2D7FF9", "#0B1324"],
        labels={
            "mta_daily_riders": "MTA daily riders",
            "bike_daily_trips": "Citi Bike daily trips",
            "transit_opportunity_score": "Opportunity",
        },
    )
    return apply_layout(fig, height=height, title=title)
