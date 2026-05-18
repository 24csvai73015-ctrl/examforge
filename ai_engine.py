import json
import re
from utils import get_llm_client


def _extract_json(text: str) -> dict:
    """Extract JSON from model output, handling markdown fences gracefully."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        if brace:
            text = brace.group(0)
    return json.loads(text)


def generate_questions(
    question_plan: list,
    difficulty: str,
    use_openai: bool,
    openai_key: str = "",
    openai_model: str = "gpt-4o-mini",
    ollama_model: str = "",
) -> list:
    """
    Generate exam questions from the question plan using the selected AI backend.
    Returns: [{'question_number', 'question_text', 'marks', 'topic_name'}]
    """
    client, model = get_llm_client(use_openai, openai_key, openai_model, ollama_model)

    # Compact plan to reduce tokens
    compact_plan = [
        {"topic": q["topic_name"], "marks": q["marks"]}
        for q in question_plan
    ]

    prompt = (
        f"Generate {len(question_plan)} exam questions. Difficulty: {difficulty}. "
        "Low marks = short question. High marks = detailed question. "
        "Return ONLY JSON: {\"questions\": [{\"question_number\": 1, \"question_text\": \"...\", \"marks\": 5, \"topic_name\": \"...\"}]}. "
        "No markdown, no extra text.\n\n"
        f"Topics and marks:\n{json.dumps(compact_plan)}"
    )

    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": "You are an exam question generator. Output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2048,
        temperature=0.5,
    )

    try:
        response = client.chat.completions.create(**kwargs, response_format={"type": "json_object"})
    except Exception:
        response = client.chat.completions.create(**kwargs)

    data = _extract_json(response.choices[0].message.content)
    questions = data.get("questions", [])
    if not questions:
        raise ValueError("Model returned empty questions. Try reducing the number of questions or use a different model.")
    return questions
