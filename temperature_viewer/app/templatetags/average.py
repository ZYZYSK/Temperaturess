from django import template
import numpy as np
register = template.Library()

# day


@register.simple_tag
def average_timedata_temperature(datas):
    temperatures = [data.temperature for data in datas]
    return round(np.average(temperatures), 1)


@register.simple_tag
def average_timedata_humidity(datas):
    humidities = [data.humidity for data in datas]
    return round(np.average(humidities))
# month


@register.simple_tag
def average_daydata_temperature_min(datas):
    temperatures = [data['daydata'].temperature_min.temperature for data in datas]
    return round(np.average(temperatures), 1)


@register.simple_tag
def average_daydata_temperature_max(datas):
    temperatures = [data['daydata'].temperature_max.temperature for data in datas]
    return round(np.average(temperatures), 1)


@register.simple_tag
def average_daydata_temperature_avg(datas):
    temperatures = [data['daydata'].temperature_avg for data in datas]
    return round(np.average(temperatures), 1)


@register.simple_tag
def average_daydata_humidity_min(datas):
    humidities = [data['daydata'].humidity_min.humidity for data in datas]
    return round(np.average(humidities))


@register.simple_tag
def average_daydata_humidity_max(datas):
    humidities = [data['daydata'].humidity_max.humidity for data in datas]
    return round(np.average(humidities))


@register.simple_tag
def average_daydata_humidity_avg(datas):
    humidities = [data['daydata'].humidity_avg for data in datas]
    return round(np.average(humidities))


@register.simple_tag
def average_normaldata_temperature_min(datas):
    temperatures = [data['normaldata'].temperature_min for data in datas]
    return round(np.average(temperatures), 1)


@register.simple_tag
def average_normaldata_temperature_max(datas):
    temperatures = [data['normaldata'].temperature_max for data in datas]
    return round(np.average(temperatures), 1)


@register.simple_tag
def average_normaldata_temperature_avg(datas):
    temperatures = [data['normaldata'].temperature_avg for data in datas]
    return round(np.average(temperatures), 1)
