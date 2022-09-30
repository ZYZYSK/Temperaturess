
# Create your views here.

from ast import arg
from curses.ascii import isalpha
import numpy as np
import base64
import io
import math
import calendar
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import datetime
from itertools import zip_longest
from django.utils import timezone
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.db import IntegrityError
from django.db.models import Q, Avg
from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from viewer.models import *
matplotlib.use("Agg")


def view_index(request):
    """If the URL only contains the domain name, it automatically jumps to today's page or this month's page."""
    """どっちにジャンプするかは、設定で変更可能にする"""
    # get the current date
    tm_current = timezone.datetime.now()
    # redirect to current date
    return redirect("day", tm_current.year, tm_current.month, tm_current.day)


def check_leap_year(year: int) -> bool:
    if year % 4 == 0:
        if year % 100 == 0 and year % 400 != 0:
            return False
        else:
            return True
    return False


class YearView(TemplateView):
    """jump to the page of the specified year"""
    template_name = "year.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数

    def get_context_data(self, **kwargs):
        # pass date separately
        kwargs["month"] = 1
        kwargs["day"] = 1
        # pass data
        return super().get_context_data(**kwargs)


class MonthView(TemplateView):
    """jump to the page of the specified month"""
    template_name = "month.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数
    def get(self, request, *args, **kwargs):
        # you can't get this month's data if today's date is 1
        tm_current = timezone.datetime.now()
        if tm_current.year == kwargs["year"] and tm_current.month == kwargs["month"] and tm_current.day == 1:
            if kwargs["month"] == 1:
                kwargs["year"]-=1
            else:
                kwargs["month"]-=1
            return redirect("month",kwargs["year"],kwargs["month"])
        return super().get(request,*args,**kwargs)

    def get_context_data(self, **kwargs):
        # pass date separately
        kwargs["day"] = 1
        # get objects from database
        daydatas = get_list_or_404(DayData.objects.filter(day__year=kwargs["year"], day__month=kwargs["month"]).order_by("day"))
        normaldatas = get_list_or_404(NormalData.objects.filter(day__month=kwargs["month"]).order_by("day"))
        if daydatas[0].day.month == 2 and not check_leap_year(daydatas[0].day.year):
            normaldatas.pop()
        # draw graph
        self.draw_graph(daydatas, normaldatas, kwargs)
        # zip
        kwargs["datas"] = [{"daydata": t[0], "normaldata":t[1]} for t in zip_longest(daydatas, normaldatas)]
        # pass data
        return super().get_context_data(**kwargs)

    def draw_graph(self, daydatas: list, normaldatas: list, kwargs: dict):
        x_daydatas = [daydata.day.day for daydata in daydatas]
        x_normaldatas = [normaldata.day.day for normaldata in normaldatas]
        # temperature
        y_1_temperatures_day_min = [round(daydata.temperature_min.temperature, 1) for daydata in daydatas]
        y_1_temperatures_day_max = [round(daydata.temperature_max.temperature, 1) for daydata in daydatas]
        y_1_temperatures_day_avg = [round(daydata.temperature_avg, 1) for daydata in daydatas]
        y_1_temperatures_normal_min = [round(normaldata.temperature_min, 1) for normaldata in normaldatas]
        y_1_temperatures_normal_max = [round(normaldata.temperature_max, 1) for normaldata in normaldatas]
        y_1_temperatures_normal_avg = [round(normaldata.temperature_avg, 1) for normaldata in normaldatas]
        kwargs["graph_1_temperature"] = self.graph_1(
            x=x_daydatas,
            x_n=x_normaldatas,
            y_min=y_1_temperatures_day_min,
            y_max=y_1_temperatures_day_max,
            y_avg=y_1_temperatures_day_avg,
            y_n_min=y_1_temperatures_normal_min,
            y_n_max=y_1_temperatures_normal_max,
            y_n_avg=y_1_temperatures_normal_avg,
            dtick=2
        )
        # humidity
        y_1_humidities_min = [round(daydata.humidity_min.humidity) for daydata in daydatas]
        y_1_humidities_max = [round(daydata.humidity_max.humidity) for daydata in daydatas]
        y_1_humidities_avg = [round(daydata.humidity_avg) for daydata in daydatas]
        kwargs["graph_1_humidity"] = self.graph_1(
            x=x_daydatas,
            x_n=x_normaldatas,
            y_min=y_1_humidities_min,
            y_max=y_1_humidities_max,
            y_avg=y_1_humidities_avg,
            dtick=20)
        # 5-days average temperature
        y_5_temperatures_daydata = []
        y_5_temperatures_normaldata = []
        for daydata in daydatas:
            # get 5-days average value
            y_5_dicts_daydata = DayData.objects.filter(day__range=[daydata.day - datetime.timedelta(days=2), daydata.day + datetime.timedelta(days=2)]).values()
            if daydata.day.month == 1 and daydata.day.day == 1:
                y_5_dicts_normaldata = NormalData.objects.filter(
                    Q(day__range=[datetime.date(2000, daydata.day.month, daydata.day.day), datetime.date(2000, daydata.day.month, daydata.day.day) + datetime.timedelta(days=2)])
                    | Q(day=datetime.date(2000, 12, 30)) | Q(day=datetime.date(2000, 12, 31))).values()
            elif daydata.day.month == 1 and daydata.day.day == 2:
                y_5_dicts_normaldata = NormalData.objects.filter(
                    Q(day__range=[datetime.date(2000, daydata.day.month, daydata.day.day), datetime.date(2000, daydata.day.month, daydata.day.day) + datetime.timedelta(days=2)])
                    | Q(day=datetime.date(2000, 12, 31)) | Q(day=datetime.date(2000, 1, 1))).values()
            elif daydata.day.month == 12 and daydata.day.day == 30:
                y_5_dicts_normaldata = NormalData.objects.filter(
                    Q(day__range=[datetime.date(2000, daydata.day.month, daydata.day.day) - datetime.timedelta(days=2), datetime.date(2000, daydata.day.month, daydata.day.day)])
                    | Q(day=datetime.date(2000, 12, 31)) | Q(day=datetime.date(2000, 1, 1))).values()
            elif daydata.day.month == 12 and daydata.day.day == 31:
                y_5_dicts_normaldata = NormalData.objects.filter(
                    Q(day__range=[datetime.date(2000, daydata.day.month, daydata.day.day) - datetime.timedelta(days=2), datetime.date(2000, daydata.day.month, daydata.day.day)])
                    | Q(day=datetime.date(2000, 1, 1)) | Q(day=datetime.date(2000, 1, 2))).values()
            else:
                y_5_dicts_normaldata = NormalData.objects.filter(
                    day__range=[datetime.date(2000, daydata.day.month, daydata.day.day) - datetime.timedelta(days=2), datetime.date(2000, daydata.day.month, daydata.day.day) + datetime.timedelta(days=2)]
                ).values()

            # remove if can't calculate average
            if len(y_5_dicts_daydata) != 5:
                x_daydatas.remove(daydata.day.day)
                continue
            # append data
            y_5_temperatures_daydata.append(np.mean([t["temperature_avg"] for t in y_5_dicts_daydata]))
            y_5_temperatures_normaldata.append(np.mean([t["temperature_avg"] for t in y_5_dicts_normaldata]))
        kwargs["graph_5"] = self.graph_5(
            x=x_daydatas,
            graph_x_n=x_normaldatas,
            y=y_5_temperatures_daydata,
            y_n=y_5_temperatures_normaldata
        )

    def graph_1(self, x: list, x_n: list, y_min: list, y_max: list, y_avg: list, y_n_min: list = None, y_n_max: list = None, y_n_avg: list = None, dtick: int = 1):
        # draw daydatas
        fig = go.Figure(data=[
            go.Scatter(x=x, y=y_min, name="最低", mode="lines+markers", line=dict(color="blue")),
            go.Scatter(x=x, y=y_max, name="最高", mode="lines+markers", line=dict(color="red")),
            go.Scatter(x=x, y=y_avg, name="平均", mode="lines+markers", line=dict(color="green")),
        ])
        # draw normaldatas(temperature only)
        if y_n_min is not None and y_n_avg is not None and y_n_max is not None:
            fig.add_trace(go.Scatter(x=x_n, y=y_n_min, name="最高(平年)", mode="lines", line=dict(color="black")))
            fig.add_trace(go.Scatter(x=x_n, y=y_n_max, name="最低(平年)", mode="lines", line=dict(color="black")))
            fig.add_trace(go.Scatter(x=x_n, y=y_n_avg, name="平均(平年)", mode="lines", line=dict(color="black")))
        # set graph's limit(humidity)
        graph_min = 0
        graph_max = 100
        # set graph's limit(temperature)
        if y_n_min is not None:
            graph_min = min(y_min + y_n_min)
        if y_n_max is not None:
            graph_max = max(y_max + y_n_max)

        fig.update_layout(
            plot_bgcolor="#F5F5F5",
            xaxis_tickformat="%d日",
            autosize=True,
            xaxis=dict(range=(x_n[0], x_n[-1]), dtick="D1"),
            yaxis=dict(
                range=(math.floor(graph_min), math.ceil(graph_max)),
                dtick=dtick
            )
        )
        fig.update_xaxes(linecolor="black", gridcolor="grey", mirror="allticks", zeroline=False)
        fig.update_yaxes(linecolor="black", gridcolor="grey", mirror="allticks", zeroline=False)
        return fig.to_html(include_plotlyjs=False, full_html=False, default_width="90vw")

    def graph_5(self, x: list, graph_x_n: list, y: list, y_n: list):
        graph_x = np.array(x)
        graph_y = np.array(y) - np.array(y_n)
        graph_y_n = np.zeros(len(graph_x_n))
        # 描画
        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        ax.set_xlim(graph_x_n[0], graph_x_n[-1])
        ax.set_xticks(graph_x_n)
        ax.set_ylim(min(-3, math.floor(np.min(graph_y))), max(3, math.ceil(np.max(graph_y))))
        ax.set_yticks(np.arange(min(-3, math.floor(np.min(graph_y))), max(4, math.ceil(np.max(graph_y)))))
        ax.plot(graph_x_n, graph_y_n, color="black", linewidth=2)
        # 描画できるデータがある場合のみ描画
        if len(graph_x) and len(graph_y):
            ax.plot(graph_x, graph_y, color="grey")
            y2 = graph_y_n[graph_x[0]:graph_x[-1] + 1]
            ax.fill_between(x=graph_x, y1=graph_y, y2=graph_y_n[graph_x[0] - 1:graph_x[-1]], where=graph_y >= graph_y_n[graph_x[0] - 1:graph_x[-1]], facecolor="#fe9696", interpolate=True)
            ax.fill_between(x=graph_x, y1=graph_y, y2=graph_y_n[graph_x[0] - 1:graph_x[-1]], where=graph_y <= graph_y_n[graph_x[0] - 1:graph_x[-1]], facecolor="#9696e6", interpolate=True)
            ax.grid()
        # バッファ
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        plt.close()
        graph = base64.b64encode(buffer.getvalue())
        graph = graph.decode("utf-8")
        return graph


