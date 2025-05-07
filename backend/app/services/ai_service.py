# backend/app/services/ai_service.py
from openai import OpenAI
from datetime import datetime
import pandas as pd
import io
import base64

class AIService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate_response(self, prompt: str, table_data=None) -> str:
        try:
            messages = [
                {"role": "system", "content": """Ты — эксперт по созданию рекламных креативов для Telegram Ads. 
Твоя задача — на основе предоставленного примера креатива создать 10 новых, но уникальных и работающих креатива, которые соответствуют:

1. Правилам Telegram Ads:  
   – без намёков на запрещённые тематики  
   – без кликбейта, агрессии и сексизма  
   – текст до 200 символов  
   – не использовать эмодзи в изображении  
   – соблюдать правила шрифта и контраста (если нужно — дать инструкцию для дизайнера)  
   – использовать максимально понятный и лаконичный язык

2. Маркетинговым принципам:  
   – использовать боль + желание + CTA  
   – избегать воды и банальных фраз  
   – цеплять внимание целевой аудитории с первой строки  
   – транслировать конкретную выгоду  
   – использовать язык ЦА (простые фразы, без канцелярита)

Формат вывода:
- Креатив №1: [Текст креатива]  
- Креатив №2: [Текст креатива]  
...  
- Креатив №10: [Текст креатива]  
+ Рекомендация к каждому: какую картинку под это использовать (описать идею)"""}
            ]
            
            # Добавляем таблицу к промпту, если она есть
            if table_data is not None:
                table_content = f"""
Используй данную таблицу для генерации креативов:

{table_data}

Адаптируй креативы под данные из таблицы, используя информацию о целевой аудитории, ключевых преимуществах и стиле коммуникации.
"""
                messages.append({"role": "user", "content": table_content})
            
            # Добавляем основной промпт
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def process_table_file(self, file_data: bytes, ext: str) -> str:
        """Обрабатывает Excel и CSV файлы"""
        import pandas as pd
        import io
        
        try:
            if ext == "csv":
                df = pd.read_csv(io.BytesIO(file_data))
            else:  # xlsx, xls
                df = pd.read_excel(io.BytesIO(file_data))
            
            # Преобразуем в markdown для удобного чтения
            return df.to_markdown(index=False)
        except Exception as e:
            return f"Ошибка обработки таблицы: {e}"

    def improve_creative(self, original: str, edits: str, table_data=None) -> str:
        """Улучшаем один креатив по правкам пользователя"""
        try:
            messages = [
                {"role": "system", "content": "Ты — эксперт по редактированию рекламных текстов для Telegram Ads. Улучши данный креатив с учётом правок пользователя."},
                {"role": "user", "content": f"Оригинал креатива:\n{original}\n\nПравки пользователя:\n{edits}"}
            ]
            # Добавляем таблицу к промпту, если она есть
            if table_data is not None:
                table_content = f"""
Используй данную таблицу для генерации креативов:

{table_data}

Адаптируй креативы под данные из таблицы, используя информацию о целевой аудитории, ключевых преимуществах и стиле коммуникации.
"""
                messages.append({"role": "user", "content": table_content})
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error improving creative: {str(e)}"