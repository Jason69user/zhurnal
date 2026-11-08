import re

# Ключевые слова для определения типа записи
EXPENSE_KEYWORDS = ["потратил", "купил", "заплатил", "оплатил", "потрачено"]
NOTE_KEYWORDS = ["идея", "заметка", "запомни", "мысль", "todo"]
EVENT_KEYWORDS = ["завтра", "сегодня", "послезавтра", "встреча", "напомни", "событие"]

# Категория для повтора
REPEAT_KEYWORDS = {
    "каждый день": "daily",
    "каждую неделю": "weekly",
    "каждый месяц": "monthly",
}

# Категории трат (можно расширять)
CATEGORIES = {
    "еда": ["еда", "еду", "продукты", "обед", "ужин", "завтрак", "кофе", "кафе", "ресторан"],
    "транспорт": ["такси", "метро", "автобус", "бензин", "транспорт"],
    "жильё": ["квартира", "аренда", "коммуналка", "жкх"],
    "развлечения": ["кино", "игры", "подписка", "развлечения"],
    "здоровье": ["аптека", "врач", "лекарства", "здоровье"],
    "одежда": ["одежда", "обувь", "куртка", "джинсы"],
}

def parse_text(text: str) -> dict:
    """
    Принимает текст, возвращает словарь с типом и данными.
    """
    text_lower = text.lower().strip()

    # Проверяем на трату
    if any(word in text_lower for word in EXPENSE_KEYWORDS):
        return parse_expense(text)

    # Проверяем на заметку
    if any(word in text_lower for word in NOTE_KEYWORDS):
        return parse_note(text)

    # Если не поняли — сохраняем как "неразобранное"
    return {"type": "unknown", "raw_text": text}


def parse_expense(text: str) -> dict:
    """
    Вытаскивает сумму и категорию из текста.
    """
    # Ищем число (сумму)
    amount_match = re.search(r'\d+', text)
    amount = float(amount_match.group()) if amount_match else 0.0

    # Определяем категорию
    text_lower = text.lower()
    category = "прочее"
    for cat, keywords in CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            category = cat
            break

    return {
        "type": "expense",
        "amount": amount,
        "category": category,
        "raw_text": text
    }


def parse_note(text: str) -> dict:
    """
    Обрабатывает заметку: убирает ключевое слово, вытаскивает теги.
    """
    # Убираем ключевое слово из начала
    content = text
    for kw in NOTE_KEYWORDS:
        content = re.sub(rf'^{kw}[:\s]*', '', content, flags=re.IGNORECASE)

    # Ищем теги в формате #тег
    tags = re.findall(r'#(\w+)', text)

    return {
        "type": "note",
        "content": content.strip(),
        "tags": tags,
        "raw_text": text
    }

def parse_event(text: str) -> dict:
    """
    Парсит событие: «завтра в 14:00 к зубному».
    """
    text_lower = text.lower().strip()

    # Определяем дату
    from datetime import datetime, timedelta
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if "послезавтра" in text_lower:
        event_date = today + timedelta(days=2)
    elif "завтра" in text_lower:
        event_date = today + timedelta(days=1)
    elif "сегодня" in text_lower:
        event_date = today
    else:
        event_date = today

    # Ищем время (формат «в 14:00» или «в 2»)
    time_match = re.search(r'в\s+(\d{1,2})(?::(\d{2}))?', text_lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        event_date = event_date.replace(hour=hour, minute=minute)

    # Определяем тип повтора
    repeat_type = "none"
    for keyword, value in REPEAT_KEYWORDS.items():
        if keyword in text_lower:
            repeat_type = value
            break

    # Убираем ключевые слова из title
    title = text
    for word in ["завтра", "сегодня", "послезавтра", "встреча", "напомни", "событие"]:
        title = re.sub(rf'\b{word}\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'в\s+\d{1,2}(?::\d{2})?', '', title).strip()

    return {
        "type": "event",
        "title": title or "Событие",
        "event_date": event_date,
        "repeat_type": repeat_type,
        "raw_text": text
    }