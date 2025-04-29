import re

text = "Пример текста с № 123456, RU 123456, 15567 и (CN123456)."
pattern = r"(?i)\b(?:RU|CN|US|DE|РФ|SK|EP|JP|SU|WO)\s*\d{5,}\b|(?:№|#|N)\s*\d{5,}\b"
matches = re.findall(pattern, text)
print(matches)  # Вывод: ['№ 123456', 'RU123456', 'CN123456']