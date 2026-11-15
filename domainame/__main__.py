"""CLI: python -m domainame [options].

Examples:
    python -m domainame                       # one random label: daring-heron
    python -m domainame -n 5 --style blend    # daringeron, quiequasar, ...
    python -m domainame --env dev --zone lab.internal
    python -m domainame --validate keen-falcon
    python -m domainame --validate-fqdn dev.keen-falcon.example.com
    python -m domainame --sanitize "Keen Falcon_2"
"""

from __future__ import annotations

import argparse
import random
import sys

from .generator import (
    LABEL_STYLES,
    generate_domain_label,
    generate_fqdn,
    generate_n,
    sanitize_domain_label,
    validate_domain_label,
    validate_fqdn,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="domainame",
        description="Generate Docker-style adjective-noun domain labels.",
    )
    parser.add_argument("-n", "--count", type=int, default=1,
                        help="how many names to generate (default: 1)")
    parser.add_argument("--style", choices=LABEL_STYLES, default="hyphen",
                        help="hyphen: daring-heron; fuse: daringheron; "
                             "blend: daringeron (default: hyphen)")
    parser.add_argument("--unique", action="store_true",
                        help="append a short code for CI sandboxes")
    parser.add_argument("--env", help="environment label placed to the left (dev, staging)")
    parser.add_argument("--zone", help="zone appended after the label (e.g. example.com)")
    parser.add_argument("--seed", type=int, help="random seed for reproducible runs")
    parser.add_argument("--validate", metavar="LABEL",
                        help="validate an existing label and exit")
    parser.add_argument("--validate-fqdn", metavar="NAME",
                        help="validate a full domain name (RFC 1123 syntax) and exit")
    parser.add_argument("--sanitize", metavar="NAME",
                        help="coerce arbitrary text into a DNS-safe label and exit")
    args = parser.parse_args(argv)

    if args.validate is not None:
        errors = validate_domain_label(args.validate)
        if errors:
            for err in errors:
                print(f"INVALID: {err}", file=sys.stderr)
            return 1
        print("OK")
        return 0

    if args.validate_fqdn is not None:
        errors = validate_fqdn(args.validate_fqdn)
        if errors:
            for err in errors:
                print(f"INVALID: {err}", file=sys.stderr)
            return 1
        print("OK")
        return 0

    if args.sanitize is not None:
        print(sanitize_domain_label(args.sanitize))
        return 0

    if args.zone:
        for role, value in (("env", args.env), ("zone", args.zone)):
            if not value:
                continue
            errors = validate_fqdn(value)
            if errors:
                parser.error(f"invalid --{role} {value!r}: {'; '.join(errors)}")

    rng = random.Random(args.seed) if args.seed is not None else None
    if args.zone:
        names = [generate_fqdn(zone=args.zone, env=args.env, rng=rng,
                               unique=args.unique, style=args.style)
                 for _ in range(args.count)]
    else:
        names = generate_n(args.count, rng=rng, unique=args.unique,
                           style=args.style)
    for name in names:
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
