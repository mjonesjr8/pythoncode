import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import csv
import os

# === CONFIGURATION ====
csv_path = os.path.expanduser("~/Documents/Peptide_Log.csv")
profile_path = os.path.expanduser("~/Documents/Peptide_Profiles.txt")
last_calc = {}
vial_usage = {}  # Tracks doses per vial

# === CORE FUNCTIONS ====
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
    units = min(units, 100)
    fill_width = int((units / 100) * 500)
    color = "#4caf50" if units <= 50 else "#ff9800" if units <= 80 else "#f44336"
    syringe_canvas.create_rectangle(0, 0, fill_width, 20, fill=color, tags="fill")
    for i in range(0, 101, 10):
        x = int((i / 100) * 500)
        syringe_canvas.create_line(x, 0, x, 20, fill="black", tags="ticks")
        syringe_canvas.create_text(x, 30, text=str(i), font=("Helvetica", 8), tags="ticks")

def save_profile():
    name = vial_name.get()
    compound = compound_type.get()
    size = vial_size.get()
    bac = bac_volume.get()
    if name and size and bac and compound:
        with open(profile_path, "a") as f:
            f.write(f"{name}|{compound}|{size}|{bac}\n")
        refresh_profile_dropdown()
        messagebox.showinfo("Saved", f"Profile saved: {name}")
    else:
        messagebox.showerror("Error", "Please fill in all profile fields.")

def load_profile():
    selected = profile_dropdown.get()
    if selected:
        parts = selected.split("|")
        if len(parts) == 4:
            vial_name.set(parts[0])
            compound_type.set(parts[1])
            vial_size.set(parts[2])
            bac_volume.set(parts[3])

def delete_profile():
    selected = profile_dropdown.get()
    if not selected:
        messagebox.showerror("Error", "Please select a profile to delete.")
        return
    confirm = messagebox.askyesno("Confirm Deletion", f"Delete profile:\n{selected}")
    if confirm:
        if os.path.exists(profile_path):
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

def log_injection():
    if not last_calc:
        messagebox.showerror("Error", "Please calculate dose first.")
        return
    vial = last_calc["vial"]
    vial_usage[vial] = vial_usage.get(vial, 0) + 1

    timestamp = f"{last_calc['date']} {datetime.now().strftime('%H:%M')}"
    entry = [timestamp, last_calc['compound'], vial, last_calc['dose'], last_calc['dose_mg'], last_calc['units'], last_calc['weight']]
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(entry)
    messagebox.showinfo("Logged", f"Injection logged: {entry}")
    refresh_log_dropdown()

def reset_vial_usage():
    vial = vial_name.get()
    vial_usage[vial] = 0
    messagebox.showinfo("Reset", f"Usage for '{vial}' reset to 0.")

def refresh_log_dropdown():
    if os.path.exists(csv_path):
        with open(csv_path, "r") as f:
            logs = [",".join(line.strip().split(",")) for line in f]
        log_dropdown["values"] = logs
    else:
        log_dropdown["values"] = []

