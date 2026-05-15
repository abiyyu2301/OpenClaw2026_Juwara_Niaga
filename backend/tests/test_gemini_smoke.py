"""Phase 0 smoke test: one Gemini call returning JSON.

Run with: `python -m backend.tests.test_gemini_smoke` from the repo root,
or `python tests/test_gemini_smoke.py` from inside backend/.

Requires:
- credentials/niaga-backend-key.json present
- GOOGLE_APPLICATION_CREDENTIALS pointing to it (set in .env)
- Vertex AI API enabled on the GCP project
"""

import asyncio
import os
import sys
from pathlib import Path

# Allow running this file directly from inside backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


async def main() -> None:
    # Make sure GOOGLE_APPLICATION_CREDENTIALS is set before importing genai.
    from settings import settings

    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        # Fall back to the .env value if present
        if settings.google_application_credentials:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials

    from agents.llm import gemini_json

    print(f"→ Project: {settings.gcp_project_id}")
    print(f"→ Location: {settings.gcp_location}")
    print(f"→ Credentials: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")
    print(f"→ Model: {settings.model_judge}")
    print()

    result = await gemini_json(
        model=settings.model_judge,
        system_instruction=(
            "You are a JSON-only test assistant. Reply with the exact shape "
            "requested. Do not add any prose."
        ),
        user_prompt=(
            "Reply with JSON: "
            '{"greeting": "<a one-word greeting in Bahasa Indonesia>", '
            '"ready_to_build": <true or false>}'
        ),
        max_output_tokens=80,
        temperature=0.0,
    )
    print(f"✓ Latency: {result.latency_ms} ms")
    print(f"✓ Tokens: {result.prompt_tokens} in / {result.completion_tokens} out")
    print(f"✓ Parsed JSON: {result.data}")


if __name__ == "__main__":
    asyncio.run(main())
