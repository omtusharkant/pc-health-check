import psutil
import platform
import datetime
import logging
import os
import re
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Constants
BYTES_TO_GB = 1024 * 1024 * 1024
BYTES_TO_MB = 1024 * 1024

def get_cpu_usage():
    """Get current CPU usage percentage."""
    return psutil.cpu_percent(interval=1)

def get_cpu_info():
    """Get detailed CPU information."""
    try:
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            current_freq = cpu_freq.current
        else:
            current_freq = 0
            
        # Get per-core usage
        per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        
        return {
            'count': cpu_count,
            'frequency': round(current_freq, 2),
            'per_core': per_core
        }
    except Exception as e:
        logger.exception("Error getting CPU info")
        return {'count': 0, 'frequency': 0, 'per_core': []}

def get_memory_usage():
    """Get current memory usage information."""
    try:
        memory = psutil.virtual_memory()
        return {
            'total': round(memory.total / BYTES_TO_GB, 2),  # GB
            'used': round(memory.used / BYTES_TO_GB, 2),    # GB
            'free': round(memory.available / BYTES_TO_GB, 2),  # GB
            'percent': memory.percent
        }
    except Exception as e:
        logger.exception("Error getting memory usage")
        return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}

def get_disk_usage(path="/"):
    """Get disk usage for the main drive."""
    try:
        # Get root path for current OS
        if platform.system() == 'Windows':
            path = "C:\\"
        
        disk = psutil.disk_usage(path)
        return {
            'total': round(disk.total / BYTES_TO_GB, 2),  # GB
            'used': round(disk.used / BYTES_TO_GB, 2),    # GB
            'free': round(disk.free / BYTES_TO_GB, 2),    # GB
            'percent': disk.percent
        }
    except Exception as e:
        logger.exception(f"Error getting disk usage for {path}")
        return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}

def get_disk_info():
    """Get information about all disk partitions."""
    try:
        partitions = psutil.disk_partitions(all=False)
        disk_info = []
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': round(usage.total / BYTES_TO_GB, 2),
                    'used': round(usage.used / BYTES_TO_GB, 2),
                    'free': round(usage.free / BYTES_TO_GB, 2),
                    'percent': usage.percent
                })
            except Exception:
                # Some partitions might not be accessible
                pass
                
        return disk_info
    except Exception as e:
        logger.exception("Error getting disk information")
        return []

def get_network_info():
    """Get network usage information."""
    try:
        net_counters = psutil.net_io_counters()
        return {
            'bytes_sent': net_counters.bytes_sent,
            'bytes_recv': net_counters.bytes_recv,
            'packets_sent': net_counters.packets_sent,
            'packets_recv': net_counters.packets_recv,
            'errin': net_counters.errin,
            'errout': net_counters.errout,
            'dropin': net_counters.dropin,
            'dropout': net_counters.dropout
        }
    except Exception as e:
        logger.exception("Error getting network information")
        return {
            'bytes_sent': 0, 'bytes_recv': 0, 
            'packets_sent': 0, 'packets_recv': 0,
            'errin': 0, 'errout': 0, 'dropin': 0, 'dropout': 0
        }

def get_system_logs(count=10):
    """
    Get recent system logs.
    Creates system event logs based on system metrics since actual log access may be restricted.
    """
    logs = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Always generate useful system information logs regardless of platform
        # System info logs
        system_info = get_system_info()
        logs.append({
            'timestamp': current_time,
            'source': 'System',
            'level': 'Information',
            'message': f'OS: {system_info["system"]} {system_info["release"]}, Machine: {system_info["machine"]}'
        })
        
        # Boot time
        boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        logs.append({
            'timestamp': current_time,
            'source': 'Boot',
            'level': 'Information',
            'message': f'System boot time: {boot_time}'
        })
        
        # CPU information
        cpu_info = get_cpu_info()
        cpu_percent = get_cpu_usage()
        logs.append({
            'timestamp': current_time,
            'source': 'CPU',
            'level': 'Information' if cpu_percent < 80 else 'Warning',
            'message': f'CPU usage: {cpu_percent}%, Cores: {cpu_info["count"]}, Frequency: {cpu_info["frequency"]} MHz'
        })
        
        # Memory information
        memory_info = get_memory_usage()
        logs.append({
            'timestamp': current_time,
            'source': 'Memory',
            'level': 'Information' if memory_info['percent'] < 80 else 'Warning',
            'message': f'Memory: {memory_info["used"]} GB used out of {memory_info["total"]} GB ({memory_info["percent"]}%)'
        })
        
        # Disk information
        disk_usage = get_disk_usage()
        logs.append({
            'timestamp': current_time,
            'source': 'Disk',
            'level': 'Information' if disk_usage['percent'] < 80 else 'Warning',
            'message': f'Disk: {disk_usage["used"]} GB used out of {disk_usage["total"]} GB ({disk_usage["percent"]}%)'
        })
        
        # Network information
        network_info = get_network_info()
        logs.append({
            'timestamp': current_time,
            'source': 'Network',
            'level': 'Information',
            'message': f'Network: {network_info["bytes_sent"]/BYTES_TO_MB:.2f} MB sent, {network_info["bytes_recv"]/BYTES_TO_MB:.2f} MB received'
        })
        
        # Add top processes information
        processes = get_processes(1)  # Get top process
        if processes:
            top_process = processes[0]
            logs.append({
                'timestamp': current_time,
                'source': 'Process',
                'level': 'Information',
                'message': f'Top process: {top_process["name"]} (PID: {top_process["pid"]}) - CPU: {top_process["cpu_percent"]}%, Memory: {top_process["memory_percent"]}%'
            })
        
    except Exception as e:
        logger.exception("Error generating system logs")
        logs.append({
            'timestamp': current_time,
            'source': 'Error',
            'level': 'Error',
            'message': f'Failed to generate system logs: {str(e)}'
        })
    
    # Return at most 'count' logs, newest first
    return logs[-count:]

