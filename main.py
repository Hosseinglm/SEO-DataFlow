import streamlit as st
import pandas as pd
from database import Database
from data_pipeline import SEOPipeline
from utils import validate_seo_data, format_date, get_theme_toggle
from visualization import create_seo_timeline, create_keyword_distribution, create_url_performance
from theme import apply_theme
from ml_engine import SEOMLEngine
from seo_analyzer import SEOAnalyzer
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import io

# Initialize
st.set_page_config(page_title="AI-Powered SEO Management System", layout="wide")
db = Database()
pipeline = SEOPipeline()
ml_engine = SEOMLEngine()
seo_analyzer = SEOAnalyzer()

# Apply theme
theme = get_theme_toggle()
apply_theme(theme)

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "AI Insights", "SEO Analysis", "Data Pipeline", "Reports", "Settings"])

if page == "Dashboard":
    st.title("SEO Dashboard")

    # Load data
    seo_data = db.get_seo_data()

    if not seo_data.empty:
        # KPI metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total URLs", len(seo_data))
        with col2:
            st.metric("Average Page Rank", round(seo_data['page_rank'].mean(), 2))
        with col3:
            st.metric("Last Update", format_date(seo_data['created_at'].max()))

        # Visualizations
        st.plotly_chart(create_seo_timeline(seo_data), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_keyword_distribution(seo_data), use_container_width=True)
        with col2:
            st.plotly_chart(create_url_performance(seo_data), use_container_width=True)
    else:
        st.info("No SEO data available. Please add data through the Data Pipeline.")

elif page == "AI Insights":
    st.title("AI-Powered SEO Insights")

    insights = ml_engine.get_seo_insights()

    # Anomaly Detection
    st.subheader("🔍 Anomaly Detection")
    if not insights['anomalies'].empty:
        st.warning(f"Found {len(insights['anomalies'])} anomalies in your SEO data")
        st.dataframe(insights['anomalies'][['url', 'page_rank', 'created_at']])
    else:
        st.success("No anomalies detected in your SEO data")

    # Trend Forecasting
    st.subheader("📈 SEO Trend Forecast")
    if not insights['forecast'].empty:
        fig = px.line(insights['forecast'],
                     x='ds',
                     y=['yhat', 'yhat_lower', 'yhat_upper'],
                     labels={'ds': 'Date', 'yhat': 'Predicted Page Rank'},
                     title='30-Day SEO Performance Forecast')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data for forecasting")

    # Significant Changes
    st.subheader("⚠️ Significant Changes")
    if insights['changes']:
        for change in insights['changes']:
            with st.expander(f"{abs(change['change']):.1f}% change for {change['url']}"):
                st.write(f"Previous Rank: {change['previous_rank']:.2f}")
                st.write(f"Current Rank: {change['current_rank']:.2f}")
                st.write(f"Date: {change['date']}")
    else:
        st.success("No significant changes detected")

