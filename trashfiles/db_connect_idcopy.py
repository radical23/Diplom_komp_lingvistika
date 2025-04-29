import re
import clickhouse_connect
from tkinter import Tk, Text, Button, Listbox, END, Label, Menu
import tkinter as tk
import sqlite3
from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, NewsSyntaxParser, Doc
from razdel import sentenize

"""
добавить в бд колонку с помощью кода patent_Id
"""

# Глобальный список для хранения выделенных фрагментов
highlighted_ranges = []

# Функция поиска недостатков (разбирает только 1 патент за раз)
def find_weaknesses_with_context(full_text):
    keywords = ['недостаток', 'недостатком', 'недостатки', 'недостатков', 'минусы', 'недостатками', 'проблема', 'проблемой']

    segmenter = Segmenter()
    morph_vocab = MorphVocab()
    emb = NewsEmbedding()
    morph_tagger = NewsMorphTagger(emb)
    syntax_parser = NewsSyntaxParser(emb)

    doc = Doc(full_text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_parser)

    paragraphs = full_text.split("\n")
    results = []

    for i, paragraph in enumerate(paragraphs):
        if any(keyword in paragraph.lower() for keyword in keywords):
            context = paragraphs[i - 1] if i > 0 else "Нет контекста"
            results.append(f"Контекст: {context}\n\nФрагмент: {paragraph}")
    
    return results

def find_weaknesses_in_text(full_text):
    keywords = ['недостаток', 'недостатком', 'недостатки', 'недостатков', 'минусы', 'недостатками', 'проблема', 'проблемой']
    
    text_box.tag_remove("weakness_highlight", "1.0", END)

    sentences = list(sentenize(full_text))

    for sent in sentences:

        if any(keyword in sent.text.lower() for keyword in keywords):

            start_idx = text_box.search(sent.text,"1.0",stopindex=END)

            if start_idx:

                end_idx = f"{start_idx}+{len(sent.text)}c"

                text_box.tag_add("weakness_highlight", start_idx, end_idx) 
                highlighted_ranges.append((start_idx,end_idx))



    text_box.tag_config("weakness_highlight", background="red", foreground="black")
# Функция обновления текста и поиска недостатков только для 1 патента
def update_text():
    global weakness_list,highlighted_ranges
    text_box.delete(1.0, END)
    listbox.delete(0, END)  # Очищаем список недостатков
    
    if patents:
        patent_text = patents[current_index]
        
        text_box.insert(END, patent_text)
        find_RU_patents(patent_text)
        label_index.config(text=f"{current_index+1}/{len(patents)}")

        find_weaknesses_in_text(patent_text)

        # for start_idx, end_idx in highlighted_ranges:
        #     text_box.tag_add("highlight",start_idx,end_idx)

        #highlight_existing_weaknesses()
        # Ищем недостатки только для текущего патента
        weakness_list = find_weaknesses_with_context(patent_text)
        
        ru_patents = find_RU_patents(patent_text)

        for ru_patent in ru_patents:
            listbox.insert(END, ru_patent)
        #for weakness in weakness_list:
            #listbox.insert(END, weakness)
    else:
        text_box.insert(END, "Нет данных о патентах")

def next_patent():
    global current_index,highlighted_ranges
    if current_index < len(patents) - 1:
        current_index += 1
        update_text()

def prev_patent():
    global current_index
    if current_index > 0:
        current_index -= 1
        update_text()

def highlight_existing_weaknesses():
    text_box.tag_remove("highlight", "1.0", END)  # Удаляем старое выделение

    cursor.execute("SELECT text FROM weaknesses")  
    saved_weaknesses = [row[0] for row in cursor.fetchall()]  # Загружаем сохранённые недостатки
    
    for weakness in saved_weaknesses:
        start_idx = "1.0"
        while True:
            start_idx = text_box.search(weakness, start_idx, stopindex=END)
            if not start_idx:
                break
            end_idx = f"{start_idx}+{len(weakness)}c"  # Конец выделения
            text_box.tag_add("highlight", start_idx, end_idx)
            start_idx = end_idx  # Двигаемся дальше по тексту

    # Настроить стиль выделения
    text_box.tag_config("highlight", background="yellow", foreground="black")

def find_RU_patents(patent_text):
    pattern = r"(?:RU|CN|US|DE)\s\d{6,}"
    matches = re.findall(pattern, patent_text)
    return matches

