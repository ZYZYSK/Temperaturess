from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from app.models import *


class TemperatureListView(TemplateView):
    template_name = "temperature.html"
    # アスタリスク1つ：可変長引数(タプル型)
    # アスタリスク2つ：辞書型引数

    def get(self, request, *args, **kwargs):
        context = super(TemperatureListView, self).get_context_data(**kwargs)
        # データベースからオブジェクトの取得
        context['timedata_list'] = TimeData.objects.all()
        context['daydata_list'] = DayData.objects.all()
        context['normaldata_list'] = NormalData.objects.all()
        return render(self.request, self.template_name, context)
