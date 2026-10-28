subscribers = set()


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
    return {"subscribed": True}


def unsubscribe(name: str):
    """Remove a subscriber if present. Empty names raise ValueError."""
    norm = normalize_name(name)
    if not norm:
        raise ValueError("empty name")
    existed = norm in subscribers
    if existed:
        subscribers.remove(norm)
    return {"unsubscribed": bool(existed)}


def is_subscribed(name: str) -> bool:
    norm = normalize_name(name)
    return bool(norm) and norm in subscribers


def list_subscribers():
    """Return a sorted list of current subscribers for stable output."""
    return sorted(subscribers)
