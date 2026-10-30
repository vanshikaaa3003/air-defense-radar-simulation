import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv, math, heapq
from pathlib import Path
from radar_core import RadarModel, FIELDS, EVENT_FIELDS, build_priority_queue

ROOT = Path(__file__).resolve().parent
BG, PANEL, PANEL2 = "#071522", "#102638", "#163548"
CYAN, MUTED, WHITE = "#65f5d0", "#a9c5d2", "#eaf7fa"
COLORS = {"HIGH":"#ff6b75","MEDIUM":"#ffd166","LOW":"#65d6a5"}
STATUS_COLORS = {"DETECTED":"#8bd5ff","TRACKING":"#ffd166","INTERCEPTED":"#65d6a5","ESCAPED":"#b8a1ff"}

class RadarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Air Defense Radar Simulation | SGT University")
        self.root.geometry("1320x850"); self.root.minsize(1050,700)
        self.root.configure(bg=BG)
        self.model = RadarModel(ROOT/"aircraft_records.csv", ROOT/"event_history.csv")
        self.selected_id = None; self.angle = 0; self.running = True
        self._style(); self._build(); self.refresh_all(); self._animate()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def _style(self):
        s=ttk.Style(); s.theme_use("clam")
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=PANEL2, foreground=WHITE, padding=(18,10), font=("Arial",10,"bold"))
        s.map("TNotebook.Tab", background=[("selected","#087f8c")], foreground=[("selected","white")])
        s.configure("Treeview", background=PANEL, foreground=WHITE, fieldbackground=PANEL,
                    rowheight=27, borderwidth=0, font=("Arial",9))
        s.configure("Treeview.Heading", background=PANEL2, foreground=CYAN,
                    relief="flat", font=("Arial",9,"bold"))
        s.map("Treeview", background=[("selected","#087f8c")], foreground=[("selected","white")])

    def _button(self, parent, text, command, accent=False):
        return tk.Button(parent,text=text,command=command,bg="#087f8c" if accent else "#1b5266",
                         fg="white",activebackground="#0a9da7",activeforeground="white",
                         relief="flat",bd=0,padx=13,pady=8,font=("Arial",9,"bold"),cursor="hand2")

    def _card(self,parent,title,key):
        f=tk.Frame(parent,bg=PANEL,padx=14,pady=11,highlightthickness=1,highlightbackground="#1a4658")
        tk.Label(f,text=title,bg=PANEL,fg=MUTED,font=("Arial",8,"bold")).pack(anchor="w")
        v=tk.Label(f,text="0",bg=PANEL,fg=CYAN,font=("Arial",21,"bold")); v.pack(anchor="w",pady=(5,0))
        self.stat_labels[key]=v
        return f

    def _build(self):
        header=tk.Frame(self.root,bg=BG); header.pack(fill="x",padx=20,pady=(14,8))
        tk.Label(header,text="AIR DEFENSE RADAR",bg=BG,fg=CYAN,font=("Arial",22,"bold")).pack(side="left")
        tk.Label(header,text="  /  EDUCATIONAL SIMULATION  •  SYNTHETIC DATA  •  SGT UNIVERSITY",
                 bg=BG,fg=MUTED,font=("Arial",9)).pack(side="left",pady=(8,0))
        self.stat_labels={}
        cards=tk.Frame(self.root,bg=BG); cards.pack(fill="x",padx=20,pady=5)
        for title,key in [("TOTAL TARGETS","total"),("ACTIVE TARGETS","active"),("HIGH THREAT","high"),
                          ("MEDIUM THREAT","medium"),("LOW THREAT","low"),("INTERCEPTED","intercepted"),("ESCAPED","escaped")]:
            self._card(cards,title,key).pack(side="left",fill="x",expand=True,padx=(0,7))
        self.tabs=ttk.Notebook(self.root); self.tabs.pack(fill="both",expand=True,padx=20,pady=12)
        self.radar_tab=tk.Frame(self.tabs,bg=BG); self.targets_tab=tk.Frame(self.tabs,bg=BG)
        self.intercept_tab=tk.Frame(self.tabs,bg=BG); self.analytics_tab=tk.Frame(self.tabs,bg=BG)
        for frame,title in [(self.radar_tab,"LIVE RADAR"),(self.targets_tab,"TARGET MANAGEMENT"),
                            (self.intercept_tab,"INTERCEPTION SIMULATION"),(self.analytics_tab,"ANALYTICS & EVENTS")]:
            self.tabs.add(frame,text=title)
        self._build_radar(); self._build_targets(); self._build_interception(); self._build_analytics()
        self.footer=tk.Label(self.root,text="SYSTEM READY  •  Fictional data only — no real-world tracking or control",
                             bg="#06111b",fg=MUTED,anchor="w",padx=20,pady=8,font=("Arial",9))
        self.footer.pack(fill="x",side="bottom")

    def _build_radar(self):
        left=tk.Frame(self.radar_tab,bg=BG); left.pack(side="left",fill="both",expand=True,padx=(0,12),pady=12)
        right=tk.Frame(self.radar_tab,bg=PANEL,padx=15,pady=15); right.pack(side="right",fill="y",pady=12)
        tk.Label(left,text="SCAN FIELD  /  360°",bg=BG,fg=CYAN,font=("Arial",11,"bold")).pack(anchor="w",pady=(0,8))
        self.canvas=tk.Canvas(left,bg="#04101a",highlightthickness=1,highlightbackground="#1a5261")
        self.canvas.pack(fill="both",expand=True)
        controls=tk.Frame(left,bg=BG); controls.pack(fill="x",pady=8)
        self._button(controls,"PAUSE / RESUME",self.toggle_radar).pack(side="left",padx=(0,6))
        self._button(controls,"RESET VIEW",self.reset_view).pack(side="left")
        tk.Label(right,text="SELECTED TARGET",bg=PANEL,fg=CYAN,font=("Arial",11,"bold")).pack(anchor="w")
        self.radar_detail=tk.Label(right,text="Select a target in the table to inspect it.",
            bg=PANEL,fg=WHITE,justify="left",wraplength=230,font=("Arial",10))
        self.radar_detail.pack(anchor="w",pady=12)
        tk.Label(right,text="PRIORITY QUEUE  /  NEXT ACTIVE",bg=PANEL,fg=CYAN,font=("Arial",10,"bold")).pack(anchor="w",pady=(18,4))
        self.queue_detail=tk.Label(right,text="Queue is empty.",bg=PANEL,fg=WHITE,justify="left",wraplength=230,font=("Arial",10))
        self.queue_detail.pack(anchor="w",pady=5)

    def _build_targets(self):
        bar=tk.Frame(self.targets_tab,bg=BG); bar.pack(fill="x",pady=12)
        tk.Label(bar,text="Target ID",bg=BG,fg=MUTED).pack(side="left")
        self.search_var=tk.StringVar(); e=tk.Entry(bar,textvariable=self.search_var,bg=PANEL,fg=WHITE,
            insertbackground=WHITE,relief="flat",width=20); e.pack(side="left",ipady=7,padx=8)
        e.bind("<Return>",lambda _:self.apply_filters())
        self.threat_filter=tk.StringVar(value="ALL"); self.status_filter=tk.StringVar(value="ALL")
        for label,var,values in [("Threat",self.threat_filter,["ALL","HIGH","MEDIUM","LOW"]),
                                 ("Status",self.status_filter,["ALL","DETECTED","TRACKING","INTERCEPTED","ESCAPED"])]:
            tk.Label(bar,text=label,bg=BG,fg=MUTED).pack(side="left",padx=(8,3))
            ttk.Combobox(bar,textvariable=var,values=values,state="readonly",width=13).pack(side="left")
        self._button(bar,"APPLY FILTERS",self.apply_filters,True).pack(side="left",padx=8)
        self._button(bar,"CLEAR",self.clear_filters).pack(side="left")
        cols=("id","distance","speed","altitude","score","threat","status")
        self.tree=ttk.Treeview(self.targets_tab,columns=cols,show="headings")
        for col,title,width in zip(cols,["TARGET ID","DISTANCE","SPEED","ALTITUDE","SCORE","THREAT","STATUS"],[110,110,110,110,100,110,130]):
            self.tree.heading(col,text=title); self.tree.column(col,width=width,anchor="center")
        self.tree.pack(fill="both",expand=True,pady=(0,10))
        for k,c in COLORS.items(): self.tree.tag_configure(k,foreground=c)
        self.tree.bind("<<TreeviewSelect>>",self.on_select)
        self._button(self.targets_tab,"EXPORT TARGET CSV",self.export_targets).pack(anchor="e",pady=5)

    def _build_interception(self):
        panel=tk.Frame(self.intercept_tab,bg=PANEL,padx=22,pady=20); panel.pack(fill="x",pady=16)
        tk.Label(panel,text="SIMULATED TARGET LIFECYCLE",bg=PANEL,fg=CYAN,font=("Arial",13,"bold")).pack(anchor="w")
        tk.Label(panel,text="DETECTED   →   TRACKING   →   INTERCEPTED     |     DETECTED / TRACKING   →   ESCAPED",
                 bg=PANEL,fg=WHITE,font=("Arial",10)).pack(anchor="w",pady=12)
        row=tk.Frame(panel,bg=PANEL); row.pack(fill="x")
        tk.Label(row,text="Selected target:",bg=PANEL,fg=MUTED).pack(side="left")
        self.action_target=tk.Label(row,text="None",bg=PANEL,fg=CYAN,font=("Arial",11,"bold")); self.action_target.pack(side="left",padx=8)
        self.action_status=tk.Label(panel,text="Choose a target from Target Management or the radar table.",
                                    bg=PANEL,fg=MUTED,font=("Arial",10)); self.action_status.pack(anchor="w",pady=10)
        buttons=tk.Frame(panel,bg=PANEL); buttons.pack(anchor="w",pady=8)
        self._button(buttons,"START TRACKING",lambda:self.perform("track"),True).pack(side="left",padx=(0,8))
        self._button(buttons,"SIMULATE INTERCEPTION",lambda:self.perform("intercept")).pack(side="left",padx=8)
        self._button(buttons,"MARK ESCAPED",lambda:self.perform("escape")).pack(side="left",padx=8)
        self._button(buttons,"RESET COMPLETED TARGET",lambda:self.perform("reset_target")).pack(side="left",padx=8)
        note=tk.Label(self.intercept_tab,text="This is a status-only classroom simulation. No weapons, guidance, trajectories, or real systems are modeled.",
                      bg=BG,fg=MUTED,font=("Arial",9)); note.pack(anchor="w",pady=10)

    def _build_analytics(self):
        top=tk.Frame(self.analytics_tab,bg=BG); top.pack(fill="x",pady=12)
        self.threat_summary=tk.Label(top,text="",bg=BG,fg=WHITE,justify="left",font=("Arial",11))
        self.threat_summary.pack(side="left",anchor="nw",padx=12)
        self.lifecycle_summary=tk.Label(top,text="",bg=BG,fg=WHITE,justify="left",font=("Arial",11))
        self.lifecycle_summary.pack(side="left",anchor="nw",padx=30)
        tk.Label(self.analytics_tab,text="RECENT EVENT HISTORY",bg=BG,fg=CYAN,font=("Arial",11,"bold")).pack(anchor="w",pady=(10,5))
        cols=("time","id","event","details")
        self.events_tree=ttk.Treeview(self.analytics_tab,columns=cols,show="headings",height=15)
        for c,t,w in zip(cols,["TIMESTAMP","TARGET ID","EVENT","DETAILS"],[220,110,130,700]):
            self.events_tree.heading(c,text=t); self.events_tree.column(c,width=w,anchor="w")
        self.events_tree.pack(fill="both",expand=True)
        self._button(self.analytics_tab,"EXPORT EVENT HISTORY CSV",self.export_events).pack(anchor="e",pady=8)

    def refresh_all(self):
        self.refresh_dashboard(); self.refresh_table(); self.refresh_analytics(); self.draw_radar()
        if self.selected_id:
            target=self.model.find(self.selected_id)
            if target: self._show_selected(target)

    def refresh_dashboard(self):
        s=self.model.stats()
        for key,val in [("total",s["total"]),("active",s["active"]),("high",s["threat"]["HIGH"]),
                        ("medium",s["threat"]["MEDIUM"]),("low",s["threat"]["LOW"]),
                        ("intercepted",s["intercepted"]),("escaped",s["escaped"])]:
            self.stat_labels[key].config(text=str(val))
                                                                                             
        queue=self.model.priority_queue()
        next_target=heapq.heappop(queue)[2] if queue else None
        if hasattr(self,"queue_detail"):
            self.queue_detail.config(text=(f'{next_target["target_id"]}  |  {next_target["priority_level"]}  |  '
                f'Score {next_target["priority_score"]:.2f}\nStatus: {next_target["status"]}'
                if next_target else "No active targets in queue."))

    def refresh_table(self, rows=None):
        self.tree.delete(*self.tree.get_children())
        for r in (self.model.ranked() if rows is None else rows):
            self.tree.insert("","end",iid=r["target_id"],values=(r["target_id"],f'{r["distance"]:.2f}',
                f'{r["speed"]:.1f}',r["altitude"],f'{r["priority_score"]:.2f}',r["priority_level"],r["status"]),
                tags=(r["priority_level"],))
        if self.selected_id and self.tree.exists(self.selected_id):
            self.tree.selection_set(self.selected_id)

    def refresh_analytics(self):
        s=self.model.stats()
        self.threat_summary.config(text="THREAT DISTRIBUTION\n"+ "\n".join(f"{k}: {v}" for k,v in s["threat"].items()))
        self.lifecycle_summary.config(text="LIFECYCLE COUNTS\n"+ "\n".join(f"{k}: {v}" for k,v in s["status"].items()))
        self.events_tree.delete(*self.events_tree.get_children())
        for ev in reversed(self.model.events[-250:]):
            self.events_tree.insert("","end",values=(ev["timestamp"],ev["target_id"],ev["event_type"],ev["details"]))

    def _show_selected(self,r):
        details=(f'ID: {r["target_id"]}\nThreat: {r["priority_level"]} ({r["priority_score"]:.2f})\n'
                 f'Status: {r["status"]}\nDistance: {r["distance"]:.2f}\nSpeed: {r["speed"]:.1f}\n'
                 f'Altitude: {r["altitude"]}\nCoordinates: ({r["x_position"]:.2f}, {r["y_position"]:.2f})\n'
                 f'Detected: {r["timestamp"]}')
        self.radar_detail.config(text=details); self.action_target.config(text=r["target_id"])
        self.action_status.config(text=f'Current lifecycle status: {r["status"]}')

    def on_select(self,event=None):
        selection=self.tree.selection()
        if selection:
            self.selected_id=selection[0]
            target=self.model.find(self.selected_id)
            if target: self._show_selected(target); self.draw_radar()

    def apply_filters(self):
        q=self.search_var.get().strip().upper()
        rows=[r for r in self.model.rows if (not q or q in r["target_id"]) and
              (self.threat_filter.get()=="ALL" or r["priority_level"]==self.threat_filter.get()) and
              (self.status_filter.get()=="ALL" or r["status"]==self.status_filter.get())]
        self.refresh_table(rows)
        self.footer.config(text=f"FILTER RESULT  •  {len(rows)} matching target(s)")

    def clear_filters(self):
        self.search_var.set(""); self.threat_filter.set("ALL"); self.status_filter.set("ALL")
        self.refresh_table(); self.footer.config(text="Filters cleared.")

    def perform(self,action):
        if not self.selected_id:
            messagebox.showwarning("Target required","Select a target in Target Management first."); return
        try:
            result=getattr(self.model,action)(self.selected_id)
            self.action_status.config(text=f'Success: {result["target_id"]} is now {result["status"]}.')
            self.footer.config(text=f'{result["target_id"]} lifecycle updated to {result["status"]}.')
            self.refresh_all()
        except ValueError as exc:
            self.action_status.config(text=f"Action unavailable: {exc}")
            messagebox.showwarning("Action not allowed",str(exc))

    def draw_radar(self):
        if not hasattr(self,"canvas"): return
        self.canvas.delete("all")
        w=max(self.canvas.winfo_width(),420); h=max(self.canvas.winfo_height(),420)
        cx,cy=w/2,h/2; radius=min(w,h)*.43
        for frac in (.25,.5,.75,1):
            rr=radius*frac
            self.canvas.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,outline="#176477",width=1)
        self.canvas.create_line(cx-radius,cy,cx+radius,cy,fill="#174555")
        self.canvas.create_line(cx,cy-radius,cx,cy+radius,fill="#174555")
        if self.running:
            a=math.radians(self.angle)
            self.canvas.create_line(cx,cy,cx+radius*math.cos(a),cy-radius*math.sin(a),fill=CYAN,width=2)
        for r in self.model.rows:
            if r["status"] in {"INTERCEPTED","ESCAPED"}: continue
            x=cx+(r["x_position"]/150)*radius; y=cy-(r["y_position"]/150)*radius
            color=COLORS[r["priority_level"]]; size=6 if r["target_id"]==self.selected_id else 3
            self.canvas.create_oval(x-size,y-size,x+size,y+size,fill=color,outline=WHITE if size==6 else "")
        self.canvas.create_oval(cx-4,cy-4,cx+4,cy+4,fill=WHITE,outline="")
        self.canvas.create_text(12,12,anchor="nw",text=f"SWEEP {self.angle:03d}°  |  ACTIVE {self.model.stats()['active']}",
                                fill=MUTED,font=("Arial",9))

    def toggle_radar(self):
        self.running=not self.running
        self.footer.config(text="Radar sweep running." if self.running else "Radar sweep paused.")

    def reset_view(self):
        self.angle=0; self.selected_id=None; self.running=True
        self.radar_detail.config(text="Select a target in the table to inspect it.")
        self.action_target.config(text="None"); self.action_status.config(text="No target selected.")
        self.refresh_table(); self.draw_radar()

    def _animate(self):
        if self.running: self.angle=(self.angle+2)%360
        self.draw_radar()
        self.root.after(90,self._animate)

    def export_targets(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",initialfile="target_export.csv",
            filetypes=[("CSV files","*.csv")])
        if not path: return
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(self.model.ranked())
        messagebox.showinfo("Export complete",f"Exported {len(self.model.rows)} targets.")

    def export_events(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",initialfile="event_history_export.csv",
            filetypes=[("CSV files","*.csv")])
        if not path: return
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=EVENT_FIELDS); w.writeheader(); w.writerows(self.model.events)
        messagebox.showinfo("Export complete",f"Exported {len(self.model.events)} events.")

def main():
    root=tk.Tk(); RadarApp(root); root.mainloop()

if __name__=="__main__": main()
