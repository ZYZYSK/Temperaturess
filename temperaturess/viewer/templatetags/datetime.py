from django import template
import datetime
from dateutil.relativedelta import relativedelta
register = template.Library()


@register.simple_tag
def previous_year(year, month=None, day=None):
    # calculate previous year / month / day & return the year
    # year
    if month is None and day is None:
        return year - 1
    # month
    elif day is None:
        dt = datetime.date(year, month, 1)
        return (dt - relativedelta(months=1)).year
    # day
    else:
        dt = datetime.date(year, month, day)
        return (dt - datetime.timedelta(days=1)).year


@register.simple_tag
def previous_month(year, month, day=None):
    # calculate previous month / day & return the month
    # month
    if day is None:
        dt = datetime.date(year, month, 1)
        return (dt - relativedelta(months=1)).month
    # day
    else:
        dt = datetime.date(year, month, day)
        return (dt - datetime.timedelta(days=1)).month


@register.simple_tag
def previous_day(year, month, day):
    # calculate previous day & return the day
    dt = datetime.date(year, month, day)
    return (dt - datetime.timedelta(days=1)).day


@register.simple_tag
def next_year(year, month=None, day=None):
    # calculate next year / month / day & return the year
    # year
    if month is None and day is None:
        return year + 1
    # month
    elif day is None:
        dt = datetime.date(year, month, 1)
        return (dt + relativedelta(months=1)).year
    # day
    else:
        dt = datetime.date(year, month, day)
        return (dt + datetime.timedelta(days=1)).year


@register.simple_tag
def next_month(year, month, day=None):
    # calculate next month / day & return the month
    # month
    if day is None:
        dt = datetime.date(year, month, 1)
        return (dt + relativedelta(months=1)).month
    # day
    else:
        dt = datetime.date(year, month, day)
        return (dt + datetime.timedelta(days=1)).month


@register.simple_tag
def next_day(year, month, day):
    # calculate next day & return the day
    dt = datetime.date(year, month, day)
    return (dt + datetime.timedelta(days=1)).day
