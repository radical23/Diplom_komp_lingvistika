from django.db import models

class AnalyzedPatent(models.Model):
    patent = models.CharField(max_length=255, default='ПАТЕНТ_НЕ_УКАЗАН')
    sentence = models.TextField(default='')
    classification = models.CharField(max_length=100, default='Недостатки')

    class Meta:
        db_table = 'classified_weaknesses'  # Жёстко фиксируем имя таблицы