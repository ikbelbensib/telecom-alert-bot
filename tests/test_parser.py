"""
Unit tests for parser.py module
"""

import pytest
from datetime import datetime
from src.parser import (
    parse_log_line,
    detect_incident,
    parse_log_file,
    Incident,
    Priority,
    LOG_PATTERN,
)


class TestLogParsing:
    """Test log line parsing functionality."""

    def test_parse_valid_log_line(self):
        """Test parsing a valid log line."""
        line = "[2024-04-01 08:01:12] [INFO] [CRM] User session started"
        parsed = parse_log_line(line)
        
        assert parsed is not None
        assert parsed["timestamp"] == "2024-04-01 08:01:12"
        assert parsed["level"] == "INFO"
        assert parsed["component"] == "CRM"
        assert parsed["message"] == "User session started"

    def test_parse_log_line_with_special_chars(self):
        """Test parsing log with special characters."""
        line = "[2024-04-01 08:09:55] [ERROR] [BILLING] TIMEOUT on payment gateway – transaction TXN-44821"
        parsed = parse_log_line(line)
        
        assert parsed is not None
        assert parsed["level"] == "ERROR"
        assert "TXN-44821" in parsed["message"]

    def test_parse_invalid_log_line(self):
        """Test that invalid lines return None."""
        invalid_lines = [
            "This is not a valid log",
            "[2024-04-01] Missing brackets",
            "Random text without format",
            "",
        ]
        
        for line in invalid_lines:
            assert parse_log_line(line) is None

    def test_parse_log_line_with_extra_spaces(self):
        """Test parsing with various spacing."""
        line = "[2024-04-01 08:01:12]   [INFO]   [CRM]   User session started"
        parsed = parse_log_line(line)
        
        # Should still parse with multiple spaces
        assert parsed is not None


class TestIncidentDetection:
    """Test incident detection logic."""

    def test_detect_p1_incident_critical(self):
        """Test detection of CRITICAL P1 incident."""
        parsed = {
            "timestamp": "2024-04-01 08:11:03",
            "level": "CRITICAL",
            "component": "CORE",
            "message": "SERVICE_DOWN – HLR node unreachable"
        }
        raw_line = "[2024-04-01 08:11:03] [CRITICAL] [CORE] SERVICE_DOWN"
        
        incident = detect_incident(parsed, raw_line)
        
        assert incident is not None
        assert incident.priority == Priority.P1
        assert incident.component == "CORE"

    def test_detect_p1_incident_outage(self):
        """Test detection of OUTAGE P1 incident."""
        parsed = {
            "timestamp": "2024-04-01 08:11:04",
            "level": "CRITICAL",
            "component": "CORE",
            "message": "OUTAGE detected on MSC cluster"
        }
        raw_line = "[2024-04-01 08:11:04] [CRITICAL] [CORE] OUTAGE"
        
        incident = detect_incident(parsed, raw_line)
        
        assert incident is not None
        assert incident.priority == Priority.P1

    def test_detect_p1_incident_sla_breach(self):
        """Test detection of SLA_BREACH P1 incident."""
        parsed = {
            "timestamp": "2024-04-01 08:14:10",
            "level": "CRITICAL",
            "component": "BILLING",
            "message": "SLA_BREACH – billing reconciliation delayed"
        }
        raw_line = "[2024-04-01 08:14:10] [CRITICAL] [BILLING] SLA_BREACH"
        
        incident = detect_incident(parsed, raw_line)
        
        assert incident is not None
        assert incident.priority == Priority.P1

    def test_detect_p2_incident_error(self):
        """Test detection of ERROR P2 incident."""
        parsed = {
            "timestamp": "2024-04-01 08:09:55",
            "level": "ERROR",
            "component": "BILLING",
            "message": "TIMEOUT on payment gateway"
        }
        raw_line = "[2024-04-01 08:09:55] [ERROR] [BILLING] TIMEOUT"
        
        incident = detect_incident(parsed, raw_line)
        
        assert incident is not None
        assert incident.priority == Priority.P2

    def test_detect_p2_incident_degraded(self):
        """Test detection of DEGRADED P2 incident."""
        parsed = {
            "timestamp": "2024-04-01 08:17:00",
            "level": "ERROR",
            "component": "CORE",
            "message": "DEGRADED service on VoLTE gateway"
        }
        raw_line = "[2024-04-01 08:17:00] [ERROR] [CORE] DEGRADED"
        
        incident = detect_incident(parsed, raw_line)
        
        assert incident is not None
        assert incident.priority == Priority.P2

    def test_detect_p2_incident_high_latency(self):
        """Test detection of HIGH_LATENCY P2 incident."""
        parsed = {
            "timestamp": "2024-04-01 08:13:00",
            "level": "ERROR",
            "component": "CRM",
            "message": "HIGH_LATENCY on CRM API – avg response 4200ms"
        }
        raw_line = "[2024-04-01 08:13:00] [ERROR] [CRM] HIGH_LATENCY"
        
        incident = detect_incident(parsed, raw_line)
        
        assert incident is not None
        assert incident.priority == Priority.P2

    def test_no_incident_for_info_logs(self):
        """Test that INFO logs do not create incidents."""
        parsed = {
            "timestamp": "2024-04-01 08:01:12",
            "level": "INFO",
            "component": "CRM",
            "message": "User session started"
        }
        raw_line = "[2024-04-01 08:01:12] [INFO] [CRM] User session started"
        
        incident = detect_incident(parsed, raw_line)
        
        assert incident is None

    def test_no_incident_for_warn_logs(self):
        """Test that WARN logs without keywords do not create incidents."""
        parsed = {
            "timestamp": "2024-04-01 08:03:10",
            "level": "WARN",
            "component": "PROVISIONING",
            "message": "Slow response from eSIM activation API"
        }
        raw_line = "[2024-04-01 08:03:10] [WARN] [PROVISIONING] Slow response"
        
        incident = detect_incident(parsed, raw_line)
        
        assert incident is None

    def test_incident_data_structure(self):
        """Test that Incident object has correct data."""
        parsed = {
            "timestamp": "2024-04-01 08:11:03",
            "level": "CRITICAL",
            "component": "CORE",
            "message": "SERVICE_DOWN – HLR node unreachable"
        }
        raw_line = "[2024-04-01 08:11:03] [CRITICAL] [CORE] SERVICE_DOWN"
        
        incident = detect_incident(parsed, raw_line)
        
        assert incident.timestamp == "2024-04-01 08:11:03"
        assert incident.component == "CORE"
        assert incident.priority == Priority.P1
        assert incident.raw_line == raw_line
        assert hasattr(incident, "detected_at")


