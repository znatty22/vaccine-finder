import json
import logging
import requests

logger = logging.getLogger(__name__)


def send_request(session, method_name, url, **kwargs):
    """
    Send HTTP request to url
    """
    # Send request
    http_method = getattr(session, method_name)
    response = http_method(url, **kwargs)
    response.raise_for_status()

    # Parse response
    try:
        content = response.json()
    except json.decoder.JSONDecodeError as e:
        logger.error(f"Got unexpected response:\n{response.text}")

    return content


def setup_logger(log_level=logging.INFO):
    """
    Setup logger
    """
    format_ = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    root = logging.getLogger()
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logging.Formatter(format_))
    root.setLevel(log_level)
    root.addHandler(consoleHandler)
    logger = logging.getLogger(__name__)
    return logger
