"""
Chart Helpers - Reusable Plotly chart generators for the dashboard.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


class ChartHelpers:
    """Static methods for generating dashboard charts."""

    # Color scheme
    COLORS = {
        "CRITICAL": "#DC2626",
        "HIGH": "#EA580C",
        "MEDIUM": "#D97706",
        "LOW": "#16A34A",
        "primary": "#1E40AF",
        "secondary": "#6B7280",
        "background": "#F9FAFB",
    }

    @staticmethod
    def health_gauge(score: int, title: str = "Project Health") -> go.Figure:
        """Create a gauge chart for health score.

        Args:
            score: Health score 0-100.
            title: Chart title.

        Returns:
            Plotly figure.
        """
        color = (
            "#DC2626" if score < 50
            else "#D97706" if score < 70
            else "#16A34A"
        )

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": title, "font": {"size": 16}},
            number={"suffix": "/100", "font": {"size": 28}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": color},
                "bgcolor": "white",
                "steps": [
                    {"range": [0, 50], "color": "#FEE2E2"},
                    {"range": [50, 70], "color": "#FEF3C7"},
                    {"range": [70, 100], "color": "#DCFCE7"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 2},
                    "thickness": 0.75,
                    "value": score,
                },
            },
        ))

        fig.update_layout(
            height=200,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        return fig

    @staticmethod
    def risk_heatmap(data: list[dict]) -> go.Figure:
        """Create a risk heatmap showing projects vs risk dimensions.

        Args:
            data: List of project risk records.

        Returns:
            Plotly figure.
        """
        if not data:
            return go.Figure().update_layout(
                title="No risk data available",
                height=300,
            )

        df = pd.DataFrame(data)

        # Create severity score for heatmap coloring
        severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

        fig = go.Figure(data=go.Heatmap(
            z=[
                df.get("DELAY_RISK_COUNT", pd.Series([0] * len(df))).tolist(),
                df.get("CONTRACT_RISK_COUNT", pd.Series([0] * len(df))).tolist(),
                (df.get("TOTAL_FINANCIAL_IMPACT", pd.Series([0] * len(df))) / 10000).tolist(),
            ],
            x=df.get("PROJECT_NAME", pd.Series([])).tolist(),
            y=["Delay Risk", "Contract Risk", "Financial Impact (×$10K)"],
            colorscale="RdYlGn_r",
            showscale=True,
            hovertemplate="Project: %{x}<br>Category: %{y}<br>Score: %{z}<extra></extra>",
        ))

        fig.update_layout(
            title="Project Risk Heatmap",
            height=350,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    @staticmethod
    def financial_exposure_bar(data: list[dict]) -> go.Figure:
        """Create a bar chart of financial exposure by project.

        Args:
            data: List of project risk records.

        Returns:
            Plotly figure.
        """
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)
        df = df.sort_values("TOTAL_FINANCIAL_IMPACT", ascending=True)

        colors = [
            ChartHelpers.COLORS.get(
                str(row.get("MAX_SEVERITY", "LOW")),
                ChartHelpers.COLORS["secondary"]
            )
            for _, row in df.iterrows()
        ]

        fig = go.Figure(go.Bar(
            x=df["TOTAL_FINANCIAL_IMPACT"],
            y=df["PROJECT_NAME"],
            orientation="h",
            marker_color=colors,
            text=df["TOTAL_FINANCIAL_IMPACT"].apply(lambda x: f"${x:,.0f}"),
            textposition="auto",
        ))

        fig.update_layout(
            title="Financial Exposure by Project",
            xaxis_title="Exposure ($)",
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=False,
        )
        return fig

    @staticmethod
    def vendor_risk_chart(data: list[dict]) -> go.Figure:
        """Create a scatter plot of vendor risk (delay days vs exposure).

        Args:
            data: List of vendor risk records.

        Returns:
            Plotly figure.
        """
        if not data:
            return go.Figure()

        df = pd.DataFrame(data)

        tier_colors = {
            "LOW": "#16A34A",
            "MEDIUM": "#D97706",
            "HIGH": "#EA580C",
            "CRITICAL": "#DC2626",
        }

        fig = px.scatter(
            df,
            x="TOTAL_DELAY_DAYS",
            y="TOTAL_EXPOSURE",
            size="ASSIGNED_TASKS",
            color="RISK_TIER",
            color_discrete_map=tier_colors,
            hover_name="VENDOR_NAME",
            text="VENDOR_NAME",
            title="Vendor Risk Profile",
        )

        fig.update_traces(textposition="top center", textfont_size=9)
        fig.update_layout(
            xaxis_title="Total Delay Days",
            yaxis_title="Financial Exposure ($)",
            height=350,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    @staticmethod
    def severity_donut(risks: list[dict]) -> go.Figure:
        """Create a donut chart showing risk distribution by severity.

        Args:
            risks: List of risk signal records.

        Returns:
            Plotly figure.
        """
        if not risks:
            return go.Figure()

        df = pd.DataFrame(risks)
        severity_counts = df["SEVERITY"].value_counts()

        colors = [ChartHelpers.COLORS.get(s, "#6B7280") for s in severity_counts.index]

        fig = go.Figure(go.Pie(
            labels=severity_counts.index.tolist(),
            values=severity_counts.values.tolist(),
            hole=0.5,
            marker_colors=colors,
            textinfo="label+value",
        ))

        fig.update_layout(
            title="Risks by Severity",
            height=280,
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=True,
        )
        return fig

    @staticmethod
    def timeline_chart(tasks: list[dict]) -> go.Figure:
        """Create a Gantt-style timeline of tasks.

        Args:
            tasks: List of task records with dates.

        Returns:
            Plotly figure.
        """
        if not tasks:
            return go.Figure()

        df = pd.DataFrame(tasks)

        status_colors = {
            "COMPLETED": "#16A34A",
            "IN_PROGRESS": "#2563EB",
            "DELAYED": "#DC2626",
            "BLOCKED": "#7C3AED",
            "NOT_STARTED": "#9CA3AF",
        }

        fig = px.timeline(
            df,
            x_start="PLANNED_START",
            x_end="PLANNED_END",
            y="TASK_NAME",
            color="STATUS",
            color_discrete_map=status_colors,
            title="Task Timeline",
        )

        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig
