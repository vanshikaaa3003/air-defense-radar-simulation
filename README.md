# Air Defense Radar Simulation — Rebuilt Edition

**Student:** Vanshika — 251302176  
**Team member:** Vinit — 251302086  
**University:** SGT University  
**Department:** School of Engineering and Technology  
**Course:** B.Tech CSE (AI & ML)

A desktop educational simulation built with Python and Tkinter. It uses fictional synthetic records to demonstrate data structures, searching, sorting, CSV persistence, visualization, and a status-only target lifecycle. It is not connected to real radar, aircraft, weapons, or defence systems.

## Features

- Animated 360-degree radar sweep, rings, color-coded synthetic targets, selected-target highlight, pause/resume and reset.
- Target table with ID search, threat/status filters, and priority ranking.
- Lifecycle workflow: `DETECTED → TRACKING → INTERCEPTED`; `DETECTED / TRACKING → ESCAPED`.
- Interception is only allowed after tracking. Completed targets leave the active count and radar display.
- Target status persists in `aircraft_records.csv`; every lifecycle action is appended to `event_history.csv`.
- Dashboard threat/lifecycle counts, recent events, CSV exports.
- 1,000 unique fictional records; original target IDs, coordinates, speed, altitude and timestamps are retained where available. Scores and categories are recalculated consistently.

## Scoring model

All inputs are normalized to 0–1 before weighting:

- `P = 1 - clamp(distance / 150, 0, 1)` (closer means larger proximity component)
- `V = clamp((speed - 150) / 1050, 0, 1)` (higher speed means larger speed component)
- `A = 1 - clamp(altitude / 15000, 0, 1)` (lower altitude means larger low-altitude component)

`score = round(100 × (0.50P + 0.30V + 0.20A), 2)`

Classification thresholds: HIGH ≥ 65; MEDIUM ≥ 40 and < 65; LOW < 40.

The old formula mixed raw units with different scales and added speed/altitude contributions to a distance baseline. For the actual data, this produced scores with mean 99.97, minimum 86.53, and 1,000/1,000 HIGH records after the 100-point cap. Normalization prevents any one raw unit scale from dominating, while explicit weights and thresholds make the new score explainable. The model is an educational ranking exercise, not a real-world threat model.

## DSA concepts used

1. **List:** `RadarModel.rows` stores all target dictionaries in dataset order. It is easy to iterate over for dashboard counts and rendering.
2. **Dictionary / hash lookup:** `RadarModel.by_id` maps target ID to its record, making exact ID lookup approximately O(1) average time.
3. **Heap / priority queue:** `build_priority_queue()` uses Python `heapq` with negative scores to implement a max-priority queue. Highest score is at the root and can be popped first. Completed targets are excluded.
4. **Searching:** `find()` performs dictionary lookup for exact IDs. The GUI's partial-ID filter scans records linearly (O(n)).
5. **Sorting:** `ranked()` sorts by descending score, then target ID for stable tie-breaking (O(n log n)).
6. **CSV handling:** `csv.DictReader` and `csv.DictWriter` load/save target records and event history. CSV is human-readable and easy to inspect in a spreadsheet.

## Project structure

- `main.py` — Tkinter GUI and event handlers
- `radar_core.py` — score calculation, CSV persistence, heap, search, lifecycle model
- `aircraft_records.csv` — 1,000+ fictional targets
- `event_history.csv` — persistent lifecycle event log
- `tests.py` — automated tests
- `README.md` — setup, algorithms, scoring and viva notes

## macOS setup and run

1. Install Python 3.10 or later. On macOS, install a Python distribution that includes Tkinter (the python.org installer is a straightforward option).
2. Unzip the project folder.
3. Open Terminal and change into the folder:
   `cd Air_Defense_Radar_Rebuilt`
4. Check Tkinter:
   `python3 -m tkinter`
   A small Tk window should appear. If not, install a Python build with Tcl/Tk support.
5. Launch:
   `python3 main.py`

No third-party Python packages are required. The interface uses the standard-library Tkinter, csv, heapq, and unittest modules.

## Run tests

From the project folder:

`python3 -m unittest -v tests.py`

The tests cover dataset size and unique IDs, score range and formula, thresholds, all three categories, heap ordering, lifecycle transitions, interception restrictions, escape, persistence, CSV export, searching and sorting.

## Viva preparation

**Q1. Why did the original program classify almost everything HIGH?**  
The original formula mixed distance, speed, and altitude in raw units. Speed and altitude often offset the distance penalty, and the result was capped at 100. The inspected file had 1,000 HIGH records, with mean score 99.97.

**Q2. Why normalize the inputs?**  
Distance, speed, and altitude use different numeric ranges and units. Normalization maps each factor to 0–1 so weights have a clear meaning.

**Q3. Why use a heap?**  
A priority queue lets the program access the highest-scoring active target efficiently. With `heapq`, insertion and removal are O(log n), and peeking at the root is O(1).

**Q4. Why use a dictionary as well as a list?**  
The list supports full iteration and display. The dictionary supports quick exact target-ID lookup.

**Q5. What prevents interception before tracking?**  
The model checks the current status and raises a `ValueError` unless it is `TRACKING`.

**Q6. What happens after interception or escape?**  
The status is persisted, the target is excluded from the active count and radar rendering, and an event is appended to the history CSV.

**Q7. How does data survive a restart?**  
The model writes target status to `aircraft_records.csv` and events to `event_history.csv`; both are reloaded at startup.

**Q8. What is the difference between search and sorting complexity?**  
Partial search scans n records in O(n). Ranking uses comparison sorting in O(n log n). Exact dictionary lookup is O(1) average.

**Q9. Is this a real defence system?**  
No. It is a fictional classroom simulation. It does not connect to sensors, aircraft, weapons, or operational defence systems.

## Limitations

- Radar coordinates are synthetic display coordinates, not geographic coordinates.
- Status changes are simulated labels only; no physical interception is modeled.
- Tkinter GUI interaction should be manually checked on the target macOS machine because a headless build environment may not provide a display server.
