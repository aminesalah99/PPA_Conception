import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import json
import math

# --- CHEMINS À ADAPTER ---
PROJECT_ROOT = r'C:\Projets\PPA_Conception'
IMG_FOLDER = os.path.join(PROJECT_ROOT, 'data', 'images', 'dents')
FOND_PATH = os.path.join(PROJECT_ROOT, 'data', 'images', 'fonds', 'fond_superieur.png')
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'teeth_data.json')
DENT_SIZE = 60

class TeethTestApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Test des Dents - Arcade Supérieure")
        self.geometry("1200x800")
        self.minsize(800, 600)

        # Données initiales
        self.dents = self._initialize_teeth()
        self.dents_images = {}
        self.dents_canvas_ids = {}
        self.active_dent_nom = None
        self.dent_drag_offset = (0, 0)
        self.grid_visible = False
        self.bg_scale_factor = 1.0
        self.bg_width = 0
        self.bg_height = 0

        # Interface
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.controls_frame = tk.LabelFrame(self.main_frame, text="Contrôles", padx=10, pady=10)
        self.controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, width=800, height=600, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        self._setup_controls()
        self._load_background()
        self._bind_canvas_events()

    def _initialize_teeth(self):
        """Initialise les dents avec des positions par défaut, cohérentes avec frontend."""
        teeth = []
        center_x, center_y = 400, 300  # Ajusté pour un canvas de 800x600
        radius = 150
        angle_step = 360 / 16
        for i in range(16):
            dent_id = i + 1
            if i < 8:
                nom = f"dent_1{dent_id}"
                fichier = f"dent_1{dent_id}.png"
            else:
                nom = f"dent_2{i - 7}"
                fichier = f"dent_2{i - 7}.png"
            angle = i * angle_step - 90
            x = center_x + radius * math.cos(math.radians(angle))
            y = center_y + radius * math.sin(math.radians(angle))
            teeth.append({"id": dent_id, "nom": nom, "fichier": fichier, "x": x, "y": y})
        return teeth

    def _setup_controls(self):
        """Configure les boutons de contrôle avec un menu déroulant et l'affichage des coordonnées."""
        # Menu déroulant pour sélectionner la dent
        tk.Label(self.controls_frame, text="Sélectionner une Dent :").pack()
        self.dent_var = tk.StringVar(value=self.dents[0]["nom"] if self.dents else "")
        self.dent_menu = tk.OptionMenu(self.controls_frame, self.dent_var, *[dent["nom"] for dent in self.dents])
        self.dent_menu.pack(pady=5)

        # Boutons par dent
        tk.Button(self.controls_frame, text="Afficher Dent", command=self._show_selected_dent).pack(pady=5)
        tk.Button(self.controls_frame, text="Masquer Dent", command=self._hide_selected_dent).pack(pady=5)

        # Boutons de déplacement collectif
        tk.Button(self.controls_frame, text="Haut (5px)", command=lambda: self._move_all_dents(0, -5)).pack(pady=5)
        tk.Button(self.controls_frame, text="Bas (5px)", command=lambda: self._move_all_dents(0, 5)).pack(pady=5)
        tk.Button(self.controls_frame, text="Gauche (5px)", command=lambda: self._move_all_dents(-5, 0)).pack(pady=5)
        tk.Button(self.controls_frame, text="Droite (5px)", command=lambda: self._move_all_dents(5, 0)).pack(pady=5)

        # Réinitialisation, grille et génération
        tk.Button(self.controls_frame, text="Réinitialiser Positions", command=self._reset_positions).pack(pady=5)
        tk.Button(self.controls_frame, text="Afficher Grille", command=self.toggle_grid).pack(pady=5)
        tk.Button(self.controls_frame, text="Générer Fichier JSON", command=self.generate_json).pack(pady=5)

        # Affichage des coordonnées
        self.coords_label = tk.Label(self.controls_frame, text="Coordonnées: (x, y)", font=("Arial", 10))
        self.coords_label.pack(pady=10)

    def _on_canvas_resize(self, event):
        """Gère le redimensionnement du canevas, cohérent avec frontend."""
        if event.width < 100 or event.height < 100:
            return
        self.canvas.config(width=event.width, height=event.height)
        self._load_background()
        for nom in self.dents_canvas_ids:
            self._refresh_dent(nom)

    def _load_background(self):
        """Charge l'image d'arrière-plan, cohérent avec frontend."""
        if os.path.exists(FOND_PATH):
            with Image.open(FOND_PATH) as img:
                self.original_bg_width = img.width
                self.original_bg_height = img.height
                max_width = 700
                img_ratio = img.width / img.height
                new_width = min(img.width, max_width)
                new_height = int(new_width / img_ratio)
                if new_height > self.canvas.winfo_height():
                    new_height = self.canvas.winfo_height()
                    new_width = int(new_height * img_ratio)
                self.bg_scale_factor = new_width / self.original_bg_width
                self.bg_width = new_width
                self.bg_height = new_height
                self.bg_photo = ImageTk.PhotoImage(img.resize((self.bg_width, self.bg_height), Image.Resampling.LANCZOS))
                if hasattr(self, 'bg_id'):
                    self.canvas.delete(self.bg_id)
                self.bg_id = self.canvas.create_image(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2,
                                                     image=self.bg_photo, anchor=tk.CENTER)
                self.canvas.lower(self.bg_id)
        else:
            messagebox.showerror("Erreur", f"Le fond {FOND_PATH} n'existe pas.")

    def _show_selected_dent(self):
        """Affiche la dent sélectionnée."""
        selected_dent = self.dent_var.get()
        if selected_dent:
            dent = next(d for d in self.dents if d["nom"] == selected_dent)
            if dent["nom"] not in self.dents_canvas_ids:
                self._add_dent_to_canvas(dent)

    def _hide_selected_dent(self):
        """Masque la dent sélectionnée."""
        selected_dent = self.dent_var.get()
        if selected_dent and selected_dent in self.dents_canvas_ids:
            self.canvas.delete(self.dents_canvas_ids[selected_dent])
            del self.dents_canvas_ids[selected_dent]
            if self.active_dent_nom == selected_dent:
                self.active_dent_nom = None
                self.coords_label.config(text="Coordonnées: (x, y)")

    def _add_dent_to_canvas(self, dent):
        """Ajoute une dent au canvas avec ajustements cohérents."""
        nom = dent["nom"]
        fichier = dent["fichier"]
        x, y = dent["x"], dent["y"]
        img_path = os.path.join(IMG_FOLDER, fichier)
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path).convert("RGBA")
                img = img.resize((int(DENT_SIZE * self.bg_scale_factor), int(DENT_SIZE * self.bg_scale_factor)), Image.Resampling.LANCZOS)
                self.dents_images[nom] = ImageTk.PhotoImage(img)
                adjusted_x = (x * self.bg_scale_factor + (self.canvas.winfo_width() - self.bg_width) // 2)
                adjusted_y = (y * self.bg_scale_factor + (self.canvas.winfo_height() - self.bg_height) // 2)
                cid = self.canvas.create_image(adjusted_x, adjusted_y, image=self.dents_images[nom], tags=("dent", nom), anchor=tk.CENTER)
                self.dents_canvas_ids[nom] = cid
                self.active_dent_nom = nom
                self._update_coords_label(adjusted_x, adjusted_y)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur avec {fichier} : {e}")
        else:
            messagebox.showerror("Erreur", f"Fichier {fichier} non trouvé.")

    def _refresh_dent(self, nom):
        """Met à jour l'affichage d'une dent après redimensionnement."""
        if nom in self.dents_canvas_ids:
            dent = next(d for d in self.dents if d["nom"] == nom)
            self.canvas.delete(self.dents_canvas_ids[nom])
            del self.dents_canvas_ids[nom]
            self._add_dent_to_canvas(dent)

    def _bind_canvas_events(self):
        """Lie les événements de déplacement individuel et affiche les coordonnées au clic."""
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        self.canvas.bind("<Button-1>", self.show_coords, add="+")

    def start_drag(self, event):
        """Démarre le déplacement individuel, corrige le ciblage de la dent."""
        cid = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(cid)
        self.active_dent_nom = None
        for tag in tags:
            if tag.startswith("dent_") and tag in self.dents_canvas_ids:
                self.active_dent_nom = tag
                x, y = self.canvas.coords(cid)
                self.dent_drag_offset = (event.x - x, event.y - y)
                break

    def drag(self, event):
        """Déplace une dent individuellement et met à jour les coordonnées."""
        if self.active_dent_nom and self.active_dent_nom in self.dents_canvas_ids:
            cid = self.dents_canvas_ids[self.active_dent_nom]
            x = event.x - self.dent_drag_offset[0]
            y = event.y - self.dent_drag_offset[1]
            x = max(50, min(self.canvas.winfo_width() - 50, x))
            y = max(50, min(self.canvas.winfo_height() - 50, y))
            self.canvas.coords(cid, x, y)
            self._update_coords_label(x, y)
            dent = next(d for d in self.dents if d["nom"] == self.active_dent_nom)
            dent["x"] = (x - (self.canvas.winfo_width() - self.bg_width) // 2) / self.bg_scale_factor
            dent["y"] = (y - (self.canvas.winfo_height() - self.bg_height) // 2) / self.bg_scale_factor

    def stop_drag(self, event):
        """Arrête le déplacement."""
        pass

    def show_coords(self, event):
        """Affiche les coordonnées de la dent cliquée."""
        cid = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(cid)
        for tag in tags:
            if tag.startswith("dent_"):
                x, y = self.canvas.coords(cid)
                self._update_coords_label(x, y)
                break

    def _update_coords_label(self, x, y):
        """Met à jour l'étiquette des coordonnées."""
        if self.active_dent_nom:
            self.coords_label.config(text=f"Coordonnées ({self.active_dent_nom}): ({x:.1f}, {y:.1f})")

    def _move_all_dents(self, dx, dy):
        """Déplace toutes les dents collectivement."""
        for dent in self.dents:
            dent["x"] += dx
            dent["y"] += dy
            dent["x"] = max(50, min(750, dent["x"]))  # Ajusté pour canvas de 800
            dent["y"] = max(50, min(550, dent["y"]))  # Ajusté pour canvas de 600
            if dent["nom"] in self.dents_canvas_ids:
                adjusted_x = dent["x"] * self.bg_scale_factor + (self.canvas.winfo_width() - self.bg_width) // 2
                adjusted_y = dent["y"] * self.bg_scale_factor + (self.canvas.winfo_height() - self.bg_height) // 2
                self.canvas.coords(self.dents_canvas_ids[dent["nom"]], adjusted_x, adjusted_y)
                if dent["nom"] == self.active_dent_nom:
                    self._update_coords_label(adjusted_x, adjusted_y)

    def _reset_positions(self):
        """Réinitialise les positions des dents."""
        self._hide_all_dents()
        self.dents = self._initialize_teeth()
        for dent in self.dents:
            if dent["nom"] in self.dents_canvas_ids:
                self._add_dent_to_canvas(dent)

    def toggle_grid(self):
        """Active ou désactive la grille."""
        self.grid_visible = not self.grid_visible
        if self.grid_visible:
            self._draw_grid()
        else:
            self.canvas.delete("grid")

    def _draw_grid(self):
        """Dessine une grille cohérente avec frontend (pas de 20px, couleur claire)."""
        self.canvas.delete("grid")
        step = 20
        for x in range(0, self.canvas.winfo_width(), step):
            self.canvas.create_line(x, 0, x, self.canvas.winfo_height(), fill="#e0e0e0", tags="grid")
        for y in range(0, self.canvas.winfo_height(), step):
            self.canvas.create_line(0, y, self.canvas.winfo_width(), y, fill="#e0e0e0", tags="grid")

    def generate_json(self):
        """Génère un fichier JSON avec les positions."""
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.dents, f, indent=4)
        messagebox.showinfo("Succès", f"Données enregistrées dans {OUTPUT_FILE}")

if __name__ == "__main__":
    app = TeethTestApp()
    app.mainloop()