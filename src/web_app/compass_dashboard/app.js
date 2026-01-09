/**
 * Investment Compass Dashboard JavaScript
 * Handles data fetching and UI updates for the dashboard
 */

// ===== DATA SAFETY LAYER =====
// Critical utility functions to prevent null/undefined crashes

/**
 * Safely get a nested property with fallback value
 * @param {Object} obj - The object to traverse
 * @param {string} path - Dot-notation path (e.g., 'portfolio_snapshot.total_value')
 * @param {*} defaultValue - Fallback value if path doesn't exist
 * @returns {*} The value at path or defaultValue
 */
function safeGet(obj, path, defaultValue = null) {
    if (!obj || typeof obj !== 'object') return defaultValue;
    
    const keys = path.split('.');
    let current = obj;
    
    for (const key of keys) {
        if (current === null || current === undefined || !(key in current)) {
            return defaultValue;
        }
        current = current[key];
    }
    
    return current !== null && current !== undefined ? current : defaultValue;
}

/**
 * Safely format a number with proper null handling
 * @param {number} value - The number to format
 * @param {number} decimals - Number of decimal places (default: 1)
 * @param {string} fallback - Fallback string if value is invalid
 * @returns {string} Formatted number or fallback
 */
function safeToFixed(value, decimals = 1, fallback = '0.0') {
    if (value === null || value === undefined || isNaN(value)) {
        return fallback;
    }
    return Number(value).toFixed(decimals);
}

/**
 * Format number with thousands separator and proper null handling
 * @param {number} value - The number to format
 * @param {string} fallback - Fallback string if value is invalid
 * @returns {string} Formatted number with commas or fallback
 */
function safeFormatNumber(value, fallback = '0') {
    if (value === null || value === undefined || isNaN(value)) {
        return fallback;
    }
    return Number(value).toLocaleString();
}

/**
 * Safely get array with fallback to empty array
 * @param {*} value - Potential array value
 * @returns {Array} The array or empty array if invalid
 */
function safeArray(value) {
    return Array.isArray(value) ? value : [];
}

/**
 * Safely get string with fallback
 * @param {*} value - Potential string value
 * @param {string} fallback - Fallback string
 * @returns {string} The string or fallback
 */
function safeString(value, fallback = '') {
    return (value !== null && value !== undefined) ? String(value) : fallback;
}

// Configuration
const CONFIG = {
    API_BASE_URL: '', // Use relative path
    MOCK_API_ENDPOINT: '/api/unified_analysis', // Use real analysis endpoint
    REFRESH_INTERVAL: 300000, // 5 minutes in milliseconds
};

// Global state
let dashboardData = null;
let lastUpdateTime = null;

/**
 * Initialize the dashboard when the page loads
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Investment Compass Dashboard loading...');
    initializeDashboard();
});

/**
 * Initialize the dashboard
 */
async function initializeDashboard() {
    try {
        // Show loading states
        showLoadingStates();
        
        // Fetch data from mock API
        await fetchDashboardData();
        
        // Populate all dashboard components
        populateAllComponents();
        
        // Set up auto-refresh
        setupAutoRefresh();
        
        console.log('Dashboard initialized successfully');
    } catch (error) {
        console.error('Failed to initialize dashboard:', error);
        showErrorStates('Failed to load dashboard data');
    }
}

/**
 * Show loading states for all components
 */
function showLoadingStates() {
    const components = [
        'portfolio-snapshot',
        'asset-allocation', 
        'rebalancing-advice',
        'single-asset-risk'
    ];
    
    components.forEach(componentId => {
        const element = document.getElementById(componentId);
        if (element) {
            element.innerHTML = '<div class="loading">Loading data...</div>';
        }
    });
}

/**
 * Show error states for all components
 */
