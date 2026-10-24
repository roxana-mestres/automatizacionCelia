# api_client.py — Cliente OpenRouter con visión multimodal (modelo configurable en .env)
# TODO(security): Implementar rate limiting por sesión para evitar abuso de la key.

import base64
import io
import json
import re
import os
import time
import requests
import streamlit as st
from typing import Optional

from PIL import Image, ImageOps

from prompts import build_system_prompt, build_user_message

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
# Claude Sonnet da la corrección más fina. OpenRouter prueba los modelos en orden
# si el primero no existe o falla; se puede cambiar con OPENROUTER_MODELS en .env.
MODELS = [m.strip() for m in os.environ.get(
    "OPENROUTER_MODELS",
    "anthropic/claude-sonnet-5.5,google/gemini-3.8-flash,openai/gpt-5.4-mini",
).split(",") if m.strip()][:3]
MAX_TOKENS = 8000
TEMPERATURE = 0.1
TIMEOUT = 180

IMAGE_SIGNATURES = {
    "jpeg": b"\xff\xd8\xff",
    "png": b"\x89PNG",
}


def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise EnvironmentError("OPENROUTER_API_KEY not set. Add it to the .env file.")
    return key


def validate_image_bytes(data: bytes, filename: str) -> tuple:
    if len(data) < 4:
        return False, "", "File too small to be a valid image."
    if data[:3] == IMAGE_SIGNATURES["jpeg"]:
        return True, "image/jpeg", ""
    elif data[:4] == IMAGE_SIGNATURES["png"]:
        return True, "image/png", ""
    else:
        return False, "", f"'{filename}' no es un JPEG o PNG válido (magic bytes incorrectos)."


MAX_IMAGE_SIDE = 2000  # px; suficiente para leer letra manuscrita


def prepare_image(data: bytes) -> bytes:
    """Endereza fotos de móvil (EXIF) y las reduce a JPEG ligero para la API (límite 5 MB)."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85, optimize=True)
    return out.getvalue()


def encode_image_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def build_vision_messages(images: list, target_level: str, task_prompt: str = "") -> list:
    num_pages = len(images)
    system_prompt = build_system_prompt(target_level)
    user_content = [
        {"type": "text", "text": build_user_message(num_pages, target_level, task_prompt)}
    ]
    for img in images:
        b64 = encode_image_b64(img["data"])
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{img['mime_type']};base64,{b64}", "detail": "high"}
        })
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def evaluate_exam(images: list, target_level: str = "B2", task_prompt: str = "", retry: int = 1) -> dict:
    api_key = get_api_key()
    messages = build_vision_messages(images, target_level, task_prompt)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://timshelstudio.cl",
        "X-Title": "Corrección de Writings EOI",
    }
    payload = {
        "models": MODELS,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "response_format": {"type": "json_object"},
        "usage": {"include": True},
    }

    attempt = 0
    last_error = None
    while attempt <= retry:
        try:
            response = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            result = normalize_result(parse_json(content))
            result["_usage"] = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "estimated_cost_usd": usage.get("cost") or 0.0,
                "model": data.get("model", MODELS[0]),
            }
            return result
        except requests.exceptions.Timeout:
            last_error = f"La API tardó demasiado (timeout {TIMEOUT}s). Inténtalo de nuevo."
        except requests.exceptions.HTTPError as e:
            # Response es falsy en errores HTTP, por eso se compara con None
            status = e.response.status_code if e.response is not None else "?"
            if status == 401:
                last_error = "API key inválida. Revisa el archivo .env."
            elif status == 402:
                last_error = "Sin créditos en OpenRouter. Recarga saldo o sube el límite de la key."
                break
            elif status == 429:
                last_error = "Límite de velocidad alcanzado. Espera unos segundos."
                time.sleep(3)
            elif status == 413:
                last_error = "Imágenes demasiado grandes. Reduce el tamaño."
            else:
                last_error = f"Error HTTP {status} de la API."
        except (json.JSONDecodeError, TypeError):
            last_error = "La API devolvió una respuesta no válida. Inténtalo de nuevo."
        except KeyError as e:
            last_error = f"Respuesta inesperada de la API (campo faltante: {e})."
        attempt += 1
        if attempt <= retry:
            time.sleep(2)
    raise ValueError(last_error or "Error desconocido al contactar la API.")


CRITERIA = ("comunicativa", "coherencia", "correccion", "alcance")


def normalize_result(result: dict) -> dict:
    """Garantiza que las 4 notas existan y sean enteros 0-3 aunque el modelo se desvíe."""
    if not isinstance(result, dict):
        raise json.JSONDecodeError("not an object", "", 0)
    scores = result.get("scores")
    if not isinstance(scores, dict):
        scores = {}
    for key in CRITERIA:
        entry = scores.get(key)
        if not isinstance(entry, dict):
            entry = {}
        try:
            score = int(round(float(entry.get("score", 0))))
        except (TypeError, ValueError):
            score = 0
        entry["score"] = max(0, min(3, score))
        entry.setdefault("justification", "")
        scores[key] = entry
    result["scores"] = scores
    # Recuento real a partir de la transcripción, sin marcadores [ILEGIBLE], [¿x?]...
    transcription = result.get("transcription") if isinstance(result.get("transcription"), str) else ""
    words = [w for w in re.sub(r"\[[^\]]*\]", " ", transcription).split() if re.search(r"[A-Za-z]", w)]
    result["word_count_estimate"] = len(words)
    if not isinstance(result.get("vision_log"), list):
        result["vision_log"] = []
    result["vision_log"] = [e for e in result["vision_log"] if isinstance(e, dict)]
    for field in ("transcription", "examiner_commentary", "student_feedback"):
        if not isinstance(result.get(field), str):
            result[field] = ""
    return result


def parse_json(content: str) -> dict:
    """Acepta JSON puro o envuelto en ```json ... ``` por si el modelo lo añade."""
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise json.JSONDecodeError("no JSON object", text, 0)
    return json.loads(text[start:end + 1])


@st.cache_data(ttl=300, show_spinner=False)
def get_balance() -> Optional[dict]:
    try:
        api_key = get_api_key()
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.get(f"{OPENROUTER_BASE}/auth/key", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json().get("data", {})
            return {
                "usage": data.get("usage", 0),
                "limit": data.get("limit"),
                "limit_remaining": data.get("limit_remaining"),
                "is_free_tier": data.get("is_free_tier", False),
                "label": data.get("label", "API Key"),
            }
    except Exception:
        pass
    return None
