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

ui.page_opts(window_title="Sales Dashboard - Video 5 of 5", fillable=False)

@reactive.calc
def dat():
    infile = Path(__file__).parent / "data/sales.csv"
    df = pd.read_csv(infile)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.month_name()
    df["hour"] = df["order_date"].dt.hour
    df['value'] = df['quantity_ordered'] * df['price_each']
    return df

with ui.div(class_="header-container"):
    with ui.div(class_="logo-container"):
        @render.image  
        def image():
            here = Path(__file__).parent
            img = {"src": here / "images/shiny-logo.png", "height": "100%"}  
            return img
        
    with ui.div(class_="title-container"):
        ui.h2("Sales Dashboard - Video 5 of 5")

ui.tags.style(
    """
    .header-container {
        display: flex;
        align-items: center;
        height:60px;
        justify-content: center;
        padding: 10px;
    }

    .logo-container {
        height: 100%; /* Adjust the spacing between the logo and the title */
    }

    .logo-container img {
        height: 40px; /* Maintain aspect ratio */
        margin-right: 5px;
    }

    .title-container h2 {
        color: white;
        text-align: center;
        padding: 10px; /* Adjust padding as needed */
        margin: 0; /* Remove default margin */
        display: inline-block; /* Ensure the background color only covers the text */
        line-height: 1.2; /* Adjust line height as needed */
    }

    body {
        background-color: #5DADE2
    }

    .modebar {
        display: none;
    }
    """
)

# Function to apply common layout updates
def apply_layout_updates(fig, yaxis_title):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Remove background color
        xaxis=dict(
            title='',  # Remove x-axis label
            showgrid=False  # Remove x-axis grid lines
        ),
        yaxis=dict(
            title=yaxis_title,  # Set y-axis label
            showgrid=False  # Remove y-axis grid lines
        ),
        showlegend=False,  # Hide legend
        coloraxis_showscale=False
    )
    return fig

# Set Matplotlib rcParams for font customization
plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 12,
    'text.color': '#1f4b99',
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12
})


with ui.card():  
    ui.card_header("Sales by City 2023")

    with ui.layout_sidebar():  
        with ui.sidebar(bg="#f8f8f8", open='open', id_="Lalalala"):  
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
                selected='Boston (MA)'
            )

        @render_widget
        def sales_over_time_altair():
            df = dat()
            # Group the data by city and month, then sum the quantities ordered
            sales = df.groupby(["city", "month"])["quantity_ordered"].sum().reset_index()

            # Filter the sales data to only include the selected city
            sales_by_city = sales[sales["city"] == input.city()]

            # Define the order of months
            month_orders = list(calendar.month_name)[1:]

            # Create the bar chart
            chart = alt.Chart(sales_by_city).mark_bar().encode(
                x=alt.X('month', title="Month", sort=month_orders),
                y=alt.Y('quantity_ordered', title="Quantity Ordered"),
                tooltip=['month', 'quantity_ordered']
            ).properties(
                title=f"Sales over Time -- {input.city()}"
            ).configure_axis(
                labelFont='Arial',
                labelFontSize=12,
                labelColor='#1f4b99',
                titleFont='Arial',
                titleFontSize=14,
                titleColor='#1f4b99',
                labelAngle=0,
                grid=False,
            ).configure_title(
                fontSize=14,
                font='Arial',
                color='#1f4b99',
            ).configure_view(
                strokeWidth=0
            )

            return chart

with ui.layout_column_wrap(width=1/2):
    with ui.navset_card_underline(id="tab", footer=ui.input_numeric("n", "Number of Items", 5, min=0, max=20)):  
        with ui.nav_panel("Top Sellers"):

            @render_plotly
            def plot_top_sellers():
                df = dat()
                top_sales = df.groupby('product')['quantity_ordered'].sum().nlargest(input.n()).reset_index()
                fig = px.bar(top_sales, x='product', y='quantity_ordered', color="quantity_ordered", color_continuous_scale="Blues")
                apply_layout_updates(fig, "Quantity Ordered")
                return fig

        with ui.nav_panel("Top Sellers Value ($)"):

            @render_plotly
            def plot_top_sellers_value():
                df = dat()
                top_sales = df.groupby('product')['value'].sum().nlargest(input.n()).reset_index()
                fig = px.bar(top_sales, x='product', y='value', color_continuous_scale="Blues")
                return fig

        with ui.nav_panel("Lowest Sellers"):

            @render_plotly
            def plot_lowest_sellers():
                df = dat()
                top_sales = df.groupby('product')['quantity_ordered'].sum().nsmallest(input.n()).reset_index()
                fig = px.bar(top_sales, x='product', y='quantity_ordered')
                return fig

        with ui.nav_panel("Lowest Sellers Value ($)"):
            @render_plotly
            def plot_lowest_sellers_value():
                df = dat()
                top_sales = df.groupby('product')['value'].sum().nsmallest(input.n()).reset_index()
                fig = px.bar(top_sales, x='product', y='value')
                return fig


    with ui.card():
        ui.card_header("Sales by Time of Day Heatmap")
        @render.plot
        def plot_sales_by_time():
            df = dat()
            sales_by_hour = df['hour'].value_counts().reindex(np.arange(0,24), fill_value=0)

            heatmap_data = sales_by_hour.values.reshape(24,1)
            ax = sns.heatmap(heatmap_data,
                        annot=True,
                        fmt="d",
                        cmap="Blues",
                        cbar=False,
                        xticklabels=[],
                        yticklabels=[f"{i}:00" for i in range(24)])
            
            plt.title("Number of Orders by Hour of Day")
            plt.xlabel("Hour of Day", color='#1f4b99')
            plt.ylabel("Order Count", color='#1f4b99')

            # Setting the tick labels' color explicitly
            ax.tick_params(axis='x', colors='#1f4b99')
            ax.tick_params(axis='y', colors='#1f4b99')
            


with ui.card():
    ui.card_header("Sales by Location Map")
    @render.ui
    def plot_us_heatmap():
        df = dat()

        heatmap_data = df[['lat','long','quantity_ordered']].values

        map = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
        HeatMap(heatmap_data).add_to(map)
        return map
    

with ui.card():
    ui.card_header("Sample Sales Data")

    @render.data_frame
    def sample_sales_data():
        return dat().head(100)
