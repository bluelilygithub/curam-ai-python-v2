"""
Property Analysis Service
High-level service for Australian property intelligence with real RSS data
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
    
    def analyze_property_question(self, question: str) -> Dict:
        """Complete property analysis pipeline with real RSS data"""
        try:
            question_type = self._determine_question_type(question)
            
            # Stage 1: Get Real Australian Property Data
            data_sources = self._get_real_property_data_sources(question)
            rss_context = self._build_rss_context(question, data_sources)
            
            # Stage 2: Claude Analysis (Strategic Research with real data)
            claude_result = self.llm_service.analyze_with_claude(question, context=rss_context)
            
            # Stage 3: Gemini Processing (Comprehensive Analysis with real data)
            enhanced_context = self._build_enhanced_context(question, claude_result, rss_context)
            gemini_result = self.llm_service.analyze_with_gemini(
                question, 
                claude_result.get('analysis', ''),
                context=enhanced_context
            )
            
            # Stage 4: Format Final Answer
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
                    'real_data_used': bool(data_sources)
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
                logger.warning("RSS service not available, using fallback data")
                return self._get_fallback_data_sources()
            
            # Determine if question is location-specific
            question_lower = question.lower()
            brisbane_keywords = ['brisbane', 'queensland', 'qld', 'gold coast', 'sunshine coast']
            is_brisbane_focused = any(keyword in question_lower for keyword in brisbane_keywords)
            
            # Get real RSS articles
            if is_brisbane_focused:
                articles = self.rss_service.get_brisbane_news(max_articles=6)
                logger.info(f"Retrieved {len(articles)} Brisbane-specific articles")
            else:
                articles = self.rss_service.get_recent_news(max_articles=8)
                logger.info(f"Retrieved {len(articles)} Australian property articles")
            
            # Convert articles to data sources format
            data_sources = []
            for article in articles:
                data_sources.append({
                    'source': article['source'],
                    'title': article['title'],
                    'summary': article['summary'],
                    'link': article['link'],
                    'published': article['published'],
                    'type': 'rss_news',
                    'date': article['published'],
                    'relevance': 'high' if article.get('brisbane_relevant') else 'medium',
                    'real_data': True
                })
            
            return data_sources
            
        except Exception as e:
            logger.error(f"Failed to get RSS data: {e}")
            return self._get_fallback_data_sources()
    
    def _get_fallback_data_sources(self) -> List[Dict]:
        """Fallback data sources when RSS is unavailable"""
        return [{
            'source': 'Australian Property Market Analysis',
            'title': 'RSS feeds temporarily unavailable',
            'summary': 'Analysis based on general Australian property market knowledge',
            'type': 'fallback',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'relevance': 'medium',
            'real_data': False
        }]
    
    def _build_rss_context(self, question: str, data_sources: List[Dict]) -> str:
        """Build context from real RSS data for LLM analysis"""
        if not data_sources or not data_sources[0].get('real_data'):
            return """
# Australian Property Market Analysis Context
Note: Real-time RSS data is temporarily unavailable. Analysis based on general property market knowledge.
"""
        
        context = f"""
