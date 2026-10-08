# Wusool AI Tutor - API Specifications & Integration Contract

This document outlines the OpenAPI/REST specifications and WebSocket contract for the **Wusool (وصول)** AI Tutor backend. It serves as the official integration contract between the frontend interface and backend microservices.

---

## Base URL
http://localhost:8000/api
---

## 1. AI Tutor & RAG Engine (`/api/tutor`)

### **`POST /api/tutor/ask`**
Submits a student's text/voice query to the RAG engine for curriculum context retrieval and response generation.

* **Headers:** `Content-Type: application/json`
* **Request Body:**
```json
{
  "subject": "math",
  "question": "كم مجموع 5 + 3؟",
  "language": "ar",
  "lesson_id": "math_g2_add_01"
}
lesson_id is optional. If provided, retrieval is narrowed down to the specified lesson context.

Response (200 OK - Answer Found in Curriculum):{
  "answer": "مجموع 5 زائد 3 يساوي 8! أحسنت يا بطل.",
  "citations": [
    {
      "file": "math_grade2_addition.json",
      "pages": [1, 2]
    }
  ],
  "used_fallback": false,
  "not_covered": false
}
Response (200 OK - Similarity Score < 0.30 / Out of Scope):
{
  "answer": "عفواً، هذا السؤال خارج المنهج الدراسي المتاح حالياً.",
  "citations": [],
  "used_fallback": true,
  "not_covered": true
}
2. Student Profile Management (/api/students)
POST /api/students
Registers a new anonymous or named student profile with accessibility preferences.

Headers: Content-Type: application/json

Request Body:

JSON
{
  "nickname": "بطل الوصول",
  "accessibility_mode": "vision",
  "language": "ar"
}
Supported accessibility_mode values: "vision" (Visually Impaired / Blind), "dyslexia" (Dyslexia / Learning Disabilities).

Response (201 Created):

JSON
{
  "student_id": "st_xk9L_3mQ1z"
}
DELETE /api/students/{student_id}
Deletes a student profile and purges associated attempt records.

Parameters: student_id (Path parameter)

Response (200 OK):

JSON
{
  "deleted": true,
  "student_id": "st_xk9L_3mQ1z"
}
3. Progress Tracking (/api/progress)
POST /api/progress/attempts
Logs a student's answer attempt for a specific question/lesson.

Headers: Content-Type: application/json

Request Body:

JSON
{
  "student_id": "st_xk9L_3mQ1z",
  "lesson_id": "ict_basics_01",
  "question_id": "q_cpu_01",
  "correct": true
}
Response (200 OK):

JSON
{
  "saved": true
}
GET /api/progress/{student_id}
Retrieves historical performance statistics and progress breakdown for a given student.

Parameters: student_id (Path parameter)

Response (200 OK):

JSON
{
  "student_id": "st_xk9L_3mQ1z",
  "attempts_total": 12,
  "correct_total": 10,
  "lessons": [
    {
      "lesson_id": "math_g2_add_01",
      "attempts": 7,
      "correct": 6
    },
    {
      "lesson_id": "ict_basics_01",
      "attempts": 5,
      "correct": 4
    }
  ]
}
4. Group Sessions & WebSockets (/ws/group/{room_id})
WebSocket /ws/group/{room_id}
Real-time connection for managing group sessions, turn allocation, and audio events.

Connection Query Params: ?student_id=st_xk9L_3mQ1z&nickname=بطل_الوصول

Inbound Message Format (Client -> Server):

JSON
{
  "action": "submit_answer",
  "question_id": "q_cpu_01",
  "answer": "3"
}
Outbound Event Format (Server -> Clients):

JSON
{
  "event": "turn_allocated",
  "active_student_id": "st_xk9L_3mQ1z",
  "active_nickname": "بطل الوصول",
  "message": "الان دور البطل أحمد للإجابة على السؤال التالي!"
}
5. Privacy, Audio & Browser Requirements
Browser Microphone Permissions:

Web Audio & Speech Recognition APIs strictly require an HTTPS connection or localhost execution environment.

Third-Party Speech Processing Note:

Browser-native speech recognition (e.g., Google SpeechRecognition on Chrome/Edge) transmits audio packets to external processing servers. Parent/Guardian consent must be declared in the UI.

Demo Security Disclaimer:

The /api/progress/attempts endpoint accepts client-evaluated correct flags for MVP demo simplicity. Production implementations will validate answers strictly server-side.