def save_to_second_column(selected_text,patent_number):
    if not selected_text or not patent_number:
        return
    combined_text = f"Патент: {patent_number}\nТекст: {selected_text}"

    # Добавляем результат во второй Listbox
    listbox.insert(END, combined_text)

    # Очищаем синее выделение после сохранения
    text_box.tag_remove("sentence_highlight", "1.0", END)
    

def highlight_sentence(event):
    widget = event.widget
    text = widget.get("1.0", "end-1c")  # Получаем весь текст
    click_index = widget.index(tk.CURRENT)  # Индекс клика в формате "строка.символ"
    
    # Определяем позицию клика
    line, char = map(int, click_index.split("."))

    # Разбиваем текст на предложения
    sentences = list(sentenize(text))
    
    # Определяем абсолютную позицию клика в тексте
    absolute_pos = sum(len(widget.get(f"{i}.0", f"{i}.end")) for i in range(1, line)) + char

    # Находим предложение, в которое попал клик
    start_pos = 0
    selected_sentence = None
    for sent in sentences:
        end_pos = start_pos + len(sent.text)
        if start_pos <= absolute_pos <= end_pos:
            selected_sentence = sent.text
            break
        start_pos = end_pos + 1  # Учитываем пробел

    if selected_sentence:
        # Убираем предыдущее выделение
        widget.tag_remove("sentence_highlight", "1.0", "end")
        
        # Ищем предложение в тексте и выделяем
        match = re.search(re.escape(selected_sentence), text)
        if match:
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            widget.tag_add("sentence_highlight", start_idx, end_idx)
            widget.tag_config("sentence_highlight", background="blue", foreground="white")

def union_patent_and_description(selected_text, patent_number):
    """
    Объединяет выделенный текст с номером патента и сохраняет результат.
    """
    try:
        if not selected_text:
            raise ValueError("Текст не выделен")
        
        if not patent_number:
            raise ValueError("Номер патента не выбран")
        
        # Объединяем номер патента и выделенный текст
        combined_text = f"Патент: {patent_number}\nТекст: {selected_text}"
        
        # Добавляем результат во второй Listbox
        saved_weaknesses_box.insert(END, combined_text)
    except ValueError as e:
        print(f"Ошибка: {e}")

def show_context_menu(event, root, patent_text):
    m = Menu(root, tearoff=0)

    # Проверяем, есть ли выделенный текст
    try:
        selected_text = text_box.get("sentence_highlight.first", "sentence_highlight.last").strip()
    except tk.TclError:
        # Если текст не выделен, показываем сообщение
        m.add_command(label="Текст не выделен")
        m.post(event.x_root, event.y_root)
        return

    # Если текст выделен, продолжаем
    if not patent_text:
        m.add_command(label="Нет определенных патентов")
    else:
        # Добавляем пункты меню для каждого патента
        for patent_t in patent_text:
            # Используем лямбда-функцию с явным присваиванием переменной
            m.add_command(
                label=patent_t,
                command=lambda p=patent_t: save_to_second_column(selected_text, p)
            )
    
    # Отображаем контекстное меню
    m.post(event.x_root, event.y_root)

