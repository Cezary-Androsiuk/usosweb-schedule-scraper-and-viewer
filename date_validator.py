from datetime import date, datetime, timedelta

def __todays_date() -> str:
    dzisiaj = date.today()
    return dzisiaj.strftime("%Y-%m-%d")

def __add_days(date_str: str, days: int) -> str:
    date = datetime.strptime(date_str, "%Y-%m-%d")
    if days == 0:
        return date_str
    elif days < 0:
        new_date = date - timedelta(days=days)
    elif days > 0:
        new_date = date + timedelta(days=days)
    
    return new_date.strftime('%Y-%m-%d')


# validate date
def to_week_date(date_str: str) -> str:
    date = datetime.strptime(date_str, "%Y-%m-%d")
    week_day = date.weekday()
    monday = date - timedelta(days=week_day)
    return monday.strftime("%Y-%m-%d")

def todays_week() -> str:
    return to_week_date(date_str=__todays_date())

def week_range(date_str: str) -> str:
    v_date = to_week_date(date_str=date_str)
    last_day_date = __add_days(date_str, 4)
    return f'{v_date} - {last_day_date}'

def week_forward(date_str: str) -> str:
    return __add_days(date_str=date_str, days=7)

def week_backwards(date_str: str) -> str:
    return __add_days(date_str=date_str, days=7)