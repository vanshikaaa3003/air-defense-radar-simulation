
import csv
import math
import random
import heapq
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "aircraft_records.csv"
FIELDS = ["target_id", "x_position", "y_position", "speed", "altitude", "distance", "timestamp", "priority_score", "priority_level"]

def calculate_priority(distance, speed, altitude):
    score = 100 - distance * 0.45 + speed * 0.22 + altitude * 0.0008
    return round(max(0, min(100, score)), 2)

def priority_level(score):
    if score >= 75:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    return "LOW"

def generate_dataset(count=1000):
    random.seed(42)
    rows = []
    start = datetime.now() - timedelta(days=7)
    for i in range(1, count + 1):
        x = round(random.uniform(-100, 100), 2)
        y = round(random.uniform(-100, 100), 2)
        distance = round(math.sqrt(x * x + y * y), 2)
        speed = round(random.uniform(150, 1200), 2)
        altitude = random.randint(500, 15000)
        score = calculate_priority(distance, speed, altitude)
        rows.append({
            "target_id": f"T{i:04d}",
            "x_position": x,
            "y_position": y,
            "speed": speed,
            "altitude": altitude,
            "distance": distance,
            "timestamp": (start + timedelta(seconds=i * 37)).strftime("%Y-%m-%d %H:%M:%S"),
            "priority_score": score,
            "priority_level": priority_level(score)
        })
    with DATA_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows

