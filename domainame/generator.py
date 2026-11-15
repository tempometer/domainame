"""Docker-style domain label generator.

Docker's adjective-noun container names, adapted to DNS rules.

Why the differences from the container-name scheme:

- DNS labels (RFC 1123) allow only [a-z0-9-] and must not start or end with
  a hyphen: ``_`` is illegal in hostnames, so the join character is ``-``.
- Underscores exist only in special underscore-prefixed records
  (_dmarc, _acme-challenge, DKIM) and are never produced here.
- A container lives for hours, so a timestamp in the name is fine; a domain
  (even a dev one) outlives it, so uniqueness comes from a short base32-ish
  code instead of a date.
- A leading ``xn--`` means punycode; we refuse it so tooling never mistakes
  a generated label for an IDN.
- Environments are separate labels to the LEFT of the name
  (``env.name.zone``), because env is routing policy, not identity.
"""

from __future__ import annotations

import random
import re
from typing import List, Optional

from .words import ADJECTIVES, NOUNS

#: Uniqueness code alphabet: no 0/1/o/l (visual collisions), no i/u
#: (codes must never spell words).
CODE_ALPHABET = "23456789abcdefghjkmnpqrstvwxyz"

MAX_LABEL_LEN = 63
MAX_FQDN_LEN = 253

#: Longest acceptable single-word blend (daringeron, quiequasar land ~10).
MAX_BLEND_LEN = 13

#: y counts as a vowel here: it carries a vowel sound in tawny/quarry.
VOWELS = "aeiouy"

LABEL_STYLES = ("hyphen", "fuse", "blend")

#: RFC 1123 hostname label: starts/ends alphanumeric, [a-z0-9-] inside.
LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")

PUNYCODE_PREFIX = "xn--"

#: Labels that belong to infrastructure, not to random names. Generating
#: one of these would shadow a well-known service name.
SYSTEM_LABELS = frozenset(
    {
        "admin",
        "api",
        "cdn",
        "dev",
        "ftp",
        "imap",
        "mail",
        "ns",
        "ns1",
        "ns2",
        "pop",
        "smtp",
        "staging",
        "webmail",
        "www",
    }
)

#: Substrings rejected anywhere in a full label. Kept minimal on purpose:
#: the hyphen join already prevents cross-word mashups (the classic
#: pen-island problem); this list only guards the word pools themselves and
#: random codes. Every entry must be checked against words.py before the
#: pools grow, or valid words (titan, title) would be rejected.
EMBARRASSING_SUBSTRINGS = (
    "anal",
    "anus",
    "arse",
    "ass",
    "boob",
    "cock",
    "coon",
    "cum",
    "cunt",
    "dick",
    "fag",
    "fart",
    "fuck",
    "gook",
    "homo",
    "jizz",
    "kike",
    "kkk",
    "muff",
    "nazi",
    "nigg",
    "paki",
    "penis",
    "piss",
    "porn",
    "prick",
    "pube",
    "rape",
    "scum",
    "semen",
    "sex",
    "shit",
    "slut",
    "spic",
    "tadg",
    "twat",
    "vag",
    "wank",
    "whore",
    "wog",
)


def sanitize_domain_label(name: str) -> str:
    """Coerce arbitrary text into a DNS-safe label.

    Collapses runs of unsafe characters to hyphens instead of underscores
    and trims edge hyphens (a label may not start or end with one).
    """
    safe = re.sub(r"[^a-z0-9-]+", "-", (name or "").strip().lower())
    safe = re.sub(r"-{2,}", "-", safe).strip("-")
    return safe[:MAX_LABEL_LEN].rstrip("-") or "site"


def validate_domain_label(label: str) -> List[str]:
    """Return a list of RFC 1123 / policy violations; empty means valid."""
    errors: List[str] = []
    if not label:
        return ["label is empty"]
    if len(label) > MAX_LABEL_LEN:
        errors.append(f"label longer than {MAX_LABEL_LEN} bytes")
    if not LABEL_RE.match(label):
        errors.append(
            "label must be lowercase [a-z0-9-], starting and ending "
            "with a letter or digit"
        )
    if label.startswith(PUNYCODE_PREFIX):
        errors.append("label uses reserved punycode prefix xn--")
    if is_embarrassing(label):
        errors.append("label contains a blocked substring")
    return errors


