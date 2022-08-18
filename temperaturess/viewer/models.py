from django.db import models

# Create your models here.

# 観測値


class TimeData(models.Model):
    # 日時
    tm = models.DateTimeField(primary_key=True)
    # 気温
    temperature = models.FloatField(null=True, blank=True)
    # 湿度
    humidity = models.FloatField(null=True, blank=True)
    # 外部プローブ
    is_external = models.BooleanField(null=True, blank=True)
    # バッテリーの残量
    battery = models.IntegerField(null=True, blank=True)


# 日別値
class DayData(models.Model):
    # 日付
    day = models.DateField(primary_key=True)
    # 最低気温
    temperature_min = models.ForeignKey(TimeData, null=True, blank=True, on_delete=models.SET_NULL, related_name='temperature_min')
    # 最高気温
    temperature_max = models.ForeignKey(TimeData, null=True, blank=True, on_delete=models.SET_NULL, related_name='temperature_max')
    # 平均気温
    temperature_avg = models.FloatField(null=True, blank=True)
    # 最低湿度
    humidity_min = models.ForeignKey(TimeData, null=True, blank=True, on_delete=models.SET_NULL, related_name='humidity_min')
    # 最低湿度
    humidity_max = models.ForeignKey(TimeData, null=True, blank=True, on_delete=models.SET_NULL, related_name='humidity_max')
    # 平均湿度
    humidity_avg = models.FloatField(null=True, blank=True)
    # 天気
    weather = models.CharField(max_length=50, default='')

    # データ件数がすべてそろっていないかどうか
    is_incomplete = models.BooleanField(default=True)


# 平年値
class NormalData(models.Model):
    # 開始年
    year_start = models.IntegerField()
    # 終了年
    year_end = models.IntegerField()
    # 日付
    day = models.DateField(primary_key=True)
    # 最低気温
    temperature_min = models.FloatField()
    # 最高気温
    temperature_max = models.FloatField()
    # 平均気温
    temperature_avg = models.FloatField()
    # 閾値
    # 「高い」の閾値
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