def get_processes(count=10):
    """Get top processes by memory usage."""
    try:
        processes = []
        for proc in sorted(psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']), 
                           key=lambda p: p.info['memory_percent'] or 0, 
                           reverse=True)[:count]:
            try:
                # Get process creation time
                create_time = datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S")
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info['username'],
                    'memory_percent': round(proc.info['memory_percent'], 2) if proc.info['memory_percent'] else 0,
                    'cpu_percent': round(proc.info['cpu_percent'], 2) if proc.info['cpu_percent'] else 0,
                    'create_time': create_time
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes
    except Exception as e:
        logger.exception("Error getting process information")
        return []

def get_cache_info():
    """
    Get information about cache, temp files, and other unwanted files.
    Returns the total size and file counts in various temp/cache locations.
    """
    cache_paths = []
    
    # Define OS-specific paths
    if platform.system() == 'Windows':
        cache_paths = [
            os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'AppData', 'Local', 'Temp'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
            os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'AppData', 'Local', 'Microsoft', 'Windows', 'Temporary Internet Files'),
            os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'AppData', 'Local', 'Microsoft', 'Windows', 'INetCache'),
            os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Cache'),
            os.path.join(os.environ.get('USERPROFILE', 'C:\\'), 'AppData', 'Local', 'Mozilla', 'Firefox', 'Profiles')
        ]
    else:  # Unix-like systems (Linux, macOS)
        home = os.path.expanduser('~')
        cache_paths = [
            '/tmp',
            '/var/tmp',
            os.path.join(home, '.cache'),
            os.path.join(home, '.thumbnails'),
            os.path.join(home, '.mozilla', 'firefox'),
            os.path.join(home, '.config', 'google-chrome', 'Default', 'Cache')
        ]
    
    result = {
        'total_size': 0,  # in bytes
        'file_count': 0,
        'paths': {}
    }
    
    for path in cache_paths:
        try:
            path_size = 0
            file_count = 0
            
            if os.path.exists(path):
                for root, dirs, files in os.walk(path, topdown=True, onerror=None, followlinks=False):
                    try:
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                file_size = os.path.getsize(file_path)
                                path_size += file_size
                                file_count += 1
                            except (OSError, PermissionError):
                                continue
                    except (OSError, PermissionError):
                        continue
                
                # Only add non-empty directories
                if path_size > 0:
                    result['paths'][path] = {
                        'size': path_size,
                        'file_count': file_count
                    }
                    result['total_size'] += path_size
                    result['file_count'] += file_count
        except Exception as e:
            logger.warning(f"Error scanning cache directory {path}: {str(e)}")
    
    return result

def clean_cache_files(paths=None):
    """
    Clean cache and temporary files from the system.
    If paths is None, it will clean all known cache locations.
    Otherwise, it will only clean the specified paths.
    Returns a dictionary with the results of the cleaning operation.
    """
    if paths is None:
        # Get all cache paths from get_cache_info
        cache_info = get_cache_info()
        paths = list(cache_info['paths'].keys())
    
    result = {
        'successful': [],
        'failed': [],
        'total_cleaned': 0,  # bytes
        'files_removed': 0
    }
    
    for path in paths:
        try:
            path_cleaned = 0
            files_removed = 0
            
            if os.path.exists(path):
                for root, dirs, files in os.walk(path, topdown=True, onerror=None, followlinks=False):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            path_cleaned += file_size
                            files_removed += 1
                        except (OSError, PermissionError):
                            continue
                
                # Try to remove empty directories
                for root, dirs, files in os.walk(path, topdown=False, onerror=None, followlinks=False):
                    for dir_name in dirs:
                        try:
                            dir_path = os.path.join(root, dir_name)
                            if not os.listdir(dir_path):  # if directory is empty
                                os.rmdir(dir_path)
                        except (OSError, PermissionError):
                            continue
                
                result['successful'].append({
                    'path': path,
                    'cleaned': path_cleaned,
                    'files_removed': files_removed
                })
                result['total_cleaned'] += path_cleaned
                result['files_removed'] += files_removed
            
        except Exception as e:
            result['failed'].append({
                'path': path,
                'error': str(e)
            })
    
    return result

def get_system_info():
    """Get general system information."""
    try:
        return {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.exception("Error getting system information")
        return {
            'system': 'Unknown',
            'node': 'Unknown',
            'release': 'Unknown',
            'version': 'Unknown',
            'machine': 'Unknown',
            'processor': 'Unknown',
            'boot_time': 'Unknown'
        }
