import os
from openai import OpenAI
from typing import Dict, List, Any
import json
import re
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

class SEOAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"

    def calculate_content_metrics(self, content: str, meta_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate statistical metrics for content"""
        word_count = len(content.split())
        keyword_density = {}

        if meta_data.get('keywords'):
            for keyword in meta_data['keywords']:
                count = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', content.lower()))
                if word_count > 0:
                    density = (count / word_count) * 100
                    keyword_density[keyword] = density

        return {
            'word_count': word_count,
            'keyword_density': keyword_density,
            'title_length': len(meta_data.get('title', '')) if meta_data.get('title') else 0,
            'meta_description_length': len(meta_data.get('meta_description', '')) if meta_data.get('meta_description') else 0
        }

    def check_technical_factors(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze technical SEO factors"""
        images = soup.find_all('img')
        links = soup.find_all('a')
        headings = {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1, 7)}

        return {
            'images_without_alt': len([img for img in images if not img.get('alt')]),
            'internal_links': len([link for link in links if not link.get('href') or urlparse(link['href']).netloc == urlparse(url).netloc]),
            'external_links': len([link for link in links if link.get('href') and urlparse(link['href']).netloc != urlparse(url).netloc]),
            'heading_structure': headings
        }

    def calculate_scores(self, metrics: Dict[str, Any], technical_factors: Dict[str, Any]) -> Dict[str, float]:
        """Calculate various SEO scores based on metrics"""
        scores = {
            'content_quality_score': 0.0,
            'keyword_effectiveness_score': 0.0,
            'meta_tags_score': 0.0,
            'technical_score': 0.0,
            'mobile_friendliness_score': 0.0
        }

        # Content Quality Score (0-100)
        if metrics['word_count'] >= 300:
            scores['content_quality_score'] = min(100, metrics['word_count'] / 10)
        else:
            scores['content_quality_score'] = (metrics['word_count'] / 300) * 100

        # Keyword Effectiveness Score
        if metrics['keyword_density']:
            keyword_scores = []
            for density in metrics['keyword_density'].values():
                if 0.5 <= density <= 2.5:  # Ideal keyword density range
                    keyword_scores.append(100)
                else:
                    keyword_scores.append(max(0, 100 - abs(density - 1.5) * 20))
            scores['keyword_effectiveness_score'] = sum(keyword_scores) / len(keyword_scores)

        # Meta Tags Score
        title_score = 100 if 30 <= metrics['title_length'] <= 60 else max(0, 100 - abs(45 - metrics['title_length']) * 2)
        desc_score = 100 if 120 <= metrics['meta_description_length'] <= 155 else max(0, 100 - abs(140 - metrics['meta_description_length']))
        scores['meta_tags_score'] = (title_score + desc_score) / 2

        # Technical Score
        technical_score = 100
        if technical_factors['images_without_alt'] > 0:
            technical_score -= min(30, technical_factors['images_without_alt'] * 5)
        if technical_factors['internal_links'] < 3:
            technical_score -= 20
        if technical_factors['heading_structure']['h1'] != 1:
            technical_score -= 20
        scores['technical_score'] = max(0, technical_score)

        return scores

    def analyze_website_seo(self, url: str, content: str, meta_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze website SEO using statistical metrics and AI insights"""
        try:
            # Set up headers to mimic a regular browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }

            # Get HTML content for technical analysis
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Calculate metrics
            content_metrics = self.calculate_content_metrics(content, meta_data)
            technical_factors = self.check_technical_factors(url, soup)
            scores = self.calculate_scores(content_metrics, technical_factors)

            # Get AI insights for qualitative analysis
            ai_insights = self._get_ai_insights(url, content[:2000], meta_data)

            # Calculate overall SEO score
            seo_score = int(sum([
                scores['content_quality_score'] * 0.25,
                scores['keyword_effectiveness_score'] * 0.25,
                scores['meta_tags_score'] * 0.2,
                scores['technical_score'] * 0.2,
                scores.get('mobile_friendliness_score', 0) * 0.1
            ]))

            # Combine all results
            analysis_results = {
                'url': url,
                'seo_score': seo_score,
                'content_quality_score': scores['content_quality_score'],
                'keyword_effectiveness_score': scores['keyword_effectiveness_score'],
                'meta_tags_score': scores['meta_tags_score'],
                'technical_score': scores['technical_score'],
                'mobile_friendliness_score': scores.get('mobile_friendliness_score', 0),
                'analysis_data': {
                    'content_metrics': content_metrics,
                    'technical_factors': technical_factors,
                    'qualitative_insights': ai_insights
                }
            }

            return analysis_results

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise Exception("This website blocks automated access. Please try a different website or contact the website administrator.")
            raise Exception(f"HTTP Error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error accessing website: {str(e)}")
        except Exception as e:
            print(f"Error in SEO analysis: {str(e)}")
            return {
                'url': url,
                'seo_score': 0,
                'content_quality_score': 0,
                'keyword_effectiveness_score': 0,
                'meta_tags_score': 0,
                'technical_score': 0,
                'mobile_friendliness_score': 0,
                'analysis_data': {
                    'error': str(e)
                }
            }

    def _get_ai_insights(self, url: str, content_preview: str, meta_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get qualitative insights from AI"""
        prompt = f"""Analyze this website's SEO and provide specific recommendations:

URL: {url}

Content Preview:
{content_preview}

Meta Data:
Title: {meta_data.get('title', 'Not found')}
Description: {meta_data.get('meta_description', 'Not found')}
Keywords: {', '.join(meta_data.get('keywords', ['None found']))}

Provide insights in JSON format with:
{{
    "strengths": [<list of current SEO strengths>],
    "improvements": [<list of specific areas needing improvement>],
    "keyword_recommendations": [<list of suggested keywords>],
    "content_suggestions": [<list of content improvement suggestions>],
    "technical_recommendations": [<list of technical SEO fixes>]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are an expert SEO analyst. Provide detailed, actionable SEO recommendations."
                },
                {
                    "role": "user",
                    "content": prompt
                }],
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error getting AI insights: {str(e)}")
            return {
                "strengths": [],
                "improvements": [],
                "keyword_recommendations": [],
                "content_suggestions": [],
                "technical_recommendations": []
            }

    def generate_seo_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate a detailed SEO report from analysis results"""
        try:
            prompt = f"""Generate a detailed SEO report based on the following analysis:

Analysis Results: {json.dumps(analysis_results, indent=2)}

Please provide a comprehensive report with actionable insights and recommendations."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"Failed to generate SEO report: {str(e)}"

    def get_keyword_suggestions(self, current_keywords: List[str], industry: str) -> List[str]:
        """Get AI-powered keyword suggestions"""
        try:
            prompt = f"""Generate relevant SEO keyword suggestions for a {industry} website.

Current Keywords: {', '.join(current_keywords) if current_keywords else 'None provided'}
Industry: {industry}

Respond with a JSON object containing an array of keyword suggestions under the 'keywords' key.
Each keyword should be relevant to the industry and have good search potential.

Format:
{{
    "keywords": [
        "keyword 1",
        "keyword 2",
        ...
    ]
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": "You are an SEO keyword research expert. Suggest relevant, high-potential keywords."
                },
                {
                    "role": "user",
                    "content": prompt
                }],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("keywords", [])
        except Exception as e:
            print(f"Error in keyword suggestions: {str(e)}")
            return []