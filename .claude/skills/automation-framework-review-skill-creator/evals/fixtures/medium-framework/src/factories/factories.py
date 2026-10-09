"""Test-data builders.

Builder pattern used consistently across all test-data construction
(accounts, contacts, tickets, subscriptions) instead of ad hoc dicts
scattered through test bodies. Every builder returns a plain dict ready
to hand to the matching *Client or *Page, and every mutator returns self so
calls chain.
"""
import itertools
import uuid

_seq = itertools.count(1)


class AccountBuilder:
    def __init__(self):
        n = next(_seq)
        self._payload = {
            "name": f"Acme Test Account {n}",
            "billing_email": f"billing.{n}@example.com",
            "plan_tier": "standard",
            "status": "active",
        }

    def with_name(self, name: str) -> "AccountBuilder":
        self._payload["name"] = name
        return self

    def with_plan_tier(self, tier: str) -> "AccountBuilder":
        self._payload["plan_tier"] = tier
        return self

    def suspended(self) -> "AccountBuilder":
        self._payload["status"] = "suspended"
        return self

    def build(self) -> dict:
        return dict(self._payload)


class ContactBuilder:
    def __init__(self):
        n = next(_seq)
        self._payload = {
            "full_name": f"Test Contact {n}",
            "email": f"contact.{n}@example.com",
            "phone": "+1-555-0100",
            "is_primary": False,
        }

    def with_email(self, email: str) -> "ContactBuilder":
        self._payload["email"] = email
        return self

    def as_primary(self) -> "ContactBuilder":
        self._payload["is_primary"] = True
        return self

    def build(self) -> dict:
        return dict(self._payload)


class TicketBuilder:
    def __init__(self):
        n = next(_seq)
        self._payload = {
            "subject": f"Test ticket {n}",
            "description": "Auto-generated ticket for automation coverage.",
            "priority": "normal",
            "status": "open",
        }

    def with_subject(self, subject: str) -> "TicketBuilder":
        self._payload["subject"] = subject
        return self

    def with_priority(self, priority: str) -> "TicketBuilder":
        self._payload["priority"] = priority
        return self

    def build(self) -> dict:
        return dict(self._payload)


class SubscriptionBuilder:
    def __init__(self):
        self._payload = {
            "plan_code": "PRO-MONTHLY",
            "seats": 5,
            "auto_renew": True,
            "external_ref": str(uuid.uuid4()),
        }

    def with_plan_code(self, plan_code: str) -> "SubscriptionBuilder":
        self._payload["plan_code"] = plan_code
        return self

    def with_seats(self, seats: int) -> "SubscriptionBuilder":
        self._payload["seats"] = seats
        return self

    def without_auto_renew(self) -> "SubscriptionBuilder":
        self._payload["auto_renew"] = False
        return self

    def build(self) -> dict:
        return dict(self._payload)
