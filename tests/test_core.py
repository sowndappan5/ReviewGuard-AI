import pytest
from pathlib import Path
from reviewguard.core import added_lines, scan_diff, review

ROOT = Path(__file__).resolve().parents[1]
def sample(name): return (ROOT / "samples" / name).read_text()

def test_risky_fixture():
    found = scan_diff(sample("risky.diff"))
    assert {x.rule_id for x in found} == {"PY-SECRET", "PY-EVAL", "PY-VERIFY", "PY-ASSERT"}
    assert {x.line for x in found} == {2, 3, 4, 5}

def test_clean_fixture():
    assert scan_diff(sample("clean.diff")) == []

def test_deletions_not_scanned():
    diff = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1,2 +1,2 @@\n-eval(user_input)\n+safe = 1\n"
    assert scan_diff(diff) == []

def test_non_python_ignored():
    diff = "diff --git a/a.js b/a.js\n--- a/a.js\n+++ b/a.js\n@@ -0,0 +1 @@\n+eval(x)\n"
    assert scan_diff(diff) == []

def test_comment_ignored():
    diff = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -0,0 +1 @@\n+# eval(x)\n"
    assert scan_diff(diff) == []

def test_oversize_rejected():
    with pytest.raises(ValueError): scan_diff("x" * 250001)

def test_summary():
    result = review(sample("risky.diff"))
    assert result["summary"]["high_or_critical"] == 3
    assert result["summary"]["static"] == 4

def test_line_offsets():
    diff = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -10,2 +20,3 @@\n keep\n+eval(x)\n-old\n+assert ok\n"
    assert [(n, s) for _,n,s in added_lines(diff)] == [(21,"eval(x)"),(22,"assert ok")]
