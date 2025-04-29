from django.db import models

# Create your models here.
class AnalyzedPatent(models.Model):
    patent_url = models.URLField()
    result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.patent_url