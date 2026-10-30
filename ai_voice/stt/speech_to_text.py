import os
import whisper

class SpeechToTextEngine:
    def __init__(self, model_size: str = "base"):
        """
        Initializes local Whisper model.
        Available sizes: 'tiny', 'base', 'small', 'medium', 'large'
        """
        print(f"Loading Whisper model ({model_size})...")
        self.model = whisper.load_model(model_size)

    def transcribe_audio(self, audio_path: str, language: str = "ar") -> str:
        """
        Transcribes audio file to text. Defaults to Arabic ('ar').
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found at: {audio_path}")
            
        print(f"Transcribing audio file: {audio_path}...")
        result = self.model.transcribe(audio_path, language=language)
        return result.get("text", "").strip()

if __name__ == "__main__":
    stt = SpeechToTextEngine(model_size="base")
    print("STT Engine initialized successfully!")