function showErrorStates(message) {
    const components = [
        'portfolio-snapshot',
        'asset-allocation',
        'rebalancing-advice', 
        'single-asset-risk'
    ];
    
    components.forEach(componentId => {
        const element = document.getElementById(componentId);
        if (element) {
            element.innerHTML = `<div class="error">${message}</div>`;
        }
    });
}

/**
 * Fetch data from the mock API endpoint
 */
async function fetchDashboardData() {
    try {
        const url = CONFIG.API_BASE_URL + CONFIG.MOCK_API_ENDPOINT;
        console.log('Fetching data from:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.status} ${response.statusText}`);
        }
        
        dashboardData = await response.json();
        lastUpdateTime = new Date();
        
        console.log('Dashboard data fetched successfully:', dashboardData);
        
        // Update the last updated timestamp
        updateLastUpdatedTime();
        
        return dashboardData;
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        throw error;
    }
}

/**
 * Update the last updated timestamp in the header
 */
function updateLastUpdatedTime() {
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement && lastUpdateTime) {
        lastUpdatedElement.textContent = `Last updated: ${lastUpdateTime.toLocaleString()}`;
    }
}

/**
 * Populate all dashboard components with data
 */
function populateAllComponents() {
    if (!dashboardData) {
        console.error('No dashboard data available');
        return;
    }
    
    populatePortfolioSnapshot();
    populateAssetAllocation();
    populateRebalancingAdvice();
    populateSingleAssetRisk();
}

/**
 * Populate the portfolio snapshot component with data-safe access
 */
function populatePortfolioSnapshot() {
    const container = document.getElementById('portfolio-snapshot');
    
    if (!container) {
        console.error('Portfolio snapshot container not found');
        return;
    }
    
    // Use data-safe access to get portfolio snapshot data
    const totalValue = safeGet(dashboardData, 'portfolio_snapshot.total_value', 0);
    const holdingsCount = safeGet(dashboardData, 'portfolio_snapshot.holdings_count', 0);
    const lastUpdated = safeGet(dashboardData, 'portfolio_snapshot.last_updated', new Date().toISOString());
    
    // Single asset risk data with safe access
    const riskTicker = safeGet(dashboardData, 'portfolio_snapshot.single_asset_risk.ticker', 'N/A');
    const riskPercentage = safeGet(dashboardData, 'portfolio_snapshot.single_asset_risk.percentage', 0);
    const riskLevel = safeGet(dashboardData, 'portfolio_snapshot.single_asset_risk.level', '风险未知');
    
    // Create the main portfolio metrics section with safe formatting
    const portfolioMetricsHtml = `
        <div class="portfolio-metrics">
            <div class="metric-card primary">
                <div class="metric-label">Total Portfolio Value</div>
                <div class="metric-value">¥${safeFormatNumber(totalValue)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Holdings</div>
                <div class="metric-value">${safeFormatNumber(holdingsCount)}</div>
                <div class="metric-subtitle">individual assets</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Last Updated</div>
                <div class="metric-value">${formatDate(lastUpdated)}</div>
                <div class="metric-subtitle">${formatTime(lastUpdated)}</div>
            </div>
        </div>
    `;
    
    // Create the single asset risk section with safe data access
    const riskClass = getRiskClass(riskLevel);
    const riskSectionHtml = `
        <div class="single-asset-risk-section">
            <h4 class="risk-section-title">Single Asset Concentration Risk</h4>
            <div class="risk-details">
                <div class="risk-asset">
                    <div class="risk-asset-name">
                        <span class="asset-label">Largest Holding:</span>
                        <span class="asset-ticker">${safeString(riskTicker, 'N/A')}</span>
                    </div>
                    <div class="risk-concentration">
                        <div class="concentration-bar">
                            <div class="concentration-fill" style="width: ${Math.min(riskPercentage, 100)}%"></div>
                        </div>
                        <span class="concentration-percentage">${safeToFixed(riskPercentage, 1)}%</span>
                    </div>
                </div>
                <div class="risk-assessment">
                    <span class="risk-level-badge ${riskClass}">${safeString(riskLevel, '风险未知')}</span>
                    <p class="risk-description">${getRiskDescription(riskLevel, riskPercentage)}</p>
                </div>
            </div>
        </div>
    `;
    
    // Combine all sections
    container.innerHTML = portfolioMetricsHtml + riskSectionHtml;
}

