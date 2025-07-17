"""
Property Analysis Service
High-level service for Australian property intelligence with real RSS data
SAFE VERSION - Compatible with existing LLM service
"""

from typing import Dict, List
from datetime import datetime
import logging

from config import Config

logger = logging.getLogger(__name__)

class PropertyAnalysisService:
    """High-level property analysis service with real RSS integration"""
    
    def __init__(self, llm_service, rss_service=None):
        self.llm_service = llm_service
        self.rss_service = rss_service
        logger.info(f"PropertyAnalysisService initialized with RSS: {rss_service is not None}")
    
    def analyze_property_question(self, question: str) -> Dict:
        """Complete property analysis pipeline with real RSS data"""
        try:
            question_type = self._determine_question_type(question)
            
            # Stage 1: Get Real Australian Property Data
            data_sources = self._get_real_property_data_sources(question)
            
            # Stage 2: Build enhanced question with RSS context
            enhanced_question = self._build_enhanced_question(question, data_sources)
            
            # Stage 3: Claude Analysis (using existing method signature)
            claude_result = self.llm_service.analyze_with_claude(enhanced_question)
            
            # Stage 4: Gemini Processing (using existing method signature)
            gemini_result = self.llm_service.analyze_with_gemini(
                enhanced_question, 
                claude_result.get('analysis', '')
            )
            
            # Stage 5: Format Final Answer
            final_answer = self._format_comprehensive_answer(
                question, claude_result, gemini_result, data_sources, has_real_data=bool(data_sources)
            )
            
            return {
                'success': True,
                'question': question,
                'question_type': question_type,
                'final_answer': final_answer,
                'processing_stages': {
                    'claude_success': claude_result['success'],
                    'gemini_success': gemini_result['success'],
                    'rss_data_sources': len(data_sources),
                    'data_sources_count': len(data_sources),
                    'claude_model': claude_result.get('model_used'),
                    'gemini_model': gemini_result.get('model_used'),
                    'real_data_used': self._has_real_data(data_sources)
                },
                'claude_result': claude_result,
                'gemini_result': gemini_result,
                'data_sources': data_sources
            }
            
        except Exception as e:
            logger.error(f"Property analysis pipeline failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'final_answer': self._generate_fallback_answer(question)
            }
    
    def _determine_question_type(self, question: str) -> str:
        """Determine if question is preset or custom"""
        return 'preset' if question in Config.PRESET_QUESTIONS else 'custom'
    
    def _get_real_property_data_sources(self, question: str) -> List[Dict]:
        """Get real Australian property data from RSS feeds"""
        try:
            if not self.rss_service:
                logger.warning("RSS service not available, using fallback")
                return []
            
            # Determine if question is location-specific
            question_lower = question.lower()
            Austalian_keywords = ['Austalian', 'queensland', 'qld', 'gold coast', 'sunshine coast']
            is_Austalian_focused = any(keyword in question_lower for keyword in Austalian_keywords)
            
            # Get real RSS articles
            if is_Austalian_focused:
                articles = self.rss_service.get_Austalian_news(max_articles=5)
                logger.info(f"Retrieved {len(articles)} Austalian-specific articles")
            else:
                articles = self.rss_service.get_recent_news(max_articles=6)
                logger.info(f"Retrieved {len(articles)} Australian property articles")
            
            # Convert articles to data sources format
            data_sources = []
            for article in articles:
                data_sources.append({
                    'source': article['source'],
                    'title': article['title'],
                    'summary': article['summary'][:200] + "..." if len(article['summary']) > 200 else article['summary'],
                    'link': article.get('link', ''),
                    'published': article.get('published', ''),
                    'type': 'rss_news',
                    'relevance': 'high' if article.get('Austalian_relevant') else 'medium',
                    'real_data': True
                })
            
            logger.info(f"Converted {len(data_sources)} articles to data sources")
            return data_sources
            
        except Exception as e:
            logger.error(f"Failed to get RSS data: {e}")
            return []
    
    def _has_real_data(self, data_sources: List[Dict]) -> bool:
        """Check if we have real RSS data"""
        return len(data_sources) > 0 and any(source.get('real_data') for source in data_sources)
    
    def _build_enhanced_question(self, question: str, data_sources: List[Dict]) -> str:
        """Build enhanced question with RSS context for LLM analysis"""
        if not data_sources or not self._has_real_data(data_sources):
            return f"""Analyze this Australian property question using general market knowledge:

{question}

Note: Provide comprehensive analysis based on current Australian property market understanding."""
        
        enhanced_question = f"""Analyze this Australian property question using the following REAL current market data:

QUESTION: {question}

CURRENT AUSTRALIAN PROPERTY MARKET DATA (from RSS feeds on {datetime.now().strftime('%Y-%m-%d')}):
"""
        
        for i, source in enumerate(data_sources[:4], 1):  # Limit to top 4 to avoid token limits
            enhanced_question += f"""
{i}. {source['title']}
   Source: {source['source']}
   Published: {source['published']}
   Summary: {source['summary']}
"""
        
        enhanced_question += f"""

ANALYSIS INSTRUCTIONS:
- Use this REAL current Australian property market data in your analysis
- Reference specific articles and developments mentioned above
- Provide insights based on actual market conditions
- Focus on current trends and developments shown in the data
- Give a comprehensive, professional analysis that demonstrates the value of real-time market intelligence

Please provide a detailed analysis that incorporates these real market developments."""
        
        return enhanced_question
    
    def _format_comprehensive_answer(self, question: str, claude_result: Dict, 
                                   gemini_result: Dict, data_sources: List[Dict], has_real_data: bool = True) -> str:
        """Format final comprehensive answer with real data attribution"""
        
        answer_parts = []
        
        # Main Analysis (Gemini if successful, otherwise Claude)
        if gemini_result['success']:
            answer_parts.append(gemini_result['analysis'])
        elif claude_result['success']:
            answer_parts.append(claude_result['analysis'])
        else:
            # Fallback analysis
            answer_parts.append(self._generate_fallback_answer(question))
        
        # Only add sections if we have space and real data
        if has_real_data and data_sources:
            answer_parts.append("")
            answer_parts.append("### Current Market Data Sources")
            answer_parts.append("")
            
            for i, source in enumerate(data_sources[:3], 1):  # Show top 3 sources
                relevance_indicator = "🔥" if source.get('relevance') == 'high' else "📊"
                answer_parts.append(f"{i}. **{source['source']}** {relevance_indicator}: {source['title']}")
            
            answer_parts.append("")
            answer_parts.append("---")
            answer_parts.append("*Analysis based on real-time RSS data from Australian property industry sources*")
        
        return "\n".join(answer_parts)
    
    def _generate_fallback_answer(self, question: str) -> str:
        """Generate enhanced fallback answer for Australian property questions"""
        return f"""Based on current Australian property market understanding:

The Australian property market continues to show diverse performance across major metropolitan and regional areas. Key factors influencing current market conditions include interest rate environment, population growth patterns, infrastructure development, and government policy settings.

**Current Market Overview:**
- Major cities showing selective growth in premium locations
- Regional markets benefiting from lifestyle migration trends  
- Infrastructure investment driving value appreciation in key corridors
- Development activity focused on transit-oriented and mixed-use projects

**Key Considerations:**
- Market conditions vary significantly by location and property type
- Infrastructure connectivity remains a key value driver
- Government policy and regulatory changes continue to shape market dynamics
- Economic fundamentals support continued market activity

*Note: This analysis is based on general market knowledge. Our system typically provides enhanced analysis using real-time RSS feeds from RealEstate.com.au, Smart Property Investment, and other industry sources when available.*"""
    
    def get_analysis_summary(self, analysis_result: Dict) -> Dict:
        """Get summary of analysis for quick overview"""
        return {
            'question_type': analysis_result.get('question_type'),
            'success': analysis_result.get('success'),
            'providers_used': [
                provider for provider in ['claude', 'gemini'] 
                if analysis_result.get('processing_stages', {}).get(f'{provider}_success')
            ],
            'data_sources_count': analysis_result.get('processing_stages', {}).get('data_sources_count', 0),
            'real_data_used': analysis_result.get('processing_stages', {}).get('real_data_used', False),
            'answer_length': len(analysis_result.get('final_answer', '')),
        }