"""domainame: Docker-style naming for DNS labels and hostnames."""

from .generator import (
    CODE_ALPHABET,
    LABEL_STYLES,
    blend_pair,
    fuse_pair,
    generate_code,
    generate_domain_label,
    generate_fqdn,
    generate_n,
    is_embarrassing,
    is_system_label,
    sanitize_domain_label,
    validate_domain_label,
    validate_fqdn,
)
from .words import ADJECTIVES, NOUNS

__all__ = [
    "ADJECTIVES",
    "CODE_ALPHABET",
    "LABEL_STYLES",
    "NOUNS",
    "blend_pair",
    "fuse_pair",
    "generate_code",
    "generate_domain_label",
    "generate_fqdn",
    "generate_n",
    "is_embarrassing",
    "is_system_label",
    "sanitize_domain_label",
    "validate_domain_label",
    "validate_fqdn",
]
