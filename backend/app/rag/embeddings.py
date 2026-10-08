from __future__ import annotations
import hashlib
import math
import re

ARABIC_DIACRITICS = re.compile(r"[\u0617-\u061A\u064B-\u0652]")


def normalize_arabic(text: str) -> str:
    """تنظيف وتوحيد الأحرف العربية للحصول على نتائج بحث دقيقة."""
    text = ARABIC_DIACRITICS.sub("", text.lower())
    text = text.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ؤ": "و", "ئ": "ي"}))
    return re.sub(r"[^\w]+", " ", text, flags=re.UNICODE).strip()


class HashingEmbedder:
    """مخلق متجهات ومضمن نصوص سريع يعتمد على التشفير وبدون الحاجة لـ APIs خارجية."""

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        normalized = normalize_arabic(text)
        words = normalized.split()
        features = [f"w:{word}" for word in words]
        compact = normalized.replace(" ", "_")
        features.extend(f"c:{compact[index:index + 3]}" for index in range(max(0, len(compact) - 2)))
        vector = [0.0] * self.dimensions
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            vector[value % self.dimensions] += 1.0 if value & 1 else -1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """حساب التشابه بين متجهين."""
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))