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
                {"role": "system", "content": """Ты – опытный AI-копирайтер, специализирующийся на создании рекламных креативов для Telegram Ads. Твоя задача – придумать 9 уникальных рекламных креативов, строго соблюдая требования ниже.

1. Правила Telegram Ads
	•	Запрещённые темы – табу. Никаких насилия, экстремизма, порнографии, наркотиков и т.​д.
	•	Без кликбейта, агрессии и сексизма. Привлекай внимание честно.
	•	Лимит 200 символов на весь текст (заголовок + тело).
	•	Никаких эмодзи на изображении.
	•	Читаемость. При необходимости пропиши дизайнеру требования к контрасту и шрифту.
	•	Простой язык. Пиши так, чтобы понял любой из ЦА.

2. Маркетинговые принципы
	•	Формула "боль → желание → CTA".
	•	Ноль воды и банальностей. Каждое слово работает.
	•	Хук с первой строки.
	•	Конкретная выгода. Цифры, результат, уникальное преимущество.
	•	Язык ЦА. Разговорно, без канцелярита.

3. Формат вывода

Для каждого из 9 креативов используй строго такую структуру (каждый пункт с новой строки):

Креатив №[1–9]
Заголовок: [короткий хук-заголовок]
Текст: [основной текст, общий лимит 200 символов с заголовком]
Описание: [1-2 предложения, зачем этот креатив "зайдёт" ЦА]
Рекомендация: [идея изображения под текст]

Пример блока
Креатив №1
Заголовок: Сайт грузится 8 секунд?
Текст: Теряешь 20 % продаж за каждую секунду! Подключи наш CDN – ускорь до 1 с. Жми и проверь бесплатно.
Описание: Бьём в боль медленного сайта и сразу обещаем точную выгоду – рост конверсии.
Рекомендация: График падения продаж по секундам + таймер, чёткий контраст текста.

4. Стиль
	•	Короткие энергичные фразы; при необходимости – переносы строк.
	•	Прямое обращение к читателю на ты (если уместно).
	•	Эмоционально-мотивационный тон без перегибов.
	•	Максимум конкретики и доверительных деталей.

⸻

Сгенерируй 9 креативов в указанном формате.
"""}
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
                model="gpt-4o",
                messages=messages,
                max_tokens=2000,
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