elif page == "SEO Analysis":
    st.title("AI-Powered SEO Analysis")

    # URL Input
    url = st.text_input("Enter Website URL to Analyze", placeholder="https://example.com")
    industry = st.text_input("Industry/Niche", placeholder="e.g., Technology, E-commerce, Healthcare")

    if st.button("Analyze SEO"):
        if not url.startswith(('http://', 'https://')):
            st.error("Please enter a valid URL starting with http:// or https://")
        else:
            with st.spinner("Analyzing website... This may take a few moments"):
                try:
                    # Initial content fetch
                    response = requests.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    }, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Extract meta data
                    meta_data = {
                        'title': soup.title.string if soup.title else 'No title found',
                        'meta_description': '',
                        'keywords': []
                    }

                    meta_desc_tag = soup.find('meta', {'name': 'description'})
                    if meta_desc_tag:
                        meta_data['meta_description'] = meta_desc_tag.get('content', '')

                    keywords_tag = soup.find('meta', {'name': 'keywords'})
                    if keywords_tag:
                        meta_data['keywords'] = [tag.strip() for tag in keywords_tag.get('content', '').split(',') if tag.strip()]

                    # Get analysis
                    analysis = seo_analyzer.analyze_website_seo(url, soup.get_text(), meta_data)

                    if 'error' in analysis.get('analysis_data', {}):
                        st.error(f"Analysis Error: {analysis['analysis_data']['error']}")
                        st.info("Please try a different website that allows automated access.")
                        st.stop()

                    st.success("Analysis completed! Review the results below.")

                    # Store analysis in session state for save button
                    st.session_state.current_analysis = {
                        'analysis': analysis,
                        'meta_data': meta_data,
                        'h1_tags': [h.get_text() for h in soup.find_all('h1')]
                    }

                    # Display historical trend if available
                    history = db.get_seo_analysis_history(url)
                    if not history.empty and len(history) > 1:
                        st.subheader("📈 SEO Score History")
                        fig = px.line(history, x='created_at', y='seo_score',
                                    title='SEO Score Trend')
                        st.plotly_chart(fig)

                    # Main metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        score = analysis['seo_score']
                        score_color = 'red' if score < 50 else 'yellow' if score < 80 else 'green'
                        st.metric("Overall SEO Score", f"{score}/100")
                    with col2:
                        st.metric("Content Quality", f"{analysis['content_quality_score']:.1f}%")
                    with col3:
                        st.metric("Technical Score", f"{analysis['technical_score']:.1f}%")

                    # Detailed scores
                    st.subheader("📊 Detailed Scores")
                    scores_df = pd.DataFrame({
                        'Metric': ['Content Quality', 'Keyword Effectiveness', 'Meta Tags', 'Technical', 'Mobile Friendliness'],
                        'Score': [
                            analysis['content_quality_score'],
                            analysis['keyword_effectiveness_score'],
                            analysis['meta_tags_score'],
                            analysis['technical_score'],
                            analysis['mobile_friendliness_score']
                        ]
                    })
                    fig = px.bar(scores_df, x='Metric', y='Score',
                               title='SEO Component Scores')
                    st.plotly_chart(fig)

                    # Content Metrics
                    st.subheader("📝 Content Analysis")
                    metrics = analysis['analysis_data']['content_metrics']
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Word Count", metrics['word_count'])
                        st.metric("Title Length", metrics['title_length'])
                    with col2:
                        st.metric("Meta Description Length", metrics['meta_description_length'])
                        if metrics['keyword_density']:
                            st.write("Keyword Density:")
                            for keyword, density in metrics['keyword_density'].items():
                                st.write(f"• {keyword}: {density:.2f}%")

                    # Technical Factors
                    st.subheader("⚙️ Technical Analysis")
                    tech = analysis['analysis_data']['technical_factors']
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Internal Links", tech['internal_links'])
                        st.metric("External Links", tech['external_links'])
                    with col2:
                        st.metric("Images Missing Alt Text", tech['images_without_alt'])
                        st.write("Heading Structure:")
                        for heading, count in tech['heading_structure'].items():
                            st.write(f"• {heading.upper()}: {count}")

                    # Qualitative Insights
                    insights = analysis['analysis_data']['qualitative_insights']
                    with st.expander("🔍 Qualitative Insights", expanded=False):
                        if insights.get('strengths'):
                            st.subheader("💪 Strengths")
                            for strength in insights['strengths']:
                                st.success(strength)

                        if insights.get('improvements'):
                            st.subheader("🎯 Areas for Improvement")
                            for improvement in insights['improvements']:
                                st.warning(improvement)

                        if insights.get('technical_recommendations'):
                            st.subheader("⚙️ Technical Recommendations")
                            for i, rec in enumerate(insights['technical_recommendations'], 1):
                                st.code(f"{i}. {rec}")

                    # Add save button at the bottom
                    if st.button("Save Analysis to Pipeline"):
                        try:
                            # Prepare data for pipeline
                            pipeline_data = {
                                'url': url,
                                'title': meta_data['title'],
                                'meta_description': meta_data['meta_description'],
                                'h1_tags': st.session_state.current_analysis['h1_tags'],
                                'keywords': meta_data['keywords'],
                                'page_rank': analysis['seo_score'] / 20  # Convert to 0-5 scale
                            }

                            # Save to pipeline
                            success, message = pipeline.run_pipeline(pipeline_data)
                            if success:
                                # Save analysis results
                                db.insert_seo_analysis(analysis)
                                st.success("Analysis saved to pipeline successfully!")
                            else:
                                st.error(f"Error saving to pipeline: {message}")
                        except Exception as e:
                            st.error(f"Error saving to pipeline: {str(e)}")

                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403:
                        st.error("This website blocks automated access. Please try a different website.")
                        st.info("Some popular websites have strict security measures that prevent automated analysis.")
                    else:
                        st.error(f"HTTP Error: {str(e)}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error accessing the website: {str(e)}")
                    st.info("Please make sure the website is accessible and try again.")
                except Exception as e:
                    st.error(f"An error occurred during analysis: {str(e)}")
                    st.info("If the problem persists, try analyzing a different website.")

elif page == "Data Pipeline":
    st.title("Data Pipeline Management")

    # Show pending analyses first
    st.subheader("Recent SEO Analyses")
    analyses = db.get_seo_data()
    if not analyses.empty:
        for _, analysis in analyses.iterrows():
            with st.expander(f"{analysis['url']} - {format_date(analysis['created_at'])}"):
                st.write(f"Title: {analysis['title']}")
                st.write(f"Meta Description: {analysis['meta_description']}")
                st.write(f"Page Rank: {analysis['page_rank']}")
                st.write("Keywords:", ", ".join(analysis['keywords']) if analysis['keywords'] else "None")
                st.write("H1 Tags:", ", ".join(analysis['h1_tags']) if analysis['h1_tags'] else "None")

    st.divider()
    st.subheader("Add New SEO Data")

    with st.form("seo_data_form"):
        url = st.text_input("URL")
        title = st.text_input("Page Title")
        meta_description = st.text_area("Meta Description")
        h1_tags = st.text_input("H1 Tags (comma-separated)")
        keywords = st.text_input("Keywords (comma-separated)")
        page_rank = st.number_input("Page Rank", min_value=0.0, max_value=10.0)

        submit = st.form_submit_button("Process Data")
        if submit:
            data = {
                'url': url,
                'title': title,
                'meta_description': meta_description,
                'h1_tags': [tag.strip() for tag in h1_tags.split(',')],
                'keywords': [kw.strip() for kw in keywords.split(',')],
                'page_rank': page_rank
            }

            is_valid, message = validate_seo_data(data)
            if is_valid:
                success, message = pipeline.run_pipeline(data)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error(message)

