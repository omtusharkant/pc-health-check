import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Configuration file paths
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
EMAIL_CONFIG_FILE = os.path.join(CONFIG_DIR, 'email_config.json')
DISCORD_CONFIG_FILE = os.path.join(CONFIG_DIR, 'discord_config.json')

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

def get_email_config():
    """Get email configuration from file."""
    try:
        if os.path.exists(EMAIL_CONFIG_FILE):
            with open(EMAIL_CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # Return default empty config
            return {
                'email_from': '',
                'email_to': '',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_username': '',
                'smtp_password': ''
            }
    except Exception as e:
        logger.exception("Error loading email configuration")
        return {
            'email_from': '',
            'email_to': '',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_username': '',
            'smtp_password': ''
        }

def save_email_config(config):
    """Save email configuration to file."""
    try:
        with open(EMAIL_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.exception("Error saving email configuration")
        return False

def get_discord_config():
    """Get Discord webhook configuration from file."""
    try:
        if os.path.exists(DISCORD_CONFIG_FILE):
            with open(DISCORD_CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # Return default empty config
            return {'webhook_url': ''}
    except Exception as e:
        logger.exception("Error loading Discord configuration")
        return {'webhook_url': ''}

def save_discord_config(config):
    """Save Discord webhook configuration to file."""
    try:
        with open(DISCORD_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.exception("Error saving Discord configuration")
        return False

def send_email_alert(subject, message, config=None):
    """Send an email alert."""
    if config is None:
        config = get_email_config()
        
    email_from = config.get('email_from')
    email_to = config.get('email_to')
    smtp_server = config.get('smtp_server')
    smtp_port = config.get('smtp_port')
    smtp_username = config.get('smtp_username')
    smtp_password = config.get('smtp_password')
    
    if not all([email_from, email_to, smtp_server, smtp_port, smtp_username, smtp_password]):
        logger.error("Incomplete email configuration")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = subject
        
        # Add timestamp to message
        full_message = f"{message}\n\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        msg.attach(MIMEText(full_message, 'plain'))
        
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email alert sent: {subject}")
        return True
    except Exception as e:
        logger.exception(f"Error sending email alert: {str(e)}")
        return False

def send_discord_alert(title, message, config=None):
    """Send a Discord alert via webhook."""
    if config is None:
        config = get_discord_config()
        
    webhook_url = config.get('webhook_url')
    
    if not webhook_url:
        logger.error("Discord webhook URL not configured")
        return False
    
    try:
        # Create payload
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        payload = {
            "embeds": [{
                "title": title,
                "description": message,
                "color": 16711680,  # Red color for alerts
                "footer": {
                    "text": f"PC Health Dashboard • {timestamp}"
                }
            }]
        }
        
        # Send request to webhook
        response = requests.post(
            webhook_url, 
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 204:
            logger.info(f"Discord alert sent: {title}")
            return True
        else:
            logger.error(f"Failed to send Discord alert. Status code: {response.status_code}")
            return False
    except Exception as e:
        logger.exception(f"Error sending Discord alert: {str(e)}")
        return False
