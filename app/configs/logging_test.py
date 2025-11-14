import json
import logging

from app.configs import logging as logging_module


def test_configure_logging(capfd):
    # Configure logging at INFO level
    logging_module.configure_logging(level=logging.INFO)

    # Use the root logger (so it uses your configured JSON StreamHandler)
    logger = logging.getLogger()

    # Log a test message
    logger.info("Test message")

    # Capture stdout
    out, _ = capfd.readouterr()
    log_line = out.strip()

    # Make sure something was captured
    assert log_line, "No log output captured"

    # Parse JSON
    log_data = json.loads(log_line)

    # Check fields
    assert log_data["level"] == "INFO"
    assert log_data["message"] == "Test message"
    assert "trace_id" in log_data
    assert "timestamp" in log_data
    assert "source" in log_data
