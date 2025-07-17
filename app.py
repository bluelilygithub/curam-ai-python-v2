"""
Brisbane Property Intelligence API
Professional Flask application with clean architecture
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import logging
import time
from datetime import datetime

# Import professional services
from config import Config
from services import LLMService, PropertyAnalysisService
from database import PropertyDatabase
from utils import HealthChecker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS
CORS(app, origins=Config.CORS_ORIGINS)

# Update your initialize_services() function in app.py:

def initialize_services():
    """Initialize all services with proper error handling"""
    services = {}
    
    # Log configuration status
    Config.log_config_status()
    
    # Database
    try:
        services['database'] = PropertyDatabase(Config.DATABASE_PATH)
        logger.info("✅ Database service initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        services['database'] = None
    
    # LLM Service
    try:
        services['llm'] = LLMService()
        logger.info("✅ LLM service initialized")
    except Exception as e:
        logger.error(f"❌ LLM service initialization failed: {e}")
        services['llm'] = None
    
    # RSS Service for Australian Property Data (MOVE THIS UP)
    try:
        from services.rss_service import RSSService
        services['rss'] = RSSService()
        logger.info("✅ RSS service initialized")
    except Exception as e:
        logger.error(f"❌ RSS service initialization failed: {e}")
        services['rss'] = None
    
    # Property Analysis Service (UPDATED - now receives RSS service)
    if services['llm']:
        try:
            services['property'] = PropertyAnalysisService(services['llm'], services['rss'])  # Pass RSS service
            logger.info("✅ Property analysis service initialized")
        except Exception as e:
            logger.error(f"❌ Property service initialization failed: {e}")
            services['property'] = None
    else:
        services['property'] = None
    
    # Stability AI Service
    try:
        from services import StabilityService
        services['stability'] = StabilityService()
        logger.info("✅ Stability AI service initialized")
    except Exception as e:
        logger.error(f"❌ Stability service initialization failed: {e}")
        services['stability'] = None
    
    # Health Checker
    try:
        services['health'] = HealthChecker(services)
        logger.info("✅ Health checker initialized")
    except Exception as e:
        logger.error(f"❌ Health checker initialization failed: {e}")
        services['health'] = None
    
    # Log service summary
    available_services = [name for name, service in services.items() if service is not None]
    logger.info(f"🚀 Services initialized: {', '.join(available_services)}")
    
    return services

# Initialize services
services = initialize_services()


#--------------------------------------

@app.route('/debug/claude')
def debug_claude():
    """Debug Claude with proxy handling"""
    import traceback
    import sys
    import os
    
    debug_info = []
    debug_info.append("=== CLAUDE DEBUG INFO ===")
    debug_info.append(f"Python version: {sys.version}")
    
    try:
        import anthropic
        debug_info.append(f"Anthropic version: {anthropic.__version__}")
        
        # Check for proxy environment variables
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for var in proxy_vars:
            if os.getenv(var):
                debug_info.append(f"Found proxy: {var}={os.getenv(var)}")
        
        # Test API key
        api_key = Config.CLAUDE_API_KEY
        debug_info.append(f"API key configured: {'Yes' if api_key else 'No'}")
        
        # Try with explicit proxy handling
        client = anthropic.Anthropic(
            api_key=api_key,
            base_url="https://api.anthropic.com",
        )
        debug_info.append("Client created successfully")
        
        # Test minimal request
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=5,
            messages=[{"role": "user", "content": "Hi"}]
        )
        debug_info.append(f"Test successful: {response.content[0].text}")
        
    except Exception as e:
        debug_info.append(f"ERROR: {type(e).__name__}: {str(e)}")
        debug_info.append(f"Traceback: {traceback.format_exc()}")
    
    return "<pre>" + "\n".join(debug_info) + "</pre>"

@app.route('/debug/services')
def debug_services():
    """Debug service initialization"""
    import traceback
    
    debug_info = []
    debug_info.append("=== SERVICE DEBUG ===")
    
    try:
        # Test LLM Service directly
        debug_info.append("Testing LLM Service...")
        from services import LLMService
        
        llm_service = LLMService()
        debug_info.append(f"LLM Service created: {llm_service is not None}")
        
        if llm_service:
            debug_info.append(f"Claude client: {llm_service.claude_client is not None}")
            debug_info.append(f"Gemini model: {llm_service.gemini_model is not None}")
            debug_info.append(f"Working Claude model: {llm_service.working_claude_model}")
            debug_info.append(f"Working Gemini model: {llm_service.working_gemini_model}")
            
            # Test health status
            health_status = llm_service.get_health_status()
            debug_info.append(f"Health status: {health_status}")
        
        # Test Property Service
        debug_info.append("\nTesting Property Service...")
        from services import PropertyAnalysisService
        
        if llm_service:
            property_service = PropertyAnalysisService(llm_service)
            debug_info.append(f"Property Service created: {property_service is not None}")
        else:
            debug_info.append("Property Service: Cannot create without LLM service")
        
    except Exception as e:
        debug_info.append(f"ERROR: {type(e).__name__}: {str(e)}")
        debug_info.append(f"Traceback: {traceback.format_exc()}")
    
    return "<pre>" + "\n".join(debug_info) + "</pre>"

@app.route('/debug/stability')
def debug_stability():
    """Debug Stability AI service"""
    import traceback
    
    debug_info = []
    debug_info.append("=== STABILITY AI DEBUG ===")
    
    try:
        # Test Stability Service
        debug_info.append("Testing Stability AI Service...")
        from services import StabilityService
        
        stability_service = StabilityService()
        debug_info.append(f"Stability Service created: {stability_service is not None}")
        
        if stability_service:
            debug_info.append(f"Enabled: {stability_service.enabled}")
            debug_info.append(f"API Key configured: {bool(stability_service.api_key)}")
            debug_info.append(f"Base URL: {stability_service.base_url}")
            debug_info.append(f"Models available: {list(stability_service.models.keys())}")
            
            # Test health status
            health_status = stability_service.get_health_status()
            debug_info.append(f"Health status: {health_status}")
            
            # Test connection (if enabled)
            if stability_service.enabled:
                debug_info.append("\nTesting API connection...")
                connection_test = stability_service.test_connection()
                debug_info.append(f"Connection test: {connection_test}")
            else:
                debug_info.append("Connection test skipped - service not enabled")
        
    except Exception as e:
        debug_info.append(f"ERROR: {type(e).__name__}: {str(e)}")
        debug_info.append(f"Traceback: {traceback.format_exc()}")
    
    return "<pre>" + "\n".join(debug_info) + "</pre>"

@app.route('/debug/rss')
def debug_rss():
    """Debug RSS service"""
    import traceback
    
    debug_info = []
    debug_info.append("=== RSS SERVICE DEBUG ===")
    
    try:
        # Test feedparser import
        import feedparser
        debug_info.append(f"✅ feedparser available: {getattr(feedparser, '__version__', 'unknown')}")
        
        # Test requests import
        import requests
        debug_info.append(f"✅ requests available: {getattr(requests, '__version__', 'unknown')}")
        
        # Test RSS service
        if services.get('rss'):
            debug_info.append("✅ RSS service initialized")
            
            # Test health status
            health_status = services['rss'].get_health_status()
            debug_info.append(f"Health status: {health_status}")
            
            # Test connection
            debug_info.append("\nTesting RSS feed connections...")
            connection_test = services['rss'].test_connection()
            debug_info.append(f"Connection test: {connection_test}")
            
            # Get sample news
            debug_info.append("\nFetching sample news...")
            sample_news = services['rss'].get_recent_news(max_articles=3)
            debug_info.append(f"Sample articles fetched: {len(sample_news)}")
            
            for i, article in enumerate(sample_news[:2], 1):
                debug_info.append(f"  {i}. {article['title'][:60]}... (from {article['source']})")
                
        else:
            debug_info.append("❌ RSS service not available")
        
    except Exception as e:
        debug_info.append(f"ERROR: {type(e).__name__}: {str(e)}")
        debug_info.append(f"Traceback: {traceback.format_exc()}")
    
    return "<pre>" + "\n".join(debug_info) + "</pre>"

    
#---------------------------------------

@app.route('/')
def index():
    """Australian Property Intelligence API information"""
    return jsonify({
        'name': 'Australian Property Intelligence API',  # Changed from Brisbane
        'version': '2.1.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'description': 'Professional multi-LLM Australian property analysis system with real RSS data',  # Updated
        'features': [
            'Professional Multi-LLM Integration',
            'Claude & Gemini Support',
            'Real Australian Property RSS Feeds',
            'Database Storage & Analytics',
            'Query History Management',
            'Australian Property Market Focus',  # Changed from Brisbane
            'Comprehensive Health Monitoring',
            'Professional Error Handling'
        ],
        'services': services['health'].get_service_status() if services['health'] else {},
        'preset_questions': Config.PRESET_QUESTIONS,  # Will use new national questions
        'api_endpoints': {
            'analyze': 'POST /api/property/analyze',
            'questions': 'GET /api/property/questions',
            'history': 'GET /api/property/history',
            'stats': 'GET /api/property/stats',
            'health': 'GET /health',
            'rss_debug': 'GET /debug/rss'
        }
    })

@app.route('/health')
def health():
    """Comprehensive health check"""
    if not services['health']:
        return jsonify({
            'status': 'error',
            'error': 'Health checker not available',
            'timestamp': datetime.now().isoformat()
        }), 500
    
    return jsonify(services['health'].get_comprehensive_health())

@app.route('/health/deep', methods=['GET'])
def deep_health_check():
    """Deep health check with actual API tests"""
    if not services['health']:
        return jsonify({
            'status': 'error',
            'error': 'Health checker not available'
        }), 500
    
    return jsonify(services['health'].perform_deep_health_check())

@app.route('/api/property/questions', methods=['GET'])
def get_property_questions():
    """Get preset and popular questions"""
    try:
        questions = []
        
        # Add preset questions
        for question in Config.PRESET_QUESTIONS:
            questions.append({
                'question': question,
                'type': 'preset',
                'count': 0
            })
        
        # Add popular questions from database
        if services['database']:
            try:
                popular = services['database'].get_popular_questions(5)
                for item in popular:
                    if item['question'] not in Config.PRESET_QUESTIONS:
                        questions.append({
                            'question': item['question'],
                            'type': 'popular',
                            'count': item['count']
                        })
            except Exception as e:
                logger.error(f"Failed to get popular questions: {e}")
        
        return jsonify({
            'success': True,
            'questions': questions,
            'preset_questions': Config.PRESET_QUESTIONS,
            'total_count': len(questions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get questions error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/property/analyze', methods=['POST'])
def analyze_property_question():
    """Analyze Brisbane property question using professional pipeline"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body must be JSON'
            }), 400
        
        question = data.get('question', '').strip()
        if not question:
            return jsonify({
                'success': False,
                'error': 'Question is required'
            }), 400
        
        if not services['property']:
            return jsonify({
                'success': False,
                'error': 'Property analysis service not available',
                'details': 'LLM services may not be configured correctly'
            }), 500
        
        logger.info(f"🔍 Processing property question: {question}")
        start_time = time.time()
        
        # Use professional property analysis service
        result = services['property'].analyze_property_question(question)
        processing_time = time.time() - start_time
        
        # Store in database if available
        query_id = None
        if services['database'] and result['success']:
            try:
                query_id = services['database'].store_query(
                    question=question,
                    answer=result['final_answer'],
                    question_type=result['question_type'],
                    processing_time=processing_time,
                    success=result['success']
                )
                logger.info(f"💾 Query stored with ID: {query_id}")
            except Exception as e:
                logger.error(f"Failed to store query: {e}")
        
        # Add summary for quick overview
        analysis_summary = services['property'].get_analysis_summary(result) if services['property'] else {}
        
        response = {
            'success': result['success'],
            'question': question,
            'question_type': result['question_type'],
            'answer': result['final_answer'],
            'processing_time': round(processing_time, 2),
            'query_id': query_id,
            'processing_stages': result['processing_stages'],
            'analysis_summary': analysis_summary,
            'timestamp': datetime.now().isoformat()
        }
        
        # Include detailed results if requested
        if data.get('include_details'):
            response['detailed_results'] = {
                'claude_result': result.get('claude_result'),
                'gemini_result': result.get('gemini_result'),
                'data_sources': result.get('data_sources')
            }
        
        logger.info(f"✅ Analysis completed in {processing_time:.2f}s")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Property analysis error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/property/history', methods=['GET'])
