"""Exact source checks. A bad model quote is failure, not negative candidate evidence."""
def require_quotes(quotes: list[str], source: str, *, required: bool = True) -> None:
    if required and not quotes:
        raise ValueError('missing_source_quote')
    if any(not q.strip() or q not in source for q in quotes):
        raise ValueError('invalid_source_quote')
