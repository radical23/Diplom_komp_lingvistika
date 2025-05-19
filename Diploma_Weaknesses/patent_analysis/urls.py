from django.urls import path, include
from . import views
from .views import analyze_page  # Если она вам нужна

urlpatterns = [
    path('analyze/', views.analyze_patent, name='analyze_patent'),
    path('save/', views.save_analysis, name='save_analysis'),  # Исправлено на save_analysis
    path("analyze-page/", analyze_page, name="analyze_page"),
    path('', views.home_page,name='home_page'),
    #path('api-auth/', include('rest_framework.urls'))
]