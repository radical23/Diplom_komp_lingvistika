from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("DROP TABLE IF EXISTS classified_weaknesses")
    print("Таблица удалена")