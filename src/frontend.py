import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from PIL import Image, ImageTk, ImageOps
import os
import sqlite3
from backend import Backend, SelleProperties
from typing import Dict, Tuple, Set, Optional, List
from functools import lru_cache
from threading import Timer

class DentalAppLower:
    def __init__(self, root):
        self.root = root
        self.root.title("Conception d'Arcades Dentaires - PFE")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        self.image_folder = os.path.abspath(r"C:\Projets\PPA_Conception\data\images")
        self.json_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elements_valides")
        os.makedirs(self.json_dir, exist_ok=True)

        self.backend = Backend(self.image_folder, self.json_dir)

        self.current_modele = tk.StringVar(value=self._load_last_modele())
        self.backend.set_current_model(self.current_modele.get())

        self.selle_tk_images: Dict[str, ImageTk.PhotoImage] = {}
        self.selle_canvas_ids: Dict[str, int] = {}
        self.active_selle: Optional[str] = None
        self.drag_offset: Optional[Tuple[float, float]] = None

        self.dent_size = 60
        self.teeth_images: Dict[str, ImageTk.PhotoImage] = {}
        self.teeth_objects: Dict[str, int] = {}
        self.selected_teeth: Set[str] = set()

        self._setup_ui()
        self._bind_shortcuts()

    def _load_last_modele(self) -> str:
        try:
            with open(os.path.join(self.json_dir, 'last_modele.dat'), 'r') as f:
                last = f.read().strip()
                return last if last in self.backend.models else 'arcade_inf'
        except Exception:
            return 'arcade_inf'

    def _save_current_modele(self):
        with open(os.path.join(self.json_dir, 'last_modele.dat'), 'w') as f:
            f.write(self.current_modele.get())

    def _setup_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.controls_frame = tk.LabelFrame(self.main_frame, text="Contrôles", padx=10, pady=10)
        self.controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._setup_modele_selector()
        self._setup_canvas()
        self._load_background()
        self._load_teeth_images()
        self._create_teeth_buttons()
        self._display_all_teeth()
        self._setup_selle_controls()
        self._setup_transformation_controls()
        self._setup_menu()

    def _bind_shortcuts(self):
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-s>", lambda e: self.save_selle())

    def _setup_modele_selector(self):
        modele_frame = tk.LabelFrame(self.controls_frame, text="Type d'Arcade", padx=5, pady=5)
        modele_frame.pack(fill=tk.X, pady=10)
        tk.OptionMenu(modele_frame, self.current_modele, *self.backend.models.keys(),
                      command=self._on_modele_change).pack(fill=tk.X)

    def _setup_canvas(self):
        self.canvas_width = 800
        self.canvas_height = 600
        self.canvas = tk.Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height,
                                bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _on_canvas_resize(self, event):
        if event.width < 100 or event.height < 100:
            return
        self.canvas_width = event.width
        self.canvas_height = event.height
        self._load_background()
        for filename in self.selle_canvas_ids:
            self._refresh_selle(filename)

    @lru_cache(maxsize=64)
    def _load_image_cached(self, path: str, size: Tuple[int, int]) -> Optional[Image.Image]:
        try:
            with Image.open(path) as img:
                return img.resize(size, Image.Resampling.LANCZOS)
        except Exception:
            return None

    def _load_teeth_images(self):
        self.teeth_images.clear()
        for filename in self.backend.get_teeth_positions().keys():
            path = os.path.join(self.image_folder, "dents", filename)
            img = self._load_image_cached(path, (self.dent_size, self.dent_size))
            if img is None:
                img = Image.new('RGBA', (self.dent_size, self.dent_size), (255, 0, 0, 128))
            self.teeth_images[filename] = ImageTk.PhotoImage(img)

    def _create_teeth_buttons(self):
        teeth_frame = tk.LabelFrame(self.controls_frame, text="Contrôle des Dents", padx=5, pady=5)
        teeth_frame.pack(fill=tk.X, pady=5)

        buttons_frame = tk.Frame(teeth_frame)
        buttons_frame.pack()
        for filename in sorted(self.backend.get_teeth_positions().keys(), key=lambda x: x.split('_')[1]):
            num = filename.split('.')[0].split('_')[1]
            if num not in ['18', '28', '38', '48']:
                btn = tk.Button(buttons_frame, text=num, width=4, bg="green", fg="white",
                                command=lambda f=filename: self._toggle_tooth(f))
                btn.pack(side=tk.LEFT, padx=2)

        global_frame = tk.Frame(teeth_frame)
        global_frame.pack(pady=5)
        tk.Button(global_frame, text="Tout Afficher", command=self._display_all_teeth).pack(side=tk.LEFT, padx=2)
        tk.Button(global_frame, text="Tout Masquer", command=self._hide_all_teeth).pack(side=tk.LEFT, padx=2)
        tk.Button(global_frame, text="Afficher Positions", command=self._show_teeth_positions).pack(side=tk.LEFT, padx=2)

    def _show_teeth_positions(self):
        positions = []
        for filename in self.teeth_objects:
            x, y = self.canvas.coords(self.teeth_objects[filename])
            positions.append(f"{filename}: ({x:.1f}, {y:.1f})")
        if positions:
            messagebox.showinfo("Positions des Dents", "\n".join(positions))
        else:
            messagebox.showwarning("Aucune Dent Visible", "Aucune dent n'est actuellement affichée.")

    def _toggle_tooth(self, filename: str):
        if filename in self.teeth_objects:
            self._hide_tooth(filename)
        else:
            self._display_tooth(filename)

    def _adjust_teeth_positions(self, x: float, y: float) -> Tuple[float, float]:
        scaled_x = x * self.bg_scale_factor
        scaled_y = y * self.bg_scale_factor
        offset_x = (self.canvas_width - self.bg_width) // 2
        offset_y = (self.canvas_height - self.bg_height) // 2
        return offset_x + scaled_x, offset_y + scaled_y

    def _display_tooth(self, filename: str):
        if filename in self.teeth_objects:
            return
        positions = self.backend.get_teeth_positions()
        if filename not in positions:
            x, y = self.canvas_width // 2, self.canvas_height // 2
            scale, rotation = 1.0, 0.0
        else:
            x, y, scale, rotation = positions[filename]

        if hasattr(self, 'bg_scale_factor'):
            x, y = self._adjust_teeth_positions(x, y)

        img = Image.open(os.path.join(self.image_folder, "dents", filename)).convert("RGBA")
        img = img.resize((int(self.dent_size * scale), int(self.dent_size * scale)), Image.Resampling.LANCZOS)
        img = img.rotate(rotation, expand=True, resample=Image.BICUBIC)
        self.teeth_images[filename] = ImageTk.PhotoImage(img)

        img_id = self.canvas.create_image(x, y, image=self.teeth_images[filename], tags=("tooth", filename), anchor=tk.CENTER)
        self.teeth_objects[filename] = img_id

    def _update_teeth_positions(self):
        for filename in list(self.teeth_objects.keys()):
            self._hide_tooth(filename)
            self._display_tooth(filename)

    def _hide_tooth(self, filename: str):
        if filename in self.teeth_objects:
            self.canvas.delete(self.teeth_objects[filename])
            del self.teeth_objects[filename]
            self.selected_teeth.discard(filename)

    def _display_all_teeth(self):
        for filename in self.backend.get_teeth_positions().keys():
            self._display_tooth(filename)

    def _hide_all_teeth(self):
        for filename in list(self.teeth_objects.keys()):
            self._hide_tooth(filename)

    def _setup_selle_controls(self):
        selle_frame = tk.LabelFrame(self.controls_frame, text="Gestion des Selles", padx=5, pady=5)
        selle_frame.pack(fill=tk.X, pady=10)

        self.selle_files = self._get_selle_files()
        self.selected_selle = tk.StringVar(value=self.selle_files[0] if self.selle_files else "")
        tk.Label(selle_frame, text="Sélectionner une selle :").pack(anchor=tk.W)
        self.selle_menu = tk.OptionMenu(selle_frame, self.selected_selle, *self.selle_files, command=self.load_selle)
        self.selle_menu.pack(fill=tk.X)

        manage_frame = tk.Frame(selle_frame)
        manage_frame.pack(fill=tk.X, pady=5)
        tk.Button(manage_frame, text="Importer", command=self._import_selle).pack(side=tk.LEFT, padx=2)
        tk.Button(manage_frame, text="Renommer", command=self._rename_selle).pack(side=tk.LEFT, padx=2)
        tk.Button(manage_frame, text="Supprimer", command=self._delete_selle).pack(side=tk.LEFT, padx=2)
        tk.Button(manage_frame, text="Effacer les Selles", command=self._clear_selle).pack(side=tk.LEFT, padx=2)
        tk.Button(manage_frame, text="Afficher Toutes les Selles", command=self._show_all_selles).pack(side=tk.LEFT, padx=2)

    def _get_selle_files(self) -> List[str]:
        folder = os.path.join(self.image_folder, self.backend.current_model['folder'])
        try:
            files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            return sorted(files) if files else ["(aucune selle)"]
        except Exception:
            return ["(aucune selle)"]

    def _import_selle(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if file_path:
            dest_path = os.path.join(self.image_folder, self.backend.current_model['folder'], os.path.basename(file_path))
            os.copy(file_path, dest_path)
            self._update_selle_menu(os.path.basename(file_path))
            messagebox.showinfo("Succès", f"Selle importée : {os.path.basename(file_path)}")

    def _rename_selle(self):
        current_selle = self.selected_selle.get()
        if not current_selle or current_selle == "(aucune selle)":
            messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
            return
        new_name = simpledialog.askstring("Renommer", "Nouveau nom pour la selle :", initialvalue=current_selle)
        if new_name and new_name != current_selle:
            old_path = os.path.join(self.image_folder, self.backend.current_model['folder'], current_selle)
            new_path = os.path.join(self.image_folder, self.backend.current_model['folder'], new_name)
            os.rename(old_path, new_path)
            self._update_selle_after_rename(current_selle, new_name)
            messagebox.showinfo("Succès", f"Selle renommée en {new_name}")

    def _update_selle_after_rename(self, old_name: str, new_name: str):
        if old_name in self.selle_canvas_ids:
            self.selle_tk_images[new_name] = self.selle_tk_images.pop(old_name)
            self.selle_canvas_ids[new_name] = self.selle_canvas_ids.pop(old_name)
            self.canvas.itemconfig(self.selle_canvas_ids[new_name], tags=("selle", new_name))
            if old_name in self.backend.selles_props:
                self.backend.selles_props[new_name] = self.backend.selles_props.pop(old_name)
                self.backend.selles_props[new_name].image = new_name
            if self.active_selle == old_name:
                self.active_selle = new_name
        self._update_selle_menu(new_name)

    def _update_selle_menu(self, selected: str):
        self.selle_files = self._get_selle_files()
        self.selle_menu["menu"].delete(0, "end")
        for f in self.selle_files:
            self.selle_menu["menu"].add_command(label=f, command=tk._setit(self.selected_selle, f))
        self.selected_selle.set(selected)

    def _delete_selle(self):
        current_selle = self.selected_selle.get()
        if not current_selle or current_selle == "(aucune selle)":
            messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
            return
        if messagebox.askyesno("Confirmer", f"Voulez-vous vraiment supprimer {current_selle} ?"):
            path = os.path.join(self.image_folder, self.backend.current_model['folder'], current_selle)
            os.remove(path)
            self._remove_selle_from_canvas(current_selle)
            self._update_selle_menu(self.selle_files[0] if self.selle_files else "")
            messagebox.showinfo("Succès", f"Selle {current_selle} supprimée.")

    def _remove_selle_from_canvas(self, selle: str):
        if selle in self.selle_canvas_ids:
            self.canvas.delete(self.selle_canvas_ids[selle])
            del self.selle_canvas_ids[selle]
            del self.selle_tk_images[selle]
            if selle in self.backend.selles_props:
                del self.backend.selles_props[selle]
            if self.active_selle == selle:
                self.active_selle = None

    def load_selle(self, filename: Optional[str] = None):
        filename = filename or self.selected_selle.get()
        if not filename or filename == "(aucune selle)":
            messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
            return
        props = self.backend.load_selle_properties(filename)
        self._refresh_selle(filename)
        self._select_selle(filename)

    def _refresh_selle(self, filename: str):
        props = self.backend.selles_props[filename]
        img = self._load_transformed_image(props)
        self.selle_tk_images[filename] = ImageTk.PhotoImage(img)
        if filename in self.selle_canvas_ids:
            self.canvas.delete(self.selle_canvas_ids[filename])
        self.selle_canvas_ids[filename] = self.canvas.create_image(
            props.x, props.y, image=self.selle_tk_images[filename], tags=("selle", filename), anchor=tk.CENTER
        )
        self._bind_selle_events(filename)

    def _load_transformed_image(self, props: SelleProperties) -> Image.Image:
        path = os.path.join(self.image_folder, self.backend.current_model['folder'], props.image)
        with Image.open(path) as img:
            img = img.convert("RGBA")
            if props.flip_x:
                img = ImageOps.mirror(img)
            if props.flip_y:
                img = ImageOps.flip(img)
            w, h = img.size
            img = img.resize((int(w * props.scale), int(h * props.scale)), Image.Resampling.LANCZOS)
            img = img.rotate(props.angle, expand=True, resample=Image.BICUBIC)
            return img

    def _select_selle(self, filename: str):
        if filename in self.backend.selles_props:
            self.active_selle = filename
            props = self.backend.selles_props[filename]
            for fname in self.selle_canvas_ids:
                if fname != filename:
                    self.canvas.tag_lower(self.selle_canvas_ids[fname])
            self.canvas.tag_raise(self.selle_canvas_ids[filename])
            self.rotation_slider.set(props.angle)
            self.scale_slider.set(props.scale)
            self.selle_x_var.set(props.x)
            self.selle_y_var.set(props.y)

    def _clear_selle(self):
        for filename in list(self.selle_canvas_ids.keys()):
            self._remove_selle_from_canvas(filename)
        self.backend.save_state()

    def _bind_selle_events(self, filename: str):
        canvas_id = self.selle_canvas_ids[filename]
        self.canvas.tag_bind(canvas_id, "<Button-1>", lambda e, fname=filename: self._start_drag(e, fname))
        self.canvas.tag_bind(canvas_id, "<B1-Motion>", self._do_drag)
        self.canvas.tag_bind(canvas_id, "<ButtonRelease-1>", self._stop_drag)

    def _setup_transformation_controls(self):
        transform_frame = tk.LabelFrame(self.controls_frame, text="Transformations", padx=5, pady=5)
        transform_frame.pack(fill=tk.X, pady=10)

        tk.Button(transform_frame, text="💾 Enregistrer Configuration", command=self.save_selle, bg="#4CAF50", fg="white",
                  font=("Arial", 12, "bold"), pady=8).pack(fill=tk.X, pady=(0, 10), padx=5)

        self._setup_selle_sliders(transform_frame)
        self._setup_flip_buttons(transform_frame)
        self._setup_undo_redo_buttons(transform_frame)
        tk.Button(transform_frame, text="Exporter en PNG", command=self._export_canvas, bg="#2196F3", fg="white").pack(fill=tk.X, pady=5, padx=5)

    def _setup_selle_sliders(self, parent):
        selle_frame = tk.Frame(parent)
        selle_frame.pack(fill=tk.X, pady=5)

        self.selle_x_var = tk.DoubleVar(value=0)
        self.selle_x_slider = tk.Scale(selle_frame, from_=-200, to=800, orient=tk.HORIZONTAL, variable=self.selle_x_var,
                                       command=lambda _: self._move_selle())
        tk.Label(selle_frame, text="Décalage X (Selle) :").pack(side=tk.LEFT, padx=5)
        self.selle_x_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        self.selle_y_var = tk.DoubleVar(value=0)
        self.selle_y_slider = tk.Scale(selle_frame, from_=-200, to=600, orient=tk.HORIZONTAL, variable=self.selle_y_var,
                                       command=lambda _: self._move_selle())
        tk.Label(selle_frame, text="Décalage Y (Selle) :").pack(side=tk.LEFT, padx=5)
        self.selle_y_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        self.rotation_slider = tk.Scale(selle_frame, from_=0, to=360, orient=tk.HORIZONTAL,
                                        command=lambda _: self._apply_transform())
        tk.Label(selle_frame, text="Rotation (°) :").pack(side=tk.LEFT, padx=5)
        self.rotation_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        self.scale_slider = tk.Scale(selle_frame, from_=0.2, to=3.0, resolution=0.1, orient=tk.HORIZONTAL,
                                     command=lambda _: self._apply_transform())
        self.scale_slider.set(1.0)
        tk.Label(selle_frame, text="Échelle :").pack(side=tk.LEFT, padx=5)
        self.scale_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

    def _setup_flip_buttons(self, parent):
        flip_frame = tk.Frame(parent)
        flip_frame.pack(fill=tk.X, pady=5)
        tk.Button(flip_frame, text="Retourner Horizontalement", command=self._flip_x).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(flip_frame, text="Retourner Verticalement", command=self._flip_y).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def _setup_undo_redo_buttons(self, parent):
        undo_frame = tk.Frame(parent)
        undo_frame.pack(fill=tk.X, pady=5)
        tk.Button(undo_frame, text="↩ Annuler (Ctrl+Z)", command=self.undo).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(undo_frame, text="↪ Rétablir (Ctrl+Y)", command=self.redo).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def _apply_transform(self):
        if self.active_selle:
            self.backend.update_selle_angle(self.active_selle, self.rotation_slider.get())
            self.backend.update_selle_scale(self.active_selle, self.scale_slider.get())
            self._refresh_selle(self.active_selle)
            self.backend.save_state()
            self.backend.save_selle_properties(self.active_selle)

    def _flip_x(self):
        if self.active_selle:
            self.backend.flip_selle_x(self.active_selle)
            self._refresh_selle(self.active_selle)
            self.backend.save_state()
            self.backend.save_selle_properties(self.active_selle)

    def _flip_y(self):
        if self.active_selle:
            self.backend.flip_selle_y(self.active_selle)
            self._refresh_selle(self.active_selle)
            self.backend.save_state()
            self.backend.save_selle_properties(self.active_selle)

    def _start_drag(self, event, filename: str):
        self.active_selle = filename
        props = self.backend.selles_props[filename]
        self.drag_offset = (event.x - props.x, event.y - props.y)
        self._select_selle(filename)

    def _do_drag(self, event):
        if self.drag_offset and self.active_selle:
            new_x = max(50, min(self.canvas_width - 50, event.x - self.drag_offset[0]))
            new_y = max(50, min(self.canvas_height - 50, event.y - self.drag_offset[1]))
            self.backend.update_selle_position(self.active_selle, new_x, new_y)
            self.canvas.coords(self.selle_canvas_ids[self.active_selle], new_x, new_y)

    def _stop_drag(self, event):
        self.drag_offset = None
        self.backend.save_state()
        self.backend.save_selle_properties(self.active_selle)

    def _move_selle(self):
        if self.active_selle:
            self.backend.update_selle_position(self.active_selle, self.selle_x_var.get(), self.selle_y_var.get())
            self._refresh_selle(self.active_selle)
            self.backend.save_state()
            self.backend.save_selle_properties(self.active_selle)

    def undo(self):
        if self.backend.undo():
            for filename in self.backend.get_selles_props():
                if filename in self.selle_canvas_ids:
                    self._refresh_selle(filename)
            if self.active_selle:
                self._select_selle(self.active_selle)

    def redo(self):
        if self.backend.redo():
            for filename in self.backend.get_selles_props():
                if filename in self.selle_canvas_ids:
                    self._refresh_selle(filename)
            if self.active_selle:
                self._select_selle(self.active_selle)

    def save_selle(self, auto_save=False):
        if not self.backend.get_selles_props():
            if not auto_save:
                messagebox.showwarning("Avertissement", "Aucune selle à enregistrer.")
            return
        name = "selles_config" if auto_save else simpledialog.askstring("Nom de la Configuration", "Entrez un nom pour cette configuration :", initialvalue="selles_config")
        if name:
            if not auto_save:
                messagebox.showinfo("Succès", f"Configuration '{name}' enregistrée dans la base de données.")

    def _export_canvas(self):
        img = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        bg_path = os.path.join(self.image_folder, "fonds", self.backend.current_model['background'])
        with Image.open(bg_path) as bg_img:
            img.paste(bg_img.resize((self.canvas_width, self.canvas_height), Image.Resampling.LANCZOS))
        for tooth, obj_id in self.teeth_objects.items():
            x, y = self.canvas.coords(obj_id)
            tooth_img = self.teeth_images[tooth]
            img.paste(tooth_img, (int(x - tooth_img.width() // 2), int(y - tooth_img.height() // 2)), tooth_img)
        for filename in self.selle_canvas_ids:
            props = self.backend.selles_props[filename]
            selle_img = self.selle_tk_images[filename]
            img.paste(selle_img, (int(props.x - selle_img.width() // 2), int(props.y - selle_img.height() // 2)), selle_img)
        output_path = os.path.join(self.json_dir, f"design_{self.current_modele.get()}_{self.active_selle or 'sans_nom'}.png")
        img.save(output_path)
        messagebox.showinfo("Succès", f"Design exporté vers {output_path}")

    def _load_background(self):
        bg_path = os.path.join(self.image_folder, "fonds", self.backend.current_model['background'])
        with Image.open(bg_path) as img:
            self._resize_background(img)
            self.bg_photo = ImageTk.PhotoImage(img.resize((self.bg_width, self.bg_height), Image.Resampling.LANCZOS))
            if hasattr(self, 'bg_id'):
                self.canvas.delete(self.bg_id)
            self.bg_id = self.canvas.create_image(self.canvas_width // 2, self.canvas_height // 2,
                                                  image=self.bg_photo, anchor=tk.CENTER)
            self.canvas.lower(self.bg_id)
            self._update_teeth_positions()

    def _resize_background(self, img: Image.Image):
        self.original_bg_width = img.width
        self.original_bg_height = img.height
        max_width = 700
        img_ratio = img.width / img.height
        new_width = min(img.width, max_width)
        new_height = int(new_width / img_ratio)
        if new_height > self.canvas_height:
            new_height = self.canvas_height
            new_width = int(new_height * img_ratio)
        self.bg_scale_factor = new_width / self.original_bg_width
        self.bg_width = new_width
        self.bg_height = new_height

    def _on_modele_change(self, *_):
        if hasattr(self, '_modele_timer'):
            self._modele_timer.cancel()
        self._modele_timer = Timer(0.2, self._apply_modele_change)
        self._modele_timer.start()

    def _apply_modele_change(self):
        self._save_current_modele()
        self._clear_selle()
        self._hide_all_teeth()
        self.backend.set_current_model(self.current_modele.get())
        self._load_background()
        self._load_teeth_images()
        for child in self.controls_frame.winfo_children():
            if isinstance(child, tk.LabelFrame) and "Contrôle des Dents" in child.cget("text"):
                child.destroy()
        self._create_teeth_buttons()
        self._update_selle_menu(self.selle_files[0] if self.selle_files else "")
        self._display_all_teeth()

    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Actualiser", command=self._refresh)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Guide de l'Utilisateur", command=self._show_help)
        help_menu.add_command(label="À Propos", command=self._show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)
        self.root.config(menu=menubar)

    def _refresh(self):
        self._on_modele_change()

    def _show_help(self):
        messagebox.showinfo("Guide de l'Utilisateur", "Guide de l'Utilisateur :\n\n1. Sélectionnez un type d'arcade\n2. Choisissez une selle dans la liste\n3. Ajustez la rotation/échelle/position avec les curseurs\n4. Enregistrez vos configurations\n\nRaccourcis :\nCtrl+Z : Annuler\nCtrl+Y : Rétablir\nCtrl+S : Enregistrer")

    def _show_about(self):
        messagebox.showinfo("À Propos", "Logiciel de Conception d'Arcades Dentaires\nVersion 2.0\n\nProjet de Fin d'Études\nAuteur : Amine\nAnnée : 2023\n\nTechnologies :\n- Python 3\n- Tkinter (Interface Utilisateur)\n- Pillow (Traitement d'Images)")

    def _show_all_selles(self):
        self._clear_selle()
        for filename in self.selle_files:
            if filename != "(aucune selle)":
                self.backend.load_selle_properties(filename)
                self._refresh_selle(filename)
        messagebox.showinfo("Info", "Toutes les selles ont été chargées avec leurs propriétés sauvegardées si disponibles.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DentalAppLower(root)
    root.mainloop()