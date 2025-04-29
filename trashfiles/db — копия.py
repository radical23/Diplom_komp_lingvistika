import re
import tkinter as tk
from razdel import sentenize

def highlight_sentence(event):
    widget = event.widget
    text = widget.get("1.0", "end-1c")  # Получаем весь текст
    click_index = widget.index(tk.CURRENT)  # Индекс клика в формате "строка.символ"
    
    # Определяем позицию клика
    line, char = map(int, click_index.split("."))

    # Разбиваем текст на предложения
    sentences = list(sentenize(text))
    
    # Определяем абсолютную позицию клика в тексте
    absolute_pos = sum(len(line) + 1 for line in text.split("\n")[:line - 1]) + char  # +1 за счет \n

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
            widget.tag_config("highlight", background="blue")

# Создаем окно
root = tk.Tk()
root.title("Выделение предложения по двойному клику")

text_box = tk.Text(root, wrap="word", height=10, width=50)
text_box.pack(padx=10, pady=10)
text_box.insert("1.0", "Это первое предложение. Это второе предложение! А вот и третье?")

text_box.bind("<Double-Button-1>", highlight_sentence)  # Привязываем обработчик события

root.mainloop()