class DayView(TemplateView):
    template_name = "day.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数

    def get_context_data(self, **kwargs):
        # get objects from database
        timedatas = get_list_or_404(TimeData.objects.filter(tm__year=kwargs["year"], tm__month=kwargs["month"], tm__day=kwargs["day"]).values())
        kwargs["timedatas"] = timedatas
        # draw graph
        x = [timezone.localtime(timedata["tm"]) for timedata in timedatas]
        y_temperature = [round(timedata["temperature"], 1) for timedata in timedatas]
        y_humidity = [round(timedata["humidity"], 0) for timedata in timedatas]
        kwargs["graph_temperature"] = self.graph(x, y_temperature)
        kwargs["graph_humidity"] = self.graph(x, y_humidity)
        # pass data
        return super().get_context_data(**kwargs)

    def graph(self, x: list, y: list):
        # 描画
        fig = go.Figure(go.Scatter(x=x, y=y))
        fig.update_layout(plot_bgcolor="#F5F5F5", xaxis_tickformat="%H:%M", autosize=True)
        fig.update_xaxes(linecolor="black", gridcolor="grey", mirror="allticks", zeroline=False)
        fig.update_yaxes(linecolor="black", gridcolor="grey", mirror="allticks", zeroline=False)
        return fig.to_html(include_plotlyjs=False, full_html=False, default_width="90vw")


