# air-quality-analysis: Project Notes

> Living document. Update at the end of each working session, commit it to the repo, and re-upload it to the Claude Project knowledge.
> **Last updated:** 2026-11-11; code status as of the last working session

## 1. Goal

A portfolio demo of an **automated analysis pipeline**: a marimo notebook exported to WASM and hosted on GitHub Pages, fed by a daily GitHub Action that pulls fresh data from the Open-Meteo Air Quality API.

Priorities, in order:
1. **Stability:** every visit, the site works and shows the latest data.
2. **Polish:** a finished read-only app, not a scratchpad.
3. **Learning:** this is a learning project. Walk through concepts step by step; don't just hand over code.

## 2. Architecture (decided)

```
GitHub Action (daily cron + push to main)
  1. Check out repo
  2. Run scripts/fetch_data.py  ->  overwrites public/data/aqi.json
  3. marimo export html-wasm apps/air_quality_analysis.py --mode run
  4. Deploy to GitHub Pages (upload-pages-artifact + deploy-pages)
```

| Decision | Choice | Why |
|---|---|---|
| Data freshness | Snapshot baked in at build time (daily overwrite, single file) | Browser never calls the API, so the site doesn't depend on Open-Meteo being up or CORS-friendly at view time |
| Data storage | Overwrite one file, no history | Simplicity and stability; complexity goes in the notebook, not the pipeline |
| API calls | One batched call for all cities | Simple, fewer failure points |
| Notebook mode | `apps/` with `--mode run` (read-only) | Code is public in the repo; the site is the polished product |
| On fetch failure | Fail the job and keep the last good deploy | Stability over stale-but-deployed |
| Alerting | GitHub's built-in failure email (baseline) | Add a Slack or auto-issue step later only if needed |
| Repo | Standalone `air-quality-analysis` (not inside `python_business_automation`) | One Pages site per repo; clearer portfolio story. Cross-link from the other repo's README |
| Editor | marimo browser editor (`python -m marimo edit ...`) from VS Code terminal; GitHub Desktop for commits | Personal preference |
| Dependencies | `.venv` locally; consider PEP 723 inline deps in the notebook for WASM export | Only Pyodide-compatible packages work in WASM (pandas, numpy, altair/plotly are fine) |
| Chart library | Altair 6.x (`altair~=6.3`) | Tooltips by default, a grammar close to ggplot/Tableau, loads in the WASM export (tested) |
| Data format | JSON records, not Parquet | Needs no extra browser dependency (pyarrow) and is human-readable; costs a few type fixes in the notebook |
| Export | `python -m marimo export html-wasm apps/air_quality_analysis.py -o site --mode run` | Directory export, not `--single-file` (which skips `public/`); must be served over HTTP |
| Browser packages | Unpinned; accepted risk | A third-party doc says marimo strips PEP 723 version pins in WASM (unverified); revisit only if something breaks |
| DST | Accept as known limitation | See section 3 |

Repo: https://github.com/julierose/air-quality-analysis

### Planned structure
```
air-quality-analysis/
├── apps/air_quality_analysis.py      # marimo notebook
├── scripts/fetch_data.py             # data pull
├── apps/public/data/aqi.json         # generated daily by fetch_data.py; gitignored
├── docs/PROJECT_NOTES.md             # working notes
├── .github/workflows/deploy.yml
├── .gitignore                        # .venv/, __pycache__/, *.pyc, .DS_Store, requests_cache sqlite file
└── README.md
```

## 3. Data spec

**Cities** (top 5 US by population, per chat; Census Bureau Vintage 2025 estimates, released May 2026; verify figures before citing in the README):

| City | Population (2025 est.) | Lat | Lon |
|---|---|---|---|
| New York, NY | 8,584,629 | 40.7128 | -74.0060 |
| Los Angeles, CA | 3,869,089 | 34.0522 | -118.2437 |
| Chicago, IL | 2,731,585 | 41.8781 | -87.6298 |
| Houston, TX | 2,397,315 | 29.7604 | -95.3698 |
| Phoenix, AZ | 1,665,481 | 33.4484 | -112.0740 |

Source: https://www.census.gov/newsroom/press-kits/2026/vintage-2025-city-town-pop-estimates.html

The cities were chosen for geographic diversity, in the hope of distinct pollution profiles (e.g. dust in Phoenix, ozone in LA).
Open-Meteo snaps to its own grid, so returned coordinates differ slightly from those above (e.g. NYC came back as 40.70, -74.00).

