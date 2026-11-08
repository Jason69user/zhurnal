from fastapi import FastAPI
import os
import psycopg2
import redis
from app.parser import parse_text
from pydantic import BaseModel
from app.parser import parse_event

app = FastAPI(title="Журнал API")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://zhurnal:zhurnal_password@db:5432/zhurnal_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

class AddRequest(BaseModel):
    text: str

class EventRequest(BaseModel):
    text: str

@app.get("/")
def root():
    count = redis_client.incr("visits")
    return {"status": "ok", "message": "Журнал работает!", "visits": count}

@app.get("/db-check")
def db_check():
    cached = redis_client.get("db_check_cache")
    if cached:
        return {"status": "ok", "message": "База данных доступна!", "source": "cache"}
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()

        redis_client.set("db_check_cache", "ok", ex=30)

        return {"status": "ok", "message": "База данных доступна!", "source": "database"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/redis-check")
def redis_check():
    try:
        redis_client.ping()
        return {"status": "ok", "message": "Redis доступен!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/add")
def add_entry(request: AddRequest):
    parsed = parse_text(request.text)

    # Если парсер не понял — попробуем как событие
    if parsed["type"] == "unknown":
        from app.parser import parse_event
        event_parsed = parse_event(request.text)
        if event_parsed["title"]:
            parsed = event_parsed

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        if parsed["type"] == "expense":
            cur.execute(
                "INSERT INTO expenses (amount, category, raw_text) VALUES (%s, %s, %s)",
                (parsed["amount"], parsed["category"], parsed["raw_text"])
            )
            conn.commit()
            cur.close()
            conn.close()
            return {"status": "ok", "type": "expense", "parsed": parsed}

        elif parsed["type"] == "note":
            cur.execute(
                "INSERT INTO notes (content, tags, raw_text) VALUES (%s, %s, %s)",
                (parsed["content"], parsed["tags"], parsed["raw_text"])
            )
            conn.commit()
            cur.close()
            conn.close()
            return {"status": "ok", "type": "note", "parsed": parsed}

        elif parsed["type"] == "event":
            cur.execute(
                "INSERT INTO events (title, description, event_date, repeat_type) VALUES (%s, %s, %s, %s)",
                (parsed["title"], parsed["raw_text"], parsed["event_date"], parsed["repeat_type"])
            )
            conn.commit()
            cur.close()
            conn.close()
            return {"status": "ok", "type": "event", "parsed": parsed}

        else:
            cur.close()
            conn.close()
            return {"status": "unknown", "message": "Не удалось распознать запись", "raw_text": request.text}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/expenses")
def get_expenses():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT id, amount, category, raw_text, created_at FROM expenses ORDER BY created_at DESC LIMIT 50")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "id": row[0],
                "amount": float(row[1]),
                "category": row[2],
                "raw_text": row[3],
                "created_at": row[4].isoformat()
            }
            for row in rows
        ]
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/notes")
def get_notes():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT id, content, tags, raw_text, created_at FROM notes ORDER BY created_at DESC LIMIT 50")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "id": row[0],
                "content": row[1],
                "tags": row[2] or [],
                "raw_text": row[3],
                "created_at": row[4].isoformat()
            }
            for row in rows
        ]
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "ok", "message": "Трата удалена"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM notes WHERE id = %s", (note_id,))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "ok", "message": "Заметка удалена"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/events")
def add_event(request: EventRequest):
    parsed = parse_event(request.text)

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO events (title, description, event_date, repeat_type) VALUES (%s, %s, %s, %s)",
            (parsed["title"], parsed["raw_text"], parsed["event_date"], parsed["repeat_type"])
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "ok", "parsed": parsed}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/events")
def get_events():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT id, title, description, event_date, repeat_type FROM events ORDER BY event_date")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "event_date": row[3].isoformat(),
                "repeat_type": row[4]
            }
            for row in rows
        ]
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.delete("/events/{event_id}")
def delete_event(event_id: int):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM events WHERE id = %s", (event_id,))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "ok", "message": "Событие удалено"}
    except Exception as e:
        return {"status": "error", "message": str(e)}