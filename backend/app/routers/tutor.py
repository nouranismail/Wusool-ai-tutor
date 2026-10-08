from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from typing import Optional

# استدعاء وحدات الصوت والـ RAG الجاهزة عندك
from backend.app.audio.tts import text_to_speech_bytes
from backend.app.audio.stt import speech_to_text
from backend.app.rag.retriever import retrieve_context

# هيلزم استدعاء دوال الـ Tutor لما زميلتك تخلصها من backend.app.tutor.explain
# from backend.app.tutor.explain import generate_tutor_response

router = APIRouter(prefix="/api/tutor", tags=["Tutor"])


@router.post("/ask")
async def ask_tutor(
    subject: str = Form("ict"),
    question: str = Form(...),
    language: str = Form("ar"),
    lesson_id: Optional[str] = Form(None)
):
    """
    مسار استقبال الأسئلة نصياً وإرجاع النص والصوت معاً
    """
    try:
        # 1. استرجاع السياق من الـ RAG
        rag_result = retrieve_context(question, lesson_id)
        
        # 2. مبدئياً نستخدم نص الـ RAG لحين اكتمال explain.py من الزميلة
        if rag_result.get("not_covered"):
            answer_text = "عفواً يا بطل، هذا السؤال خارج المنهج المتاح حالياً."
        else:
            answer_text = rag_result["context"][0] if rag_result["context"] else "أحسنت يا بطل!"

        # 3. تحويل النص الناتج إلى صوت
        audio_bytes = await text_to_speech_bytes(answer_text)

        return {
            "answer": answer_text,
            "citations": rag_result.get("citations", []),
            "used_fallback": rag_result.get("used_fallback", False),
            "not_covered": rag_result.get("not_covered", False)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask-audio")
async def ask_tutor_audio(file: UploadFile = File(...)):
    """
    مسار استقبال صوت الطفل مباشرة (Speech-to-Speech)
    """
    try:
        # 1. حفظ ملف الصوت المؤقت وتحويله لنص
        temp_audio_path = f"temp_{file.filename}"
        with open(temp_audio_path, "wb") as f:
            f.write(await file.read())

        user_text = speech_to_text(temp_audio_path)

        # 2. معالجة السؤال بالـ RAG
        rag_result = retrieve_context(user_text)
        answer_text = rag_result["context"][0] if rag_result.get("context") else "عفواً، لم أفهم السؤال جيداً."

        # 3. تحويل الرد إلى صوت
        audio_bytes = await text_to_speech_bytes(answer_text)

        return Response(content=audio_bytes, media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))