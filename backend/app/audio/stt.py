import os
from openai import OpenAI

client = OpenAI()

def speech_to_text(audio_file_path: str) -> str:
    """تحويل ملف صوتي إلى نص باستخدام Whisper"""
    if not os.path.exists(audio_file_path):
        return ""
    
    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ar"  # تعيين العربية كلغة أساسية
        )
    return transcript.text

