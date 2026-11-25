
from .retriever import Retriever


def main():
    retriever = Retriever()
    grade_text = input("Grade (4, 5, or empty for all): ").strip()
    if grade_text and grade_text not in {"4", "5"}:
        raise SystemExit("Grade must be 4, 5, or empty")
    grade = int(grade_text) if grade_text else None

    subject = input("Subject (English, ICT, Science, or empty for all): ").strip()
    subjects = {"english": "English", "ict": "ICT", "science": "Science"}
    if subject and subject.casefold() not in subjects:
        raise SystemExit("Subject must be English, ICT, Science, or empty")
    subject = subjects[subject.casefold()] if subject else None

    while True:
        question = input("\nQuestion (empty to quit): ").strip()
        if not question:
            break
        results = retriever.search(
            question,
            grade=grade,
            subject=subject,
        )
        if not results:
            print("No matching chunks found.")
        for result in results:
            print(f"\n[{result['score']}] {result['subject']} Grade {result['grade']} | "
                  f"{result['lesson_title'] or result['section_title']} | page "
                  f"{result['printed_page_number']}")
            print(result["text"][:300].replace("\n", " / "))


if __name__ == "__main__":
    main()
