"""CLI tests for python -m domainame (stdlib unittest only)."""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domainame.__main__ import main  # noqa: E402
from domainame.generator import validate_fqdn  # noqa: E402


def run_cli(argv):
    """Run main() capturing output; returns (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class TestValidateFqdnFlag(unittest.TestCase):
    def test_validate_fqdn_ok(self):
        self.assertEqual(
            run_cli(["--validate-fqdn", "dev.keen-falcon.example.com"]),
            (0, "OK\n", ""),
        )

    def test_validate_fqdn_invalid(self):
        code, out, err = run_cli(["--validate-fqdn", "bad_zone..com"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(
            err.splitlines(),
            [f"INVALID: {e}" for e in validate_fqdn("bad_zone..com")],
        )
        self.assertEqual(len(err.splitlines()), 2)

    def test_validate_fqdn_empty(self):
        code, out, err = run_cli(["--validate-fqdn", ""])
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(err, "INVALID: fqdn is empty\n")


class TestValidateFlagUnchanged(unittest.TestCase):
    def test_validate_label_ok(self):
        code, out, _ = run_cli(["--validate", "keen-falcon"])
        self.assertEqual((code, out), (0, "OK\n"))

    def test_validate_label_rejects_fqdn(self):
        code, out, err = run_cli(["--validate", "a.b"])
        self.assertEqual((code, out), (1, ""))
        self.assertIn("INVALID:", err)


class TestInvalidZoneEnv(unittest.TestCase):
    def assert_parser_error(self, argv, needle):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                main(argv)
        self.assertEqual(cm.exception.code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("domainame: error:", err.getvalue())
        self.assertIn(needle, err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        return err.getvalue()

    def test_invalid_zone_exits_2(self):
        self.assert_parser_error(["--zone", "Bad_Zone..com"], "--zone")

    def test_invalid_env_exits_2(self):
        # Equals form "--env=-x" passes "-x" through argparse untouched.
        for argv in (["--zone", "example.com", "--env", "Dev"],
                     ["--zone", "example.com", "--env=-x"]):
            self.assert_parser_error(argv, "--env")

    def test_env_trailing_dot_exits_2(self):
        self.assert_parser_error(
            ["--zone", "example.com", "--env", "dev."], "invalid --env"
        )


class TestGeneration(unittest.TestCase):
    def test_valid_zone_generation_reproducible(self):
        first = run_cli(["--seed", "7", "--zone", "example.com", "--env", "dev"])
        second = run_cli(["--seed", "7", "--zone", "example.com", "--env", "dev"])
        self.assertEqual(first, second)
        self.assertEqual(first[0], 0)
        line = first[1].strip()
        self.assertTrue(line.startswith("dev."))
        self.assertEqual(validate_fqdn(line), [])

    def test_seed_7_golden_line(self):
        _, out, _ = run_cli(["--seed", "7", "--zone", "example.com", "--env", "dev"])
        self.assertEqual(out, "dev.heroic-crane.example.com\n")

    def test_env_without_zone_ignored(self):
        code, out, err = run_cli(["--seed", "7", "--env", "Bad"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertNotIn("Bad", out)


if __name__ == "__main__":
    unittest.main()
