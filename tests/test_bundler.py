from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure scripts dir is on sys.path for importing bundle_local
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "skills" / "bundle-local" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bundle_local import (
    validate_version_name,
    clean_commit_message,
    format_combined_sql,
)


class TestValidateVersionName:
    """Item (1): Input validation tests for release version strings."""

    @pytest.mark.parametrize("valid_name", [
        "v1.0.0",
        "uat-2026.10",
        "release_1.2.3",
        "patch-1",
        "1.0.0",
        "feature.flag-test_01",
        "v0.1.0-rc1",
        "Release-2026_Q4",
    ])
    def test_valid_version_names(self, valid_name: str):
        assert validate_version_name(valid_name) is True

    @pytest.mark.parametrize("invalid_name", [
        "",                             # empty string
        " ",                            # whitespace only
        "..",                           # traversal relative
        "../v1.0.0",                    # path traversal upward
        "../../etc/passwd",             # deep path traversal
        "v1.0/sub",                     # slash path separator
        "v1.0\\sub",                    # Windows backslash
        "; rm -rf /",                   # command injection attempt
        "& echo pwned",                 # shell pipe injection
        "$(whoami)",                    # shell expansion
        "-rf",                          # leading dash flag injection
        ".hidden",                      # leading dot
        "_underscore_leading",          # leading underscore
        "version with spaces",          # space disallowed
        "a" * 129,                      # exceed max length 128
    ])
    def test_invalid_version_names(self, invalid_name: str):
        assert validate_version_name(invalid_name) is False


class TestCleanCommitMessage:
    """Item (10): Commit message cleanup tests across Conventional Commits, JIRA, revert, and unicode."""

    @pytest.mark.parametrize("raw, expected", [
        # Standard Conventional Commits
        ("feat: add user authentication", "Add user authentication"),
        ("fix: resolve crash on startup", "Resolve crash on startup"),
        ("docs: update API reference table", "Update API reference table"),
        ("refactor: extract helper function", "Extract helper function"),
        ("chore: update build dependencies", "Update build dependencies"),
        ("perf: optimize database query", "Optimize database query"),

        # Scopes & Breaking Changes
        ("fix(scope)!: resolve token expiration deadlock", "Resolve token expiration deadlock"),
        ("feat(auth)!: replace session cookie with JWT", "Replace session cookie with JWT"),
        ("chore(deps): bump urllib3 from 1.26 to 2.0", "Bump urllib3 from 1.26 to 2.0"),
        ("refactor(payment-gateway): simplify retry logic", "Simplify retry logic"),

        # Ticket / Issue ID prefixes
        ("[PROJ-123] feat: add bulk import capability", "Add bulk import capability"),
        ("[PROJ-123] feat(order): add bulk import capability", "Add bulk import capability"),
        ("PROJ-456: fix: handle null pointer in discount service", "Handle null pointer in discount service"),
        ("(#789) update: clarify database migration guide", "Clarify database migration guide"),
        ("[CORE-999] style: format SQL statements", "Format SQL statements"),

        # Reverts
        ('revert: "feat: add buggy payment webhook"', "Add buggy payment webhook"),
        ('Revert "feat(auth): experimental oauth provider"', "Experimental oauth provider"),
        ("revert: fix memory leak", "Fix memory leak"),
        ("revert(ui)!: remove old navbar component", "Remove old navbar component"),

        # Vietnamese & Non-ASCII plain text
        ("cập nhật giao diện thanh toán đơn hàng", "Cập nhật giao diện thanh toán đơn hàng"),
        ("feat: cập nhật thông tin kho hàng MISA", "Cập nhật thông tin kho hàng MISA"),
        ("fix(kho)!: sửa lỗi đồng bộ tồn kho âm", "Sửa lỗi đồng bộ tồn kho âm"),

        # Edge cases
        ("", ""),
        ("   ", ""),
        ("already capitalized regular commit", "Already capitalized regular commit"),
        ("lowercase regular commit message", "Lowercase regular commit message"),
    ])
    def test_clean_commit_message_transformations(self, raw: str, expected: str):
        assert clean_commit_message(raw) == expected