def get_property_history():
    """Get query history from database"""
    if not services['database']:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 500
    
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validate parameters
        if limit > 1000:
            limit = 1000
        if limit < 1:
            limit = 10
        
        history = services['database'].get_query_history(limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history),
            'limit': limit,
            'offset': offset,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get history error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/property/stats', methods=['GET'])
def get_property_stats():
    """Get comprehensive database and system statistics"""
    try:
        stats = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'version': '2.1.0',
                'python_version': sys.version.split()[0],
                'uptime': 'N/A'  # Could implement uptime tracking
            }
        }
        
        # Database stats
        if services['database']:
            try:
                db_stats = services['database'].get_database_stats()
                stats['database'] = db_stats
            except Exception as e:
                stats['database'] = {'error': str(e)}
        else:
            stats['database'] = {'status': 'not_available'}
        
        # LLM provider stats
        if services['llm']:
            try:
                llm_health = services['llm'].get_health_status()
                stats['llm_providers'] = llm_health
            except Exception as e:
                stats['llm_providers'] = {'error': str(e)}
        else:
            stats['llm_providers'] = {'status': 'not_available'}
        
        # Configuration stats
        stats['configuration'] = {
            'enabled_providers': Config.get_enabled_llm_providers(),
            'preset_questions_count': len(Config.PRESET_QUESTIONS),
            'timeout_settings': {
                'llm_timeout': Config.LLM_TIMEOUT,
                'max_retries': Config.LLM_MAX_RETRIES
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/property/reset', methods=['POST'])
def reset_property_database():
    """Reset database (clear all queries)"""
    if not services['database']:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 500
    
    try:
        # Get current stats before reset
        pre_reset_stats = services['database'].get_database_stats()
        
        # Perform reset
        services['database'].clear_all_data()
        
        logger.info(f"🗑️ Database reset completed. Cleared {pre_reset_stats.get('total_queries', 0)} queries")
        
        return jsonify({
            'success': True,
            'message': 'Database reset successfully',
            'cleared_queries': pre_reset_stats.get('total_queries', 0),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Reset database error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'GET /health',
            'GET /api/property/questions',
            'POST /api/property/analyze',
            'GET /api/property/history',
            'GET /api/property/stats',
            'POST /api/property/reset'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'timestamp': datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    # Validate configuration before starting
    if not Config.validate_config():
        logger.warning("⚠️ Configuration validation failed - some features may not work")
    
    # Start the application
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"🚀 Starting Australian Property Intelligence API v2.1")  # Changed from Brisbane
    logger.info(f"📡 Port: {port}")
    logger.info(f"🔧 Debug: {debug_mode}")
    logger.info(f"🤖 Available LLM providers: {Config.get_enabled_llm_providers()}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)