# AI Notes

Built with Claude (Anthropic's Claude Code) as pair programmer, one feature at a time, each reviewed before moving on.

## 1. AI-generated vs. hand-written

- Human role throughout: set scope, chose between options presented via explicit questions, reviewed every diff before accepting it.
- Features 1–5 (add, view all, filter, summary, delete) — AI-generated, from the original spec.
- `GET /categories` — user's idea, not Claude's; AI-generated implementation.
- Feature 6 (search) — user-requested addition beyond the original spec; AI-generated implementation.
- `ExpenseFilter` title normalization/length check (`models.py`) — **human-written**.
- `ExpenseFilter.is_impossible()` early-exit method (`models.py`) — **human-written**; short-circuits impossible month+date-range combos before hitting storage.
- `ExpenseFilter.start_date`/`end_date` bound of `2000–2100` — human-specified design; AI-implemented (`Field(ge=..., le=...)`).
- `storage.py` (`read_all`, `write_all`, `FILE_LOCK`) — **human-written**, full rewrite dropped in and applied verbatim.
- `repository.py`'s two `storage.LOCK` → `storage.FILE_LOCK` reference updates (required by the rename above) — AI-written glue fix, not part of the human-written credit.
- Everything else (`config.py`, `repository.py` business logic, `services.py`, `routes/`, `main.py`, `tests/`, `README.md`) — AI-generated.
- Feature 1 (add) — `models.py`, `storage.py`, `repository.add()`, `POST /expenses`: UUID4 ids, lock + atomic write.
- Feature 2 (view all) — `repository.get_all()` re-validates stored data on read; skips locking since atomic writes prevent torn reads.
- Feature 3 (filter) — `category` added as an optional `get_all()` param, validated via the `Category` enum.
- Feature 4 (summary) — `services.py::compute_summary()`: pure function, rounds once at the end.
- Feature 5 (delete) — `repository.delete()`: lock-guarded, skips the write when nothing was removed.
- Feature 6 (search) — `get_all()` extended to 8 filters; `ExpenseFilter` model validates ranges at the API boundary.

## 2. What was validated, tested, or changed — and why

- Smoke-tested the add-expense endpoint manually before writing the formal test suite.
- Verified `round(1.005, 2) == 1.0` by actually running it, not assuming standard rounding.
- Verified `dict[Category, float]` serializes enum keys as plain strings by inspecting real JSON output.
- Verified FastAPI's `Annotated[Model, Query()]` actually works via a diagnostic script before designing Feature 6 around it.
- Re-ran the full 33-test suite after changing `get_all()`'s signature to confirm backward compatibility.
- Fixed a logging bug: `repository.add` was logging the raw enum instead of `.value`.
- Verified README install/run/test commands on a simulated clean checkout after every feature.
- Full test suite passing after every feature — 49/49 tests after Feature 6.
- Verified the user-written `storage.py` drop-in: full 49-test suite still passes, plus a targeted manual check of the new shape-validation (rejects non-list JSON and non-dict items) and the read/write round-trip.

## 3. Decisions and rejected alternatives (production-level reasoning, one line each)

- UUID4 over auto-increment ids — avoids a full-file scan per insert and id-reuse bugs after deletes.
- Sync handlers + `threading.Lock` over async file I/O — simplest correct concurrency model at this scale.
- Fixed `Category` enum over free text — prevents near-duplicate categories from corrupting the summary.
- No repository/service stubs ahead of need — avoids dead code for features not yet built.
- No pagination/sorting beyond spec (pre–Feature 6) — kept API surface matching what was actually required.
- No lock on reads in `get_all()` — atomic writes already prevent torn reads, so it would only add contention.
- Query param over a separate `/by-category/{category}` route — avoids duplicating the same read-and-parse logic.
- Round once at the end in `compute_summary`, not per addition — avoids compounding binary-float error.
- No DI wrapper around `compute_summary` — it's pure and stateless, so DI would add indirection with no benefit.
- No combined `get_summary()` repository method — keeps the persistence/computation boundary clean.
- `uuid.UUID` path param type over manual validation — lets FastAPI reject malformed ids with `422` for free.
- Skip the write in `delete()` when nothing was removed — avoids a pointless atomic replace on every `404`.
- Extended `GET /expenses` over a new `/search` route — same underlying operation as the existing category filter.
- Substring title match over exact match — an exact-match "search" isn't actually useful for searching.
- Independent `month`/`year` filters, ANDed with everything else — consistent with how every other filter composes.
- Unpacked kwargs into `get_all()` over passing the Pydantic object — keeps the repository decoupled from the API schema.
- Shape-validating JSON on read (list of dicts) — catches a hand-corrupted-but-valid-JSON file before it silently breaks downstream parsing.
- `f.flush()` + `os.fsync()` before the atomic rename in `write_all` — closes a real durability gap; without it a crash right after rename can still lose buffered data on some filesystems.
- `ensure_ascii=False` in `json.dump` — avoids escaping non-English expense titles into `\uXXXX` sequences.
- Dropped the `write_all([])` side effect from `read_all` — a read function shouldn't have a write side effect; the first real write still creates the file/dir.
