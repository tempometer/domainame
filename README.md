# domainame

Генератор імен у Docker-стайлі, адаптований під DNS: та сама пара
«прикметник-іменник», що й у контейнерів Docker, але з правилами RFC 1123
для доменних міток.

## Канон схеми

```
[env.]<adjective>-<noun>[-<code>][.zone]

стилі (—-style):
  hyphen (канон):  daring-heron, quiet-quasar, calm-badger
  fuse:            daringheron, cosmicomet        (злиття з поглинанням overlap)
  blend:           daringeron, quiequasar         (злиття з обрізанням)

приклади FQDN:
  daring-heron.example.com
  dev.quiet-quasar.lab.internal
  crisp-heron-7k3m.example.com      ← код — лише опція для CI-пісочниць
```

- **adjective-noun** — та сама пара, що в Docker (`clever_liskov`), але через
  **дефіс**: підкреслення в іменах хостів заборонене (RFC 1123), `_` живе лише
  в службових записах (`_dmarc`, `_acme-challenge`).
- **Без кодів за замовчуванням.** Словники 96×96 = **9 216 базових пар**, з
  fuse/blend-варіантами — десятки тисяч міток. Код-суфікс залишено як опцію
  (`--unique`) для CI-пісочниць, де колізії неприпустимі; в людських URL він
  виглядає «підозріливо» і не потрібен.
- **env зліва окремою міткою** (`dev.`, `staging.`), а не префіксом всередині:
  середовище — це політика маршрутизації, не частина імені. Prod = без env-мітки.

## Злиття слів (fuse / blend)

Два режими одиночної мітки:

- **fuse** — чесне склеювання з поглинанням збігу суфіікса/префікса:
  `cosmic+comet → cosmicomet`, `eager+raven → eageraven`, без збігу —
  конкатенація `daring+heron → daringheron`.
- **blend** — портманто з обрізанням, як людина скорає вимову:
  - обрізати голову іменника: `daring+heron → daringeron`, `quiet+quasar → quietuasar`
  - обрізати хвіст прикметника: `quiet+quasar → quiequasar`

Фонотактичні правила blend (щоб шов читався):

1. Обрізаний край має відкривати/закривати голосну: `heron → eron` можна,
   `spruce → pruce` ні (приголосний кластер).
2. Шов чергує голосні/приголосні (CV або VC): `daringeron` (g|e) ок,
   `snowyuartz` (y|u — дві голосні) відкидається.
3. Довжина ≤ 13, без трьох однакових літер підряд, без embarrassing-підрядників
   (шов без дефісу знову відкриває проблему `pen_island` — тому повна мітка
   перевіряється целиком).
4. Якщо чистого злиття нема — чесний fallback на дефіс (`swift+spruce → swift-spruce`).

## Чим домен відрізняється від контейнера

| | Контейнер (Docker) | Домен (тут) |
|---|---|---|
| З'єднувач | `_` | `-` (RFC 1123 забороняє `_`) |
| Унікальність | випадковість | великий пул пар + blend (код — опція) |
| Ліміти | — | мітка ≤ 63 б, FQDN ≤ 253 б |
| env | частина імені | окрема мітка зліва |
| Фільтри | — | `xn--`, системні (`www`, `api`…), embarrassing, шов blend |
| Життя | години | тижні-роки |

Дефіс як з'єднувач у hyphen-режимі **безпечніший за конкатенацію**: класична
проблема `pen_island → penisland` тут неможлива — слова ніколи не склеюються.
Фільтр `EMBARRASSING_SUBSTRINGS` додатково перевіряє повну мітку.

## Акроніми — так, можна

DNS-мітці байдуже, як слово виглядає: `abc`, `nasa`, `s3` — усе легальне,
поки `[a-z0-9-]` і не понад 63 байти. Практичні правила:

1. **Акронім — для стійких сутностей** (сервіс, команда), adjective-noun — для
   випадкових/особистих (dev-мітка, preview, pet-проєкт). Не мішай у одну мету.
2. Акронім ≤ 5–6 літер, вимовний як слово (`sonar` ок, `xq7z2k` — ні).
3. Крапка структурніша за дефіс: `api.acme.example.com`, а не `acme-api`.
4. Продакшн-ім'я не генеруй випадково — воно має бути передбачуваним.

## Що вже є на ринку (і чому свій)

- [docker/docker namesgenerator](https://pkg.go.dev/github.com/docker/docker/pkg/namesgenerator) —
  канонічний Go-пакет Docker; офіційно «заморожений», слів не додають.
- [haikunator](https://github.com/usmanbashir/haikunator) — Heroku-стайл
  `wispy-frost-8542`, десятки портів на різні мови.
- [beasteers/randomname](https://github.com/beasteers/randomname) (Python),
  [unique-names-generator](https://www.npmjs.com/package/unique-names-generator) (npm) —
  генератори словникових імен із словниками.
- Портманто: [trishume/portmanteau](https://github.com/trishume/portmanteau)
  (Rust, graph search), [qm3jp/portmanteau-generator](https://github.com/qm3jp/portmanteau-generator) (Python).

Ніхто з них не робить саме **доменних** правил: дефіс замість `_`, заборона
`xn--`, системні мітки, embarrassing-фільтр, фонотактика шва, env-мітка зліва.
Тому свій — тонкий шар над тією ж ідеєю.

## API

```python
from domainame import generate_domain_label, generate_fqdn, blend_pair, validate_domain_label

generate_domain_label()                              # 'keen-falcon'
generate_domain_label(style="fuse")                  # 'cosmicomet'
generate_domain_label(style="blend")                 # 'daringeron'
blend_pair("quiet", "quasar")                        # 'quietuasar' | 'quiequasar'
generate_fqdn(zone="example.com", env="dev")         # 'dev.brisk-aurora.example.com'
validate_domain_label("keen_falcon")                 # ['label must be lowercase [a-z0-9-]...']
```

## CLI

```
python -m domainame                          # одне ім'я: daring-heron
python -m domainame -n 5 --style blend       # daringeron, quiequasar, ...
python -m domainame --style fuse --env dev --zone lab.internal
python -m domainame --validate keen-falcon   # OK / INVALID
python -m domainame --sanitize "Keen Falcon_2"   # keen-falcon-2
```

## Тести

```
python -m unittest discover -s tests -t .
```

## Як розширювати словники

Слова додавай у `domainame/words.py`: короткі (≤8), нижній регістр, без дефісів
усередині, без підрядків зі списку `EMBARRASSING_SUBSTRINGS` у
`domainame/generator.py`. Голосні-на-старті іменники (`otter`, `acorn`) і
голосні-на-фініші прикметники (`quiet`, `tawny`) — сировина для blend-ів: чим
їх більше, тим частіше blend знаходить чистий шов. Тест `test_word_pools_are_clean`
ловить проколи.
