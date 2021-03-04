import time as time_module
from datetime import datetime

MINUTE = 60
HOUR = 60 * 60
DAY = 24 * 60 * 60
MONTH = 30 * 24 * 60 * 60


def now_ts() -> float:
    return datetime.now().timestamp()  # don't use utcnow() since timestamp() does this conversion


def seconds_diff(t1: datetime, t2: datetime) -> float:
    return (t1 - t2).total_seconds()


def seconds_human(seconds, equal_str='same time') -> str:
    seconds = int(seconds)

    def append_if_not_zero(acc, val, time_type):
        return acc if val == 0 else "{} {} {}".format(acc, val, time_type)

    if seconds == 0:
        return equal_str
    else:
        minutes = seconds // 60
        hours = minutes // 60
        days = hours // 24

        s = ''
        s = append_if_not_zero(s, days, 'day' if days == 1 else 'days')
        if days <= 31:
            s = append_if_not_zero(s, hours % 24, 'hour' if hours == 1 else 'hours')
        if not days:
            s = append_if_not_zero(s, minutes % 60, 'min')
        if not hours:
            s = append_if_not_zero(s, seconds % 60, 'sec')
        return s.strip()


LONG_AGO = datetime(1980, 1, 1)


def parse_timespan_to_seconds(span: str):
    try:
        return int(span)
    except ValueError:
        result = 0
        str_for_number = ''
        for symbol in span:
            symbol = symbol.lower()
            if symbol in ['d', 'h', 'm', 's']:
                if str_for_number:
                    try:
                        number = int(str_for_number)
                    except ValueError:
                        return 'Error! Invalid number: {}'.format(str_for_number)
                    else:
                        multipliers = {
                            's': 1,
                            'm': 60,
                            'h': 3600,
                            'd': 3600 * 24
                        }
                        result += multipliers[symbol] * number
                    finally:
                        str_for_number = ''
                else:
                    return 'Error! Must be some digits before!'
            elif symbol in [chr(i + ord('0')) for i in range(10)]:
                str_for_number += symbol
            elif symbol in [' ', ',', ';', ':', '\t', '/', '.']:
                pass
            else:
                return 'Error! Unexpected symbol: {}'.format(symbol)

        if str_for_number:
            return 'Error! Unfinished component in the end: {}'.format(str_for_number)

        return result


def format_time_ago(d):
    if d is None or d == 0:
        return 'never'
    else:
        return f'{seconds_human(now_ts() - d)} ago'


def format_time_ago_short(d, now=None):
    now = now or now_ts()
    seconds = int(d - now)
    if seconds < 0:
        return "-" + format_time_ago_short(now, d)

    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    days = f'{days}d ' if days else ''
    minutes = minutes % 60
    hours = hours % 24
    return f'{days}{hours:02}:{minutes:02}'


def delay_to_next_hour_minute(hour, minute, second=0, now=None):
    now = now or datetime.now()
    that_time = datetime.now().replace(hour=hour, minute=minute, second=second, microsecond=0)
    return (now - that_time).seconds


def parse_time(time_str):
    r = time_module.strptime(time_str, "%H:%M")
    return r.tm_hour, r.tm_min


def is_time_to_do(h, m):
    due_dt = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
    now = datetime.now()
    sec_to_next_daily_event = (due_dt - now).total_seconds()
    return sec_to_next_daily_event < 0