class TestIncidentToSlackBlock:
    """Test Slack block formatting."""

    def test_slack_block_format_p1(self):
        """Test Slack block for P1 incident."""
        incident = Incident(
            timestamp="2024-04-01 08:11:03",
            priority=Priority.P1,
            component="CORE",
            message="SERVICE_DOWN – HLR node unreachable",
            raw_line="[2024-04-01 08:11:03] [CRITICAL] [CORE] SERVICE_DOWN"
        )
        
        block = incident.to_slack_block()
        
        assert block["type"] == "section"
        assert "P1" in block["text"]["text"]
        assert "CORE" in block["text"]["text"]
        assert "SERVICE_DOWN" in block["text"]["text"]

    def test_slack_block_format_p2(self):
        """Test Slack block for P2 incident."""
        incident = Incident(
            timestamp="2024-04-01 08:09:55",
            priority=Priority.P2,
            component="BILLING",
            message="TIMEOUT on payment gateway",
            raw_line="[2024-04-01 08:09:55] [ERROR] [BILLING] TIMEOUT"
        )
        
        block = incident.to_slack_block()
        
        assert block["type"] == "section"
        assert "P2" in block["text"]["text"]
        assert "BILLING" in block["text"]["text"]


class TestParseLogFile:
    """Test log file parsing."""

    def test_parse_log_file_basic(self, tmp_path):
        """Test parsing a complete log file."""
        # Create a temporary log file
        log_file = tmp_path / "test.log"
        log_file.write_text(
            "[2024-04-01 08:11:03] [CRITICAL] [CORE] SERVICE_DOWN - HLR node unreachable\n"
    "[2024-04-01 08:09:55] [ERROR] [BILLING] TIMEOUT on payment gateway\n"
    "[2024-04-01 08:01:12] [INFO] [CRM] User session started\n"
        )
        
        incidents = parse_log_file(str(log_file))
        
        assert len(incidents) == 2  # Only 2 incidents (P1 and P2), no INFO
        assert incidents[0].priority == Priority.P1
        assert incidents[1].priority == Priority.P2

    def test_parse_log_file_empty(self, tmp_path):
        """Test parsing an empty log file."""
        log_file = tmp_path / "empty.log"
        log_file.write_text("")
        
        incidents = parse_log_file(str(log_file))
        
        assert len(incidents) == 0

    def test_parse_log_file_with_comments(self, tmp_path):
        """Test parsing log file with comments."""
        log_file = tmp_path / "with_comments.log"
        log_file.write_text(
              "# This is a comment\n"
    "[2024-04-01 08:11:03] [CRITICAL] [CORE] SERVICE_DOWN\n"
    "# Another comment\n"
    "[2024-04-01 08:09:55] [ERROR] [BILLING] TIMEOUT\n"
        )
        
        incidents = parse_log_file(str(log_file))
        
        assert len(incidents) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
