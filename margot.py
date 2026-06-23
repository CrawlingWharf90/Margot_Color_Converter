import customtkinter as ctk
from tkinter import filedialog, messagebox
from CTkColorPicker import CTkColorPicker
from PIL import Image
import json
import os
import math
import colorsys

#* ==========================================
#* 1. CORE IMAGE PROCESSING
#* ==========================================
def shift_image(input_path, output_path, shirt_hex, alpha):
    shirt_hex = shirt_hex.lstrip('#')
    shirt_r, shirt_g, shirt_b = tuple(int(shirt_hex[i:i+2], 16) for i in (0, 2, 4))
    
    img = Image.open(input_path).convert("RGBA")
    pixels = img.load()
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0: continue
            
            new_r = max(0, min(255, int((r - shirt_r * (1 - alpha)) / alpha)))
            new_g = max(0, min(255, int((g - shirt_g * (1 - alpha)) / alpha)))
            new_b = max(0, min(255, int((b - shirt_b * (1 - alpha)) / alpha)))
            
            pixels[x, y] = (new_r, new_g, new_b, a)
            
    img.save(output_path)

#* ==========================================
#* 2. COLOR PICKER WINDOW
#* ==========================================
class ColorPickerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Target Color Matrix")
        self.geometry("420x540")
        self.configure(fg_color="#0A0A0C")
        self.attributes("-topmost", True)
        self.resizable(False, False)

        self.current_mode = "hex" 
        self._is_updating = False

        self.picker = CTkColorPicker(
            self, 
            width=300, 
            command=self.on_picker_drag,
            fg_color="#12121A"
        )
        self.picker.pack(pady=(20, 10))

        try: #! Remove various unneeded internal color picker sliders and labels
            if hasattr(self.picker, 'slider'):
                self.picker.slider.pack_forget()
                
            def clear_text(widget):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        text = child.cget("text")
                        
                        if isinstance(text, str) and "#" in text:
                            child.configure(text="")
                            
                            original_configure = child.configure
                            
                            def muted_configure(*args, orig=original_configure, **kwargs):
                                if "text" in kwargs:
                                    kwargs["text"] = ""
                                return orig(*args, **kwargs)
                                
                            child.configure = muted_configure
                            
                    clear_text(child)
            clear_text(self.picker)
        except Exception:
            pass

        self.input_container = ctk.CTkFrame(self, fg_color="transparent")
        self.input_container.pack(pady=10, fill="x")

        self.hex_frame = ctk.CTkFrame(self.input_container, fg_color="transparent")
        self.hex_entry = ctk.CTkEntry(
            self.hex_frame, 
            width=200, 
            height=40,
            justify="center", 
            font=("Courier New", 16, "bold"),
            text_color="#00A8FF",
            fg_color="#12121A",
            border_color="#2A2A2A"
        )
        self.hex_entry.pack()
        self.hex_entry.bind("<KeyRelease>", self.on_hex_type)
        self.hex_entry.bind("<Return>", lambda e: self.force_picker_update())
        self.hex_entry.bind("<FocusOut>", lambda e: self.force_picker_update())

        self.rgb_frame = ctk.CTkFrame(self.input_container, fg_color="transparent")
        
        self.r_entry = ctk.CTkEntry(self.rgb_frame, width=60, height=40, justify="center", font=("Courier New", 14))
        self.g_entry = ctk.CTkEntry(self.rgb_frame, width=60, height=40, justify="center", font=("Courier New", 14))
        self.b_entry = ctk.CTkEntry(self.rgb_frame, width=60, height=40, justify="center", font=("Courier New", 14))
        
        self.r_entry.pack(side="left", padx=8)
        self.g_entry.pack(side="left", padx=8)
        self.b_entry.pack(side="left", padx=8)

        for entry in (self.r_entry, self.g_entry, self.b_entry):
            entry.bind("<KeyRelease>", self.on_rgb_type)
            entry.bind("<Return>", lambda e: self.force_picker_update())
            entry.bind("<FocusOut>", lambda e: self.force_picker_update())

        self.hex_frame.pack()

        self.toggle_btn = ctk.CTkButton(
            self, 
            text="Switch to RGB", 
            command=self.toggle_input_mode,
            fg_color="transparent",
            text_color="#6C6C75",
            hover_color="#1A1A24"
        )
        self.toggle_btn.pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(
            btn_frame, text="Use Color", command=self.use_color, 
            fg_color="#1E1E26", hover_color="#2A2A35", width=140, height=40
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, text="Save & Use", command=self.save_color, 
            fg_color="#005C99", hover_color="#00a8ff", width=140, height=40, font=("Helvetica", 13, "bold")
        ).pack(side="left", padx=10)

        self.on_picker_drag(self.picker.get())

    def force_picker_update(self):
        """Calculates X,Y coordinates and executes a delayed override of the visual colors."""
        hex_val = self.hex_entry.get().strip().upper()
        if len(hex_val) == 7 and hex_val.startswith('#'):
            try:
                r, g, b = tuple(int(hex_val.lstrip('#')[i:i+2], 16) / 255.0 for i in (0, 2, 4))
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                
                h_deg = h * 360
                if h_deg <= 120:
                    angle_deg = h_deg * 1.5
                elif h_deg <= 240:
                    angle_deg = 180 + (h_deg - 120) * 0.75
                else:
                    angle_deg = 270 + (h_deg - 240) * 0.75
                    
                angle = math.radians(angle_deg)

                canvas_size = self.picker.canvas.winfo_width()
                if canvas_size <= 1: canvas_size = 200
                
                center = canvas_size / 2
                radius = s * (center - 10) 
                
                target_x = center + (radius * math.cos(angle))
                target_y = center - (radius * math.sin(angle))
                
                class DummyEvent:
                    def __init__(self, x, y):
                        self.x = x
                        self.y = y
                
                self._is_updating = True
                
                if hasattr(self.picker, 'slider'):
                    brightness_val = int(v * 255)
                    self.picker.slider.set(brightness_val)
                
                self.picker.on_mouse_drag(DummyEvent(target_x, target_y))
                
                def apply_perfect_color():
                    try:
                        imperfect_color = self.picker.get().upper()
                        
                        self.picker.default_hex_color = hex_val
                        
                        def sweep_and_clean(widget):
                            for child in widget.winfo_children():
                                if isinstance(child, ctk.CTkLabel):
                                    text = child.cget("text")
                                    if isinstance(text, str) and "#" in text:
                                        child.configure(text="")
                                
                                try:
                                    current_fg = child.cget("fg_color")
                                    if isinstance(current_fg, str) and current_fg.upper() == imperfect_color:
                                        child.configure(fg_color=hex_val)
                                    elif isinstance(current_fg, (list, tuple)):
                                        if any(c.upper() == imperfect_color for c in current_fg if isinstance(c, str)):
                                            child.configure(fg_color=hex_val)
                                except Exception:
                                    pass
                                
                                sweep_and_clean(child)
                                
                        sweep_and_clean(self.picker)
                    finally:
                        self._is_updating = False

                self.after(50, apply_perfect_color)
                
            except Exception:
                self._is_updating = False

    def on_picker_drag(self, color_hex):
        if self._is_updating: return
        self._is_updating = True

        self.hex_entry.delete(0, 'end')
        self.hex_entry.insert(0, color_hex.upper())

        r, g, b = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        self.r_entry.delete(0, 'end'); self.r_entry.insert(0, str(r))
        self.g_entry.delete(0, 'end'); self.g_entry.insert(0, str(g))
        self.b_entry.delete(0, 'end'); self.b_entry.insert(0, str(b))

        self._is_updating = False

    def on_hex_type(self, event=None):
        if self._is_updating: return
        
        raw_val = self.hex_entry.get().strip().upper()
        if not raw_val.startswith('#'):
            raw_val = '#' + raw_val.replace('#', '')
            
        valid_chars = set('0123456789ABCDEF')
        clean_val = '#' + ''.join(c for c in raw_val[1:] if c in valid_chars)[:6]
        
        if clean_val != self.hex_entry.get():
            self._is_updating = True
            self.hex_entry.delete(0, 'end')
            self.hex_entry.insert(0, clean_val)
            self._is_updating = False
            
        if len(clean_val) == 7:
            try:
                self._is_updating = True
                r, g, b = tuple(int(clean_val.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                self.r_entry.delete(0, 'end'); self.r_entry.insert(0, str(r))
                self.g_entry.delete(0, 'end'); self.g_entry.insert(0, str(g))
                self.b_entry.delete(0, 'end'); self.b_entry.insert(0, str(b))
            except ValueError:
                pass
            finally:
                self._is_updating = False

    def on_rgb_type(self, event=None):
        if self._is_updating: return
        
        try:
            def get_clean_digit(entry):
                val = entry.get().strip()
                digits = ''.join(filter(str.isdigit, val))
                if not digits:
                    return 0
                num = min(255, int(digits))
                if str(num) != val:
                    entry.delete(0, 'end')
                    entry.insert(0, str(num))
                return num

            r_val = get_clean_digit(self.r_entry)
            g_val = get_clean_digit(self.g_entry)
            b_val = get_clean_digit(self.b_entry)

            self._is_updating = True
            hex_val = f"#{r_val:02x}{g_val:02x}{b_val:02x}".upper()
            self.hex_entry.delete(0, 'end')
            self.hex_entry.insert(0, hex_val)
        except Exception:
            pass
        finally:
            self._is_updating = False

    def toggle_input_mode(self):
        if self.current_mode == "hex":
            self.hex_frame.pack_forget()
            self.rgb_frame.pack()
            self.toggle_btn.configure(text="Switch to Hex")
            self.current_mode = "rgb"
        else:
            self.rgb_frame.pack_forget()
            self.hex_frame.pack()
            self.toggle_btn.configure(text="Switch to RGB")
            self.current_mode = "hex"

    def use_color(self):
        hex_val = self.hex_entry.get().strip()
        if len(hex_val) == 7:
            self.parent.set_active_color("Custom Unsaved", hex_val)
            self.destroy()

    def save_color(self):
        hex_val = self.hex_entry.get().strip()
        if len(hex_val) != 7:
            messagebox.showerror("Error", "Invalid color formatting.")
            return
            
        if any(c['hex'].lower() == hex_val.lower() for c in self.parent.saved_colors):
            messagebox.showwarning("Warning", "This color profile is already saved!")
            return

        dialog = ctk.CTkInputDialog(text=f"Assign an alias for {hex_val}:", title="Save Color Profile")
        name = dialog.get_input()
        
        if name:
            self.parent.saved_colors.append({"name": name.strip(), "hex": hex_val})
            self.parent.save_colors_to_json()
            self.parent.refresh_color_list()
            self.parent.set_active_color(name.strip(), hex_val)
            self.destroy()

#* ==========================================
#* 3. MAIN APPLICATION GUI
#* ==========================================
class Margot(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Margot Color Converter")
        self.geometry("500x650")
        self.configure(fg_color="#0a0a0c")

        self.json_file = "user_colors.json"
        self.saved_colors = self.load_colors()
        self.input_image_path = None
        self.active_shirt_hex = None

        self.build_ui()

    def load_colors(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, "r") as f:
                return json.load(f)
        return [{"name": "Default White", "hex": "#FFFFFF"}]

    def save_colors_to_json(self):
        with open(self.json_file, "w") as f:
            json.dump(self.saved_colors, f, indent=4)

    def build_ui(self):
        ctk.CTkLabel(self, text="—ฅ/ᐠ. ̫ .ᐟ\ฅ —", font=("Helvetica", 24, "bold"), text_color="#00a8ff").pack(pady=(30, 20))

        self.img_label = ctk.CTkLabel(self, text="No Image Selected", text_color="gray")
        self.img_label.pack(pady=(0, 5))
        ctk.CTkButton(self, text="Select Design", command=self.pick_image, fg_color="#1E1E1E", hover_color="#2A2A2A").pack(pady=(0, 20))

        ctk.CTkLabel(self, text="Printer Ink Alpha (Opacity) Threshold\n[Usually around 0.4-0.6]", text_color="#00a8ff", font=("Segoe UI", 14)).pack()
        self.alpha_slider = ctk.CTkSlider(self, from_=0.1, to=1.0, number_of_steps=90, button_color="#00a8ff", button_hover_color="#007ACC")
        self.alpha_slider.set(0.5)
        self.alpha_slider.pack(pady=10)
        self.alpha_val_label = ctk.CTkLabel(self, text="0.50")
        self.alpha_val_label.pack()
        self.alpha_slider.configure(command=lambda v: self.alpha_val_label.configure(text=f"{v:.2f}"))

        color_frame = ctk.CTkFrame(self, fg_color="#141416", corner_radius=10)
        color_frame.pack(pady=20, padx=40, fill="x")
        
        ctk.CTkLabel(color_frame, text="Shirt Color", font=("Helvetica", 14, "bold")).pack(pady=(10, 5))

        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.filter_colors)
        self.search_entry = ctk.CTkEntry(color_frame, placeholder_text="Search saved colors...", textvariable=self.search_var)
        self.search_entry.pack(pady=5, padx=20, fill="x")

        self.color_dropdown = ctk.CTkOptionMenu(color_frame, values=[], command=self.select_dropdown_color, fg_color="#1E1E1E", button_color="#2A2A2A")
        self.color_dropdown.pack(pady=10, padx=20, fill="x")

        self.active_color_label = ctk.CTkLabel(self, text="Ready: Select an image and a shirt color.", text_color="gray")
        self.active_color_label.pack(pady=10)

        ctk.CTkButton(color_frame, text="+ Add New Color", command=self.open_color_picker, fg_color="transparent", border_width=1, border_color="#00a8ff", text_color="#00a8ff").pack(pady=(0, 15))

        self.refresh_color_list()

        ctk.CTkButton(self, text="PROCESS & SAVE IMAGE", command=self.process_and_save, font=("Helvetica", 14, "bold"), fg_color="#00a8ff", hover_color="#007ACC", height=45).pack(pady=20)

    def pick_image(self):
        filepath = filedialog.askopenfilename(filetypes=[("PNG Images", "*.png")])
        if filepath:
            self.input_image_path = filepath
            self.img_label.configure(text=os.path.basename(filepath), text_color="white")

    def filter_colors(self, *args):
        query = self.search_var.get().lower()
        filtered = [c['name'] for c in self.saved_colors if query in c['name'].lower()]
        self.color_dropdown.configure(values=filtered if filtered else ["No matches found"])
        if filtered:
            self.color_dropdown.set(filtered[0])

    def refresh_color_list(self):
        self.color_dropdown.configure(values=[c['name'] for c in self.saved_colors])
        if self.saved_colors:
            self.color_dropdown.set(self.saved_colors[0]['name'])
            self.select_dropdown_color(self.saved_colors[0]['name'])

    def select_dropdown_color(self, selected_name):
        for c in self.saved_colors:
            if c['name'] == selected_name:
                self.set_active_color(c['name'], c['hex'])
                break

    def set_active_color(self, name, hex_val):
        self.active_shirt_hex = hex_val
        self.active_color_label.configure(text=f"Selected Shirt: {name} ({hex_val})", text_color="#00a8ff")

    def open_color_picker(self):
        ColorPickerWindow(self)

    def process_and_save(self):
        if not self.input_image_path:
            messagebox.showerror("Error", "Please select an input image first.")
            return
        if not self.active_shirt_hex:
            messagebox.showerror("Error", "Please select a shirt color.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=f"shifted_{os.path.basename(self.input_image_path)}",
            filetypes=[("PNG files", "*.png")]
        )
        
        if save_path:
            alpha = self.alpha_slider.get()
            try:
                shift_image(self.input_image_path, save_path, self.active_shirt_hex, alpha)
                messagebox.showinfo("Success", f"Image saved successfully to:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Processing Error", f"An error occurred:\n{str(e)}")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = Margot()
    app.mainloop()