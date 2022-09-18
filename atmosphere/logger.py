import structlog


def get_logger():
    return structlog.get_logger()
