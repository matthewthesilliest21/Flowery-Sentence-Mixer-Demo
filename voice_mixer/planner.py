from .models import Plan, PlanStep
from .phonetics import phones_for_word
from .text import normalize, words
from pathlib import Path

BONUS = {"phrase": 100, "word": 60, "syllable": 35, "phone": 20, "character": 8}
PREFERRED_WORD_SOURCES = {"you": "im_only_trying_to_help_you"}

def _score(target, f):
    t, x = normalize(target), normalize(f.text)
    # Phrase fragments are rendered as their full timestamped audio span.
    # A substring match would therefore play unrelated neighboring words too.
    if t != x: return -10**9
    ratio = min(len(t), len(x)) / max(1, max(len(t), len(x)))
    return BONUS.get(f.kind, 0) + 100*ratio + 20*f.confidence - (10 if f.duration < .08 else 0)

def _word_candidates(word, fragments):
    out=[]; target_phones=phones_for_word(word)
    for f in fragments:
        # Word-level matches must be exact. Substring scoring can turn "all"
        # into a match for "falling", or a character into a whole word.
        exact = normalize(word) == normalize(f.text)
        if f.kind == "word" and exact:
            s=_score(word,f)
            reason=f"{f.kind} match"
            preferred_source=PREFERRED_WORD_SOURCES.get(normalize(word))
            if preferred_source and preferred_source in Path(f.source).stem.casefold():
                s += 35
                reason="preferred source match"
            out.append((s,f,reason))
        elif f.kind == "character" and len(normalize(word)) == 1 and exact:
            s=_score(word,f)
            out.append((s,f,f"{f.kind} match"))
        if f.kind == "phone" and target_phones and f.phones:
            if tuple(p.rstrip("012").upper() for p in f.phones) == target_phones:
                out.append((95+20*f.confidence,f,"phoneme sequence match"))
    return sorted(out, key=lambda z:z[0], reverse=True)

def _assemble_from_phones(word, fragments):
    """Choose one aligned audio fragment for every phone in a new word."""
    target = phones_for_word(word)
    if not target:
        return None

    candidates = {}
    for fragment in fragments:
        if fragment.kind != "phone" or fragment.duration <= 0:
            continue
        labels = fragment.phones or (fragment.text,)
        if len(labels) != 1:
            continue
        phone = labels[0].rstrip("012").upper()
        candidates.setdefault(phone, []).append(fragment)
    if any(phone not in candidates for phone in target):
        return None

    # Dynamic programming prefers phone runs that are adjacent in the same
    # recording, preserving natural coarticulation whenever such a run exists.
    states = []
    for index, phone in enumerate(target):
        next_states = []
        for fragment in candidates[phone]:
            base = 20 * fragment.confidence + min(fragment.duration, .12) * 20
            if fragment.left_context or fragment.right_context:
                at_word_start = fragment.left_context == "^"
                at_word_end = fragment.right_context == "$"
                if index == 0:
                    base += 7 if at_word_start else -3
                elif at_word_start:
                    base -= 8
                if index == len(target) - 1:
                    base += 12 if at_word_end else -6
                elif at_word_end:
                    base -= 18
            if index == 0:
                next_states.append((base, [fragment]))
                continue

            best_state = None
            for prior_score, prior_path in states:
                previous = prior_path[-1]
                same_source = Path(previous.source).resolve() == Path(fragment.source).resolve()
                gap = fragment.start - previous.end
                if same_source and -.02 <= gap <= .04:
                    transition = 8
                elif same_source and -.08 <= gap <= .12:
                    transition = 3
                elif same_source:
                    transition = 0
                else:
                    transition = -3
                candidate_state = (prior_score + base + transition, prior_path + [fragment])
                if best_state is None or candidate_state[0] > best_state[0]:
                    best_state = candidate_state
            if best_state is not None:
                next_states.append(best_state)
        states = next_states
    if not states:
        return None
    score, path = max(states, key=lambda state: state[0])
    return path, score / len(target)

