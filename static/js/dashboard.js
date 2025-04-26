// Initialize Socket.IO connection
const socket = io();

// Store previous network values to calculate rates
let prevNetworkData = {
    bytes_sent: 0,
    bytes_recv: 0,
    timestamp: Date.now()
};

// Initialize charts and gauge objects
let cpuChart, memoryChart, networkChart;
let cpuGauge, memoryGauge, diskGauge;

// Initialize gauges on document load
document.addEventListener('DOMContentLoaded', function() {
    // Create gauges
    cpuGauge = createGauge('cpuGauge', 'CPU', [75, 90]);
    memoryGauge = createGauge('memoryGauge', 'Memory', [75, 90]);
    diskGauge = createGauge('diskGauge', 'Disk', [80, 95]);
    
    // Initialize charts
    initializeCharts();
    
    // Setup cache cleanup functionality
    setupCacheCleanup();
});

// Socket event handlers
socket.on('connect', function() {
    console.log('Connected to server');
});

socket.on('disconnect', function() {
    console.log('Disconnected from server');
});

socket.on('system_metrics', function(data) {
    updateDashboard(data);
});

// Function to update all dashboard elements with new data
function updateDashboard(data) {
    // Update CPU metrics
    updateCpuMetrics(data.cpu);
    
    // Update memory metrics
    updateMemoryMetrics(data.memory);
    
    // Update disk metrics
    updateDiskMetrics(data.disk);
    
    // Update disk info table
    updateDiskInfoTable(data.disk_info);
    
    // Update network metrics
    updateNetworkMetrics(data.network);
    
    // Update processes table
    updateProcesses(data.processes);
    
    // Update system logs
    updateSystemLogs(data.logs);
    
    // Update uptime
    updateUptime(data.uptime);
    
    // Update cache information
    if (data.cache_info) {
        updateCacheInfo(data.cache_info);
    }
    
    // Update historical charts
    updateCharts(data.historical);
}

// CPU metrics update
function updateCpuMetrics(cpu) {
    // Update gauge
    updateGauge(cpuGauge, cpu.percent);
    
    // Update text values
    document.getElementById('cpu-usage-value').textContent = `${cpu.percent.toFixed(1)}%`;
    document.getElementById('cpu-cores').textContent = cpu.cores.count;
    document.getElementById('cpu-freq').textContent = cpu.cores.frequency;
    
    // Update CPU cores display
    updateCpuCoresDisplay(cpu.cores.per_core);
}

// Update CPU cores display
function updateCpuCoresDisplay(coresData) {
    const container = document.getElementById('cpu-cores-container');
    container.innerHTML = '';
    
    coresData.forEach((usage, index) => {
        const coreDiv = document.createElement('div');
        coreDiv.className = 'col-md-3 col-sm-4 col-6';
        
        // Determine progress bar color based on usage
        let barClass = 'bg-success';
        if (usage > 90) {
            barClass = 'bg-danger';
        } else if (usage > 75) {
            barClass = 'bg-warning';
        }
        
        coreDiv.innerHTML = `
            <div class="cpu-core-item">
                <div class="d-flex justify-content-between">
                    <small>Core ${index}</small>
                    <small>${usage.toFixed(1)}%</small>
                </div>
                <div class="progress" style="height: 6px;">
                    <div class="progress-bar ${barClass}" role="progressbar" 
                         style="width: ${usage}%;" aria-valuenow="${usage}" 
                         aria-valuemin="0" aria-valuemax="100"></div>
                </div>
            </div>
        `;
        
        container.appendChild(coreDiv);
    });
}

// Memory metrics update
function updateMemoryMetrics(memory) {
    // Update gauge
    updateGauge(memoryGauge, memory.percent);
    
    // Update text values
    document.getElementById('memory-usage-value').textContent = `${memory.percent.toFixed(1)}%`;
    document.getElementById('memory-used').textContent = `Used: ${memory.used.toFixed(2)} GB`;
    document.getElementById('memory-free').textContent = `Free: ${memory.free.toFixed(2)} GB`;
    document.getElementById('memory-total').textContent = `Total: ${memory.total.toFixed(2)} GB`;
}

