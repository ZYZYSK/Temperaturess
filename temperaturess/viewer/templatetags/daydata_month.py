from django import template
import numpy as np
register = template.Library()

# day


@register.filter
def average_day_temperature_min(datas):
    temperatures = [data["daydata"].temperature_min.temperature for data in datas if data["daydata"] is not None]
    return np.average(temperatures)


@register.filter
def average_day_temperature_max(datas):
    temperatures = [data["daydata"].temperature_max.temperature for data in datas if data["daydata"] is not None]
    return np.average(temperatures)


@register.filter
def average_day_temperature_avg(datas):
    temperatures = [data["daydata"].temperature_avg for data in datas if data["daydata"] is not None]
    return np.average(temperatures)


@register.filter
def average_day_humidity_min(datas):
    humidities = [data["daydata"].humidity_min.humidity for data in datas if data["daydata"] is not None]
    return np.average(humidities)


@register.filter
def average_day_humidity_max(datas):
    humidities = [data["daydata"].humidity_max.humidity for data in datas if data["daydata"] is not None]
    return np.average(humidities)


@register.filter
def average_day_humidity_avg(datas):
    humidities = [data["daydata"].humidity_avg for data in datas if data["daydata"] is not None]
    return np.average(humidities)


@register.filter
def average_normal_temperature_min(datas):
    temperatures = [data["normaldata"].temperature_min for data in datas if data["normaldata"] is not None]
    return np.average(temperatures)


@register.filter
def average_normal_temperature_max(datas):
    temperatures = [data["normaldata"].temperature_max for data in datas if data["normaldata"] is not None]
    return np.average(temperatures)


@register.filter
def average_normal_temperature_avg(datas):
    temperatures = [data["normaldata"].temperature_avg for data in datas if data["normaldata"] is not None]
    return np.average(temperatures)