def is_embarrassing(label: str) -> bool:
    """True if any blocked substring appears anywhere in the label."""
    lowered = (label or "").lower()
    return any(bad in lowered for bad in EMBARRASSING_SUBSTRINGS)


def is_system_label(label: str) -> bool:
    """True if the label would shadow a well-known service name."""
    return (label or "").lower() in SYSTEM_LABELS


def validate_fqdn(name: str) -> List[str]:
    """Syntax-only RFC 1123 validation of a full domain name; [] = valid.

    Each dot-separated label must be 1-63 bytes of lowercase [a-z0-9-]
    and must not start or end with a hyphen. Exactly one trailing dot is
    accepted and excluded from the total-length count.

    Deliberately policy-free: punycode, system-label and embarrassing
    substring rules constrain GENERATED names, not arbitrary zones a user
    already owns (``xn--`` is legal IDN; ``sussex.ac.uk`` is a real zone).
    Per-label error messages quote the offending label so the user can
    see which part is wrong.
    """
    errors: List[str] = []
    if not name:
        return ["fqdn is empty"]
    stripped = name[:-1] if name.endswith(".") else name
    for label in stripped.split("."):
        if not label:
            errors.append(f"label {label!r} is empty")
        elif len(label) > MAX_LABEL_LEN:
            errors.append(f"label {label!r} longer than {MAX_LABEL_LEN} bytes")
        elif not LABEL_RE.match(label):
            errors.append(
                f"label {label!r} must be lowercase [a-z0-9-], starting "
                "and ending with a letter or digit"
            )
    if len(stripped) > MAX_FQDN_LEN:
        errors.append(
            f"fqdn longer than {MAX_FQDN_LEN} bytes (excluding trailing "
            f"dot): {len(stripped)}"
        )
    return errors


def generate_code(length: int = 4, rng: Optional[random.Random] = None) -> str:
    """Short uniqueness code from a word-safe alphabet (default ~923k)."""
    rng = rng or random
    return "".join(rng.choice(CODE_ALPHABET) for _ in range(length))


def _has_triple_run(text: str) -> bool:
    """True if three identical characters appear in a row (aaab seams)."""
    return any(text[i] == text[i + 1] == text[i + 2] for i in range(len(text) - 2))


def _max_overlap(adjective: str, noun: str) -> int:
    """Longest k where the adjective's suffix equals the noun's prefix."""
    best = 0
    for k in range(1, min(len(adjective), len(noun)) + 1):
        if adjective[-k:] == noun[:k]:
            best = k
    return best


def fuse_pair(adjective: str, noun: str) -> str:
    """Glue a pair into one word, merging any suffix/prefix overlap.

    cosmic+comet -> cosmicomet, eager+raven -> eageraven,
    daring+heron -> daringheron (no overlap, plain concat).
    """
    return adjective + noun[_max_overlap(adjective, noun):]


def _seam_is_pronounceable(left: str, right: str) -> bool:
    """True when the crop seam alternates vowel/consonant (CV or VC).

    Two vowels in a row at the seam (snowy+quartz -> snowyuartz) read as
    an awkward hiatus, so reject them. CC seams are impossible under the
    crop rules that build the candidates.
    """
    return not (left[-1] in VOWELS and right[0] in VOWELS)


def blend_pair(
    adjective: str, noun: str, rng: Optional[random.Random] = None
) -> Optional[str]:
    """Blend a pair the way a human would crop it (portmanteau rules).

    daring+heron   -> daringeron  (drop the noun's head consonant)
    quiet+quasar   -> quietuasar / quiequasar (head or tail crop)
    Returns None when no crop keeps the seam pronounceable; the caller
    then falls back to another style.
    """
    rng = rng or random
    candidates = []
    # Head-drop: only when the noun keeps a vowel right after the cut,
    # so the seam stays pronounceable (heron -> eron, quasar -> uasar).
    if len(noun) > 2 and noun[0] not in VOWELS and noun[1] in VOWELS:
        candidates.append((adjective, noun[1:]))
    # Tail-drop: only when the adjective ends on a vowel+consonant pair
    # (quiet -> quie), so the crop does not cluster consonants.
    if len(adjective) > 2 and adjective[-1] not in VOWELS and adjective[-2] in VOWELS:
        candidates.append((adjective[:-1], noun))
    candidates = [
        left + right
        for left, right in candidates
        if len(left) + len(right) <= MAX_BLEND_LEN
        and _seam_is_pronounceable(left, right)
        and not _has_triple_run(left + right)
        and not is_embarrassing(left + right)
    ]
    if not candidates:
        return None
    return rng.choice(sorted(candidates))


