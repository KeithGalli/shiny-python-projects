from pathlib import Path
import pandas as pd
import calendar

import plotly.express as px
from shiny import reactive
from shiny.express import render, input, ui
from shinywidgets import render_plotly

ui.page_opts(title="Sales Dashboard - Video 2 of 5", fillable=False)

ui.input_checkbox("bar_color", "Make Bars Red?", False)  

ui.input_numeric("n", "Number of Items", 5, min=0, max=20)

@reactive.calc
def color():
    return "red" if input.bar_color() else "blue"

@reactive.calc
def dat():
    infile = Path(__file__).parent / "data/sales.csv"
    df = pd.read_csv(infile)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.month_name()
    return df

@render_plotly
def plot1():
    df = dat()
    top_sales = df.groupby('product')['quantity_ordered'].sum().nlargest(input.n()).reset_index()
    fig = px.bar(top_sales, x='product', y='quantity_ordered')
    fig.update_traces(marker_color=color())
    return fig

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


@render_plotly
def sales_over_time():
    df = dat()
    print(list(df.city.unique()))
    sales = df.groupby(["city", "month"])["quantity_ordered"].sum().reset_index()
    sales_by_city = sales[sales["city"] == input.city()]
    month_orders = calendar.month_name[1:]
    fig = px.bar(
        sales_by_city,
        x="month",
        y="quantity_ordered",
        title=f"Sales over Time -- {input.city()}",
        category_orders={"month": month_orders},
    )
    fig.update_traces(marker_color=color())
    return fig

with ui.card():
    ui.card_header("Sample Sales Data")

    @render.data_frame
    def sample_sales_data():
        return dat().head(100)
