import os
import json
import logging
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SlackNotifier:
    """Send notifications to Slack via webhook."""
    
    def __init__(self, webhook_url: str = None):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL. If not provided, reads from SLACK_WEBHOOK_URL env var.
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not configured")
    
    def send_message(self, text: str, blocks: list = None) -> bool:
        """
        Send a message to Slack.
        
        Args:
            text: Plain text message (fallback for notifications)
            blocks: Optional list of Slack block kit elements for rich formatting
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.error("Cannot send message: SLACK_WEBHOOK_URL not configured")
            return False
        
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Slack message sent successfully: {text[:50]}...")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False
    
    def send_alert(self, title: str, message: str, level: str = "info") -> bool:
        """
        Send a formatted alert to Slack.
        
        Args:
            title: Alert title
            message: Alert message
            level: Alert level (info, warning, error)
            
        Returns:
            bool: True if alert sent successfully
        """
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🚨",
            "success": "✅"
        }
        
        emoji = emoji_map.get(level, "📢")
        text = f"{emoji} {title}: {message}"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
        
        return self.send_message(text, blocks)


if __name__ == "__main__":
    # Simple test - send one message
    notifier = SlackNotifier()
    success = notifier.send_message("🚀 SentinelStream: Test message from crontab")
    exit(0 if success else 1)
