# Wusool-ai-tutor

wusool-ai-tutor/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── data/
│   ├── curriculum/
│   │   ├── math_grade2_addition.json
│   │   └── ict_basics.json
│   └── misconceptions/
│       └── math_grade2_misconceptions.json
│
├── backend/
│   ├── main.py                 # FastAPI app الأساسي
│   ├── rag/
│   │   ├── indexer.py           # بناء فهرسة FAISS
│   │   └── retriever.py         # استرجاع المحتوى
│   ├── tutor/
│   │   ├── explain.py           # توليد الشرح
│   │   ├── exercise.py          # توليد التمارين
│   │   └── evaluate.py          # تقييم الإجابة + تصنيف الغلط
│   ├── session/
│   │   └── group_manager.py     # إدارة الجلسات الجماعية والدور
│   └── models/
│       └── schemas.py           # Pydantic models
│
├── frontend/
│   └── (نسخة الـ HTML/Gradio بتاعت البروتوتايب)
│
├── docs/
│   ├── pitch_deck.pdf
│   ├── problem_statement.md
│   └── architecture_diagram.png
│
└── tests/
    └── test_rag.py
