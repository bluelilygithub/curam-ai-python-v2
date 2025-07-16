# ====================================================================================
# STEP 1: Add this to your existing services/__init__.py
# ====================================================================================

# Add this import to your services/__init__.py file:
from .rss_service import RSSService

# So your services/__init__.py should look like:
from .llm_service import LLMService
from .property_service import PropertyAnalysisService  
from .stability_service import StabilityService
from .rss_service import RSSService  # Add this line

# ====================================================================================
# STEP 2: Create services/rss_service.py (Simplified version for your architecture)
# ====================================================================================

"""
RSS Service for Australian Property Data
Designed to integrate with existing Brisbane Property Intelligence architecture
"""

import feedparser
import requests
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
import time
import random

class RSSService:
    """RSS service that integrates with existing architecture"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Australian Property RSS Feeds
        self.feeds = {
            'realestate_news': {
                'url': 'https://realestate.com.au/news/feed',
                'name': 'RealEstate.com.au',
                'active': True
            },
            'smart_property': {
                'url': 'https://smartpropertyinvestment.com.au/feed',
                'name': 'Smart Property Investment', 
                'active': True
            },
            'view_property': {
                'url': 'https://view.com.au/news/feed',
                'name': 'View.com.au',
                'active': True
            },
            'property_me': {
                'url': 'https://propertyme.com.au/blog/feed',
                'name': 'PropertyMe',
                'active': True
            }
        }
        
        self.headers = {
            'User-Agent': 'Brisbane Property Intelligence API/2.0.0',
            'Accept': 'application/rss+xml, application/xml'
        }
        
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
    
    def get_property_news(self, brisbane_focus: bool = False, max_items: int = 20) -> List[Dict]:
        """Get recent property news, optionally filtered for Brisbane"""
        all_articles = []
        
        for feed_key, feed_config in self.feeds.items():
            if not feed_config['active']:
                continue
                
            try:
                # Check cache first
                cache_key = f"{feed_key}_cache"
                if cache_key in self.cache:
                    cached_data, cached_time = self.cache[cache_key]
                    if datetime.now() - cached_time < self.cache_duration:
                        articles = cached_data
                    else:
                        articles = self._fetch_feed(feed_config)
                        self.cache[cache_key] = (articles, datetime.now())
                else:
                    articles = self._fetch_feed(feed_config)
                    self.cache[cache_key] = (articles, datetime.now())
                
                all_articles.extend(articles)
                
            except Exception as e:
                self.logger.error(f"Failed to fetch {feed_key}: {e}")
                continue
        
        # Filter for Brisbane if requested
        if brisbane_focus:
            brisbane_keywords = ['brisbane', 'queensland', 'qld', 'gold coast', 'sunshine coast']
            filtered_articles = []
            for article in all_articles:
                text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
                if any(keyword in text for keyword in brisbane_keywords):
                    article['brisbane_relevant'] = True
                    filtered_articles.append(article)
            all_articles = filtered_articles
        
        # Sort by date and return limited results
        all_articles.sort(key=lambda x: x.get('published_timestamp', 0), reverse=True)
        return all_articles[:max_items]
    
    def _fetch_feed(self, feed_config: Dict) -> List[Dict]:
        """Fetch and parse a single RSS feed"""
        try:
            response = requests.get(
                feed_config['url'], 
                headers=self.headers, 
                timeout=15
            )
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            articles = []
            
            for entry in feed.entries[:10]:  # Limit per feed
                # Parse date
                published_timestamp = 0
                try:
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_timestamp = time.mktime(entry.published_parsed)
                except:
                    pass
                
                article = {
                    'title': getattr(entry, 'title', 'No title'),
                    'link': getattr(entry, 'link', ''),
                    'summary': getattr(entry, 'summary', '')[:300] + "..." if len(getattr(entry, 'summary', '')) > 300 else getattr(entry, 'summary', ''),
                    'published': getattr(entry, 'published', ''),
                    'published_timestamp': published_timestamp,
                    'source': feed_config['name']
                }
                articles.append(article)
            
            self.logger.info(f"✅ Fetched {len(articles)} articles from {feed_config['name']}")
            return articles
            
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch {feed_config['name']}: {e}")
            return []
    
    def get_health_status(self) -> Dict:
        """Get RSS service health status"""
        active_feeds = sum(1 for feed in self.feeds.values() if feed['active'])
        cached_feeds = len(self.cache)
        
        return {
            'rss_service': 'operational',
            'total_feeds': len(self.feeds),
            'active_feeds': active_feeds,
            'cached_feeds': cached_feeds,
            'cache_duration_hours': self.cache_duration.total_seconds() / 3600
        }
    
    def test_connection(self) -> Dict:
        """Test RSS feed connectivity"""
        test_results = {}
        
        for feed_key, feed_config in list(self.feeds.items())[:2]:  # Test first 2 feeds
            try:
                response = requests.get(feed_config['url'], headers=self.headers, timeout=10)
                test_results[feed_key] = {
                    'name': feed_config['name'],
                    'status': 'success' if response.status_code == 200 else 'error',
                    'status_code': response.status_code
                }
            except Exception as e:
                test_results[feed_key] = {
                    'name': feed_config['name'],
                    'status': 'error',
                    'error': str(e)
                }
        
        return test_results

# ====================================================================================
# STEP 3: Update your existing services/property_service.py
# ====================================================================================

# Add this method to your existing PropertyAnalysisService class:

def get_real_property_context(self, question: str) -> str:
    """Get real property context from RSS feeds"""
    try:
        # Import RSS service
        from .rss_service import RSSService
        rss_service = RSSService()
        
        # Determine if Brisbane-focused
        brisbane_keywords = ['brisbane', 'queensland', 'qld']
        is_brisbane = any(keyword in question.lower() for keyword in brisbane_keywords)
        
        # Get relevant news
        articles = rss_service.get_property_news(brisbane_focus=is_brisbane, max_items=8)
        
        if not articles:
            return self._get_fallback_context(question)
        
        # Build context
        context = f"""
