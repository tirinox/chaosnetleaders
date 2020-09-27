import asyncio


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
        await func(*args)
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