elif page == "Reports":
    st.title("Advanced Report Management")

    # Report Type Selection
    report_type = st.sidebar.selectbox(
        "Select Report Type",
        ["SEO Performance", "Keyword Analysis", "Technical Health", "Custom Query"]
    )

    # Create new report
    with st.expander("Create New Report", expanded=True):
        with st.form("new_report"):
            report_name = st.text_input("Report Name")
            report_description = st.text_area("Description")

            if report_type == "Custom Query":
                report_query = st.text_area("SQL Query", 
                    placeholder="SELECT url, page_rank, created_at FROM seo_data WHERE page_rank > 3")
            else:
                # Predefined templates based on report type
                if report_type == "SEO Performance":
                    report_query = """
                        SELECT url, page_rank, created_at 
                        FROM seo_data 
                        ORDER BY created_at DESC 
                        LIMIT 10
                    """
                elif report_type == "Keyword Analysis":
                    report_query = """
                        SELECT url, keywords, created_at 
                        FROM seo_data 
                        WHERE array_length(keywords, 1) > 0
                        ORDER BY created_at DESC
                    """
                else:  # Technical Health
                    report_query = """
                        SELECT url, meta_description, h1_tags 
                        FROM seo_data 
                        WHERE array_length(h1_tags, 1) = 0 
                        OR meta_description IS NULL
                    """
                st.code(report_query, language="sql")

            # Schedule options
            schedule_type = st.selectbox("Schedule Type", ["Daily", "Weekly", "Monthly", "Custom"])
            if schedule_type == "Custom":
                schedule_time = st.time_input("Schedule Time")
                schedule_days = st.multiselect("Select Days", 
                    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
                schedule_value = f"{schedule_time.strftime('%H:%M')} on {','.join(schedule_days)}"
            else:
                schedule_time = st.time_input("Time to Run")
                schedule_value = f"{schedule_type} at {schedule_time.strftime('%H:%M')}"

            # Export format
            export_format = st.selectbox("Export Format", ["CSV", "JSON", "Excel"])

            if st.form_submit_button("Save Report"):
                try:
                    db.save_report(
                        name=report_name,
                        description=report_description,
                        query=report_query,
                        schedule=schedule_value
                    )
                    st.success("Report saved successfully!")
                except Exception as e:
                    st.error(f"Error saving report: {str(e)}")

    # View existing reports
    st.subheader("Existing Reports")
    reports = db.get_reports()
    if not reports.empty:
        for _, report in reports.iterrows():
            with st.expander(f"{report['name']} - {format_date(report['created_at'])}"):
                st.write(f"Description: {report['description']}")
                st.code(report['query'], language="sql")
                st.text(f"Scheduled: {report['schedule']}")

                # Execute report
                if st.button(f"Run Report: {report['name']}"):
                    try:
                        # Execute the report query
                        with st.spinner("Generating report..."):
                            results = pd.read_sql(report['query'], db.engine)

                            # Display results
                            st.dataframe(results)

                            # Download buttons based on format
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                csv = results.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    "Download CSV",
                                    csv,
                                    f"{report['name']}.csv",
                                    "text/csv"
                                )
                            with col2:
                                json_str = results.to_json(orient='records')
                                st.download_button(
                                    "Download JSON",
                                    json_str,
                                    f"{report['name']}.json",
                                    "application/json"
                                )
                            with col3:
                                excel_buffer = io.BytesIO()
                                results.to_excel(excel_buffer, index=False)
                                excel_data = excel_buffer.getvalue()
                                st.download_button(
                                    "Download Excel",
                                    excel_data,
                                    f"{report['name']}.xlsx",
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                    except Exception as e:
                        st.error(f"Error executing report: {str(e)}")
    else:
        st.info("No reports configured yet.")

elif page == "Settings":
    st.title("Settings")

    st.subheader("Database Configuration")
    st.info("Database connection is configured through environment variables.")

    st.subheader("Pipeline Settings")
    st.checkbox("Enable automatic data collection", value=True)
    st.number_input("Data collection interval (minutes)", min_value=5, value=60)

    # ML Settings
    st.subheader("AI/ML Settings")
    st.slider("Anomaly Detection Sensitivity", min_value=0.01, max_value=0.5, value=0.1, step=0.01)
    st.number_input("Forecast Days", min_value=7, max_value=90, value=30)
    st.slider("Change Detection Threshold (%)", min_value=5, max_value=50, value=20)

    if st.button("Save Settings"):
        st.success("Settings saved successfully!")

# Run the app
if __name__ == "__main__":
    st.sidebar.markdown("---")
    st.sidebar.markdown("v1.2.0 - SEO Analysis Enhanced")