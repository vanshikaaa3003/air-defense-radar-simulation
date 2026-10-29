
# Air Defense Radar Simulation

## Project Team

- Vanshika — 251302176
- Vinit — 251302086

## Overview

Air Defense Radar Simulation is a Python-based educational application that visualizes fictional radar targets, calculates priority scores, searches target records, and displays target information through a graphical interface.

## Technologies Used

- Python 3
- Tkinter for the graphical interface
- CSV for dataset storage
- Heap-based priority queue using heapq
- Python unittest for automated testing

## Features

- Radar sweep animation
- Visualization of 1,000 synthetic target records
- Color-coded HIGH, MEDIUM, and LOW priority levels
- Target ID search
- Priority score calculation
- Target tracking table
- Pause and resume controls
- Radar reset
- Export of priority-ranked CSV snapshot
- Automated tests

## Data Structures and Algorithms

- List: stores target records
- Linear Search: searches target IDs
- Heap: organizes targets by priority score
- Sorting: ranks targets for CSV export

## Dataset

The application generates a synthetic dataset containing 1,000 fictional target records. Each record includes target ID, coordinates, speed, altitude, distance, timestamp, priority score, and priority level.

The dataset is generated locally and is not sourced from real radar systems.

## How to Run

1. Install Python 3.
2. Open the project folder in VS Code.
3. Run `python3 main.py` in the terminal.
4. To execute automated tests, run `python3 -m unittest tests.py -v`.

## Team

Vanshika (251302176)  
Vinit (251302086)

## Project Scope

This is an educational simulation developed to demonstrate graphical visualization, data handling, searching, sorting, and priority queue concepts. It is not a real-world defense or tracking system.
