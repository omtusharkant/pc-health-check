import os
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Configuration file paths
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
ALERT_SETTINGS_FILE = os.path.join(CONFIG_DIR, 'alert_settings.json')

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

def get_default_alert_settings():
    """Get default alert settings."""
    return {
        'alerts_enabled': True,
        'cpu_threshold': 80.0,
        'memory_threshold': 80.0,
        'disk_threshold': 85.0,
        'email_alerts': False,
        'discord_alerts': False
    }

def load_alert_settings():
    """Load alert settings from file."""
    try:
        if os.path.exists(ALERT_SETTINGS_FILE):
            with open(ALERT_SETTINGS_FILE, 'r') as f:
                return json.load(f)
        else:
            # Return default settings
            default_settings = get_default_alert_settings()
            save_alert_settings(default_settings)
            return default_settings
    except Exception as e:
        logger.exception("Error loading alert settings")
        return get_default_alert_settings()

def save_alert_settings(settings):
    """Save alert settings to file."""
    try:
        with open(ALERT_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        logger.exception("Error saving alert settings")
        return False
