
import hashlib


class ContextEngine:
    """Manage reusable cybersecurity analysis context."""

    def __init__(self, max_items=50):
        self.cache = {}
        self.max_items = max_items

    def _make_key(self, question, context):
        """Generate a unique key for question and context."""
        content = (
            question.strip().lower()
            + "|"
            + context.strip().lower()
        )

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    def get_context(self, question, context):
        """Retrieve a previously generated answer."""
        key = self._make_key(question, context)
        return self.cache.get(key)

    def save_context(self, question, context, answer):
        """Store a generated answer for future reuse."""
        key = self._make_key(question, context)

        if key not in self.cache and len(self.cache) >= self.max_items:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = answer

    def clear_context(self):
        """Clear stored context."""
        self.cache.clear()

    def get_cache_size(self):
        """Return number of stored answers."""
        return len(self.cache)
