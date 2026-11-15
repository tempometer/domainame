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
    validate_fqdn,
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

    def test_rejects_trailing_or_inner_newline(self):
        # `$` alone matches before a trailing \n; only fullmatch catches it.
        for label in ("keen-falcon\n", "keen\nfalcon", "keen-falcon\n\n"):
            self.assertTrue(validate_domain_label(label), repr(label))


class TestValidateFqdn(unittest.TestCase):
    def test_valid_fqdns(self):
        for name in ("keen-falcon.example.com", "dev.quiet-quasar.lab.internal",
                     "localhost", "a.b"):
            self.assertEqual(validate_fqdn(name), [], name)

    def test_trailing_dot_accepted(self):
        self.assertEqual(validate_fqdn("example.com."), [])
        self.assertNotEqual(validate_fqdn("example.com.."), [])

    def test_rejects_empty(self):
        self.assertEqual(validate_fqdn(""), ["fqdn is empty"])

    def test_rejects_empty_label(self):
        for name in ("a..b", ".a.b"):
            self.assertNotEqual(validate_fqdn(name), [], name)

    def test_rejects_bad_label_and_names_it(self):
        for name, bad in (("dev.bad_zone.com", "'bad_zone'"),
                          ("-x.example.com", "'-x'"),
                          ("Dev.example.com", "'Dev'")):
            errors = validate_fqdn(name)
            self.assertTrue(errors, name)
            self.assertTrue(any(bad in err for err in errors), (name, errors))

    def test_rejects_label_over_63(self):
        self.assertNotEqual(validate_fqdn("a" * 64 + ".com"), [])
        self.assertEqual(validate_fqdn("a" * 63 + ".com"), [])

    def test_rejects_total_over_253(self):
        fqdn_253 = ".".join(["a" * 63, "a" * 63, "a" * 63, "a" * 61])
        fqdn_254 = ".".join(["a" * 63, "a" * 63, "a" * 63, "a" * 62])
        self.assertEqual(len(fqdn_253), 253)
        self.assertEqual(len(fqdn_254), 254)
        self.assertEqual(validate_fqdn(fqdn_253), [])
        self.assertNotEqual(validate_fqdn(fqdn_254), [])
        self.assertEqual(validate_fqdn(fqdn_253 + "."), [])

    def test_policy_not_applied_to_fqdn(self):
        for name in ("xn--80ak6aa92e.com", "sussex.ac.uk", "www.example.com"):
            self.assertEqual(validate_fqdn(name), [], name)

    def test_rejects_trailing_newline(self):
        for name in ("example.com\n", "a\n.com"):
            self.assertNotEqual(validate_fqdn(name), [], repr(name))

    def test_empty_label_message_is_exact(self):
        self.assertEqual(validate_fqdn("a..b"), ["label '' is empty"])

    def test_dot_only_and_double_dot(self):
        self.assertEqual(validate_fqdn("."), ["label '' is empty"])
        self.assertEqual(validate_fqdn("a.."), ["label '' is empty"])
        self.assertEqual(len(validate_fqdn("..")), 2)

    def test_trailing_dot_does_not_rescue_over_length(self):
        fqdn_254 = ".".join(["a" * 63, "a" * 63, "a" * 63, "a" * 62])
        self.assertNotEqual(validate_fqdn(fqdn_254 + "."), [])


class TestSanitize(unittest.TestCase):
    def test_spaces_and_underscores_become_hyphens(self):
        self.assertEqual(sanitize_domain_label("Keen Falcon_2"), "keen-falcon-2")

    def test_collapses_repeats_and_trims_edges(self):
        self.assertEqual(sanitize_domain_label("  --keen---falcon-- "), "keen-falcon")

    def test_empty_falls_back(self):
        self.assertEqual(sanitize_domain_label("!!!"), "site")

    def test_newline_becomes_hyphen(self):
        self.assertEqual(sanitize_domain_label("keen\nfalcon"), "keen-falcon")


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

    def test_invalid_zone_raises(self):
        with self.assertRaisesRegex(ValueError, "invalid zone"):
            generate_fqdn(zone="Bad_Zone..com", label="keen-falcon")

    def test_invalid_env_raises(self):
        for env in ("-x", "Dev"):
            with self.assertRaisesRegex(ValueError, "invalid env"):
                generate_fqdn(zone="example.com", label="keen-falcon", env=env)

    def test_env_trailing_dot_raises(self):
        with self.assertRaisesRegex(ValueError, "invalid env"):
            generate_fqdn(zone="example.com", label="keen-falcon", env="dev.")

    def test_trailing_dot_zone_excluded_from_total(self):
        zone = ".".join(["b" * 63, "b" * 63, "b" * 61, ""])
        fqdn = generate_fqdn(zone=zone, label="a" * 63)
        self.assertEqual(len(fqdn), 254)
        self.assertTrue(fqdn.endswith("."))
        self.assertEqual(validate_fqdn(fqdn), [])
        zone_over = ".".join(["b" * 63, "b" * 63, "b" * 62, ""])
        with self.assertRaisesRegex(ValueError, "fqdn exceeds"):
            generate_fqdn(zone=zone_over, label="a" * 63)

    def test_multi_label_env_and_trailing_dot_zone(self):
        fqdn = generate_fqdn(zone="example.com.", label="keen-falcon", env="dev.eu")
        self.assertEqual(fqdn, "dev.eu.keen-falcon.example.com.")

    def test_empty_env_and_zone_still_skipped(self):
        fqdn = generate_fqdn(zone="", label="keen-falcon", env="")
        self.assertEqual(fqdn, "keen-falcon")


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
