from django import template
import numpy as np
register = template.Library()


@register.filter
# 気温の平均値
def average_temperature(datas: list):
    if len(datas) == 0: return
    temperatures = [data.temperature for data in datas]
    return np.average(temperatures)


@register.filter
# 湿度の平均値
def average_humidity(datas: list):
    if len(datas) == 0: return
    humidities = [data.humidity for data in datas]
    return np.average(humidities)


@register.filter
# 気温の最小値と時間
def min_temperature(datas: list, i=1):
    if len(datas) == 0: return
    datas = [data.__dict__ for data in datas]
    if i == 1:
        return min(datas, key=lambda x: x['temperature'])['temperature']
    else:
        return min(datas, key=lambda x: x['temperature'])['tm']


@register.filter
# 湿度の最小値と時間
def min_humidity(datas: list, i=1):
    if len(datas) == 0: return
    datas = [data.__dict__ for data in datas]
    if i == 1:
        return min(datas, key=lambda x: x['humidity'])['humidity']
    else:
        return min(datas, key=lambda x: x['humidity'])['tm']


@register.filter
# 気温の最大値と時間
def max_temperature(datas: list, i=1):
    if len(datas) == 0: return
    datas = [data.__dict__ for data in datas]
    if i == 1:
        return max(datas, key=lambda x: x['temperature'])['temperature']
    else:
        return max(datas, key=lambda x: x['temperature'])['tm']


@register.filter
# 湿度の最大値と時間
def max_humidity(datas: list, i=1):
    if len(datas) == 0: return
    datas = [data.__dict__ for data in datas]
    if i == 1:
        return max(datas, key=lambda x: x['humidity'])['humidity']
    else:
        return max(datas, key=lambda x: x['humidity'])['tm']
