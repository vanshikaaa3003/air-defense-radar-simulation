
import csv
import unittest
from pathlib import Path
from main import calculate_priority, priority_level, build_priority_queue, load_dataset

class RadarTests(unittest.TestCase):
    def test_dataset_has_at_least_1000_records(self):
        rows = load_dataset()
        self.assertGreaterEqual(len(rows), 1000)

    def test_target_ids_are_unique(self):
        rows = load_dataset()
        ids = [row["target_id"] for row in rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_priority_score_is_bounded(self):
        for distance, speed, altitude in [(0, 150, 500), (50, 600, 7000), (150, 1200, 15000)]:
            score = calculate_priority(distance, speed, altitude)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)

    def test_priority_levels(self):
        self.assertEqual(priority_level(80), "HIGH")
        self.assertEqual(priority_level(60), "MEDIUM")
        self.assertEqual(priority_level(20), "LOW")

    def test_priority_queue_orders_highest_first(self):
        rows = [
            {"target_id": "T1", "priority_score": 20},
            {"target_id": "T2", "priority_score": 90},
            {"target_id": "T3", "priority_score": 50}
        ]
        heap = build_priority_queue(rows)
        self.assertEqual(heap[0][2]["target_id"], "T2")

    def test_csv_has_expected_columns(self):
        path = Path(__file__).resolve().parent / "aircraft_records.csv"
        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            self.assertEqual(reader.fieldnames, ["target_id", "x_position", "y_position", "speed", "altitude", "distance", "timestamp", "priority_score", "priority_level"])

if __name__ == "__main__":
    unittest.main()
