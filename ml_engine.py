import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from prophet import Prophet
from database import Database
import streamlit as st
from datetime import datetime, timedelta

class SEOMLEngine:
    def __init__(self):
        self.db = Database()
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)

    def detect_anomalies(self, data):
        """Detect anomalies in SEO metrics using Isolation Forest"""
        if len(data) < 2:
            return pd.DataFrame()

        try:
            # Prepare data for anomaly detection
            X = data[['page_rank']].values
            anomalies = self.isolation_forest.fit_predict(X)

            # Create anomaly DataFrame
            anomaly_data = data.copy()
            anomaly_data['is_anomaly'] = anomalies == -1
            return anomaly_data[anomaly_data['is_anomaly']]
        except Exception as e:
            st.error(f"Error in anomaly detection: {str(e)}")
            return pd.DataFrame()

    def forecast_trends(self, data, periods=30):
        """Forecast SEO trends using Prophet"""
        if len(data) < 2:
            return pd.DataFrame()

        try:
            # Prepare data for Prophet
            df = data[['created_at', 'page_rank']].copy()
            df.columns = ['ds', 'y']

            # Create and fit Prophet model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=0.95
            )
            model.fit(df)

            # Make future predictions
            future_dates = model.make_future_dataframe(periods=periods)
            forecast = model.predict(future_dates)

            return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        except Exception as e:
            st.error(f"Error in trend forecasting: {str(e)}")
            return pd.DataFrame()

    def check_significant_changes(self, data, threshold=0.2):
        """Check for significant changes in SEO metrics"""
        if len(data) < 2:
            return []

        try:
            changes = []
            recent_data = data.sort_values('created_at', ascending=False)

            if len(recent_data) >= 2:
                current = recent_data.iloc[0]
                previous = recent_data.iloc[1]

                percent_change = (current['page_rank'] - previous['page_rank']) / previous['page_rank']

                if abs(percent_change) >= threshold:
                    changes.append({
                        'url': current['url'],
                        'change': percent_change * 100,
                        'previous_rank': previous['page_rank'],
                        'current_rank': current['page_rank'],
                        'date': current['created_at']
                    })

            return changes
        except Exception as e:
            st.error(f"Error checking for significant changes: {str(e)}")
            return []

    def get_seo_insights(self):
        """Get comprehensive SEO insights including anomalies and forecasts"""
        try:
            data = self.db.get_seo_data()

            if data.empty:
                return {
                    'anomalies': pd.DataFrame(),
                    'forecast': pd.DataFrame(),
                    'changes': []
                }

            anomalies = self.detect_anomalies(data)
            forecast = self.forecast_trends(data)
            changes = self.check_significant_changes(data)

            return {
                'anomalies': anomalies,
                'forecast': forecast,
                'changes': changes
            }
        except Exception as e:
            st.error(f"Error getting SEO insights: {str(e)}")
            return {
                'anomalies': pd.DataFrame(),
                'forecast': pd.DataFrame(),
                'changes': []
            }