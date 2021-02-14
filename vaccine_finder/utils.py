import logging


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
