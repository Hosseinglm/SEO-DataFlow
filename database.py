import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import pandas as pd
from sqlalchemy import create_engine

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            port=os.environ['PGPORT']
        )
        # Create SQLAlchemy engine for pandas operations
        self.engine = create_engine(os.environ['DATABASE_URL'])
        self.create_tables()

    def create_tables(self):
        with self.conn.cursor() as cur:
            # SEO Data table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS seo_data (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    meta_description TEXT,
                    h1_tags TEXT[],
                    keywords TEXT[],
                    page_rank FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # SEO Analysis Results table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS seo_analysis (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    seo_score INTEGER,
                    content_quality_score FLOAT,
                    keyword_effectiveness_score FLOAT,
                    meta_tags_score FLOAT,
                    technical_score FLOAT,
                    mobile_friendliness_score FLOAT,
                    analysis_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Reports table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    query TEXT NOT NULL,
                    schedule TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.conn.commit()

    def insert_seo_data(self, data):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO seo_data (url, title, meta_description, h1_tags, keywords, page_rank)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (data['url'], data['title'], data['meta_description'],
                       data['h1_tags'], data['keywords'], data['page_rank']))
            self.conn.commit()

    def insert_seo_analysis(self, analysis_data):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO seo_analysis (
                    url, seo_score, content_quality_score, 
                    keyword_effectiveness_score, meta_tags_score,
                    technical_score, mobile_friendliness_score,
                    analysis_data
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    analysis_data['url'],
                    analysis_data['seo_score'],
                    analysis_data['content_quality_score'],
                    analysis_data['keyword_effectiveness_score'],
                    analysis_data['meta_tags_score'],
                    analysis_data['technical_score'],
                    analysis_data['mobile_friendliness_score'],
                    Json(analysis_data['analysis_data'])
                ))
            self.conn.commit()

    def get_seo_data(self):
        return pd.read_sql("SELECT * FROM seo_data ORDER BY created_at DESC", self.engine)

    def get_seo_analysis_history(self, url=None):
        query = "SELECT * FROM seo_analysis ORDER BY created_at DESC"
        if url:
            query = "SELECT * FROM seo_analysis WHERE url = %s ORDER BY created_at DESC"
            return pd.read_sql(query, self.engine, params=(url,))
        return pd.read_sql(query, self.engine)

    def save_report(self, name, description, query, schedule):
        """Save a new report configuration"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO reports (name, description, query, schedule)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """, (name, description, query, schedule))
            report_id = cur.fetchone()[0]
            self.conn.commit()
            return report_id

    def get_reports(self):
        """Get all configured reports"""
        return pd.read_sql("""
            SELECT id, name, description, query, schedule, created_at 
            FROM reports 
            ORDER BY created_at DESC
        """, self.engine)

    def execute_report(self, report_id):
        """Execute a specific report by ID"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            # First get the report details
            cur.execute("SELECT query FROM reports WHERE id = %s", (report_id,))
            report = cur.fetchone()
            if not report:
                raise Exception("Report not found")

            # Execute the report query
            cur.execute(report['query'])
            results = cur.fetchall()
            return results