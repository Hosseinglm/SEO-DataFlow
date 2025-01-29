import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def create_seo_timeline(data):
    """Create timeline of SEO data entries"""
    fig = px.line(data, x='created_at', y='page_rank',
                  title='SEO Performance Over Time')
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Page Rank",
        template="plotly_dark"
    )
    return fig


def create_keyword_distribution(data):
    """Create keyword distribution chart"""
    keywords = [kw for sublist in data['keywords'] for kw in sublist]
    keyword_counts = pd.Series(keywords).value_counts().head(10)

    fig = px.bar(
        x=keyword_counts.index,
        y=keyword_counts.values,
        title='Top 10 Keywords Distribution'
    )
    fig.update_layout(
        xaxis_title="Keywords",
        yaxis_title="Frequency",
        template="plotly_dark"
    )
    return fig


def create_url_performance(data):
    """Create URL performance chart"""
    top_urls = data.nlargest(10, 'page_rank')

    fig = px.bar(
        top_urls,
        x='url',
        y='page_rank',
        title='Top 10 Performing URLs'
    )
    fig.update_layout(
        xaxis_title="URL",
        yaxis_title="Page Rank",
        template="plotly_dark",
        xaxis_tickangle=-45
    )
    return fig
