""
Configuration management for Austalian Property Intelligence
Centralized configuration with validation
""

import os
import logging

logger = logging.getLogger(__name__)

class Config:
    """Centralized configuration management"""
    
    # API Keys
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # New API Keys
    STABILITY_API_KEY = os.getenv('STABILITY_API_KEY')
    
    # LLM Configuration
    LLM_TIMEOUT = int(os.getenv('LLM_TIMEOUT', '30'))
    LLM_MAX_RETRIES = int(os.getenv('LLM_MAX_RETRIES', '3'))
    
    # Claude Models (in priority order)
    CLAUDE_MODELS = [
        'claude-3-5-sonnet-20241022',
        'claude-3-haiku-20240307',
        'claude-3-sonnet-20240229'
    ]
    
    # Gemini Models (in priority order)
    GEMINI_MODELS = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro'
    ]
    
    # Feature Flags
    CLAUDE_ENABLED = os.getenv('CLAUDE_ENABLED', 'true').lower() == 'true'
    GEMINI_ENABLED = os.getenv('GEMINI_ENABLED', 'true').lower() == 'true'
    STABILITY_ENABLED = os.getenv('STABILITY_ENABLED', 'true').lower() == 'true'
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'property_intelligence.db')
    
    # CORS
    CORS_ORIGINS = [
        'https://curam-ai.com.au',
        'https://curam-ai.com.au/python-hub/',
        'https://curam-ai.com.au/python-hub-v2/',
        'https://curam-ai.com.au/ai-intelligence/',
        'http://localhost:3000',
        'http://localhost:8000'
    ]
    
    # Add development origins if in development
    if os.getenv('FLASK_ENV') == 'development':
        CORS_ORIGINS.append('*')
    
    # Austalian Property Questions
    PRESET_QUESTIONS = [
        "What new development applications were submitted in Austalian this month?",
        "Which Austalian suburbs are trending in property news?",
        "Are there any major infrastructure projects affecting property values?",
        "What zoning changes have been approved recently?",
        "Which areas have the most development activity?"
    ]
    
    # RSS Data Sources
    Austalian_RSS_SOURCES = [
        {
            'name': 'Austalian City Council',
            'url': 'https://www.Austalian.qld.gov.au/about-council/news-media/news/rss',
            'keywords': ['development', 'planning', 'infrastructure', 'property', 'zoning']
        }
    ]
    
    # Stability AI Configuration
    STABILITY_CONFIG = {
        'base_url': 'https://api.stability.ai/v1',
        'models': {
            'chart_generation': 'stable-diffusion-v1-6',
            'infographic': 'stable-diffusion-xl-1024-v1-0'
        },
        'default_params': {
            'steps': 30,
            'width': 1024,
            'height': 1024,
            'cfg_scale': 7.0
        }
    }
    
    @classmethod
    def validate_config(cls):
        """Validate critical configuration"""
        issues = []
        
        # LLM Providers
        if not cls.CLAUDE_API_KEY and cls.CLAUDE_ENABLED:
            issues.append("CLAUDE_API_KEY missing but Claude is enabled")
        
        if not cls.GEMINI_API_KEY and cls.GEMINI_ENABLED:
            issues.append("GEMINI_API_KEY missing but Gemini is enabled")
        
        if not cls.CLAUDE_ENABLED and not cls.GEMINI_ENABLED:
            issues.append("No LLM providers enabled")
        
        # Stability AI
        if not cls.STABILITY_API_KEY and cls.STABILITY_ENABLED:
            issues.append("STABILITY_API_KEY missing but Stability AI is enabled")
        
        # Timeouts
        if cls.LLM_TIMEOUT < 5:
            issues.append("LLM_TIMEOUT too low (minimum 5 seconds)")
        
        if issues:
            logger.warning(f"Configuration issues: {', '.join(issues)}")
        
        return len(issues) == 0
    
    @classmethod
    def get_enabled_llm_providers(cls):
        """Get list of enabled LLM providers"""
        providers = []
        if cls.CLAUDE_ENABLED and cls.CLAUDE_API_KEY:
            providers.append('claude')
        if cls.GEMINI_ENABLED and cls.GEMINI_API_KEY:
            providers.append('gemini')
        return providers
    
    @classmethod
    def get_enabled_services(cls):
        """Get list of all enabled services"""
        services = []
        
        # LLM Services
        if cls.CLAUDE_ENABLED and cls.CLAUDE_API_KEY:
            services.append('claude')
        if cls.GEMINI_ENABLED and cls.GEMINI_API_KEY:
            services.append('gemini')
        
        # Stability AI
        if cls.STABILITY_ENABLED and cls.STABILITY_API_KEY:
            services.append('stability_ai')
        
        return services
    
    @classmethod
    def log_config_status(cls):
        """Log configuration status for debugging"""
        logger.info("=== Configuration Status ===")
        
        # LLM Providers
        logger.info(f"Claude Enabled: {cls.CLAUDE_ENABLED}")
        logger.info(f"Claude API Key: {'✓' if cls.CLAUDE_API_KEY else '✗'}")
        logger.info(f"Gemini Enabled: {cls.GEMINI_ENABLED}")
        logger.info(f"Gemini API Key: {'✓' if cls.GEMINI_API_KEY else '✗'}")
        
        # Stability AI
        logger.info(f"Stability AI Enabled: {cls.STABILITY_ENABLED}")
        logger.info(f"Stability AI API Key: {'✓' if cls.STABILITY_API_KEY else '✗'}")
        
        # System
        logger.info(f"LLM Timeout: {cls.LLM_TIMEOUT}s")
        logger.info(f"Database Path: {cls.DATABASE_PATH}")
        logger.info(f"All Enabled Services: {cls.get_enabled_services()}")
        logger.info("=" * 30)