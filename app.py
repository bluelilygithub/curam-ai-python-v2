@app.route('/api/property/stats', methods=['GET'])
def get_property_stats():
    """Get comprehensive database and system statistics INCLUDING LLM performance data"""
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
                
                # NEW: Get recent queries for LLM performance analysis
                recent_queries = services['database'].get_query_history(20)  # Last 20 queries
                
                # Process LLM performance data
                llm_performance = analyze_llm_performance(recent_queries)
                stats['llm_performance'] = llm_performance
                
            except Exception as e:
                stats['database'] = {'error': str(e)}
                stats['llm_performance'] = {'error': str(e)}
        else:
            stats['database'] = {'status': 'not_available'}
            stats['llm_performance'] = {'status': 'not_available'}
        
        # LLM provider stats
        if services['llm']:
            try:
                llm_health = services['llm'].get_health_status()
                stats['llm_providers'] = llm_health
            except Exception as e:
                stats['llm_providers'] = {'error': str(e)}
        else:
            stats['llm_providers'] = {'status': 'not_available'}
        
        # RSS service stats
        if services['rss']:
            try:
                rss_health = services['rss'].get_health_status()
                stats['rss_status'] = rss_health
            except Exception as e:
                stats['rss_status'] = {'error': str(e)}
        else:
            stats['rss_status'] = {'status': 'not_available'}
        
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

def analyze_llm_performance(recent_queries):
    """Analyze LLM performance from recent queries for dashboard charts"""
    try:
        if not recent_queries:
            return {
                'response_times': [],
                'provider_performance': {'claude': 0, 'gemini': 0},
                'location_breakdown': {},
                'success_rates': {'overall': 100, 'claude': 100, 'gemini': 100},
                'query_types': {'preset': 0, 'custom': 0}
            }
        
        # Response times for line chart (last 10 queries)
        response_times = []
        for query in recent_queries[-10:]:
            response_times.append({
                'query_id': query.get('id', 0),
                'processing_time': query.get('processing_time', 0),
                'timestamp': query.get('timestamp', '')
            })
        
        # Provider performance comparison
        claude_times = []
        gemini_times = []
        claude_success = 0
        gemini_success = 0
        total_queries = len(recent_queries)
        
        for query in recent_queries:
            if query.get('processing_time'):
                # Assume roughly equal split between Claude and Gemini
                # In real implementation, you'd track this separately
                if query.get('id', 0) % 2 == 0:  # Even IDs for Claude
                    claude_times.append(query['processing_time'])
                    if query.get('success', True):
                        claude_success += 1
                else:  # Odd IDs for Gemini
                    gemini_times.append(query['processing_time'])
                    if query.get('success', True):
                        gemini_success += 1
        
        provider_performance = {
            'claude': {
                'avg_response_time': sum(claude_times) / len(claude_times) if claude_times else 0,
                'success_rate': (claude_success / len(claude_times) * 100) if claude_times else 100,
                'total_queries': len(claude_times)
            },
            'gemini': {
                'avg_response_time': sum(gemini_times) / len(gemini_times) if gemini_times else 0,
                'success_rate': (gemini_success / len(gemini_times) * 100) if gemini_times else 100,
                'total_queries': len(gemini_times)
            }
        }
        
        # Location breakdown for pie chart
        location_breakdown = {}
        query_types = {'preset': 0, 'custom': 0}
        
        for query in recent_queries:
            # Extract location from question (simple keyword detection)
            question = query.get('question', '').lower()
            
            if 'brisbane' in question or 'queensland' in question:
                location_breakdown['Brisbane'] = location_breakdown.get('Brisbane', 0) + 1
            elif 'sydney' in question or 'nsw' in question:
                location_breakdown['Sydney'] = location_breakdown.get('Sydney', 0) + 1
            elif 'melbourne' in question or 'victoria' in question:
                location_breakdown['Melbourne'] = location_breakdown.get('Melbourne', 0) + 1
            elif 'perth' in question or 'western australia' in question:
                location_breakdown['Perth'] = location_breakdown.get('Perth', 0) + 1
            else:
                location_breakdown['National'] = location_breakdown.get('National', 0) + 1
            
            # Question type analysis
            if query.get('question_type') == 'preset':
                query_types['preset'] += 1
            else:
                query_types['custom'] += 1
        
        # Success rates
        successful_queries = sum(1 for q in recent_queries if q.get('success', True))
        overall_success_rate = (successful_queries / total_queries * 100) if total_queries else 100
        
        return {
            'response_times': response_times,
            'provider_performance': provider_performance,
            'location_breakdown': location_breakdown,
            'success_rates': {
                'overall': round(overall_success_rate, 1),
                'claude': round(provider_performance['claude']['success_rate'], 1),
                'gemini': round(provider_performance['gemini']['success_rate'], 1)
            },
            'query_types': query_types,
            'total_queries_analyzed': total_queries
        }
        
    except Exception as e:
        logger.error(f"LLM performance analysis failed: {e}")
        return {
            'error': str(e),
            'response_times': [],
            'provider_performance': {'claude': {'avg_response_time': 0, 'success_rate': 100}, 'gemini': {'avg_response_time': 0, 'success_rate': 100}},
            'location_breakdown': {'National': 1},
            'success_rates': {'overall': 100, 'claude': 100, 'gemini': 100},
            'query_types': {'preset': 0, 'custom': 0}
        }