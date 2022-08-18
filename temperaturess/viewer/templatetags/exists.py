from django import template
from django.db.models import Avg, Max
import numpy as np
from ..models import *
register = template.Library()


@register.filter
def exist_year(year: int):
    # yearをもつDayDataが存在するか
    return DayData.objects.filter(day__year=year).exists()


@register.filter
def exist_month(year: int, month: int):
    # year,monthをもつDayDataが存在するか
    return DayData.objects.filter(day__year=year, day__month=month).exists()


@register.simple_tag
def exist_day(year: int, month: int, day: int):
    # year,month,dayをもつTimeDataが存在するか
    return TimeData.objects.filter(tm__year=year, tm__month=month, tm__day=day).exists()