def _decompose_suffix(word, fragments):
    """Return (stem_fragment, suffix_fragment) for common possessive/plural endings."""
    w=normalize(word)
    suffix=None; stem=None
    if w.endswith("'s") and len(w)>2:
        stem=w[:-2]; suffix_type="possessive"
    elif w.endswith("s") and len(w)>2:
        stem=w[:-1]; suffix_type="plural"
    else:
        return None
    stem_candidates=_word_candidates(stem, fragments)
    if not stem_candidates: return None
    stem_score, stem_frag, _=stem_candidates[0]
    target=phones_for_word(w)
    # CMUdict may not contain apostrophe spellings. For common English possessives
    # infer the suffix phone from the stem's final phone: voiced -> Z, voiceless -> S.
    if target:
        suffix_phone=target[-1]
    else:
        stem_phones=phones_for_word(stem)
        if stem_phones:
            voiced={"B","D","G","V","DH","Z","ZH","JH","M","N","NG","L","R","W","Y"}
            suffix_phone="Z" if stem_phones[-1].rstrip("012") in voiced else "S"
        else:
            # Lightweight fallback when CMUdict isn't installed. This is only
            # a heuristic; the real AI path should use pronunciation data.
            last=stem[-1:]
            suffix_phone="Z" if last in {"b","d","g","v","m","n","l","r","w","y"} else "S"
    for f in fragments:
        if f.kind=="phone" and len(f.phones)==1 and f.phones[0].rstrip("012")==suffix_phone.rstrip("012"):
            return stem, stem_frag, stem_score, f, suffix_type
    return None

def plan_sentence(target, fragments):
    units=words(target); steps=[]; notes=[]; i=0
    while i < len(units):
        best=None
        for n in range(min(4,len(units)-i),1,-1):
            phrase=" ".join(units[i:i+n])
            for f in fragments:
                if f.kind != "phrase": continue
                s=_score(phrase,f)
                if best is None or s>best[2]: best=(phrase,f,s)
            if best and best[2] > 180: break
        if best and best[2] > 135:
            phrase,f,s=best
            steps.append(PlanStep(phrase,f,s,"preferred multi-word phrase")); i+=len(phrase.split()); continue

        word=units[i]
        candidates=_word_candidates(word,fragments)
        if candidates:
            s,f,reason=candidates[0]
            # If the only match is a tiny phone fragment, do not use it when a
            # stem + suffix construction is available.
            suffix=_decompose_suffix(word,fragments)
            if suffix and (f.kind=="phone" or normalize(f.text) != normalize(word)):
                stem,stem_frag,stem_score,suf_frag,suffix_type=suffix
                steps.append(PlanStep(stem,stem_frag,stem_score,f"stem of {suffix_type}"))
                steps.append(PlanStep(word[len(stem):] or "'s",suf_frag,72+20*suf_frag.confidence,f"reused final phoneme for {suffix_type}"))
            else:
                steps.append(PlanStep(word,f,s,reason))
            i+=1; continue

        suffix=_decompose_suffix(word,fragments)
        if suffix:
            stem,stem_frag,stem_score,suf_frag,suffix_type=suffix
            steps.append(PlanStep(stem,stem_frag,stem_score,f"stem of {suffix_type}"))
            steps.append(PlanStep(word[len(stem):] or "'s",suf_frag,72+20*suf_frag.confidence,f"reused final phoneme for {suffix_type}"))
            i+=1; continue

        phone_path = _assemble_from_phones(word, fragments)
        if phone_path:
            parts, score = phone_path
            steps.append(PlanStep(word,parts[0],score,f"assembled from {len(parts)} phonemes",parts))
            i+=1; continue

        steps.append(PlanStep(word,None,-50,"not found; no generation will be used"))
        notes.append(f"No existing audio was found for {word!r}. The engine will not invent the missing voice.")
        i+=1
    return Plan(target,steps,sum(s.score for s in steps),notes)
