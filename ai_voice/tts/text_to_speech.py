import asyncio
import re
import edge_tts


class TextToSpeechEngine:
    VOICES = {
        "ar": "ar-EG-SalmaNeural",   # Nouran (Simplified MSA)
        "en": "en-US-JennyNeural"    # Rachel (Clear, mature, warm female tutor voice)
    }

    PERSONA_NAMES = {
        "ar": "Nouran",
        "en": "Rachel"
    }

    def __init__(self, ar_rate: str = "-5%", ar_pitch: str = "+3Hz", en_rate: str = "-3%"):
        self.ar_rate = ar_rate
        self.ar_pitch = ar_pitch
        self.en_rate = en_rate  # Slightly slower (-3%) for crisp articulation for kids

    def _humanize_text(self, text: str, lang: str) -> str:
        text = re.sub(r'[*#_`~]', '', text)
        
        if lang == "en":
            # Phonetic spelling adjustment so English TTS pronounces "وصول" clearly
            text = re.sub(r'\bWusool\b', 'Wu-sool', text, flags=re.IGNORECASE)

        text = text.replace("،", "، ... ")
        text = text.replace(",", ", ... ")
        text = text.replace("!", "! ... ")
        text = text.replace("؟", "؟ ... ")
        text = text.replace("?", "? ... ")
        return text.strip()

    async def _generate_audio(self, text: str, lang: str, voice: str, output_path: str) -> None:
        clean_text = self._humanize_text(text, lang)
        rate = self.en_rate if lang == "en" else self.ar_rate
        pitch = "+0Hz" if lang == "en" else self.ar_pitch

        communicate = edge_tts.Communicate(
            clean_text,
            voice,
            rate=rate,
            pitch=pitch
        )
        await communicate.save(output_path)

    def synthesize(self, text: str, lang: str = "ar", output_path: str = "output.mp3") -> str:
        voice = self.VOICES.get(lang, self.VOICES["ar"])
        persona = self.PERSONA_NAMES.get(lang, "Nouran")
        print(f"Synthesizing [{lang}] audio with '{persona}' ({voice})...")
        asyncio.run(self._generate_audio(text, lang, voice, output_path))
        return output_path


if __name__ == "__main__":
    tts = TextToSpeechEngine()

    # 1. Nouran (Arabic - Simplified MSA)
    arabic_text = "أهلاً بِكَ يا بَطَل في تَطبيقِ وُصول! أنا نوران، مُعَلِّمَتُكَ الذَّكِيَّة. ماذا تُحِبُّ أن نَتَعَلَّمَ اليَوم؟ اللُّغَةَ الإنجليزِيَّة، أمِ العُلوم، أم أساسيّاتِ الحاسِبِ الآلي؟"
    tts.synthesize(arabic_text, lang="ar", output_path="test_nouran.mp3")

    # 2. Rachel (English Only - Mature, crisp tutor voice)
    english_text = "Welcome to Wusool! I am Rachel, your smart tutor. What would you like to learn today? English, Science, or ICT?"
    tts.synthesize(english_text, lang="en", output_path="test_rachel.mp3")