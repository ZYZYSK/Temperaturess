from django.db import models

# Create your models here.

# 観測値


class TimeData(models.Model):
    tm = models.DateTimeField(primary_key=True)
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    # whether or not an external probe is connected
    is_external = models.BooleanField(null=True, blank=True)
    # battery remaining
    battery = models.IntegerField(null=True, blank=True)


class DayData(models.Model):
    day = models.DateField(primary_key=True)
    temperature_min = models.ForeignKey(TimeData, null=True, blank=True, on_delete=models.SET_NULL, related_name="temperature_min")
    temperature_max = models.ForeignKey(TimeData, null=True, blank=True, on_delete=models.SET_NULL, related_name="temperature_max")
    temperature_avg = models.FloatField(null=True, blank=True)
    humidity_min = models.ForeignKey(TimeData, null=True, blank=True, on_delete=models.SET_NULL, related_name="humidity_min")
    humidity_max = models.ForeignKey(TimeData, null=True, blank=True, on_delete=models.SET_NULL, related_name="humidity_max")
    humidity_avg = models.FloatField(null=True, blank=True)
    weather = models.CharField(max_length=50, default="")
    # whether or not all data is recorded
    is_incomplete = models.BooleanField(default=True)


# Normal value
class NormalData(models.Model):
    # from what time
    year_start = models.IntegerField()
    # until what time
    year_end = models.IntegerField()
    day = models.DateField(primary_key=True)
    temperature_min = models.FloatField()
    temperature_max = models.FloatField()
    temperature_avg = models.FloatField()
    # threshold
    temperature_min_lowest = models.FloatField()
    temperature_min_low = models.FloatField()
    temperature_min_high = models.FloatField()
    temperature_min_highest = models.FloatField()
    temperature_max_lowest = models.FloatField()
    temperature_max_low = models.FloatField()
    temperature_max_high = models.FloatField()
    temperature_max_highest = models.FloatField()
    temperature_avg_lowest = models.FloatField()
    temperature_avg_low = models.FloatField()
    temperature_avg_high = models.FloatField()
    temperature_avg_highest = models.FloatField()
