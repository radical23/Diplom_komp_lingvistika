from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import AnalyzedPatent
from .neural_engine import classify_weakness_by_patent, stop_phrases
from .parsing.description_parser import fetch_patent_description_selenium
import pickle
import os
import re
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'classifier.pickle')
with open(MODEL_PATH, 'rb') as model_file:
    classifier = pickle.load(model_file)

def upload_form(request):
    """Отображает форму загрузки патента"""
    return render(request, 'analyze_patent.html') 

def clean_description(text):
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.lower() in ['description', 'translated from']:
            continue
        clean_lines.append(line)
    return '\n'.join(clean_lines)

def analyze_patent(request):
    """Основная функция анализа с двумя режимами: JSON и HTML"""
    if request.method == "POST":
        url = request.POST.get("url")
        if not url:
            return JsonResponse({"error": "Не передан URL патента."}, status=400)

        description = fetch_patent_description_selenium(url)
        
        all_patents = list(set(re.findall(
            r'(?i)\b(?:RU|CN|US|DE|РФ|SK|EP|JP|SU|WO)\s*\d{5,}\b|(?:№|#|N)\s*\d{5,}\b',
            description
        )))
        
        if description.startswith("Ошибка") or description == "Описание не найдено.":
            return JsonResponse({"error": description}, status=500)

        cleaned_description = ' '.join(description.split())
        weaknesses = classify_weakness_by_patent(cleaned_description, classifier, stop_phrases)

        # Возвращаем HTML для двухоконного интерфейса
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return render(request, 'split_view.html', {
                'description': clean_description(description),
                'weaknesses': weaknesses,
                'all_patents': all_patents,
                'original_url': url
            })
        
        # Или JSON для AJAX-запросов
        return JsonResponse({
            "description": description,
            "weaknesses": weaknesses
        })

    return render(request, 'analyze_patent.html')

def save_analysis(request):
    if request.method == 'POST':
        try:
            i = 1
            while f'patent_{i}' in request.POST:
                AnalyzedPatent.objects.create(
                    patent=request.POST.get(f'patent_{i}'),  # Номер патента
                    sentence=request.POST.get(f'weakness_{i}'),  # Текст недостатка
                    classification="Недостатки"  # Фиксированное значение
                )
                i += 1
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return redirect('analyze_patent')

def analyze_page(request):
    """Страница с двумя окнами (альтернативная версия)"""
    return render(request, "analyze_patent.html")

def save_results(request):
    """Алиас для save_analysis"""
    return save_analysis(request)