def delete_log_entry():
    selected = log_dropdown.get()
    if not selected:
        messagebox.showerror("Error", "Please select an entry to delete.")
        return
    confirm = messagebox.askyesno("Confirm Deletion", f"Delete entry:\n{selected}")
    if confirm:
        if os.path.exists(csv_path):
            with open(csv_path, "r") as f:
                lines = f.readlines()
            with open(csv_path, "w") as f:
                for line in lines:
                    if ",".join(line.strip().split(",")) != selected:
                        f.write(line)
                    else:
                        parts = line.strip().split(",")
                        vial_name_deleted = parts[2]
                        if vial_name_deleted in vial_usage:
                            vial_usage[vial_name_deleted] = max(vial_usage[vial_name_deleted] - 1, 0)
        messagebox.showinfo("Deleted", "Entry deleted and vial usage updated.")
        refresh_log_dropdown()

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
    compound = compound_type.get()
    dose_info = calculate_dose(total_mcg, bac_ml, dose_mcg_val, vial)
    expiry = datetime.now() + timedelta(days=28)
    selected_date = date_picker.get()

    global last_calc
    last_calc = {
        "vial": vial,
        "compound": compound,
        "dose": dose_mcg_val,
        "dose_mg": dose_info["dose_mg"],
        "units": dose_info["units"],
        "date": selected_date,
        "weight": weight_lbs
    }

    output = [
        f"Compound: {compound}",
        f"Vial: {vial}",
        f"Vial Size: {vial_size.get()} mg",
        f"Dose: {dose_mcg_val} mcg ({dose_info['dose_mg']} mg)",
        f"Draw: {dose_info['units']} units on 100u syringe",
        f"Remaining Doses: {dose_info['remaining']}",
        f"Weight: {weight_lbs} lbs",
        f"Scheduled Date: {selected_date}",
        f"BAC Expires: {expiry.strftime('%m/%d/%Y')}"
    ]

    if datetime.now() > expiry:
        output.append("⚠️ WARNING: BAC expired!")
        messagebox.showwarning("Warning", "BAC has expired!")

    if dose_info["remaining"] < 5:
        output.append(f"⚠️ WARNING: Only {dose_info['remaining']} doses left in this vial!")
        messagebox.showwarning("Low Vial Warning", f"Only {dose_info['remaining']} doses remain in '{vial}'.")

    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, "\n".join(output))
    update_syringe_fill(dose_info["units"])

# === GUI SETUP ===
root = tk.Tk()
root.title("Peptide Multi-Tracker (No Matplotlib)")
root.geometry("580x700")

compound_type = tk.StringVar(value="BPC-157")
vial_name = tk.StringVar(value="Vial 1")
vial_size = tk.StringVar(value="10")
bac_volume = tk.StringVar(value="4")
dose = tk.StringVar(value="250")
weight = tk.StringVar()
date_picker = ttk.Entry(root)
date_picker.insert(0, datetime.now().strftime("%m/%d/%Y"))

# Fields
fields = [
    ("Compound Type:", compound_type),
    ("Vial Name:", vial_name),
    ("Vial Size (mg):", vial_size),
    ("BAC Volume (ml):", bac_volume),
    ("Dose (mcg):", dose),
    ("Weight (lbs):", weight),
    ("Select Date:", date_picker)
]

for i, (label_text, var) in enumerate(fields):
    tk.Label(root, text=label_text).place(x=20, y=20 + i*30)
    if isinstance(var, tk.StringVar):
        tk.Entry(root, textvariable=var).place(x=150, y=20 + i*30, width=140)
    else:
        var.place(x=150, y=20 + i*30, width=140)

tk.Button(root, text="Calculate Dose", command=calculate_action).place(x=20, y=300, width=120)
tk.Button(root, text="Log Injection", command=log_injection).place(x=160, y=300, width=120)
tk.Button(root, text="Reset Vial Usage", command=reset_vial_usage).place(x=300, y=300, width=120)

# Profile Management
tk.Button(root, text="Save Profile", command=save_profile).place(x=20, y=340, width=120)
profile_dropdown = ttk.Combobox(root)
profile_dropdown.place(x=150, y=340, width=270)
tk.Button(root, text="Load Profile", command=load_profile).place(x=440, y=340, width=80)
tk.Button(root, text="Delete Profile", command=delete_profile).place(x=20, y=370, width=120)

# Output Box
output_box = tk.Text(root, wrap="word")
output_box.place(x=20, y=410, width=540, height=120)

# Syringe Fill
tk.Label(root, text="Syringe Fill:").place(x=20, y=540)
syringe_canvas = tk.Canvas(root, width=540, height=40, bg="#ddd", highlightthickness=1, highlightbackground="#aaa")
syringe_canvas.place(x=20, y=560)

# Log Management
tk.Label(root, text="Delete Logged Entry:").place(x=20, y=610)
log_dropdown = ttk.Combobox(root)
log_dropdown.place(x=20, y=640, width=420)
tk.Button(root, text="Delete Entry", command=delete_log_entry).place(x=450, y=640, width=110)

refresh_profile_dropdown()
refresh_log_dropdown()
root.mainloop()
