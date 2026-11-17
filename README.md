# Job Watcher

[![Tests](https://github.com/mattoxknod/job-watcher/actions/workflows/tests.yml/badge.svg)](https://github.com/mattoxknod/job-watcher/actions/workflows/tests.yml)
[![Daily run](https://github.com/mattoxknod/job-watcher/actions/workflows/daily.yml/badge.svg)](https://github.com/mattoxknod/job-watcher/actions/workflows/daily.yml)

A tool that watches the job market on its own. Once a day GitHub Actions calls
every employer's job board, saves what each one returns, compares it with what
it saw before, records what is new and what is gone, and publishes the result.

**Live site:** https://mattoxknod.github.io/job-watcher/

The watch is aimed at financial analyst, data analyst, credit and risk analyst,
and investment banking work, together with the one-to-three year rotational and
development programs that hire into those roles.

---

## How a run works

Every run does five things, in this order:

1. **Calls every source** and saves what it returns, compressed, to
   `data/raw/<date>/<source>.json.gz`. One source failing does not stop the
   run. A source that fails writes no raw file that day, and the result of
   every source, success or failure, is recorded in `data/raw/<date>/_run.json`.
2. **Builds the history** from the raw files alone.
3. **Writes the status file.**
4. **Opens a GitHub Issue** titled with the date, listing the new and the
   removed postings with a link each, and closes the previous day's issue. The
   issue is opened every day, including a day with no changes.
5. **Commits** the raw files, the history file and the status file.

A successful run is one that finishes and commits, even when some sources
failed. A second run on the same day replaces that day's raw files, builds the
history again, and updates that day's issue, so each day counts once.

### The command that builds the history file from the raw files

```bash
uv run python -m jobwatcher.cli build
```

It reads every `data/raw/<date>/<source>.json.gz` and writes `data/history.csv`
and `data/status.json`. It never touches the network, so running it again
produces the same file, and a change to a rule applies to every day of the
history.

Other commands:

```bash
uv run python -m jobwatcher.cli fetch   # call every source, save raw files
uv run python -m jobwatcher.cli run     # fetch, then build
uv run python -m jobwatcher.cli issue   # open or update today's issue
uv run pytest                           # the test suite
```

---

## The watch list

Eighteen employers across three applicant tracking systems. Every board returns
JSON to a request made with no login; none of them is read as HTML.

| # | Employer | Applicant tracking system | Board |
|---|---|---|---|
| 1 | Walmart | Workday | `walmart.wd504` / `WalmartExternal` |
| 2 | Bank of America | Workday | `ghr.wd1` / `lateral-us` |
| 3 | Citi | Workday | `citi.wd5` / `2` |
| 4 | Capital One | Workday | `capitalone.wd12` / `Capital_One` |
| 5 | Truist | Workday | `truist.wd1` / `Careers` |
| 6 | PNC Financial Services | Workday | `pnc.wd5` / `External` |
| 7 | Northern Trust | Workday | `ntrs.wd1` / `northerntrust` |
| 8 | The Vanguard Group | Workday | `vanguard.wd5` / `vanguard_external` |
| 9 | Federal Reserve System | Workday | `rb.wd5` / `FRS` |
| 10 | Tyson Foods | Workday | `tysonfoods.wd5` / `TSN` |
| 11 | J.B. Hunt Transport Services | Workday | `jbhunt.wd501` / `Careers` |
| 12 | The Coca-Cola Company | Workday | `coke.wd1` / `coca-cola-careers` |
| 13 | Acxiom | Workday | `acxiomllc.wd5` / `AcxiomUSA` |
| 14 | Arkansas Children's | Workday | `archildrens.wd1` / `external_career_site` |
| 15 | University of Arkansas System | Workday | `uasys.wd5` / `UASYS` |
| 16 | FedEx | Workday | `fedex.wd1` / `FXE-MEISA-External` |
| 17 | Amazon | Amazon Jobs (in-house) | `amazon.jobs/en/search.json` |
| 18 | JPMorgan Chase | Oracle Recruiting Cloud | `jpmc.fa.oraclecloud.com` |

Arkansas Children's and the University of Arkansas System are on the list for
Little Rock and Northwest Arkansas, which the national employers above barely
cover on their own.

The Federal Reserve board is the shared Federal Reserve System one, so the
St. Louis and Dallas banks both come through that single source.

### Boards read with a search term

Two boards list more than 5,000 postings, so they are requested with a search
term rather than in full:

| Source | Search term | Why |
|---|---|---|
| Amazon | `analyst` | The full board runs to hundreds of thousands of postings. |
| JPMorgan Chase | `analyst` | The full board reported 6,892 postings. |

Every other board is read in full, with no search term, so postings outside the
watched roles are kept too.

### A note on rate limits

Workday serves at most 20 postings per request, so a board with two thousand
openings takes a hundred requests. Several tenants answer `429 Too Many
Requests` when those arrive back to back. `src/jobwatcher/http.py` keeps a
minimum gap between requests to the same host and waits out a 429, honouring
`Retry-After` when the server sends one. A board that still cannot be read is
recorded as a failed source for that day rather than being written out
half-read, because a partial read would look like every missing posting had
been removed.

For the same reason, a board that answers cleanly but lists no postings at all
is treated as a failed read rather than as an employer with nothing open. Every
board here always has openings, so an empty response means something changed on
their end — a renamed site, a board moved behind a login — and writing it out
would mark all of that source's postings removed in one day.

---

## The title rule

A posting is **in role** when its title names one of the tracks below **and**
does not name a job above the analyst/associate level. The rule reads the title
only, so it gives the same answer for every day of the history, and changing it
re-labels the whole history on the next build. It lives in
`src/jobwatcher/role.py`.

**In role** when the title matches any of:

| Track | Matched wording |
|---|---|
| Financial analysis, FP&A | `financial/finance analy…`, `FP&A`, `financial planning`, `corporate finance`, `treasury`, `valuation`, `accounting analy…` |
| Data, analytics, BI | `data analy…`, `business intelligence`, `analytics analy…`, `reporting analy…`, `business analy…`, `quantitative analy…` |
| Credit and risk | `credit analy…`, `credit risk`, `risk analy…`, `underwrit…`, `portfolio analy…`, `fraud analy…` |
| Investment banking, markets | `investment bank…`, `capital markets`, `equity research`, `investment analy…`, `research analy…` |
| Supply chain, merchandising, pricing | `supply chain analy…`, `replenishment`, `merchandis… analy…`, `pricing analy…`, `procurement analy…`, `sourcing analy…`, `operations analy…` |
| Early-career programs | `analyst program`, `rotational`, `development program`, `leadership program`, `summer analyst`, `new grad`, `campus`, `intern` |

**Not in role** when the title also names a level above analyst or associate —
`manager`, `director`, `vice president`, `VP`, `head of`, `chief`, `principal`,
`partner`, `lead`, `supervisor`, `executive` — unless the title is a program
posting (`analyst program`, `development program`, `leadership program`,
`rotational`, `summer analyst`, `intern`), which keeps its place regardless.

Each pattern is matched on word boundaries, so `intern` does not fire on
*international* or *internal*.

Every posting each board returns is kept in the history whether or not it is in
role; `in_role` is only a label, and the Browse page switches between the two.

---

## The region rule

Every board writes locations its own way — `Dallas, TX`, `US - GA - Atlanta`,
`USA-AR-FORT-SMITH-08134-SAMS-CLUB`, `Bellevue, Washington, USA`, `Conway`,
`Remote/Homebased`, `2 Locations` — so there is no location field they share.
`src/jobwatcher/region.py` sorts each posting into exactly one region from its
location text, and the Browse page filters on it.

Three regions are **primary**, the ones this watch is aimed at:

| Region | Covers |
|---|---|
| Northwest Arkansas | Fayetteville, Bentonville, Rogers, Springdale, Bella Vista, Siloam Springs |
| Little Rock | Little Rock, North Little Rock, Maumelle, Conway, Benton, Bryant |
| Dallas–Fort Worth | Dallas, Fort Worth, Plano, Irving, Frisco, Arlington and the rest of the metroplex |

Anything else falls back, in order, to: `Remote`, `Multiple locations` (what
Workday writes when one posting covers several places), the US state, then
`International`, `Other U.S.` or `Other`.

The order matters, because a city name alone is not enough. **The state always
beats a shared city name**, so `Fayetteville, NC` is North Carolina rather than
Northwest Arkansas, `Arlington, VA` is Virginia rather than Dallas–Fort Worth,
and `Conway, SC` is South Carolina. Only when a board names no state at all —
Acxiom writes just `Conway` — does a short list of distinctive city names decide
it. A two-letter state code counts only when the board capitalised it, so an
ordinary word is never read as a state.

---

## The data

Two files at fixed paths. The site loads both in the browser and does all the
arithmetic there.

### `data/history.csv`

One row per posting.

| Column | Meaning |
|---|---|
| `posting_id` | `<source>:<source_id>` |
| `source` | Which source listed it |
| `source_id` | The source's own ID for the posting |
| `employer` | Employer name |
| `title` | Posting title |
| `location` | Location, exactly as the board writes it |
| `department` | Department, where the board gives one |
| `posted_date` | Posting date, where the board gives one |
| `url` | Link to apply |
| `in_role` | `true` / `false`, from the title rule |
| `first_run` | `true` for a posting listed in the first raw file of its source |
| `first_seen` | First day the tool saw it |
| `last_seen` | Last day its source listed it |
| `status` | `open` or `removed` |
| `removed_date` | The day it was marked removed |
| `region` | The region the location falls in (see below) |

`region` is the one column beyond what the project asks for. It is appended
after `removed_date`, so the required columns keep the exact order the project
lists them in.

Dates are UTC dates written `YYYY-MM-DD`; every run takes the UTC date of the
moment it runs. A column a source does not provide is left empty for that
source's rows — Workday gives no department on its search endpoint, for
instance, and reports posting dates only as "Posted 5 Days Ago", which the
build resolves against the run date and leaves empty for "30+ Days Ago".

The history rules, in `src/jobwatcher/history.py`:

* A posting seen for the first time gets that day as its `first_seen`.
* Every posting its source lists that day gets that day as its `last_seen`.
* An open posting is marked `removed`, with that day's date, when its source
  has a raw file for that day and no longer lists it. A source that failed
  removes nothing.
* A removed posting that its source lists again becomes open again, with its
  `removed_date` cleared and its `first_seen` unchanged.
* Rows are sorted by `posting_id`.

### `data/status.json`

| Key | Meaning |
|---|---|
| `run_time` | UTC time of the latest run |
| `first_run_date` | Date of the earliest raw file |
| `days_with_success` | Number of different dates with a raw file |
| `open` | Number of open postings |
| `new_today` | Postings first seen in the latest run, leaving out first-run postings |
| `removed_today` | Postings removed in the latest run |
| `sources` | One entry per source: `name`, `ok`, `count` |

---

## The site

Three pages sharing one navigation bar, one set of fonts and one set of colors.
Each loads the two data files and computes everything in the browser.

* **`index.html` — Today.** The time of the last run, the status of every
  source, the four counts from the status file, and the lists of new and
  removed postings in the latest run.
* **`browse.html` — Browse.** The open postings, with a switch between postings
  in my role (the default) and all postings; filters for employer, location and
  days open; a search box matching titles; a sort by first-seen date; an apply
  link on every posting; and a star that saves a posting to a shortlist kept in
  the browser, which survives a reload.
* **`market.html` — Market.** Seven sections, each with a heading that states the
  finding, a paragraph explaining it, and a chart: new postings per day (all and
  in role), removed postings per day, open postings per employer, days open with
  the median, the share removed within seven days, the top locations, and a seventh section of
  my own: open postings by region.
  Postings with `first_run` set are left out of the definitions that need a real
  start date.

The site is installable: it has a web app manifest and a service worker, and
installs from the browser as an app. Online, the pages load the data files from
the network; offline, the site still opens and shows the last data it loaded.
The charts are hand-drawn SVG rather than a charting library, so nothing has to
be fetched from a CDN for the installed app to work.

---

## Every file

| Path | What it does |
|---|---|
| `src/jobwatcher/sources.py` | The watch list: every employer, its applicant tracking system, and how to address its board |
| `src/jobwatcher/http.py` | Outbound HTTP, with throttling and 429-aware retries |
| `src/jobwatcher/adapters/__init__.py` | Picks the adapter for a source |
| `src/jobwatcher/adapters/workday.py` | Reads Workday boards and maps them to the common columns |
| `src/jobwatcher/adapters/amazon.py` | Reads Amazon's `search.json` board |
| `src/jobwatcher/adapters/oracle.py` | Reads Oracle Recruiting Cloud boards |
| `src/jobwatcher/role.py` | The title rule |
| `src/jobwatcher/region.py` | Turns a board's location text into one region |
| `src/jobwatcher/history.py` | First-seen, last-seen and removed logic; reads and writes `history.csv` |
| `src/jobwatcher/store.py` | Paths on disk and the raw-file reader and writer |
| `src/jobwatcher/fetch.py` | Calls every source, saves raw files, records each result |
| `src/jobwatcher/build.py` | Rebuilds `history.csv` and `status.json` from the raw files |
| `src/jobwatcher/issue.py` | Renders and posts the daily GitHub Issue |
| `src/jobwatcher/cli.py` | The `fetch`, `build`, `issue` and `run` commands |
| `scripts/make_icons.py` | Generates the app icons the manifest points at |
| `tests/test_role.py` | Tests for the title rule |
| `tests/test_region.py` | Tests for the region rule |
| `tests/test_fetch.py` | Tests that a failed source is recorded and does not stop the run |
| `tests/test_normalize.py` | Tests converting each source to the common columns |
| `tests/test_history.py` | Tests for first-seen, last-seen and removed logic |
| `.github/workflows/daily.yml` | The daily run: fetch, build, issue, commit |
| `.github/workflows/tests.yml` | Runs the test suite on every push |
| `index.html` | The Today page |
| `browse.html` | The Browse page |
| `market.html` | The Market page |
| `assets/style.css` | Shared fonts, colors and chrome for all three pages |
| `assets/data.js` | Loads and parses the two data files; shared page chrome |
| `assets/charts.js` | The SVG charts, tooltips, legends and table views |
| `assets/icon.svg`, `assets/icon-*.png` | App icons |
| `manifest.webmanifest` | Web app manifest, so the site installs as an app |
| `sw.js` | Service worker: cache-first shell, network-first data |
| `data/raw/<date>/<source>.json.gz` | What each source returned that day |
| `data/raw/<date>/_run.json` | Each source's result that day, success or failure |
| `data/history.csv` | One row per posting |
| `data/status.json` | The latest run |
| `pyproject.toml`, `uv.lock` | Dependencies, managed by uv |

---

## Running it locally

```bash
uv sync
uv run python -m jobwatcher.cli run
uv run pytest
python -m http.server 8000   # then open http://localhost:8000
```

The site must be served over HTTP rather than opened as a `file://` path: the
pages are ES modules and the service worker only registers over HTTP.
