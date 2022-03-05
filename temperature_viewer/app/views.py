from django.shortcuts import get_list_or_404, render
import datetime
# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from app.models import *


def view_index(request):
    # 最新の年月にジャンプ
    tm_current = datetime.datetime.now()
    return redirect(f'{tm_current.year}/{tm_current.month}')


class YearView(TemplateView):
    template_name = "year.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数

    def get(self, request, *args, **kwargs):
        context = super(DayView, self).get_context_data(**kwargs)
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
        # データベースからオブジェクトの取得
        context['timedata_list'] = get_list_or_404(TimeData.objects.filter(tm__year=kwargs['year'], tm__month=kwargs['month'], tm__day=kwargs['day']))
        return render(self.request, self.template_name, context)
