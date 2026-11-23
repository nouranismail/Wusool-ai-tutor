"""
POST /api/voice/stt
POST /api/voice/chat
POST /api/voice/tts
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response

from backend.app.core.dependencies import get_current_child
from backend.app.db.models.child import Child
from backend.app.schemas.voice import STTResponse, VoiceChatResponse
from backend.app.services.mock_data import mock_stt, mock_voice_chat

router = APIRouter()


@router.post("/voice/stt", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(...),
    lang: str = Form(default="ar"),
    _: Child = Depends(get_current_child),
):
    """
    Transcribe uploaded audio to text.
    Mock implementation: ignores audio bytes and returns a fixed transcript.
    Replace with real STT (Whisper / Groq) when Engineer 5 is ready.
    """
    return mock_stt(lang)


@router.post("/voice/chat", response_model=VoiceChatResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    lang: str = Form(default="ar"),
    lessonId: str = Form(default=""),
    conversationId: str = Form(default=""),
    _: Child = Depends(get_current_child),
):
    """
    Voice round-trip: STT → AI response → (TTS URL).
    Mock implementation: returns fixed transcript and reply.
    """
    return mock_voice_chat(lang)


@router.post("/voice/tts")
async def text_to_speech(
    body: dict,
    _: Child = Depends(get_current_child),
):
    """
    Convert text to speech and return raw audio binary (audio/mpeg).
    Mock implementation: returns minimal silent MP3 bytes.
    Replace with ElevenLabs / gTTS when Engineer 5 is ready.
    """
    # Minimal valid MP3 frame header (silent audio)
    silent_mp3 = bytes([
        0xFF, 0xFB, 0x90, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ])
    return Response(content=silent_mp3, media_type="audio/mpeg")
