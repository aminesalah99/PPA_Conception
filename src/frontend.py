import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from PIL import Image, ImageTk, ImageOps
import os
from backend import Backend, SelleProperties
from typing import Dict, Tuple, Set, Optional
from functools import lru_cache
from threading import Timer

class DentalAppLower:
    """Classe principale pour la conception des arcades dentaires."""
    def __init__(self, root):
        self.root = root
        self.root.title("Conception d'Arcades Dentaires - PFE")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        self.image_folder = os.path.abspath(r"C:\Projets\PPA_Conception\data\images")
        self.json_dir = os.path.abspath("elements_valides")
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
        self.teeth_offset_x = tk.DoubleVar(value=0.0)
        self.teeth_offset_y = tk.DoubleVar(value=0.0)

        self._setup_ui()
        self._bind_shortcuts()

    def _load_last_modele(self) -> str:
        """Charge le dernier modèle utilisé depuis un fichier."""
        try:
            with open('last_modele.dat', 'r') as f:
                last = f.read().strip()
                return last if last in self.backend.models else 'arcade_inf'
        except Exception:
            return 'arcade_inf'

    def _save_current_modele(self):
        """Enregistre le modèle actuel dans un fichier."""
        with open('last_modele.dat', 'w') as f:
            f.write(self.current_modele.get())

    def _setup_ui(self):
        """Configure l'interface utilisateur principale."""
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
        """Lie les raccourcis clavier."""
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-s>", lambda e: self.save_selle())

    def _setup_modele_selector(self):
        """Configure le sélecteur de modèle d'arcade."""
        modele_frame = tk.LabelFrame(self.controls_frame, text="Type d'Arcade", padx=5, pady=5)
        modele_frame.pack(fill=tk.X, pady=10)
        tk.OptionMenu(modele_frame, self.current_modele, *self.backend.models.keys(),
                      command=self._on_modele_change).pack(fill=tk.X)

    def _setup_canvas(self):
        """Configure le canevas principal."""
        self.canvas_width = 800
        self.canvas_height = 600
        self.canvas = tk.Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height,
                                bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _on_canvas_resize(self, event):
        """Gère le redimensionnement du canevas."""
        if event.width < 100 or event.height < 100:
            return
        self.canvas_width = event.width
        self.canvas_height = event.height
        self._load_background()
        for filename in self.selle_canvas_ids:
            self._refresh_selle(filename)

    @lru_cache(maxsize=64)
    def _load_image_cached(self, path: str, size: Tuple[int, int]) -> Optional[Image.Image]:
        """Charge une image avec mise en cache."""
        try:
            with Image.open(path) as img:
                return img.resize(size, Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Erreur lors du chargement de l'image {path} : {e}")
            return None

    def _load_teeth_images(self):
        """Charge les images des dents pour le modèle actuel."""
        self.teeth_images.clear()
        for filename in self.backend.current_model['teeth'].keys():
            path = os.path.join(self.image_folder, filename)
            img = self._load_image_cached(path, (self.dent_size, self.dent_size))
            self.teeth_images[filename] = ImageTk.PhotoImage(img or Image.new('RGBA', (self.dent_size, self.dent_size), (255, 0, 0, 128)))

    def _create_teeth_buttons(self):
        """Crée les boutons pour contrôler l'affichage des dents."""
        teeth_frame = tk.LabelFrame(self.controls_frame, text="Contrôle des Dents", padx=5, pady=5)
        teeth_frame.pack(fill=tk.X, pady=5)

        buttons_frame = tk.Frame(teeth_frame)
        buttons_frame.pack()
        for filename in sorted(self.backend.current_model['teeth'].keys(), key=lambda x: x.split('_')[1]):
            num = filename.split('.')[0].split('_')[1]
            btn = tk.Button(buttons_frame, text=num, width=4, bg="green", fg="white",
                            command=lambda f=filename: self._toggle_tooth(f))
            btn.pack(side=tk.LEFT, padx=2)
            self._create_tooltip(btn, f"Afficher/Masquer la dent {num}")

        global_frame = tk.Frame(teeth_frame)
        global_frame.pack(pady=5)
        tk.Button(global_frame, text="Tout Afficher", command=self._display_all_teeth).pack(side=tk.LEFT, padx=2)
        tk.Button(global_frame, text="Tout Masquer", command=self._hide_all_teeth).pack(side=tk.LEFT, padx=2)

    def _toggle_tooth(self, filename: str):
        """Bascule l'affichage d'une dent."""
        if filename in self.teeth_objects:
            self._hide_tooth(filename)
        else:
            self._display_tooth(filename)

    def _adjust_teeth_positions(self, x: float, y: float) -> Tuple[float, float]:
        """Ajuste les positions des dents en fonction de l'arrière-plan et des décalages."""
        scaled_x = x * self.bg_scale_factor
        scaled_y = y * self.bg_scale_factor
        offset_x = (self.canvas_width - self.bg_width) // 2
        offset_y = (self.canvas_height - self.bg_height) // 2
        return offset_x + scaled_x + self.teeth_offset_x.get(), offset_y + scaled_y + self.teeth_offset_y.get()

    def _display_tooth(self, filename: str):
        """Affiche une dent sur le canevas."""
        if filename in self.teeth_objects:
            return
        x, y = self.backend.get_teeth_positions().get(filename, (self.canvas_width // 2, self.canvas_height // 2))
        if hasattr(self, 'bg_scale_factor'):
            x, y = self._adjust_teeth_positions(x, y)
        img_id = self.canvas.create_image(x, y, image=self.teeth_images[filename], tags=("tooth", filename), anchor=tk.CENTER)
        self.teeth_objects[filename] = img_id

    def _update_teeth_positions(self):
        """Met à jour les positions de toutes les dents affichées."""
        for filename in list(self.teeth_objects.keys()):
            self._hide_tooth(filename)
            self._display_tooth(filename)

    def _hide_tooth(self, filename: str):
        """Masque une dent du canevas."""
        if filename in self.teeth_objects:
            self.canvas.delete(self.teeth_objects[filename])
            del self.teeth_objects[filename]
            self.selected_teeth.discard(filename)

    def _display_all_teeth(self):
        """Affiche toutes les dents pour le modèle actuel."""
        for filename in self.backend.current_model['teeth'].keys():
            self._display_tooth(filename)

    def _hide_all_teeth(self):
        """Masque toutes les dents affichées."""
        for filename in list(self.teeth_objects.keys()):
            self._hide_tooth(filename)

    def _setup_selle_controls(self):
        """Configure les contrôles pour gérer les selles."""
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
        """Obtient la liste des fichiers de selles pour le modèle actuel."""
        folder = os.path.join(self.image_folder, self.backend.current_model['folder'])
        try:
            files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            return sorted(files) if files else ["(aucune selle)"]
        except Exception:
            return ["(aucune selle)"]

    def _import_selle(self):
        """Importe une nouvelle selle dans le dossier du modèle actuel."""
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if file_path:
            dest_path = os.path.join(self.image_folder, self.backend.current_model['folder'], os.path.basename(file_path))
            os.copy(file_path, dest_path)
            self._update_selle_menu(os.path.basename(file_path))
            messagebox.showinfo("Succès", f"Selle importée : {os.path.basename(file_path)}")

    def _rename_selle(self):
        """Renomme la selle sélectionnée."""
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
        """Met à jour l'état interne après le renommage d'une selle."""
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
        """Met à jour le menu déroulant des selles."""
        self.selle_files = self._get_selle_files()
        self.selle_menu["menu"].delete(0, "end")
        for f in self.selle_files:
            self.selle_menu["menu"].add_command(label=f, command=tk._setit(self.selected_selle, f))
        self.selected_selle.set(selected)

    def _delete_selle(self):
        """Supprime la selle sélectionnée du dossier et du canevas."""
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
        """Supprime une selle du canevas et de l'état interne."""
        if selle in self.selle_canvas_ids:
            self.canvas.delete(self.selle_canvas_ids[selle])
            del self.selle_canvas_ids[selle]
            del self.selle_tk_images[selle]
            if selle in self.backend.selles_props:
                del self.backend.selles_props[selle]
            if self.active_selle == selle:
                self.active_selle = None

    def load_selle(self, filename: Optional[str] = None):
        """Charge et sélectionne une selle."""
        filename = filename or self.selected_selle.get()
        if not filename or filename == "(aucune selle)":
            messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
            return
        props = self.backend.load_selle_properties(filename)
        self._refresh_selle(filename)
        self._select_selle(filename)

    def _refresh_selle(self, filename: str):
        """Met à jour l'affichage d'une selle sur le canevas."""
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
        """Charge et applique les transformations à l'image de la selle."""
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
        """Sélectionne une selle et met à jour l'interface utilisateur."""
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
        """Efface toutes les selles du canevas."""
        for filename in list(self.selle_canvas_ids.keys()):
            self._remove_selle_from_canvas(filename)
        self.backend.save_state()

    def _bind_selle_events(self, filename: str):
        """Lie les événements de la souris à une selle."""
        canvas_id = self.selle_canvas_ids[filename]
        self.canvas.tag_bind(canvas_id, "<Button-1>", lambda e, fname=filename: self._start_drag(e, fname))
        self.canvas.tag_bind(canvas_id, "<B1-Motion>", self._do_drag)
        self.canvas.tag_bind(canvas_id, "<ButtonRelease-1>", self._stop_drag)

    def _setup_transformation_controls(self):
        """Configure les contrôles de transformation pour les selles et les dents."""
        transform_frame = tk.LabelFrame(self.controls_frame, text="Transformations", padx=5, pady=5)
        transform_frame.pack(fill=tk.X, pady=10)

        tk.Button(transform_frame, text="💾 Enregistrer Configuration", command=self.save_selle, bg="#4CAF50", fg="white",
                  font=("Arial", 12, "bold"), pady=8).pack(fill=tk.X, pady=(0, 10), padx=5)

        self._setup_teeth_sliders(transform_frame)
        self._setup_selle_sliders(transform_frame)
        self._setup_flip_buttons(transform_frame)
        self._setup_undo_redo_buttons(transform_frame)
        tk.Button(transform_frame, text="Exporter en PNG", command=self._export_canvas, bg="#2196F3", fg="white").pack(fill=tk.X, pady=5, padx=5)

    def _setup_teeth_sliders(self, parent):
        """Configure les curseurs pour les ajustements de décalage des dents."""
        teeth_frame = tk.Frame(parent)
        teeth_frame.pack(fill=tk.X, pady=5)
        self.teeth_x_slider = tk.Scale(teeth_frame, from_=-200, to=200, orient=tk.HORIZONTAL, variable=self.teeth_offset_x,
                                       command=lambda _: self._update_teeth_positions())
        tk.Label(teeth_frame, text="Décalage X (Dents) :").pack(side=tk.LEFT, padx=5)
        self.teeth_x_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        self.teeth_y_slider = tk.Scale(teeth_frame, from_=-200, to=200, orient=tk.HORIZONTAL, variable=self.teeth_offset_y,
                                       command=lambda _: self._update_teeth_positions())
        tk.Label(teeth_frame, text="Décalage Y (Dents) :").pack(side=tk.LEFT, padx=5)
        self.teeth_y_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

    def _setup_selle_sliders(self, parent):
        """Configure les curseurs pour les transformations des selles."""
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
        """Configure les boutons de retournement pour les selles."""
        flip_frame = tk.Frame(parent)
        flip_frame.pack(fill=tk.X, pady=5)
        tk.Button(flip_frame, text="Retourner Horizontalement", command=self._flip_x).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(flip_frame, text="Retourner Verticalement", command=self._flip_y).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def _setup_undo_redo_buttons(self, parent):
        """Configure les boutons d'annulation et de rétablissement."""
        undo_frame = tk.Frame(parent)
        undo_frame.pack(fill=tk.X, pady=5)
        tk.Button(undo_frame, text="↩ Annuler (Ctrl+Z)", command=self.undo).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(undo_frame, text="↪ Rétablir (Ctrl+Y)", command=self.redo).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def _apply_transform(self):
        """Applique les transformations à la selle active."""
        if self.active_selle:
            self.backend.update_selle_angle(self.active_selle, self.rotation_slider.get())
            self.backend.update_selle_scale(self.active_selle, self.scale_slider.get())
            self._refresh_selle(self.active_selle)
            self.backend.save_state()
            self.backend.save_selle_properties(self.active_selle)

    def _flip_x(self):
        """Retourne la selle active horizontalement."""
        if self.active_selle:
            self.backend.flip_selle_x(self.active_selle)
            self._refresh_selle(self.active_selle)
            self.backend.save_state()
            self.backend.save_selle_properties(self.active_selle)

    def _flip_y(self):
        """Retourne la selle active verticalement."""
        if self.active_selle:
            self.backend.flip_selle_y(self.active_selle)
            self._refresh_selle(self.active_selle)
            self.backend.save_state()
            self.backend.save_selle_properties(self.active_selle)

    def _start_drag(self, event, filename: str):
        """Commence le déplacement d'une selle."""
        self.active_selle = filename
        props = self.backend.selles_props[filename]
        self.drag_offset = (event.x - props.x, event.y - props.y)
        self._select_selle(filename)

    def _do_drag(self, event):
        """Déplace la selle active."""
        if self.drag_offset and self.active_selle:
            new_x = max(50, min(self.canvas_width - 50, event.x - self.drag_offset[0]))
            new_y = max(50, min(self.canvas_height - 50, event.y - self.drag_offset[1]))
            self.backend.update_selle_position(self.active_selle, new_x, new_y)
            self.canvas.coords(self.selle_canvas_ids[self.active_selle], new_x, new_y)

    def _stop_drag(self, event):
        """Arrête le déplacement et enregistre l'état."""
        self.drag_offset = None
        self.backend.save_state()
        self.backend.save_selle_properties(self.active_selle)

    def _move_selle(self):
        """Déplace la selle active à l'aide des curseurs."""
        if self.active_selle:
            self.backend.update_selle_position(self.active_selle, self.selle_x_var.get(), self.selle_y_var.get())
            self._refresh_selle(self.active_selle)
            self.backend.save_state()
            self.backend.save_selle_properties(self.active_selle)

    def undo(self):
        """Annule la dernière action sur les selles."""
        if self.backend.undo():
            for filename in self.backend.get_selles_props():
                if filename in self.selle_canvas_ids:
                    self._refresh_selle(filename)
            if self.active_selle:
                self._select_selle(self.active_selle)

    def redo(self):
        """Rétablit la dernière action annulée sur les selles."""
        if self.backend.redo():
            for filename in self.backend.get_selles_props():
                if filename in self.selle_canvas_ids:
                    self._refresh_selle(filename)
            if self.active_selle:
                self._select_selle(self.active_selle)

    def save_selle(self, auto_save=False):
        """Enregistre toutes les selles dans un fichier JSON global."""
        if not self.backend.get_selles_props():
            if not auto_save:
                messagebox.showwarning("Avertissement", "Aucune selle à enregistrer.")
            return
        name = "selles_config" if auto_save else simpledialog.askstring("Nom de la Configuration", "Entrez un nom pour cette configuration :", initialvalue="selles_config")
        if name:
            self.backend.save_global_config(name)
            if not auto_save:
                messagebox.showinfo("Succès", f"Configuration '{name}' enregistrée.")

    def _export_canvas(self):
        """Exporte le canevas actuel sous forme d'image PNG."""
        img = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        bg_path = os.path.join(self.image_folder, self.backend.current_model['background'])
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
        """Charge l'image d'arrière-plan pour le modèle actuel."""
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
        """Redimensionne l'image d'arrière-plan pour qu'elle s'adapte au canevas."""
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
        """Gère le changement de modèle avec un délai."""
        if hasattr(self, '_modele_timer'):
            self._modele_timer.cancel()
        self._modele_timer = Timer(0.2, self._apply_modele_change)
        self._modele_timer.start()

    def _apply_modele_change(self):
        """Applique les changements lors du changement de modèle."""
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
        """Configure le menu principal de l'application."""
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
        """Actualise l'interface en rechargeant le modèle actuel."""
        self._on_modele_change()

    def _show_help(self):
        """Affiche le guide de l'utilisateur."""
        messagebox.showinfo("Guide de l'Utilisateur", "Guide de l'Utilisateur :\n\n1. Sélectionnez un type d'arcade\n2. Choisissez une selle dans la liste\n3. Ajustez la rotation/échelle/position avec les curseurs\n4. Enregistrez vos configurations\n\nRaccourcis :\nCtrl+Z : Annuler\nCtrl+Y : Rétablir\nCtrl+S : Enregistrer")

    def _show_about(self):
        """Affiche les informations sur l'application."""
        messagebox.showinfo("À Propos", "Logiciel de Conception d'Arcades Dentaires\nVersion 2.0\n\nProjet de Fin d'Études\nAuteur : [Votre Nom]\nAnnée : 2023\n\nTechnologies :\n- Python 3\n- Tkinter (Interface Utilisateur)\n- Pillow (Traitement d'Images)")

    def _create_tooltip(self, widget, text: str):
        """Crée une info-bulle pour un widget."""
        def show(event):
            if hasattr(self, 'tooltip') and self.tooltip:
                self.tooltip.destroy()
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            tk.Label(self.tooltip, text=text, bg="#e0e0e0", fg="black", padx=5, pady=2, relief="solid", borderwidth=1).pack()
        def hide(event):
            if hasattr(self, 'tooltip') and self.tooltip:
                self.tooltip.destroy()
                self.tooltip = None
        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)
        widget.bind("<Button-1>", hide)

    def _show_all_selles(self):
        """Affiche toutes les selles avec leurs propriétés sauvegardées."""
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