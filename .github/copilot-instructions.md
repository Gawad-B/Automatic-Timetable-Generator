# Copilot Instructions for Automatic-Timetable-Generator

## Build, test, and lint commands

### Setup
- `pip install -r requirements.txt`
- `npm install`

### Build
- `npm run build` (compiles `static/js/app.ts` to `static/js/app.js` via `tsc`)
- `npm run watch` (TypeScript watch mode)

### Run
- `python server.py`
- `./start.sh` (installs missing deps, builds TS if needed, then starts Flask)

### Tests and linting
- There is currently no automated test suite or lint script configured in `package.json` or repository tooling.
- There is no single-test command available at this time.

## High-level architecture

- **Flask app (`server.py`)** serves `templates/index.html`, handles uploads, runs timetable generation, and returns a downloadable ZIP of Excel files.
- **Frontend (`templates/index.html` + `static/js/app.ts`)** is a single-page flow: collect 5 CSVs, call `POST /upload`, then `POST /generate`, then download from `GET /download`.
- **Scheduling engine (`csp.py`)** loads CSV inputs, builds CSP domains, solves with forward-checking backtracking, then converts assignments into a tabular schedule.
- **Export pipeline (`server.py`)** transforms solver output into:
  - `Main_Timetable.xlsx`
  - per-year files (`Years/Year_X.xlsx`)
  - per-instructor files
  - per-room files
  packaged into one in-memory ZIP for `/download`.

## Key repository conventions

- Expected upload targets are fixed: `courses`, `instructors`, `rooms`, `timeslots`, `sections`.
- Uploaded files are stored under `static/uploads/<target>/<target>.csv`; `csp.load_csvs` also supports fallback paths `static/uploads/<target>.csv`.
- CSP variable naming is structured as `CourseID::G<group_index>::<SessionType>` (for example, `CSC111::G0::Lecture`), and `meta[var]["sections"]` is authoritative for expanding group assignments back to per-section rows.
- Section grouping is session-specific:
  - `TUT`: 1 section per group
  - `Lab`: 2 sections per group
  - `Lecture`: 3 or 4 sections per group (based on section count)
- `SectionID` format drives assignment logic:
  - Years 1-2: `year/number`
  - Years 3-4: `year/department/number`
  with department matching from the first 3 letters of `CourseID`, except Year 3 `Shared=Yes` courses which can map across core departments.
- Role constraint is intentionally hard in domain generation:
  - `Professor` (non-assistant) -> lectures only
  - `Assistant Professor` -> labs/TUTs only
  This rule is not relaxed in fallback passes.
- Timeslot duration behavior is significant:
  - Lectures/labs use 90-minute slots
  - TUT uses 45-minute slots only when course type includes lecture + lab + TUT; otherwise TUT uses 90-minute slots.
