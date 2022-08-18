from urllib.parse import urlparse
from django.urls import path
from .views import YearView, MonthView, DayView, UploadView, EditWeatherView, view_index

urlpatterns = [
    path('', view_index, name='index'),
    path('<int:year>', YearView.as_view(), name='year'),
    path('<int:year>/<int:month>', MonthView.as_view(), name='month'),
    path('<int:year>/<int:month>/<int:day>', DayView.as_view(), name='day'),
    path('upload/', UploadView.as_view(), name='upload'),
    path('edit_weather/<int:year>/<int:month>/<int:day>', EditWeatherView.as_view(), name='edit_weather'),
]
