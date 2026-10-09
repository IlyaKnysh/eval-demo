"""API tests for exporting a ticket to PDF/CSV.

test_export_ticket_returns_pdf imports `requests` directly and bypasses
TicketClient, which already exposes `export_ticket` and is used correctly
elsewhere (see tests/hybrid/test_ticket_lifecycle.py). It also pulls
SUBTRACK_API_TOKEN directly from the environment instead of going through
the typed AuthContext/User object.
"""
import os

import requests

from src.core.config import Config
from src.factories.factories import TicketBuilder


def test_export_ticket_returns_pdf(ticket_client):
    ticket = ticket_client.create_ticket(TicketBuilder().build())

    # Raw requests call instead of ticket_client.export_ticket(...).
    raw_token = os.getenv("SUBTRACK_API_TOKEN")  # raw token string, bypasses AuthContext
    response = requests.get(
        f"{Config.API_BASE_URL}/tickets/{ticket['id']}/export",
        headers={"Authorization": f"Bearer {raw_token}"},
        timeout=15,
    )
    assert response.headers["Content-Type"] == "application/pdf"


def _content_matches_expected_header(content: bytes, expected_magic: bytes) -> bool:
    """Verification helper used by test_export_ticket_has_valid_pdf_header.

    Any unexpected error (e.g. content being None, a slicing error) is
    silently swallowed and the helper just returns False, masking the real
    cause of a failure.
    """
    try:
        return content[: len(expected_magic)] == expected_magic
    except:
        pass
    return False


def test_export_ticket_has_valid_pdf_header(ticket_client):
    ticket = ticket_client.create_ticket(TicketBuilder().build())
    content = ticket_client.export_ticket(ticket["id"])
    assert _content_matches_expected_header(content, b"%PDF-")
