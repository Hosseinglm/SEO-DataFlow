import pandas as pd
from database import Database
import schedule
import time
from datetime import datetime


class SEOPipeline:
    def __init__(self):
        self.db = Database()

    def process_seo_data(self, data):
        """Process and clean SEO data before storing"""
        processed_data = {
            'url': data['url'],
            'title': data['title'].strip(),
            'meta_description': data['meta_description'].strip(),
            'h1_tags': [tag.strip() for tag in data['h1_tags']],
            'keywords': [kw.strip().lower() for kw in data['keywords']],
            'page_rank': float(data['page_rank'])
        }
        return processed_data

    def run_pipeline(self, data):
        """Execute the SEO data pipeline"""
        try:
            processed_data = self.process_seo_data(data)
            self.db.insert_seo_data(processed_data)
            return True, "Data processed successfully"
        except Exception as e:
            return False, str(e)

    def schedule_report(self, report_id, schedule_time):
        """Schedule a report to run at specified time"""

        def job():
            print(f"Running report {report_id} at {datetime.now()}")
            # Add report execution logic here

        schedule.every().day.at(schedule_time).do(job)

    @staticmethod
    def run_scheduled_jobs():
        """Run scheduled jobs"""
        while True:
            schedule.run_pending()
            time.sleep(60)
