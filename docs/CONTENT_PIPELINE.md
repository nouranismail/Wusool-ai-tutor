# Curriculum content pipeline

The supplied Math PDF contains scanned pages, so normal PDF text extraction returns no usable lesson text.

1. Store an authorized copy in `data/raw/` (ignored by Git).
2. Render every page at 300 DPI.
3. Run Arabic OCR and extract mathematical regions separately.
4. Have a teacher verify numbers, operators, examples, and answer keys against each page image.
5. Split content by subject, unit, lesson, concept, example, and exercise.
6. Store metadata: grade, language, lesson, page, content type, and review status.
7. Embed only approved chunks and keep page citations attached.
8. Evaluate retrieval and generated answers with a teacher-authored test set before release.

Never use unreviewed OCR output to teach a child; a single incorrect symbol can reverse the meaning of a mathematics problem.