def show_results():
    global listbox, btn_next, btn_prev, text_box, label_index, patents, current_index, saved_weaknesses_box
    root = Tk()
    # Привязываем контекстное меню к текстовому полю
    root.bind("<ButtonRelease-3>", lambda e: show_context_menu(e, root, find_RU_patents(patents[current_index]) if patents else []))
    root.title("Поиск недостатков в патентах")

    # Настроим сетку
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    # Текстовое поле
    text_box = Text(root, wrap="word", height=40, width=40)
    text_box.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

    text_box.bind("<Button-1>", highlight_sentence)
    # Список
    listbox = Listbox(root, width=40, height=40)
    listbox.grid(row=0, column=2, padx=10, pady=10, sticky="n")

    saved_weaknesses_box = Listbox(root, width=40, height=40)
    saved_weaknesses_box.grid(row=0, column=3, padx=10, pady=10, sticky="n")

    # Кнопки
    btn_prev = Button(root, text="Предыдущий", command=prev_patent)
    btn_prev.grid(row=1, column=0, padx=10, pady=10, sticky="w")

    label_index = Label(root, text="1/{}".format(len(patents)), height=1, width=10)
    label_index.grid(row=1, column=1, padx=10, pady=10)

    btn_next = Button(root, text="Следующий", command=next_patent)
    btn_next.grid(row=1, column=2, padx=10, pady=10, sticky="e")

    # Кнопка сохранения
    def save_to_db():
        selected = listbox.curselection()
        if selected:
            text = listbox.get(selected[0])
            cursor.execute("INSERT INTO weaknesses (text) VALUES (?)", (text,))
            conn.commit()
    
    def load_save_weaknesses():
        cursor.execute("SELECT text from weaknesses")
        saved_weaknesses_box.delete(0, END)
        for row in cursor.fetchall():
            saved_weaknesses_box.insert(END, row[0])

    def save_selected_text():
    # Получаем выбранный элемент из второго Listbox (listbox)
        selected = listbox.curselection()
        if not selected:
            return  # Если ничего не выбрано, выходим

        # Получаем текст выбранного элемента
        selected_text = listbox.get(selected[0])

        # Разделяем текст на номер патента и недостаток
        try:
            # Используем регулярное выражение для извлечения номера патента и текста недостатка
            match = re.match(r"Патент:\s*(.*?)\s*текст:\s*(.*)", selected_text, re.IGNORECASE)
            if not match:
                raise ValueError("Текст не соответствует формату 'Патент: <номер> текст: <недостаток>'")

            patent_number = match.group(1).strip()  # Номер патента
            weakness_text = match.group(2).strip()  # Текст недостатка

            # Проверяем, что номер патента и текст недостатка не пустые
            if not patent_number or not weakness_text:
                raise ValueError("Номер патента или текст недостатка пустые")

        except Exception as e:
            print(f"Ошибка при разборе текста: {e}")
            return

        # Добавляем в третий Listbox (saved_weaknesses_box)
        saved_weaknesses_box.insert(END, selected_text)

        # Сохраняем в базу данных
        try:
            cursor.execute(
                "INSERT INTO weaknesses (text, patent_id) VALUES (?, ?)",
                (weakness_text, patent_number)
            )
            conn.commit()
            print("Данные успешно сохранены в базу данных.")
        except Exception as e:
            print(f"Ошибка при сохранении в базу данных: {e}")
    # def save_selected_text():
    #     selected = listbox.curselection()

    #     if not selected:
    #         return
        
    #     selected_text = listbox.get(selected[0])
    #     try:
    #         patent_part,weakness_part = selected_text.split("")
    #         patent_number = patent_part.replace("Патент: ", "").strip()
    #         weakness_text = weakness_part.replace("Текст: ", "").strip()
    #     except Exception as e:
    #         print(f"Ошибка при разборе текста {e}")
    #         return
        
    #     saved_weaknesses_box.insert(END, selected_text)

    #     try:
    #         cursor.execute(
    #             "INSERT INTO weaknesses (text,patent_id) VALUES (?),(?)",
    #             (weakness_text,patent_number)
    #         )
    #         conn.commit()
    #         print("Данные успешно занесены в базу данных")
    #     except Exception as e:
    #         print(f"Ошибка при сохранении в базу данных: {e}")


    btn_save = Button(root, text="Сохранить", command=save_selected_text)
    btn_save.grid(row=1, column=3, padx=10, pady=10, sticky="e")

    # Загружаем первый патент сразу
    update_text()
    load_save_weaknesses()
    root.mainloop()

if __name__ == "__main__":
    client = clickhouse_connect.get_client(
        host='localhost',
        port=8123,
        username='dev',
        password='dev',
        database='dev'
    )
    def setup_database():
        conn = sqlite3.connect("weaknesses.db")
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS weaknesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            patent_id TEXT NOT NULL
        )
    """)
    
    # Проверяем, существует ли колонка patent_id
        cursor.execute("PRAGMA table_info(weaknesses)")
        columns = [column[1] for column in cursor.fetchall()]  # Получаем список колонок
        
        if "patent_id" not in columns:
            # Добавляем колонку patent_id, если её нет
            cursor.execute("ALTER TABLE weaknesses ADD COLUMN patent_id TEXT NOT NULL DEFAULT ''")
            conn.commit()
        
        return conn

    conn = setup_database()
    cursor = conn.cursor()
    
    # Загружаем ТОЛЬКО 10 патентов (чтобы не зависало)
    query_result = client.query('SELECT description FROM patent_google')
    #print("Результат запроса:", query_result.result_set)

    patents = [row[0] for row in query_result.result_set if row[0] is not None]
    #print("Загруженные патенты:", patents)
    current_index = 0
    weakness_list = []
    
    show_results()