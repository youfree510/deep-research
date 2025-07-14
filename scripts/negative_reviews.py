import json
import os

try:
    import google.generativeai as genai
except Exception as e:
    genai = None

def create_ideal_prompt(company_name: str) -> str:
    return f"""
Задача: Ты — автоматизированный ИИ-аналитик. Твоя цель — найти в интернете реальные негативные отзывы о компании или теме, указанной ниже. Работай автономно, пока не соберешь необходимое количество отзывов или не убедишься, что их больше нет.

Тема для поиска: {company_name}

Требования к выполнению:
1.  **Количество**: Собери от 20 до 50 негативных отзывов. Если найдешь меньше 20, собери все, что есть. Если не найдешь ни одного, верни пустой список.
2.  **Аутентичность**: Используй ТОЛЬКО реальные отзывы с публичных сайтов (форумы, отзовики, блоги). НЕ придумывай текст, не пересказывай и не изменяй его. Сохраняй орфографию и пунктуацию оригинала.
3.  **Критерий негатива**: Негативным считается отзыв, где автор явно выражает недовольство, описывает проблемы, финансовые потери, плохое качество услуг или обман. Игнорируй отзывы с нейтральной или позитивной окраской.
4.  **Избегай рекламы**: Не бери информацию с самого сайта компании, из рекламных статей или пресс-релизов.

Правила форматирования результата:
1.  **Формат**: Верни ОДИН ответ в формате JSON. Никакого другого текста, объяснений или приветствий в ответе быть не должно.
2.  **Структура JSON**:
    {{
    "reviews": [
    {{
    "name": "Имя или ник автора",
    "review": "Полный оригинальный текст отзыва",
    "city": "Город (если указан)",
    "date": "Дата отзыва (в оригинальном формате)"
    }}
    ],
    "total_count": 0,
    "search_topic": "{company_name}"
    }}
3.  **Пустые поля**: Если на сайте отсутствует имя автора, город или дата, оставь соответствующее поле в JSON как пустую строку "". Поле `review` должно быть всегда заполнено.
"""

def find_negative_reviews_autonomously(company_name: str, model) -> dict:
    print(f"\U0001f916 Запускаю автономный поиск отзывов для '{company_name}'...")
    prompt = create_ideal_prompt(company_name)
    safety_settings = {
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
    }
    response = model.generate_content(
        prompt,
        tools=['Google Search'],
        safety_settings=safety_settings,
    )
    print("✅ Поиск завершен. Обрабатываю результат...")
    try:
        cleaned_text = response.text.strip().replace('```json', '').replace('```', '')
        data = json.loads(cleaned_text)
        return data
    except (json.JSONDecodeError, AttributeError):
        print("❌ Ошибка: Модель вернула невалидный JSON.")
        print("Ответ модели:", getattr(response, 'text', ''))
        return {"error": "Failed to parse JSON from model.", "raw_response": getattr(response, 'text', '')}

def main() -> None:
    if genai is None:
        raise SystemExit("google.generativeai is not installed")
    company = input("Введите название компании для поиска отзывов: ").strip()
    if not company:
        raise SystemExit("Не указано название компании")
    model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest')
    results = find_negative_reviews_autonomously(company, model)
    print("\n--- РЕЗУЛЬТАТ ПОИСКА ---")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    file_name = f"reviews_{company.replace(' ', '_').lower()}.json"
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"\n👍 Результат сохранен в файл: {file_name}")

if __name__ == '__main__':
    main()
