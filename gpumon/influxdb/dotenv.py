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
        par_func = partial(func, **env_dict)
        par_func.__doc__ = func.__doc__
        return par_func
    except IOError:
        logger.info('Didn\'t find .env')
        return func