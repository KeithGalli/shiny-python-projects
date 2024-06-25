from pathlib import Path
import pandas as pd
import numpy as np
import calendar

import matplotlib.pyplot as plt

import altair as alt

import folium
from folium.plugins import HeatMap

import seaborn as sns

import plotly.express as px
from shiny import reactive
from shiny.express import render, input, ui
from shinywidgets import render_plotly, render_altair, render_widget

ui.page_opts(title="Sales Dashboard - Video 4 of 5", fillable=False)

def apply_common_styles(fig):
    # Set the background to transparent
    fig.update_layout(
        {
            "plot_bgcolor": "rgba(0,0,0,0)",  # Transparent plot background
            "paper_bgcolor": "rgba(0,0,0,0)",  # Transparent figure background
            "font": {"family": "Arial, sans-serif", "size": 12, "color": "darkblue"},
        }
    )
    return fig

@reactive.calc
def dat():
    infile = Path(__file__).parent / "data/sales.csv"
    df = pd.read_csv(infile)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.month_name()
    df["hour"] = df["order_date"].dt.hour
    df['value'] = df['quantity_ordered'] * df['price_each']
    return df


with ui.card(full_screen=True):
    ui.card_header("Sales by City in 2023")
    with ui.layout_sidebar():
        with ui.sidebar(open="open", bg="#f8f8f8"):
            ui.input_select(
                "select",
                "Select an option below:",
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
            )

        @render_altair
        def sales_over_time():
            df = dat()

            month_order = calendar.month_name[1:]

            # Creating a month order for sorting in Altair
            df["month"] = pd.Categorical(
                df["month"], categories=month_order, ordered=True
            )
            counts = (
                df.groupby(["month", "city"], observed=True)["quantity_ordered"]
                .sum()
                .reset_index()
            )
            city_counts = counts[counts["city"] == input.select()]
            # Create the Altair chart
            chart = (
                alt.Chart(city_counts)
                .mark_bar()
                .encode(
                    x="month",
                    y="quantity_ordered",
                    tooltip=["city", "month", "quantity_ordered"],
                )
                .properties(title=f"Sales Over Time in {input.select()}")
                .configure_axis(labelAngle=0)  # Adjust label angle if needed
            )
            return chart


with ui.layout_columns(widths=1 / 2):
    with ui.navset_card_underline():
        with ui.nav_panel("Top Sellers"):
            ui.input_numeric(
                "items", "Number of Items", 5, min=1, max=10, step=None, width=0.5
            )

            @render_plotly
            def top_sellers():
                df = dat()
                top_5_products = (
                    df.groupby("product")["quantity_ordered"]
                    .sum()
                    .nlargest(input.items())
                    .reset_index()
                )

                fig = px.bar(top_5_products, x="product", y="quantity_ordered")

                fig.update_traces(
                    marker_color=top_5_products["quantity_ordered"],
                    marker_colorscale="Blues",
                )
                apply_common_styles(fig)
                return fig

        with ui.nav_panel("Top Sellers Value ($)"):

            @render_plotly
            def top_sellers_value():
                df = dat()
                top_5_products = (
                    df.groupby("product")["value"]
                    .sum()
                    .nlargest(input.items())
                    .reset_index()
                )

                fig = px.bar(top_5_products, x="product", y="value")

                fig.update_traces(
                    marker_color=top_5_products["value"], marker_colorscale="Blues"
                )
                apply_common_styles(fig)
                return fig

        with ui.nav_panel("Lowest Sellers"):

            @render_plotly
            def lowest_sellers():
                df = dat()
                top_5_products = (
                    df.groupby("product")["quantity_ordered"]
                    .sum()
                    .nsmallest(input.items())
                    .reset_index()
                    .sort_values("quantity_ordered", ascending=False)
                )

                fig = px.bar(top_5_products, x="product", y="quantity_ordered")

                fig.update_traces(
                    marker_color=top_5_products["quantity_ordered"],
                    marker_colorscale="Reds",
                )
                apply_common_styles(fig)
                return fig

        with ui.nav_panel("Lowest Sellers Value ($)"):

            @render_plotly
            def lowest_sellers_value():
                df = dat()
                top_5_products = (
                    df.groupby("product")["value"]
                    .sum()
                    .nsmallest(input.items())
                    .reset_index()
                    .sort_values("value", ascending=False)
                )

                fig = px.bar(top_5_products, x="product", y="value")

                fig.update_traces(
                    marker_color=top_5_products["value"], marker_colorscale="Reds"
                )
                apply_common_styles(fig)
                return fig

    with ui.card():

        @render.plot
        def time_heatmap():
            # Step 1: Extract the hour from the order_date
            df = dat()

            # Step 2: Aggregate data by hour
            hourly_counts = df["hour"].value_counts().sort_index()

            # Step 3: Prepare data for heatmap (optional: create a dummy dimension if needed)
            # For simplicity, let's assume you want to view by hours (24 hrs) and just map counts directly.
            heatmap_data = np.zeros((24, 1))  # 24 hours, 1 dummy column
            for hour in hourly_counts.index:
                heatmap_data[hour, 0] = hourly_counts[hour]

            # Convert heatmap data to integer if needed
            heatmap_data = heatmap_data.astype(int)

            # Step 4: Plot with Seaborn
            plt.figure(figsize=(10, 8))
            sns.heatmap(
                heatmap_data,
                annot=True,
                fmt="d",
                cmap="coolwarm",
                cbar=False,
                xticklabels=[],
                yticklabels=[f"{i}:00" for i in range(24)],
            )
            plt.title("Number of Orders by Hour of Day")
            plt.ylabel("Hour of Day")
            plt.xlabel("Order Count")


with ui.navset_card_underline():
    with ui.nav_panel("Sales Locations"):

        @render.ui
        def heatmap():
            # Create a map centered roughly in the middle of the US
            df = dat()
            map = folium.Map(location=[37.0902, -95.7129], zoom_start=4)

            # Prepare the data for the HeatMap; each entry in heatmap_data is (lat, lon, weight)
            heatmap_data = [
                (lat, long, qty)
                for lat, long, qty in zip(df["lat"], df["long"], df["quantity_ordered"])
            ]
            # Add HeatMap to the map
            HeatMap(heatmap_data).add_to(map)

            return map


with ui.navset_card_underline():
    with ui.nav_panel("Dataframe Sample"):

        @render.data_frame
        def frame():
            return dat().head(1000)
