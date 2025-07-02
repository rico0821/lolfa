# LoL eSports Player Card Web App

## Project Purpose

A web app for managing, creating, and analyzing League of Legends eSports player stat cards. Supports batch creation, class management, stat adjustments, and robust search/filtering.

---

## Key Concepts

- **Creation Method**: The algorithm or process used to generate a set of cards (e.g., stat pipeline, custom adjustments).
- **Class**: A set of cards created with a specific method and conditions (e.g., by year, league, or custom filter).
- **Stat Adjustments**: Additive or multiplicative modifications applied to stats at the card or class level (without altering original stats).
- **Batch Operations**: Creating or modifying multiple cards/classes at once (e.g., all seasons for a league).

---

## Features

### Implemented

- **Card Table**: Search, filter, and sort all cards by player, team, league, year, split, and class.
- **Admin Card Preview**: Visual preview of any card with selectable backgrounds.
- **Stat Calculation Pipeline**: Multi-step, normalized, and reliability-adjusted stat computation (see `stat_card.py`).
- **SQLite Database**: Stores all card data, including creation method and class.
- **Batch DB Population**: Scripted batch creation of cards from raw CSVs (see `db_init.py`).
- **Basic Test Coverage**: Unit tests for stat pipeline (see `tests/`).

### Planned

- **Web UI for Class Management**: Create, edit, and delete classes of cards from the app.
- **Web UI for Stat Adjustments**: Apply additive/multiplicative adjustments at card/class level.
- **Batch Operations in UI**: Batch create/modify card sets for all league seasons, etc.
- **Dynamic Image Management**: Upload/select player/team/class images via the UI.
- **Export/Share Cards**: Download or share card images.
- **Admin Authentication**: Secure admin features.
- **Enhanced Error Handling**: User feedback for failed actions.
- **Input Validation & Security**: Prevent SQL injection and bad data.
- **Performance Improvements**: Caching, optimized queries.
- **Expanded Testing**: More unit/integration/UI tests.

---

## Technical Notes

- **Data Source**: Raw CSVs in `data/` (not in repo, see `.gitignore`).
- **DB Schema**: See `db_init.py` for table structure (includes creation_method, class).
- **Stat Pipeline**: Modular, stepwise, and testable (`stat_card.py`).
- **Batch Population**: Run `db_init.py` to populate DB from all available CSVs (limited to 5 splits for speed in dev).
- **Frontend**: Streamlit app (`app.py`), two main tabs (Card Table, Admin Card Preview).
- **Static Assets**: Images in `static/` (backgrounds, logos, player/class icons).

---

## Roadmap

| Feature/Task                        | Status      | Notes/Links                |
|--------------------------------------|-------------|----------------------------|
| Card Table (search/filter/sort)      | Done        | `app.py`                   |
| Admin Card Preview                   | Done        | `app.py`                   |
| Stat Calculation Pipeline            | Done        | `stat_card.py`             |
| Batch DB Population (script)         | Done        | `db_init.py`               |
| Web UI: Class Management             | Planned     |                            |
| Web UI: Stat Adjustments             | Planned     |                            |
| Batch Operations in UI               | Planned     |                            |
| Dynamic Image Management             | Planned     |                            |
| Export/Share Cards                   | Planned     |                            |
| Admin Authentication                 | Planned     |                            |
| Enhanced Error Handling              | Planned     |                            |
| Input Validation & Security          | Planned     |                            |
| Performance Improvements             | Planned     |                            |
| Expanded Testing                     | Planned     |                            |

---

## How to Run

1. Install dependencies:  
   `pip install -r requirements.txt`
2. (Optional) Populate DB:  
   `python db_init.py`
3. Start the app:  
   `streamlit run app.py`

---

## Developer Notes

- For batch DB population, edit/remove the 5-split limit in `db_init.py` for full data.
- To add new stat pipelines or creation methods, extend `stat_card.py` and update `db_init.py`.
- For new features, follow the roadmap and update this file. 