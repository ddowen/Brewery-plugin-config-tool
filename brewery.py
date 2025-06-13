import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path

TRACKER_FILE = Path("config_tracker.json")
APPEND_FILE = "recipes.yml"
OUTPUT_DIR = Path(".")
OUTPUT_PREFIX = "output-"
OUTPUT_SUFFIX = ".log"

WOOD_OPTIONS = {
    "Any": 0, "Birch": 1, "Oak": 2, "Jungle": 3,
    "Spruce": 4, "Acacia": 5, "Dark Oak": 6, "Crimson": 7,
    "Warped": 8, "Mangrove": 9, "Cherry": 10, "Bamboo": 11,
    "Cut Copper": 12
}

def get_next_output_id():
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE, "r") as f:
            return json.load(f).get("next_id", 1)
    return 1

def increment_output_id():
    current = get_next_output_id()
    with open(TRACKER_FILE, "w") as f:
        json.dump({"next_id": current + 1}, f)

class BrewConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Brew Config Generator")
        self.entries = {}
        self.ingredients = []
        self.lore = []
        self.name_vars = {}

        self.build_gui()

    def build_gui(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Text fields (strings)
        self.add_field(frame, "UUID", "Name in config", is_int=False)

        # Names (3 sub-fields combined with slashes)
        self.add_name_fields(frame)

        # Ingredients section
        self.add_ingredient_section(frame)

        # Integer fields (these are validated to be integers)
        self.add_field(frame, "Cooking Time", "Integer", is_int=True)
        self.add_field(frame, "Distill Runs", "Integer", is_int=True)
        self.add_dropdown(frame, "Barrel Type", "", list(WOOD_OPTIONS.keys()))
        self.add_field(frame, "Age", "Integer", is_int=True)
        self.add_field(frame, "Color (any hex value)", "", is_int=False)
        self.add_slider(frame, "Difficulty", 1, 10)
        self.add_field(frame, "Alcohol in ml", "Integer", is_int=True)

        # Lore lines section
        self.add_lore_section(frame)

        tk.Button(frame, text="Generate Config", command=self.generate_config).pack(pady=10)

    def add_field(self, parent, label, typ, is_int=False):
        f = tk.Frame(parent)
        f.pack(fill=tk.X, pady=2)
        label_text = f"{label}"
        if typ:
            label_text += f" ({typ})"
        tk.Label(f, text=label_text, width=20, anchor="w").pack(side=tk.LEFT)
        var = tk.StringVar()
        entry = tk.Entry(f, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entries[label] = (var, is_int)

    def add_dropdown(self, parent, label, typ, options):
        f = tk.Frame(parent)
        f.pack(fill=tk.X, pady=2)
        label_text = label
        if typ:
            label_text += f" ({typ})"
        tk.Label(f, text=label_text, width=20, anchor="w").pack(side=tk.LEFT)
        var = tk.StringVar(value=options[0])
        dropdown = ttk.Combobox(f, textvariable=var, values=options, state="readonly")
        dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entries[label] = (var, False)

    def add_slider(self, parent, label, minval, maxval):
        f = tk.Frame(parent)
        f.pack(fill=tk.X, pady=2)
        label_var = tk.StringVar(value=f"{label}: {minval}")
        tk.Label(f, textvariable=label_var, width=20, anchor="w").pack(side=tk.LEFT)
        var = tk.IntVar(value=minval)
        style = ttk.Style()
        style.configure("Custom.Horizontal.TScale", sliderlength=10)
        slider = ttk.Scale(f, variable=var, from_=minval, to=maxval, orient=tk.HORIZONTAL, length=150, style="Custom.Horizontal.TScale")
        slider.pack(side=tk.LEFT)
        slider.config(command=lambda val: label_var.set(f"{label}: {int(float(val))}"))  # cast float->int
        self.entries[label] = (var, True)


    def add_name_fields(self, parent):
        f = tk.Frame(parent)
        f.pack(fill=tk.X, pady=2)
        for name in ["poor", "average", "pristine"]:
            subf = tk.Frame(f)
            subf.pack(side=tk.LEFT, padx=5)
            tk.Label(subf, text=name.capitalize()).pack()
            var = tk.StringVar()
            entry = tk.Entry(subf, textvariable=var, width=15)
            entry.pack()
            self.name_vars[name] = var

    def add_ingredient_section(self, parent):
        tk.Label(parent, text="Ingredients (item / qty)", anchor="w").pack()
        self.ingredient_frame = tk.Frame(parent)
        self.ingredient_frame.pack(fill=tk.X)
        self.add_ingredient()
        tk.Button(parent, text="+ Add Ingredient", command=self.add_ingredient).pack(pady=2)

    def add_ingredient(self):
        frame = tk.Frame(self.ingredient_frame)
        frame.pack(fill=tk.X, pady=1)

        item_var = tk.StringVar()
        qty_var = tk.StringVar()

        item_entry = tk.Entry(frame, textvariable=item_var)
        item_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))

        qty_entry = tk.Entry(frame, textvariable=qty_var, width=5)
        qty_entry.pack(side=tk.LEFT)

        self.ingredients.append((item_var, qty_var))

    def add_lore_section(self, parent):
        tk.Label(parent, text="Lore", anchor="w").pack()
        self.lore_frame = tk.Frame(parent)
        self.lore_frame.pack(fill=tk.X)
        self.add_lore()
        tk.Button(parent, text="+ Add Lore", command=self.add_lore).pack(pady=2)

    def add_lore(self):
        var = tk.StringVar()
        entry = tk.Entry(self.lore_frame, textvariable=var)
        entry.pack(fill=tk.X, pady=1)
        self.lore.append(var)

    def generate_config(self):
        try:
            data = {}
            for key, (var, is_int) in self.entries.items():
                if is_int:
                    val_raw = var.get()
                    if isinstance(val_raw, int):
                        val = val_raw
                    else:
                        val = int(val_raw.strip())
                else:
                    val = var.get().strip()

                if key == "Color (any hex value)" and val and not val.startswith("#"):
                    raise ValueError("Color must start with '#'")

                data[key] = val

            name_data = [self.name_vars[k].get().strip() for k in ["poor", "average", "pristine"]]
            data["Name"] = "/".join(name_data)

            ingredients = []
            for item_var, qty_var in self.ingredients:
                item = item_var.get().strip()
                qty_raw = qty_var.get().strip()
                if item and qty_raw:
                    qty = int(qty_raw)
                    ingredients.append(f"{item}/{qty}")

            wood_code = WOOD_OPTIONS.get(data["Barrel Type"], 0)

            lore = [line.get().strip() for line in self.lore if line.get().strip()]

            yaml_block = f"{data['UUID']}:\n"
            yaml_block += f"  name: {data['Name']}\n"
            yaml_block += f"  ingredients:\n"
            for ingr in ingredients:
                yaml_block += f"  - {ingr}\n"
            yaml_block += f"  cookingtime: {data['Cooking Time']}\n"
            yaml_block += f"  distillruns: {data['Distill Runs']}\n"
            yaml_block += f"  wood: {wood_code}\n"
            yaml_block += f"  age: {data['Age']}\n"
            yaml_block += f"  color: {data['Color (any hex value)']}\n"
            yaml_block += f"  difficulty: {data['Difficulty']}\n"
            yaml_block += f"  alcohol: {data['Alcohol in ml']}\n"
            yaml_block += f"  lore:\n"
            for l in lore:
                yaml_block += f"  - {l}\n"

            self.output_result(yaml_block)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def output_result(self, yaml_block):
        popup = tk.Toplevel(self.root)
        popup.title("Generated Config")
        text = tk.Text(popup, wrap=tk.WORD)
        text.insert("1.0", yaml_block)
        text.pack(expand=True, fill=tk.BOTH)
        text.config(state=tk.NORMAL)

        next_id = get_next_output_id()
        numbered_path = OUTPUT_DIR / f"{OUTPUT_PREFIX}{next_id:02}{OUTPUT_SUFFIX}"
        with open(numbered_path, "w") as f:
            f.write(yaml_block)
        increment_output_id()

        with open(APPEND_FILE, "a") as f:
            f.write("\n" + yaml_block)

        messagebox.showinfo("Success", f"Saved as:\n{numbered_path}\nAppended to {APPEND_FILE}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BrewConfigApp(root)
    root.mainloop()
