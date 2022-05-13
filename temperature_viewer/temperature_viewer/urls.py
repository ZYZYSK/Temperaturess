"""temperature_viewer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from unicodedata import name
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path
from app.views import YearView, MonthView, DayView, UploadView, EditWeatherView, view_index
urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('', view_index, name='index'),
    path('<int:year>', YearView.as_view(), name='year'),
    path('<int:year>/<int:month>', MonthView.as_view(), name='month'),
    path('<int:year>/<int:month>/<int:day>', DayView.as_view(), name='day'),
    path('upload/', UploadView.as_view(), name='upload'),
    path('edit_weather/<int:year>/<int:month>/<int:day>', EditWeatherView.as_view(), name='edit_weather'),
]
