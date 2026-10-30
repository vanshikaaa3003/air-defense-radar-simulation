from __future__ import annotations
import csv
import heapq
from datetime import datetime
from pathlib import Path

FIELDS = ["target_id","x_position","y_position","distance","speed","altitude",
          "timestamp","priority_score","priority_level","status"]
EVENT_FIELDS = ["timestamp","target_id","event_type","details"]
VALID_STATUSES = {"DETECTED", "TRACKING", "INTERCEPTED", "ESCAPED"}

def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))

def calculate_priority(distance, speed, altitude):
    proximity = 1.0 - _clamp(float(distance) / 150.0)
    speed_factor = _clamp((float(speed) - 150.0) / 1050.0)
    altitude_factor = 1.0 - _clamp(float(altitude) / 15000.0)
    return round(100.0 * (0.50*proximity + 0.30*speed_factor + 0.20*altitude_factor), 2)

def priority_level(score):
    score = float(score)
    if score >= 65: return "HIGH"
    if score >= 40: return "MEDIUM"
    return "LOW"

def load_targets(path):
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as f:
        result = list(csv.DictReader(f))
    for row in result:
        for key in ("x_position","y_position","distance","speed","priority_score"):
            row[key] = float(row[key])
        row["altitude"] = int(float(row["altitude"]))
        if row.get("status") not in VALID_STATUSES:
            row["status"] = "DETECTED"
    return result

def save_targets(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

def build_priority_queue(rows):
    heap = []
    for row in rows:
        if row["status"] not in {"INTERCEPTED", "ESCAPED"}:
            heapq.heappush(heap, (-float(row["priority_score"]), row["target_id"], row))
    return heap

def pop_highest_priority(heap):
    return heapq.heappop(heap)[2] if heap else None

class RadarModel:
    def __init__(self, data_path, event_path):
        self.data_path, self.event_path = Path(data_path), Path(event_path)
        self.rows = load_targets(self.data_path)
        self.by_id = {r["target_id"]: r for r in self.rows}
        self.events = []
        if self.event_path.exists():
            with self.event_path.open(newline="", encoding="utf-8") as f:
                self.events = list(csv.DictReader(f))

    def find(self, target_id):
        return self.by_id.get(str(target_id).strip().upper())

    def search(self, query):
        q = str(query).strip().upper()
        return [r for r in self.rows if q in r["target_id"].upper()] if q else list(self.rows)

    def ranked(self, active_only=False):
        rows = [r for r in self.rows if not active_only or r["status"] not in {"INTERCEPTED","ESCAPED"}]
        return sorted(rows, key=lambda r: (-r["priority_score"], r["target_id"]))

    def priority_queue(self):
        return build_priority_queue(self.rows)

    def _event(self, target, event_type, details):
        event = {"timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
                 "target_id": target["target_id"], "event_type": event_type, "details": details}
        self.events.append(event)
        with self.event_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EVENT_FIELDS)
            writer.writeheader(); writer.writerows(self.events)

    def _set_status(self, target, status, details):
        target["status"] = status
        save_targets(self.data_path, self.rows)
        self._event(target, status, details)
        return target

    def track(self, target_id):
        target = self.find(target_id)
        if target is None: raise ValueError("Select a valid target first.")
        if target["status"] != "DETECTED":
            raise ValueError("Tracking can only start for a DETECTED target.")
        return self._set_status(target, "TRACKING", "Target moved from DETECTED to TRACKING.")

    def intercept(self, target_id):
        target = self.find(target_id)
        if target is None: raise ValueError("Select a valid target first.")
        if target["status"] != "TRACKING":
            raise ValueError("Interception requires the target to be TRACKING first.")
        return self._set_status(target, "INTERCEPTED", "Fictional simulation: target marked INTERCEPTED.")

    def escape(self, target_id):
        target = self.find(target_id)
        if target is None: raise ValueError("Select a valid target first.")
        if target["status"] not in {"DETECTED","TRACKING"}:
            raise ValueError("Only DETECTED or TRACKING targets can escape.")
        return self._set_status(target, "ESCAPED", "Target marked ESCAPED in the simulation.")

    def reset_target(self, target_id):
        target = self.find(target_id)
        if target is None: raise ValueError("Select a valid target first.")
        if target["status"] not in {"INTERCEPTED","ESCAPED"}:
            raise ValueError("Only completed targets can be reset.")
        return self._set_status(target, "DETECTED", "Target lifecycle reset to DETECTED.")

    def stats(self):
        threat = {k: sum(r["priority_level"] == k for r in self.rows) for k in ("HIGH","MEDIUM","LOW")}
        status = {k: sum(r["status"] == k for r in self.rows) for k in ("DETECTED","TRACKING","INTERCEPTED","ESCAPED")}
        return {"total":len(self.rows), "active":sum(r["status"] not in {"INTERCEPTED","ESCAPED"} for r in self.rows),
                "intercepted":status["INTERCEPTED"], "escaped":status["ESCAPED"],
                "threat":threat, "status":status}