def load_dataset():
    if not DATA_FILE.exists():
        return generate_dataset()
    with DATA_FILE.open("r", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if len(rows) < 1000 or any(field not in (rows[0] if rows else {}) for field in FIELDS):
        return generate_dataset()
    for row in rows:
        for field in ["x_position", "y_position", "speed", "altitude", "distance", "priority_score"]:
            row[field] = float(row[field])
        row["altitude"] = int(row["altitude"])
    return rows

def build_priority_queue(rows):
    heap = []
    for row in rows:
        heapq.heappush(heap, (-float(row["priority_score"]), row["target_id"], row))
    return heap

class RadarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Air Defense Radar Simulation")
        self.root.geometry("1200x760")
        self.root.minsize(950, 650)
        self.rows = load_dataset()
        self.heap = build_priority_queue(self.rows)
        self.running = True
        self.angle = 0
        self.selected_id = None
        self.root.configure(bg="#071522")
        self.build_ui()
        self.populate_table()
        self.update_dashboard()
        self.animate()

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#102638", foreground="#e4f4f5", fieldbackground="#102638", rowheight=25)
        style.configure("Treeview.Heading", background="#173d50", foreground="white", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#087f8c")])
        header = tk.Frame(self.root, bg="#071522")
        header.pack(fill="x", padx=16, pady=(12, 5))
        tk.Label(header, text="AIR DEFENSE RADAR SIMULATION", font=("Arial", 22, "bold"), fg="#65f5d0", bg="#071522").pack(anchor="w")
        tk.Label(header, text="Educational simulation • Synthetic targets • DSA priority analysis", font=("Arial", 10), fg="#a9c5d2", bg="#071522").pack(anchor="w", pady=(3, 0))
        stats = tk.Frame(self.root, bg="#071522")
        stats.pack(fill="x", padx=16, pady=8)
        self.stat_labels = {}
        for key, label in [("total", "TOTAL TARGETS"), ("high", "HIGH PRIORITY"), ("medium", "MEDIUM PRIORITY"), ("low", "LOW PRIORITY")]:
            card = tk.Frame(stats, bg="#102638", padx=14, pady=10)
            card.pack(side="left", fill="x", expand=True, padx=(0, 8))
            tk.Label(card, text=label, bg="#102638", fg="#a9c5d2", font=("Arial", 9, "bold")).pack(anchor="w")
            value = tk.Label(card, text="0", bg="#102638", fg="#65f5d0", font=("Arial", 19, "bold"))
            value.pack(anchor="w", pady=(4, 0))
            self.stat_labels[key] = value
        body = tk.Frame(self.root, bg="#071522")
        body.pack(fill="both", expand=True, padx=16, pady=6)
        left = tk.Frame(body, bg="#071522")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = tk.Frame(body, bg="#071522")
        right.pack(side="right", fill="both", expand=True)
        tk.Label(left, text="LIVE RADAR DISPLAY", bg="#071522", fg="#65f5d0", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 6))
        self.canvas = tk.Canvas(left, bg="#06111b", highlightthickness=1, highlightbackground="#1a5261", height=400)
        self.canvas.pack(fill="both", expand=True)
        controls = tk.Frame(left, bg="#071522")
        controls.pack(fill="x", pady=8)
        tk.Button(controls, text="Pause / Resume", command=self.toggle_radar, bg="#176477", fg="white", relief="flat", padx=12, pady=7).pack(side="left", padx=(0, 6))
        tk.Button(controls, text="Reset Radar", command=self.reset_radar, bg="#176477", fg="white", relief="flat", padx=12, pady=7).pack(side="left", padx=6)
        tk.Button(controls, text="Export Snapshot", command=self.export_snapshot, bg="#176477", fg="white", relief="flat", padx=12, pady=7).pack(side="left", padx=6)
        tk.Label(right, text="TARGET TRACKING TABLE", bg="#071522", fg="#65f5d0", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 6))
        searchbar = tk.Frame(right, bg="#071522")
        searchbar.pack(fill="x", pady=(0, 8))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(searchbar, textvariable=self.search_var, bg="#102638", fg="white", insertbackground="white", relief="flat")
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 6))
        self.search_entry.insert(0, "Search target ID, e.g. T0001")
        self.search_entry.bind("<FocusIn>", self.clear_placeholder)
        self.search_entry.bind("<Return>", lambda event: self.search_target())
        tk.Button(searchbar, text="Search", command=self.search_target, bg="#087f8c", fg="white", relief="flat", padx=12, pady=7).pack(side="left")
        tk.Button(searchbar, text="Show All", command=self.populate_table, bg="#176477", fg="white", relief="flat", padx=10, pady=7).pack(side="left", padx=(5, 0))
        columns = ("id", "distance", "speed", "altitude", "score", "level")
        self.tree = ttk.Treeview(right, columns=columns, show="headings", height=15)
        headings = [("id", "Target ID"), ("distance", "Distance"), ("speed", "Speed"), ("altitude", "Altitude"), ("score", "Score"), ("level", "Priority")]
        widths = [76, 72, 72, 78, 65, 78]
        for (column, title), width in zip(headings, widths):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("HIGH", foreground="#ff8d8d")
        self.tree.tag_configure("MEDIUM", foreground="#ffd479")
        self.tree.tag_configure("LOW", foreground="#80e8b1")
        self.tree.bind("<<TreeviewSelect>>", self.select_target)
        self.status = tk.Label(self.root, text="Ready", bg="#071522", fg="#a9c5d2", anchor="w")
        self.status.pack(fill="x", padx=18, pady=(0, 10))

    def clear_placeholder(self, event):
        if self.search_var.get() == "Search target ID, e.g. T0001":
            self.search_var.set("")

    def populate_table(self, rows=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        displayed = self.rows if rows is None else rows
        for row in displayed:
            self.tree.insert("", "end", iid=row["target_id"], values=(
                row["target_id"], f'{float(row["distance"]):.1f}', f'{float(row["speed"]):.1f}',
                row["altitude"], f'{float(row["priority_score"]):.1f}', row["priority_level"]
            ), tags=(row["priority_level"],))
        self.status.config(text=f"Displaying {len(displayed)} of {len(self.rows)} synthetic target records")

    def update_dashboard(self):
        counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for row in self.rows:
            counts[row["priority_level"]] += 1
        self.stat_labels["total"].config(text=str(len(self.rows)))
        self.stat_labels["high"].config(text=str(counts["HIGH"]))
        self.stat_labels["medium"].config(text=str(counts["MEDIUM"]))
        self.stat_labels["low"].config(text=str(counts["LOW"]))

    def search_target(self):
        query = self.search_var.get().strip().upper()
        if not query or query == "SEARCH TARGET ID, E.G. T0001":
            self.populate_table()
            return
        matches = [row for row in self.rows if query in row["target_id"].upper()]
        self.populate_table(matches)
        if matches:
            self.status.config(text=f"Found {len(matches)} matching target record(s)")
            if len(matches) == 1:
                self.selected_id = matches[0]["target_id"]
                self.draw_radar()
        else:
            self.status.config(text=f"No target found for '{query}'")
            messagebox.showinfo("Search Result", f"No target found for '{query}'")

    def select_target(self, event):
        selected = self.tree.selection()
        if selected:
            self.selected_id = selected[0]
            self.draw_radar()

    def toggle_radar(self):
        self.running = not self.running
        self.status.config(text="Radar sweep running" if self.running else "Radar sweep paused")

    def reset_radar(self):
        self.angle = 0
        self.selected_id = None
        self.running = True
        self.populate_table()
        self.draw_radar()
        self.status.config(text="Radar display reset")

    def export_snapshot(self):
        path = BASE_DIR / "radar_snapshot.csv"
        ordered = sorted(self.rows, key=lambda row: float(row["priority_score"]), reverse=True)
        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(ordered)
        self.status.config(text=f"Priority-ranked snapshot saved to {path.name}")
        messagebox.showinfo("Export Complete", f"Saved {len(ordered)} records to {path.name}")

    def draw_radar(self):
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 350)
        height = max(self.canvas.winfo_height(), 350)
        cx, cy = width / 2, height / 2
        radius = min(width, height) * 0.42
        for fraction in [0.25, 0.5, 0.75, 1]:
            r = radius * fraction
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#176477", width=1)
        self.canvas.create_line(cx-radius, cy, cx+radius, cy, fill="#176477")
        self.canvas.create_line(cx, cy-radius, cx, cy+radius, fill="#176477")
        self.canvas.create_text(cx+radius-15, cy-12, text="N", fill="#65f5d0", font=("Arial", 9, "bold"))
        self.canvas.create_text(cx+radius-15, cy+12, text="E", fill="#65f5d0", font=("Arial", 9, "bold"))
        if self.running:
            radians = math.radians(self.angle)
            self.canvas.create_line(cx, cy, cx + radius * math.cos(radians), cy - radius * math.sin(radians), fill="#65f5d0", width=2)
        for row in self.rows:
            x = cx + float(row["x_position"]) / 100 * radius
            y = cy - float(row["y_position"]) / 100 * radius
            if row["target_id"] == self.selected_id:
                color, size = "#ffffff", 6
            else:
                color = {"HIGH": "#ff6262", "MEDIUM": "#ffd166", "LOW": "#65f5d0"}[row["priority_level"]]
                size = 2
            self.canvas.create_oval(x-size, y-size, x+size, y+size, fill=color, outline="")
        self.canvas.create_oval(cx-4, cy-4, cx+4, cy+4, fill="#ffffff", outline="")
        self.canvas.create_text(10, 10, anchor="nw", text=f"SWEEP {self.angle}°  |  TARGETS {len(self.rows)}", fill="#a9c5d2", font=("Arial", 9))

    def animate(self):
        if self.running:
            self.angle = (self.angle + 3) % 360
        self.draw_radar()
        self.root.after(80, self.animate)

def main():
    root = tk.Tk()
    app = RadarApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
