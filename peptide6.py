import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import csv
import os
import winsound
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
from tkcalendar import DateEntry

# === SPLASH / DISCLAIMER ====
def show_splash(root):
    splash = tk.Toplevel(root)
    splash.title("Research Use Disclaimer")
    splash.geometry("540x300")
    splash.resizable(False, False)
    splash.configure(bg="#f8f8f8")
    splash.transient(root)
    splash.grab_set()

    tk.Label(
        splash,
        text="⚠️ Research Use Only",
        font=("Helvetica", 16, "bold"),
        bg="#f8f8f8",
        fg="#333"
    ).pack(pady=(20, 10))

    disclaimer_text = (
        "This software is provided for informational and research purposes only.\n\n"
        "It is not intended to provide medical advice, diagnosis, or treatment.\n"
        "Use at your own risk. The author assumes no responsibility for misuse."
    )

    tk.Label(
        splash,
        text=disclaimer_text,
        font=("Helvetica", 11),
        bg="#f8f8f8",
        wraplength=480,
        justify="center",
        fg="#333"
    ).pack(padx=20, pady=(0, 10))

    agree_var = tk.BooleanVar(value=False)

    def toggle_continue():
        btn_continue.config(state="normal" if agree_var.get() else "disabled")

    ttk.Checkbutton(
        splash,
        text="I understand and accept the risks.",
        variable=agree_var,
        command=toggle_continue
    ).pack(pady=10)

    btn_frame = tk.Frame(splash, bg="#f8f8f8")
    btn_frame.pack(pady=10)

    def on_continue():
        splash.destroy()

    def on_quit():
        root.destroy()

    btn_continue = ttk.Button(btn_frame, text="Continue", command=on_continue, state="disabled")
    btn_quit = ttk.Button(btn_frame, text="Quit", command=on_quit)
    btn_continue.grid(row=0, column=0, padx=10)
    btn_quit.grid(row=0, column=1, padx=10)

    root.wait_window(splash)


# === CONFIGURATION ===
base_dir = os.path.expanduser("~/Documents")
profile_path = os.path.join(base_dir, "BPC157_Profiles.txt")
config_path = os.path.join(base_dir, "BPC157_LastProfile.txt")
syringe_path = os.path.join(base_dir, "BPC157_LastSyringe.txt")

last_calc = {}
vial_usage = {}

def get_csv_path(vial):
    safe_name = "".join(c for c in vial if c.isalnum() or c in ("_", "-")).replace(" ", "_")
    return os.path.join(base_dir, f"BPC157_{safe_name}_Log.csv")


# === CORE FUNCTIONS ===
def calculate_dose(total_mcg, bac_ml, dose_mcg, vial_name):
    concentration = total_mcg / bac_ml
    dose_volume_ml = round(dose_mcg / concentration, 3)
    units = round(dose_volume_ml * 100, 1)
    max_doses = total_mcg // dose_mcg
    used = vial_usage.get(vial_name, 0)
    remaining = max(max_doses - used, 0)
    dose_mg = round(dose_mcg / 1000, 3)
    return {"volume": dose_volume_ml, "units": units, "remaining": remaining, "dose_mg": dose_mg}


def update_syringe_fill(units):
    syringe_canvas.delete("fill")
    syringe_canvas.delete("ticks")
    try:
        syringe_ml = float(syringe_size.get())
    except:
        syringe_ml = 1.0

    max_units = syringe_ml * 100
    units = min(units, max_units)
    fill_width = int((units / max_units) * 500)

    color = "#4caf50" if units <= (0.5 * max_units) else "#ff9800" if units <= (0.8 * max_units) else "#f44336"
    syringe_canvas.create_rectangle(0, 0, fill_width, 20, fill=color, tags="fill")

    for i in range(0, int(max_units) + 1, int(max_units / 10)):
        x = int((i / max_units) * 500)
        syringe_canvas.create_line(x, 0, x, 20, fill="black", tags="ticks")
        syringe_canvas.create_text(x, 30, text=str(int(i)), font=("Helvetica", 8), tags="ticks")


def save_profile():
    name, size, bac = vial_name.get(), vial_size.get(), bac_volume.get()
    if name and size and bac:
        with open(profile_path, "a") as f:
            f.write(f"{name}|{size}|{bac}\n")
        with open(config_path, "w") as f:
            f.write(f"{name}|{size}|{bac}")
        refresh_profile_dropdown()
        messagebox.showinfo("Saved", f"Profile saved: {name}")
    else:
        messagebox.showerror("Error", "Please fill in all profile fields.")


def load_profile():
    selected = profile_dropdown.get()
    if selected:
        parts = selected.split("|")
        if len(parts) == 3:
            vial_name.set(parts[0])
            vial_size.set(parts[1])
            bac_volume.set(parts[2])
            with open(config_path, "w") as f:
                f.write(selected)
            refresh_log_dropdown()