**API parameters**
- `hourly`: `pm10`, `pm2_5`, `carbon_monoxide`, `nitrogen_dioxide`, `sulphur_dioxide`, `ozone`, `us_aqi` (6 pollutants + overall US AQI)
- `past_days: 1`, `forecast_days: 2`
- `timezone: "auto"` 

**Shape:** 72 hourly rows per city × 5 cities = 360 rows, each labeled `observed`, `forecast_today`, or `forecast_tomorrow`, in **city-local time**.

**Labels:** `past`, `forecast_today`, `forecast_tomorrow` (renamed from `observed`, since past hours are also model output).

**Derived in the notebook:** `local_day` (the local date) and `time_period` (`past` or `forecast`).

**Units:** μg/m³ for all pollutants; `us_aqi` is a 0-500 index, the maximum of the six pollutant sub-indices (PM uses a rolling 24 h average, CO 8 h).

**DST caveat:** Open-Meteo fixes the UTC offset at request time for the whole response. Windows that span a clock change have local times off by one hour for part of the window, for DST-observing cities (not Phoenix). Decision: accept and document; revisit before launch.

## 4. Status

### Done
- Repo created, cloned locally, connected to GitHub Desktop; folders and `.gitignore` in place; venv working.
- Notebook file created and confirmed to open in the marimo browser editor.
- `fetch_data.py` (working, cell-by-cell):
  - Batched Open-Meteo call for 5 cities × 7 variables.
  - `build_city_dataframe(city, response, variable_names)`: builds one city's dataframe from the binary response.
  - Loop over `zip(CITIES, responses)` and `pd.concat(..., ignore_index=True)` into one dataframe.
  - UTC offset captured per city (`utc_offset_seconds`).
  - Local-time shift of the `date` column and the `time_label` column via `np.select`.
  - Validated: 360 rows, 72 per city, labels observed 177 / forecast_today 63 / forecast_tomorrow 120, zero `Unmapped`.

