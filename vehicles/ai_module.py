import base64
import requests
from django.conf import settings


def analyze_image(image_path):
    try:
        # Read and base64-encode the image
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        # Detect media type from extension
        ext = image_path.lower().split(".")[-1]
        media_type_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif",
        }
        media_type = media_type_map.get(ext, "image/jpeg")

        prompt = """Ты система диагностики транспортных средств.

Внимательно осмотри изображение и сделай краткое заключение:
- есть ли транспортное средство на изображении
- если есть — что это за транспорт (марка, тип, цвет если видно)
- есть ли видимые повреждения, дефекты или проблемы (если нет — прямо скажи)
- общее техническое состояние по внешнему виду

Также в конце укажи числом от 0 до 100 уровень уверенности в своём анализе в формате:
УВЕРЕННОСТЬ: <число>

Ответ на русском, 4-5 предложений."""

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

        # Parse confidence score from the response
        confidence = 0.0
        lines = full_text.splitlines()
        for line in lines:
            if line.strip().startswith("УВЕРЕННОСТЬ:"):
                try:
                    confidence = float(line.split(":")[1].strip())
                except ValueError:
                    pass

        # Remove the confidence line from the displayed text
        display_text = "\n".join(
            line for line in lines if not line.strip().startswith("УВЕРЕННОСТЬ:")
        ).strip()

        return {
            "text": display_text,
            "confidence": round(confidence, 1),
        }

    except Exception as e:
        return {
            "text": f"Ошибка AI: {str(e)}",
            "confidence": 0,
        }