def delete_profile():
    selected = profile_dropdown.get()
    if not selected:
        messagebox.showerror("Error", "Please select a profile to delete.")
        return
    confirm = messagebox.askyesno("Confirm Deletion", f"Delete profile:\n{selected}")
    if confirm and os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            profiles = [line.strip() for line in f]
        with open(profile_path, "w") as f:
            for profile in profiles:
                if profile != selected:
                    f.write(profile + "\n")
        messagebox.showinfo("Deleted", "Profile deleted.")
        refresh_profile_dropdown()


def refresh_profile_dropdown():
    if os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            profiles = [line.strip() for line in f]
        profile_dropdown["values"] = profiles
    else:
        profile_dropdown["values"] = []


def auto_load_last_profile():
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            line = f.read().strip()
            if "|" in line:
                parts = line.split("|")
                if len(parts) == 3:
                    vial_name.set(parts[0])
                    vial_size.set(parts[1])
                    bac_volume.set(parts[2])
                    profile_dropdown.set(line)
                    refresh_log_dropdown()


def save_last_syringe():
    with open(syringe_path, "w") as f:
        f.write(syringe_size.get())


def auto_load_last_syringe():
    if os.path.exists(syringe_path):
        with open(syringe_path, "r") as f:
            val = f.read().strip()
            if val in ["1.0", "0.5", "0.3"]:
                syringe_size.set(val)


def refresh_log_dropdown():
    vial = vial_name.get().strip()
    csv_path = get_csv_path(vial)
    if os.path.exists(csv_path):
        with open(csv_path, "r") as f:
            logs = [",".join(line.strip().split(",")) for line in f]
        log_dropdown["values"] = logs
    else:
        log_dropdown["values"] = []


def reset_vial_usage():
    vial = vial_name.get()
    vial_usage[vial] = 0
    messagebox.showinfo("Reset", f"Usage for '{vial}' reset to 0.")


def doses_today_info():
    vial = vial_name.get().strip()
    csv_path = get_csv_path(vial)
    if not os.path.exists(csv_path):
        return 0, []
    today = datetime.now().strftime("%m/%d/%Y")
    times = []
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) > 0 and row[0].startswith(today):
                parts = row[0].split()
                if len(parts) > 1:
                    times.append(parts[1])
    return len(times), times


def log_injection():
    if not last_calc:
        messagebox.showerror("Error", "Please calculate dose first.")
        return

    count_today, times = doses_today_info()
    if count_today >= 1:
        times_str = ", ".join(times)
        proceed = messagebox.askyesno(
            "Confirm Additional Dose",
            f"You’ve already logged {count_today} dose{'s' if count_today > 1 else ''} today.\n"
            f"Previous times: {times_str}\n\n"
            "Are you sure you want to log another?"
        )
        if not proceed:
            return

    vial = last_calc["vial"]
    csv_path = get_csv_path(vial)
    vial_usage[vial] = vial_usage.get(vial, 0) + 1

    timestamp = f"{last_calc['date']} {datetime.now().strftime('%I:%M %p')}"
    entry = [timestamp, vial, last_calc['dose'], last_calc['dose_mg'], last_calc['units'], last_calc['weight']]
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(entry)

    winsound.MessageBeep(winsound.MB_ICONASTERISK)
    messagebox.showinfo("Logged", f"Injection logged: {entry}")
    refresh_log_dropdown()


def delete_log_entry():
    vial = vial_name.get().strip()
    csv_path = get_csv_path(vial)
    selected = log_dropdown.get().strip()
    if not selected:
        messagebox.showerror("Error", "Please select a log entry to delete.")
        return
    if not os.path.exists(csv_path):
        messagebox.showerror("Error", f"No log file for {vial}.")
        return

    confirm = messagebox.askyesno("Confirm Deletion", f"Delete this log entry?\n\n{selected}")
    if not confirm:
        return

    with open(csv_path, "r") as f:
        rows = [line.strip() for line in f]
    with open(csv_path, "w") as f:
        for row in rows:
            if row.strip() != selected:
                f.write(row + "\n")

    messagebox.showinfo("Deleted", "Log entry deleted.")
    refresh_log_dropdown()


