from django import template
import numpy as np
register = template.Library()


@register.simple_tag
def average_timedata_temperature(datas):
    temperatures = [data.temperature for data in datas]
    return round(np.average(temperatures), 1)


@register.simple_tag
def average_timedata_humidity(datas):
    humidities = [data.humidity for data in datas]
    return round(np.average(humidities))
