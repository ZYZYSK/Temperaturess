from multiprocessing.sharedctypes import Value
from sqlite3 import Time
from django.db import IntegrityError
from django.shortcuts import get_list_or_404, render
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from app.models import *
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.utils import timezone
from django.db.models import Avg
import plotly.graph_objects as go
# Create your views here.


def view_index(request):
    # 最新の年月にジャンプ
    tm_current = timezone.datetime.now()
    return redirect(f'{tm_current.year}/{tm_current.month}/{tm_current.day}')


class YearView(TemplateView):
    template_name = "year.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数

    def get(self, request, *args, **kwargs):
        context = super(YearView, self).get_context_data(**kwargs)
        # データベースからオブジェクトの取得
        context['daydata_list'] = get_list_or_404(DayData.objects.filter(day__year=kwargs['year']))
        context['normaldata_list'] = get_list_or_404(NormalData.objects.filter(day__year=kwargs['year']))
        return render(self.request, self.template_name, context)


class MonthView(TemplateView):
    template_name = "month.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数

    def get(self, request, *args, **kwargs):
        context = super(MonthView, self).get_context_data(**kwargs)
        # データベースからオブジェクトの取得
        context['daydata_list'] = get_list_or_404(DayData.objects.filter(day__year=kwargs['year'], day__month=kwargs['month']))
        context['normaldata_list'] = get_list_or_404(NormalData.objects.filter(day__year=kwargs['year'], day__month=kwargs['month']))
        context['normaldata_list'] = NormalData.objects.all()
        return render(self.request, self.template_name, context)


class DayView(TemplateView):
    template_name = "day.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数

    def get(self, request, *args, **kwargs):
        context = super(DayView, self).get_context_data(**kwargs)
        # 年月日を個別に渡す
        context['year'] = kwargs['year']
        context['month'] = kwargs['month']
        context['day'] = kwargs['day']
        # 最古の日付かどうか
        object_oldest = DayData.objects.order_by('day').first()
        if object_oldest is not None:
            context['oldest'] = object_oldest.day.year == kwargs['year'] and object_oldest.day.month == kwargs['month'] and object_oldest.day.day == kwargs['day']
        else:
            context['oldest'] = False
        # データベースからオブジェクトの取得
        context['timedata_list'] = get_list_or_404(TimeData.objects.filter(tm__year=kwargs['year'], tm__month=kwargs['month'], tm__day=kwargs['day']))
        # グラフ描画
        x = [timezone.localtime(data.tm) for data in context['timedata_list']]
        y_temperature = [round(data.temperature, 1) for data in context['timedata_list']]
        y_humidity = [round(data.humidity, 0) for data in context['timedata_list']]
        context['graph_temperature'] = self.graph(x, y_temperature)
        context['graph_humidity'] = self.graph(x, y_humidity)
        return render(self.request, self.template_name, context)

    def graph(self, x: list, y: list):
        # 描画
        fig = go.Figure(go.Scatter(x=x, y=y))
        fig.update_layout(plot_bgcolor="#F5F5F5", xaxis_tickformat='%H:%M', autosize=True)
        fig.update_xaxes(linecolor="black", gridcolor="grey", mirror="allticks", zeroline=False)
        fig.update_yaxes(linecolor="black", gridcolor="grey", mirror="allticks", zeroline=False)
        return fig.to_html(include_plotlyjs=False, full_html=False, default_width='90vw')
        # return plot(fig, output_type='div', include_plotlyjs=False)


class UploadView(TemplateView):
    template_name = "upload.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数

    def get(self, request, *args, **kwargs):
        context = super(UploadView, self).get_context_data(**kwargs)
        context['year'] = timezone.datetime.now().year
        context['month'] = timezone.datetime.now().month
        context['day'] = timezone.datetime.now().day
        context['succeed'] = 1
        context['state'] = ''
        return render(self.request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # HTMLに渡す変数
        context = super(UploadView, self).get_context_data(**kwargs)
        context['year'] = timezone.datetime.now().year
        context['month'] = timezone.datetime.now().month
        context['day'] = timezone.datetime.now().day
        context['succeed'] = 1
        context['state'] = ''
        # データの取得（POST）
        file_type = request.POST.get('filetype', None)
        content = request.FILES['content']
        # データの読み取り
        if file_type == 'ambient':
            context['succeed'], context['state'] = self.process_ambient(file=content)
        else:
            pass
        return render(self.request, self.template_name, context)

    def process_ambient(self, file: TemporaryUploadedFile):
        cnt_timedata = 0
        cnt_daydata = 0
        cnt_daydata_changed = 0
        first = True
        try:
            data = file.read().decode('utf-8')
        # [例外処理]ファイルエラー
        except UnicodeDecodeError:
            return 0, 'ファイルが無効です'
        days = []
        for line in data.split('\n'):
            try:
                # 1行目は飛ばす
                if first:
                    first = False
                    continue
                # もし最終行だったら
                # データの読み取り
                records = line.split(',')[1:]
                if records is None or len(records) == 0:
                    continue
                tm = timezone.datetime.strptime(records[0], '%Y%m%d%H%M')
                tm = timezone.make_aware(tm)
                days.append(timezone.datetime(tm.year, tm.month, tm.day, 0, 0))
                temperature = float(records[1])
                if temperature > 327.67:
                    temperature -= 655.36
                humidity = float(records[2])
                is_external = bool(records[3])
                # DBへの登録
                TimeData.objects.create(tm=tm, temperature=temperature, humidity=humidity, is_external=is_external)
            # [例外処理]重複エラー
            except IntegrityError:
                continue
            # [例外処理]読み込みエラー
            except ValueError:
                return 0, 'ファイルが無効です'
            # 正常に処理されたデータの件数のカウント
            else:
                cnt_timedata += 1
        # DayDataの作成
        days = set(days)
        for day in days:
            try:
                temperature_sorted = TimeData.objects.filter(tm__year=day.year, tm__month=day.month, tm__day=day.day).order_by('temperature')
                humidity_sorted = TimeData.objects.filter(tm__year=day.year, tm__month=day.month, tm__day=day.day).order_by('humidity')
                temperature_min = temperature_sorted.first()
                temperature_max = temperature_sorted.last()
                temperature_ave = temperature_sorted.aggregate(Avg('temperature'))
                humidity_min = humidity_sorted.first()
                humidity_max = humidity_sorted.last()
                humidity_ave = humidity_sorted.aggregate(Avg('humidity'))
                # DBへの登録
                DayData.objects.create(day=day, temperature_min=temperature_min, temperature_max=temperature_max, temperature_ave=temperature_ave['temperature__avg'], humidity_min=humidity_min, humidity_max=humidity_max, humidity_ave=humidity_ave['humidity__avg'])
            # [例外処理]重複エラー
            except IntegrityError:
                daydata = DayData.objects.filter(day__year=day.year, day__month=day.month, day__day=day.day).first()
                daydata.day = day
                daydata.temperature_min = temperature_min
                daydata.temperature_max = temperature_max
                daydata.temperature_ave = temperature_ave['temperature__avg']
                daydata.humidity_min = humidity_min
                daydata.humidity_max = humidity_max
                daydata.humidity_ave = humidity_ave['humidity__avg']
                daydata.save()
                cnt_daydata_changed += 1
            else:
                cnt_daydata += 1

        return 1, f'{cnt_timedata}件のTimeDataを作成しました<br>{cnt_daydata}件のDayDataを作成しました<br>{cnt_daydata_changed}件のDayDataを変更しました'
