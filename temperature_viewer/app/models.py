from django.db import models

# Create your models here.


# 観測値
class TimeData(models.Model):
    # 日時
    tm = models.DateTimeField()
    # 気温
    temperature = models.FloatField(null=True)
    # 湿度
    humidity = models.IntegerField(null=True)


# 日別値
class DayData(models.Model):
    # 日付
    day = models.DateField()
    # 最低気温
    temperature_min = models.ForeignKey(TimeData, null=True, on_delete=models.SET_NULL, related_name='temperature_min')
    # 最高気温
    temperature_max = models.ForeignKey(TimeData, null=True, on_delete=models.SET_NULL, related_name='temperature_max')
    # 平均気温
    temperature_ave = models.FloatField(null=True)
    # 平均湿度
    humidity_ave = models.IntegerField(null=True)
    # 最低湿度
    humidity_min = models.ForeignKey(TimeData, null=True, on_delete=models.SET_NULL, related_name='humidity_min')


# 平年値
class NormalData(models.Model):
    # 日付
    day = models.DateField()
    # 最低気温
    temperature_min = models.FloatField()
    # 最高気温
    temperature_max = models.FloatField()
    # 平均気温
    temperature_ave = models.FloatField()
    # 「高い」の閾値
    temperature_threshold_highest = models.FloatField()
    # 「やや高い」の閾値
    temperature_threshold_high = models.FloatField()
    # 「やや低い」の閾値
    temperature_threshold_low = models.FloatField()
    # 「低い」の閾値
    temperature_threshold_lowest = models.FloatField()
