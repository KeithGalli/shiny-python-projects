from pathlib import Path
import pandas as pd
import numpy as np
import seaborn as sns
import calendar

import altair as alt

import folium
from folium.plugins import HeatMap

import matplotlib.pyplot as plt

import plotly.express as px
from shiny import reactive
from shiny.express import render, input, ui
from shinywidgets import render_plotly, render_altair, render_widget

ui.tags.style(
    """
    .header-container {
        display: flex;
        align-items: center;
        justify-content: center; /* Centers the content horizontally */
        height: 60px;
    }

    .logo-container {
        margin-right: 5px; /* Adjust the spacing as needed */
        height: 100% !important;
        padding: 10px;
    }

    .logo-container img {
        height: 40px;
    }

    .title-container h2 {
        color: white;
        padding: 5px;
        margin: 0;
    }

    body {
        background-color: #5DADE2;
    }

    .modebar{
        display: none;
    }
    """
)

FONT_COLOR = "#4C78A8"
FONT_TYPE = "Arial"


def style_plotly_chart(fig, yaxis_title):
    fig.update_layout(
        xaxis_title="",  # Remove x-axis label
        yaxis_title=yaxis_title,  # Change y-axis label
        plot_bgcolor="rgba(0,0,0,0)",  # Remove background color
        showlegend=False,  # Remove the legend
        coloraxis_showscale=False,
        font=dict(family="Arial", size=12, color=FONT_COLOR),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


ui.page_opts(window_title="Sales Dashboard - Video 5 of 5", fillable=False)


@reactive.calc
def dat():
    infile = Path(__file__).parent / "data/sales.csv"
    df = pd.read_csv(infile)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.month_name()
    df["hour"] = df["order_date"].dt.hour
    df["value"] = df["quantity_ordered"] * df["price_each"]
    return df


with ui.div(class_="header-container"):
    with ui.div(class_="logo-container"):

        @render.image
        def image():
            here = Path(__file__).parent
            img = {"src": here / "images/shiny-logo.png"}
            return img

    with ui.div(class_="title-container"):
        ui.h2("Sales Dashboard - Video 5 of 5")

with ui.card():
    ui.card_header("Sales by City 2023")

    with ui.layout_sidebar():
        with ui.sidebar(bg="#f8f8f8", open="open"):
            ui.input_selectize(
                "city",
                "Select a City:",
                [
                    "Dallas (TX)",
                    "Boston (MA)",
                    "Los Angeles (CA)",
                    "San Francisco (CA)",
                    "Seattle (WA)",
                    "Atlanta (GA)",
                    "New York City (NY)",
                    "Portland (OR)",
                    "Austin (TX)",
                    "Portland (ME)",
                ],
                multiple=False,
                selected="Boston (MA)",
            )

        @render_widget
        def sales_over_time_altair():
            df = dat()
            # Group the data by city and month, then sum the quantities ordered
            sales = (
                df.groupby(["city", "month"])["quantity_ordered"].sum().reset_index()
            )

            # Filter the sales data to only include the selected city
            sales_by_city = sales[sales["city"] == input.city()]

            # Define the order of months
            month_orders = list(calendar.month_name)[1:]

            font_props = alt.Axis(
                labelFont="Arial",
                labelColor=FONT_COLOR,
                titleFont="Arial",
                titleColor=FONT_COLOR,
                tickSize=0,
                labelAngle=0,
            )
            # Create the bar chart
            chart = (
                alt.Chart(sales_by_city)
                .mark_bar(color="#3485BF")
                .encode(
                    x=alt.X("month", sort=month_orders, title="Month", axis=font_props),
                    y=alt.Y(
                        "quantity_ordered", title="Quantity Ordered", axis=font_props
                    ),
                    tooltip=["month", "quantity_ordered"],
                )
                .properties(title=alt.Title(f"Sales over Time -- {input.city()}"))
                .configure_axis(grid=False)
                .configure_title(font="Arial", color=FONT_COLOR)
            )

            return chart


with ui.layout_column_wrap(width=1 / 2):
    with ui.navset_card_underline(
        id="tab", footer=ui.input_numeric("n", "Number of Items", 5, min=0, max=20)
    ):
        with ui.nav_panel("Top Sellers"):

            @render_plotly
            def plot_top_sellers():
                df = dat()
                top_sales = (
                    df.groupby("product")["quantity_ordered"]
                    .sum()
                    .nlargest(input.n())
                    .reset_index()
                )

                # Create the bar chart
                fig = px.bar(
                    top_sales,
                    x="product",
                    y="quantity_ordered",
                    color="quantity_ordered",
                    color_continuous_scale="Blues",
                )

                # Apply the standardized style
                fig = style_plotly_chart(fig, "Quantity Ordered")

                return fig

        with ui.nav_panel("Top Sellers Value ($)"):

            @render_plotly
            def plot_top_sellers_value():
                df = dat()
                top_sales = (
                    df.groupby("product")["value"]
                    .sum()
                    .nlargest(input.n())
                    .reset_index()
                )
                # Create the bar chart
                fig = px.bar(
                    top_sales,
                    x="product",
                    y="value",
                    color="value",
                    color_continuous_scale="Blues",
                )

                # Apply the standardized style
                fig = style_plotly_chart(fig, "Total Sales ($)")
                return fig

        with ui.nav_panel("Lowest Sellers"):

            @render_plotly
            def plot_lowest_sellers():
                df = dat()
                top_sales = (
                    df.groupby("product")["quantity_ordered"]
                    .sum()
                    .nsmallest(input.n())
                    .reset_index()
                )
                # Create the bar chart
                fig = px.bar(
                    top_sales,
                    x="product",
                    y="quantity_ordered",
                    color="quantity_ordered",
                    color_continuous_scale="Reds",
                )

                # Apply the standardized style
                fig = style_plotly_chart(fig, "Quantity Ordered")
                return fig

        with ui.nav_panel("Lowest Sellers Value ($)"):

            @render_plotly
            def plot_lowest_sellers_value():
                df = dat()
                top_sales = (
                    df.groupby("product")["value"]
                    .sum()
                    .nsmallest(input.n())
                    .reset_index()
                )
                fig = px.bar(
                    top_sales,
                    x="product",
                    y="value",
                    color="value",
                    color_continuous_scale="Reds",
                )

                # Apply the standardized style
                fig = style_plotly_chart(fig, "Total Sales ($)")
                return fig

    with ui.card():
        ui.card_header("Sales by Time of Day Heatmap")

        @render.plot
        def plot_sales_by_time():
            df = dat()
            sales_by_hour = (
                df["hour"].value_counts().reindex(np.arange(0, 24), fill_value=0)
            )

            heatmap_data = sales_by_hour.values.reshape(24, 1)
            sns.heatmap(
                heatmap_data,
                annot=True,
                fmt="d",
                cmap="Blues",
                cbar=False,
                xticklabels=[],
                yticklabels=[f"{i}:00" for i in range(24)],
            )

            # plt.title("Number of Orders by Hour of Day")
            plt.xlabel("Order Count", color=FONT_COLOR, fontname=FONT_TYPE)
            plt.ylabel("Hour of Day", color=FONT_COLOR, fontname=FONT_TYPE)

            # Change the tick label color and font
            plt.yticks(color=FONT_COLOR, fontname=FONT_TYPE)
            plt.xticks(color=FONT_COLOR, fontname=FONT_TYPE)


with ui.card():
    ui.card_header("Sales by Location Map")

    @render.ui
    def plot_us_heatmap():
        df = dat()

        heatmap_data = df[["lat", "long", "quantity_ordered"]].values

        map = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
        # Define a blue gradient
        blue_gradient = {
            0.0: "#E3F2FD",
            0.2: "#BBDEFB",
            0.4: "#64B5F6",
            0.6: "#42A5F5",
            0.8: "#2196F3",
            1.0: "#1976D2",
        }

        # Add the heatmap layer with the blue gradient
        HeatMap(heatmap_data, gradient=blue_gradient).add_to(map)

        return map


with ui.card():
    ui.card_header("Sample Sales Data")

    @render.data_frame
    def sample_sales_data():
        return dat().head(1000)
