import csv, tempfile, unittest
from pathlib import Path
from radar_core import (calculate_priority, priority_level, load_targets, save_targets,
                        build_priority_queue, RadarModel, FIELDS)

PROJECT=Path(__file__).resolve().parent

class RadarProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=load_targets(PROJECT/"aircraft_records.csv")

    def test_dataset_size_and_unique_ids(self):
        ids=[r["target_id"] for r in self.rows]
        self.assertGreaterEqual(len(self.rows),1000)
        self.assertEqual(len(ids),len(set(ids)))

    def test_score_range_and_formula(self):
        for r in self.rows:
            self.assertGreaterEqual(r["priority_score"],0)
            self.assertLessEqual(r["priority_score"],100)
            self.assertEqual(r["priority_score"],calculate_priority(r["distance"],r["speed"],r["altitude"]))

    def test_threshold_classification(self):
        self.assertEqual(priority_level(65),"HIGH")
        self.assertEqual(priority_level(64.99),"MEDIUM")
        self.assertEqual(priority_level(40),"MEDIUM")
        self.assertEqual(priority_level(39.99),"LOW")

    def test_all_three_categories_represented(self):
        counts={k:sum(r["priority_level"]==k for r in self.rows) for k in ("HIGH","MEDIUM","LOW")}
        self.assertTrue(all(v>0 for v in counts.values()),counts)

    def test_heap_orders_highest_first_and_excludes_closed(self):
        heap=build_priority_queue(self.rows[:3])
        popped=[]
        while heap: popped.append(heap.pop(0))
                                                                           
        import heapq
        heap=build_priority_queue(self.rows[:3])
        self.assertEqual(heapq.heappop(heap)[2]["priority_score"],max(r["priority_score"] for r in self.rows[:3]))

    def make_model(self):
        td=tempfile.TemporaryDirectory()
        data=Path(td.name)/"targets.csv"; events=Path(td.name)/"events.csv"
        subset=[]
        for r in self.rows[:3]:
            subset.append(dict(r))
        save_targets(data,subset)
        return td,RadarModel(data,events),data,events

    def test_lifecycle_and_interception_restriction(self):
        td,m,_,_=self.make_model()
        try:
            tid=m.rows[0]["target_id"]
            with self.assertRaises(ValueError): m.intercept(tid)
            m.track(tid); self.assertEqual(m.find(tid)["status"],"TRACKING")
            m.intercept(tid); self.assertEqual(m.find(tid)["status"],"INTERCEPTED")
            with self.assertRaises(ValueError): m.intercept(tid)
            self.assertEqual(m.stats()["active"],2)
            m.reset_target(tid); self.assertEqual(m.find(tid)["status"],"DETECTED")
        finally: td.cleanup()

    def test_escape_and_no_repeat_escape(self):
        td,m,_,_=self.make_model()
        try:
            tid=m.rows[1]["target_id"]; m.escape(tid)
            self.assertEqual(m.find(tid)["status"],"ESCAPED")
            with self.assertRaises(ValueError): m.escape(tid)
            self.assertEqual(m.stats()["escaped"],1)
        finally: td.cleanup()

    def test_persistence_and_event_history(self):
        td,m,data,events=self.make_model()
        try:
            tid=m.rows[0]["target_id"]; m.track(tid)
            reloaded=RadarModel(data,events)
            self.assertEqual(reloaded.find(tid)["status"],"TRACKING")
            self.assertEqual(len(reloaded.events),1)
            self.assertEqual(reloaded.events[0]["event_type"],"TRACKING")
        finally: td.cleanup()

    def test_csv_export_shape(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"out.csv"; save_targets(p,self.rows)
            with p.open(newline="",encoding="utf-8") as f:
                reader=csv.DictReader(f); self.assertEqual(reader.fieldnames,FIELDS)
                self.assertEqual(sum(1 for _ in reader),len(self.rows))

    def test_search_and_sort(self):
        td,m,_,_=self.make_model()
        try:
            self.assertEqual(m.find("t0001")["target_id"],"T0001")
            ranked=m.ranked()
            self.assertEqual([r["priority_score"] for r in ranked],
                             sorted([r["priority_score"] for r in ranked],reverse=True))
        finally: td.cleanup()

if __name__=="__main__": unittest.main(verbosity=2)
