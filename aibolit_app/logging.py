import logging
import re

import structlog

from aibolit_app.settings import AppEnvironments

USER_ID_PATTERN = re.compile(r'user_id=(\d+)')


def filter_user_id_from_query_parameter(logger, method_name: str, event_dict: dict):
    if query := event_dict.get('query'):
        query: str
        event_dict['query'] = USER_ID_PATTERN.sub('user_id=*', query)

    return event_dict


def setup_logging(app_environment: AppEnvironments) -> None:
    shared_processors = [
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt=r'%Y-%m-%d %H:%M:%S', utc=True),
    ]
    if app_environment is AppEnvironments.PROD:
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        shared_processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(
        processors=[structlog.contextvars.merge_contextvars, filter_user_id_from_query_parameter, *shared_processors],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, *shared_processors],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
