// Function to create gauge chart
function createGauge(canvasId, label, thresholds) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    
    const ctx = canvas.getContext('2d');
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [0, 100],
                backgroundColor: [
                    getGaugeColor(0, thresholds),
                    'rgba(120, 120, 120, 0.2)'
                ],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                tooltip: {
                    enabled: false
                },
                legend: {
                    display: false
                }
            },
            animation: {
                duration: 500
            }
        }
    });
}

// Update gauge with new value
function updateGauge(gauge, value) {
    if (!gauge) return;
    
    // Determine color based on thresholds
    let thresholds = [75, 90]; // Default
    if (gauge.config.data.datasets[0].backgroundColor.length > 1) {
        gauge.config.data.datasets[0].backgroundColor[0] = getGaugeColor(value, thresholds);
    }
    
    // Update value
    gauge.config.data.datasets[0].data = [value, 100 - value];
    gauge.update();
}

// Get color for gauge based on value and thresholds
function getGaugeColor(value, thresholds) {
    if (value >= thresholds[1]) {
        return 'rgba(255, 99, 132, 0.8)'; // Red
    } else if (value >= thresholds[0]) {
        return 'rgba(255, 205, 86, 0.8)'; // Yellow
    } else {
        return 'rgba(75, 192, 192, 0.8)'; // Green
    }
}

// Initialize charts
function initializeCharts() {
    try {
        // CPU Usage Chart
        const cpuChartElement = document.getElementById('cpuChart');
        if (cpuChartElement) {
            const cpuChartCtx = cpuChartElement.getContext('2d');
            cpuChart = new Chart(cpuChartCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU Usage (%)',
                        data: [],
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderWidth: 2,
                        tension: 0.2,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 500 // Faster animations
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Percentage (%)'
                            }
                        },
                        x: {
                            ticks: {
                                maxTicksLimit: 10
                            }
                        }
                    }
                }
            });
        } else {
            console.warn('CPU chart element not found');
        }
        
        // Memory Usage Chart
        const memoryChartElement = document.getElementById('memoryChart');
        if (memoryChartElement) {
            const memoryChartCtx = memoryChartElement.getContext('2d');
            memoryChart = new Chart(memoryChartCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Memory Usage (%)',
                        data: [],
                        borderColor: 'rgba(153, 102, 255, 1)',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
                        borderWidth: 2,
                        tension: 0.2,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 500 // Faster animations
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Percentage (%)'
                            }
                        },
                        x: {
                            ticks: {
                                maxTicksLimit: 10
                            }
                        }
                    }
                }
            });
        } else {
            console.warn('Memory chart element not found');
        }
        
        // Network Chart
        const networkChartElement = document.getElementById('networkChart');
        if (networkChartElement) {
            const networkChartCtx = networkChartElement.getContext('2d');
            networkChart = new Chart(networkChartCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Upload (KB/s)',
                            data: [],
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'transparent',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: false
                        },
                        {
                            label: 'Download (KB/s)',
                            data: [],
                            borderColor: 'rgba(54, 162, 235, 1)',
                            backgroundColor: 'transparent',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 500 // Faster animations
                    },
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'KB/s'
                            }
                        },
                        x: {
                            ticks: {
                                maxTicksLimit: 8
                            }
                        }
                    }
                }
            });
        } else {
            console.warn('Network chart element not found');
        }
    } catch (error) {
        console.error('Error initializing charts:', error);
    }
}
