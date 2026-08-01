# AI Notes

Built with Claude (Anthropic's Claude Code) as pair programmer, one feature at a time, each reviewed before moving on.

## 1. AI-generated vs. hand-written

- Human role throughout: set scope, chose between options presented via explicit questions, reviewed every diff before accepting it.
- `ExpenseFilter` title normalization/length check (`models.py`) — **human-written**.
- `ExpenseFilter.is_impossible()` early-exit method (`models.py`) — **human-written**; short-circuits impossible month+date-range combos before hitting storage.
- `ExpenseFilter.start_date`/`end_date` bound of `2000–2100` — human-specified design; 
- `storage.py` (`read_all`, `write_all`, `FILE_LOCK`) — **human-written**.
- Everything else (`config.py`, `repository.py` business logic, `services.py`, `routes/`, `main.py`, `tests/`, `README.md`) — AI-generated.

## 2. Features implemented

- Feature 1 — Add an expense (`POST /expenses`): UUID4 ids, lock + atomic write.
- Feature 2 — View all expenses (`GET /expenses`).
- Feature 3 — Filter by category (`?category=`).
- Feature 4 — Category-wise/total summary (`GET /expenses/summary`), via `services.py`.
- Feature 5 — Delete an expense (`DELETE /expenses/{id}`).
- Feature 6 — Search (`?title=`, `?min_amount=`, `?start_date=`, `?month=`, etc.).

## 3. What was validated, tested, or changed — and why

- Verified FastAPI's `Annotated[Model, Query()]` actually works via a diagnostic script before designing Feature 6 around it.
- Fixed a logging bug: `repository.add` was logging the raw enum instead of `.value`.
- Re-ran the full 33-test suite after changing `get_all()`'s signature to confirm backward compatibility.
- Verified README install/run/test commands on a simulated clean checkout after every feature.
- Full test suite passing after every feature — 49/49 tests after Feature 6.
- Verified the user-written `storage.py` drop-in: full suite still passes, plus a targeted manual check of shape-validation and the read/write round-trip.

## 4. Decisions and rejected alternatives (production-level reasoning, one line each)

- UUID4 over auto-increment ids — avoids a full-file scan per insert and id-reuse bugs after deletes.
- Sync handlers + `threading.Lock` over async file I/O — simplest correct concurrency model at this scale.
- Fixed `Category` enum over free text — prevents near-duplicate categories from corrupting the summary.
- No lock on reads in `get_all()` — atomic writes already prevent torn reads, so it would only add contention.
- Round once at the end in `compute_summary`, not per addition — avoids compounding binary-float error.
- `uuid.UUID` path param type over manual validation — lets FastAPI reject malformed ids with `422` for free.
- Skip the write in `delete()` when nothing was removed — avoids a pointless atomic replace on every `404`.
- Extended `GET /expenses` over a new `/search` route — same underlying operation as the existing category filter.
- Substring title match over exact match — an exact-match "search" isn't actually useful for searching.
- Shape-validating JSON on read (list of dicts) — catches a hand-corrupted-but-valid-JSON file before it silently breaks downstream parsing.
- `f.flush()` + `os.fsync()` before the atomic rename in `write_all` — closes a real durability gap; without it a crash right after rename can still lose buffered data on some filesystems.
- Dropped the `write_all([])` side effect from `read_all` — a read function shouldn't have a write side effect; the first real write still creates the file/dir.
