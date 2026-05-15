import base64
import requests
from django.conf import settings


PROMPTS = {
    "ru": """Ты система диагностики транспортных средств.

Внимательно осмотри изображение и сделай краткое заключение:
- есть ли транспортное средство на изображении
- если есть — что это за транспорт (марка, тип, цвет если видно)
- есть ли видимые повреждения, дефекты или проблемы (если нет — прямо скажи)
- общее техническое состояние по внешнему виду

Также в конце укажи числом от 0 до 100 уровень уверенности в своём анализе в формате:
УВЕРЕННОСТЬ: <число>

Ответ на русском, 4-5 предложений.""",

    "uz": """Siz transport vositalarini diagnostika qilish tizimisiz.

Rasmni diqqat bilan ko'rib chiqing va qisqacha xulosa bering:
- rasmda transport vositasi bormi
- agar bor bo'lsa — bu qanday transport (marka, turi, ko'rinsa rangi)
- ko'rinadigan shikastlar, nuqsonlar yoki muammolar bormi (yo'q bo'lsa — to'g'ridan-to'g'ri ayting)
- tashqi ko'rinishiga qarab umumiy texnik holat

Shuningdek, oxirida tahlil ishonchlilik darajangizni 0 dan 100 gacha raqam bilan ko'rsating:
ISHONCH: <raqam>

Javob o'zbek tilida, 4-5 gap.""",

    "en": """You are a vehicle diagnostics system.

Carefully examine the image and provide a brief assessment:
- whether there is a vehicle in the image
- if yes — what type of transport it is (make, type, color if visible)
- whether there are any visible damages, defects or issues (if none — state that clearly)
- overall technical condition based on visual appearance

Also at the end, indicate your confidence level from 0 to 100 in the format:
CONFIDENCE: <number>

Answer in English, 4-5 sentences.""",
}

CONFIDENCE_KEYS = {
    "ru": "УВЕРЕННОСТЬ:",
    "uz": "ISHONCH:",
    "en": "CONFIDENCE:",
}


def analyze_image(image_path, language="ru"):
    try:
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        ext = image_path.lower().split(".")[-1]
        media_type_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif",
        }
        media_type = media_type_map.get(ext, "image/jpeg")

        lang = language if language in PROMPTS else "ru"
        prompt = PROMPTS[lang]
        confidence_key = CONFIDENCE_KEYS[lang]

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "anthropic/claude-haiku-4-5",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}",
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            },
        )

        data = response.json()
        full_text = data["choices"][0]["message"]["content"]

        confidence = 0.0
        lines = full_text.splitlines()
        import re
        # Strip markdown bold (**), asterisks, and whitespace before matching
        clean_key = confidence_key.rstrip(":")
        for line in lines:
            # Remove markdown bold markers and strip whitespace
            clean_line = re.sub(r'\*+', '', line).strip()
            if re.match(r'(?i)' + re.escape(clean_key) + r'\s*:', clean_line):
                try:
                    value_part = clean_line.split(":", 1)[1].strip()
                    # Extract the first number found (e.g. "85" from "85" or "85.")
                    match = re.search(r'[\d.]+', value_part)
                    if match:
                        confidence = float(match.group())
                except (ValueError, IndexError):
                    pass

        def is_confidence_line(line):
            clean = re.sub(r'\*+', '', line).strip()
            return bool(re.match(r'(?i)' + re.escape(clean_key) + r'\s*:', clean))

        display_text = "\n".join(
            line for line in lines if not is_confidence_line(line)
        ).strip()

        return {
            "text": display_text,
            "confidence": round(confidence, 1),
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
        }