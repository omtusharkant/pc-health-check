import os
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
from apscheduler.schedulers.background import BackgroundScheduler
import monitor
import alert
import config
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize the scheduler
scheduler = BackgroundScheduler()

# Initialize data storage for historical data (24 hours of data points)
HISTORY_POINTS = 1440  # 24 hours with 1-minute intervals
historical_data = {
    'cpu': [],
    'memory': [],
    'disk': [],
    'network': {'sent': [], 'received': []},
    'timestamps': []
}

# Initialize alert settings with defaults
alert_settings = config.get_default_alert_settings()

# Disk information cache
disk_info = []

# Cache/Temp files information
cache_info = {
    'total_size': 0,
    'file_count': 0,
    'paths': {}
}

# System logs cache
system_logs = []

# System uptime start
system_start_time = datetime.now()

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('dashboard.html')

@app.route('/settings')
def settings():
    """Render the settings page."""
    email_config = alert.get_email_config()
    discord_config = alert.get_discord_config()
    return render_template('settings.html', 
                          alert_settings=alert_settings,
                          email_config=email_config,
                          discord_config=discord_config)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update alert settings."""
    data = request.json
    global alert_settings
    
    try:
        # Update alert thresholds
        if 'cpu_threshold' in data:
            alert_settings['cpu_threshold'] = float(data['cpu_threshold'])
        if 'memory_threshold' in data:
            alert_settings['memory_threshold'] = float(data['memory_threshold'])
        if 'disk_threshold' in data:
            alert_settings['disk_threshold'] = float(data['disk_threshold'])
            
        # Update alert methods
        if 'alerts_enabled' in data:
            alert_settings['alerts_enabled'] = data['alerts_enabled']
        if 'email_alerts' in data:
            alert_settings['email_alerts'] = data['email_alerts']
        if 'discord_alerts' in data:
            alert_settings['discord_alerts'] = data['discord_alerts']
            
        # Update email configuration
        if 'email_config' in data:
            alert.save_email_config(data['email_config'])
            
        # Update Discord webhook
        if 'discord_webhook' in data:
            alert.save_discord_config({'webhook_url': data['discord_webhook']})
            
        # Save settings to file
        config.save_alert_settings(alert_settings)
        
        return jsonify({'status': 'success', 'message': 'Settings updated successfully'})
    except Exception as e:
        logger.exception("Error updating settings")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/test_alert', methods=['POST'])
def test_alert():
    """Test alert functionality."""
    data = request.json
    alert_type = data.get('type', 'email')
    
    try:
        if alert_type == 'email':
            email_config = alert.get_email_config()
            if not email_config.get('email_from') or not email_config.get('email_to'):
                return jsonify({'status': 'error', 'message': 'Email configuration incomplete'}), 400
                
            success = alert.send_email_alert(
                "Test Alert", 
                "This is a test alert from your PC Health Dashboard.",
                email_config
            )
            
        elif alert_type == 'discord':
            discord_config = alert.get_discord_config()
            if not discord_config.get('webhook_url'):
                return jsonify({'status': 'error', 'message': 'Discord webhook URL not configured'}), 400
                
            success = alert.send_discord_alert(
                "Test Alert", 
                "This is a test alert from your PC Health Dashboard.",
                discord_config
            )
            
        else:
            return jsonify({'status': 'error', 'message': 'Unknown alert type'}), 400
            
        if success:
            return jsonify({'status': 'success', 'message': f'{alert_type.capitalize()} test alert sent successfully'})
        else:
            return jsonify({'status': 'error', 'message': f'Failed to send {alert_type} test alert'}), 500
            
    except Exception as e:
        logger.exception(f"Error sending test {alert_type} alert")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/clean_cache', methods=['POST'])
def clean_cache():
    """Clean cache and temporary files."""
    data = request.json
    paths = data.get('paths', None)  # If None, clean all cache paths
    
    try:
        # Update cache info before cleaning
        global cache_info
        cache_info = monitor.get_cache_info()
        
        # Get total size before cleaning for reporting
        total_size_before = cache_info['total_size']
        file_count_before = cache_info['file_count']
        
        # Clean the cache
        result = monitor.clean_cache_files(paths)
        
        # Update cache info after cleaning
        cache_info = monitor.get_cache_info()
        
        # Calculate space freed
        space_freed = total_size_before - cache_info['total_size']
        files_removed = file_count_before - cache_info['file_count']
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully cleaned {files_removed} files and freed {space_freed / (1024 * 1024):.2f} MB of space',
            'details': result,
            'space_freed': space_freed,
            'files_removed': files_removed
        })
        
    except Exception as e:
        logger.exception("Error cleaning cache files")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def update_system_metrics():
    """
    Collect system metrics and emit them via SocketIO.
    Also stores historical data and checks for alerts.
    """
    try:
        # Get current metrics
        cpu_percent = monitor.get_cpu_usage()
        memory_info = monitor.get_memory_usage()
        disk_usage = monitor.get_disk_usage()
        network_info = monitor.get_network_info()
        current_logs = monitor.get_system_logs(10)  # Get latest 10 logs
        
        # Update disk information (less frequently)
        global disk_info
        if not disk_info or len(historical_data.get('timestamps', [])) % 10 == 0:  # Every 10 minutes
            disk_info = monitor.get_disk_info()
        
        # Get cache information (less frequently to avoid excessive file system scans)
        global cache_info
        if not cache_info or len(historical_data.get('timestamps', [])) % 20 == 0:  # Every 10 minutes
            cache_info = monitor.get_cache_info()
        
        # Update system logs
        global system_logs
        # Completely refresh logs every time to ensure platform compatibility
        system_logs = current_logs + system_logs
        
        # Keep only the last 100 logs
        system_logs = system_logs[-100:]
        
        # Calculate uptime
        global system_start_time
        uptime_seconds = (datetime.now() - system_start_time).total_seconds()
        uptime = {
            'days': int(uptime_seconds // (24 * 3600)),
            'hours': int((uptime_seconds % (24 * 3600)) // 3600),
            'minutes': int((uptime_seconds % 3600) // 60),
            'seconds': int(uptime_seconds % 60)
        }
        
        # Update historical data
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Make sure all the lists exist
        if 'cpu' not in historical_data:
            historical_data['cpu'] = []
        if 'memory' not in historical_data:
            historical_data['memory'] = []
        if 'disk' not in historical_data:
            historical_data['disk'] = []
        if 'network' not in historical_data:
            historical_data['network'] = {'sent': [], 'received': []}
        if 'timestamps' not in historical_data:
            historical_data['timestamps'] = []
            
        # Add new data points
        historical_data['cpu'].append(cpu_percent)
        historical_data['memory'].append(memory_info['percent'])
        historical_data['disk'].append(disk_usage['percent'])
        historical_data['network']['sent'].append(network_info['bytes_sent'] / 1024)  # KB
        historical_data['network']['received'].append(network_info['bytes_recv'] / 1024)  # KB
        historical_data['timestamps'].append(timestamp)
        
        # Limit historical data to last 24 hours (1440 minutes)
        if len(historical_data['timestamps']) > HISTORY_POINTS:
            historical_data['cpu'] = historical_data['cpu'][-HISTORY_POINTS:]
            historical_data['memory'] = historical_data['memory'][-HISTORY_POINTS:]
            historical_data['disk'] = historical_data['disk'][-HISTORY_POINTS:]
            historical_data['network']['sent'] = historical_data['network']['sent'][-HISTORY_POINTS:]
            historical_data['network']['received'] = historical_data['network']['received'][-HISTORY_POINTS:]
            historical_data['timestamps'] = historical_data['timestamps'][-HISTORY_POINTS:]
        
        # Get top processes by resource usage
        processes = monitor.get_processes(15)  # Get top 15 processes

        # Prepare data to emit
        data = {
            'cpu': {
                'percent': cpu_percent,
                'cores': monitor.get_cpu_info()
            },
            'memory': memory_info,
            'disk': disk_usage,
            'disk_info': disk_info,
            'network': network_info,
            'logs': system_logs[-10:],  # Send only last 10 logs
            'processes': processes,  # Add processes information
            'cache_info': cache_info,  # Add cache information
            'uptime': uptime,
            'historical': {
                'cpu': historical_data['cpu'][-60:],  # Last 60 minutes for charts
                'memory': historical_data['memory'][-60:],
                'disk': historical_data['disk'][-60:],
                'network': {
                    'sent': historical_data['network']['sent'][-60:],
                    'received': historical_data['network']['received'][-60:]
                },
                'timestamps': historical_data['timestamps'][-60:]
            }
        }
        
        # Emit data via SocketIO
        socketio.emit('system_metrics', data)
        
        # Check for alerts
        if alert_settings['alerts_enabled']:
            # CPU alert
            if cpu_percent > alert_settings['cpu_threshold']:
                alert_message = f"CPU usage is high: {cpu_percent}% (threshold: {alert_settings['cpu_threshold']}%)"
                send_alerts("High CPU Usage", alert_message)
                
            # Memory alert
            if memory_info['percent'] > alert_settings['memory_threshold']:
                alert_message = f"Memory usage is high: {memory_info['percent']}% (threshold: {alert_settings['memory_threshold']}%)"
                send_alerts("High Memory Usage", alert_message)
                
            # Disk alert
            if disk_usage['percent'] > alert_settings['disk_threshold']:
                alert_message = f"Disk usage is high: {disk_usage['percent']}% (threshold: {alert_settings['disk_threshold']}%)"
                send_alerts("High Disk Usage", alert_message)
        
    except Exception as e:
        logger.exception("Error updating system metrics")

def send_alerts(title, message):
    """Send alerts via configured methods."""
    if alert_settings['email_alerts']:
        email_config = alert.get_email_config()
        if email_config.get('email_from') and email_config.get('email_to'):
            alert.send_email_alert(title, message, email_config)
    
    if alert_settings['discord_alerts']:
        discord_config = alert.get_discord_config()
        if discord_config.get('webhook_url'):
            alert.send_discord_alert(title, message, discord_config)

@socketio.on('connect')
def handle_connect(auth=None):
    """Handle client connection and send initial data."""
    logger.info("Client connected")
    # Force an immediate update
    update_system_metrics()

def start_scheduler():
    """Start the background scheduler for metric collection."""
    if not scheduler.running:
        scheduler.add_job(update_system_metrics, 'interval', seconds=30)
        scheduler.start()
        logger.info("Scheduler started")

# Start the scheduler when the application starts
start_scheduler()

# Define a function to stop the scheduler on application shutdown
def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown")

# Register the shutdown function
import atexit
atexit.register(shutdown_scheduler)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
