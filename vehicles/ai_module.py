"""
AI module: calls OpenRouter / Claude Vision and returns
(1) a human-readable text report and
(2) a structured metrics JSON used by the 3D visualisations on the result page.

The model is instructed to output a single JSON code block followed by free-text
narrative. We extract the JSON block ourselves so the visualisations stay reliable.
"""
import base64
import json
import re
import requests
from django.conf import settings


SIMPLE_INSTRUCTIONS = {
    "ru": """Ты система диагностики транспортных средств.

Пользователь сообщил, что на изображении: {vehicle}

Внимательно осмотри изображение и выдай ответ в ДВУХ частях:

ЧАСТЬ 1 — JSON блок (обязательно). Сначала выведи ОДИН JSON-блок в тройных бэктиках с такими полями (число от 0 до 100):
```json
{{
  "confidence": 85,
  "overall": 80,
  "body": 80,
  "paint": 75,
  "tires": 90,
  "lights": 95,
  "windows": 100,
  "frame": 85,
  "vehicle_detected": true,
  "vehicle_type": "седан",
  "color_detected": "белый",
  "severity": "minor",
  "damage_areas": ["передний_бампер", "правое_крыло"]
}}
```
severity: одно из none, minor, moderate, severe.
damage_areas: список из этих кодов (можно несколько): front_bumper, rear_bumper, hood, roof, left_door, right_door, left_fender, right_fender, left_mirror, right_mirror, windshield, rear_window, headlights, taillights, wheels, undercarriage. Пустой массив если повреждений нет.

ЧАСТЬ 2 — Текстовый отчёт после JSON блока. На русском, 4-5 предложений: что за транспорт, есть ли повреждения, общее состояние.""",

    "uz": """Siz transport vositalarini diagnostika qilish tizimisiz.

Foydalanuvchi rasmda quyidagi transport borligini ko'rsatdi: {vehicle}

Rasmni diqqat bilan tahlil qiling va javobni IKKI qismda bering:

QISM 1 — JSON blok (majburiy). Birinchi navbatda uchta backtick ichida BITTA JSON blok chiqaring (qiymatlar 0 dan 100 gacha):
```json
{{
  "confidence": 85,
  "overall": 80,
  "body": 80,
  "paint": 75,
  "tires": 90,
  "lights": 95,
  "windows": 100,
  "frame": 85,
  "vehicle_detected": true,
  "vehicle_type": "sedan",
  "color_detected": "oq",
  "severity": "minor",
  "damage_areas": ["front_bumper"]
}}
```
severity: none, minor, moderate, severe dan biri.
damage_areas: ushbu kodlardan ro'yxat: front_bumper, rear_bumper, hood, roof, left_door, right_door, left_fender, right_fender, left_mirror, right_mirror, windshield, rear_window, headlights, taillights, wheels, undercarriage. Shikastlar bo'lmasa, bo'sh ro'yxat.

QISM 2 — JSON dan keyin matn hisoboti. O'zbek tilida 4-5 gap: qanday transport, shikastlar, umumiy holat.""",

    "en": """You are a vehicle diagnostics system.

The user reported the vehicle as: {vehicle}

Carefully examine the image and produce a response in TWO parts:

PART 1 — JSON block (required). First output a SINGLE JSON block inside triple backticks with these fields (numbers are 0-100):
```json
{{
  "confidence": 85,
  "overall": 80,
  "body": 80,
  "paint": 75,
  "tires": 90,
  "lights": 95,
  "windows": 100,
  "frame": 85,
  "vehicle_detected": true,
  "vehicle_type": "sedan",
  "color_detected": "white",
  "severity": "minor",
  "damage_areas": ["front_bumper"]
}}
```
severity is one of: none, minor, moderate, severe.
damage_areas is a list from these codes: front_bumper, rear_bumper, hood, roof, left_door, right_door, left_fender, right_fender, left_mirror, right_mirror, windshield, rear_window, headlights, taillights, wheels, undercarriage. Empty list if no damage.

PART 2 — Text report after the JSON block. In English, 4-5 sentences covering what the vehicle is, any damages, and overall condition.""",
}


