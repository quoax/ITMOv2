subscribers = set()
"""Set of subscriber names kept for backward-compat tests and simple API."""

# Extra in-memory metadata to support pagination/sorting demo
# name -> { id: str, email: str, created_at: RFC3339 str, created_ts: float }
subscriber_meta = {}


def normalize_name(name: str) -> str:
    """Normalize subscriber name for consistent storage and lookup.
    Currently trims whitespace; keep simple to avoid language-specific changes.
    """
    return name.strip()


def subscribe(name: str):
    norm = normalize_name(name)
    if not norm:
        raise ValueError("empty name")
    subscribers.add(norm)
    # Create metadata record on first subscribe
    if norm not in subscriber_meta:
        # Defer imports to avoid overhead on test import
        from datetime import datetime, timezone
        from uuid import uuid4
        now = datetime.now(timezone.utc)
        # RFC3339 with Z suffix
        created_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        subscriber_meta[norm] = {
            "id": str(uuid4()),
            "email": norm,
            "created_at": created_at,
            "created_ts": now.timestamp(),
        }
    return {"subscribed": True}


def unsubscribe(name: str):
    """Remove a subscriber if present. Empty names raise ValueError."""
    norm = normalize_name(name)
    if not norm:
        raise ValueError("empty name")
    existed = norm in subscribers
    if existed:
        subscribers.remove(norm)
        # Remove metadata if exists
        subscriber_meta.pop(norm, None)
    return {"unsubscribed": bool(existed)}


def is_subscribed(name: str) -> bool:
    norm = normalize_name(name)
    return bool(norm) and norm in subscribers


def list_subscribers():
    """Return a sorted list of current subscribers for stable output."""
    return sorted(subscribers)


def list_records_raw():
    """Return raw record dicts for current subscribers.
    Records include internal field created_ts for sorting; caller should not expose it.
    """
    items = []
    for name in subscribers:
        rec = subscriber_meta.get(name)
        if rec:
            items.append(rec)
        else:
            # Backfill record if missing for any reason
            from datetime import datetime, timezone
            from uuid import uuid4
            now = datetime.now(timezone.utc)
            created_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
            rec = {
                "id": str(uuid4()),
                "email": name,
                "created_at": created_at,
                "created_ts": now.timestamp(),
            }
            subscriber_meta[name] = rec
            items.append(rec)
    return items