- **A1 audit (2026-10-03):** history and files audited. Only 4 files were ever committed, with no personal paths, no secrets, and no sqlite file. `.gitignore` broadened to `*.sqlite` and `__marimo__/`. 
- **A2 (2026-10-10):** MIT `LICENSE` added (code only; the data keeps its own terms). `requirements.txt` hand-written with compatible-release pins (`~=`): marimo `~=0.24.2` (patch updates only, since it is 0.x), the other five `~=` to the minor version I run. `pip install --dry-run -r requirements.txt` confirmed it matches my environment. Local Python is 3.14.7.
- **A3-A4 (2026-10-10):** README written and pushed: description, work-in-progress note, "How it works", "Data notes", status checklist, local setup (Windows/PowerShell), data sources and attribution (Open-Meteo CC BY 4.0, both CAMS citations, Copernicus notice, Census source), and a License section. 
- **A5 (2026-10-17 to 2026-10-18):** About box (description and topics) added; pre-flight checks done; notes file reviewed and trimmed; repo flipped to public; logged-out check passed (README, status checkboxes, notes link, attribution links, clone URL). Cross-link added to the `python_business_automation` README ("Related project" section, below the Demos table). Git email settings repaired (see gotchas): both the global and repo-level `user.email` are now the noreply address, and the "misattributed" warning in GitHub Desktop is gone.
- **B1 (2026-10-22): JSON shape decided.** Plain records (flat list of row objects), written with `orient="records"`, `date_format="iso"`, `date_unit="s"`, `double_precision=2` (two decimals avoids implying false precision; it only affects the JSON text, not the dataframe). `indent=2` is optional. Helper columns: **drop `utc_offset_timedelta` once used** (`utc_offset_seconds` carries the same info), **keep `current_time_utc` and `current_time_local`**. This amends the 2026-09-30 decision to keep all three.
- **B2 (2026-10-22): JSON file written.** `fetch_data.py` builds `output_path` from the script's own location (`Path(__file__).resolve().parent.parent / "apps" / "public" / "data" / "aqi.json"`), creates the folder if needed (`output_path.parent.mkdir(parents=True, exist_ok=True)`), and writes the file with `to_json`. Verified: reads back as 360 rows × 13 columns, about 134 KB.
- **Decision (2026-10-22): the data file is not committed.** `aqi.json` is in `.gitignore`. The GitHub Action regenerates it on every run, and committing it meant daily noise while testing. Consequence: a fresh clone has no data until the fetch script runs.
- **Path change (2026-10-22):** marimo's docs say WASM exports copy a `public/` folder located in the same directory as the notebook, so the data lives in `apps/public/data/`, not the repo-root `public/` the plan originally had.
- **B3:** `fetch_data.py` restructured: processing lives in `main()` with the `__main__` guard, `zip(..., strict=True)`, section comments, `observed` renamed to `past`. A separate labeling function was skipped (fixed schedule; testing by deliberate breakage instead).
- **B4:** four checks run after labeling and before the write, each raising `ValueError` with a descriptive message: no `Unmapped` labels; total row count (computed from `params` and `CITIES`); equal row count per city; no pollutant column entirely NaN. Each was tested by deliberately breaking the data: exit code 1 and `aqi.json` unchanged. A bad URL also fails loudly. The 1-hour request cache was left as is.
- **C1:** notebook loads `aqi.json` via `mo.notebook_location()`, parses the two `current_time_*` columns, casts pollutants to float64, uses `precise_float=True`, and adds `local_day` and `time_period`.
- **C2:** WASM smoke test passed. `marimo check --select MW` is clean, the export copies `apps/public/`, the data loads in the browser, and Altair installs and renders. Browser pandas is 3.0.2 (local 3.0.6). `site/` is gitignored.
- **C3-C6:** Altair chosen. Controls (city dropdown, pollutant dropdown built from a display-name dictionary with units, city multiselect), a single-city chart, and a multi-city comparison chart with past solid and forecast dashed.
- **Decisions:** JSON over Parquet; unpinned browser packages accepted; DST caveat accepted for now.
- **C complete (notebook).** Finished since the last update:
  - Snapshot section: KPI card (today's average AQI vs yesterday, category caption, direction arrow, `n/a` fallbacks when a value is missing), six small pollutant charts in two fixed rows of three, title and dashed-line caption.
  - Table section: city-filtered `mo.ui.table` with renamed headers (units included), `page_size=24`, date `format_mapping`, full attribution block beneath it.
  - Page header: title, one-sentence description, "Data refreshed" time read from `current_time_utc`, and a short Open-Meteo/CAMS credit. Full attribution stays at the bottom.
  - Fixes from review: invalid CSS key in a `.style()` call, a crash in the AQI category code when the average is missing, and a meaningless dash legend on the in-depth chart.
- **Decisions (C):**
  - "What stood out today" analysis is dropped; the KPI card and charts cover it.
  - Two fixed rows of three charts, no `wrap=True`; check on a phone after deployment.
  - Two-tier attribution: a short credit at the top, the full block by the table.
  - The same dropdowns shown in two sections were tested and are not a problem.

### In progress
- Nothing started. Next up: a final export and browser check of the whole notebook, then **D1**.

## 5. Remaining work

**Pacing:** work in 30-minute blocks. A 60-minute sitting is two blocks, a 90-minute sitting is three. Each block should end at a clean commit. Estimates are padded for a learning pace, so they assume time to read, experiment and break things. Total: about 27-29 blocks (~14 hours).

**README upkeep:** update the Status checklist whenever a milestone is reached.

### Phase A: Public-readiness (complete)

A1-A5 complete (see Status). Planned at 5 blocks; actual was roughly double, mostly README iteration and attribution research.

**Hold off on the scheduled workflow until the pipeline is ready** (see gotchas), or add a workflow with only a manual trigger for now.
### Phase B: Finish `fetch_data.py` (done)

### Phase C: Marimo notebook (done)
Planned at ~7-9 blocks left; the "what stood out today" cell was dropped.

### Before Phase D: final check (~1 block)
Export again and look at the whole site in the browser: sorting the date column across a month boundary, the table's download button (does it export formatted or raw values?), the "Data refreshed" time against `aqi.json`, load time, and the KPI card for all five cities.

### Phase D: Automation and deploy (~6 blocks; least predictable)
- D1: workflow skeleton, manual trigger only. Check the current GitHub docs for Pages deployment, and that the Python setup offers 3.14.
- D2-D3: add the fetch step before the export step; the script creates `apps/public/data` itself.
- D4: enable Pages and upload `site/`.
- D5: add schedule and push triggers. Pick a run time that isn't near local midnight in any of the five cities (around 10:00 UTC), and verify the failure-email setting.
- D6: handle the 60-day inactivity rule. *Decision needed:* keep-alive step vs reminder.

### Phase E: Polish (~2-3 blocks)
- README: tick the JSON output and Notebook boxes now; replace the "notebook has no data to load" sentence; add the local-setup step "run `scripts/fetch_data.py` before opening the notebook"; add the rounding to the list of changes; update the status as milestones land; screenshots and live link.
- Add the live site link to the repo's About box (Website field).
- Update the "Related project" text in the `python_business_automation` README once the site is live.
- Check the live site on a phone (the layout uses fixed-width charts).
- Confirm `altair~=6.3` is in `requirements.txt`.

### Open decisions
DST handling before launch (accept, or convert with the IANA zone); keep-alive approach (D6).

Estimate: ~9-10 blocks (~5 hours) remaining, padded for the pace so far.

## 6. Gotchas and lessons learned

- **Open-Meteo timestamps come back as raw UTC epoch seconds even with `timezone="auto"`.** Add each city's `utc_offset_seconds` to the `date` column yourself, or everything is silently shifted.
- **Parameter typos fail silently.** `timezone`, not `time_zone`.
- **Don't use `utc=True`** when parsing if you're storing local times. The `date` column is tz-naive; strip tz from "now" with `.dt.tz_localize(None)` before comparing.
- **`np.select`** (conditions list, choices list, default) is cleaner than nested `np.where` for the 3-way label. Keep `default='Unmapped'` as a canary.
- **Date arithmetic:** `.dt.date + pd.Timedelta(days=1)` stays a date; `pd.DateOffset` promotes to Timestamp and breaks `==` comparisons.
- **`requests_cache` creates a sqlite file**; it is gitignored.
- **Scheduled workflows in public repos are automatically disabled after 60 days with no repository activity.** GitHub's docs say this, and once disabled, the daily job silently stops until re-enabled. Fine while actively developing; for the finished site, plan a keep-alive (e.g. a workflow step that makes periodic activity) or a calendar reminder to check Actions.
- **Open-Meteo terms:** the free API is for non-commercial use, and the data is CC BY 4.0, so attribution is required (link to Open-Meteo.com, link to the license, say if changed). Some older Open-Meteo repos state CC BY-NC instead. Check https://open-meteo.com/en/license for the current wording, especially if the repo ever supports paid work.
- PowerShell blocked venv activation by execution policy (resolved during setup).
- Git LF/CRLF warning on Windows is harmless.
- A push to GitHub from GitHub Desktop once hung on a 504; retrying later worked.
- **`.gitignore` patterns match the exact file name.** requests_cache creates `.cache.sqlite` (leading dot) from `CachedSession('.cache')`, so `cache.sqlite` didn't match. `*.sqlite` covers it.
- **`git log` opens a pager** that can look like duplicated output in the VS Code terminal. Use `git --no-pager log ...`.
- **Audit commands that worked:** `git ls-files` (tracked files), `git log --all --name-only --pretty=format: | Sort-Object -Unique` (every file ever committed), `git grep -n -i "term" (git rev-list --all)` (search all history).
- **The air quality data is modeled, not measured.** Open-Meteo's air quality data comes from CAMS (Copernicus) model forecasts. Locations outside Europe use the CAMS global atmospheric composition forecasts (~40 km, 0.4° grid; the European model only covers Europe). Each city's values describe the whole grid cell, so within-city detail is smoothed. The README says this.
- **Attribution requirements:** Open-Meteo's data is CC BY 4.0, which requires credit, a link to the license, a note of any changes, and a link to Open-Meteo next to wherever the data is displayed. Open-Meteo's air quality page also asks users to cite the CAMS European ENSEMBLE data (its own wording). Separately, the CAMS global dataset (DOI 10.24381/04a0b097) asks for its own citation plus a Copernicus attribution notice, both in the dialog behind "Citation and attribution" on the dataset page. The license page is spelled `open-meteo.com/en/licence`.
- **Hourly vs 3-hourly is unresolved.** CAMS lists single-level global fields as hourly, but Open-Meteo's table lists the global data as 3-hourly. I can't tell which one Open-Meteo actually uses, so the README just says "hourly", which is what the API returns.
- **VS Code's Markdown preview doesn't render task-list checkboxes** (`- [ ]`); GitHub does. Check checkboxes on github.com.
- **Code blocks inside numbered lists:** flush-left fences split the list into separate lists but still render with the right numbers on GitHub; indenting them by exactly 3 spaces nests them properly (4 spaces makes a code block inside a code block).
- **`~=` pins:** `~=1.7` means >=1.7 and <2.0, while `~=0.24.2` means >=0.24.2 and <0.25. pip installs the newest version inside the range, so a fresh install can differ from what I tested.
- **After any config change, verify the next commit:** `git --no-pager log -1 --format="%an | %ae"`.
- **The Quarto extension can hijack the Markdown preview button/shortcut in VS Code.** Fix: stop the preview with Ctrl+C in the terminal, then right-click the generated files in GitHub Desktop and choose Discard changes.
- **`DataFrame.to_json` defaults to epoch milliseconds**, which silently turns local timestamps into apparent UTC times; pandas 3 deprecates it (`Pandas4Warning`). Always pass `date_format="iso"`. ISO output of tz-naive columns has no suffix (local), tz-aware UTC columns end in `Z`.
- **Negative timedeltas serialize as e.g. `P-1DT20H0M0S`** (= −4 h). `pd.to_timedelta` parses it, but `read_json` returns it as a string. Prefer an integer like `utc_offset_seconds`.
- **Open-Meteo returns 32-bit floats**, so values print like `4.5999999046`. `double_precision=2` cleans the JSON text.
- **`pd.read_json` only auto-converts date-like column names** (`date`); other time columns load as strings. Whole-number float columns load as `int64`.
- **`df.drop(columns=[...])` returns a new dataframe**: assign it back, or nothing changes (no error).
- **Build paths from `Path(__file__)`** so they work wherever the script is run from; `.parent` once is `scripts/`, twice is the repo root. `/` joins path pieces on any OS.
- **marimo WASM exports copy a `public/` folder located next to the notebook** (`apps/public/`), and data paths use `mo.notebook_location()`.
- **`.gitignore` patterns with a slash in the middle are anchored** to the `.gitignore`'s folder; a bare filename like `aqi.json` matches in any folder. `git check-ignore -v <path>` shows which rule applies.
- **`$LASTEXITCODE`** (PowerShell) holds the last program's exit code; 0 is success. The 1-hour request cache can mask a failed fetch, so to test failure, change the request (e.g. break the URL).
- **`round(NaN)` raises `ValueError`:** check `pd.isna(...)` before rounding.
- **`pd.read_json` parses floats approximately by default** (`1.68` can come back as `1.6800000000000002`). Use `precise_float=True`.
- **`groupby(...).size()` omits groups with no rows**, so a missing city doesn't show as 0.
- **`df2 = df1` does not copy;** both names point at the same object. Use `.copy()`.
- **`mo.ui.dropdown` with dict options:** `.value` is the dict value (the column), `.selected_key` is the display name, and the `value=` argument takes the key.
- **`mo.ui.table`:** no header-rename option (rename columns in a display dataframe); `format_mapping` formats display only, so sorting still uses real values; key it by the displayed column name.
- **`mo.stat`:** `direction=None` for no arrow; `target_direction` says which direction is good (`"decrease"` for AQI).
- **Layout:** default page width is `compact`; use `mo.vstack(..., align="center")` to center; `hstack` defaults to `space-between`.
- **Altair:** `legend=` goes inside the encoding it describes; `legend=None` hides it (commenting out `alt.Legend` does not); dash patterns are assigned alphabetically, so set `domain` and `range` explicitly; `point=True` breaks dash legend symbols; the default tooltip date format drops the hour; `width` is the plot area, not the whole chart; `configure_*` goes on the outermost chart.
- **WASM export:** serve it over HTTP (`python -m http.server --directory site --bind 127.0.0.1`); the browser loads Python from a CDN, so viewers need internet access; check pandas/platform in the browser with `f"pandas {pd.__version__} on {sys.platform}"` (shows `emscripten`).
- **Comparing `None` to a number raises `TypeError`:** handle the missing case first, before any `<` or `>`.
- **Attribution:** show a short Open-Meteo credit near the top of the page, not only in a footer or beside the table. The full citations can stay in one place.
- **Per-row `hstack(wrap=True)` wraps each row independently**, giving uneven rows (2, 1, 2, 1). For responsive layouts, put all charts in one wrapping `hstack`.
