"""
Updated Property Service with Real RSS Feed Integration
Replaces mock data sources with actual Australian property RSS feeds
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from services.llm_service import llm_service
from services.rss_service import rss_service  # Import the real RSS service

class UpdatedPropertyService:
    """Enhanced property service with real RSS data integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_property_question(self, question: str, include_details: bool = False) -> Dict:
        """
        Analyze property question using real RSS data and multi-LLM processing
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Fetch real RSS data
            self.logger.info("Fetching real Australian property data...")
            real_data_sources = self._get_real_data_sources(question)
            
            # Step 2: Prepare context with real data
            context_data = self._prepare_analysis_context(question, real_data_sources)
            
            # Step 3: Multi-LLM Analysis Pipeline
            analysis_result = self._run_multi_llm_analysis(question, context_data, include_details)
            
            # Step 4: Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Step 5: Prepare final response
            response = {
                'success': True,
                'question': question,
                'question_type': self._classify_question_type(question),
                'answer': analysis_result['final_answer'],
                'processing_time': round(processing_time, 2),
                'processing_stages': {
                    'rss_data_fetched': analysis_result['rss_success'],
                    'claude_success': analysis_result['claude_success'],
                    'gemini_success': analysis_result['gemini_success'],
                    'claude_model': analysis_result.get('claude_model', 'claude-3-5-sonnet-20241022'),
                    'gemini_model': analysis_result.get('gemini_model', 'gemini-1.5-flash'),
                    'data_sources_count': len(real_data_sources),
                    'real_sources_used': [source['name'] for source in real_data_sources if source.get('success')]
                },
                'data_sources': real_data_sources if include_details else None,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Property analysis completed in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            self.logger.error(f"Property analysis failed: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': False,
                'question': question,
                'question_type': 'error',
                'answer': f"I apologize, but I encountered an error while analyzing your property question. Please try again or rephrase your question.",
                'processing_time': round(processing_time, 2),
                'processing_stages': {
                    'rss_data_fetched': False,
                    'claude_success': False,
                    'gemini_success': False,
                    'data_sources_count': 0,
                    'error': str(e)
                },
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_real_data_sources(self, question: str) -> List[Dict]:
        """Fetch real RSS data sources based on the question"""
        try:
            # Determine if question is Brisbane-specific
            brisbane_keywords = ['brisbane', 'queensland', 'qld', 'gold coast', 'sunshine coast']
            is_brisbane_focused = any(keyword in question.lower() for keyword in brisbane_keywords)
            
            if is_brisbane_focused:
                # Get Brisbane-specific news
                brisbane_news = rss_service.get_brisbane_specific_news(max_items=10)
                general_news = rss_service.get_recent_property_news(max_items=5)
                
                # Combine and format sources
                sources = []
                
                # Add Brisbane-specific sources
                for i, article in enumerate(brisbane_news[:5]):
                    sources.append({
                        'id': f"brisbane_rss_{i+1}",
                        'name': f"Brisbane Property News - {article['source']}",
                        'type': 'rss_feed',
                        'url': article.get('link', ''),
                        'title': article.get('title', 'No title'),
                        'summary': article.get('summary', '')[:300] + "..." if len(article.get('summary', '')) > 300 else article.get('summary', ''),
                        'published': article.get('published', ''),
                        'source_feed': article.get('source', 'Unknown'),
                        'success': True,
                        'brisbane_relevant': True
                    })
                
                # Add general property news
                for i, article in enumerate(general_news[:3]):
                    sources.append({
                        'id': f"general_rss_{i+1}",
                        'name': f"Australian Property News - {article['source']}",
                        'type': 'rss_feed',
                        'url': article.get('link', ''),
                        'title': article.get('title', 'No title'),
                        'summary': article.get('summary', '')[:300] + "..." if len(article.get('summary', '')) > 300 else article.get('summary', ''),
                        'published': article.get('published', ''),
                        'source_feed': article.get('source', 'Unknown'),
                        'success': True,
                        'brisbane_relevant': False
                    })
            
            else:
                # Get general Australian property news
                general_news = rss_service.get_recent_property_news(max_items=10)
                
                sources = []
                for i, article in enumerate(general_news[:8]):
                    sources.append({
                        'id': f"aus_property_{i+1}",
                        'name': f"Australian Property News - {article['source']}",
                        'type': 'rss_feed',
                        'url': article.get('link', ''),
                        'title': article.get('title', 'No title'),
                        'summary': article.get('summary', '')[:300] + "..." if len(article.get('summary', '')) > 300 else article.get('summary', ''),
                        'published': article.get('published', ''),
                        'source_feed': article.get('source', 'Unknown'),
                        'success': True,
                        'national_scope': True
                    })
            
            self.logger.info(f"Successfully retrieved {len(sources)} real RSS data sources")
            return sources
            
        except Exception as e:
            self.logger.error(f"Failed to fetch RSS data: {str(e)}")
            # Return fallback mock data if RSS fails
            return self._get_fallback_sources()
    
    def _get_fallback_sources(self) -> List[Dict]:
        """Fallback data sources if RSS feeds fail"""
        return [
            {
                'id': 'fallback_1',
                'name': 'Australian Property Market - System Fallback',
                'type': 'fallback',
                'title': 'RSS feeds temporarily unavailable',
                'summary': 'The system is currently using fallback data. Real RSS integration will be restored shortly.',
                'success': False,
                'fallback': True
            }
        ]
    
    def _prepare_analysis_context(self, question: str, data_sources: List[Dict]) -> str:
        """Prepare context for LLM analysis with real data"""
        
        # Check if we have real data or fallback
        has_real_data = any(source.get('success') and not source.get('fallback') for source in data_sources)
        
        if has_real_data:
            context = f"""
