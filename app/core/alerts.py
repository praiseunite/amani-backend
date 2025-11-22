"""
Alert and notification integrations for monitoring.
"""

import logging
from typing import Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_slack_alert(
    message: str,
    severity: str = "warning",
    context: Optional[Dict] = None,
) -> bool:
    """
    Send an alert to Slack via webhook.
    
    Args:
        message: Alert message
        severity: Alert severity (info, warning, error, critical)
        context: Additional context dictionary
        
    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.SLACK_WEBHOOK_URL:
        logger.debug("Slack webhook URL not configured, skipping alert")
        return False

    # Map severity to Slack colors
    color_map = {
        "info": "#36a64f",  # Green
        "warning": "#ff9800",  # Orange
        "error": "#f44336",  # Red
        "critical": "#9c27b0",  # Purple
    }

    # Build Slack message payload
    payload = {
        "attachments": [
            {
                "color": color_map.get(severity, "#808080"),
                "title": f"[{severity.upper()}] Amani Backend Alert",
                "text": message,
                "fields": [
                    {
                        "title": "Environment",
                        "value": settings.ENVIRONMENT,
                        "short": True,
                    },
                    {
                        "title": "Version",
                        "value": settings.APP_VERSION,
                        "short": True,
                    },
                ],
                "footer": settings.APP_NAME,
                "ts": None,  # Slack will use current timestamp
            }
        ]
    }

    # Add context fields if provided
    if context:
        for key, value in context.items():
            payload["attachments"][0]["fields"].append(
                {"title": key, "value": str(value), "short": True}
            )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.SLACK_WEBHOOK_URL,
                json=payload,
            )
            response.raise_for_status()
            logger.info(f"Slack alert sent: {message[:100]}")
            return True
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")
        return False


async def send_pagerduty_alert(
    summary: str,
    severity: str = "warning",
    source: str = "amani-backend",
    context: Optional[Dict] = None,
) -> bool:
    """
    Create a PagerDuty incident via Events API v2.
    
    Args:
        summary: Brief description of the issue
        severity: Alert severity (info, warning, error, critical)
        source: Source of the alert
        context: Additional context dictionary
        
    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.PAGERDUTY_API_KEY or not settings.PAGERDUTY_SERVICE_ID:
        logger.debug("PagerDuty not configured, skipping alert")
        return False

    # Map severity to PagerDuty severity
    severity_map = {
        "info": "info",
        "warning": "warning",
        "error": "error",
        "critical": "critical",
    }

    # Build PagerDuty payload
    payload = {
        "routing_key": settings.PAGERDUTY_API_KEY,
        "event_action": "trigger",
        "payload": {
            "summary": summary,
            "severity": severity_map.get(severity, "warning"),
            "source": source,
            "custom_details": {
                "environment": settings.ENVIRONMENT,
                "version": settings.APP_VERSION,
                **(context or {}),
            },
        },
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.info(f"PagerDuty alert sent: {summary[:100]}")
            return True
    except Exception as e:
        logger.error(f"Failed to send PagerDuty alert: {e}")
        return False


async def send_alert(
    message: str,
    severity: str = "warning",
    context: Optional[Dict] = None,
    channels: Optional[list] = None,
) -> Dict[str, bool]:
    """
    Send alert to multiple notification channels.
    
    Args:
        message: Alert message
        severity: Alert severity (info, warning, error, critical)
        context: Additional context dictionary
        channels: List of channels to send to. If None, sends to all configured.
                  Options: ['slack', 'pagerduty']
        
    Returns:
        Dictionary mapping channel names to success status
    """
    if channels is None:
        channels = []
        if settings.SLACK_WEBHOOK_URL:
            channels.append("slack")
        if settings.PAGERDUTY_API_KEY:
            channels.append("pagerduty")

    results = {}

    if "slack" in channels:
        results["slack"] = await send_slack_alert(message, severity, context)

    if "pagerduty" in channels:
        results["pagerduty"] = await send_pagerduty_alert(message, severity, context=context)

    return results
