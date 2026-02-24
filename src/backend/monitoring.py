"""
Monitoring and observability setup for the Observatorio API.
Integrates Sentry for error tracking and structured logging.
"""
import logging
import os
import sys


def setup_logging():
    """Configure structured logging for the application."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(handler)

    # Reduce noise from libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return logging.getLogger("observatorio")


def init_sentry():
    """
    Initialize Sentry error tracking if SENTRY_DSN is set.
    Safe to call even if sentry-sdk is not installed.
    """
    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn:
        logging.getLogger("observatorio").info("Sentry DSN not configured, skipping Sentry init")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_RATE", "0.1")),
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            send_default_pii=False,
        )
        logging.getLogger("observatorio").info("Sentry initialized successfully")
    except ImportError:
        logging.getLogger("observatorio").warning(
            "sentry-sdk not installed. Run: pip install sentry-sdk[fastapi]"
        )
    except Exception as e:
        logging.getLogger("observatorio").error("Failed to initialize Sentry: %s", e)