DETAILED_INSTRUCTIONS = {
    "ru": """Ты экспертная система диагностики транспортных средств.

Пользователь сообщил детальные данные транспорта:
{vehicle_details}

Внимательно изучи изображение в контексте этих данных и выдай ответ в ДВУХ частях:

ЧАСТЬ 1 — JSON блок (обязательно). Сначала выведи ОДИН JSON-блок в тройных бэктиках с такими полями (число от 0 до 100):
```json
{{
  "confidence": 88,
  "overall": 82,
  "body": 80,
  "paint": 78,
  "tires": 90,
  "lights": 95,
  "windows": 100,
  "frame": 85,
  "interior": 75,
  "engine_estimate": 80,
  "vehicle_detected": true,
  "vehicle_type": "седан",
  "color_detected": "белый",
  "severity": "minor",
  "damage_areas": ["передний_бампер"],
  "estimated_age_score": 70,
  "maintenance_score": 75
}}
```
severity: одно из none, minor, moderate, severe.
damage_areas: коды из: front_bumper, rear_bumper, hood, roof, left_door, right_door, left_fender, right_fender, left_mirror, right_mirror, windshield, rear_window, headlights, taillights, wheels, undercarriage, interior_seats, interior_dashboard.

ЧАСТЬ 2 — Развёрнутый текстовый отчёт после JSON. На русском, 7-10 предложений. Опиши: 1) внешнее состояние кузова и краски, 2) колёса и шины, 3) фары и окна, 4) предположения о салоне исходя из указанных данных, 5) предположения о двигателе и трансмиссии, 6) общая оценка с учётом года и пробега, 7) рекомендации по обслуживанию.""",

    "uz": """Siz transport diagnostikasi bo'yicha ekspert tizimisiz.

Foydalanuvchi batafsil ma'lumotlarni berdi:
{vehicle_details}

Rasmni shu ma'lumotlar kontekstida diqqat bilan tahlil qiling va javobni IKKI qismda bering:

QISM 1 — JSON blok (majburiy). Birinchi BITTA JSON blok chiqaring (0-100):
```json
{{
  "confidence": 88,
  "overall": 82,
  "body": 80,
  "paint": 78,
  "tires": 90,
  "lights": 95,
  "windows": 100,
  "frame": 85,
  "interior": 75,
  "engine_estimate": 80,
  "vehicle_detected": true,
  "vehicle_type": "sedan",
  "color_detected": "oq",
  "severity": "minor",
  "damage_areas": ["front_bumper"],
  "estimated_age_score": 70,
  "maintenance_score": 75
}}
```
severity: none, minor, moderate, severe dan biri.
damage_areas: kodlar: front_bumper, rear_bumper, hood, roof, left_door, right_door, left_fender, right_fender, left_mirror, right_mirror, windshield, rear_window, headlights, taillights, wheels, undercarriage, interior_seats, interior_dashboard.

QISM 2 — JSON dan keyin batafsil matn. O'zbek tilida 7-10 gap. Yoritib bering: 1) tana va bo'yoq, 2) g'ildiraklar va shinalar, 3) chiroqlar va oynalar, 4) salon haqida taxminlar, 5) dvigatel va transmissiya, 6) yil va probegga qarab umumiy baho, 7) tavsiyalar.""",

    "en": """You are an expert vehicle diagnostics system.

The user provided these detailed vehicle parameters:
{vehicle_details}

Carefully examine the image in the context of those parameters and produce a response in TWO parts:

PART 1 — JSON block (required). First output ONE JSON block inside triple backticks (numbers 0-100):
```json
{{
  "confidence": 88,
  "overall": 82,
  "body": 80,
  "paint": 78,
  "tires": 90,
  "lights": 95,
  "windows": 100,
  "frame": 85,
  "interior": 75,
  "engine_estimate": 80,
  "vehicle_detected": true,
  "vehicle_type": "sedan",
  "color_detected": "white",
  "severity": "minor",
  "damage_areas": ["front_bumper"],
  "estimated_age_score": 70,
  "maintenance_score": 75
}}
```
severity is one of: none, minor, moderate, severe.
damage_areas codes: front_bumper, rear_bumper, hood, roof, left_door, right_door, left_fender, right_fender, left_mirror, right_mirror, windshield, rear_window, headlights, taillights, wheels, undercarriage, interior_seats, interior_dashboard.

PART 2 — A detailed text report after the JSON block. In English, 7-10 sentences. Cover: 1) body and paint, 2) wheels and tires, 3) lights and windows, 4) interior estimate based on the provided data, 5) engine and transmission estimate, 6) overall assessment given year and mileage, 7) maintenance recommendations.""",
}


