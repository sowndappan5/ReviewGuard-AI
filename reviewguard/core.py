"""Offline deterministic checks."""
import re
from collections import namedtuple

MAX_DIFF_BYTES = 250_000

Finding = namedtuple(
    "Finding",
    ["rule_id", "severity", "file", "line", "evidence", "explanation", "suggestion", "source"],
    defaults=["static"],
)

RULES = [
    ("PY-EVAL", "high", re.compile(r"\beval\s*\("), "Dynamic eval can execute attacker-controlled expressions.", "Replace eval with a safe parser or explicit allowlist."),
    ("PY-SHELL", "high", re.compile(r"\b(?:subprocess\.(?:run|Popen|call|check_output)|os\.system)\s*\(.*shell\s*=\s*True"), "Shell execution can enable command injection if input is untrusted.", "Use an argument list with shell=False and validate inputs."),
    ("PY-PICKLE", "high", re.compile(r"\bpickle\.loads?\s*\("), "Deserializing untrusted pickle data can execute code.", "Use JSON or a constrained serialization format for untrusted input."),
    ("PY-VERIFY", "high", re.compile(r"\bverify\s*=\s*False\b"), "Disabling TLS verification permits man-in-the-middle attacks.", "Enable certificate verification."),
    ("PY-SECRET", "high", re.compile(r"\b(?:api_key|secret_key|password|access_token)\s*=\s*['\"][^'\"]{8,}['\"]", re.I), "A possible credential is embedded in source code.", "Load credentials from a secret manager or environment variable; rotate exposed credentials."),
    ("PY-DEBUG", "medium", re.compile(r"\bdebug\s*=\s*True\b"), "Debug mode can expose internal application details.", "Disable debug mode outside local development."),
    ("PY-ASSERT", "medium", re.compile(r"^\s*assert\s+"), "Assertions can be disabled by optimized Python execution.", "Use explicit validation and raise a suitable exception for runtime checks."),
]

def added_lines(diff):
    """Yield from unified diff; never scan deleted lines."""
    if len(diff.encode("utf-8")) > MAX_DIFF_BYTES:
        raise ValueError("Diff exceeds 250 KB safety limit")
    path, line_no, in_hunk = "", 0, False
    for raw in diff.splitlines():
        if raw.startswith("diff --git "):
            path, in_hunk = "", False
        elif raw.startswith("+++ b/"):
            path = raw[6:]
        elif raw.startswith("+++ /dev/null"):
            path = ""
        elif raw.startswith("@@"):
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
            if m:
                line_no, in_hunk = int(m.group(1)), True
            else:
                in_hunk = False
        elif in_hunk and raw.startswith("+") and not raw.startswith("+++"):
            if path:
                yield path, line_no, raw[1:]
            line_no += 1
        elif in_hunk and raw.startswith(" "):
            line_no += 1
        elif in_hunk and raw.startswith("-"):
            pass
        elif raw.startswith("\\ No newline"):
            pass

def scan_diff(diff):
    findings = []
    for path, number, content in added_lines(diff):
        if not path.endswith(".py"):
            continue
        if content.lstrip().startswith("#"):
            continue
        for rule_id, severity, pattern, explanation, suggestion in RULES:
            if pattern.search(content):
                findings.append(Finding(rule_id, severity, path, number, content.strip()[:180], explanation, suggestion))
    return findings

def review(diff, llm_findings=None):
    static = scan_diff(diff)
    all_findings = static + (llm_findings or [])
    rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    all_findings.sort(key=lambda f: (-rank.get(f.severity, 0), f.file, f.line))
    return {
        "summary": {
            "total": len(all_findings),
            "high_or_critical": sum(f.severity in {"high", "critical"} for f in all_findings),
            "static": len(static),
            "llm": len(llm_findings or []),
            "risk_label": "needs attention" if any(f.severity in {"high", "critical"} for f in all_findings) else "no high-severity pattern detected",
        },
        "findings": [f._asdict() for f in all_findings],
        "limitations": "Pattern-based findings are potential risks, not proof of exploitability; absence of findings does not imply safe code.",
    }