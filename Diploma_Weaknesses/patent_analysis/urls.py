from django.urls import path
from . import views
from .views import analyze_page

urlpatterns = [
    #path("upload/",views.upload_patent, name="upload_patent"),
    path('save/',views.save_analysis,name='save_analysis'),
    path('analyze/',views.analyze_patent, name='analyze_patent'),
    path("analyze-page/", analyze_page, name="analyze_page"),
]