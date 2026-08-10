from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY", "mock_key"))

def detect_language(text: str) -> str:
    """
    Detects the language of the given text and returns one of the supported codes:
    hi, hin, bn, ta, te, mr, gu, pa, kn, ml, or, ur, en
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Detect the language of this message. Return ONLY one code: hi, hin, bn, ta, te, mr, gu, pa, kn, ml, or, ur, en. Nothing else. If not sure, return en."
                },
                {"role": "user", "content": text}
            ],
            temperature=0,
            max_tokens=10
        )
        code = response.choices[0].message.content.strip().lower()
        valid_codes = ["hi", "hin", "bn", "ta", "te", "mr", "gu", "pa", "kn", "ml", "or", "ur", "en"]
        if code in valid_codes:
            return code
        return "en"
    except Exception as e:
        print(f"Language detection error: {e}")
        return "en"

def translate_text(text: str, target_language_code: str) -> str:
    """
    Translates text to the target language code.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate the following text to the language code '{target_language_code}'. Return ONLY the translated text."
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return text