def _format_detail_block(data, lang):
    """Render the user-supplied detailed fields as a labelled block for the prompt."""
    labels = {
        "ru": {
            "vehicle": "Транспорт", "brand": "Марка", "model": "Модель", "year": "Год",
            "color": "Цвет", "mileage": "Пробег", "fuel": "Топливо",
            "transmission": "Трансмиссия", "extra": "Дополнительно",
        },
        "uz": {
            "vehicle": "Transport", "brand": "Brand", "model": "Model", "year": "Yil",
            "color": "Rang", "mileage": "Probeg", "fuel": "Yoqilg'i",
            "transmission": "Uzatma", "extra": "Qo'shimcha",
        },
        "en": {
            "vehicle": "Vehicle", "brand": "Brand", "model": "Model", "year": "Year",
            "color": "Color", "mileage": "Mileage", "fuel": "Fuel",
            "transmission": "Transmission", "extra": "Additional",
        },
    }
    L = labels.get(lang, labels["en"])
    lines = []
    if data.get("vehicle"): lines.append(f"- {L['vehicle']}: {data['vehicle']}")
    if data.get("brand"):   lines.append(f"- {L['brand']}: {data['brand']}")
    if data.get("model"):   lines.append(f"- {L['model']}: {data['model']}")
    if data.get("year"):    lines.append(f"- {L['year']}: {data['year']}")
    if data.get("color"):   lines.append(f"- {L['color']}: {data['color']}")
    if data.get("mileage"): lines.append(f"- {L['mileage']}: {data['mileage']}")
    if data.get("fuel"):    lines.append(f"- {L['fuel']}: {data['fuel']}")
    if data.get("transmission"): lines.append(f"- {L['transmission']}: {data['transmission']}")
    if data.get("extra"):   lines.append(f"- {L['extra']}: {data['extra']}")
    return "\n".join(lines) if lines else "(none provided)"


def _extract_json(text):
    """Pull the first ```json ... ``` block out of the text and parse it."""
    if not text:
        return None, text
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not m:
        # Fallback: try to find a bare {...} object
        m = re.search(r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})", text, re.DOTALL)
    if not m:
        return None, text
    raw_json = m.group(1)
    cleaned_text = (text[:m.start()] + text[m.end():]).strip()
    try:
        return json.loads(raw_json), cleaned_text
    except Exception:
        # Sometimes models add trailing commas; try a quick fix
        fixed = re.sub(r",(\s*[}\]])", r"\1", raw_json)
        try:
            return json.loads(fixed), cleaned_text
        except Exception:
            return None, cleaned_text


def _clamp(v, lo=0, hi=100):
    try:
        v = float(v)
    except Exception:
        return 0
    return max(lo, min(hi, v))


