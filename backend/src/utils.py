import asyncio
import logging
import time
from functools import wraps

from aiohttp import web


async def run_periodically(wait_time, func, _delay=0, *args):
    """
    Helper for schedule_task_periodically.
    Wraps a function in a coroutine that will run the
    given function indefinitely
    :param _delay: star delay in seconds
    :param wait_time: seconds to wait between iterations of func
    :param func: the function that will be run
    :param args: any args that need to be provided to func
    """
    if _delay > 0:
        await asyncio.sleep(_delay)
    while True:
        try:
            await func(*args)
        except:
            logging.exception(f"ERROR in run_periodically with {func}:")
        await asyncio.sleep(wait_time)


def schedule_task_periodically(wait_time, func, _delay=0, *args):
    """
    Schedule a function to run periodically as an asyncio.Task
    :param wait_time: interval (in seconds)
    :param func: the function that will be run
    :param _delay: star delay in seconds
    :param args: any args needed to be provided to func
    :return: an asyncio Task that has been scheduled to run
    """
    return asyncio.create_task(run_periodically(wait_time, func, _delay, *args))


async def cancel_scheduled_task(task):
    """
    Gracefully cancels a task
    :type task: asyncio.Task
    """
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def error_json(error):
    return web.json_response({
        'result': 'error',
        'error': error
    })


def error_guard(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            return error_json(str(e))

    return wrapped


def a_result_cached(ttl=60):
    def decorator(func):
        last_update_ts = -1.0
        last_result = None

        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_result, last_update_ts
            if last_update_ts < 0 or time.monotonic() - ttl > last_update_ts:
                last_result = await func(*args, **kwargs)
                last_update_ts = time.monotonic()
            return last_result

        return wrapper

    return decorator
