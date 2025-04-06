"""
Alert dispatcher for sending notifications.
"""

import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

from ..utils.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertDispatcher:
    """Alert dispatcher for sending notifications."""
    
    def __init__(self):
        """Initialize the alert dispatcher."""
        pass
    
    def send_email(self, 
                  recipient: str, 
                  subject: str, 
                  body: str,
                  html_body: Optional[str] = None) -> bool:
        """Send an email notification.
        
        Args:
            recipient: Email recipient
            subject: Email subject
            body: Plain text email body
            html_body: HTML email body (optional)
            
        Returns:
            bool: True if email was sent successfully
        """
        # This is a placeholder. In a real application, you would configure SMTP settings.
        try:
            # This part would be implemented with actual email sending logic
            logger.info(f"Sending email to {recipient}: {subject}")
            
            # Simulate email sending for now
            logger.info(f"Email body: {body[:100]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_slack(self, 
                  webhook_url: str, 
                  message: str,
                  blocks: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Send a Slack notification.
        
        Args:
            webhook_url: Slack webhook URL
            message: Message text
            blocks: Slack blocks for advanced formatting
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            payload = {
                "text": message
            }
            
            if blocks:
                payload["blocks"] = blocks
                
            response = requests.post(
                webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False
    
    def send_webhook(self, 
                    url: str, 
                    data: Dict[str, Any]) -> bool:
        """Send a webhook notification.
        
        Args:
            url: Webhook URL
            data: JSON data to send
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            response = requests.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {str(e)}")
            return False
    
    def format_threat_alert_email(self, 
                                 threat_data: Dict[str, Any]) -> Dict[str, str]:
        """Format a threat alert for email.
        
        Args:
            threat_data: Threat data to format
            
        Returns:
            Dict with subject and body for the email
        """
        severity = threat_data.get("severity", "UNKNOWN").upper()
        category = threat_data.get("category", "Unknown Threat")
        potential_targets = threat_data.get("potential_targets", [])
        
        subject = f"[{severity} ALERT] {category} Threat Detected"
        
        body = f"""
SEER - Cyber Threat Alert

Severity: {severity}
Category: {category}
Detected: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Description:
{threat_data.get('justification', 'No details available.')}

{f"Potential Targets: {', '.join(potential_targets)}" if potential_targets else ""}

This is an automated alert from the SEER Cyber Threat Prediction System.
"""
        
        html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
    <h1 style="color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px;">SEER - Cyber Threat Alert</h1>
    
    <div style="background-color: {'#ff5252' if severity == 'CRITICAL' else '#ff9100' if severity == 'HIGH' else '#ffb74d' if severity == 'MEDIUM' else '#8bc34a'}; color: white; padding: 10px; border-radius: 3px; margin: 10px 0;">
        <strong>Severity:</strong> {severity}
    </div>
    
    <div style="margin: 15px 0;">
        <p><strong>Category:</strong> {category}</p>
        <p><strong>Detected:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
    
    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 3px; margin: 15px 0;">
        <h3>Description:</h3>
        <p>{threat_data.get('justification', 'No details available.').replace('\n', '<br>')}</p>
    </div>
    
    {f"<div style='margin: 15px 0;'><strong>Potential Targets:</strong> {', '.join(potential_targets)}</div>" if potential_targets else ""}
    
    <div style="font-size: 12px; color: #777; margin-top: 20px; padding-top: 10px; border-top: 1px solid #ddd;">
        This is an automated alert from the SEER Cyber Threat Prediction System.
    </div>
</div>
"""
        
        return {
            "subject": subject,
            "body": body,
            "html_body": html_body
        }
    
    def format_threat_alert_slack(self, 
                                 threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format a threat alert for Slack.
        
        Args:
            threat_data: Threat data to format
            
        Returns:
            Dict with text and blocks for Slack message
        """
        severity = threat_data.get("severity", "UNKNOWN").upper()
        category = threat_data.get("category", "Unknown Threat")
        potential_targets = threat_data.get("potential_targets", [])
        
        color = "#ff0000" if severity == "CRITICAL" else "#ff9900" if severity == "HIGH" else "#ffcc00" if severity == "MEDIUM" else "#33cc33"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {severity} Alert: {category} Threat Detected"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{severity}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Category:*\n{category}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{threat_data.get('justification', 'No details available.')}"
                }
            }
        ]
        
        if potential_targets:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Potential Targets:*\n{', '.join(potential_targets)}"
                }
            })
            
        text = f"[{severity} ALERT] {category} Threat Detected"
        
        return {
            "text": text,
            "blocks": blocks
        }


# Create a default dispatcher instance
dispatcher = AlertDispatcher() 