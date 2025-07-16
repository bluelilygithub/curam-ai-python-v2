"""
Professional LLM Service
Handles Claude and Gemini integration with proper error handling
"""

import os
import logging
import time
from typing import Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class LLMService:
    """Professional LLM service with multiple providers"""
    
    def __init__(self):
        self.claude_client = None
        self.gemini_model = None
        self.working_claude_model = None
        self.working_gemini_model = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients with proper error handling"""
        if Config.CLAUDE_ENABLED:
            self._init_claude()
        
        if Config.GEMINI_ENABLED:
            self._init_gemini()
    
    def _init_claude(self):
        """Initialize Claude client with working configuration"""
        try:
            if not Config.CLAUDE_API_KEY:
                logger.warning("Claude API key not configured")
                return
            
            import anthropic
            
            # Use the exact same configuration that worked in debug
            self.claude_client = anthropic.Anthropic(
                api_key=Config.CLAUDE_API_KEY.strip(),
                base_url="https://api.anthropic.com"
            )
            
            # Test connection with working models
            self._test_claude_connection()
            logger.info(f"Claude client initialized with model: {self.working_claude_model}")
            
        except Exception as e:
            logger.error(f"Claude initialization failed: {e}")
            self.claude_client = None
    
    def _init_gemini(self):
        """Initialize Gemini client with working models from your other project"""
        try:
            if not Config.GEMINI_API_KEY:
                logger.warning("Gemini API key not configured")
                return
            
            import google.generativeai as genai
            genai.configure(api_key=Config.GEMINI_API_KEY.strip())
            
            # Test with models in priority order
            for model_name in Config.GEMINI_MODELS:
                try:
                    self.gemini_model = genai.GenerativeModel(model_name)
                    self._test_gemini_connection()
                    self.working_gemini_model = model_name
                    logger.info(f"Gemini initialized with model: {model_name}")
                    break
                except Exception as e:
                    logger.warning(f"Gemini model {model_name} failed: {e}")
                    continue
            
            if not self.working_gemini_model:
                logger.error("No working Gemini models found")
                self.gemini_model = None
            
        except ImportError:
            logger.error("google-generativeai library not installed")
            self.gemini_model = None
        except Exception as e:
            logger.error(f"Gemini initialization failed: {e}")
            self.gemini_model = None
    
    def _test_claude_connection(self):
        """Test Claude connection with working model"""
        for model in Config.CLAUDE_MODELS:
            try:
                response = self.claude_client.messages.create(
                    model=model,
                    max_tokens=5,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                self.working_claude_model = model
                logger.info(f"Claude model {model} working")
                return True
            except Exception as e:
                logger.warning(f"Claude model {model} test failed: {e}")
                continue
        
        raise Exception("No working Claude models found")
    
    def _test_gemini_connection(self):
        """Test Gemini connection with minimal call"""
        response = self.gemini_model.generate_content("hi")
        return True
    
    def analyze_with_claude(self, question: str) -> Dict:
        """Analyze question with Claude using working model"""
        if not self.claude_client:
            return self._error_response("Claude client not available")
        
        try:
            prompt = self._create_brisbane_prompt(question)
            model = self.working_claude_model or Config.CLAUDE_MODELS[0]
            
            start_time = time.time()
            response = self.claude_client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'analysis': response.content[0].text,
                'model_used': model,
                'processing_time': processing_time,
                'provider': 'claude'
            }
            
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return self._error_response(f"Claude analysis failed: {str(e)}")
    
    def analyze_with_gemini(self, question: str, claude_context: str = "") -> Dict:
        """Analyze question with Gemini"""
        if not self.gemini_model:
            return self._error_response("Gemini model not available")
        
        try:
            prompt = self._create_gemini_prompt(question, claude_context)
            model = self.working_gemini_model or Config.GEMINI_MODELS[0]
            
            start_time = time.time()
            response = self.gemini_model.generate_content(prompt)
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'analysis': response.text,
                'model_used': model,
                'processing_time': processing_time,
                'provider': 'gemini'
            }
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return self._error_response(f"Gemini analysis failed: {str(e)}")
    
    def _create_brisbane_prompt(self, question: str) -> str:
        """Create Brisbane-specific prompt for initial analysis"""
        return f"""You are a Brisbane property research specialist. Analyze this question and provide insights:

Question: "{question}"

Please provide:
1. What type of property question this is (development, market, infrastructure, zoning, etc.)
2. Which specific Brisbane suburbs/areas are most relevant
3. What data sources would help answer this question
4. Key insights to look for in the data

Keep your response concise and focused specifically on Brisbane, Queensland, Australia."""
    
    def _create_gemini_prompt(self, question: str, claude_context: str) -> str:
        """Create Gemini prompt for comprehensive analysis"""
        base_prompt = f"""You are a Brisbane property market analyst. Provide a comprehensive answer to this question:

Question: "{question}"

Please provide a detailed Brisbane property market analysis that directly answers the question. Include:
- Specific Brisbane suburbs and areas
- Current market trends and data
- Investment or development implications
- Professional insights for property industry

Focus on actionable information for Brisbane property professionals."""
        
        if claude_context:
            return f"""{base_prompt}

Initial Research Context: {claude_context}

Build upon this context to provide your comprehensive analysis."""
        
        return base_prompt
    
    def _error_response(self, error_msg: str) -> Dict:
        """Standardized error response"""
        return {
            'success': False,
            'analysis': None,
            'error': error_msg,
            'processing_time': 0
        }
    
    def get_health_status(self) -> Dict:
        """Get health status of all LLM services"""
        return {
            'claude': {
                'available': self.claude_client is not None,
                'enabled': Config.CLAUDE_ENABLED,
                'working_model': self.working_claude_model,
                'api_key_configured': bool(Config.CLAUDE_API_KEY)
            },
            'gemini': {
                'available': self.gemini_model is not None,
                'enabled': Config.GEMINI_ENABLED,
                'working_model': self.working_gemini_model,
                'api_key_configured': bool(Config.GEMINI_API_KEY)
            }
        }
    
    def get_available_providers(self) -> list:
        """Get list of currently available LLM providers"""
        providers = []
        if self.claude_client:
            providers.append('claude')
        if self.gemini_model:
            providers.append('gemini')
        return providers