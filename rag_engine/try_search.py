
from .retriever import Retriever


def main():
    retriever = Retriever()
    grade_text = input("Grade (4, 5, or empty for all): ").strip()
    subject = input("Subject (English, ICT, Science, or empty for all): ").strip()

    while True:
        question = input("\nQuestion (empty to quit): ").strip()
        if not question:
            break
        results = retriever.search(
            question,
            grade=int(grade_text) if grade_text else None,
            subject=subject or None,
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
