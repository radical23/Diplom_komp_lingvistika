import re
import clickhouse_connect
from tkinter import Tk, Text, Button, Listbox, END, Label, Menu
import tkinter as tk
import sqlite3
from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, NewsSyntaxParser, Doc
from razdel import sentenize

"""
Осталось сделать так чтобы по нажатию пкм с выделенным текстом
и нажатию на номер патента производилась привязка(чтобы был номер патента и его недостаток)и отображалась
во 2 столбце вместе а потом оттуда добавлять в бд в колонку 
upd: добавил функцию union и ее вызов но еще не тестил
выводит ошибку смотреть deepseek завтра исправлю
"""



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
    
    text_box.tag_remove("highlight","1.0",END)

    sentences = list(sentenize(full_text))

    for sent in sentences:

        if any(keyword in sent.text.lower() for keyword in keywords):

            start_idx = text_box.search(sent.text,"1.0",stopindex=END)

            if start_idx:

                end_idx = f"{start_idx}+{len(sent.text)}c"

                text_box.tag_add("highlight",start_idx,end_idx)

    text_box.tag_config("highlight",background="red",foreground="black")


# Функция обновления текста и поиска недостатков только для 1 патента
def update_text():
    global weakness_list
    text_box.delete(1.0, END)
    listbox.delete(0, END)  # Очищаем список недостатков
    
    if patents:
        patent_text = patents[current_index]
        
        text_box.insert(END, patent_text)
        find_RU_patents(patent_text)
        label_index.config(text=f"{current_index+1}/{len(patents)}")

        find_weaknesses_in_text(patent_text)

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
    global current_index
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
        widget.tag_remove("highlight", "1.0", "end")
        
        # Ищем предложение в тексте и выделяем
        match = re.search(re.escape(selected_sentence), text)
        if match:
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            widget.tag_add("highlight", start_idx, end_idx)
            widget.tag_config("highlight", background="blue", foreground="white")

def show_results():
    global listbox, btn_next, btn_prev, text_box,label_index, patents, current_index,saved_weaknesses_box
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

    saved_weaknesses_box = Listbox(root, width=40,height=40)
    saved_weaknesses_box.grid(row=0, column=3,padx=10,pady=10, sticky="n")

    # Кнопки
    btn_prev = Button(root, text="Предыдущий", command=prev_patent)
    btn_prev.grid(row=1, column=0, padx=10, pady=10, sticky="w")

    label_index = Label(root, text="1/{}".format(len(patents)),height=1,width=10)
    label_index.grid(row=1,column=1,padx=10,pady=10)

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
        saved_weaknesses_box.delete(0,END)
        for row in cursor.fetchall():
            saved_weaknesses_box.insert(END,row[0])

    def save_selected_text():
        selected_text = text_box.get("sel.first","sel.last")
        if selected_text.strip():
            cursor.execute("INSERT INTO weaknesses (text) VALUES (?)",(selected_text,))
            conn.commit()
            load_save_weaknesses()

    
    btn_save = Button(root, text="Сохранить", command=save_selected_text)
    btn_save.grid(row=1, column=3, padx=10, pady=10, sticky="e")

    # btn_save_references = Button(root, text="Сохранить недостатки и ссылки", command=save_weaknesses_with_references)
    # btn_save_references.grid(row=2, column=3, padx=10, pady=10, sticky="e")
    
    update_text()  # Загружаем первый патент сразу
    load_save_weaknesses()
    root.mainloop()

def show_context_menu(event,root,patent_text):
    m = Menu(root, tearoff = 0)

    selected_text = text_box.get("sel.first", "sel.last").strip()
   
    if not patent_text:
        m.add_command(label="Нет определенных патентов")

    for patent_t in patent_text:
            # Используем лямбда-функцию с явным присваиванием переменной
            m.add_command(
                label=patent_t,
                command=lambda p=patent_t: union_patent_and_description(selected_text, p)
            )
    m.post(event.x_root,event.y_root)


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
# def save_weaknesses_with_references():
#     """Сохраняет найденные недостатки и связанные с ними патенты"""
#     if not patents:
#         return  

#     patent_text = patents[current_index]  # Текущий патент
#     patent_id_list = find_RU_patents(patent_text)  # Ищем ссылки на другие патенты
#     weaknesses = find_weaknesses_with_context(patent_text)  # Ищем недостатки

#     for weakness in weaknesses:
#         for patent_id in patent_id_list:
#             cursor.execute(
#                 "INSERT INTO weaknesses (text, patent_id) VALUES (?, ?)",
#                 (weakness, patent_id)
#             )
    
#     conn.commit()
#     load_save_weaknesses()  # Обновить список сохранённых данных



if __name__=="__main__":
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
        conn.commit()
        return conn


    conn = setup_database()
    cursor = conn.cursor()
    
    # Загружаем ТОЛЬКО 10 патентов (чтобы не зависало)
    query_result = client.query('SELECT description FROM patent_google')
    #query_result = client.query('SELECT description FROM patent_google ORDER BY parsedAt DESC LIMIT 10')
    print("Результат запроса:",query_result.result_set)

    patents = [row[0] for row in query_result.result_set if row[0] is not None]
    #sentences = [list(sentenize(patent)) for patent in patents]

    print("Загруженные патенты:", patents)
    current_index = 0
    weakness_list = []
    
    show_results()
