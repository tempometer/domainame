# domainame

Docker-style name generator adapted for DNS: the same adjective–noun pairs
Docker gives its containers, but following RFC 1123 rules for domain labels.

**[Українська версія](README.ua.md)**

## The naming scheme

```
[env.]<adjective>-<noun>[-<code>][.zone]

styles (--style):
  hyphen (canonical): daring-heron, quiet-quasar, calm-badger
  fuse:               daringheron, cosmicomet        (glued, overlap merged)
  blend:              daringeron, quiequasar         (glued, cropped)

FQDN examples:
  daring-heron.example.com
  dev.quiet-quasar.lab.internal
  crisp-heron-7k3m.example.com      <- code is an option for CI sandboxes only
```

- **adjective-noun** — the same pair Docker uses (`clever_liskov`), but joined
  with a **hyphen**: underscores are illegal in hostnames (RFC 1123); `_` lives
  only in service records (`_dmarc`, `_acme-challenge`).
- **No codes by default.** The word pools give 96×96 = **9,216 base pairs**;
  with fuse/blend variants — tens of thousands of labels. A code suffix stays
  an option (`--unique`) for CI sandboxes where collisions are unacceptable;
  in human-facing URLs it looks "suspicious" and is not needed.
- **env is its own label to the left** (`dev.`, `staging.`), not an inner
  prefix: the environment is routing policy, not part of the name.
  Prod = no env label.

## Word fusion (fuse / blend)

Two single-label modes:

- **fuse** — honest gluing that absorbs any suffix/prefix overlap:
  `cosmic+comet → cosmicomet`, `eager+raven → eageraven`; with no overlap it
  is plain concatenation, `daring+heron → daringheron`.
- **blend** — a cropped portmanteau, the way a person would shorten the
  pronunciation:
  - drop the noun's head: `daring+heron → daringeron`, `quiet+quasar → quietuasar`
  - drop the adjective's tail: `quiet+quasar → quiequasar`

Phonotactic rules for the blend seam (so it reads as one word):

1. The cropped edge must open or close with a vowel: `heron → eron` is fine,
   `spruce → pruce` is not (consonant cluster).
2. The seam alternates vowel/consonant (CV or VC): `daringeron` (g|e) is fine,
   `snowyuartz` (y|u — two vowels) is rejected.
3. Length ≤ 13, no three identical letters in a row, no embarrassing
   substrings (gluing without a hyphen reopens the classic `pen_island`
   problem — that is why the full label is checked as a whole).
4. If no clean fusion exists, fall back honestly to the hyphen
   (`swift+spruce → swift-spruce`).

## How a domain differs from a container

| | Container (Docker) | Domain (here) |
|---|---|---|
| Joiner | `_` | `-` (RFC 1123 forbids `_`) |
| Uniqueness | randomness | large pair pool + blends (code is an option) |
| Limits | — | label ≤ 63 bytes, FQDN ≤ 253 bytes |
| env | part of the name | separate label to the left |
| Filters | — | `xn--`, system labels (`www`, `api`…), embarrassing, blend seam |
| Lifetime | hours | weeks to years |

The hyphen joiner in hyphen mode is **safer than concatenation**: the classic
`pen_island → penisland` problem is impossible here — words are never glued
together. The `EMBARRASSING_SUBSTRINGS` filter additionally checks the full
label.

## Acronyms — yes, you can

DNS labels do not care what a word looks like: `abc`, `nasa`, `s3` are all
legal, as long as they are `[a-z0-9-]` and at most 63 bytes. Practical rules:

1. **An acronym is for durable entities** (a service, a team); adjective-noun
   is for random/personal ones (a dev label, a preview, a pet project).
   Do not mix the two in one purpose.
2. An acronym is ≤ 5–6 letters and pronounceable as a word (`sonar` yes,
   `xq7z2k` no).
3. A dot is more structural than a hyphen: `api.acme.example.com`, not
   `acme-api`.
4. Never generate a production name randomly — it has to be predictable.

## What already exists (and why roll our own)

- [docker/docker namesgenerator](https://pkg.go.dev/github.com/docker/docker/pkg/namesgenerator) —
  the canonical Go package from Docker; officially "frozen", words are never
  added.
- [haikunator](https://github.com/usmanbashir/haikunater) — Heroku-style
  `wispy-frost-8542`, with dozens of ports across languages.
- [beasteers/randomname](https://github.com/beasteers/randomname) (Python),
  [unique-names-generator](https://www.npmjs.com/package/unique-names-generator) (npm) —
  dictionary-based name generators.
- Portmanteau: [trishume/portmanteau](https://github.com/trishume/portmanteau)
  (Rust, graph search), [qm3jp/portmanteau-generator](https://github.com/qm3jp/portmanteau-generator) (Python).

None of them apply **domain** rules: hyphen instead of `_`, the `xn--` ban,
system labels, the embarrassing filter, seam phonotactics, the env label on
the left. Hence our own — a thin layer over the same idea.

## API

```python
from domainame import generate_domain_label, generate_fqdn, blend_pair, validate_domain_label, validate_fqdn

generate_domain_label()                              # 'keen-falcon'
generate_domain_label(style="fuse")                  # 'cosmicomet'
generate_domain_label(style="blend")                 # 'daringeron'
blend_pair("quiet", "quasar")                        # 'quietuasar' | 'quiequasar'
generate_fqdn(zone="example.com", env="dev")         # 'dev.brisk-aurora.example.com'
validate_domain_label("keen_falcon")                 # ['label must be lowercase [a-z0-9-]...']
validate_fqdn("dev.keen-falcon.example.com")         # [] — RFC 1123 syntax, no generator policies
```

## CLI

```
python -m domainame                          # one name: daring-heron
python -m domainame -n 5 --style blend       # daringeron, quiequasar, ...
python -m domainame --style fuse --env dev --zone lab.internal
python -m domainame --validate keen-falcon   # OK / INVALID
python -m domainame --validate-fqdn dev.keen-falcon.example.com   # OK / INVALID for a full FQDN
python -m domainame --sanitize "Keen Falcon_2"   # keen-falcon-2
```

## Tests

```
python -m unittest discover -s tests -t .
```

## Extending the word pools

Add words to `domainame/words.py`: short (≤8), lowercase, no hyphens inside,
no substrings from the `EMBARRASSING_SUBSTRINGS` list in
`domainame/generator.py`. Vowel-initial nouns (`otter`, `acorn`) and
vowel-final adjectives (`quiet`, `tawny`) are the raw material for blends —
the more of them, the more often a blend finds a clean seam. The
`test_word_pools_are_clean` test catches slip-ups.