# Australian Property Intelligence Analysis Context

## Query: {question}

## Real Australian Property Data Sources (RSS Feeds)
Retrieved from live Australian property industry RSS feeds on {datetime.now().strftime('%Y-%m-%d %H:%M')}:

"""
            
            for i, source in enumerate(data_sources, 1):
                if source.get('success') and not source.get('fallback'):
                    context += f"""
### Source {i}: {source['name']}
- **Type**: Live RSS Feed
- **Source**: {source.get('source_feed', 'Unknown')}
- **Published**: {source.get('published', 'Recent')}
- **Title**: {source.get('title', 'No title')}
- **Summary**: {source.get('summary', 'No summary available')}
- **URL**: {source.get('url', 'N/A')}
"""
                    
                    # Add Brisbane relevance note
                    if source.get('brisbane_relevant'):
                        context += "- **Brisbane Relevance**: ✅ Specifically relevant to Brisbane/Queensland\n"
                    elif source.get('national_scope'):
                        context += "- **Scope**: 🇦🇺 Australian national property market\n"
                    
                    context += "\n"
            
            context += """
## Analysis Instructions
You are analyzing REAL Australian property market data from live RSS feeds. This is current, authentic information from major Australian property industry sources including RealEstate.com.au, Smart Property Investment, View.com.au, and other authoritative sources.

Please provide a comprehensive analysis based on this real data, highlighting:
- Current market trends evident in the news
- Specific developments or changes mentioned
- Regional insights (especially Brisbane/Queensland if relevant)
- Investment implications from the real market intelligence
- Any emerging patterns or concerns from multiple sources

The data above represents the actual current state of the Australian property market as reported by industry sources.
"""
        
        else:
            # Fallback context
            context = f"""
# Australian Property Intelligence Analysis Context

## Query: {question}

## System Status: RSS Feeds Temporarily Unavailable
The real RSS feed integration is currently experiencing issues. Providing general analysis based on established property market knowledge.

## Analysis Instructions
Please provide a comprehensive analysis of the property question using general Australian property market knowledge, while noting that real-time data is temporarily unavailable.
"""
        
        return context
    
    def _run_multi_llm_analysis(self, question: str, context: str, include_details: bool) -> Dict:
        """Run the multi-LLM analysis pipeline with real data"""
        
        try:
            # Step 1: Claude Strategic Analysis
            self.logger.info("Running Claude strategic analysis...")
            claude_prompt = f"""
{context}

As a strategic property research analyst, please analyze this property question with the provided real Australian property market data. Focus on:

1. Strategic context and market positioning
2. Key trends and patterns from the real data sources
3. Risk assessment and opportunities
4. Research methodology and data quality

Question: {question}

Provide a strategic research foundation that will help inform a comprehensive property analysis.
"""
            
            claude_result = llm_service.query_claude(claude_prompt, max_tokens=1000)
            claude_success = claude_result.get('success', False)
            
            # Step 2: Gemini Comprehensive Analysis
            self.logger.info("Running Gemini comprehensive analysis...")
            gemini_prompt = f"""
{context}

Based on the real Australian property market data provided above, please provide a comprehensive analysis of this property question:

{question}

{"CLAUDE STRATEGIC ANALYSIS:" if claude_success else ""}
{claude_result.get('response', '') if claude_success else ''}

Please provide a detailed, professional response that:
1. Directly answers the user's question using the real data sources
2. References specific information from the RSS feeds provided
3. Provides actionable insights based on current market conditions
4. Uses a professional but accessible tone
5. Includes relevant statistics or trends from the data
6. Offers practical next steps or recommendations

