import json
from pathlib import Path
from uuid import uuid4
from openai import OpenAI
from ai_agent_config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, MIN_CANDIDATES


POOL = Path("candidate_pool.json")
VAC = Path("vacancies.json")

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


# ------------------------------
# Вспомогательные
# ------------------------------

def load_pool():
    try:
        return json.loads(POOL.read_text("utf-8"))
    except:
        return []

def save_pool(pool):
    POOL.write_text(json.dumps(pool, ensure_ascii=False, indent=2), "utf-8")

def load_vacancies():
    return json.loads(VAC.read_text("utf-8"))


# ------------------------------
# LLM helper
# ------------------------------

def call_llm(prompt: str):
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    content = resp.choices[0].message.content
    try:
        return json.loads(content)
    except:
        return {"error": "LLM returned non-json", "raw": content}


# ------------------------------
# Tools — полностью LLM-основанные
# ------------------------------

def parse_resume(text: str):
    prompt = f"""
    Проанализируй текст резюме:

    {text}

    Верни JSON:
    {{
      "skills": [...],
      "experience_years": число,
      "quality": число от 1 до 10,
      "summary": "краткое описание"
    }}
    """
    return call_llm(prompt)


def match_vacancy(parsed_resume: dict):
    vacancies = load_vacancies()
    prompt = f"""
    У тебя есть резюме:

    {json.dumps(parsed_resume, ensure_ascii=False)}

    И вакансии:

    {json.dumps(vacancies, ensure_ascii=False)}

    Определи лучшую вакансию, на которую подходит данное резюме (и подходит ли вообще).
    Верни JSON:
    {{
      "matched": true/false,
      "vacancy_id": int или null,
      "vacancy_title": строка или null,
      "confidence": число 0-100,
      "explanation": "краткое объяснение"
    }}
    """
    return call_llm(prompt)


def add_to_candidate_pool(candidate: dict):
    pool = load_pool()
    candidate["id"] = str(uuid4())
    pool.append(candidate)
    save_pool(pool)
    return {"status": "added", "pool_size": len(pool)}


def compare_with_candidate_pool(candidate: dict):
    pool = load_pool()
    prompt = f"""
    В пуле есть кандидаты:

    {json.dumps(pool, ensure_ascii=False)}

    Новый кандидат:
    {json.dumps(candidate, ensure_ascii=False)}

    Оцени кандидата среди других. Верни JSON:
    {{
      "better_than_average": true/false,
      "rank_estimate": число от 1 до N,
      "explanation": "..."
    }}
    """
    return call_llm(prompt)


def sort_candidate_pool(criteria):
    pool = load_pool()

    prompt = f"""
    Отсортируй кандидатов по критерию "{criteria}".

    Кандидаты:
    {json.dumps(pool, ensure_ascii=False)}

    Верни JSON:
    {{
      "sorted": [...кандидаты...]
    }}
    """
    result = call_llm(prompt)

    if "sorted" in result:
        save_pool(result["sorted"])
        return {"status": "sorted", "criteria": criteria}

    return {"error": "LLM sorting failed", "raw": result}


def get_best_candidate():
    pool = load_pool()

    if len(pool) < MIN_CANDIDATES:
        return {
            "enough": False,
            "message": f"Нужно минимум {MIN_CANDIDATES} резюме"
        }

    prompt = f"""
    Выбери лучшего кандидата из пула:

    {json.dumps(pool, ensure_ascii=False)}

    Верни JSON:
    {{
      "best_candidate": {{...}}
    }}
    """
    return call_llm(prompt)


def reply_to_candidate(message: str, status: str):
    return {"type": status, "message": message}
