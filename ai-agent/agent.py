import json
from typing import Dict, Any, List
from openai import OpenAI
from ai_agent_config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from .prompts import SYSTEM_PROMPT
from . import tools as T


client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

TOOLS = {
    "parse_resume": T.parse_resume,
    "match_vacancy": T.match_vacancy,
    "add_to_candidate_pool": T.add_to_candidate_pool,
    "compare_with_candidate_pool": T.compare_with_candidate_pool,
    "sort_candidate_pool": T.sort_candidate_pool,
    "get_best_candidate": T.get_best_candidate,
    "reply_to_candidate": T.reply_to_candidate
}

FUNCTIONS = [
    {
        "name": "parse_resume",
        "description": "Проанализировать текст резюме",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "match_vacancy",
        "description": "Сравнить parsed_resume с вакансиями",
        "parameters": {
            "type": "object",
            "properties": {
                "parsed_resume": {"type": "object"}
            },
            "required": ["parsed_resume"]
        }
    },
    {
        "name": "add_to_candidate_pool",
        "description": "Добавить кандидата в JSON-пул",
        "parameters": {
            "type": "object",
            "properties": {
                "candidate": {"type": "object"}
            },
            "required": ["candidate"]
        }
    },
    {
        "name": "compare_with_candidate_pool",
        "description": "Сравнить кандидата с пулом",
        "parameters": {
            "type": "object",
            "properties": {
                "candidate": {"type": "object"}
            },
            "required": ["candidate"]
        }
    },
    {
        "name": "sort_candidate_pool",
        "description": "Отсортировать пул",
        "parameters": {
            "type": "object",
            "properties": {
                "criteria": {"type": "string"}
            }
        }
    },
    {
        "name": "get_best_candidate",
        "description": "Вернуть лучшего кандидата",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "reply_to_candidate",
        "description": "Ответ кандидату",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "status": {"type": "string"}
            },
            "required": ["message", "status"]
        }
    }
]


def agent_loop(user_id: str, text: str) -> Dict[str, Any]:
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Кандидат {user_id} прислал резюме:\n{text}\n"}
    ]

    while True:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            functions=FUNCTIONS,
            function_call="auto",
            temperature=0.2
        )
        msg = resp.choices[0].message

        if not msg.function_call:
            return {"type": "reply", "message": msg.content}

        func = msg.function_call.name
        args = json.loads(msg.function_call.arguments or "{}")

        result = TOOLS[func](**args)

        if func == "reply_to_candidate":
            return result

        messages.append({
            "role": "assistant",
            "content": f"RESULT_{func}: {json.dumps(result, ensure_ascii=False)}"
        })
