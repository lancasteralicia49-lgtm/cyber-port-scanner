import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import csv
from datetime import datetime
import time

results = []
lock = threading.Lock()
stop_flag = False
ports_scanned = 0
start_time = 0

# ------------------ SCAN ------------------
def scan_port(target, port, tree, total_ports):
    global ports_scanned

    if stop_flag:
        return

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)

        result = s.connect_ex((target, port))

        if result == 0:
            try:
                service = socket.getservbyport(port).strip()
            except:
                service = "unknown"

            try:
                banner = s.recv(1024).decode().strip()
            except:
                banner = "No banner"

            with lock:
                results.append((port, "OPEN", service, banner))
                tree.insert("", "end",
                            values=(port, "OPEN", service, banner),
                            tags=("open",))

        s.close()
    except:
        pass

    # Progress
    with lock:
        ports_scanned += 1
        percent = int((ports_scanned / total_ports) * 100)

        elapsed = time.time() - start_time
        speed = int(ports_scanned / elapsed) if elapsed > 0 else 0

        progress_bar["value"] = percent
        status_label.config(
            text=f"Scanning... {percent}% | {ports_scanned}/{total_ports} ports | {speed} ports/sec"
        )


# ------------------ START ------------------
def start_scan():
    global stop_flag, ports_scanned, start_time

    stop_flag = False
    ports_scanned = 0
    start_time = time.time()

    tree.delete(*tree.get_children())
    results.clear()

    try:
        target = ip_entry.get()
        start_port = int(start_port_entry.get())
        end_port = int(end_port_entry.get())
        thread_count = int(thread_entry.get())
    except:
        messagebox.showerror("Error", "Invalid input")
        return

    total_ports = end_port - start_port + 1

    progress_bar["value"] = 0
    status_label.config(text="Starting scan...")

    semaphore = threading.Semaphore(thread_count)

    def worker(port):
        if stop_flag:
            return
        semaphore.acquire()
        scan_port(target, port, tree, total_ports)
        semaphore.release()

    threads = []

    for port in range(start_port, end_port + 1):
        if stop_flag:
            break
        t = threading.Thread(target=worker, args=(port,))
        threads.append(t)
        t.start()

    def monitor():
        for t in threads:
            t.join()

        elapsed = round(time.time() - start_time, 2)

        if stop_flag:
            status_label.config(text=f"Scan Stopped | Time: {elapsed}s")
        else:
            status_label.config(
                text=f"Scan Complete | {len(results)} open ports | Time: {elapsed}s"
            )

    threading.Thread(target=monitor).start()


# ------------------ STOP ------------------
def stop_scan():
    global stop_flag
    stop_flag = True
    status_label.config(text="Stopping scan...")


# ------------------ SAVE ------------------
def save_results():
    if not results:
        messagebox.showinfo("Info", "No results to save")
        return

    filename = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Port", "Status", "Service", "Banner"])
        writer.writerows(results)

    messagebox.showinfo("Saved", f"Saved as {filename}")


# ------------------ CLEAR ------------------
def clear_results():
    tree.delete(*tree.get_children())
    results.clear()
    progress_bar["value"] = 0
    status_label.config(text="Status: Cleared")


# ------------------ UI ------------------
root = tk.Tk()
root.title("Cyber Port Scanner")
root.geometry("850x600")
root.configure(bg="#0d1117")

# Title
tk.Label(root, text="Cyber Port Scanner", font=("Arial", 18, "bold"),
         fg="#00ffcc", bg="#0d1117").pack(pady=10)

# Inputs
frame = tk.Frame(root, bg="#0d1117")
frame.pack()

labels = ["Target IP", "Start Port", "End Port", "Threads"]
entries = []

defaults = ["192.168.211.128", "1", "1024", "100"]

for i, label in enumerate(labels):
    tk.Label(frame, text=label, fg="white", bg="#0d1117").grid(row=i, column=0, padx=5, pady=2)
    entry = tk.Entry(frame)
    entry.insert(0, defaults[i])
    entry.grid(row=i, column=1, padx=5, pady=2)
    entries.append(entry)

ip_entry, start_port_entry, end_port_entry, thread_entry = entries

# Buttons
btn_frame = tk.Frame(root, bg="#0d1117")
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Start", bg="#238636", fg="white", width=10, command=start_scan).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Stop", bg="#da3633", fg="white", width=10, command=stop_scan).grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="Clear", bg="#d29922", fg="white", width=10, command=clear_results).grid(row=0, column=2, padx=5)
tk.Button(btn_frame, text="Save", bg="#1f6feb", fg="white", width=10, command=save_results).grid(row=0, column=3, padx=5)

# Progress
progress_bar = ttk.Progressbar(root, length=700)
progress_bar.pack(pady=5)

# Style table
style = ttk.Style()
style.theme_use("default")
style.configure("Treeview",
                background="#161b22",
                foreground="white",
                rowheight=25,
                fieldbackground="#161b22")
style.map("Treeview", background=[("selected", "#238636")])

# Table
columns = ("Port", "Status", "Service", "Banner")
tree = ttk.Treeview(root, columns=columns, show="headings", height=15)

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

tree.tag_configure("open", foreground="#00ff00")

tree.pack(fill="both", expand=True, pady=10)

# Status bar
status_label = tk.Label(root, text="Status: Ready",
                        bg="#161b22", fg="white")
status_label.pack(fill="x")

root.mainloop()

