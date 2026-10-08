try:
    import pronouncing
except Exception:
    pronouncing = None

def phones_for_word(word: str) -> tuple[str, ...]:
    if pronouncing is None:
        return ()
    variants = pronouncing.phones_for_word(word.lower())
    if not variants:
        return ()
    return tuple(p.rstrip("012") for p in variants[0].split())

