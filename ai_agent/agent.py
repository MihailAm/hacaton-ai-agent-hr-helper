import json
from openai import OpenAI
from ai_agent_config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from . import tools as T
from .prompts import SYSTEM_PROMPT


client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)


# --------------------------
# 1. Tools (function definitions)
# --------------------------
TOOLS = [
    {
        "type": "function",
        "name": "parse_resume",
        "description": "Анализирует текст резюме и возвращает структурированные данные.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            },
            "required": ["text"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "match_vacancy",
        "description": "Находит подходящую вакансию на основе структурированных данных резюме.",
        "parameters": {
            "type": "object",
            "properties": {
                "parsed_resume": {"type": "object"}
            },
            "required": ["parsed_resume"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "add_to_candidate_pool",
        "description": "Добавляет кандидата в JSON-пул.",
        "parameters": {
            "type": "object",
            "properties": {
                "candidate": {"type": "object"}
            },
            "required": ["candidate"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "compare_with_candidate_pool",
        "description": "Сравнивает кандидата с другими кандидатами в пуле.",
        "parameters": {
            "type": "object",
            "properties": {
                "candidate": {"type": "object"}
            },
            "required": ["candidate"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "sort_candidate_pool",
        "description": "Сортирует пул по заданному критерию.",
        "parameters": {
            "type": "object",
            "properties": {
                "criteria": {"type": "string"}
            },
            "required": ["criteria"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "get_best_candidate",
        "description": "Возвращает лучшего кандидата.",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "reply_to_candidate",
        "description": "Финальное решение кандидату",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "status": {"type": "string"}
            },
            "required": ["message", "status"],
            "additionalProperties": False
        },
        "strict": True
    }
]


# --------------------------
# 2. Tool name → Python function
# --------------------------
PY_TOOLS = {
    "parse_resume": T.parse_resume,
    "match_vacancy": T.match_vacancy,
    "add_to_candidate_pool": T.add_to_candidate_pool,
    "compare_with_candidate_pool": T.compare_with_candidate_pool,
    "sort_candidate_pool": T.sort_candidate_pool,
    "get_best_candidate": T.get_best_candidate,
    "reply_to_candidate": T.reply_to_candidate
}


# --------------------------
# 3. Agent loop under Responses API
# --------------------------
def agent_loop(user_id: str, text: str) -> str:
    """
    Полный многошаговый агент.
    Работает по циклу:
    THOUGHT → ACTION (tool) → OBSERVATION → THOUGHT → ...
    """

    # История сообщений (новый API)
    history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Кандидат {user_id} прислал резюме:\n{text}"}
    ]

    while True:
        # ------------------------------
        # 1. Получаем ответ модели
        # ------------------------------
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=history,
            tools=TOOLS,
        )

        print(f"Ответ модели: {response.output}")
        # Добавляем reasoning и прочее в историю
        history += response.output

        tool_calls = [item for item in response.output if item.type == "function_call"]

        # Если модель НЕ вызывает tool → финальный ответ
        if not tool_calls:
            final_text = response.output_text
            return final_text

        # ------------------------------
        # 2. Обрабатываем tool calls
        # ------------------------------
        for call in tool_calls:
            name = call.name
            print(f"Вызвана функция {name}")
            args = json.loads(call.arguments)
            call_id = call.call_id

            # Выполняем Python-функцию
            py_result = PY_TOOLS[name](**args)

            print(f"Результат функции {name}: {py_result}")
            # Передаем результат модели
            history.append({
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(py_result, ensure_ascii=False)
            })

            # Если reply_to_candidate вызван → это конец
            if name == "reply_to_candidate":
                return py_result["message"]

        # После tool_call модель должна продолжить диалог
        # Цикл повторяется
