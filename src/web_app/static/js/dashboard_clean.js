// Dashboard JavaScript - Personal Investment System
console.log('🚀 Dashboard JavaScript loaded successfully');

// Global variables for chart instances
let networthChart = null;
let portfolioChart = null;

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 DOM loaded, starting initialization...');
    
    // Add immediate debug info
    updateDebugInfo('chart-status', 'DOM Ready - Starting...');
    
    // Load real data first, then create charts
    setTimeout(function() {
        console.log('⏰ Timer triggered - Loading real data...');
        loadRealDataAndCreateCharts();
    }, 500);
});

// Function to load real data first and create charts
function loadRealDataAndCreateCharts() {
    console.log('🔄 loadRealDataAndCreateCharts starting...');
    
    // Update debug info immediately
    updateDebugInfo('chart-status', 'Calling API...');
    updateDebugInfo('api-status', 'API: Fetching data...');
    updateDebugInfo('data-status', 'Data: Waiting for API...');
    
    console.log('📡 Making fetch request to /api/unified_analysis');
    
    fetch('/api/unified_analysis')
        .then(response => {
            console.log('📥 API response received, status:', response.status);
            updateDebugInfo('api-status', `API: ${response.status} ${response.statusText}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return response.json();
        })
        .then(data => {
            console.log('📊 API data parsed successfully');
            console.log('Data status:', data.status);
            console.log('Data keys:', Object.keys(data.data || {}));
            
            if (data.status === 'success' && data.data) {
                console.log('✅ Valid API data received, processing...');
                
                // Extract real asset allocation data
                console.log('🎯 Extracting asset allocation data...');
                const realAllocationData = extractAssetAllocationData(data.data);
                console.log('Asset allocation result:', realAllocationData);
                
                // Extract real cash flow data
                console.log('💰 Extracting cash flow data...');
                const realCashFlowData = extractCashFlowData(data.data);
                console.log('Cash flow result:', realCashFlowData);
                
                // Extract recommendations data
                console.log('📋 Extracting recommendations data...');
                const recommendationsData = extractRecommendationsData(data.data);
                console.log('Recommendations result:', recommendationsData);
                
                if (realAllocationData && realAllocationData.length > 0) {
                    console.log('🎨 Creating charts with REAL DATA');
                    updateDebugInfo('data-status', `Data: REAL (${realAllocationData.length} assets, ${realCashFlowData ? realCashFlowData.length : 0} months, ${recommendationsData ? recommendationsData.length : 0} recommendations)`);
                    updateDebugInfo('chart-status', 'Charts: Creating with REAL data');
                    
                    // Create charts
                    createChartsWithRealData(realAllocationData, realCashFlowData);
                    
                    // Populate recommendations table
                    console.log('📋 Populating recommendations table...');
                    populateRecommendationsTable(recommendationsData);
                    
                    updateDebugInfo('chart-status', 'Charts: COMPLETED with real data');
                } else {
                    console.log('⚠️ No real allocation data found, using sample data');
                    updateDebugInfo('data-status', 'Data: No allocation data found');
                    updateDebugInfo('chart-status', 'Charts: Using SAMPLE data');
                    createTestCharts();
                    
                    // Populate with sample recommendations
                    populateRecommendationsTable(generateSampleRecommendations());
                }
            } else {
                console.log('❌ Invalid API response structure');
                updateDebugInfo('data-status', 'Data: Invalid API structure');
                updateDebugInfo('chart-status', 'Charts: Using SAMPLE data (invalid API)');
                createTestCharts();
                populateRecommendationsTable(generateSampleRecommendations());
            }
        })
        .catch(error => {
            console.error('❌ API error:', error);
            updateDebugInfo('api-status', `API: ERROR - ${error.message}`);
            updateDebugInfo('data-status', 'Data: Error loading');
            updateDebugInfo('chart-status', 'Charts: Using SAMPLE data (API failed)');
            createTestCharts();
            
            // Populate with sample recommendations on error
            populateRecommendationsTable(generateSampleRecommendations());
        });
}

// Helper function to update debug info
function updateDebugInfo(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
    }
}

// Function to create charts with real data
function createChartsWithRealData(realAllocationData, realCashFlowData) {
    console.log('createChartsWithRealData called with data:', realAllocationData);
    console.log('Cash flow data:', realCashFlowData);
    
    // Create portfolio chart (keeping as sample for now)
    const portfolioCtx = document.getElementById('portfolioChart');
    if (portfolioCtx) {
        console.log('Creating portfolio chart...');
        try {
            portfolioChart = new Chart(portfolioCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Stocks', 'Bonds', 'Cash'],
                    datasets: [{
                        data: [60, 30, 10],
                        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' },
                        title: { display: true, text: 'Portfolio Overview' }
                    }
                }
            });
            console.log('Portfolio chart created successfully!');
        } catch (error) {
            console.error('Portfolio chart error:', error);
        }
    }
    
    // Create REAL asset allocation chart
    const allocationCtx = document.getElementById('allocationChart');
    if (allocationCtx) {
        console.log('Creating REAL asset allocation chart with data:', realAllocationData);
        try {
            const allocationChart = new Chart(allocationCtx, {
                type: 'doughnut',
                data: {
                    labels: realAllocationData.map(item => item.label),
                    datasets: [{
                        data: realAllocationData.map(item => item.value),
                        backgroundColor: realAllocationData.map(item => item.color),
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                usePointStyle: true,
                                padding: 15,
                                font: { size: 12 }
                            }
                        },
                        title: {
                            display: true,
                            text: 'Real Asset Allocation',
                            font: { size: 16, weight: 'bold' }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const item = realAllocationData[context.dataIndex];
                                    const percentage = item.value.toFixed(1);
                                    const amount = item.amount.toLocaleString('en-US', {
                                        style: 'currency',
                                        currency: 'USD'
                                    });
                                    return `${item.label}: ${percentage}% (${amount})`;
                                }
                            }
                        }
                    }
                }
            });
            console.log('REAL asset allocation chart created successfully!');
        } catch (error) {
            console.error('Real asset allocation chart error:', error);
        }
    }
    
    // Create net worth chart (sample data for now)
    const networthCtx = document.getElementById('networthChart');
    if (networthCtx) {
        console.log('Creating net worth chart...');
        try {
            networthChart = new Chart(networthCtx, {
                type: 'line',
                data: {
                    labels: ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024', 'May 2024', 'Jun 2024'],
                    datasets: [{
                        label: 'Net Worth',
                        data: [100000, 105000, 103000, 108000, 112000, 115000],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { display: true, text: 'Net Worth Trend' }
                    },
                    scales: {
                        y: {
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
            console.log('Net worth chart created successfully!');
        } catch (error) {
            console.error('Net worth chart error:', error);
        }
    }
    
    // Create cash flow chart
    const cashflowCtx = document.getElementById('cashflowChart');
    if (cashflowCtx && realCashFlowData && realCashFlowData.length > 0) {
        console.log('Creating cash flow chart with real data...');
        try {
            const cashflowChart = new Chart(cashflowCtx, {
                type: 'bar',
                data: {
                    labels: realCashFlowData.map(item => item.month),
                    datasets: [
                        {
                            label: 'Income',
                            data: realCashFlowData.map(item => item.income),
                            backgroundColor: '#4CAF50',
                            borderColor: '#388E3C',
                            borderWidth: 1
                        },
                        {
                            label: 'Expenses',
                            data: realCashFlowData.map(item => item.expense),
                            backgroundColor: '#F44336',
                            borderColor: '#D32F2F',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { 
                            display: true, 
                            text: 'Monthly Cash Flow',
                            font: { size: 16, weight: 'bold' }
                        },
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed.y;
                                    const formattedValue = value.toLocaleString('en-US', {
                                        style: 'currency',
                                        currency: 'USD'
                                    });
                                    return `${context.dataset.label}: ${formattedValue}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Month'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Amount (CNY)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return '¥' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
            console.log('Cash flow chart created successfully!');
        } catch (error) {
            console.error('Cash flow chart error:', error);
        }
    } else if (cashflowCtx) {
        console.log('Creating cash flow chart with sample data...');
        try {
            const cashflowChart = new Chart(cashflowCtx, {
                type: 'bar',
                data: {
                    labels: ['Jul 24', 'Aug 24', 'Sep 24', 'Oct 24', 'Nov 24', 'Dec 24'],
                    datasets: [
                        {
                            label: 'Income',
                            data: [45000, 48000, 46000, 49000, 47000, 50000],
                            backgroundColor: '#4CAF50',
                            borderColor: '#388E3C',
                            borderWidth: 1
                        },
                        {
                            label: 'Expenses',
                            data: [35000, 38000, 33000, 40000, 36000, 39000],
                            backgroundColor: '#F44336',
                            borderColor: '#D32F2F',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { 
                            display: true, 
                            text: 'Monthly Cash Flow (Sample)',
                            font: { size: 16, weight: 'bold' }
                        },
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Month'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Amount (CNY)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return '¥' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
            console.log('Sample cash flow chart created successfully!');
        } catch (error) {
            console.error('Sample cash flow chart error:', error);
        }
    }
}

function createTestCharts() {
    
    // Test Portfolio Chart
    const portfolioCtx = document.getElementById('portfolioChart');
    console.log('Portfolio canvas found:', !!portfolioCtx);
    
    if (portfolioCtx) {
        console.log('Creating portfolio chart...');
        try {
            portfolioChart = new Chart(portfolioCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Stocks', 'Bonds', 'Cash'],
                    datasets: [{
                        data: [60, 30, 10],
                        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        title: {
                            display: true,
                            text: 'Portfolio Overview'
                        }
                    }
                }
            });
            console.log('Portfolio chart created successfully!');
        } catch (error) {
            console.error('Portfolio chart error:', error);
        }
    }
    
    // Asset Allocation Chart (New Implementation)
    const allocationCtx = document.getElementById('allocationChart');
    console.log('Asset allocation canvas found:', !!allocationCtx);
    
    if (allocationCtx) {
        console.log('Creating asset allocation chart...');
        try {
            const allocationChart = new Chart(allocationCtx, {
                type: 'doughnut',
                data: {
                    labels: [
                        'US Stocks', 
                        'International Stocks', 
                        'Bonds', 
                        'Real Estate (REITs)', 
                        'Commodities',
                        'Cash & Equivalents'
                    ],
                    datasets: [{
                        data: [35, 20, 25, 10, 5, 5],
                        backgroundColor: [
                            '#FF6384', // US Stocks - Red/Pink
                            '#36A2EB', // International - Blue  
                            '#FFCE56', // Bonds - Yellow
                            '#4BC0C0', // REITs - Teal
                            '#9966FF', // Commodities - Purple
                            '#FF9F40'  // Cash - Orange
                        ],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                usePointStyle: true,
                                padding: 15,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        title: {
                            display: true,
                            text: 'Current Asset Allocation',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${percentage}%`;
                                }
                            }
                        }
                    }
                }
            });
            console.log('Asset allocation chart created successfully!');
        } catch (error) {
            console.error('Asset allocation chart error:', error);
        }
    }
    
    // Test Net Worth Chart
    const networthCtx = document.getElementById('networthChart');
    console.log('Net worth canvas found:', !!networthCtx);
    
    if (networthCtx) {
        console.log('Creating net worth chart...');
        try {
            networthChart = new Chart(networthCtx, {
                type: 'line',
                data: {
                    labels: ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024', 'May 2024', 'Jun 2024'],
                    datasets: [{
                        label: 'Net Worth',
                        data: [100000, 105000, 103000, 108000, 112000, 115000],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
            console.log('Net worth chart created successfully!');
        } catch (error) {
            console.error('Net worth chart error:', error);
        }
    }
    
    // Sample Cash Flow Chart
    const cashflowCtx = document.getElementById('cashflowChart');
    if (cashflowCtx) {
        console.log('Creating sample cash flow chart...');
        try {
            const cashflowChart = new Chart(cashflowCtx, {
                type: 'bar',
                data: {
                    labels: ['Jul 24', 'Aug 24', 'Sep 24', 'Oct 24', 'Nov 24', 'Dec 24'],
                    datasets: [
                        {
                            label: 'Income',
                            data: [45000, 48000, 46000, 49000, 47000, 50000],
                            backgroundColor: '#4CAF50',
                            borderColor: '#388E3C',
                            borderWidth: 1
                        },
                        {
                            label: 'Expenses',
                            data: [35000, 38000, 33000, 40000, 36000, 39000],
                            backgroundColor: '#F44336',
                            borderColor: '#D32F2F',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { 
                            display: true, 
                            text: 'Monthly Cash Flow (Sample)',
                            font: { size: 16, weight: 'bold' }
                        },
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Month'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Amount (CNY)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return '¥' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
            console.log('Sample cash flow chart created successfully!');
        } catch (error) {
            console.error('Sample cash flow chart error:', error);
        }
    }
    
    // Populate sample recommendations table with test charts
    populateRecommendationsTable(generateSampleRecommendations());
}

// Function to extract asset allocation data from API response
function extractAssetAllocationData(apiData) {
    try {
        console.log('Extracting asset allocation data...');
        
        // Check various possible locations for asset allocation data
        let allocationData = null;
        
        // Check portfolio_analysis -> holdings_mapping -> top_level (most likely location)
        if (apiData.portfolio_analysis && 
            apiData.portfolio_analysis.holdings_mapping && 
            apiData.portfolio_analysis.holdings_mapping.top_level) {
            allocationData = apiData.portfolio_analysis.holdings_mapping.top_level;
            console.log('Found top_level holdings data:', allocationData);
        }
        // Check portfolio_analysis section
        else if (apiData.portfolio_analysis && apiData.portfolio_analysis.asset_allocation) {
            allocationData = apiData.portfolio_analysis.asset_allocation;
        }
        // Check financial_analysis section
        else if (apiData.financial_analysis && apiData.financial_analysis.investment && 
                 apiData.financial_analysis.investment.asset_breakdown) {
            allocationData = apiData.financial_analysis.investment.asset_breakdown;
        }
        
        if (!allocationData) {
            console.log('No asset allocation data found in API response');
            return null;
        }
        
        // Convert data to chart format with translation
        const chartData = [];
        const assetTranslations = {
            '股票': 'Stocks',
            '固定收益': 'Fixed Income/Bonds', 
            '现金': 'Cash & Equivalents',
            '保险': 'Insurance',
            '商品': 'Commodities',
            '房地产': 'Real Estate'
        };
        
        const assetColors = {
            'Stocks': '#FF6384',
            'Fixed Income/Bonds': '#36A2EB',
            'Cash & Equivalents': '#FFCE56',
            'Insurance': '#4BC0C0',
            'Commodities': '#9966FF',
            'Real Estate': '#FF9F40'
        };
        
        if (typeof allocationData === 'object') {
            // Calculate total value
            const totalValue = Object.values(allocationData).reduce((sum, value) => {
                return sum + (typeof value === 'number' ? value : parseFloat(value) || 0);
            }, 0);
            
            console.log('Total portfolio value:', totalValue);
            
            Object.keys(allocationData).forEach(key => {
                const value = allocationData[key];
                const numericValue = typeof value === 'number' ? value : parseFloat(value);
                
                if (!isNaN(numericValue) && numericValue > 0) {
                    const translatedKey = assetTranslations[key] || key;
                    const percentage = (numericValue / totalValue * 100);
                    
                    chartData.push({
                        label: translatedKey,
                        value: percentage,
                        amount: numericValue,
                        color: assetColors[translatedKey] || '#999999'
                    });
                }
            });
        }
        
        // Sort by value (largest first)
        chartData.sort((a, b) => b.value - a.value);
        
        console.log(`Extracted ${chartData.length} asset allocation items:`, chartData);
        return chartData.length > 0 ? chartData : null;
        
    } catch (error) {
        console.error('Error extracting asset allocation data:', error);
        return null;
    }
}

// Function to extract monthly cash flow data from API response
function extractCashFlowData(apiData) {
    try {
        console.log('Extracting cash flow data...');
        
        if (!apiData || !apiData.financial_analysis || !apiData.financial_analysis.cash_flow) {
            console.log('No cash flow data found in API response');
            return null;
        }
        
        const cashFlow = apiData.financial_analysis.cash_flow;
        const incomeTrend = cashFlow.income_trends?.trend_data;
        const expenseTrend = cashFlow.expense_trends?.trend_data;
        
        if (!incomeTrend || !expenseTrend || !incomeTrend.data || !expenseTrend.data) {
            console.log('Missing income or expense trend data');
            return null;
        }
        
        // Get recent 12 months of data
        const dataLength = Math.min(incomeTrend.data.length, expenseTrend.data.length, 12);
        const startIndex = Math.max(0, incomeTrend.data.length - dataLength);
        
        const monthlyData = [];
        
        for (let i = startIndex; i < incomeTrend.data.length && monthlyData.length < 12; i++) {
            const dateStr = incomeTrend.index[i];
            const date = new Date(dateStr);
            const monthName = date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
            
            const income = incomeTrend.data[i]?.Total_Income_Calc_CNY || 0;
            const expense = expenseTrend.data[i]?.Total_Expense_Calc_CNY || 0;
            
            monthlyData.push({
                month: monthName,
                income: income,
                expense: expense,
                netFlow: income - expense
            });
        }
        
        console.log(`Extracted ${monthlyData.length} months of cash flow data:`, monthlyData);
        return monthlyData.length > 0 ? monthlyData : null;
        
    } catch (error) {
        console.error('Error extracting cash flow data:', error);
        return null;
    }
}

// Function to extract recommendations from API data
function extractRecommendationsData(apiData) {
    try {
        console.log('🔍 Extracting recommendations data...');
        
        const recommendations = [];
        
        // Check comprehensive recommendations from the recommendation engine
        if (apiData.recommendations) {
            const recs = apiData.recommendations;
            
            // Financial recommendations
            if (recs.financial && Array.isArray(recs.financial)) {
                recs.financial.forEach(rec => {
                    recommendations.push({
                        category: 'Financial Planning',
                        title: rec.title || 'Financial Recommendation',
                        description: rec.description || rec.rationale || 'Financial recommendation',
                        priority: rec.priority === 1 ? 'High' : rec.priority === 2 ? 'Medium' : 'Low',
                        details: JSON.stringify(rec)
                    });
                });
            }
            
            // Portfolio recommendations
            if (recs.portfolio && Array.isArray(recs.portfolio)) {
                recs.portfolio.forEach(rec => {
                    recommendations.push({
                        category: 'Portfolio Management',
                        title: rec.title || 'Portfolio Recommendation',
                        description: rec.description || rec.rationale || 'Portfolio recommendation',
                        priority: rec.priority === 1 ? 'High' : rec.priority === 2 ? 'Medium' : 'Low',
                        details: JSON.stringify(rec)
                    });
                });
            }
            
            // Risk recommendations
            if (recs.risk && Array.isArray(recs.risk)) {
                recs.risk.forEach(rec => {
                    recommendations.push({
                        category: 'Risk Management',
                        title: rec.title || 'Risk Recommendation',
                        description: rec.description || rec.rationale || 'Risk management recommendation',
                        priority: rec.priority === 1 ? 'High' : rec.priority === 2 ? 'Medium' : 'Low',
                        details: JSON.stringify(rec)
                    });
                });
            }
        }
        
        // Fallback: Check legacy recommendation locations
        if (recommendations.length === 0) {
            // Check portfolio optimization recommendations
            if (apiData.portfolio_optimization?.recommendations) {
                const portRecs = apiData.portfolio_optimization.recommendations;
                
                if (portRecs.allocation_adjustments) {
                    recommendations.push({
                        category: 'Portfolio Optimization',
                        title: 'Asset Allocation Adjustment',
                        description: 'Rebalance portfolio to optimal allocation',
                        priority: 'High',
                        details: JSON.stringify(portRecs.allocation_adjustments)
                    });
                }
            }
            
            // Check financial analysis recommendations
            if (apiData.financial_analysis?.recommendations) {
                const finRecs = apiData.financial_analysis.recommendations;
                
                Object.entries(finRecs).forEach(([key, value]) => {
                    if (value && typeof value === 'object') {
                        recommendations.push({
                            category: 'Financial Analysis',
                            title: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                            description: JSON.stringify(value).substring(0, 100) + '...',
                            priority: 'Medium',
                            details: JSON.stringify(value)
                        });
                    }
                });
            }
        }
        
        console.log(`✅ Extracted ${recommendations.length} recommendations:`, recommendations);
        return recommendations.length > 0 ? recommendations : null;
        
    } catch (error) {
        console.error('❌ Error extracting recommendations:', error);
        return null;
    }
}

// Function to populate the recommendations table
function populateRecommendationsTable(recommendationsData) {
    try {
        console.log('📋 Populating recommendations table...');
        
        const tbody = document.querySelector('#recommendations-table tbody');
        if (!tbody) {
            console.error('❌ Recommendations table body not found');
            return;
        }
        
        // Clear existing rows
        tbody.innerHTML = '';
        
        if (!recommendationsData || recommendationsData.length === 0) {
            console.log('⚠️ No recommendations data, using sample data');
            recommendationsData = generateSampleRecommendations();
        }
        
        recommendationsData.forEach((rec, index) => {
            const row = document.createElement('tr');
            
            // Get priority class
            const priorityClass = rec.priority.toLowerCase() === 'high' ? 'priority-high' :
                                 rec.priority.toLowerCase() === 'medium' ? 'priority-medium' : 'priority-low';
            
            row.innerHTML = `
                <td><span class="priority-badge ${priorityClass}">${rec.priority}</span></td>
                <td>${rec.category}</td>
                <td><strong>${rec.title}</strong><br><small>${rec.description}</small></td>
                <td><button class="btn-details" onclick="showRecommendationDetails(${index})" 
                    data-details='${rec.details}'>View Details</button></td>
            `;
            
            tbody.appendChild(row);
        });
        
        // Store recommendations globally for details view
        window.currentRecommendations = recommendationsData;
        
        console.log(`✅ Populated recommendations table with ${recommendationsData.length} items`);
        
    } catch (error) {
        console.error('❌ Error populating recommendations table:', error);
    }
}

// Function to generate sample recommendations for testing
function generateSampleRecommendations() {
    return [
        {
            category: 'Portfolio Optimization',
            title: 'Increase International Exposure',
            description: 'Consider adding 15% international equity exposure for better diversification',
            priority: 'High',
            details: '{"recommended_allocation": "15%", "current_international": "5%", "expected_benefit": "Reduced correlation risk"}'
        },
        {
            category: 'Cash Flow',
            title: 'Emergency Fund Review',
            description: 'Current emergency fund covers 4.2 months. Consider increasing to 6 months.',
            priority: 'Medium',
            details: '{"current_months": 4.2, "recommended_months": 6, "gap_amount": "¥18,500"}'
        },
        {
            category: 'Risk Management',
            title: 'Portfolio Volatility',
            description: 'Portfolio showing higher than expected volatility this quarter',
            priority: 'Medium',
            details: '{"current_volatility": "18.5%", "target_volatility": "15%", "suggested_action": "Rebalance towards bonds"}'
        },
        {
            category: 'Tax Optimization',
            title: 'Tax-Loss Harvesting Opportunity',
            description: 'Potential ¥3,200 in tax savings available through rebalancing',
            priority: 'Low',
            details: '{"potential_savings": "¥3,200", "assets_to_sell": ["Tech ETF"], "replacement_suggested": "Broad Market ETF"}'
        }
    ];
}

// Function to show recommendation details
function showRecommendationDetails(index) {
    try {
        const recommendations = window.currentRecommendations || generateSampleRecommendations();
        const rec = recommendations[index];
        
        if (rec) {
            alert(`${rec.title}\n\nCategory: ${rec.category}\nPriority: ${rec.priority}\n\nDetails:\n${rec.details}`);
        }
    } catch (error) {
        console.error('Error showing recommendation details:', error);
    }
}
