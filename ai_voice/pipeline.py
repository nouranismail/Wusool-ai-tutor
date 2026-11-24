import os
import asyncio
from langdetect import detect, DetectorFactory
# Change these lines:
# from stt.speech_to_text import SpeechToTextEngine
# from tts.text_to_speech import TextToSpeechEngine

# To these absolute package imports:
from ai_voice.stt.speech_to_text import SpeechToTextEngine
from ai_voice.tts.text_to_speech import TextToSpeechEngine

# Ensure consistent language detection results
DetectorFactory.seed = 0


class VoicePipeline:
    def __init__(self, stt_model_size: str = "base", tts_rate: str = "+15%"):
        """
        Initializes the Voice AI Pipeline combining Speech-to-Text (Whisper)
        and Text-to-Speech (edge-tts).
        """
        print("Initializing Voice AI Pipeline...")
        self.stt = SpeechToTextEngine(model_size=stt_model_size)
        self.tts = TextToSpeechEngine(rate=tts_rate)

    def detect_language(self, text: str) -> str:
        """
        Detects whether the given text is primarily Arabic or English.
        Returns 'ar' or 'en'.
        """
        try:
            lang = detect(text)
            if lang == "ar":
                return "ar"
            return "en"
        except Exception:
            # Default to Arabic for Wusool curriculum context
            return "ar"

    def process_student_audio(self, input_audio_path: str) -> dict:
        """
        Converts the student's spoken audio into text and identifies the language.
        """
        print(f"\n--- Processing Input Audio: {input_audio_path} ---")
        transcribed_text = self.stt.transcribe_audio(input_audio_path)
        detected_lang = self.detect_language(transcribed_text)

        print(f"Transcribed Text: '{transcribed_text}'")
        print(f"Detected Language: '{detected_lang}'")

        return {
            "text": transcribed_text,
            "language": detected_lang
        }

    def generate_tutor_response_audio(self, response_text: str, forced_lang: str = None, output_audio_path: str = "tutor_response.mp3") -> str:
        """
        Converts the AI tutor's text response into natural neural speech.
        """
        print(f"\n--- Generating Tutor Audio Response ---")
        target_lang = forced_lang if forced_lang else self.detect_language(response_text)
        
        saved_path = self.tts.synthesize(
            text=response_text,
            lang=target_lang,
            output_path=output_audio_path
        )
        return saved_path


if __name__ == "__main__":
    # Ensure langdetect library is installed (pip install langdetect)
    pipeline = VoicePipeline(stt_model_size="base", tts_rate="+15%")

    # Example 1: Simulating full Arabic pipeline flow
    arabic_tutor_reply = "ممتاز جداً! دعنا نحل المسألة التالية في الرياضيات."
    audio_output_ar = pipeline.generate_tutor_response_audio(
        response_text=arabic_tutor_reply,
        output_audio_path="test_pipeline_ar.mp3"
    )

    # Example 2: Simulating full US English pipeline flow
    english_tutor_reply = "Great job! Let's explore how a computer processor works."
    audio_output_en = pipeline.generate_tutor_response_audio(
        response_text=english_tutor_reply,
        output_audio_path="test_pipeline_en.mp3"
    )