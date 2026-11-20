CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS textbooks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    book_id VARCHAR(150) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    grade SMALLINT NOT NULL,
    term SMALLINT NOT NULL,
    language VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    textbook_id BIGINT NOT NULL REFERENCES textbooks(id) ON DELETE CASCADE,
    pdf_page_index INTEGER NOT NULL,
    printed_page_number VARCHAR(50),
    page_type VARCHAR(100),
    include_in_rag BOOLEAN NOT NULL DEFAULT TRUE,
    exclusion_reason TEXT,
    unit_id VARCHAR(100),
    unit_title TEXT,
    lesson_id VARCHAR(100),
    lesson_title TEXT,
    section_type VARCHAR(100),
    section_title TEXT,
    unit_type VARCHAR(100),
    raw_content TEXT,
    processed_content TEXT,
    ocr_uncertain_readings JSONB,
    source_metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (textbook_id, pdf_page_index)
);

CREATE TABLE IF NOT EXISTS chunks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chunk_id VARCHAR(255) NOT NULL UNIQUE,
    textbook_id BIGINT NOT NULL REFERENCES textbooks(id) ON DELETE CASCADE,
    page_id BIGINT NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_type VARCHAR(100),
    unit_id VARCHAR(100),
    unit_title TEXT,
    lesson_id VARCHAR(100),
    lesson_title TEXT,
    section_type VARCHAR(100),
    section_title TEXT,
    pdf_page_index INTEGER NOT NULL,
    printed_page_number VARCHAR(50),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Dimensionless vector allows model choice later. Create a dimension-specific
-- ANN index only after selecting the embedding model and dimension.
CREATE TABLE IF NOT EXISTS chunk_embeddings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chunk_id BIGINT NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    embedding_model VARCHAR(150) NOT NULL,
    embedding vector NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (chunk_id, embedding_model)
);

CREATE INDEX IF NOT EXISTS idx_pages_textbook ON pages(textbook_id);
CREATE INDEX IF NOT EXISTS idx_chunks_textbook ON chunks(textbook_id);
CREATE INDEX IF NOT EXISTS idx_chunks_page ON chunks(page_id);
CREATE INDEX IF NOT EXISTS idx_chunks_unit_lesson
    ON chunks(textbook_id, unit_id, lesson_id);
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING GIN(metadata);
