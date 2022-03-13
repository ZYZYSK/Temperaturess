from django import template
from django.db.models import Avg, Max, Min
from ..models import *
register = template.Library()


@register.filter
def average_temperature_avg(year: int, month: int = 0):
    # 平均気温の平均値
    if month == 0:
        objects = DayData.objects.filter(day__year=year).values('temperature_avg')
    else:
        objects = DayData.objects.filter(day__year=year, day__month=month).values('temperature_avg')
    if objects.count():
        return objects.aggregate(Avg('temperature_avg'))['temperature_avg__avg']
    else:
        return ''


@register.filter
def average_temperature_min(year: int, month: int = 0):
    # 最低気温の平均値
    if month == 0:
        objects = DayData.objects.filter(day__year=year).values('temperature_min__temperature')
    else:
        objects = DayData.objects.filter(day__year=year, day__month=month).values('temperature_min__temperature')
    if objects.count():
        return objects.aggregate(Avg('temperature_min__temperature'))['temperature_min__temperature__avg']
    else:
        return ''


@register.filter
def average_temperature_max(year: int, month: int = 0):
    # 最高気温の平均値
    if month == 0:
        objects = DayData.objects.filter(day__year=year).values('temperature_max__temperature')
    else:
        objects = DayData.objects.filter(day__year=year, day__month=month).values('temperature_max__temperature')
    if objects.count():
        return objects.aggregate(Avg('temperature_max__temperature'))['temperature_max__temperature__avg']
    else:
        return ''


@register.filter
def min_temperature_min(year: int, month: int = 0):
    # 最低気温の最低値
    if month == 0:
        objects = DayData.objects.filter(day__year=year).values('temperature_min__temperature')
    else:
        objects = DayData.objects.filter(day__year=year, day__month=month).values('temperature_min__temperature')
    if objects.count():
        return objects.aggregate(Min('temperature_min__temperature'))['temperature_min__temperature__min']
    else:
        return ''


@register.filter
def min_temperature_max(year: int, month: int = 0):
    # 最高気温の最低値
    if month == 0:
        objects = DayData.objects.filter(day__year=year).values('temperature_max__temperature')
    else:
        objects = DayData.objects.filter(day__year=year, day__month=month).values('temperature_max__temperature')
    if objects.count():
        return objects.aggregate(Min('temperature_max__temperature'))['temperature_max__temperature__min']
    else:
        return ''


@register.filter
def max_temperature_min(year: int, month: int = 0):
    # 最低気温の最高値
    if month == 0:
        objects = DayData.objects.filter(day__year=year).values('temperature_min__temperature')
    else:
        objects = DayData.objects.filter(day__year=year, day__month=month).values('temperature_min__temperature')
    if objects.count():
        return objects.aggregate(Max('temperature_min__temperature'))['temperature_min__temperature__max']
    else:
        return ''


@register.filter
def max_temperature_max(year: int, month: int = 0):
    # 最高気温の最高値
    if month == 0:
        objects = DayData.objects.filter(day__year=year).values('temperature_max__temperature')
    else:
        objects = DayData.objects.filter(day__year=year, day__month=month).values('temperature_max__temperature')
    if objects.count():
        return objects.aggregate(Max('temperature_max__temperature'))['temperature_max__temperature__max']
    else:
        return ''


@register.filter
def average_humidity_avg(year: int, month: int = 0):
    # 平均湿度の平均値
    if month == 0:
        objects = DayData.objects.filter(day__year=year).values('humidity_avg')
    else:
        objects = DayData.objects.filter(day__year=year, day__month=month).values('humidity_avg')
    if objects.count():
        return objects.aggregate(Avg('humidity_avg'))['humidity_avg__avg']
    else:
        return ''


@register.filter
def average_humidity_min(year: int, month: int = 0):
    # 最低湿度の最小値
    if month == 0:
        objects = DayData.objects.filter(day__year=year).values('humidity_min__humidity')
    else:
        objects = DayData.objects.filter(day__year=year, day__month=month).values('humidity_min')
    if objects.count():
        return objects.aggregate(Min('humidity_min__humidity'))['humidity_min__humidity__min']
    else:
        return ''


@register.filter
def average_humidity_max(year: int, month: int = 0):
    # 最高湿度の最大値
    if month == 0:
        objects = DayData.objects.filter(day__year=year).values('humidity_max__humidity')
    else:
        objects = DayData.objects.filter(day__year=year, day__month=month).values('humidity_max')
    if objects.count():
        return objects.aggregate(Max('humidity_max__humidity'))['humidity_max__humidity__max']
    else:
        return ''


@register.filter
def average_temperature_avg_normal(year: int, month: int = 0):
    # 平年平均気温の平均値
    if month == 0:
        objects = NormalData.objects.all().values('temperature_avg')
    else:
        objects = NormalData.objects.filter(day__month=month).values('temperature_avg')
    if objects.count():
        return objects.aggregate(Avg('temperature_avg'))['temperature_avg__avg']
    else:
        return ''


@register.filter
def average_temperature_min_normal(year: int, month: int = 0):
    # 平年最低気温の平均値
    if month == 0:
        objects = NormalData.objects.all().values('temperature_min')
    else:
        objects = NormalData.objects.filter(day__month=month).values('temperature_min')
    if objects.count():
        return objects.aggregate(Avg('temperature_min'))['temperature_min__avg']
    else:
        return ''


@register.filter
def average_temperature_max_normal(year: int, month: int = 0):
    # 平年最高気温の平均値
    if month == 0:
        objects = NormalData.objects.all().values('temperature_max')
    else:
        objects = NormalData.objects.filter(day__month=month).values('temperature_max')
    if objects.count():
        return objects.aggregate(Avg('temperature_max'))['temperature_max__avg']
    else:
        return ''