# Current Australian Property Market Data
Retrieved from live industry RSS feeds on {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Real Property News and Developments:
"""
        
        for i, source in enumerate(data_sources[:6], 1):
            context += f"""
### {i}. {source['title']}
- **Source**: {source['source']}
- **Published**: {source['published']}
- **Summary**: {source['summary']}
- **Link**: {source['link']}
"""
            if source.get('relevance') == 'high':
                context += "- **Relevance**: 🔥 High relevance to query\n"
            context += "\n"
        
        context += """
**Analysis Instructions**: This is REAL current Australian property market data from live industry RSS feeds including RealEstate.com.au, Smart Property Investment, and other authoritative sources. Provide comprehensive analysis using these actual market conditions and developments.
"""
        
        return context
    
    def _build_enhanced_context(self, question: str, claude_result: Dict, rss_context: str) -> str:
        """Build enhanced context for Gemini with Claude insights and RSS data"""
        enhanced_context = rss_context
        
        if claude_result.get('success'):
            enhanced_context += f"""

## Strategic Analysis Context (from Claude):
{claude_result.get('analysis', '')}

## Final Analysis Instructions:
Using the real Australian property market data above and the strategic analysis, provide a comprehensive, professional response that:
1. Directly answers the user's question
2. References specific information from the RSS sources
3. Provides actionable insights based on current market conditions
4. Uses a professional but accessible tone
"""
        
        return enhanced_context
    
    def _format_comprehensive_answer(self, question: str, claude_result: Dict, 
                                   gemini_result: Dict, data_sources: List[Dict], has_real_data: bool = True) -> str:
        """Format final comprehensive answer with real data attribution"""
        
        answer_parts = []
        
        # Main Analysis (Gemini if successful, otherwise Claude)
        if gemini_result['success']:
            answer_parts.append(gemini_result['analysis'])
            answer_parts.append("")
        elif claude_result['success']:
            answer_parts.append(claude_result['analysis'])
            answer_parts.append("")
        else:
            # Fallback analysis
            answer_parts.append(self._generate_fallback_answer(question))
            answer_parts.append("")
        
        # Data Sources with real attribution
        if data_sources and has_real_data:
            answer_parts.append("### Real Australian Property Data Sources")
            answer_parts.append("")
            for source in data_sources[:5]:  # Show top 5 sources
                if source.get('real_data'):
                    relevance_indicator = "🔥" if source.get('relevance') == 'high' else "📊"
                    answer_parts.append(f"- **{source['source']}** {relevance_indicator}: {source['title']}")
                    if source.get('link'):
                        answer_parts.append(f"  *Published: {source['published']}*")
            answer_parts.append("")
        elif data_sources:
            answer_parts.append("### Data Sources")
            answer_parts.append("")
            answer_parts.append("- Analysis based on general Australian property market knowledge")
            answer_parts.append("- Real-time RSS data temporarily unavailable")
            answer_parts.append("")
        
        # Processing Summary
        answer_parts.append("### AI Analysis Summary")
        answer_parts.append("")
        
        claude_status = "✅ Strategic Analysis Completed" if claude_result['success'] else "❌ Strategic Analysis Failed"
        gemini_status = "✅ Comprehensive Analysis Completed" if gemini_result['success'] else "❌ Comprehensive Analysis Failed"
        data_status = f"✅ {len(data_sources)} Real RSS Sources" if has_real_data else "⚠️ Fallback Data Used"
        
        answer_parts.append(f"- **Claude 3.5 Sonnet**: {claude_status}")
        answer_parts.append(f"- **Gemini 1.5 Flash**: {gemini_status}")
        answer_parts.append(f"- **Data Sources**: {data_status}")
        answer_parts.append(f"- **Analysis Date**: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        answer_parts.append("")
        answer_parts.append("---")
        
        if has_real_data:
            answer_parts.append("*Australian Property Intelligence - Real-time RSS data from RealEstate.com.au, Smart Property Investment, and industry sources*")
        else:
            answer_parts.append("*Australian Property Intelligence - Professional Multi-LLM Analysis System*")
        
        return "\n".join(answer_parts)
    
    def _generate_fallback_answer(self, question: str) -> str:
        """Generate enhanced fallback answer for Australian property questions"""
        question_lower = question.lower()
        
        base_response = f"""Based on general Australian property market knowledge, here's an analysis of your question:

**Current Australian Property Market Overview:**
The Australian property market shows varied performance across major cities, with strong fundamentals in key metropolitan areas and emerging growth in regional centers.

**Key National Trends:**
- Sydney and Melbourne: Established premium markets with selective growth
- Brisbane and Perth: Strong growth potential with infrastructure investment
- Adelaide and Regional Areas: Emerging opportunities with affordability focus

**Market Factors to Consider:**
- Interest rate environment and lending conditions
- Population growth and migration patterns
- Infrastructure development and transport connectivity
- Government policy and regulatory changes"""
        
        # Add question-specific insights
        if any(word in question_lower for word in ['development', 'application', 'planning']):
            base_response += f"""

**Development Activity Insights:**
Australian cities show strong development pipeline activity with focus on:
- Mixed-use developments in transit-oriented locations
- Medium-density housing in established suburbs
- Commercial developments in CBD and growth corridors"""
        
        elif any(word in question_lower for word in ['trend', 'market', 'growth']):
            base_response += f"""

**Market Trend Analysis:**
Current national trends indicate:
- Continued urbanization driving inner-city demand
- Regional growth supported by lifestyle migration
- Technology and infrastructure driving value appreciation"""
        
        elif any(word in question_lower for word in ['infrastructure', 'transport']):
            base_response += f"""

**Infrastructure Impact:**
Major infrastructure projects across Australia:
- Transport connectivity improving accessibility
- Urban renewal projects creating new precincts
- Technology infrastructure supporting modern development"""
        
        base_response += f"""

**Note**: This analysis is based on general market knowledge. For the most current data, our system typically provides real-time RSS feed analysis from RealEstate.com.au, Smart Property Investment, and other industry sources."""
        
        return base_response
    
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
            'processing_time': sum([
                analysis_result.get('claude_result', {}).get('processing_time', 0),
                analysis_result.get('gemini_result', {}).get('processing_time', 0)
            ])
        }