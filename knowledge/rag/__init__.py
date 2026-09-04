"""Shared Knowledge RAG — local-first retrieval for specialists and sibling projects."""

from .retrieve import retrieve
from .scanner import scan_directory, extract_text

__all__ = ["retrieve", "scan_directory", "extract_text"]
