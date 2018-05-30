import logging
from functools import partial

from dotenv import find_dotenv, dotenv_values


def _logger():
    return logging.getLogger(__name__)

def populate_args_from_dotenv(func):
    logger = _logger()
    try:
        dotenv_path = find_dotenv(raise_error_if_not_found=True)
        logger.info('Found .evn, loading variables')
        env_dict = dotenv_values(dotenv_path=dotenv_path)
        return partial(func, **env_dict)
    except IOError:
        logger.info('Didn\'t find .env')
        return func