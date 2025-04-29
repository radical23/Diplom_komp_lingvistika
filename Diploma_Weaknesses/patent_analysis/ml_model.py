import pickle
import os

# Путь к файлу модели
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'classifier.pickle')

# Загрузка модели один раз при первом обращении
with open(MODEL_PATH, 'rb') as model_file:
    classifier = pickle.load(model_file)
