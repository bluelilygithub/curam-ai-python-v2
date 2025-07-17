// LLM Dashboard JavaScript with Chart.js
class LLMDashboard {
    constructor() {
        this.charts = {};
        this.updateInterval = null;
        this.isProcessing = false;
        
        // Initialize dashboard when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    init() {
        console.log('🚀 Initializing LLM Dashboard...');
        this.setupCharts();
        this.loadInitialData();
        this.startAutoUpdate();
        
        // Hook into existing search function to show real-time processing
        this.hookIntoSearchFunction();
    }
    
    setupCharts() {
        // Response Times Line Chart
        this.charts.responseTimes = new Chart(
            document.getElementById('responseTimesChart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Response Time (seconds)',
                        data: [],
                        borderColor: '#4f46e5',
                        backgroundColor: 'rgba(79, 70, 229, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Seconds'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Recent Queries'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            }
        );
        
        // Provider Performance Bar Chart
        this.charts.providerPerformance = new Chart(
            document.getElementById('providerPerformanceChart').getContext('2d'),
            {
                type: 'bar',
                data: {
                    labels: ['Claude', 'Gemini'],
                    datasets: [
                        {
                            label: 'Avg Response Time (s)',
                            data: [0, 0],
                            backgroundColor: ['#059669', '#dc2626'],
                            borderColor: ['#047857', '#b91c1c'],
                            borderWidth: 1,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Success Rate (%)',
                            data: [100, 100],
                            backgroundColor: ['rgba(5, 150, 105, 0.3)', 'rgba(220, 38, 38, 0.3)'],
                            borderColor: ['#047857', '#b91c1c'],
                            borderWidth: 1,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Response Time (s)'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Success Rate (%)'
                            },
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom'
                        }
                    }
                }
            }
        );
        
        // Location Distribution Pie Chart
        this.charts.locationDistribution = new Chart(
            document.getElementById('locationDistributionChart').getContext('2d'),
            {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#4f46e5',  // National - Blue
                            '#059669',  // Brisbane - Green
                            '#dc2626',  // Sydney - Red
                            '#f59e0b',  // Melbourne - Yellow
                            '#7c3aed',  // Perth - Purple
                        ],
                        borderColor: '#ffffff',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom',
                            labels: {
                                font: {
                                    size: 11
                                }
                            }
                        }
                    }
                }
            }
        );
        
        console.log('✅ Charts initialized successfully');
    }
    
    async loadInitialData() {
        try {
            console.log('📊 Loading initial dashboard data...');
            const response = await fetch('/api/property/stats');
            const data = await response.json();
            
            if (data.success && data.stats.llm_performance) {
                this.updateDashboard(data.stats);
                console.log('✅ Initial data loaded');
            } else {
                console.warn('⚠️ No LLM performance data available');
                this.showNoDataState();
            }
        } catch (error) {
            console.error('❌ Failed to load initial data:', error);
            this.showErrorState();
        }
    }
    
    updateDashboard(stats) {
        const llmPerf = stats.llm_performance;
        
        // Update Response Times Chart
        if (llmPerf.response_times && llmPerf.response_times.length > 0) {
            const labels = llmPerf.response_times.map((_, index) => `Q${index + 1}`);
            const times = llmPerf.response_times.map(q => q.processing_time);
            
            this.charts.responseTimes.data.labels = labels;
            this.charts.responseTimes.data.datasets[0].data = times;
            this.charts.responseTimes.update('none');
        }
        
        // Update Provider Performance Chart
        if (llmPerf.provider_performance) {
            const claude = llmPerf.provider_performance.claude;
            const gemini = llmPerf.provider_performance.gemini;
            
            this.charts.providerPerformance.data.datasets[0].data = [
                claude.avg_response_time || 0,
                gemini.avg_response_time || 0
            ];
            this.charts.providerPerformance.data.datasets[1].data = [
                claude.success_rate || 100,
                gemini.success_rate || 100
            ];
            this.charts.providerPerformance.update('none');
        }
        
        // Update Location Distribution Chart
        if (llmPerf.location_breakdown) {
            const locations = Object.keys(llmPerf.location_breakdown);
            const counts = Object.values(llmPerf.location_breakdown);
            
            this.charts.locationDistribution.data.labels = locations;
            this.charts.locationDistribution.data.datasets[0].data = counts;
            this.charts.locationDistribution.update('none');
        }
        
        // Update System Metrics
        this.updateSystemMetrics(stats);
    }
    
    updateSystemMetrics(stats) {
        const llmPerf = stats.llm_performance;
        const rssStatus = stats.rss_status;
        
        // Success Rate
        const successRateEl = document.getElementById('success-rate');
        if (successRateEl && llmPerf.success_rates) {
            successRateEl.textContent = `${llmPerf.success_rates.overall}%`;
            successRateEl.className = llmPerf.success_rates.overall >= 90 ? 'metric-value success' : 'metric-value';
        }
        
        // Average Response Time
        const avgResponseEl = document.getElementById('avg-response');
        if (avgResponseEl && llmPerf.provider_performance) {
            const claude = llmPerf.provider_performance.claude.avg_response_time || 0;
            const gemini = llmPerf.provider_performance.gemini.avg_response_time || 0;
            const avg = ((claude + gemini) / 2).toFixed(1);
            avgResponseEl.textContent = `${avg}s`;
        }
        
        // RSS Status
        const rssStatusEl = document.getElementById('rss-status');
        if (rssStatusEl && rssStatus) {
            rssStatusEl.textContent = `${rssStatus.active_feeds}/${rssStatus.total_feeds}`;
            rssStatusEl.className = rssStatus.active_feeds >= rssStatus.total_feeds ? 'metric-value success' : 'metric-value';
        }
        
        // Total Queries
        const totalQueriesEl = document.getElementById('total-queries');
        if (totalQueriesEl && llmPerf.total_queries_analyzed) {
            totalQueriesEl.textContent = llmPerf.total_queries_analyzed;
        }
    }
    
    showProcessingState(question) {
        this.isProcessing = true;
        
        // Update current status
        const locationEl = document.getElementById('current-location');
        const rssEl = document.getElementById('current-rss');
        const llmEl = document.getElementById('current-llm');
        
        if (locationEl) {
            locationEl.textContent = 'Analyzing...';
            locationEl.className = 'status-value processing';
        }
        
        if (rssEl) {
            rssEl.textContent = 'Fetching...';
            rssEl.className = 'status-value processing';
        }
        
        if (llmEl) {
            llmEl.textContent = 'Processing...';
            llmEl.className = 'status-value processing';
        }
        
        // Add pulse animation to metrics
        document.querySelectorAll('.metric-value').forEach(el => {
            el.classList.add('updating');
        });
    }
    
    showCompletedState(result) {
        this.isProcessing = false;
        
        // Update current status
        const locationEl = document.getElementById('current-location');
        const rssEl = document.getElementById('current-rss');
        const llmEl = document.getElementById('current-llm');
        
        if (locationEl && result.processing_stages) {
            const location = result.processing_stages.location_detected || 'National';
            locationEl.textContent = location;
            locationEl.className = 'status-value success';
        }
        
        if (rssEl && result.processing_stages) {
            const sources = result.processing_stages.rss_data_sources || 0;
            rssEl.textContent = `${sources} sources`;
            rssEl.className = 'status-value success';
        }
        
        if (llmEl && result.processing_time) {
            llmEl.textContent = `${result.processing_time}s`;
            llmEl.className = 'status-value success';
        }
        
        // Remove pulse animation
        document.querySelectorAll('.metric-value').forEach(el => {
            el.classList.remove('updating');
        });
        
        // Refresh dashboard data
        setTimeout(() => this.loadInitialData(), 1000);
    }
    
    hookIntoSearchFunction() {
        // Hook into the existing analyzePropertyQuestion function
        const originalAnalyze = window.analyzePropertyQuestion;
        if (originalAnalyze) {
            window.analyzePropertyQuestion = async (question) => {
                console.log('🔍 Dashboard tracking query:', question);
                this.showProcessingState(question);
                
                try {
                    const result = await originalAnalyze(question);
                    this.showCompletedState(result);
                    return result;
                } catch (error) {
                    this.showErrorState();
                    throw error;
                }
            };
        }
    }
    
    showNoDataState() {
        // Show placeholder when no data available
        document.querySelectorAll('.metric-value').forEach(el => {
            if (el.textContent === '---' || el.textContent === '---s' || el.textContent === '---%') {
                el.textContent = 'No data';
                el.className = 'metric-value';
            }
        });
    }
    
    showErrorState() {
        document.querySelectorAll('.metric-value').forEach(el => {
            el.classList.remove('updating', 'processing');
            el.classList.add('error');
        });
        
        const llmEl = document.getElementById('current-llm');
        if (llmEl) {
            llmEl.textContent = 'Error';
            llmEl.className = 'status-value error';
        }
    }
    
    startAutoUpdate() {
        // Update dashboard every 30 seconds
        this.updateInterval = setInterval(() => {
            if (!this.isProcessing) {
                this.loadInitialData();
            }
        }, 30000);
    }
    
    destroy() {
        // Cleanup method
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
    }
}

// Initialize dashboard when script loads
window.llmDashboard = new LLMDashboard();

// Export for external use
window.LLMDashboard = LLMDashboard;