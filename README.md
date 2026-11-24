# ReviewGuard AI

ReviewGuard is a small prototype built for BitElevate's daily GitHub PR review workflow. It checks **newly added Python lines** in a pull request for common security and coding mistakes. It can also use an LLM (optional) to find extra issues, double-checks that the LLM's file and line numbers actually exist in the diff, and shows everything clearly for a human reviewer.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Choose **Built-in demo** then **Analyze changes**. No API key is needed. Optional: set `OPENAI_API_KEY` to enable LLM review. The app can fetch a *public* GitHub pull-request diff using a URL. A `GITHUB_TOKEN` may help with API rate limits.

## Run tests

```bash
python -m pytest -q
```

## Demonstration output

`samples/risky.diff` intentionally contains four injected issues: hardcoded password, `eval`, TLS verification disabled, and an `assert` used as runtime validation. Expected rule IDs: `PY-SECRET`, `PY-EVAL`, `PY-VERIFY`, `PY-ASSERT`. `samples/clean.diff` should yield zero findings. These are **synthetic** test fixtures, not representative accuracy measurements.

## How it works

```text
GitHub PR URL / Pasted Diff / Demo File
       ↓
Diff Parser (reads only newly added lines, max 250 KB)
       ├── Offline Python rules (regex checks)
       └── Optional LLM review (sends diff, gets JSON back)
                       ↓
             Check if file & line numbers are real
                       ↓
             Sort by severity (High -> Medium -> Low)
                       ↓
                Streamlit UI
```

## Limitations

 - Only added Python lines: It does not check other languages, deleted lines, or the rest of the repository.

 - Basic pattern matching: It uses simple rules, so it won't catch complex bugs or multi-line issues. Also, things like eval or assert might be okay in some cases, so a human needs to verify them.

 - LLM can make mistakes: Even though we check the file and line numbers, the AI's explanation can still be wrong.

 - Privacy: Don't paste private or company code when using the third-party LLM option.

 - GitHub limits: Only works with public github.com PR URLs and diffs under 250 KB.

 ## Evaluation

 The tests in this repo check that the diff parser works properly, catches the 4 sample bugs in risky.diff, ignores comments and deleted lines, skips non-Python files, and handles the 250 KB size limit. Before using something like this on real projects, it would need to be tested on around 100+ real PRs to measure how accurate it actually is.

 ## Deployment

Deploy on Streamlit Community Cloud: create a public GitHub repository, select `app.py`, set Python 3.11 and optionally add `OPENAI_API_KEY` in app secrets/environment. No deployment or public repository is claimed until actually published.