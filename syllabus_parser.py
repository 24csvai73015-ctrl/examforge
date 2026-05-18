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


def parse_syllabus_structure(
    text: str,
    use_openai: bool,
    openai_key: str = "",
    openai_model: str = "gpt-4o-mini",
    ollama_model: str = "",
) -> list:
    """
    Parse syllabus text and extract topic list using the selected AI backend.
    Returns: [{'topic_name': str, 'description': str}]
    """
    client, model = get_llm_client(use_openai, openai_key, openai_model, ollama_model)

    # Keep prompt short for local model speed
    prompt = (
        "Extract the main topics from this syllabus. "
        "Return ONLY a JSON object: {\"topics\": [{\"topic_name\": \"...\", \"description\": \"...\"}]}. "
        "No markdown, no extra text.\n\n"
        f"Syllabus (first 4000 chars):\n{text[:4000]}"
    )

    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": "You extract syllabus topics. Output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1024,
        temperature=0.2,
    )

    # Try with json response_format; fall back silently for models that don't support it
    try:
        response = client.chat.completions.create(**kwargs, response_format={"type": "json_object"})
    except Exception:
        response = client.chat.completions.create(**kwargs)

    data = _extract_json(response.choices[0].message.content)
    topics = data.get("topics", [])
    if not topics:
        raise ValueError("Model returned empty topics. Try a different model or check the PDF.")
    return topics
