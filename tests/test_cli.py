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
        self.assertIn("INVALID:", err)


class TestValidateFlagUnchanged(unittest.TestCase):
    def test_validate_label_ok(self):
        code, out, _ = run_cli(["--validate", "keen-falcon"])
        self.assertEqual((code, out), (0, "OK\n"))

    def test_validate_label_rejects_fqdn(self):
        code, out, err = run_cli(["--validate", "a.b"])
        self.assertEqual((code, out), (1, ""))
        self.assertIn("INVALID:", err)


class TestInvalidZoneEnv(unittest.TestCase):
    def test_invalid_zone_exits_2(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                main(["--zone", "Bad_Zone..com"])
        self.assertEqual(cm.exception.code, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("error:", err.getvalue())

    def test_invalid_env_exits_2(self):
        # Equals form "--env=-x" passes "-x" through argparse untouched.
        for argv in (["--zone", "example.com", "--env", "Dev"],
                     ["--zone", "example.com", "--env=-x"]):
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    main(argv)
            self.assertEqual(cm.exception.code, 2)


class TestGeneration(unittest.TestCase):
    def test_valid_zone_generation_reproducible(self):
        first = run_cli(["--seed", "7", "--zone", "example.com", "--env", "dev"])
        second = run_cli(["--seed", "7", "--zone", "example.com", "--env", "dev"])
        self.assertEqual(first, second)
        self.assertEqual(first[0], 0)
        line = first[1].strip()
        self.assertTrue(line.startswith("dev."))
        self.assertEqual(validate_fqdn(line), [])


if __name__ == "__main__":
    unittest.main()