// Disk metrics update
function updateDiskMetrics(disk) {
    // Update gauge
    updateGauge(diskGauge, disk.percent);
    
    // Update text values
    document.getElementById('disk-usage-value').textContent = `${disk.percent.toFixed(1)}%`;
    document.getElementById('disk-used').textContent = `Used: ${disk.used.toFixed(2)} GB`;
    document.getElementById('disk-free').textContent = `Free: ${disk.free.toFixed(2)} GB`;
    document.getElementById('disk-total').textContent = `Total: ${disk.total.toFixed(2)} GB`;
}

// Update disk info table
function updateDiskInfoTable(diskInfo) {
    const table = document.getElementById('disk-info-table');
    table.innerHTML = '';
    
    diskInfo.forEach(disk => {
        const row = document.createElement('tr');
        
        // Determine progress bar color based on usage
        let barClass = 'bg-success';
        if (disk.percent > 90) {
            barClass = 'bg-danger';
        } else if (disk.percent > 75) {
            barClass = 'bg-warning';
        }
        
        row.innerHTML = `
            <td>${disk.device}</td>
            <td>${disk.fstype}</td>
            <td>${disk.total.toFixed(2)} GB</td>
            <td>${disk.used.toFixed(2)} GB</td>
            <td>${disk.free.toFixed(2)} GB</td>
            <td>
                <div class="progress" style="height: 6px;">
                    <div class="progress-bar ${barClass}" role="progressbar" 
                         style="width: ${disk.percent}%;" aria-valuenow="${disk.percent}" 
                         aria-valuemin="0" aria-valuemax="100"></div>
                </div>
                <small>${disk.percent}%</small>
            </td>
        `;
        
        table.appendChild(row);
    });
}

// Network metrics update
function updateNetworkMetrics(network) {
    // Calculate rates
    const now = Date.now();
    const timeDiff = (now - prevNetworkData.timestamp) / 1000; // seconds
    
    let uploadRate = 0;
    let downloadRate = 0;
    
    if (prevNetworkData.bytes_sent > 0 && timeDiff > 0) {
        uploadRate = (network.bytes_sent - prevNetworkData.bytes_sent) / timeDiff / 1024; // KB/s
        downloadRate = (network.bytes_recv - prevNetworkData.bytes_recv) / timeDiff / 1024; // KB/s
    }
    
    // Update text values
    document.getElementById('network-upload').textContent = `${uploadRate.toFixed(2)} KB/s`;
    document.getElementById('network-download').textContent = `${downloadRate.toFixed(2)} KB/s`;
    
    // Update stored values for next calculation
    prevNetworkData = {
        bytes_sent: network.bytes_sent,
        bytes_recv: network.bytes_recv,
        timestamp: now
    };
    
    // Update network chart if available
    if (networkChart) {
        networkChart.data.datasets[0].data.push(uploadRate);
        networkChart.data.datasets[1].data.push(downloadRate);
        
        // Keep only last 30 data points
        if (networkChart.data.datasets[0].data.length > 30) {
            networkChart.data.datasets[0].data.shift();
            networkChart.data.datasets[1].data.shift();
            networkChart.data.labels.shift();
        }
        
        // Add new timestamp
        const time = new Date().toLocaleTimeString();
        networkChart.data.labels.push(time);
        
        networkChart.update();
    }
}

// Update system logs table
function updateSystemLogs(logs) {
    const table = document.getElementById('system-logs-table');
    table.innerHTML = '';
    
    // Reverse logs to show newest first
    logs.slice().reverse().forEach(log => {
        const row = document.createElement('tr');
        
        // Determine log level styling
        let levelClass = '';
        switch(log.level.toLowerCase()) {
            case 'error':
                levelClass = 'text-danger';
                break;
            case 'warning':
                levelClass = 'text-warning';
                break;
            case 'information':
                levelClass = 'text-info';
                break;
            default:
                levelClass = '';
        }
        
        row.innerHTML = `
            <td>${log.timestamp}</td>
            <td>${log.source}</td>
            <td class="${levelClass}">${log.level}</td>
            <td>${log.message}</td>
        `;
        
        table.appendChild(row);
    });
}

