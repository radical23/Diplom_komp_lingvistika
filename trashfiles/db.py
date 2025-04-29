import sqlite3
import clickhouse_connect
from tkinter import Tk, Text, Button, Listbox, END, messagebox
from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, NewsSyntaxParser, Doc

# Настройка базы данных SQLite
def setup_database():
    conn = sqlite3.connect("weaknesses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weaknesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

# Функция для поиска недостатков
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
            context = paragraphs[i - 1] if i > 0 else None
            results.append((context, paragraph))

    return results

# Обработка выбора текста
def on_select(event):
    selection = text_widget.get("sel.first", "sel.last")
    if selection:
        cursor.execute("INSERT INTO weaknesses (text) VALUES (?)", (selection,))
        conn.commit()
        update_listbox()

# Обновление списка в правом меню
def update_listbox():
    listbox.delete(0, END)
    cursor.execute("SELECT id, text FROM weaknesses")
    for row in cursor.fetchall():
        listbox.insert(END, f"{row[0]}. {row[1]}")  # Добавляем ID и текст


def delete_selected():
    try:
        selected_item = listbox.curselection()
        if not selected_item:
            messagebox.showwarning("Ошибка", "Выберите запись для удаления")
            return

        item_text = listbox.get(selected_item)
        item_id = int(item_text.split(".")[0])  # Получаем ID перед точкой

        cursor.execute("DELETE FROM weaknesses WHERE id = ?", (item_id,))
        conn.commit()

        update_listbox()  # Обновить список
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось удалить запись: {e}")


# Основной интерфейс
def show_results(results):
    def display_paragraph(context, paragraph):
        text_widget.insert(END, f"Причина: {context}\n" if context else "")
        text_widget.insert(END, f"Недостаток: {paragraph}\n\n")
        text_widget.insert(END, "-" * 50 + "\n\n")

    root = Tk()
    root.title("Анализ недостатков патентов")

    global text_widget, listbox, conn, cursor
    text_widget = Text(root, wrap="word", height=20, width=80)
    text_widget.pack(side="left", fill="both", expand=True)

    listbox = Listbox(root, width=40)
    listbox.pack(side="right", fill="y")

    Button(root, text="Добавить выделенное в базу", command=lambda: on_select(None)).pack(side="bottom")
    text_widget.bind("<Double-1>", on_select)

    Button(root, text="Удалить выделенное из бд", command=delete_selected).pack(side="bottom")


    for context, paragraph in results:
        display_paragraph(context, paragraph)

    update_listbox()
    root.mainloop()

if __name__ == '__main__':

    client = clickhouse_connect.get_client(
    host='localhost',
    port=8123,
    username='dev',  # или ваш пользователь
    password='dev',   # укажите пароль
    database='dev'      # имя базы данных
)

    # Настройка базы данных
    conn = setup_database()
    cursor = conn.cursor()

    # Ввод текста для примера
    example_text = """
    Изобретение относится к области машиностроения. Основной недостаток заключается в низкой надежности конструкции.
    Причиной этого является использование материалов низкого качества.
    Другое преимущество конструкции — ее легкость.
    """

    results = find_weaknesses_with_context(example_text)
    if results:
        show_results(results)
    else:
        print("Недостатки не найдены.")