class UploadView(TemplateView):
    template_name = "upload.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数

    def get_context_data(self, **kwargs):
        tm_current = timezone.now()
        kwargs["year"] = tm_current.year
        kwargs["month"] = tm_current.month
        kwargs["day"] = tm_current.day
        kwargs["succeed"] = 1
        kwargs["state"] = ""
        # pass data
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        # HTMLに渡す変数
        context = super(UploadView, self).get_context_data(**kwargs)
        context["year"] = timezone.datetime.now().year
        context["month"] = timezone.datetime.now().month
        context["day"] = timezone.datetime.now().day
        context["succeed"] = 1
        context["state"] = ""
        # データの取得（POST）
        file_type = request.POST.get("filetype", None)
        content = request.FILES["content"]
        # データの読み取り
        if file_type == "ambient":
            context["succeed"], context["state"] = self.process_ambient(file=content)
        elif file_type == "normal":
            context["succeed"], context["state"] = self.process_normal(file=content)
        else:
            pass
        return render(self.request, self.template_name, context)

    def process_ambient(self, file: TemporaryUploadedFile):
        cnt_timedata = 0
        cnt_daydata = 0
        cnt_daydata_changed = 0
        first = True
        try:
            datas = file.read().decode("utf-8")
        # Error: Invalid File
        except UnicodeDecodeError:
            return 0, "Invalid File!"
        # Error: Others
        except Exception as e:
            return 0, f"{e.__class__.__name__}: {e}"
        # Create TimeDatas
        days = []
        for line in datas.split("\n"):
            try:
                # read line
                record = line.split(",")[1:]
                # if reading the last line or invalid line
                if record is None or len(record) < 4:
                    continue
                # if the line contains alphabet
                if record[1].isalpha() or record[2].isalpha() or record[3].isalpha():
                    continue
                tm = timezone.datetime.strptime(record[0], "%Y%m%d%H%M")
                tm = timezone.make_aware(tm)
                days.append(timezone.datetime(tm.year, tm.month, tm.day, 0, 0))
                temperature = float(record[1])
                if temperature > 327.67:
                    temperature -= 655.36
                humidity = float(record[2])
                is_external = bool(record[3])
                # register to DB
                TimeData.objects.create(tm=tm, temperature=temperature, humidity=humidity, is_external=is_external)
            # Error: Duplication
            except IntegrityError:
                continue
            # Error: Others
            except Exception as e:
                return 0, f"{e.__class__.__name__}: {e}"
            # Count created datas
            else:
                cnt_timedata += 1
        # Create DayDatas
        days = set(days)
        for day in days:
            try:
                temperature_sorted = TimeData.objects.filter(tm__year=day.year, tm__month=day.month, tm__day=day.day).order_by("temperature")
                humidity_sorted = TimeData.objects.filter(tm__year=day.year, tm__month=day.month, tm__day=day.day).order_by("humidity")
                temperature_min = temperature_sorted.first()
                temperature_max = temperature_sorted.last()
                temperature_avg = temperature_sorted.aggregate(Avg("temperature"))
                humidity_min = humidity_sorted.first()
                humidity_max = humidity_sorted.last()
                humidity_avg = humidity_sorted.aggregate(Avg("humidity"))
                is_incomplete = temperature_sorted.count() != 288
                # register to DB
                DayData.objects.create(day=day, temperature_min=temperature_min, temperature_max=temperature_max, temperature_avg=temperature_avg["temperature__avg"], humidity_min=humidity_min, humidity_max=humidity_max, humidity_avg=humidity_avg["humidity__avg"], is_incomplete=is_incomplete)
            # Error: Duplication
            except IntegrityError:
                daydata = DayData.objects.filter(day__year=day.year, day__month=day.month, day__day=day.day).first()
                daydata.day = day
                daydata.temperature_min = temperature_min
                daydata.temperature_max = temperature_max
                daydata.temperature_avg = temperature_avg["temperature__avg"]
                daydata.humidity_min = humidity_min
                daydata.humidity_max = humidity_max
                daydata.humidity_avg = humidity_avg["humidity__avg"]
                daydata.is_incomplete = is_incomplete
                daydata.save()
                cnt_daydata_changed += 1
            # Error: Others
            except Exception as e:
                return 0, f"{cnt_timedata}件のTimeDataを作成しました<br>DayData: {e.__class__.__name__}:{e}"
            else:
                cnt_daydata += 1

        return 1, f"{cnt_timedata}件のTimeDataを作成しました<br>{cnt_daydata}件のDayDataを作成しました<br>{cnt_daydata_changed}件のDayDataを変更しました"

    def process_normal(self, file: TemporaryUploadedFile):
        cnt_normaldata = 0
        cnt_normaldata_changed = 0
        try:
            datas = file.read().decode("utf-8")
        # Error: File is Invalid
        except UnicodeDecodeError:
            return 0, "ファイルが無効です"
        # Error: Others
        except Exception as e:
            return 0, f"{e.__class__.__name__}: {e}"
        # Create NormalDatas
        year_start = 0
        year_end = 0
        temperature_mins = dict()
        temperature_maxs = dict()
        temperature_avgs = dict()
        temperature_min_lowests = dict()
        temperature_min_lows = dict()
        temperature_min_highs = dict()
        temperature_min_highests = dict()
        temperature_max_lowests = dict()
        temperature_max_lows = dict()
        temperature_max_highs = dict()
        temperature_max_highests = dict()
        temperature_avg_lowests = dict()
        temperature_avg_lows = dict()
        temperature_avg_highs = dict()
        temperature_avg_highests = dict()
        # Read lines
        for line in datas.replace(" ", "").split("\n")[:-1]:
            try:
                record = line.split(",")
                year_start = int(record[4])
                year_end = int(record[5])
                month = int(record[6])
                day = 1
                for i in range(7, len(record), 2):
                    try:
                        # 気温　日平均
                        if record[2] == "0500":
                            temperature_avgs[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日平均 低い
                        elif record[2] == "0522":
                            temperature_avg_lowests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日平均 やや低い
                        elif record[2] == "0523":
                            temperature_avg_lows[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日平均 やや高い
                        elif record[2] == "0524":
                            temperature_avg_highs[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日平均 高い
                        elif record[2] == "0525":
                            temperature_avg_highests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温　日最高
                        elif record[2] == "0600":
                            temperature_maxs[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最高 低い
                        elif record[2] == "0622":
                            temperature_max_lowests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最高 やや低い
                        elif record[2] == "0623":
                            temperature_max_lows[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最高 やや高い
                        elif record[2] == "0624":
                            temperature_max_highs[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最高 高い
                        elif record[2] == "0625":
                            temperature_max_highests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温　日最低
                        elif record[2] == "0700":
                            temperature_mins[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最低 低い
                        elif record[2] == "0722":
                            temperature_min_lowests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最低 やや低い
                        elif record[2] == "0723":
                            temperature_min_lows[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最低 やや高い
                        elif record[2] == "0724":
                            temperature_min_highs[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最低 高い
                        elif record[2] == "0725":
                            temperature_min_highests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # Others
                        else:
                            break
                    except ValueError:
                        continue
                    else:
                        # proceed
                        day += 1
            # Exception: Others
            except Exception as e:
                return 0, f"{e.__class__.__name__}: {e}"
        # Create NormalDatas
        for i in range(366):
            try:
                day = datetime.date(2000, 1, 1) + datetime.timedelta(days=i)
                temperature_min = temperature_mins[day]
                temperature_max = temperature_maxs[day]
                temperature_avg = temperature_avgs[day]
                temperature_min_lowest = temperature_min_lowests[day]
                temperature_min_low = temperature_min_lows[day]
                temperature_min_high = temperature_min_highs[day]
                temperature_min_highest = temperature_min_highests[day]
                temperature_max_lowest = temperature_max_lowests[day]
                temperature_max_low = temperature_max_lows[day]
                temperature_max_high = temperature_max_highs[day]
                temperature_max_highest = temperature_max_highests[day]
                temperature_avg_lowest = temperature_avg_lowests[day]
                temperature_avg_low = temperature_avg_lows[day]
                temperature_avg_high = temperature_avg_highs[day]
                temperature_avg_highest = temperature_avg_highests[day]
                # register tp DB
                NormalData.objects.create(
                    year_start=year_start, year_end=year_end, day=day,
                    temperature_min=temperature_min,
                    temperature_max=temperature_max,
                    temperature_avg=temperature_avg,
                    temperature_min_lowest=temperature_min_lowest,
                    temperature_min_low=temperature_min_low,
                    temperature_min_high=temperature_min_high,
                    temperature_min_highest=temperature_min_highest,
                    temperature_max_lowest=temperature_max_lowest,
                    temperature_max_low=temperature_max_low,
                    temperature_max_high=temperature_max_high,
                    temperature_max_highest=temperature_max_highest,
                    temperature_avg_lowest=temperature_avg_lowest,
                    temperature_avg_low=temperature_avg_low,
                    temperature_avg_high=temperature_avg_high,
                    temperature_avg_highest=temperature_avg_highest,
                )
            # Error: Duplication
            except IntegrityError:
                normaldata = NormalData.objects.filter(day=day).first()
                normaldata.temperature_min = temperature_min
                normaldata.temperature_max = temperature_max
                normaldata.temperature_avg = temperature_avg
                normaldata.temperature_min_lowest = temperature_min_lowest
                normaldata.temperature_min_low = temperature_min_low
                normaldata.temperature_min_high = temperature_min_high
                normaldata.temperature_min_highest = temperature_min_highest
                normaldata.temperature_max_lowest = temperature_max_lowest
                normaldata.temperature_max_low = temperature_max_low
                normaldata.temperature_max_high = temperature_max_high
                normaldata.temperature_max_highest = temperature_max_highest
                normaldata.temperature_avg_lowest = temperature_avg_lowest
                normaldata.temperature_avg_low = temperature_avg_low
                normaldata.temperature_avg_high = temperature_avg_high
                normaldata.temperature_avg_highest = temperature_avg_highest
                normaldata.save()
                cnt_normaldata_changed += 1
            # Error: Others
            except Exception as e:
                return 0, f"{e.__class__.__name__}: {e}"
            else:
                cnt_normaldata += 1
        return 1, f"{cnt_normaldata}件のNormalDataを作成しました<br>{cnt_normaldata_changed}件のNormalDataを変更しました"


class EditWeatherView(TemplateView):
    template_name = "edit_weather.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数

    def get(self, request, *args, **kwargs):
        context = super(EditWeatherView, self).get_context_data(**kwargs)
        # 年月日を個別に渡す
        context["year"] = kwargs["year"]
        context["month"] = kwargs["month"]
        context["day"] = kwargs["day"]
        # データベースからオブジェクトの取得
        daydata = get_object_or_404(DayData.objects.filter(day__year=kwargs["year"], day__month=kwargs["month"], day__day=kwargs["day"]))
        context["daydata"] = daydata
        # 渡す
        return render(self.request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = super(EditWeatherView, self).get_context_data(**kwargs)
        # データベースからオブジェクトの取得
        daydata = get_object_or_404(DayData.objects.filter(day__year=context["year"], day__month=context["month"], day__day=context["day"]))
        # データの取得（POST）
        weather = request.POST.get("weather", "")
        daydata.weather = weather
        daydata.save()
        return redirect("month", context["year"], context["month"])