// Update uptime display
function updateUptime(uptime) {
    let uptimeText = '';
    
    if (uptime.days > 0) {
        uptimeText += `${uptime.days}d `;
    }
    
    uptimeText += `${String(uptime.hours).padStart(2, '0')}:${String(uptime.minutes).padStart(2, '0')}:${String(uptime.seconds).padStart(2, '0')}`;
    
    document.getElementById('uptime-value').textContent = uptimeText;
}

// Update process list table
function updateProcesses(processes) {
    const table = document.getElementById('processes-table');
    if (!table) return;  // Table might not exist yet
    
    table.innerHTML = '';
    
    processes.forEach(proc => {
        const row = document.createElement('tr');
        
        // Determine styling based on resource usage
        const cpuClass = proc.cpu_percent > 50 ? 'text-danger' : '';
        const memClass = proc.memory_percent > 50 ? 'text-danger' : '';
        
        row.innerHTML = `
            <td>${proc.pid}</td>
            <td>${proc.name}</td>
            <td>${proc.username}</td>
            <td class="${cpuClass}">${proc.cpu_percent}%</td>
            <td class="${memClass}">${proc.memory_percent}%</td>
            <td>${proc.create_time}</td>
        `;
        
        table.appendChild(row);
    });
}

// Update charts with historical data
function updateCharts(historicalData) {
    // Update CPU chart
    if (cpuChart && historicalData && historicalData.timestamps) {
        cpuChart.data.labels = historicalData.timestamps;
        cpuChart.data.datasets[0].data = historicalData.cpu;
        cpuChart.update();
    }
    
    // Update memory chart
    if (memoryChart && historicalData && historicalData.timestamps) {
        memoryChart.data.labels = historicalData.timestamps;
        memoryChart.data.datasets[0].data = historicalData.memory;
        memoryChart.update();
    }
}

