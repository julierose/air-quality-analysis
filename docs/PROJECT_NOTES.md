# air-quality-analysis: Project Notes

> Living document. Update at the end of each working session, commit it to the repo, and re-upload it to the Claude Project knowledge.
> **Last updated:** 2026-09-30; code status as of 2026-09-26

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

### Not started
B3-B4, Phases C, D, E

## 5. Remaining work

**Pacing:** work in 30-minute blocks. A 60-minute sitting is two blocks, a 90-minute sitting is three. Each block should end at a clean commit. Estimates are padded for a learning pace, so they assume time to read, experiment and break things. Total: about 27-29 blocks (~14 hours).

**README upkeep:** update the Status checklist whenever a milestone is reached.

### Phase A: Public-readiness (complete)

A1-A5 complete (see Status). Planned at 5 blocks; actual was roughly double, mostly README iteration and attribution research.

**Hold off on the scheduled workflow until the pipeline is ready** (see gotchas), or add a workflow with only a manual trigger for now.
### Phase B: Finish `fetch_data.py` (B1-B2 done; ~2 blocks left)
- **B3:** Turn the exploration into a clean end-to-end script (functions, `main()`, debug prints removed). Decide whether to rename the `observed` label. The past hours are also model output, not measurements, so `observed` may mislead readers of the JSON and charts. *Decision needed.*
- **B4:** Exit non-zero on failure; test by deliberately breaking the fetch.

### Phase C: Marimo notebook, `apps/air_quality_analysis.py` (~10-11 blocks)
- **C1:** After loading, convert dtypes explicitly: `read_json` only auto-converts `date`, so `current_time_utc` and `current_time_local` need `pd.to_datetime`, and whole-number float columns (e.g. `carbon_monoxide`, `ozone`) come back as `int64`, so cast them so the types don't depend on that day's data. The path is `mo.notebook_location() / "public" / "data" / "aqi.json"`.
- **C2:** WASM export smoke test of that minimal notebook, early, since Pyodide compatibility is the main technical risk. When testing the WASM export, also check which pandas version Pyodide bundles, since it may differ from my local 3.0.x. Also confirm the export copies `apps/public/` and the notebook finds the data in the browser.
- **C3-C4:** First chart (one city, one pollutant). *Decision needed: chart library (Altair, Plotly, other).*
- **C5-C6:** Multi-city and multi-pollutant comparison with marimo UI controls.
- **C7:** Observed vs forecast styling (e.g. solid vs dashed).
- **C8-C9:** A computed "what stood out today" cell (worst city/metric, day-over-day change) so it earns the name *analysis*.
- **C10-C11:** Layout and polish. The live notebook needs visible credits next to the data: a link to Open-Meteo, and the Copernicus attribution notice (see gotchas).

### Phase D: Automation and deploy (~6 blocks; timing least predictable)
- **D1:** Workflow skeleton with a manual trigger only: checkout, Python setup, dependency install. Check that the Actions Python setup step offers 3.14, and match my local version if it does.
- **D2-D3:** Add the fetch and export steps; expect to debug failed runs. The workflow must run the fetch step before the export step, and the script creates apps/public/data itself because a fresh checkout has no such folder.
- **D4:** Enable Pages (GitHub Actions source) and deploy.
- **D5:** Add the schedule and push triggers; verify the failure-email setting (Settings → Notifications → Actions).
- **D6:** Handle the 60-day inactivity rule (see gotchas). *Decision needed:* keep-alive step vs calendar reminder.

### Phase E: Polish (~2-3 blocks)
- Expand the README (architecture diagram, screenshots, live link), update the status checklist, and link the live site from the repo description. Also a README local-setup step to run scripts/fetch_data.py before opening the notebook, since the data file isn’t in the repo.

### Decision points (mine to make)
chart library (C3), keep-alive approach (D6).

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
