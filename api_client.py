# api_client.py — Cliente OpenRouter para gpt-4o-mini con visión multimodal
# TODO(security): Implementar rate limiting por sesión para evitar abuso de la key.

import base64
import json
import os
import time
import requests
from typing import Optional

from prompts import build_system_prompt, build_user_message

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-4o-mini"
MAX_TOKENS = 2000
TEMPERATURE = 0.05
TIMEOUT = 90

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


def encode_image_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def build_vision_messages(images: list, target_level: str) -> list:
    num_pages = len(images)
    system_prompt = build_system_prompt(target_level)
    user_content = [
        {"type": "text", "text": build_user_message(num_pages, target_level)}
    ]
    for img in images:
        b64 = encode_image_b64(img["data"])
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{img['mime_type']};base64,{b64}"}
        })
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def evaluate_exam(images: list, target_level: str = "B2", retry: int = 1) -> dict:
    api_key = get_api_key()
    messages = build_vision_messages(images, target_level)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://correccion-writings-eoi.local",
        "X-Title": "Corrección de Writings EOI",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "response_format": {"type": "json_object"},
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
            result = json.loads(content)
            result["_usage"] = {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "estimated_cost_usd": estimate_cost(usage),
            }
            return result
        except requests.exceptions.Timeout:
            last_error = "La API tardó demasiado (timeout 90s). Inténtalo de nuevo."
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "?"
            if status == 401:
                last_error = "API key inválida o sin créditos. Revisa el archivo .env."
            elif status == 429:
                last_error = "Límite de velocidad alcanzado. Espera unos segundos."
                time.sleep(3)
            elif status == 413:
                last_error = "Imágenes demasiado grandes. Reduce el tamaño."
            else:
                last_error = f"Error HTTP {status} de la API."
        except json.JSONDecodeError:
            last_error = "La API devolvió una respuesta no válida. Inténtalo de nuevo."
        except KeyError as e:
            last_error = f"Respuesta inesperada de la API (campo faltante: {e})."
        attempt += 1
        if attempt <= retry:
            time.sleep(2)
    raise ValueError(last_error or "Error desconocido al contactar la API.")


def estimate_cost(usage: dict) -> float:
    input_t = usage.get("prompt_tokens", 0)
    output_t = usage.get("completion_tokens", 0)
    return round((input_t / 1_000_000) * 0.20 + (output_t / 1_000_000) * 0.60, 5)


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
