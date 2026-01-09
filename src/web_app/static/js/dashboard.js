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
                
                // Extract sub-category asset allocation data for detailed view
                console.log('🔍 Extracting sub-category asset allocation data...');
                const realSubCategoryData = extractSubCategoryAllocationData(data.data);
                console.log('Sub-category allocation result:', realSubCategoryData);
                
                // Extract real cash flow data
                console.log('💰 Extracting cash flow data...');
                const realCashFlowData = extractCashFlowData(data.data);
                console.log('💰 Cash flow extraction result:', realCashFlowData);
                console.log('💰 Cash flow data type:', typeof realCashFlowData);
                console.log('💰 Cash flow data length:', realCashFlowData ? realCashFlowData.length : 'null');
                
                // Extract real net worth data
                console.log('📈 Extracting net worth data...');
                const realNetWorthData = extractNetWorthData(data.data);
                console.log('Net worth result:', realNetWorthData);
                
                // Extract performance data
                console.log('📊 Extracting performance data...');
                const realPerformanceData = extractPerformanceData(data.data);
                console.log('Performance result:', realPerformanceData);
                
                // Extract recommendations data
                console.log('📋 Extracting recommendations data...');
                const recommendationsData = extractRecommendationsData(data.data);
                console.log('Recommendations result:', recommendationsData);
                
                if (realAllocationData && realAllocationData.length > 0) {
                    console.log('🎨 Creating charts with REAL DATA');
                    updateDebugInfo('data-status', `Data: REAL (${realAllocationData.length} assets, ${realCashFlowData ? realCashFlowData.length : 0} months, ${realNetWorthData ? realNetWorthData.labels.length : 0} net worth points, ${realPerformanceData ? realPerformanceData.labels.length : 0} performance periods, ${recommendationsData ? recommendationsData.length : 0} recommendations)`);
                    updateDebugInfo('chart-status', 'Charts: Creating with REAL data');
                    
                    // Create charts
                    createChartsWithRealData(realAllocationData, realCashFlowData, realNetWorthData, realPerformanceData, realSubCategoryData);
                    
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
function createChartsWithRealData(realAllocationData, realCashFlowData, realNetWorthData, realPerformanceData, realSubCategoryData) {
    console.log('createChartsWithRealData called with data:', realAllocationData);
    console.log('Cash flow data:', realCashFlowData);
    console.log('Net worth data:', realNetWorthData);
    console.log('Performance data:', realPerformanceData);
    
    // Create portfolio chart using real allocation data
    const portfolioCtx = document.getElementById('portfolioChart');
    if (portfolioCtx && realAllocationData && realAllocationData.length > 0) {
        console.log('Creating portfolio chart with real data...');
        try {
            portfolioChart = new Chart(portfolioCtx, {
                type: 'doughnut',
                data: {
                    labels: realAllocationData.map(item => item.label),
                    datasets: [{
                        data: realAllocationData.map(item => item.amount),
                        backgroundColor: realAllocationData.map(item => item.color)
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom' },
                        title: { display: true, text: 'Portfolio Overview' },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${context.label}: ¥${value.toLocaleString()} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
            console.log('Portfolio chart created successfully with real data!');
        } catch (error) {
            console.error('Portfolio chart error:', error);
        }
    }
    
    // Create detailed sub-category Asset Allocation chart
    const allocationCtx = document.getElementById('allocationChart');
    if (allocationCtx && realSubCategoryData && realSubCategoryData.length > 0) {
        console.log('Creating detailed sub-category asset allocation chart with data:', realSubCategoryData);
        try {
            const allocationChart = new Chart(allocationCtx, {
                type: 'bar',
                data: {
                    labels: realSubCategoryData.map(item => item.label),
                    datasets: [{
                        label: 'Asset Value (¥)',
                        data: realSubCategoryData.map(item => item.amount),
                        backgroundColor: realSubCategoryData.map(item => item.color),
                        borderColor: realSubCategoryData.map(item => item.color),
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false
                    }]
                },
                options: {
                    indexAxis: 'y', // This makes it a horizontal bar chart
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false // Hide legend for cleaner look with many categories
                        },
                        title: {
                            display: true,
                            text: 'Detailed Asset Allocation by Sub-Category',
                            font: { size: 16, weight: 'bold' },
                            color: '#333',
                            padding: 20
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            borderColor: '#fff',
                            borderWidth: 1,
                            callbacks: {
                                label: function(context) {
                                    const item = realSubCategoryData[context.dataIndex];
                                    const percentage = item.value.toFixed(1);
                                    const amount = `¥${item.amount.toLocaleString()}`;
                                    return `${item.label}: ${amount} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    layout: {
                        padding: {
                            top: 20,
                            bottom: 20,
                            left: 20,
                            right: 20
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Asset Value (¥)',
                                font: { size: 12, weight: 'bold' },
                                color: '#666'
                            },
                            grid: {
                                color: 'rgba(200, 200, 200, 0.2)'
                            },
                            ticks: {
                                font: { size: 10 },
                                color: '#666',
                                callback: function(value) {
                                    if (value >= 1000000) {
                                        return '¥' + (value / 1000000).toFixed(1) + 'M';
                                    } else if (value >= 1000) {
                                        return '¥' + (value / 1000).toFixed(0) + 'K';
                                    }
                                    return '¥' + value.toLocaleString();
                                }
                            }
                        },
                        y: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                font: { size: 11, weight: 'bold' },
                                color: '#666'
                            }
                        }
                    },
                    datasets: {
                        bar: {
                            barPercentage: 0.8,
                            categoryPercentage: 0.9
                        }
                    }
                }
            });
            console.log('Detailed sub-category asset allocation chart created successfully!');
        } catch (error) {
            console.error('Sub-category asset allocation chart error:', error);
        }
    } else if (allocationCtx && realAllocationData && realAllocationData.length > 0) {
        // Fallback to top-level allocation if sub-category data is not available
        console.log('Creating fallback top-level asset allocation chart with data:', realAllocationData);
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
                            text: 'Asset Allocation (Top Level)',
                            font: { size: 16, weight: 'bold' }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const item = realAllocationData[context.dataIndex];
                                    const percentage = item.value.toFixed(1);
                                    const amount = `¥${item.amount.toLocaleString()}`;
                                    return `${item.label}: ${percentage}% (${amount})`;
                                }
                            }
                        }
                    }
                }
            });
            console.log('Fallback top-level asset allocation chart created successfully!');
        } catch (error) {
            console.error('Fallback asset allocation chart error:', error);
        }
    }
    
    // Create net worth chart with real data
    const networthCtx = document.getElementById('networthChart');
    if (networthCtx && realNetWorthData && realNetWorthData.labels.length > 0) {
        console.log('Creating net worth chart with real data...');
        try {
            networthChart = new Chart(networthCtx, {
                type: 'line',
                data: {
                    labels: realNetWorthData.labels,
                    datasets: [{
                        label: 'Net Worth',
                        data: realNetWorthData.netWorth,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true
                    }, {
                        label: 'Total Assets',
                        data: realNetWorthData.assets,
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 2,
                        fill: false
                    }, {
                        label: 'Total Liabilities',
                        data: realNetWorthData.liabilities,
                        borderColor: '#f44336',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        borderWidth: 2,
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { display: true, text: 'Net Worth Trend (24 Months)' },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ¥${context.parsed.y.toLocaleString()}`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            ticks: {
                                callback: function(value) {
                                    return '¥' + (value/1000000).toFixed(1) + 'M';
                                }
                            }
                        }
                    }
                }
            });
            console.log('Net worth chart created successfully with real data!');
        } catch (error) {
            console.error('Net worth chart error:', error);
        }
    }
    
    // Create cash flow chart
    const cashflowCtx = document.getElementById('cashflowChart');
    console.log('💰 [CHART] Cash flow canvas found:', !!cashflowCtx);
    console.log('💰 [CHART] Real cash flow data:', realCashFlowData);
    console.log('💰 [CHART] Data length:', realCashFlowData ? realCashFlowData.length : 'N/A');
    
    if (cashflowCtx && realCashFlowData && realCashFlowData.length > 0) {
        console.log('💰 [CHART] Creating cash flow chart with real data...');
        try {
            const cashflowChart = new Chart(cashflowCtx, {
                type: 'bar',
                data: {
                    labels: realCashFlowData.map(item => item.month),
                    datasets: [
                        {
                            label: 'Income',
                            data: realCashFlowData.map(item => item.income),
                            backgroundColor: 'rgba(76, 175, 80, 0.7)',
                            borderColor: '#4CAF50',
                            borderWidth: 2
                        },
                        {
                            label: 'Expenses',
                            data: realCashFlowData.map(item => item.expense),
                            backgroundColor: 'rgba(244, 67, 54, 0.7)',
                            borderColor: '#F44336',
                            borderWidth: 2
                        },
                        {
                            label: 'Investments',
                            data: realCashFlowData.map(item => item.investment || 0),
                            backgroundColor: 'rgba(156, 39, 176, 0.7)',
                            borderColor: '#9C27B0',
                            borderWidth: 2
                        },
                        {
                            label: 'Net Cash Flow',
                            data: realCashFlowData.map(item => item.net),
                            backgroundColor: realCashFlowData.map(item => 
                                item.net >= 0 ? 'rgba(33, 150, 243, 0.8)' : 'rgba(255, 152, 0, 0.8)'
                            ),
                            borderColor: realCashFlowData.map(item => 
                                item.net >= 0 ? '#2196F3' : '#FF9800'
                            ),
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                        padding: {
                            top: 20,
                            bottom: 20,
                            left: 10,
                            right: 10
                        }
                    },
                    plugins: {
                        title: { 
                            display: true, 
                            text: 'Monthly Cash Flow Analysis',
                            font: { size: 18, weight: 'bold' },
                            color: '#333',
                            padding: { bottom: 20 }
                        },
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20,
                                font: { size: 13 }
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff',
                            cornerRadius: 6,
                            padding: 12,
                            callbacks: {
                                title: function(context) {
                                    return context[0].label;
                                },
                                label: function(context) {
                                    const value = context.parsed.y;
                                    const label = context.dataset.label;
                                    
                                    // Format large numbers in K for readability
                                    let formattedValue;
                                    if (Math.abs(value) >= 1000) {
                                        formattedValue = '¥' + (value / 1000).toFixed(1) + 'K';
                                    } else {
                                        formattedValue = '¥' + value.toLocaleString();
                                    }
                                    
                                    if (label === 'Net Cash Flow') {
                                        const prefix = value >= 0 ? '+' : '';
                                        return `${label}: ${prefix}${formattedValue}`;
                                    }
                                    
                                    return `${label}: ${formattedValue}`;
                                },
                                afterBody: function(context) {
                                    // Add comprehensive financial metrics
                                    const dataIndex = context[0].dataIndex;
                                    const income = realCashFlowData[dataIndex].income;
                                    const expense = realCashFlowData[dataIndex].expense;
                                    const investment = realCashFlowData[dataIndex].investment || 0;
                                    const net = realCashFlowData[dataIndex].net;
                                    
                                    if (income > 0) {
                                        const expenseRate = (expense / income * 100).toFixed(1);
                                        const investmentRate = (investment / income * 100).toFixed(1);
                                        const savingsRate = (net / income * 100).toFixed(1);
                                        return [
                                            `Expense Rate: ${expenseRate}%`,
                                            `Investment Rate: ${investmentRate}%`,
                                            `Savings Rate: ${savingsRate}%`
                                        ];
                                    }
                                    return [];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Month',
                                font: { size: 14, weight: 'bold' }
                            },
                            grid: {
                                display: false
                            },
                            ticks: {
                                font: { size: 12 }
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Amount (CNY)',
                                font: { size: 14, weight: 'bold' }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                callback: function(value) {
                                    // Format Y-axis labels in K for readability
                                    if (Math.abs(value) >= 1000) {
                                        return '¥' + (value / 1000).toFixed(0) + 'K';
                                    }
                                    return '¥' + value.toLocaleString();
                                },
                                font: { size: 12 }
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    // Increase bar thickness and spacing
                    barPercentage: 0.8,
                    categoryPercentage: 0.9
                }
            });
            console.log('💰 [CHART] Cash flow chart created successfully!');
        } catch (error) {
            console.error('💰 [CHART] Cash flow chart error:', error);
        }
    } else {
        console.log('💰 [CHART] No real cash flow data available, creating sample chart...');
        
        // Create sample cash flow chart with improved visualization
        if (cashflowCtx) {
            try {
                const sampleData = [
                    { month: 'Feb 2025', income: 52000, expense: 23000, net: 29000 },
                    { month: 'Mar 2025', income: 220000, expense: 68000, net: 152000 },
                    { month: 'Apr 2025', income: 179000, expense: 82000, net: 97000 },
                    { month: 'May 2025', income: 39000, expense: 194000, net: -155000 },
                    { month: 'Jun 2025', income: 39000, expense: 63000, net: -24000 },
                    { month: 'Jul 2025', income: 37000, expense: 68000, net: -31000 }
                ];
                
                const sampleChart = new Chart(cashflowCtx, {
                    type: 'bar',
                    data: {
                        labels: sampleData.map(item => item.month),
                        datasets: [
                            {
                                label: 'Income',
                                data: sampleData.map(item => item.income),
                                backgroundColor: 'rgba(76, 175, 80, 0.7)',
                                borderColor: '#4CAF50',
                                borderWidth: 2
                            },
                            {
                                label: 'Expenses',
                                data: sampleData.map(item => item.expense),
                                backgroundColor: 'rgba(244, 67, 54, 0.7)',
                                borderColor: '#F44336',
                                borderWidth: 2
                            },
                            {
                                label: 'Net Cash Flow',
                                data: sampleData.map(item => item.net),
                                backgroundColor: sampleData.map(item => 
                                    item.net >= 0 ? 'rgba(33, 150, 243, 0.8)' : 'rgba(255, 152, 0, 0.8)'
                                ),
                                borderColor: sampleData.map(item => 
                                    item.net >= 0 ? '#2196F3' : '#FF9800'
                                ),
                                borderWidth: 2
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        layout: {
                            padding: {
                                top: 20,
                                bottom: 20,
                                left: 10,
                                right: 10
                            }
                        },
                        plugins: {
                            title: { 
                                display: true, 
                                text: 'Monthly Cash Flow Analysis (Sample Data)',
                                font: { size: 18, weight: 'bold' },
                                color: '#666',
                                padding: { bottom: 20 }
                            },
                            legend: {
                                position: 'top',
                                labels: {
                                    usePointStyle: true,
                                    padding: 20,
                                    font: { size: 13 }
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                padding: 12,
                                callbacks: {
                                    label: function(context) {
                                        const value = context.parsed.y;
                                        const label = context.dataset.label;
                                        
                                        let formattedValue;
                                        if (Math.abs(value) >= 1000) {
                                            formattedValue = '¥' + (value / 1000).toFixed(1) + 'K';
                                        } else {
                                            formattedValue = '¥' + value.toLocaleString();
                                        }
                                        
                                        if (label === 'Net Cash Flow') {
                                            const prefix = value >= 0 ? '+' : '';
                                            return `${label}: ${prefix}${formattedValue}`;
                                        }
                                        
                                        return `${label}: ${formattedValue}`;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: 'Month',
                                    font: { size: 14, weight: 'bold' }
                                },
                                grid: { display: false },
                                ticks: {
                                    font: { size: 12 }
                                }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Amount (CNY)',
                                    font: { size: 14, weight: 'bold' }
                                },
                                grid: { color: 'rgba(0, 0, 0, 0.1)' },
                                ticks: {
                                    callback: function(value) {
                                        if (Math.abs(value) >= 1000) {
                                            return '¥' + (value / 1000).toFixed(0) + 'K';
                                        }
                                        return '¥' + value.toLocaleString();
                                    },
                                    font: { size: 12 }
                                }
                            }
                        },
                        interaction: {
                            intersect: false,
                            mode: 'index'
                        },
                        // Increase bar thickness and spacing
                        barPercentage: 0.8,
                        categoryPercentage: 0.9
                    }
                });
                console.log('💰 [CHART] Sample cash flow chart created successfully!');
            } catch (error) {
                console.error('💰 [CHART] Sample cash flow chart error:', error);
            }
        }
    }
    
    // Performance Trends chart - TEMPORARILY DISABLED due to data quality issues
    // The total return data is not making sense and needs to be fixed
    // Chart section is hidden in HTML template until data issues are resolved
    const performanceCtx = document.getElementById('performanceChart');
    if (performanceCtx && realPerformanceData && realPerformanceData.labels.length > 0) {
        console.log('Creating performance chart with real data...');
        try {
            const performanceChart = new Chart(performanceCtx, {
                type: 'bar',
                data: {
                    labels: realPerformanceData.labels,
                    datasets: [{
                        label: 'Total Return (%)',
                        data: realPerformanceData.returns,
                        backgroundColor: realPerformanceData.returns.map(val => 
                            val >= 0 ? 'rgba(76, 175, 80, 0.8)' : 'rgba(244, 67, 54, 0.8)'
                        ),
                        borderColor: realPerformanceData.returns.map(val => 
                            val >= 0 ? '#4CAF50' : '#f44336'
                        ),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { display: true, text: 'Portfolio Performance by Period' },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            title: {
                                display: true,
                                text: 'Return (%)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return value.toFixed(1) + '%';
                                }
                            }
                        }
                    }
                }
            });
            console.log('Performance chart created successfully with real data!');
        } catch (error) {
            console.error('Performance chart error:', error);
        }
    } else if (performanceCtx) {
        console.log('Creating performance chart with sample data...');
        try {
            const performanceChart = new Chart(performanceCtx, {
                type: 'bar',
                data: {
                    labels: ['3M', '6M', 'YTD', '1Y', '3Y'],
                    datasets: [{
                        label: 'Total Return (%)',
                        data: [2.5, 5.2, 8.1, 12.3, 45.6],
                        backgroundColor: ['#4CAF50', '#4CAF50', '#4CAF50', '#4CAF50', '#4CAF50'],
                        borderColor: '#388E3C',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { display: true, text: 'Portfolio Performance (Sample)' }
                    },
                    scales: {
                        y: {
                            title: { display: true, text: 'Return (%)' }
                        }
                    }
                }
            });
            console.log('Sample performance chart created successfully!');
        } catch (error) {
            console.error('Sample performance chart error:', error);
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
                            data: [25000, 28000, 23000, 30000, 26000, 29000],
                            backgroundColor: '#F44336',
                            borderColor: '#D32F2F',
                            borderWidth: 1
                        },
                        {
                            label: 'Investments',
                            data: [10000, 10000, 10000, 10000, 10000, 10000],
                            backgroundColor: '#9C27B0',
                            borderColor: '#7B1FA2',
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
        // Check financial_analysis balance_sheet section
        else if (apiData.financial_analysis && apiData.financial_analysis.balance_sheet && 
                 apiData.financial_analysis.balance_sheet.allocation && 
                 apiData.financial_analysis.balance_sheet.allocation.asset_allocation) {
            allocationData = apiData.financial_analysis.balance_sheet.allocation.asset_allocation;
            console.log('Found balance_sheet allocation data:', allocationData);
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
            // Check if this is the new format (objects with percentage/value) or simple numeric values
            const firstKey = Object.keys(allocationData)[0];
            const firstValue = allocationData[firstKey];
            const isNewFormat = typeof firstValue === 'object' && firstValue.hasOwnProperty('percentage') && firstValue.hasOwnProperty('value');
            
            let totalValue = 0;
            
            if (isNewFormat) {
                // New format: objects with percentage and value
                console.log('Processing new format allocation data');
                Object.keys(allocationData).forEach(key => {
                    const item = allocationData[key];
                    if (item && typeof item === 'object' && item.value) {
                        const translatedKey = assetTranslations[key] || key;
                        chartData.push({
                            label: translatedKey,
                            value: parseFloat(item.percentage) || 0,
                            amount: parseFloat(item.value) || 0,
                            color: assetColors[translatedKey] || '#999999'
                        });
                        totalValue += parseFloat(item.value) || 0;
                    }
                });
            } else {
                // Old format: simple numeric values
                console.log('Processing simple format allocation data');
                totalValue = Object.values(allocationData).reduce((sum, value) => {
                    return sum + (typeof value === 'number' ? value : parseFloat(value) || 0);
                }, 0);
                
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
            
            console.log('Total portfolio value:', totalValue);
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
        const incomeTrends = cashFlow.income_trends?.trend_data;
        const expenseTrends = cashFlow.expense_trends?.trend_data;
        
        if (!incomeTrends) {
            console.log('Missing income trend data');
            return null;
        }
        
        // Check if we have the expected structure with date-keyed data
        let incomeData = null;
        let expenseData = null;
        let investmentData = null;
        
        if (incomeTrends.Total_Income_Calc_CNY) {
            incomeData = incomeTrends.Total_Income_Calc_CNY;
            console.log('Found Total_Income_Calc_CNY data');
        }
        
        if (expenseTrends && expenseTrends.Total_Expense_Calc_CNY) {
            expenseData = expenseTrends.Total_Expense_Calc_CNY;
            console.log('Found Total_Expense_Calc_CNY data (corrected - no investments)');
        }
        
        // Enhanced: Look for investment data
        if (expenseTrends && expenseTrends.Total_Investment_Calc_CNY) {
            investmentData = expenseTrends.Total_Investment_Calc_CNY;
            console.log('Found Total_Investment_Calc_CNY data (dedicated investment tracking)');
        } else if (incomeTrends.Total_Investment_Calc_CNY) {
            investmentData = incomeTrends.Total_Investment_Calc_CNY;
            console.log('Found Total_Investment_Calc_CNY data in income trends');
        }
        
        if (!incomeData) {
            console.log('No income data found');
            return null;
        }
        
        // Convert date-keyed data to arrays
        const incomeDates = Object.keys(incomeData).sort();
        const recentDates = incomeDates.slice(-12); // Last 12 months
        
        const monthlyData = [];
        
        for (const dateKey of recentDates) {
            const date = new Date(dateKey);
            const monthLabel = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
            
            const income = incomeData[dateKey] || 0;
            const expense = expenseData ? (expenseData[dateKey] || 0) : 0;
            const investment = investmentData ? (investmentData[dateKey] || 0) : 0;
            
            monthlyData.push({
                month: monthLabel,
                income: Math.round(income),
                expense: Math.round(expense),
                investment: Math.round(investment),
                net: Math.round(income - expense - investment)  // Enhanced: Include investment in net calculation
            });
        }
        
        console.log('Extracted cash flow data for', monthlyData.length, 'months');
        return monthlyData;
        
    } catch (error) {
        console.error('Error extracting cash flow data:', error);
        return null;
    }
}

// Function to extract net worth trend data from API response
function extractNetWorthData(apiData) {
    try {
        console.log('Extracting net worth data...');
        
        if (!apiData || !apiData.financial_analysis || !apiData.financial_analysis.balance_sheet || 
            !apiData.financial_analysis.balance_sheet.trends || !apiData.financial_analysis.balance_sheet.trends.trend_data) {
            console.log('No balance sheet trends data found in API response');
            return null;
        }
        
        const trendsData = apiData.financial_analysis.balance_sheet.trends.trend_data;
        const netWorthData = trendsData.Net_Worth_Calc_CNY;
        const assetsData = trendsData.Total_Assets_Calc_CNY;
        const liabilitiesData = trendsData.Total_Liabilities_Calc_CNY;
        
        if (!netWorthData) {
            console.log('No net worth data found');
            return null;
        }
        
        // Convert date-keyed data to arrays and get last 24 months
        const dates = Object.keys(netWorthData).sort();
        const recentDates = dates.slice(-24); // Last 24 months
        
        const chartData = {
            labels: [],
            netWorth: [],
            assets: [],
            liabilities: []
        };
        
        for (const dateKey of recentDates) {
            const date = new Date(dateKey);
            const monthLabel = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
            
            chartData.labels.push(monthLabel);
            chartData.netWorth.push(Math.round(netWorthData[dateKey] || 0));
            chartData.assets.push(Math.round(assetsData[dateKey] || 0));
            chartData.liabilities.push(Math.round(liabilitiesData[dateKey] || 0));
        }
        
        console.log('Extracted net worth data for', chartData.labels.length, 'months');
        return chartData;
        
    } catch (error) {
        console.error('Error extracting net worth data:', error);
        return null;
    }
}

// Function to extract portfolio performance data from API response
function extractPerformanceData(apiData) {
    try {
        console.log('Extracting performance data...');
        
        if (!apiData || !apiData.financial_analysis || !apiData.financial_analysis.investment || 
            !apiData.financial_analysis.investment.portfolio_metrics) {
            console.log('No portfolio metrics data found in API response');
            return null;
        }
        
        const metrics = apiData.financial_analysis.investment.portfolio_metrics;
        const periods = ['3M', '6M', 'YTD', '1Y', '3Y', 'All'];
        
        const performanceData = {
            labels: [],
            returns: [],
            maxDrawdowns: []
        };
        
        for (const period of periods) {
            if (metrics[period] && metrics[period].status === 'success') {
                performanceData.labels.push(period);
                performanceData.returns.push(parseFloat(metrics[period].total_return_pct) || 0);
                performanceData.maxDrawdowns.push(Math.abs(parseFloat(metrics[period].max_drawdown_pct) || 0));
            }
        }
        
        console.log('Extracted performance data for', performanceData.labels.length, 'periods');
        return performanceData.labels.length > 0 ? performanceData : null;
        
    } catch (error) {
        console.error('Error extracting performance data:', error);
        return null;
    }
}

// Function to extract recommendations from API data
function extractRecommendationsData(apiData) {
    try {
        console.log('🔍 Extracting recommendations data...');
        
        const recommendations = [];
        
        // Check for new recommendation structure
        if (apiData.recommendations) {
            const recs = apiData.recommendations;
            
            // Financial recommendations
            if (recs.financial_recommendations && Array.isArray(recs.financial_recommendations)) {
                recs.financial_recommendations.forEach(rec => {
                    const urgency = rec.urgency && rec.urgency._name_ ? rec.urgency._name_.toLowerCase() : 'medium';
                    const priority = urgency === 'critical' ? 'High' : urgency === 'high' ? 'High' : urgency === 'low' ? 'Low' : 'Medium';
                    
                    recommendations.push({
                        category: 'Financial Planning',
                        title: rec.title || 'Financial Recommendation',
                        description: rec.description || 'Financial planning recommendation',
                        priority: priority,
                        details: JSON.stringify({
                            action_steps: rec.action_steps || [],
                            estimated_benefit: rec.estimated_benefit,
                            implementation_time: rec.implementation_time,
                            ease_score: rec.ease_score,
                            impact_score: rec.impact_score
                        })
                    });
                });
            }
            
            // Portfolio recommendations
            if (recs.portfolio_recommendations && Array.isArray(recs.portfolio_recommendations)) {
                recs.portfolio_recommendations.forEach(rec => {
                    const urgency = typeof rec.urgency === 'string' ? rec.urgency : 'medium';
                    const priority = urgency === 'high' ? 'High' : urgency === 'low' ? 'Low' : 'Medium';
                    
                    recommendations.push({
                        category: 'Portfolio Management',
                        title: rec.title || 'Portfolio Recommendation',
                        description: rec.description || 'Portfolio management recommendation',
                        priority: priority,
                        details: JSON.stringify({
                            current_allocation: rec.current_allocation,
                            target_allocation: rec.target_allocation,
                            specific_actions: rec.specific_actions || [],
                            implementation_cost: rec.implementation_cost,
                            ease_score: rec.ease_score,
                            impact_score: rec.impact_score
                        })
                    });
                });
            }
            
            // Risk recommendations
            if (recs.risk_recommendations && Array.isArray(recs.risk_recommendations)) {
                recs.risk_recommendations.forEach(rec => {
                    const priority_num = parseInt(rec.priority) || 3;
                    const priority = priority_num <= 2 ? 'High' : priority_num <= 3 ? 'Medium' : 'Low';
                    const risk_type = rec.risk_type && rec.risk_type._name_ ? rec.risk_type._name_ : 'General';
                    
                    recommendations.push({
                        category: `Risk Management (${risk_type})`,
                        title: rec.action || 'Risk Management Action',
                        description: rec.rationale || 'Risk management recommendation',
                        priority: priority,
                        details: JSON.stringify({
                            action: rec.action,
                            rationale: rec.rationale,
                            expected_impact: rec.expected_impact,
                            effort_level: rec.effort_level,
                            timeline: rec.timeline,
                            risk_type: risk_type
                        })
                    });
                });
            }
        }
        
        console.log(`✅ Extracted ${recommendations.length} real recommendations:`, recommendations);
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
            console.log('⚠️ No recommendations data available');
            
            // Create a single row indicating no recommendations
            const row = document.createElement('tr');
            row.innerHTML = `
                <td colspan="4" style="text-align: center; padding: 20px; color: #666; font-style: italic;">
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 10px;">
                        <div style="font-size: 18px;">📋</div>
                        <div style="font-size: 14px;">No recommendations generated</div>
                        <div style="font-size: 12px; color: #999;">
                            The system has not generated any specific recommendations at this time.
                        </div>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
            return;
        }
        
        // Sort recommendations by priority: High → Medium → Low
        const priorityOrder = { 'High': 1, 'Medium': 2, 'Low': 3 };
        const sortedRecommendations = [...recommendationsData].sort((a, b) => {
            return priorityOrder[a.priority] - priorityOrder[b.priority];
        });
        
        sortedRecommendations.forEach((rec, index) => {
            const row = document.createElement('tr');
            
            // Get priority class
            const priorityClass = rec.priority.toLowerCase() === 'high' ? 'priority-high' :
                                 rec.priority.toLowerCase() === 'medium' ? 'priority-medium' : 'priority-low';
            
            row.innerHTML = `
                <td style="text-align: center; vertical-align: middle;">
                    <span class="priority-badge ${priorityClass}">${rec.priority}</span>
                </td>
                <td style="font-size: 14px; vertical-align: middle; font-weight: 500;">
                    ${rec.category}
                </td>
                <td style="vertical-align: middle;">
                    <div style="font-size: 14px; font-weight: 600; color: #333; margin-bottom: 4px;">
                        ${rec.title}
                    </div>
                    <div style="font-size: 13px; color: #666; line-height: 1.4;">
                        ${rec.description}
                    </div>
                </td>
                <td style="text-align: center; vertical-align: middle;">
                    <button class="btn-details" onclick="showRecommendationDetails(${index})" 
                        data-details='${rec.details}' style="font-size: 12px;">
                        View Details
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
        // Store sorted recommendations globally for details view
        window.currentRecommendations = sortedRecommendations;
        
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

// Function to extract detailed sub-category asset allocation data from API response
function extractSubCategoryAllocationData(apiData) {
    try {
        console.log('🔍 Extracting sub-category asset allocation data...');
        
        // Check for sub_level holdings mapping data
        if (!apiData.portfolio_analysis || 
            !apiData.portfolio_analysis.holdings_mapping || 
            !apiData.portfolio_analysis.holdings_mapping.sub_level) {
            console.log('No sub-category allocation data found in API response');
            return null;
        }
        
        const subLevelData = apiData.portfolio_analysis.holdings_mapping.sub_level;
        console.log('Found sub-level data:', subLevelData);
        
        // Convert data to chart format with better categorization
        const chartData = [];
        
        // Enhanced sub-category translations and color scheme
        const subCategoryTranslations = {
            '住宅地产': 'Residential Real Estate',
            '保险': 'Insurance Products', 
            '公司美股RSU': 'Company Stock (RSU)',
            '国内政府债券': 'Domestic Government Bonds',
            '国内股票ETF': 'Domestic Equity ETFs',
            '活期存款': 'Demand Deposits',
            '现金': 'Cash Holdings',
            '美国股票ETF': 'US Equity ETFs',
            '货币市场': 'Money Market Funds',
            '黄金': 'Gold Holdings'
        };
        
        // Color scheme optimized for 10+ categories with good contrast
        const subCategoryColors = {
            'Residential Real Estate': '#FF6B6B',    // Coral red
            'Insurance Products': '#4ECDC4',         // Teal
            'Company Stock (RSU)': '#45B7D1',       // Sky blue
            'Domestic Government Bonds': '#96CEB4',  // Mint green
            'Domestic Equity ETFs': '#FFEAA7',       // Light yellow
            'Demand Deposits': '#DDA0DD',            // Plum
            'Cash Holdings': '#98D8C8',              // Mint
            'US Equity ETFs': '#F7DC6F',             // Gold
            'Money Market Funds': '#BB8FCE',         // Light purple
            'Gold Holdings': '#F8C471'               // Orange gold
        };
        
        // Calculate total for percentage calculations
        const totalValue = Object.values(subLevelData).reduce((sum, value) => {
            return sum + (typeof value === 'number' ? value : parseFloat(value) || 0);
        }, 0);
        
        console.log('Total sub-category portfolio value:', totalValue);
        
        // Process each sub-category
        Object.keys(subLevelData).forEach(key => {
            const value = subLevelData[key];
            const numericValue = typeof value === 'number' ? value : parseFloat(value);
            
            if (!isNaN(numericValue) && numericValue > 0) {
                const translatedKey = subCategoryTranslations[key] || key;
                const percentage = (numericValue / totalValue * 100);
                
                chartData.push({
                    label: translatedKey,
                    value: percentage,
                    amount: numericValue,
                    color: subCategoryColors[translatedKey] || '#95A5A6' // Default gray
                });
            }
        });
        
        // Sort by value (largest first) for better visualization
        chartData.sort((a, b) => b.value - a.value);
        
        console.log(`✅ Extracted ${chartData.length} sub-category allocation items:`, chartData);
        return chartData.length > 0 ? chartData : null;
        
    } catch (error) {
        console.error('Error extracting sub-category allocation data:', error);
        return null;
    }
}

// ===== NEW COMPREHENSIVE ANALYSIS FUNCTIONS =====

// Load comprehensive analysis data from all new endpoints
function loadComprehensiveAnalysis() {
    console.log('🚀 Loading comprehensive analysis data...');
    
    // Update debug info
    updateDebugInfo('chart-status', 'Loading comprehensive analysis...');
    
    // Load each component
    loadPortfolioOverview();
    // loadCashFlowForecast(); // Temporarily disabled for faster loading
    loadCashFlowForecastPlaceholder(); // Show placeholder instead
    loadGoalPlanning();
    loadPerformanceAttribution();
    loadRecommendations();
}

// Load Portfolio Overview
function loadPortfolioOverview() {
    console.log('💰 Loading portfolio overview...');
    
    fetch('/api/portfolio_overview')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const portfolioData = data.data;
                
                // Update portfolio metrics
                document.getElementById('total-portfolio-value').textContent = 
                    formatCurrency(portfolioData.total_portfolio_value);
                document.getElementById('holdings-count').textContent = 
                    portfolioData.current_holdings_count;
                document.getElementById('historical-records').textContent = 
                    portfolioData.historical_records;
                
                console.log('✅ Portfolio overview loaded successfully');
            } else {
                console.error('❌ Portfolio overview API error:', data.message);
                updatePortfolioError();
            }
        })
        .catch(error => {
            console.error('❌ Portfolio overview fetch error:', error);
            updatePortfolioError();
        });
}

// Load Cash Flow Forecast
function loadCashFlowForecast() {
    console.log('📈 Loading cash flow forecast...');
    updateDebugInfo('api-status', 'Calling /api/cash_flow_forecast...');
    
    fetch('/api/cash_flow_forecast')
        .then(response => {
            console.log('📈 Cash flow forecast response status:', response.status);
            updateDebugInfo('api-status', `Cash flow API responded: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('📈 Cash flow forecast data received:', data);
            updateDebugInfo('data-status', 'Cash flow data loaded');
            
            if (data.status === 'success') {
                const forecastData = data.data;
                
                // Update forecast metrics
                const historicalPeriodsEl = document.getElementById('forecast-historical-periods');
                const modelStatusEl = document.getElementById('forecast-model-status');
                
                if (historicalPeriodsEl) {
                    historicalPeriodsEl.textContent = forecastData.historical_periods;
                }
                if (modelStatusEl) {
                    modelStatusEl.textContent = forecastData.model_status.join(', ');
                }
                
                // Create forecast chart if data is available
                if (forecastData.forecast && Array.isArray(forecastData.forecast)) {
                    console.log('📊 Creating forecast chart with', forecastData.forecast.length, 'data points');
                    updateDebugInfo('chart-status', `Creating chart with ${forecastData.forecast.length} points`);
                    createCashFlowForecastChart(forecastData.forecast);
                } else {
                    console.warn('⚠️ No forecast data available for chart');
                    updateDebugInfo('chart-status', 'No forecast data available');
                }
                
                console.log('✅ Cash flow forecast loaded successfully');
            } else {
                console.error('❌ Cash flow forecast API error:', data.message);
                updateDebugInfo('chart-status', `API Error: ${data.message}`);
                updateForecastError();
            }
        })
        .catch(error => {
            console.error('❌ Cash flow forecast fetch error:', error);
            updateDebugInfo('chart-status', `Fetch Error: ${error.message}`);
            updateForecastError();
        });
}

// Load Cash Flow Forecast Placeholder (SARIMA disabled for faster loading)
function loadCashFlowForecastPlaceholder() {
    console.log('📈 Loading cash flow forecast placeholder...');
    updateDebugInfo('api-status', 'Cash flow forecast disabled for faster loading');
    
    // Update forecast metrics with placeholder values
    const historicalPeriodsEl = document.getElementById('forecast-historical-periods');
    const modelStatusEl = document.getElementById('forecast-model-status');
    
    if (historicalPeriodsEl) {
        historicalPeriodsEl.textContent = '69 months';
    }
    if (modelStatusEl) {
        modelStatusEl.textContent = 'SARIMA disabled for faster loading';
    }
    
    // Create placeholder chart
    createCashFlowForecastPlaceholder();
    
    console.log('✅ Cash flow forecast placeholder loaded');
}

// Load Goal Planning
function loadGoalPlanning() {
    console.log('🎯 Loading goal planning...');
    
    fetch('/api/goal_planning')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const goalData = data.data;
                
                // Update goal metrics
                document.getElementById('simulation-iterations').textContent = 
                    goalData.simulation_iterations;
                document.getElementById('projection-years').textContent = 
                    goalData.projection_years;
                document.getElementById('final-value-median').textContent = 
                    formatCurrency(goalData.final_value_median);
                
                // Update goal probabilities
                updateGoalProbabilities(goalData.goal_probabilities);
                
                console.log('✅ Goal planning loaded successfully');
            } else {
                console.error('❌ Goal planning API error:', data.message);
                updateGoalError();
            }
        })
        .catch(error => {
            console.error('❌ Goal planning fetch error:', error);
            updateGoalError();
        });
}

// Load Performance Attribution
function loadPerformanceAttribution() {
    console.log('📊 Loading performance attribution...');
    
    fetch('/api/performance_attribution')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const attributionData = data.data;
                
                // Update attribution metrics
                document.getElementById('attribution-periods').textContent = 
                    attributionData.analysis_periods || 'N/A';
                document.getElementById('allocation-effect').textContent = 
                    formatPercentage(attributionData.cumulative_allocation_effect);
                document.getElementById('selection-effect').textContent = 
                    formatPercentage(attributionData.cumulative_selection_effect);
                document.getElementById('excess-return').textContent = 
                    formatPercentage(attributionData.total_excess_return);
                
                console.log('✅ Performance attribution loaded successfully');
            } else {
                console.error('❌ Performance attribution API error:', data.message);
                updateAttributionError();
            }
        })
        .catch(error => {
            console.error('❌ Performance attribution fetch error:', error);
            updateAttributionError();
        });
}

// Load Recommendations
function loadRecommendations() {
    console.log('🧠 Loading recommendations...');
    
    fetch('/api/recommendations')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const recData = data.data;
                
                // Update recommendation counts
                document.getElementById('financial-recommendations-count').textContent = 
                    recData.financial_recommendations_count;
                document.getElementById('portfolio-recommendations-count').textContent = 
                    recData.portfolio_recommendations_count;
                document.getElementById('risk-recommendations-count').textContent = 
                    recData.risk_recommendations_count;
                document.getElementById('tax-recommendations-count').textContent = 
                    recData.tax_recommendations_count;
                
                console.log('✅ Recommendations loaded successfully');
            } else {
                console.error('❌ Recommendations API error:', data.message);
                updateRecommendationsError();
            }
        })
        .catch(error => {
            console.error('❌ Recommendations fetch error:', error);
            updateRecommendationsError();
        });
}

// Helper functions for chart creation and error handling
function createCashFlowForecastChart(forecastData) {
    const ctx = document.getElementById('cashflowForecastChart');
    if (!ctx) {
        console.error('❌ Canvas element cashflowForecastChart not found');
        return;
    }
    
    console.log('📊 Creating cash flow forecast chart with data:', forecastData);
    
    try {
        // Extract data for chart
        const labels = forecastData.map((item, index) => `Month ${index + 1}`);
        const incomeData = forecastData.map(item => item.Income_Forecast || 0);
        const expenseData = forecastData.map(item => item.Expenses_Forecast || 0);
        const netData = forecastData.map(item => item.Net_Cash_Flow_Forecast || 0);
        
        // Destroy existing chart if it exists
        if (window.cashflowForecastChart) {
            window.cashflowForecastChart.destroy();
        }
        
        window.cashflowForecastChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Income Forecast',
                        data: incomeData,
                        borderColor: '#27AE60',
                        backgroundColor: 'rgba(39, 174, 96, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'Expenses Forecast',
                        data: expenseData,
                        borderColor: '#E74C3C',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'Net Cash Flow',
                        data: netData,
                        borderColor: '#3498DB',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '12-Month Cash Flow Forecast'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });
        
        console.log('✅ Cash flow forecast chart created successfully');
    } catch (error) {
        console.error('❌ Error creating cash flow forecast chart:', error);
    }
}

// Create placeholder cash flow forecast chart (SARIMA disabled)
function createCashFlowForecastPlaceholder() {
    const ctx = document.getElementById('cashflowForecastChart');
    if (!ctx) {
        console.error('❌ Canvas element cashflowForecastChart not found');
        return;
    }
    
    console.log('📊 Creating cash flow forecast placeholder chart');
    
    try {
        // Create sample data for demonstration
        const labels = Array.from({length: 12}, (_, i) => `Month ${i + 1}`);
        const placeholderData = Array.from({length: 12}, () => 50000 + Math.random() * 20000);
        
        // Destroy existing chart if it exists
        if (window.cashflowForecastChart) {
            window.cashflowForecastChart.destroy();
        }
        
        window.cashflowForecastChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Cash Flow Forecast (Placeholder)',
                        data: placeholderData,
                        borderColor: '#95A5A6',
                        backgroundColor: 'rgba(149, 165, 166, 0.1)',
                        borderDash: [5, 5],
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Cash Flow Forecast (SARIMA Disabled for Performance)'
                    },
                    subtitle: {
                        display: true,
                        text: 'Enable SARIMA in settings for detailed forecasting'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Amount (CNY)'
                        }
                    }
                }
            }
        });
        
        console.log('✅ Cash flow forecast placeholder chart created successfully');
    } catch (error) {
        console.error('❌ Error creating cash flow forecast placeholder chart:', error);
    }
}

function updateGoalProbabilities(goalProbabilities) {
    const container = document.getElementById('goal-probabilities-list');
    if (!container) return;
    
    if (Object.keys(goalProbabilities).length === 0) {
        container.innerHTML = '<p>No goal data available</p>';
        return;
    }
    
    let html = '';
    for (const [goalId, probability] of Object.entries(goalProbabilities)) {
        const progressClass = probability >= 0.8 ? 'high' : probability >= 0.6 ? 'medium' : 'low';
        html += `
            <div class="goal-probability-item ${progressClass}">
                <span class="goal-name">${goalId.replace('_', ' ').toUpperCase()}</span>
                <span class="goal-probability">${formatPercentage(probability)}</span>
            </div>
        `;
    }
    container.innerHTML = html;
}

// Error handling functions
function updatePortfolioError() {
    document.getElementById('total-portfolio-value').textContent = 'Error loading';
    document.getElementById('holdings-count').textContent = 'Error';
    document.getElementById('historical-records').textContent = 'Error';
}

function updateForecastError() {
    document.getElementById('forecast-historical-periods').textContent = 'Error';
    document.getElementById('forecast-model-status').textContent = 'Error loading';
}

function updateGoalError() {
    document.getElementById('simulation-iterations').textContent = 'Error';
    document.getElementById('projection-years').textContent = 'Error';
    document.getElementById('final-value-median').textContent = 'Error loading';
    document.getElementById('goal-probabilities-list').innerHTML = '<p>Error loading goals</p>';
}

function updateAttributionError() {
    document.getElementById('attribution-periods').textContent = 'Error';
    document.getElementById('allocation-effect').textContent = 'Error';
    document.getElementById('selection-effect').textContent = 'Error';
    document.getElementById('excess-return').textContent = 'Error';
}

function updateRecommendationsError() {
    document.getElementById('financial-recommendations-count').textContent = 'Error';
    document.getElementById('portfolio-recommendations-count').textContent = 'Error';
    document.getElementById('risk-recommendations-count').textContent = 'Error';
    document.getElementById('tax-recommendations-count').textContent = 'Error';
}

// Utility formatting functions
function formatCurrency(value) {
    if (typeof value !== 'number' || isNaN(value)) return 'N/A';
    return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function formatPercentage(value) {
    if (typeof value !== 'number' || isNaN(value)) return 'N/A';
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

// Debug helper function
function updateDebugInfo(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
    }
    console.log(`Debug [${elementId}]: ${message}`);
}

// Update the original loadRealDataAndCreateCharts function to also load comprehensive analysis
const originalLoadFunction = loadRealDataAndCreateCharts;
loadRealDataAndCreateCharts = function() {
    console.log('🔄 Enhanced loadRealDataAndCreateCharts starting...');
    
    // Call original function
    originalLoadFunction();
    
    // Add comprehensive analysis
    setTimeout(() => {
        console.log('🚀 Loading comprehensive analysis after original data...');
        loadComprehensiveAnalysis();
    }, 1000);
};