// Update cache information
function updateCacheInfo(cacheInfo) {
    if (!cacheInfo) return;
    
    // Format total size
    const totalSizeBytes = cacheInfo.total_size;
    let sizeText = '0 B';
    
    if (totalSizeBytes > 0) {
        if (totalSizeBytes < 1024) {
            sizeText = `${totalSizeBytes} B`;
        } else if (totalSizeBytes < 1024 * 1024) {
            sizeText = `${(totalSizeBytes / 1024).toFixed(2)} KB`;
        } else if (totalSizeBytes < 1024 * 1024 * 1024) {
            sizeText = `${(totalSizeBytes / (1024 * 1024)).toFixed(2)} MB`;
        } else {
            sizeText = `${(totalSizeBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
        }
    }
    
    // Update display elements
    document.getElementById('cacheTotalSize').textContent = sizeText;
    document.getElementById('cacheFileCount').textContent = cacheInfo.file_count;
    document.getElementById('cacheLastScan').textContent = new Date().toLocaleTimeString();
    
    // Calculate % of disk used by cache (rough estimate, considering 1% of total disk)
    const diskProgress = Math.min(100, (totalSizeBytes / (1024 * 1024 * 1024 * 10)) * 100);
    
    const progressBar = document.getElementById('cacheProgressBar');
    progressBar.style.width = `${diskProgress}%`;
    progressBar.setAttribute('aria-valuenow', diskProgress);
    progressBar.textContent = `${diskProgress.toFixed(1)}%`;
    
    // Update progress bar color based on size
    if (diskProgress > 90) {
        progressBar.className = 'progress-bar bg-danger';
    } else if (diskProgress > 60) {
        progressBar.className = 'progress-bar bg-warning';
    } else {
        progressBar.className = 'progress-bar bg-success';
    }
    
    // Update cache locations
    updateCacheLocations(cacheInfo.paths);
}

// Update cache locations table
function updateCacheLocations(paths) {
    const locationsList = document.getElementById('cacheLocationsList');
    locationsList.innerHTML = '';
    
    if (!paths || Object.keys(paths).length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="3" class="text-center">No cache locations found</td>';
        locationsList.appendChild(row);
        return;
    }
    
    // Sort paths by size (largest first)
    const sortedPaths = Object.entries(paths)
        .sort((a, b) => b[1].size - a[1].size)
        .map(([path, info]) => ({ path, ...info }));
    
    sortedPaths.forEach(location => {
        const row = document.createElement('tr');
        
        // Format size
        let sizeText = '0 B';
        if (location.size < 1024) {
            sizeText = `${location.size} B`;
        } else if (location.size < 1024 * 1024) {
            sizeText = `${(location.size / 1024).toFixed(2)} KB`;
        } else if (location.size < 1024 * 1024 * 1024) {
            sizeText = `${(location.size / (1024 * 1024)).toFixed(2)} MB`;
        } else {
            sizeText = `${(location.size / (1024 * 1024 * 1024)).toFixed(2)} GB`;
        }
        
        row.innerHTML = `
            <td>${location.path}</td>
            <td>${location.file_count}</td>
            <td>${sizeText}</td>
        `;
        
        locationsList.appendChild(row);
    });
}

// Setup cache cleanup button and related functionality
function setupCacheCleanup() {
    const cleanCacheBtn = document.getElementById('cleanCacheBtn');
    const cacheInfoDiv = document.getElementById('cacheInfo');
    const cleaningProgressDiv = document.getElementById('cleaningProgress');
    const cleaningResultsDiv = document.getElementById('cleaningResults');
    const cleanupResultMessage = document.getElementById('cleanupResultMessage');
    const backToCacheInfoBtn = document.getElementById('backToCacheInfoBtn');
    const statusToast = document.getElementById('statusToast');
    const toastTitle = document.getElementById('toastTitle');
    const toastMessage = document.getElementById('toastMessage');
    
    // Initialize toast
    const toast = new bootstrap.Toast(statusToast);
    
    if (cleanCacheBtn) {
        cleanCacheBtn.addEventListener('click', function() {
            // Show cleaning in progress
            cacheInfoDiv.classList.add('d-none');
            cleaningProgressDiv.classList.remove('d-none');
            cleaningResultsDiv.classList.add('d-none');
            
            // Send cleanup request to server
            fetch('/api/clean_cache', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})  // No specific paths, clean all
            })
            .then(response => response.json())
            .then(data => {
                // Hide progress indicator
                cleaningProgressDiv.classList.add('d-none');
                
                if (data.status === 'success') {
                    // Show success message
                    cleanupResultMessage.textContent = data.message;
                    cleaningResultsDiv.classList.remove('d-none');
                    
                    // Update toast for success
                    toastTitle.textContent = 'Cleanup Complete';
                    toastMessage.textContent = data.message;
                    toast.show();
                } else {
                    // Show error message
                    cacheInfoDiv.classList.remove('d-none');
                    
                    // Show error toast
                    toastTitle.textContent = 'Cleanup Failed';
                    toastMessage.textContent = data.message || 'An error occurred during cleanup';
                    toast.show();
                }
            })
            .catch(error => {
                console.error('Error cleaning cache:', error);
                
                // Hide progress and show cache info again
                cleaningProgressDiv.classList.add('d-none');
                cacheInfoDiv.classList.remove('d-none');
                
                // Show error toast
                toastTitle.textContent = 'Cleanup Failed';
                toastMessage.textContent = 'Failed to connect to server';
                toast.show();
            });
        });
    }
    
    // Back button
    if (backToCacheInfoBtn) {
        backToCacheInfoBtn.addEventListener('click', function() {
            cleaningResultsDiv.classList.add('d-none');
            cacheInfoDiv.classList.remove('d-none');
        });
    }
}
