"""
Unit tests for the Wusool AI Tutor backend.

Covers:
  - GET  /           (root)
  - GET  /health     (health check)
  - POST /v1/ask     (success case)
  - POST /v1/ask     (missing question)
  - POST /v1/ask     (invalid mode)
  - POST /v1/ask     (invalid input_mode)

Run with:
    cd <project-root>
    python -m tests.test_backend

Or via the helper script:
    python tests/run_tests.py
"""

from __future__ import annotations

import sys
import unittest
import warnings

# ---------------------------------------------------------------------------
# Path setup
# Append the system site-packages AFTER the venv so the system's `httpx`
# (which starlette.testclient needs) is importable, while the venv's
# fastapi/pydantic/starlette packages remain authoritative.
# ---------------------------------------------------------------------------
_SYSTEM_SITE = "/usr/lib/python3.14/site-packages"
if _SYSTEM_SITE not in sys.path:
    sys.path.append(_SYSTEM_SITE)

# Silence the starlette deprecation warning about httpx vs httpx2 during tests.
warnings.filterwarnings("ignore", category=DeprecationWarning, module="starlette")

from starlette.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=True)


class TestRootEndpoint(unittest.TestCase):
    """GET / – basic API identification."""

    def test_status_200(self) -> None:
        response = client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_response_keys(self) -> None:
        data = client.get("/").json()
        self.assertIn("name", data)
        self.assertIn("version", data)
        self.assertIn("status", data)
        self.assertIn("docs", data)

    def test_status_running(self) -> None:
        data = client.get("/").json()
        self.assertEqual(data["status"], "running")


class TestHealthEndpoint(unittest.TestCase):
    """GET /health – operational health."""

    def test_status_200(self) -> None:
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_status_ok(self) -> None:
        data = client.get("/health").json()
        self.assertEqual(data["status"], "ok")

    def test_has_environment(self) -> None:
        data = client.get("/health").json()
        self.assertIn("environment", data)


class TestAskEndpointSuccess(unittest.TestCase):
    """POST /v1/ask – successful educational question flow."""

    _VALID_PAYLOAD = {
        "question": "ما هو الحاسوب؟",
        "grade": "3",
        "subject": "cs",
        "language": "ar",
        "input_mode": "text",
        "mode": "explain",
    }

    def _ask(self, payload: dict) -> tuple:
        response = client.post("/v1/ask", json=payload)
        return response.status_code, response.json()

    def test_status_200(self) -> None:
        code, _ = self._ask(self._VALID_PAYLOAD)
        self.assertEqual(code, 200)

    def test_response_status_success(self) -> None:
        _, data = self._ask(self._VALID_PAYLOAD)
        self.assertEqual(data["status"], "success")

    def test_answer_is_string(self) -> None:
        _, data = self._ask(self._VALID_PAYLOAD)
        self.assertIsInstance(data["answer"], str)
        self.assertTrue(len(data["answer"]) > 0)

    def test_sources_is_list(self) -> None:
        _, data = self._ask(self._VALID_PAYLOAD)
        self.assertIsInstance(data["sources"], list)

    def test_sources_contain_book_when_subject_grade_given(self) -> None:
        _, data = self._ask(self._VALID_PAYLOAD)
        self.assertTrue(len(data["sources"]) >= 1)
        self.assertIsNotNone(data["sources"][0]["book"])

    def test_latency_ms_present(self) -> None:
        _, data = self._ask(self._VALID_PAYLOAD)
        self.assertIsNotNone(data["latency_ms"])
        self.assertGreaterEqual(data["latency_ms"], 0)

    def test_no_sources_when_no_subject_or_grade(self) -> None:
        payload = {"question": "كم يساوي 2 زائد 2؟"}
        _, data = self._ask(payload)
        self.assertEqual(data["sources"], [])

    def test_all_modes_accepted(self) -> None:
        modes = ["explain", "simplify", "summarize", "quiz", "repeat"]
        for mode in modes:
            with self.subTest(mode=mode):
                payload = {**self._VALID_PAYLOAD, "mode": mode}
                code, data = self._ask(payload)
                self.assertEqual(code, 200)
                self.assertIn(mode.upper(), data["answer"])

    def test_voice_input_mode(self) -> None:
        payload = {**self._VALID_PAYLOAD, "input_mode": "voice"}
        code, data = self._ask(payload)
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "success")

    def test_default_language_arabic(self) -> None:
        """When language is omitted it defaults to 'ar' – request must still succeed."""
        payload = {"question": "ما هو الكمبيوتر؟"}
        code, _ = self._ask(payload)
        self.assertEqual(code, 200)


class TestAskEndpointValidation(unittest.TestCase):
    """POST /v1/ask – request validation edge cases."""

    def test_missing_question_returns_422(self) -> None:
        """question is required; omitting it must produce HTTP 422."""
        response = client.post("/v1/ask", json={"mode": "explain"})
        self.assertEqual(response.status_code, 422)

    def test_empty_question_returns_422(self) -> None:
        """question must have at least 1 character."""
        response = client.post("/v1/ask", json={"question": ""})
        self.assertEqual(response.status_code, 422)

    def test_invalid_mode_returns_422(self) -> None:
        """mode must be one of the five allowed values."""
        response = client.post(
            "/v1/ask",
            json={"question": "سؤال", "mode": "translate"},
        )
        self.assertEqual(response.status_code, 422)

    def test_invalid_input_mode_returns_422(self) -> None:
        """input_mode must be 'text' or 'voice'."""
        response = client.post(
            "/v1/ask",
            json={"question": "سؤال", "input_mode": "keyboard"},
        )
        self.assertEqual(response.status_code, 422)

    def test_empty_body_returns_422(self) -> None:
        """Sending an empty JSON body must fail validation."""
        response = client.post("/v1/ask", json={})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
