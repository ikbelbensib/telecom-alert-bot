"""
Unit tests for alerter.py module
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from src.alerter import (
    AlertSummary,
    send_slack_alert,
    dispatch_incidents,
    send_summary,
)
from src.parser import Incident, Priority


@pytest.fixture
def sample_incident_p1():
    """Create a sample P1 incident."""
    return Incident(
        timestamp="2024-04-01 08:11:03",
        priority=Priority.P1,
        component="CORE",
        message="SERVICE_DOWN – HLR node unreachable",
        raw_line="[2024-04-01 08:11:03] [CRITICAL] [CORE] SERVICE_DOWN"
    )


@pytest.fixture
def sample_incident_p2():
    """Create a sample P2 incident."""
    return Incident(
        timestamp="2024-04-01 08:09:55",
        priority=Priority.P2,
        component="BILLING",
        message="TIMEOUT on payment gateway",
        raw_line="[2024-04-01 08:09:55] [ERROR] [BILLING] TIMEOUT"
    )


@pytest.fixture
def webhook_url():
    """Sample Slack webhook URL."""
    return "https://hooks.slack.com/services/TEST/TEST/TEST"


class TestSendSlackAlert:
    """Test Slack alert sending."""

    @patch("src.alerter.urllib.request.urlopen")
    def test_send_slack_alert_success(self, mock_urlopen, sample_incident_p1, webhook_url):
        """Test successful Slack alert."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = send_slack_alert(sample_incident_p1, webhook_url)
        
        assert result is True
        mock_urlopen.assert_called_once()

    def test_send_slack_alert_no_webhook(self, sample_incident_p1):
        """Test alert with missing webhook URL."""
        with pytest.raises(ValueError, match="SLACK_WEBHOOK_URL"):
            send_slack_alert(sample_incident_p1, "")

    @patch("src.alerter.urllib.request.urlopen")
    def test_send_slack_alert_http_error(self, mock_urlopen, sample_incident_p1, webhook_url):
        """Test Slack alert with HTTP error."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            webhook_url, 403, "Forbidden", {}, None
        )
        
        result = send_slack_alert(sample_incident_p1, webhook_url)
        
        assert result is False

    @patch("src.alerter.urllib.request.urlopen")
    def test_send_slack_alert_url_error(self, mock_urlopen, sample_incident_p1, webhook_url):
        """Test Slack alert with connection error."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        
        result = send_slack_alert(sample_incident_p1, webhook_url)
        
        assert result is False


class TestAlertSummary:
    """Test AlertSummary dataclass."""

    def test_alert_summary_creation(self):
        """Test creating an AlertSummary."""
        summary = AlertSummary(
            total=5,
            p1_count=2,
            p2_count=3,
            sent=4,
            failed=1
        )
        
        assert summary.total == 5
        assert summary.p1_count == 2
        assert summary.p2_count == 3
        assert summary.sent == 4
        assert summary.failed == 1


class TestDispatchIncidents:
    """Test incident dispatching."""

    @patch("src.alerter.send_slack_alert")
    @patch("src.alerter.send_summary")
    def test_dispatch_all_incidents(self, mock_send_summary, mock_send_alert,
                                    sample_incident_p1, sample_incident_p2, webhook_url):
        """Test dispatching all incidents."""
        mock_send_alert.return_value = True
        incidents = [sample_incident_p1, sample_incident_p2]
        
        summary = dispatch_incidents(incidents, webhook_url)
        
        assert summary.total == 2
        assert summary.p1_count == 1
        assert summary.p2_count == 1
        assert summary.sent == 2
        assert summary.failed == 0
        assert mock_send_alert.call_count == 2
        mock_send_summary.assert_called_once()

    @patch("src.alerter.send_slack_alert")
    @patch("src.alerter.send_summary")
    def test_dispatch_p1_only(self, mock_send_summary, mock_send_alert,
                             sample_incident_p1, sample_incident_p2, webhook_url):
        """Test dispatching P1 only."""
        mock_send_alert.return_value = True
        incidents = [sample_incident_p1, sample_incident_p2]
        
        summary = dispatch_incidents(incidents, webhook_url, p1_only=True)
        
        assert summary.total == 2
        assert summary.p1_count == 1
        assert summary.p2_count == 1
        assert summary.sent == 1  # Only P1 sent
        assert mock_send_alert.call_count == 1

    @patch("src.alerter.send_slack_alert")
    @patch("src.alerter.send_summary")
    def test_dispatch_with_failures(self, mock_send_summary, mock_send_alert,
                                   sample_incident_p1, sample_incident_p2, webhook_url):
        """Test dispatching with some failures."""
        mock_send_alert.side_effect = [True, False]  # First succeeds, second fails
        incidents = [sample_incident_p1, sample_incident_p2]
        
        summary = dispatch_incidents(incidents, webhook_url)
        
        assert summary.sent == 1
        assert summary.failed == 1


class TestSendSummary:
    """Test sending summary."""

    @patch("src.alerter.urllib.request.urlopen")
    def test_send_summary_success(self, mock_urlopen, sample_incident_p1, 
                                 sample_incident_p2, webhook_url):
        """Test successful summary sending."""
        mock_response = MagicMock()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        send_summary([sample_incident_p1, sample_incident_p2], webhook_url)
        
        mock_urlopen.assert_called_once()

    @patch("src.alerter.urllib.request.urlopen")
    def test_send_summary_no_incidents(self, mock_urlopen, webhook_url):
        """Test summary with no incidents."""
        send_summary([], webhook_url)
        
        # Should not call urlopen if no incidents
        mock_urlopen.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