class TestFormatCombinedSql:
    """Item (6) & (10): SQL combination, deterministic ordering, and collision handling."""

    def test_empty_sql_files_data(self):
        sql_text, warnings = format_combined_sql(
            sql_files_data={},
            version="v1.0.0",
            branches=["main"],
            now_str="2026-10-31 12:00:00"
        )
        assert "COMBINED DATABASE RELEASE SCRIPT: v1.0.0" in sql_text
        assert "[INFO] No SQL migration scripts detected" in sql_text
        assert warnings == []

    def test_deterministic_sorting(self):
        # Insert files out of order
        sql_files_data = {
            "migrations/03_orders.sql": {
                "branches": ["feat/orders"],
                "hashes": {"feat/orders": "hash3"},
                "contents": {"feat/orders": "CREATE TABLE orders (id INT);"}
            },
            "migrations/01_init.sql": {
                "branches": ["feat/init"],
                "hashes": {"feat/init": "hash1"},
                "contents": {"feat/init": "CREATE TABLE app_meta (ver INT);"}
            },
            "migrations/02_users.sql": {
                "branches": ["feat/users"],
                "hashes": {"feat/users": "hash2"},
                "contents": {"feat/users": "CREATE TABLE users (id INT);"}
            },
        }

        sql_text, warnings = format_combined_sql(
            sql_files_data=sql_files_data,
            version="v1.0.0",
            branches=["feat/orders", "feat/init", "feat/users"],
            now_str="2026-10-31 12:00:00"
        )

        pos1 = sql_text.find("FILE: migrations/01_init.sql")
        pos2 = sql_text.find("FILE: migrations/02_users.sql")
        pos3 = sql_text.find("FILE: migrations/03_orders.sql")

        assert pos1 != -1 and pos2 != -1 and pos3 != -1
        assert pos1 < pos2 < pos3, "SQL files must be sorted deterministically by path"
        assert warnings == []

    def test_identical_file_across_multiple_branches_deduplication(self):
        # Two branches touched the exact same file with identical hash
        sql_files_data = {
            "migrations/05_settings.sql": {
                "branches": ["feat/settings-a", "feat/settings-b"],
                "hashes": {
                    "feat/settings-a": "samehash123",
                    "feat/settings-b": "samehash123",
                },
                "contents": {
                    "feat/settings-a": "ALTER TABLE settings ADD COLUMN timeout INT;",
                    "feat/settings-b": "ALTER TABLE settings ADD COLUMN timeout INT;",
                }
            }
        }

        sql_text, warnings = format_combined_sql(
            sql_files_data=sql_files_data,
            version="v1.1.0",
            branches=["feat/settings-a", "feat/settings-b"],
            now_str="2026-10-31 12:00:00"
        )

        assert warnings == []
        assert "COLLISION WARNING" not in sql_text
        assert "(Also present in: feat/settings-a, feat/settings-b)" in sql_text
        # Content should appear only once
        assert sql_text.count("ALTER TABLE settings ADD COLUMN timeout INT;") == 1

    def test_differing_file_across_branches_triggers_collision_warning(self):
        # Two branches modified the same file with different content
        sql_files_data = {
            "migrations/06_conflict.sql": {
                "branches": ["feat/alpha", "feat/beta"],
                "hashes": {
                    "feat/alpha": "hash_alpha",
                    "feat/beta": "hash_beta",
                },
                "contents": {
                    "feat/alpha": "ALTER TABLE items ADD COLUMN price_cents INT;",
                    "feat/beta": "ALTER TABLE items ADD COLUMN price_vnd BIGINT;",
                }
            }
        }

        sql_text, warnings = format_combined_sql(
            sql_files_data=sql_files_data,
            version="v1.2.0",
            branches=["feat/alpha", "feat/beta"],
            now_str="2026-10-31 12:00:00"
        )

        assert len(warnings) == 1
        assert "differing contents across branches" in warnings[0]
        assert "[COLLISION WARNING]" in sql_text
        assert "Using version from 'feat/beta'" in sql_text
        # Content from chosen (latest) branch
        assert "ALTER TABLE items ADD COLUMN price_vnd BIGINT;" in sql_text
