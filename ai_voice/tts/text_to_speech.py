import os
from gtts import gTTS

class TextToSpeechEngine:
    def __init__(self, language: str = "ar"):
        self.language = language

    def synthesize(self, text: str, output_path: str = "test_welcome.mp3") -> str:
        """
        Converts text to an MP3 audio file.
        """
        print(f"Synthesizing audio for text: '{text}'...")
        tts = gTTS(text=text, lang=self.language, slow=False)
        tts.save(output_path)
        print(f"Audio saved to: {output_path}")
        return output_path

if __name__ == "__main__":
    tts = TextToSpeechEngine()
    tts.synthesize("Welcome to Wusool, I am your smart AI tutor.")