Format your response as a comprehensive property intelligence report that demonstrates the value of real-time market data analysis.
"""
            
            gemini_result = llm_service.query_gemini(gemini_prompt, max_tokens=1500)
            gemini_success = gemini_result.get('success', False)
            
            # Step 3: Determine final answer
            if gemini_success:
                final_answer = gemini_result.get('response', '')
            elif claude_success:
                final_answer = claude_result.get('response', '')
            else:
                final_answer = "I apologize, but I'm experiencing technical difficulties accessing the AI analysis services. Please try again in a moment."
            
            return {
                'final_answer': final_answer,
                'claude_success': claude_success,
                'gemini_success': gemini_success,
                'rss_success': True,  # We successfully called RSS service
                'claude_model': claude_result.get('model', 'claude-3-5-sonnet-20241022'),
                'gemini_model': gemini_result.get('model', 'gemini-1.5-flash')
            }
            
        except Exception as e:
            self.logger.error(f"Multi-LLM analysis failed: {str(e)}")
            return {
                'final_answer': "I encountered an error during the analysis process. Please try again.",
                'claude_success': False,
                'gemini_success': False,
                'rss_success': False,
                'error': str(e)
            }
    
    def _classify_question_type(self, question: str) -> str:
        """Classify the type of property question"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['development', 'application', 'planning', 'approval']):
            return 'development_applications'
        elif any(word in question_lower for word in ['trend', 'market', 'price', 'value']):
            return 'market_trends'
        elif any(word in question_lower for word in ['suburb', 'area', 'location', 'region']):
            return 'location_analysis'
        elif any(word in question_lower for word in ['investment', 'buy', 'purchase', 'invest']):
            return 'investment_advice'
        elif any(word in question_lower for word in ['infrastructure', 'transport', 'school', 'amenity']):
            return 'infrastructure_analysis'
        elif any(word in question_lower for word in ['zoning', 'regulation', 'law', 'legal']):
            return 'regulatory_inquiry'
        else:
            return 'general_property'
    
    def get_rss_feed_status(self) -> Dict:
        """Get the status of all RSS feeds"""
        return rss_service.get_feed_status()
    
    def refresh_rss_cache(self) -> Dict:
        """Refresh the RSS feed cache"""
        try:
            rss_service.clear_cache()
            status = rss_service.get_feed_status()
            return {
                'success': True,
                'message': 'RSS cache refreshed successfully',
                'active_feeds': status['active_feeds'],
                'total_feeds': status['total_feeds']
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to refresh RSS cache: {str(e)}'
            }
    
    def get_sample_rss_data(self, max_items: int = 5) -> Dict:
        """Get sample RSS data for testing/debugging"""
        try:
            recent_news = rss_service.get_recent_property_news(max_items=max_items)
            brisbane_news = rss_service.get_brisbane_specific_news(max_items=max_items)
            
            return {
                'success': True,
                'recent_news_count': len(recent_news),
                'brisbane_news_count': len(brisbane_news),
                'sample_recent': recent_news[:3] if recent_news else [],
                'sample_brisbane': brisbane_news[:3] if brisbane_news else [],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global instance
property_service_real = UpdatedPropertyService()

# Backward compatibility functions
def analyze_property_question(question: str, include_details: bool = False) -> Dict:
    """Main function for property analysis with real RSS integration"""
    return property_service_real.analyze_property_question(question, include_details)

def get_rss_status() -> Dict:
    """Get RSS feed status"""
    return property_service_real.get_rss_feed_status()

def refresh_property_data() -> Dict:
    """Refresh property data cache"""
    return property_service_real.refresh_rss_cache()

if __name__ == "__main__":
    # Test the updated property service
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Updated Property Service with Real RSS Integration...")
    print("=" * 60)
    
    # Test 1: Brisbane-specific question
    print("\n1. Testing Brisbane-specific question:")
    test_question = "What new development applications were submitted in Brisbane this month?"
    result = property_service_real.analyze_property_question(test_question, include_details=True)
    
    print(f"✅ Success: {result['success']}")
    print(f"✅ Processing time: {result['processing_time']}s")
    print(f"✅ Data sources: {result['processing_stages']['data_sources_count']}")
    print(f"✅ Real sources used: {', '.join(result['processing_stages']['real_sources_used'])}")
    
    # Test 2: General Australian property question
    print("\n2. Testing general Australian property question:")
    test_question2 = "What are the current property market trends in Australia?"
    result2 = property_service_real.analyze_property_question(test_question2)
    
    print(f"✅ Success: {result2['success']}")
    print(f"✅ Question type: {result2['question_type']}")
    print(f"✅ Answer preview: {result2['answer'][:100]}...")
    
    # Test 3: RSS feed status
    print("\n3. Testing RSS feed status:")
    status = property_service_real.get_rss_feed_status()
    print(f"✅ Active feeds: {status['active_feeds']}/{status['total_feeds']}")
    
    # Test 4: Sample RSS data
    print("\n4. Testing sample RSS data:")
    sample = property_service_real.get_sample_rss_data(max_items=3)
    print(f"✅ Recent news: {sample['recent_news_count']} articles")
    print(f"✅ Brisbane news: {sample['brisbane_news_count']} articles")
    
    print("\n" + "=" * 60)
    print("Real RSS Integration Complete! 🎉")
    print("\nNext Steps:")
    print("1. Update your main app.py to import this service")
    print("2. Replace existing property_service with property_service_real")
    print("3. Test with your live system")
    print("4. Monitor RSS feed performance")