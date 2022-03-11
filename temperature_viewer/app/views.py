import datetime
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
        context['daydatas'] = get_list_or_404(DayData.objects.filter(day__year=kwargs['year']))
        context['normaldatas'] = get_list_or_404(NormalData.objects.all())
        return render(self.request, self.template_name, context)


class MonthView(TemplateView):
    template_name = "month.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数

    def get(self, request, *args, **kwargs):
        context = super(MonthView, self).get_context_data(**kwargs)
        # 年月日を個別に渡す
        context['year'] = kwargs['year']
        context['month'] = kwargs['month']
        context['day'] = 1
        # 最古の月かどうか
        object_oldest = DayData.objects.order_by('day').first()
        if object_oldest is not None:
            context['oldest'] = object_oldest.day.year == kwargs['year'] and object_oldest.day.month == kwargs['month']
        else:
            context['oldest'] = False
        # データベースからオブジェクトの取得
        daydatas = get_list_or_404(DayData.objects.filter(day__year=kwargs['year'], day__month=kwargs['month']).order_by('day'))
        normaldatas = get_list_or_404(NormalData.objects.filter(day__month=kwargs['month']).order_by('day'))
        context['datas'] = [{'daydata': t[0], 'normaldata':t[1]} for t in zip(daydatas, normaldatas)]
        # 渡す
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
        context['timedatas'] = get_list_or_404(TimeData.objects.filter(tm__year=kwargs['year'], tm__month=kwargs['month'], tm__day=kwargs['day']))
        # グラフ描画
        x = [timezone.localtime(data.tm) for data in context['timedatas']]
        y_temperature = [round(data.temperature, 1) for data in context['timedatas']]
        y_humidity = [round(data.humidity, 0) for data in context['timedatas']]
        context['graph_temperature'] = self.graph(x, y_temperature)
        context['graph_humidity'] = self.graph(x, y_humidity)
        # 渡す
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
        elif file_type == 'normal':
            context['succeed'], context['state'] = self.process_normal(file=content)
        else:
            pass
        return render(self.request, self.template_name, context)

    def process_ambient(self, file: TemporaryUploadedFile):
        cnt_timedata = 0
        cnt_daydata = 0
        cnt_daydata_changed = 0
        first = True
        try:
            datas = file.read().decode('utf-8')
        # [例外処理]ファイルエラー
        except UnicodeDecodeError:
            return 0, 'ファイルが無効です'
        # [例外処理]その他
        except Exception as e:
            return 0, f'{e.__class__.__name__}: {e}'
        # TimeDataの作成
        days = []
        for line in datas.split('\n'):
            try:
                # 1行目は飛ばす
                if first:
                    first = False
                    continue
                # データの読み取り
                record = line.split(',')[1:]
                # もし最終行だったら
                if record is None or len(record) == 0:
                    continue
                tm = timezone.datetime.strptime(record[0], '%Y%m%d%H%M')
                tm = timezone.make_aware(tm)
                days.append(timezone.datetime(tm.year, tm.month, tm.day, 0, 0))
                temperature = float(record[1])
                if temperature > 327.67:
                    temperature -= 655.36
                humidity = float(record[2])
                is_external = bool(record[3])
                # DBへの登録
                TimeData.objects.create(tm=tm, temperature=temperature, humidity=humidity, is_external=is_external)
            # [例外処理]重複エラー
            except IntegrityError:
                continue
            # [例外処理]その他
            except Exception as e:
                return 0, f'{e.__class__.__name__}: {e}'
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
                temperature_avg = temperature_sorted.aggregate(Avg('temperature'))
                humidity_min = humidity_sorted.first()
                humidity_max = humidity_sorted.last()
                humidity_avg = humidity_sorted.aggregate(Avg('humidity'))
                # DBへの登録
                DayData.objects.create(day=day, temperature_min=temperature_min, temperature_max=temperature_max, temperature_avg=temperature_avg['temperature__avg'], humidity_min=humidity_min, humidity_max=humidity_max, humidity_avg=humidity_avg['humidity__avg'])
            # [例外処理]重複エラー
            except IntegrityError:
                daydata = DayData.objects.filter(day__year=day.year, day__month=day.month, day__day=day.day).first()
                daydata.day = day
                daydata.temperature_min = temperature_min
                daydata.temperature_max = temperature_max
                daydata.temperature_avg = temperature_avg['temperature__avg']
                daydata.humidity_min = humidity_min
                daydata.humidity_max = humidity_max
                daydata.humidity_avg = humidity_avg['humidity__avg']
                daydata.save()
                cnt_daydata_changed += 1
            # [例外処理]その他
            except Exception as e:
                return 0, f'{cnt_timedata}件のTimeDataを作成しました<br>DayData: {e.__class__.__name__}:{e}'
            else:
                cnt_daydata += 1

        return 1, f'{cnt_timedata}件のTimeDataを作成しました<br>{cnt_daydata}件のDayDataを作成しました<br>{cnt_daydata_changed}件のDayDataを変更しました'

    def process_normal(self, file: TemporaryUploadedFile):
        cnt_normaldata = 0
        cnt_normaldata_changed = 0
        try:
            datas = file.read().decode('utf-8')
        # [例外処理]ファイルエラー
        except UnicodeDecodeError:
            return 0, 'ファイルが無効です'
        # [例外処理]その他
        except Exception as e:
            return 0, f'{e.__class__.__name__}: {e}'
        # NormalDataの作成
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
        # データの読み取り(最終行はのぞく)
        for line in datas.replace(' ', '').split('\n')[:-1]:
            try:
                record = line.split(',')
                year_start = int(record[4])
                year_end = int(record[5])
                month = int(record[6])
                day = 1
                for i in range(7, len(record), 2):
                    try:
                        # 気温　日平均
                        if record[2] == '0500':
                            temperature_avgs[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日平均 低い
                        elif record[2] == '0522':
                            temperature_avg_lowests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日平均 やや低い
                        elif record[2] == '0523':
                            temperature_avg_lows[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日平均 やや高い
                        elif record[2] == '0524':
                            temperature_avg_highs[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日平均 高い
                        elif record[2] == '0525':
                            temperature_avg_highests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温　日最高
                        elif record[2] == '0600':
                            temperature_maxs[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最高 低い
                        elif record[2] == '0622':
                            temperature_max_lowests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最高 やや低い
                        elif record[2] == '0623':
                            temperature_max_lows[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最高 やや高い
                        elif record[2] == '0624':
                            temperature_max_highs[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最高 高い
                        elif record[2] == '0625':
                            temperature_max_highests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温　日最低
                        elif record[2] == '0700':
                            temperature_mins[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最低 低い
                        elif record[2] == '0722':
                            temperature_min_lowests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最低 やや低い
                        elif record[2] == '0723':
                            temperature_min_lows[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最低 やや高い
                        elif record[2] == '0724':
                            temperature_min_highs[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # 気温 日最低 高い
                        elif record[2] == '0725':
                            temperature_min_highests[datetime.date(2000, month, day)] = float(record[i]) / 10
                        # それ以外
                        else:
                            break
                    except ValueError:
                        continue
                    else:
                        # 日付を進める
                        day += 1
            # [例外処理]その他
            except Exception as e:
                return 0, f'{e.__class__.__name__}: {e}'
        # NormalDataの作成
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
                # DBへの登録
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
            # [例外処理]重複エラー
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
            # [例外処理]その他
            except Exception as e:
                return 0, f'{e.__class__.__name__}: {e}'
            else:
                cnt_normaldata += 1
        return 1, f'{cnt_normaldata}件のNormalDataを作成しました<br>{cnt_normaldata_changed}件のNormalDataを変更しました'
