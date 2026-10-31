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
    categorize_commit,
    scan_sql_safety,
    format_combined_sql,
    extract_api_endpoint,
    format_changelog,
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


class TestExtractApiEndpoint:
    """Tests for API endpoint detection from commit messages."""

    @pytest.mark.parametrize("msg, expected_platform, expected_line", [
        (
            "feat(api-web): POST /api/v1/orders/export-excel - Xuất báo cáo đơn hàng ra Excel",
            "web",
            "`POST /api/v1/orders/export-excel` - Xuất báo cáo đơn hàng ra Excel"
        ),
        (
            "api(mobile): GET /api/v1/notifications",
            "mobile",
            "`GET /api/v1/notifications`"
        ),
        (
            "[PROJ-123] feat(web-api): PUT /api/v1/profile: Cập nhật thông tin",
            "web",
            "`PUT /api/v1/profile` - Cập nhật thông tin"
        ),
        (
            "feat(api/mob)!: DELETE /api/v1/devices/{id} - Xóa thiết bị",
            "mobile",
            "`DELETE /api/v1/devices/{id}` - Xóa thiết bị"
        ),
        (
            "api(mob): POST /api/v1/payments/retry",
            "mobile",
            "`POST /api/v1/payments/retry`"
        ),
    ])
    def test_extract_valid_api_endpoints(self, msg: str, expected_platform: str, expected_line: str):
        res = extract_api_endpoint(msg)
        assert res is not None
        platform, formatted = res
        assert platform == expected_platform
        assert formatted == expected_line

    @pytest.mark.parametrize("non_api_msg", [
        "feat: update user avatar",
        "fix(auth): resolve session expiration",
        "docs: update README",
        "api: not following endpoint format",
        "feat(api): missing method and path",
    ])
    def test_ignore_non_api_commits(self, non_api_msg: str):
        assert extract_api_endpoint(non_api_msg) is None


class TestFormatChangelog:
    """Tests for 4-section changelog formatting."""

    def test_format_changelog_with_apis_and_sql(self):
        content = format_changelog(
            version="uat-1.1.0",
            base_branch="develop",
            branches=["feat/orders", "fix/pay"],
            now_str="2026-10-31 16:30:00",
            business_lines=["- Add export capability", "- Fix payment timeout"],
            api_web_lines=["`POST /api/v1/orders/export` - Export to Excel"],
            api_mob_lines=["`POST /api/v1/mobile/pay/retry` - Retry payment"],
            sql_files=["migrations/01_init.sql", "migrations/02_orders.sql"],
            branch_commit_blocks=["#### Branch: `feat/orders`\n- [abc] feat: add orders"]
        )

        assert "# Release Changelog: uat-1.1.0" in content
        assert "### 1. Features & Business Highlights (Ready-to-copy):" in content
        assert "- Add export capability" in content
        assert "### 2. New API Endpoints:" in content
        assert "**Web:**" in content
        assert "`POST /api/v1/orders/export` - Export to Excel" in content
        assert "**Mobile:**" in content
        assert "`POST /api/v1/mobile/pay/retry` - Retry payment" in content
        assert "### 3. Database Migrations:" in content
        assert "`combined_db_scripts.sql` (2 files compiled: 01_init.sql, 02_orders.sql)" in content
        assert "### 4. Technical Audit (Commits by branch):" in content

    def test_format_changelog_empty_apis(self):
        content = format_changelog(
            version="hotfix-1.0.1",
            base_branch="main",
            branches=["fix/bug"],
            now_str="2026-10-31 16:30:00",
            business_lines=["- Fix critical bug"],
            api_web_lines=[],
            api_mob_lines=[],
            sql_files=[],
            branch_commit_blocks=["#### Branch: `fix/bug`\n- [def] fix: critical bug"]
        )

        assert "### 2. New API Endpoints:" in content
        assert "*(No new API endpoints detected in commit messages)*" in content
        assert "*(No SQL migration scripts in this release)*" in content


class TestCategorizeCommit:
    """Item (7): Categorization of commit messages into Features, Fixes, Others."""

    def test_feature_commits(self):
        cat, clean = categorize_commit("feat: add export to excel")
        assert cat == "features"
        assert clean == "Add export to excel"

        cat2, clean2 = categorize_commit("[PROJ-101] feat(api): create user endpoint")
        assert cat2 == "features"
        assert clean2 == "Create user endpoint"

        cat3, clean3 = categorize_commit("add: new notification banner")
        assert cat3 == "features"
        assert clean3 == "New notification banner"

    def test_fix_commits(self):
        cat, clean = categorize_commit("fix(auth)!: resolve session expiration race condition")
        assert cat == "fixes"
        assert clean == "Resolve session expiration race condition"

        cat2, clean2 = categorize_commit("hotfix: patch security vulnerability in parser")
        assert cat2 == "fixes"
        assert clean2 == "Patch security vulnerability in parser"

    def test_other_commits_and_trailers(self):
        cat, clean = categorize_commit("chore(deps): bump urllib3 from 1.26 to 2.0")
        assert cat == "others"
        assert clean == "Bump urllib3 from 1.26 to 2.0"

        # Git trailer stripping
        msg_with_trailer = "docs: update API guide\n\nCo-authored-by: Developer <dev@example.com>"
        cat2, clean2 = categorize_commit(msg_with_trailer)
        assert cat2 == "others"
        assert "Co-authored-by" not in clean2
        assert clean2 == "Update API guide"


class TestScanSqlSafety:
    """Item (3): SQL safety scanning for DROP, TRUNCATE, and unconditioned DELETE."""

    def test_safe_sql(self):
        safe_sql = """
        -- Safe migration script
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        UPDATE users SET name = 'Bob' WHERE id = 1;
        DELETE FROM users WHERE id = 2;
        """
        warnings = scan_sql_safety(safe_sql)
        assert warnings == []

    def test_dangerous_drop(self):
        sql = "DROP TABLE users; DROP DATABASE legacy_db;"
        warnings = scan_sql_safety(sql)
        assert len(warnings) == 2
        assert any("DROP TABLE `users`" in w for w in warnings)
        assert any("DROP DATABASE `legacy_db`" in w for w in warnings)

    def test_dangerous_truncate(self):
        sql = "TRUNCATE TABLE session_cache; TRUNCATE logs;"
        warnings = scan_sql_safety(sql)
        assert len(warnings) == 2
        assert any("TRUNCATE TABLE `session_cache`" in w for w in warnings)
        assert any("TRUNCATE TABLE `logs`" in w for w in warnings)

    def test_dangerous_delete_without_where(self):
        sql = """
        -- Delete all records without WHERE clause!
        DELETE FROM order_history;
        """
        warnings = scan_sql_safety(sql)
        assert len(warnings) == 1
        assert "HIGH SEVERITY DANGER: DELETE FROM `order_history` without WHERE clause" in warnings[0]

    def test_commented_dangerous_commands_ignored(self):
        sql = """
        -- DROP TABLE temp_data;
        /* TRUNCATE TABLE users; */
        -- DELETE FROM orders;
        CREATE TABLE safe (id INT);
        """
        warnings = scan_sql_safety(sql)
        assert warnings == []


