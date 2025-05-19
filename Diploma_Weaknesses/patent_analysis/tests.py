from django.test import TestCase
from patent_analysis.models import AnalyzedPatent
from django.urls import reverse
from unittest.mock import patch
class ModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.patent = AnalyzedPatent.objects.create(
            patent="RU123456",
            sentence="Низкая термостойкость материала",
            classification="Недостатки (вероятность: 0.87)"
        )

    def test_analyzed_patent_creation(self):
        patent = AnalyzedPatent.objects.get(id=self.patent.id)
        self.assertEqual(patent.sentence, "Низкая термостойкость материала")
        self.assertIn("0.87", patent.classification)
        self.assertEqual(patent.patent, "RU123456")

    def test_patent_default_values(self):
        new_patent = AnalyzedPatent.objects.create(
            patent="RU654321",
            sentence="Другой пример недостатка"
        )
        self.assertEqual(new_patent.classification, "Недостатки")

    def test_str_representation(self):
        self.assertEqual(str(self.patent), f"{self.patent.patent}: {self.patent.sentence}")

    def test_patent_filtering(self):
        results = AnalyzedPatent.objects.filter(patent="RU123456")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].sentence, "Низкая термостойкость материала")

    def test_update_classification(self):
        self.patent.classification = "Недостатки (вероятность: 0.95)"
        self.patent.save()
        updated = AnalyzedPatent.objects.get(id=self.patent.id)
        self.assertIn("вероятность: 0.95", updated.classification)

    def test_delete_patent(self):
        patent_id = self.patent.id
        self.patent.delete()
        self.assertFalse(AnalyzedPatent.objects.filter(id=patent_id).exists())

    def test_home_page_status_code(self):
        url = reverse('home_page')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_patent_exists_in_db(self):
        AnalyzedPatent.objects.create(
            patent="№158625",
            sentence="Пример недостатка",
            classification="Недостатки"
        )
        exists = AnalyzedPatent.objects.filter(patent="№158625").exists()
        self.assertTrue(exists)

    

    def test_patent_saved_after_analysis(self):
        """Проверка, что после анализа создается объект AnalyzedPatent"""
        url = reverse('analyze_patent')
        test_url = "https://patents.google.com/patent/RU219645U9/ru?oq=RU-219645"

        # Мокаем функции, чтобы не использовать Selenium и модель
        with patch("patent_analysis.views.fetch_patent_description_selenium") as mock_fetch, \
            patch("patent_analysis.views.classify_weakness_by_patent") as mock_classify:

            mock_fetch.return_value = "Описание патента. RU123456 Плохая термостойкость."
            mock_classify.return_value = [{
                "патент": "RU123456",
                "предложение": "Плохая термостойкость.",
                "классификация": "Недостатки (вероятность: 0.91)"
            }]

            response = self.client.post(url, data={"url": test_url})

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "split_view.html")
            self.assertTrue(AnalyzedPatent.objects.filter(patent="RU123456").exists())


    def test_split_view_rendered_on_post(self):
        """Проверка, что split_view.html используется при обычном POST-запросе"""
        url = reverse('analyze_patent')
        test_url = "https://patents.google.com/patent/RU219645U9/ru?oq=RU-219645"

        with self.settings(DEBUG=True):
            response = self.client.post(url, data={"url": test_url})
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "split_view.html")

