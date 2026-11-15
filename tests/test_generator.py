"""Unit tests for the domain label generator (stdlib unittest only)."""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domainame.generator import (  # noqa: E402
    ADJECTIVES,
    NOUNS,
    blend_pair,
    fuse_pair,
    generate_domain_label,
    generate_fqdn,
    generate_n,
    is_embarrassing,
    is_system_label,
    sanitize_domain_label,
    validate_domain_label,
)


class TestValidateLabel(unittest.TestCase):
    def test_valid_labels(self):
        for label in ("a", "keen-falcon", "zen2", "dev-keen-falcon-7k3m"):
            self.assertEqual(validate_domain_label(label), [], label)

    def test_rejects_underscore(self):
        self.assertTrue(validate_domain_label("keen_falcon"))

    def test_rejects_edge_hyphen(self):
        self.assertTrue(validate_domain_label("-keen"))
        self.assertTrue(validate_domain_label("keen-"))

    def test_rejects_uppercase(self):
        self.assertTrue(validate_domain_label("Keen-Falcon"))

    def test_rejects_too_long(self):
        self.assertTrue(validate_domain_label("a" * 64))

    def test_rejects_punycode_prefix(self):
        self.assertTrue(validate_domain_label("xn--keen"))

    def test_rejects_empty(self):
        self.assertTrue(validate_domain_label(""))


class TestSanitize(unittest.TestCase):
    def test_spaces_and_underscores_become_hyphens(self):
        self.assertEqual(sanitize_domain_label("Keen Falcon_2"), "keen-falcon-2")

    def test_collapses_repeats_and_trims_edges(self):
        self.assertEqual(sanitize_domain_label("  --keen---falcon-- "), "keen-falcon")

    def test_empty_falls_back(self):
        self.assertEqual(sanitize_domain_label("!!!"), "site")


class TestGenerate(unittest.TestCase):
    def test_shape_matches_adjective_noun(self):
        rng = random.Random(42)
        for _ in range(50):
            label = generate_domain_label(rng=rng)
            adjective, _, noun = label.partition("-")
            self.assertIn(adjective, ADJECTIVES)
            self.assertIn(noun, NOUNS)
            self.assertEqual(validate_domain_label(label), [])

    def test_unique_appends_code(self):
        rng = random.Random(42)
        label = generate_domain_label(rng=rng, unique=True)
        adjective, noun, code = label.split("-")
        self.assertIn(adjective, ADJECTIVES)
        self.assertIn(noun, NOUNS)
        self.assertEqual(len(code), 4)

    def test_seed_is_reproducible(self):
        a = generate_domain_label(rng=random.Random(7))
        b = generate_domain_label(rng=random.Random(7))
        self.assertEqual(a, b)

    def test_generate_n_distinct(self):
        names = generate_n(25, rng=random.Random(1), unique=True)
        self.assertEqual(len(set(names)), 25)

    def test_large_sample_is_clean(self):
        # Exhaustive-ish sweep: every pool pair plus codes stays valid.
        names = generate_n(500, rng=random.Random(99), unique=True)
        for name in names:
            self.assertEqual(validate_domain_label(name), [], name)

    def test_pools_are_96x96(self):
        self.assertEqual(len(ADJECTIVES), 96)
        self.assertEqual(len(NOUNS), 96)
        self.assertEqual(len(set(ADJECTIVES)), 96)
        self.assertEqual(len(set(NOUNS)), 96)


class TestFuse(unittest.TestCase):
    def test_overlap_merged(self):
        self.assertEqual(fuse_pair("cosmic", "comet"), "cosmicomet")
        self.assertEqual(fuse_pair("eager", "raven"), "eageraven")

    def test_no_overlap_concats(self):
        self.assertEqual(fuse_pair("daring", "heron"), "daringheron")

    def test_fuse_style_shapes(self):
        labels = generate_n(100, rng=random.Random(3), style="fuse")
        for label in labels:
            self.assertEqual(validate_domain_label(label), [], label)
            self.assertNotIn("-", label)


class TestBlend(unittest.TestCase):
    def test_owner_examples(self):
        # daring+heron: only the head crop is pronounceable.
        self.assertEqual(blend_pair("daring", "heron"), "daringeron")
        # quiet+quasar: head and tail crops both work.
        rng = random.Random(0)
        results = {blend_pair("quiet", "quasar", rng) for _ in range(50)}
        self.assertLessEqual(results, {"quietuasar", "quiequasar"})

    def test_unpronounceable_crop_returns_none(self):
        # swift+spruce: consonant after the head cut, no vowel-final crop
        # on the adjective either -- no pronounceable blend exists.
        self.assertIsNone(blend_pair("swift", "spruce"))

    def test_blend_style_never_invalid(self):
        labels = generate_n(300, rng=random.Random(11), style="blend")
        for label in labels:
            self.assertEqual(validate_domain_label(label), [], label)

    def test_unknown_style_rejected(self):
        with self.assertRaises(ValueError):
            generate_domain_label(style="spoonerism")


class TestFqdn(unittest.TestCase):
    def test_env_label_goes_left(self):
        fqdn = generate_fqdn(zone="example.com", label="keen-falcon", env="dev")
        self.assertEqual(fqdn, "dev.keen-falcon.example.com")

    def test_prod_has_no_env(self):
        fqdn = generate_fqdn(zone="example.com", label="keen-falcon")
        self.assertEqual(fqdn, "keen-falcon.example.com")

    def test_invalid_label_raises(self):
        with self.assertRaises(ValueError):
            generate_fqdn(zone="example.com", label="keen_falcon")


class TestFilters(unittest.TestCase):
    def test_word_pools_are_clean(self):
        for word in (*ADJECTIVES, *NOUNS):
            self.assertFalse(is_embarrassing(word), word)

    def test_embarrassing_detection(self):
        self.assertTrue(is_embarrassing("xshitx"))
        self.assertFalse(is_embarrassing("keen-falcon"))

    def test_system_labels(self):
        self.assertTrue(is_system_label("www"))
        self.assertFalse(is_system_label("keen-falcon"))


if __name__ == "__main__":
    unittest.main()