def generate_domain_label(
    rng: Optional[random.Random] = None,
    style: str = "hyphen",
    unique: bool = False,
    code_length: int = 4,
    max_attempts: int = 64,
) -> str:
    """Generate a Docker-style domain label from an adjective-noun pair.

    Styles:
      - "hyphen": daring-heron (canonical, like Docker)
      - "fuse":   daringheron / cosmicomet (single word, overlaps merged)
      - "blend":  daringeron / quiequasar (cropped portmanteau; falls back
                  to hyphen when no crop stays pronounceable)

    With ``unique=True`` appends ``-<code>`` for CI sandboxes where labels
    must never collide across regenerations (codes look "suspicious" in
    human-facing URLs -- prefer the 9k+ pair pool instead).
    Retries on embarrassing combinations (blocked substring inside a random
    code, pool word added later without vetting, etc.).
    """
    if style not in LABEL_STYLES:
        raise ValueError(f"unknown style {style!r}; expected one of {LABEL_STYLES}")
    rng = rng or random
    for _ in range(max_attempts):
        adjective = rng.choice(ADJECTIVES)
        noun = rng.choice(NOUNS)
        if style == "hyphen":
            label = f"{adjective}-{noun}"
        elif style == "fuse":
            label = fuse_pair(adjective, noun)
        else:
            label = blend_pair(adjective, noun, rng) or f"{adjective}-{noun}"
        if unique:
            label = f"{label}-{generate_code(code_length, rng)}"
        if validate_domain_label(label) or is_system_label(label):
            continue
        return label
    raise RuntimeError(
        f"could not generate a clean label in {max_attempts} attempts"
    )


def generate_fqdn(
    zone: str = "example.com",
    label: Optional[str] = None,
    env: Optional[str] = None,
    rng: Optional[random.Random] = None,
    unique: bool = False,
    style: str = "hyphen",
) -> str:
    """Build ``[env.]adjective-noun.zone`` from parts.

    ``env`` becomes its own label to the left of the name (canonical
    routing position). Production is the absence of an env label.
    Non-empty ``env`` and ``zone`` must be syntactically valid domain
    names (``validate_fqdn``); the generated/supplied ``label`` keeps its
    own policy check.
    """
    if label is None:
        label = generate_domain_label(rng=rng, unique=unique, style=style)
    elif validate_domain_label(label):
        raise ValueError(f"invalid label {label!r}: {validate_domain_label(label)}")
    for role, value in (("env", env), ("zone", zone)):
        if value:
            errors = validate_fqdn(value)
            if errors:
                raise ValueError(f"invalid {role} {value!r}: {errors}")
    parts = [p for p in (env, label, zone) if p]
    fqdn = ".".join(parts)
    if len(fqdn) > MAX_FQDN_LEN:
        raise ValueError(f"fqdn exceeds {MAX_FQDN_LEN} bytes: {fqdn}")
    return fqdn


def generate_n(
    n: int = 1,
    rng: Optional[random.Random] = None,
    unique: bool = False,
    zone: Optional[str] = None,
    env: Optional[str] = None,
    style: str = "hyphen",
) -> List[str]:
    """Generate n distinct labels (or FQDNs when a zone is given)."""
    rng = rng or random
    out: List[str] = []
    seen = set()
    while len(out) < n:
        item = generate_domain_label(rng=rng, unique=unique, style=style)
        if zone is not None:
            item = generate_fqdn(zone=zone, label=item, env=env)
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
