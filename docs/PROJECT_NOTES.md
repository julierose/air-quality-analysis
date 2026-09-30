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
| Visibility | **Go public early, while under construction** (updated 2026-09-30) | Portfolio visibility; build in the open. Requires the public-readiness steps in section 5, Phase A |
| Editor | marimo browser editor (`python -m marimo edit ...`) from VS Code terminal; GitHub Desktop for commits | Personal preference |
| Dependencies | `.venv` locally; consider PEP 723 inline deps in the notebook for WASM export | Only Pyodide-compatible packages work in WASM (pandas, numpy, altair/plotly are fine) |

Repo: https://github.com/julierose/air-quality-analysis

### Planned structure
```
air-quality-analysis/
├── apps/air_quality_analysis.py      # marimo notebook
├── scripts/fetch_data.py             # data pull
├── public/data/aqi.json              # overwritten daily
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
- `timezone: "auto"` (spelled exactly this way; an unknown parameter is silently ignored)

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

### Not started
See section 5.

## 5. Remaining work

**Pacing:** work in 30-minute blocks. A 60-minute sitting is two blocks, a 90-minute sitting is three. Each block should end at a clean commit. Estimates are padded for a learning pace, so they assume time to read, experiment and break things. Total: about 27-29 blocks (~14 hours).

### Phase A: Public-readiness (~5 blocks; do first)

Goal: a repo that looks intentional while it is clearly marked as a work in progress.

- **A1: Audit.** Review `git log` and the files for anything personal or sensitive (local paths, emails, notes); git history becomes public too. No API keys are involved (the Open-Meteo free API is keyless). Confirm `.gitignore` covers `.venv/`, the requests_cache sqlite file, and `__marimo__/` if you don't want it tracked.
- **A2: LICENSE and `requirements.txt`.** Without a license, default copyright applies and nobody can legally reuse the code. MIT is the common choice for portfolio projects. *Decision needed.* Requirements: marimo, openmeteo-requests, requests-cache, retry-requests, pandas, numpy (pin versions later).
- **A3-A4: README v0** (two passes):
  - Pass 1: title, one-line description, visible "Work in progress" note, the pipeline in 4 lines (fetch, export, deploy), status checklist, local setup (venv, install requirements, `python -m marimo edit apps/air_quality_analysis.py`).
  - Pass 2: **data attribution** ("Weather data by Open-Meteo.com" with a link, a link to the license CC BY 4.0, a note that the data is processed), the Census citation (section 3), and a license section.
- **A5: Go public.** Repo description and topics (e.g. `python`, `marimo`, `air-quality`, `open-meteo`, `github-actions`, `data-visualization`); leave Pages off for now. Flip to public, then add the cross-link from the `python_business_automation` README.

**Hold off on the scheduled workflow until the pipeline is ready** (see gotchas), or add a workflow with only a manual trigger for now.

### Phase B: Finish `fetch_data.py` (~4 blocks)
- **B1:** Choose the JSON shape (records-oriented is the default suggestion) and confirm how timestamps and timedeltas serialize. *Decision needed.*
- **B2:** Write `public/data/aqi.json`, overwriting each run.
- **B3:** Turn the exploration into a clean end-to-end script (functions, `main()`, debug prints removed).
- **B4:** Exit non-zero on failure; test by deliberately breaking the fetch.
- **Keep the helper columns** (`current_time_utc`, `utc_offset_timedelta`, `current_time_local`) in the output. They may be useful in the notebook and are small (decision 2026-09-30).

### Phase C: Marimo notebook, `apps/air_quality_analysis.py` (~10-11 blocks)
- **C1:** Load the JSON via `mo.notebook_location() / "public" / "data" / "aqi.json"` and confirm it works locally.
- **C2:** WASM export smoke test of that minimal notebook, early, since Pyodide compatibility is the main technical risk.
- **C3-C4:** First chart (one city, one pollutant). *Decision needed: chart library (Altair, Plotly, other).*
- **C5-C6:** Multi-city and multi-pollutant comparison with marimo UI controls.
- **C7:** Observed vs forecast styling (e.g. solid vs dashed).
- **C8-C9:** A computed "what stood out today" cell (worst city/metric, day-over-day change) so it earns the name *analysis*.
- **C10-C11:** Layout and polish.

### Phase D: Automation and deploy (~6 blocks; timing least predictable)
- **D1:** Workflow skeleton with a manual trigger only: checkout, Python setup, dependency install.
- **D2-D3:** Add the fetch and export steps; expect to debug failed runs.
- **D4:** Enable Pages (GitHub Actions source) and deploy.
- **D5:** Add the schedule and push triggers; verify the failure-email setting (Settings → Notifications → Actions).
- **D6:** Handle the 60-day inactivity rule (see gotchas). *Decision needed:* keep-alive step vs calendar reminder.

### Phase E: Polish (~2-3 blocks)
- Expand the README (architecture diagram, screenshots, live link), update the status checklist, and link the live site from the repo description.

### Decision points (mine to make)
License (A2), JSON shape (B1), chart library (C3), keep-alive approach (D6).

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