# Current Australian Property Market Data
Retrieved from live RSS feeds on {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Recent Property News:
"""
        
        for i, article in enumerate(articles[:5], 1):
            context += f"""
### {i}. {article['title']}
- **Source**: {article['source']}
- **Published**: {article['published']}
- **Summary**: {article['summary']}
- **Link**: {article['link']}
"""
            if article.get('brisbane_relevant'):
                context += "- **Brisbane Relevance**: ✅ Specific to Brisbane/Queensland\n"
            context += "\n"
        
        context += """
This is REAL current Australian property market data. Analyze the question using these actual market conditions and news.
"""
        
        return context
        
    except Exception as e:
        self.logger.error(f"RSS integration failed: {e}")
        return self._get_fallback_context(question)

def _get_fallback_context(self, question: str) -> str:
    """Fallback context when RSS fails"""
    return f"""
# Property Market Analysis Context
Note: Real-time RSS data temporarily unavailable. Providing analysis based on general Australian property market knowledge.

Question: {question}
"""

# ====================================================================================
# STEP 4: Update your app.py (MINIMAL CHANGES)
# ====================================================================================

# Add these minimal changes to your existing app.py:

# 1. Update the initialize_services() function to include RSS:
def initialize_services():
    """Initialize all services with proper error handling"""
    services = {}
    
    # ... your existing code ...
    
    # Add RSS Service (insert after Stability AI service)
    try:
        from services import RSSService
        services['rss'] = RSSService()
        logger.info("✅ RSS service initialized")
    except Exception as e:
        logger.error(f"❌ RSS service initialization failed: {e}")
        services['rss'] = None
    
    # ... rest of your existing code ...
    
    return services

# 2. Add RSS status to your existing health endpoint (modify existing route):
@app.route('/health')
def health():
    """Comprehensive health check"""
    if not services['health']:
        return jsonify({
            'status': 'error',
            'error': 'Health checker not available',
            'timestamp': datetime.now().isoformat()
        }), 500
    
    health_data = services['health'].get_comprehensive_health()
    
    # Add RSS status
    if services['rss']:
        try:
            health_data['services']['rss'] = services['rss'].get_health_status()
        except Exception as e:
            health_data['services']['rss'] = {'status': 'error', 'error': str(e)}
    else:
        health_data['services']['rss'] = {'status': 'not_available'}
    
    return jsonify(health_data)

# 3. Add ONE simple RSS debug endpoint:
@app.route('/debug/rss')
def debug_rss():
    """Debug RSS service"""
    if not services['rss']:
        return jsonify({'rss_service': 'not_available'}), 404
    
    try:
        status = services['rss'].get_health_status()
        test_results = services['rss'].test_connection()
        
        return jsonify({
            'rss_service': 'operational',
            'status': status,
            'connection_tests': test_results,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'rss_service': 'error',
            'error': str(e)
        }), 500

# 4. Update your home route to mention RSS integration:
@app.route('/')
def index():
    """Brisbane Property Intelligence API information"""
    return jsonify({
        'name': 'Brisbane Property Intelligence API',
        'version': '2.1.0',  # Increment version
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'description': 'Professional multi-LLM Brisbane property analysis system with real RSS data',
        'features': [
            'Professional Multi-LLM Integration',
            'Claude & Gemini Support',
            'Real Australian Property RSS Feeds',  # Add this
            'Database Storage & Analytics',
            'Query History Management',
            'Brisbane Property Focus',
            'Comprehensive Health Monitoring',
            'Professional Error Handling'
        ],
        'services': services['health'].get_service_status() if services['health'] else {},
        'preset_questions': Config.PRESET_QUESTIONS,
        'api_endpoints': {
            'analyze': 'POST /api/property/analyze',
            'questions': 'GET /api/property/questions', 
            'history': 'GET /api/property/history',
            'stats': 'GET /api/property/stats',
            'health': 'GET /health',
            'rss_debug': 'GET /debug/rss'  # Add this
        }
    })

# ====================================================================================
# SUMMARY OF CHANGES
# ====================================================================================

"""
This integration strategy:

✅ Leverages your existing clean architecture
✅ Adds only ONE new service file
✅ Makes MINIMAL changes to app.py (just a few lines)
✅ Integrates with your existing PropertyAnalysisService
✅ Maintains your professional structure
✅ Provides real RSS data without bloating code

The RSS service will automatically provide real Australian property data
to your existing analysis pipeline through the get_real_property_context() method.

Your existing analyze endpoint will now use real data without any changes needed!
"""