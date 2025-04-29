from django.http import HttpResponse, JsonResponse
from .forms import PatentURLForm
from django.shortcuts import render,redirect
from .models import AnalyzedPatent
from .neural_engine import classify_weakness_by_patent,stop_phrases
from .parsing.description_parser import fetch_patent_description_selenium

import pickle
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'classifier.pickle')
with open(MODEL_PATH, 'rb') as model_file:
    classifier = pickle.load(model_file)



def analyze_patent(request):
    if request.method == "POST":
        url = request.POST.get("url")
        if not url:
            return JsonResponse({"error": "Не передан URL патента."}, status=400)

        description = fetch_patent_description_selenium(url)

        if description.startswith("Ошибка") or description == "Описание не найдено.":
            return JsonResponse({"error": description}, status=500)

        сleaned_description = ' '.join(description.split())

        weaknesses = classify_weakness_by_patent(сleaned_description,classifier,stop_phrases)

        return JsonResponse({
            "description": сleaned_description,
            "weaknesses": weaknesses
        })

    return render(request, "analyze_patent.html")

# def upload_patent(request):
#     result = None
#     url = None
#     if request.method == 'POST':
#         form = PatentURLForm(request.POST)     
#             if form.is_valid():
#             url = form.cleaned_data['patent_url']
#             result = analyze_patent_text(url)
#         # elif 'save' in request.POST:
#         #     result = request.POST.get('result')
#         #     AnalyzedPatent.objects.create(patent_url=url,result=result)
#         #     return HttpResponse("Результат сохранен!")

#     else:
#         form = PatentURLForm()

#     return render(request,'patent_analysis/upload.html', {'form': form,'result': result})

def save_analysis(request):
    if request.method == 'POST':
        result = request.POST.get('result')
        source_url = request.POST.get('source_url')

        return render(request,'patent_analysis/success.html')
    else:
        return redirect('upload_patent')
    
# def analyze_view(request):
#      if request.method == "POST":
#          url = request.POST.get("url")
#          if not url:
#              return JsonResponse({"error": "URL не предоставлен"}, status=400)
    
#          results = analyze_patent_by_url(url)
#          return JsonResponse({"results":results})
#      return JsonResponse({"error":"Неверный метод запроса"}, status=405)

def analyze_page(request):
    return render(request,"analyze.html")

