"""Optional LLM extraction adapter.

The system is fully functional WITHOUT this module (rules cover the supplied
dataset). If you use a hosted model here you MUST disclose it per the project
rules, keep this interface, and keep normalization/validation downstream -
the LLM proposes, pydantic + normalize.py dispose. Never let the LLM see
golden labels or test queries.
"""
from __future__ import annotations


class LLMExtractionBackend:
    """Drop-in alternative to extract_document() for formats rules cannot parse."""

    def extract(self, text: str, source_document: str, fallback_id: str) -> dict:
        raise NotImplementedError(
            "Implement with your chosen provider (or a local model via ollama). "
            "Return a dict of Opportunity fields; validate.py must accept it."
        )