def show_dose_trend():
    vial = vial_name.get().strip()
    csv_path = get_csv_path(vial)
    if not os.path.exists(csv_path):
        messagebox.showerror("Error", f"No log file found for {vial}.")
        return

    dates, doses = [], []
    with open(csv_path, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 4:
                try:
                    dt = datetime.strptime(row[0].split()[0], "%m/%d/%Y")
                    mg = float(row[3])
                    dates.append(dt)
                    doses.append(mg)
                except:
                    continue

    if not dates:
        messagebox.showinfo("No Data", f"No valid data found for {vial}.")
        return

    plt.figure(figsize=(6, 4))
    plt.plot_date(date2num(dates), doses, linestyle="-", marker="o", color="#1565C0")
    plt.title(f"Dose Trend — {vial}", fontsize=12, fontweight="bold")
    plt.xlabel("Date")
    plt.ylabel("Dose (mg)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()


def calculate_action():
    try:
        total_mcg = int(vial_size.get()) * 1000
        bac_ml = float(bac_volume.get())
        dose_mcg_val = int(dose.get())
        weight_lbs = float(weight.get())
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numbers for Vial Size, BAC Volume, Dose, and Weight.")
        return

    vial = vial_name.get()
    dose_info = calculate_dose(total_mcg, bac_ml, dose_mcg_val, vial)
    expiry = datetime.now() + timedelta(days=28)
    selected_date = date_picker.get_date().strftime("%m/%d/%Y")

    global last_calc
    last_calc = {
        "vial": vial,
        "dose": dose_mcg_val,
        "dose_mg": dose_info["dose_mg"],
        "units": dose_info["units"],
        "date": selected_date,
        "weight": weight_lbs
    }

    syringe_units = float(syringe_size.get()) * 100
    lines = [
        f"Vial: {vial}",
        f"Vial Size: {vial_size.get()} mg",
        f"BAC Volume: {bac_volume.get()} ml",
        f"Dose: {dose_mcg_val}mcg ({dose_mcg_val / 1000:.2f}mg)",
        f"Draw: {dose_info['units']} units on {syringe_units:.0f}u syringe ({syringe_size.get()}ml)",
        f"Remaining Doses: {dose_info['remaining']}",
        f"Weight: {weight_lbs} lbs",
        f"Scheduled Date: {selected_date}",
        f"BAC Expires: {expiry.strftime('%m/%d/%Y')}"
    ]

    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.tag_configure("mg", foreground="#1565C0", font=("Helvetica", 10, "bold"))
    for i, line in enumerate(lines):
        output_box.insert(tk.END, line + "\n")
        if "Dose:" in line:
            start, end = line.find("("), line.find("mg)") + 3
            if start != -1 and end != -1:
                output_box.tag_add("mg", f"{i+1}.{start}", f"{i+1}.{end}")
    output_box.config(state="disabled")
    update_syringe_fill(dose_info["units"])
    save_last_syringe()


# === GUI ===
root = tk.Tk()
root.title("Peptide Logging App")
root.geometry("580x760")

show_splash(root)

vial_name = tk.StringVar(value="Vial 1")
vial_size = tk.StringVar(value="10")
bac_volume = tk.StringVar(value="4")
dose = tk.StringVar(value="250")
weight = tk.StringVar()
syringe_size = tk.StringVar(value="1.0")

date_picker = DateEntry(root, date_pattern="mm/dd/yyyy")
date_picker.set_date(datetime.now())

fields = [
    ("Vial Name:", vial_name),
    ("Vial Size (mg):", vial_size),
    ("BAC Volume (ml):", bac_volume),
    ("Dose (mcg):", dose),
    ("Weight (lbs):", weight),
    ("Select Date:", date_picker)
]

for i, (label, var) in enumerate(fields):
    tk.Label(root, text=label).place(x=20, y=20 + i * 30)
    if isinstance(var, tk.StringVar):
        tk.Entry(root, textvariable=var).place(x=150, y=20 + i * 30, width=120)
    else:
        var.place(x=150, y=20 + i * 30, width=120)

tk.Label(root, text="Syringe Size (ml):").place(x=300, y=110)
syringe_menu = ttk.Combobox(root, textvariable=syringe_size, values=["1.0", "0.5", "0.3"], state="readonly")
syringe_menu.place(x=420, y=110, width=70)
syringe_menu.bind("<<ComboboxSelected>>", lambda e: save_last_syringe())

tk.Button(root, text="Calculate Dose", command=calculate_action).place(x=20, y=300, width=120)
tk.Button(root, text="Log Injection", command=log_injection).place(x=160, y=300, width=120)
tk.Button(root, text="Repeat Last Dose", command=lambda: [last_calc.update({"date": datetime.now().strftime("%m/%d/%Y")}), log_injection()]).place(x=300, y=300, width=120)
tk.Button(root, text="View Graph", command=show_dose_trend).place(x=440, y=300, width=90)
tk.Button(root, text="Reset Vial Usage", command=reset_vial_usage).place(x=300, y=270, width=120)

tk.Button(root, text="Save Vial Profile", command=save_profile).place(x=20, y=240, width=120)
profile_dropdown = ttk.Combobox(root)
profile_dropdown.place(x=160, y=240, width=270)
tk.Button(root, text="Load Profile", command=load_profile).place(x=440, y=240, width=80)
tk.Button(root, text="Delete Profile", command=delete_profile).place(x=20, y=270, width=120)

output_box = tk.Text(root, wrap="word", state="disabled")
output_box.place(x=20, y=340, width=520, height=120)

tk.Label(root, text="Syringe Fill:").place(x=20, y=470)
syringe_canvas = tk.Canvas(root, width=520, height=40, bg="#ddd", highlightthickness=1, highlightbackground="#aaa")
syringe_canvas.place(x=20, y=490)

tk.Label(root, text="Delete Logged Entry:").place(x=20, y=540)
log_dropdown = ttk.Combobox(root)
log_dropdown.place(x=20, y=570, width=340)
tk.Button(root, text="Delete Entry", command=delete_log_entry).place(x=370, y=570, width=90)

refresh_profile_dropdown()
auto_load_last_profile()
auto_load_last_syringe()
refresh_log_dropdown()
root.mainloop()
