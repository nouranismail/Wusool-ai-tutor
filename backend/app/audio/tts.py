import edge_tts

# استخدام صوت عربي دافئ ومناسب للأطفال (مصر أو السعودية)
DEFAULT_VOICE = "ar-EG-SalmaNeural"  # أو "ar-SA-HamedNeural"

async def text_to_speech_bytes(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    """تحويل النص إلى مقطع صوتي (Audio Bytes) فوراً"""
    communicate = edge_tts.Communicate(text, voice)
    audio_data = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
    return bytes(audio_data)

async def save_text_to_speech_file(text: str, output_path: str, voice: str = DEFAULT_VOICE):
    """حفظ الصوت في ملف MP3"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)