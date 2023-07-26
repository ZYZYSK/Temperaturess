from django import template
import numpy as np
from ..models import DayData

register = template.Library()


@register.simple_tag
# 気温の平均値
def average_temperature(year: int, month: int, day: int, datas: list):
    try:
        return DayData.objects.get(
            day__year=year, day__month=month, day__day=day
        ).temperature_avg
    except Exception as e:
        print(e)
        if len(datas) == 0:
            return -1
        temperatures = [data["temperature"] for data in datas]
        return np.average(temperatures)


@register.simple_tag
# 湿度の平均値
def average_humidity(year: int, month: int, day: int, datas: list):
    try:
        return DayData.objects.get(
            day__year=year, day__month=month, day__day=day
        ).humidity_avg
    except Exception as e:
        print(e)
        if len(datas) == 0:
            return -1
        humidities = [data["humidity"] for data in datas]
        return np.average(humidities)


@register.filter
# 気温の最小値と時間
def min_temperature(datas: list, i=1):
    if len(datas) == 0:
        return
    if i == 1:
        return min(datas, key=lambda x: x["temperature"])["temperature"]
    else:
        return min(datas, key=lambda x: x["temperature"])["tm"]


@register.filter
# 湿度の最小値と時間
def min_humidity(datas: list, i=1):
    if len(datas) == 0:
        return
    if i == 1:
        return min(datas, key=lambda x: x["humidity"])["humidity"]
    else:
        return min(datas, key=lambda x: x["humidity"])["tm"]


@register.filter
# 気温の最大値と時間
def max_temperature(datas: list, i=1):
    if len(datas) == 0:
        return
    if i == 1:
        return max(datas, key=lambda x: x["temperature"])["temperature"]
    else:
        return max(datas, key=lambda x: x["temperature"])["tm"]


@register.filter
# 湿度の最大値と時間
def max_humidity(datas: list, i=1):
    if len(datas) == 0:
        return
    if i == 1:
        return max(datas, key=lambda x: x["humidity"])["humidity"]
    else:
        return max(datas, key=lambda x: x["humidity"])["tm"]
