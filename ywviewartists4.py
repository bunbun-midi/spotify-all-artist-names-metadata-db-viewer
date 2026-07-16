import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB_PATH = "ywartists.db"
TABLE = "yunique_artists"
COLUMN = "artist"
PAGE_SIZE = 50

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("SQLite Browser")
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

        self.search_var = tk.StringVar()
        self.page_jump_var = tk.StringVar()
        self.page = 0
        self.sort_mode = "default"

        self.setup_style()
        self.build_ui()
        self.refresh()

    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        bg = "#1e1e1e"
        fg = "#e6e6e6"
        accent = "#2d2d2d"
        self.root.configure(bg=bg)

        style.configure(".", background=bg, foreground=fg, fieldbackground=accent)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", background=accent, foreground=fg, padding=6)
        style.map("TButton",
                  background=[("active", "#3a3a3a")],
                  foreground=[("active", "#ffffff")])

        style.configure("Treeview",
                        background="#252526",
                        fieldbackground="#252526",
                        foreground=fg,
                        rowheight=24)
        style.configure("Treeview.Heading",
                        background="#333333",
                        foreground=fg)

    def build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Search:").pack(side="left")
        ttk.Entry(top, textvariable=self.search_var, width=35).pack(side="left", padx=6)
        ttk.Button(top, text="Search", command=self.do_search).pack(side="left")
        ttk.Button(top, text="Clear", command=self.clear_search).pack(side="left", padx=4)

        nav = ttk.Frame(self.root, padding=8)
        nav.pack(fill="x")

        self.prev_btn = ttk.Button(nav, text="Prev", command=self.prev_page)
        self.prev_btn.pack(side="left")
        self.next_btn = ttk.Button(nav, text="Next", command=self.next_page)
        self.next_btn.pack(side="left", padx=4)

        ttk.Label(nav, text="Jump to page:").pack(side="left", padx=(20, 4))
        ttk.Entry(nav, textvariable=self.page_jump_var, width=8).pack(side="left")
        ttk.Button(nav, text="Go", command=self.jump_to_page).pack(side="left", padx=4)

        ttk.Button(nav, text="Toggle Sort", command=self.toggle_sort).pack(side="left", padx=(20, 0))

        self.status = ttk.Label(self.root, text="")
        self.status.pack(fill="x", padx=8)

        table_frame = ttk.Frame(self.root, padding=8)
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=(COLUMN,), show="headings", height=20)
        self.tree.heading(COLUMN, text=COLUMN)
        self.tree.column(COLUMN, width=800, anchor="w")

        self.scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.tree.bind("<MouseWheel>", self.on_mousewheel)
        self.tree.bind("<Button-4>", self.on_mousewheel_linux)
        self.tree.bind("<Button-5>", self.on_mousewheel_linux)

    def on_mousewheel(self, event):
        self.tree.yview_scroll(-1 * int(event.delta / 120), "units")
        return "break"

    def on_mousewheel_linux(self, event):
        self.tree.yview_scroll(-1 if event.num == 4 else 1, "units")
        return "break"

    def get_query_parts(self):
        term = self.search_var.get().strip()
        where_sql = f"WHERE {COLUMN} LIKE ?" if term else ""
        params = (f"%{term}%",) if term else ()
        if self.sort_mode == "alpha":
            order_sql = f"ORDER BY {COLUMN} COLLATE NOCASE, rowid"
        else:
            order_sql = "ORDER BY rowid"
        return term, where_sql, params, order_sql

    def query_total(self):
        term, where_sql, params, _ = self.get_query_parts()
        cur = self.conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {TABLE} {where_sql}", params)
        return cur.fetchone()[0], term

    def refresh(self):
        total, term = self.query_total()
        _, where_sql, params, order_sql = self.get_query_parts()

        offset = self.page * PAGE_SIZE
        cur = self.conn.cursor()
        cur.execute(
            f"SELECT {COLUMN} FROM {TABLE} {where_sql} {order_sql} LIMIT ? OFFSET ?",
            params + (PAGE_SIZE, offset)
        )
        rows = cur.fetchall()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            self.tree.insert("", "end", values=(row[COLUMN],))

        start = offset + 1 if total else 0
        end = min(offset + PAGE_SIZE, total)
        sort_label = "alphabetized" if self.sort_mode == "alpha" else "default"
        self.status.config(
            text=f"{start}-{end} of {total} | sort: {sort_label}" +
                 (f" | search: {term}" if term else "")
        )

        self.prev_btn.config(state="normal" if self.page > 0 else "disabled")
        self.next_btn.config(state="normal" if end < total else "disabled")

    def do_search(self):
        self.page = 0
        self.refresh()

    def clear_search(self):
        self.search_var.set("")
        self.page = 0
        self.refresh()

    def next_page(self):
        self.page += 1
        self.refresh()

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.refresh()

    def jump_to_page(self):
        try:
            p = int(self.page_jump_var.get().strip())
            if p < 1:
                raise ValueError
            self.page = p - 1
            self.refresh()
        except ValueError:
            messagebox.showerror("Invalid page", "Enter a positive whole number.")

    def toggle_sort(self):
        self.sort_mode = "alpha" if self.sort_mode == "default" else "default"
        self.page = 0
        self.refresh()

    def on_close(self):
        self.conn.close()
        self.root.destroy()

root = tk.Tk()
app = App(root)
root.protocol("WM_DELETE_WINDOW", app.on_close)
root.mainloop()