/**
 * Populate the asset allocation component
 */
function populateAssetAllocation() {
    const container = document.getElementById('asset-allocation');
    const allocations = dashboardData.asset_allocation_details;
    
    if (!allocations || allocations.length === 0) {
        container.innerHTML = '<div class="error">Asset allocation data not available</div>';
        return;
    }
    
    // Render the donut chart
    renderAllocationChart(allocations);
    
    // Sort allocations by actual percentage (descending)
    const sortedAllocations = [...allocations].sort((a, b) => b.actual_pct - a.actual_pct);
    
    // Create allocation summary section
    const summaryHtml = `
        <div class="allocation-summary">
            <h3>Portfolio Distribution</h3>
            <div class="allocation-stats">
                <div class="stat-item">
                    <span class="stat-label">Asset Categories</span>
                    <span class="stat-value">${allocations.length}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Total Value</span>
                    <span class="stat-value">¥${formatNumber(allocations.reduce((sum, a) => sum + a.market_value, 0))}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Largest Category</span>
                    <span class="stat-value">${sortedAllocations[0].category} (${sortedAllocations[0].actual_pct.toFixed(1)}%)</span>
                </div>
            </div>
        </div>
    `;
    
    // Create detailed table
    let tableHtml = `
        <div class="allocation-table-container">
            <h3>Detailed Breakdown</h3>
            <table class="allocation-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Target %</th>
                        <th>Actual %</th>
                        <th>Deviation %</th>
                        <th>Market Value</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    sortedAllocations.forEach((allocation, index) => {
        const deviationClass = getDeviationClass(allocation.deviation_pct);
        const statusIcon = getStatusIcon(allocation.deviation_pct);
        const rowClass = allocation.actual_pct > 30 ? 'high-allocation' : '';
        
        tableHtml += `
            <tr class="allocation-row ${rowClass}">
                <td class="category-cell">
                    <div class="category-info">
                        <span class="category-indicator" style="background-color: ${getChartColor(index)}"></span>
                        <span class="category-name">${allocation.category}</span>
                    </div>
                </td>
                <td class="percentage-cell">${allocation.target_pct.toFixed(1)}%</td>
                <td class="percentage-cell actual">
                    <span class="percentage-bar">
                        <span class="percentage-fill" style="width: ${allocation.actual_pct}%; background-color: ${getChartColor(index)}"></span>
                    </span>
                    ${allocation.actual_pct.toFixed(1)}%
                </td>
                <td class="deviation-cell ${deviationClass}">
                    ${allocation.deviation_pct > 0 ? '+' : ''}${allocation.deviation_pct.toFixed(1)}%
                </td>
                <td class="value-cell">¥${formatNumber(allocation.market_value)}</td>
                <td class="status-cell">
                    <span class="status-icon">${statusIcon}</span>
                </td>
            </tr>
        `;
    });
    
    tableHtml += '</tbody></table></div>';
    
    // Combine all sections
    container.innerHTML = summaryHtml + tableHtml;
}

/**
 * Render the allocation donut chart
 */
function renderAllocationChart(allocations) {
    const ctx = document.getElementById('allocation-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (window.allocationChart) {
        window.allocationChart.destroy();
    }
    
    // Sort allocations by percentage for better visualization
    const sortedAllocations = [...allocations].sort((a, b) => b.actual_pct - a.actual_pct);
    
    const chartData = {
        labels: sortedAllocations.map(a => a.category),
        datasets: [{
            data: sortedAllocations.map(a => a.actual_pct),
            backgroundColor: sortedAllocations.map((_, index) => getChartColor(index)),
            borderColor: '#ffffff',
            borderWidth: 3,
            hoverBorderWidth: 5,
            hoverBorderColor: '#ffffff'
        }]
    };
    
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
                labels: {
                    padding: 20,
                    usePointStyle: true,
                    font: {
                        size: 14,
                        weight: '500'
                    },
                    generateLabels: function(chart) {
                        const data = chart.data;
                        return data.labels.map((label, index) => ({
                            text: `${label} (${data.datasets[0].data[index].toFixed(1)}%)`,
                            fillStyle: data.datasets[0].backgroundColor[index],
                            strokeStyle: data.datasets[0].backgroundColor[index],
                            pointStyle: 'circle',
                            hidden: false,
                            index: index
                        }));
                    }
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const allocation = sortedAllocations[context.dataIndex];
                        return [
                            `${context.label}: ${context.parsed}%`,
                            `Market Value: ¥${formatNumber(allocation.market_value)}`,
                            `Target: ${allocation.target_pct.toFixed(1)}%`,
                            `Deviation: ${allocation.deviation_pct > 0 ? '+' : ''}${allocation.deviation_pct.toFixed(1)}%`
                        ];
                    }
                },
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#ffffff',
                bodyColor: '#ffffff',
                borderColor: '#ffffff',
                borderWidth: 1
            },
            datalabels: {
                color: '#ffffff',
                font: {
                    weight: 'bold',
                    size: 12
                },
                formatter: (value, ctx) => {
                    return value > 5 ? value.toFixed(1) + '%' : '';
                }
            }
        },
        elements: {
            arc: {
                borderRadius: 8
            }
        },
        animation: {
            animateScale: true,
            animateRotate: true,
            duration: 1000
        }
    };
    
    // Create the chart
    window.allocationChart = new Chart(ctx, {
        type: 'doughnut',
        data: chartData,
        options: chartOptions,
        plugins: [ChartDataLabels]
    });
}

/**
 * Get chart color for allocation category
 */
function getChartColor(index) {
    const colors = [
        '#FF6B6B', // Red - 房地产 (Real Estate)
        '#4ECDC4', // Teal - 股票 (Stocks)
        '#45B7D1', // Blue - 现金 (Cash)
        '#96CEB4', // Green - 商品 (Commodities)
        '#FFEAA7', // Yellow - 固定收益 (Fixed Income)
        '#DDA0DD'  // Purple - 保险 (Insurance)
    ];
    return colors[index % colors.length];
}

/**
 * Get deviation class for styling
 */
function getDeviationClass(deviation) {
    if (deviation > 5) return 'deviation-high-positive';
    if (deviation > 0) return 'deviation-positive';
    if (deviation < -5) return 'deviation-high-negative';
    if (deviation < 0) return 'deviation-negative';
    return 'deviation-neutral';
}

/**
 * Get status icon based on deviation
 */
function getStatusIcon(deviation) {
    if (deviation > 10) return '⚠️';
    if (deviation > 5) return '📈';
    if (deviation < -10) return '🔻';
    if (deviation < -5) return '📉';
    return '✅';
}

/**
 * Populate the rebalancing advice component
 */
function populateRebalancingAdvice() {
    const container = document.getElementById('rebalancing-advice');
    const advice = dashboardData.rebalancing_advice;
    
    if (!advice) {
        container.innerHTML = '<div class="error">Rebalancing advice data not available</div>';
        return;
    }
    
    let html = `
        <div class="data-item mb-2">
            <div class="label">Rebalancing Status</div>
            <div class="value">${advice.needs_rebalancing ? 'Required' : 'Not Needed'}</div>
        </div>
    `;
    
    if (advice.needs_rebalancing) {
        html += `
            <div class="mb-2">
                <h4>Trigger Reason:</h4>
                <p>${advice.trigger_reason}</p>
            </div>
        `;
        
        if (advice.categories_over_threshold && advice.categories_over_threshold.length > 0) {
            html += `
                <div class="mb-2">
                    <h4>Categories Requiring Attention:</h4>
                    <ul>
            `;
            
            advice.categories_over_threshold.forEach(category => {
                html += `<li>${category.category}: ${category.deviation_pct > 0 ? '+' : ''}${category.deviation_pct.toFixed(1)}% deviation</li>`;
            });
            
            html += '</ul></div>';
        }
        
        if (advice.operational_steps && advice.operational_steps.length > 0) {
            html += `
                <div>
                    <h4>Recommended Actions:</h4>
                    <ul>
            `;
            
            advice.operational_steps.forEach(step => {
                html += `<li>${step}</li>`;
            });
            
            html += '</ul></div>';
        }
    }
    
    container.innerHTML = html;
}

/**
 * Populate the single asset risk component
 */
function populateSingleAssetRisk() {
    const container = document.getElementById('single-asset-risk');
    const risk = dashboardData.portfolio_snapshot?.single_asset_risk;
    
    if (!risk) {
        container.innerHTML = '<div class="error">Risk analysis data not available</div>';
        return;
    }
    
    const riskClass = getRiskClass(risk.level);
    
    const html = `
        <div class="data-grid">
            <div class="data-item">
                <div class="label">Largest Holding</div>
                <div class="value">${risk.ticker}</div>
            </div>
            <div class="data-item">
                <div class="label">Concentration</div>
                <div class="value">${risk.percentage.toFixed(1)}%</div>
            </div>
            <div class="data-item">
                <div class="label">Risk Level</div>
                <div class="value">
                    <span class="risk-indicator ${riskClass}">${risk.level}</span>
                </div>
            </div>
        </div>
        
        <div class="mb-2">
            <h4>Risk Assessment:</h4>
            <p>${getRiskDescription(risk.level, risk.percentage)}</p>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Get CSS class for risk level
 */
function getRiskClass(riskLevel) {
    if (riskLevel.includes('低')) return 'risk-low';
    if (riskLevel.includes('高')) return 'risk-high';
    return 'risk-medium';
}

/**
 * Get risk description based on level and percentage
 */
function getRiskDescription(riskLevel, percentage) {
    if (percentage > 50) {
        return `Your portfolio has high concentration risk with ${percentage.toFixed(1)}% in a single asset. Consider diversification to reduce risk.`;
    } else if (percentage > 30) {
        return `Your portfolio has moderate concentration risk with ${percentage.toFixed(1)}% in a single asset. Monitor this allocation closely.`;
    } else {
        return `Your portfolio has acceptable concentration levels with ${percentage.toFixed(1)}% in the largest single asset.`;
    }
}

/**
 * Set up automatic refresh of dashboard data
 */
function setupAutoRefresh() {
    setInterval(async () => {
        try {
            console.log('Auto-refreshing dashboard data...');
            await fetchDashboardData();
            populateAllComponents();
        } catch (error) {
            console.error('Auto-refresh failed:', error);
        }
    }, CONFIG.REFRESH_INTERVAL);
}

/**
 * Format number with commas for thousands separator
 */
function formatNumber(num) {
    if (typeof num !== 'number') return 'N/A';
    return num.toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}

/**
 * Format date string for display
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    } catch {
        return 'N/A';
    }
}

/**
 * Format time string for display
 */
function formatTime(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        return date.toLocaleTimeString();
    } catch {
        return '';
    }
}

/**
 * Manual refresh function (can be called from UI)
 */
async function refreshDashboard() {
    console.log('Manual refresh triggered');
    showLoadingStates();
    try {
        await fetchDashboardData();
        populateAllComponents();
    } catch (error) {
        console.error('Manual refresh failed:', error);
        showErrorStates('Failed to refresh data');
    }
}