def _normalize_metrics(metrics, mode):
    """Make sure all expected keys exist, with safe defaults."""
    if not isinstance(metrics, dict):
        metrics = {}
    keys = ["overall", "body", "paint", "tires", "lights", "windows", "frame"]
    if mode == "detailed":
        keys += ["interior", "engine_estimate", "estimated_age_score", "maintenance_score"]
    out = {}
    for k in keys:
        out[k] = round(_clamp(metrics.get(k, 0)), 1)
    out["confidence"] = round(_clamp(metrics.get("confidence", 0)), 1)
    out["vehicle_detected"] = bool(metrics.get("vehicle_detected", True))
    out["vehicle_type"] = str(metrics.get("vehicle_type", "") or "")
    out["color_detected"] = str(metrics.get("color_detected", "") or "")
    sev = str(metrics.get("severity", "") or "").lower()
    if sev not in {"none", "minor", "moderate", "severe"}:
        sev = "minor" if metrics.get("damage_areas") else "none"
    out["severity"] = sev
    raw_areas = metrics.get("damage_areas", [])
    if not isinstance(raw_areas, list):
        raw_areas = []
    # Allow Russian/Uzbek codes too — map common Cyrillic codes to English
    cyr_map = {
        "передний_бампер": "front_bumper", "задний_бампер": "rear_bumper",
        "капот": "hood", "крыша": "roof",
        "левая_дверь": "left_door", "правая_дверь": "right_door",
        "левое_крыло": "left_fender", "правое_крыло": "right_fender",
        "левое_зеркало": "left_mirror", "правое_зеркало": "right_mirror",
        "лобовое_стекло": "windshield", "заднее_стекло": "rear_window",
        "фары": "headlights", "задние_фары": "taillights",
        "колёса": "wheels", "колеса": "wheels", "днище": "undercarriage",
        "салон_сиденья": "interior_seats", "салон_панель": "interior_dashboard",
    }
    valid = {
        "front_bumper", "rear_bumper", "hood", "roof",
        "left_door", "right_door", "left_fender", "right_fender",
        "left_mirror", "right_mirror", "windshield", "rear_window",
        "headlights", "taillights", "wheels", "undercarriage",
        "interior_seats", "interior_dashboard",
    }
    mapped = []
    for a in raw_areas:
        s = str(a).strip().lower().replace(" ", "_")
        s = cyr_map.get(s, s)
        if s in valid:
            mapped.append(s)
    out["damage_areas"] = mapped
    return out


def analyze_image(image_path, language="ru", mode="simple", details=None):
    """
    Analyse a vehicle image.

    Args:
        image_path: path to the uploaded image
        language: 'ru' | 'uz' | 'en'
        mode: 'simple' | 'detailed'
        details: dict with keys vehicle, brand, model, year, color, mileage,
                 fuel, transmission, extra. Only `vehicle` is used in simple mode.

    Returns:
        {'text': <human report>, 'confidence': <0-100>, 'metrics': <dict>}
    """
    details = details or {}
    try:
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        ext = image_path.lower().split(".")[-1]
        media_type_map = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp", "gif": "image/gif",
        }
        media_type = media_type_map.get(ext, "image/jpeg")

        lang = language if language in SIMPLE_INSTRUCTIONS else "ru"

        if mode == "detailed":
            prompt = DETAILED_INSTRUCTIONS[lang].format(
                vehicle_details=_format_detail_block(details, lang)
            )
        else:
            vehicle_name = details.get("vehicle", "") or "—"
            prompt = SIMPLE_INSTRUCTIONS[lang].format(vehicle=vehicle_name)

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "anthropic/claude-haiku-4-5",
                "max_tokens": 1500,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            }},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            },
            timeout=90,
        )

        data = response.json()
        full_text = data["choices"][0]["message"]["content"]

        metrics, cleaned_text = _extract_json(full_text)
        metrics = _normalize_metrics(metrics, mode)

        # Strip stray markdown headers / leftover labels
        lines = []
        for line in cleaned_text.splitlines():
            ln = line.strip()
            if not ln:
                continue
            if re.match(r"^#+\s", ln):
                continue
            if re.match(r"^(part\s*\d|часть\s*\d|qism\s*\d)\b", ln, re.IGNORECASE):
                continue
            if re.match(r"(?i)^(confidence|уверенность|ishonch)\s*:", re.sub(r"\*+", "", ln)):
                continue
            lines.append(line.rstrip())
        display_text = "\n".join(lines).strip()

        return {
            "text": display_text,
            "confidence": metrics.get("confidence", 0),
            "metrics": metrics,
        }

    except Exception as e:
        error_messages = {
            "ru": f"Ошибка AI: {str(e)}",
            "uz": f"AI xatosi: {str(e)}",
            "en": f"AI Error: {str(e)}",
        }
        return {
            "text": error_messages.get(language, f"AI Error: {str(e)}"),
            "confidence": 0,
            "metrics": _normalize_metrics({}, mode),
        }
