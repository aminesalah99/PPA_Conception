#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from PIL import Image, ImageTk, ImageOps
import os
from backend import Backend, ElementProperties
from typing import Dict, Tuple, Set, Optional, List
from functools import lru_cache
from threading import Timer
from ui_components import UIComponent, CanvasManager


class BaseDentalApp:
    def __init__(self, root, model_type):
        self.root = root
        self.root.title("Conception d'Arcades Dentaires - PFE")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        self.image_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "images"))
        self.json_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elements_valides")
        os.makedirs(self.json_dir, exist_ok=True)

        self.backend = Backend(self.image_folder, self.json_dir)
        self.model_type = model_type
        
        # Initialiser le modèle actuel AVANT de créer StringVar
        self.backend.set_current_model(model_type)
        
        # Maintenant créer StringVar avec la bonne valeur
        self.current_modele = tk.StringVar(value=model_type)

        self.selle_tk_images: Dict[str, ImageTk.PhotoImage] = {}
        self.selle_canvas_ids: Dict[str, int] = {}
        self.active_selle: Optional[str] = None
        self.drag_offset: Optional[Tuple[float, float]] = None
        self._suppress_slider_callbacks: bool = False

        self.dent_size = 60
        self.teeth_images: Dict[str, ImageTk.PhotoImage] = {}
        self.teeth_objects: Dict[str, int] = {}
        self.selected_teeth: Set[str] = set()
        
        # Charger les positions APRÈS avoir défini le modèle
        self.teeth_positions = self.backend.get_teeth_positions()

        self.teeth_frame = None
        self._modele_timer = None
        self._is_changing_model = False  # Flag pour éviter les changements multiples
        
        self._setup_ui()
        self._bind_shortcuts()

    def _setup_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.controls_frame = UIComponent(self.main_frame, "Contrôles").frame
        self.controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas_manager = CanvasManager(self.canvas_frame)

        self._setup_modele_selector()
        self._setup_canvas()
        self._load_background()
        self._load_teeth_images()
        self._create_teeth_buttons()
        self._display_all_teeth()
        self._setup_selle_controls()
        self._setup_transformation_controls()
        self._setup_menu()

    def _setup_selle_controls(self):
        """Configurer les contrôles des selles de façon ultra-simplifiée."""
        self.selle_frame = UIComponent(self.controls_frame, "Éléments").frame
        self.selle_frame.pack(fill=tk.X, pady=5)

        # Type d'élément (affiché en permanence mais compact)
        self.element_type = tk.StringVar(value="Selles")

        # Frame compact pour le type et la sélection
        top_frame = tk.Frame(self.selle_frame)
        top_frame.pack(fill=tk.X, pady=2)

        # Menu compact du type d'élément
        element_types = ["Selles", "Appuis Cingulaires Bleus", "Appuis Cingulaires Noirs",
                        "Crochets Ackers", "Crochets Bonwill", "Crochets Nally", "Lignes d'Arrêt"]
        self.element_type_menu = tk.OptionMenu(top_frame, self.element_type, *element_types,
                                              command=self._on_element_type_change)
        self.element_type_menu.config(width=20)
        self.element_type_menu.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Bouton d'ajout compact
        tk.Button(top_frame, text="+", command=self._import_selle, width=3).pack(side=tk.RIGHT)

        # Menu des fichiers (compact)
        self.selle_files = self._get_selle_files()
        self.selected_selle = tk.StringVar(value=self.selle_files[0] if self.selle_files else "")

        self.selle_menu = tk.OptionMenu(self.selle_frame, self.selected_selle, *self.selle_files, command=self.load_selle)
        self.selle_menu.config(width=25)
        self.selle_menu.pack(fill=tk.X, pady=2)

        # Boutons d'actions rapides (ligne unique, compacte)
        actions_frame = tk.Frame(self.selle_frame)
        actions_frame.pack(fill=tk.X, pady=2)

        tk.Button(actions_frame, text="🗑️", command=self._clear_selle, width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(actions_frame, text="👁️", command=self._show_all_selles, width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(actions_frame, text="🔍", command=self._search_matching_selles, width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(actions_frame, text="⚙️", command=self._show_advanced_menu, width=3).pack(side=tk.RIGHT, padx=1)

    def _on_element_type_change(self, *args):
        """Gérer le changement de type d'élément."""
        print(f"🔄 Changement de type d'élément vers: {self.element_type.get()}")
        self.selle_files = self._get_selle_files()
        print(f"📁 Fichiers trouvés: {len(self.selle_files)} - {self.selle_files[:3]}...")

        # Recréer complètement le menu des selles pour s'assurer de sa mise à jour
        if hasattr(self, 'selle_menu') and self.selle_menu:
            self.selle_menu.destroy()

        self.selected_selle = tk.StringVar(value=self.selle_files[0] if self.selle_files else "(aucun fichier)")
        self.selle_menu = tk.OptionMenu(self.selle_frame, self.selected_selle, *self.selle_files, command=self.load_selle)
        self.selle_menu.config(width=25)
        self.selle_menu.pack(fill=tk.X, pady=2)

        print(f"✅ Menu des selles recréé avec {len(self.selle_files)} fichiers")

        # Recharger les éléments sauvegardés pour le type actuel
        self._reload_saved_elements_for_model()

        # Forcer la mise à jour de l'interface
        self.root.update_idletasks()

    def _get_selle_files(self) -> List[str]:
        """Obtenir la liste des fichiers pour le type d'élément actuel."""
        # Déterminer le dossier selon le type sélectionné
        element_type = getattr(self, 'element_type', tk.StringVar(value="Selles")).get()

        if element_type == "Selles":
            folder = os.path.join(self.image_folder, self.backend.model_manager.current_model['folder'])
        elif element_type == "Appuis Cingulaires Bleus":
            folder = os.path.join(self.image_folder, "appuis_cingulaires", "bleus")
        elif element_type == "Appuis Cingulaires Noirs":
            folder = os.path.join(self.image_folder, "appuis_cingulaires", "noirs")
        elif element_type == "Crochets Ackers":
            folder = os.path.join(self.image_folder, "crochets", "ackers")
        elif element_type == "Crochets Bonwill":
            folder = os.path.join(self.image_folder, "crochets", "bonwill")
        elif element_type == "Crochets Nally":
            folder = os.path.join(self.image_folder, "crochets", "nally")
        elif element_type == "Lignes d'Arrêt":
            model_folder = self.backend.model_manager.current_model['folder']
            if 'selles_sup' in model_folder:
                folder = os.path.join(self.image_folder, "lignes_arret", "LA_sup")
            elif 'selles_inf' in model_folder:
                folder = os.path.join(self.image_folder, "lignes_arret", "LA_inf")
        else:
            # Par défaut, selles
            folder = os.path.join(self.image_folder, self.backend.model_manager.current_model['folder'])
        
        try:
            files = []
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            # print(f"DEBUG: element_type={element_type}, folder={folder}, files count={len(files)}")  # Temporaire pour debug
            return files if files else ["(aucun fichier)"]
        except Exception as e:
            print(f"Erreur lors de la lecture du dossier {folder}: {e}")
            return ["(aucun fichier)"]

    def _load_transformed_image(self, props: ElementProperties) -> Optional[Image.Image]:
        """Charger et transformer une image selon le type d'élément."""
        element_type = getattr(self, 'element_type', tk.StringVar(value="Selles")).get()

        if element_type == "Selles":
            folder = self.backend.model_manager.current_model['folder']
        elif element_type == "Lignes d'Arrêt":
            model_folder = self.backend.model_manager.current_model['folder']
            if 'selles_sup' in model_folder:
                folder = os.path.join("lignes_arret", "LA_sup")
            elif 'selles_inf' in model_folder:
                folder = os.path.join("lignes_arret", "LA_inf")
        elif element_type == "Appuis Cingulaires Bleus":
            folder = os.path.join("appuis_cingulaires", "bleus")
        elif element_type == "Appuis Cingulaires Noirs":
            folder = os.path.join("appuis_cingulaires", "noirs")
        elif element_type == "Crochets Ackers":
            folder = os.path.join("crochets", "ackers")
        elif element_type == "Crochets Bonwill":
            folder = os.path.join("crochets", "bonwill")
        elif element_type == "Crochets Nally":
            folder = os.path.join("crochets", "nally")
        
        path = os.path.join(self.image_folder, folder, props.image)
        
        try:
            if not os.path.exists(path):
                print(f"Fichier non trouvé: {path}")
                return None
            with Image.open(path) as img:
                if img is None:
                    raise ValueError("Image introuvable ou corrompue")
                img = img.copy().convert("RGBA")
                if props.flip_x:
                    img = ImageOps.mirror(img)
                if props.flip_y:
                    img = ImageOps.flip(img)
                w, h = img.size
                img = img.resize((int(w * props.scale), int(h * props.scale)), Image.Resampling.LANCZOS)
                img = img.rotate(props.angle, expand=True, resample=Image.BICUBIC)
                return img
        except Exception as e:
            print(f"Erreur lors du chargement de {path}: {e}")
            return None

    # [Keep all other existing methods unchanged]
    def _bind_shortcuts(self):
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-s>", lambda e: self._save_to_database())

    def _setup_modele_selector(self):
        """Configurer le sélecteur de modèle."""
        modele_frame = UIComponent(self.controls_frame, "Type d'Arcade").frame
        modele_frame.pack(fill=tk.X, pady=10)
        
        options = list(self.backend.model_manager.models.keys())
        
        # S'assurer que la valeur actuelle est dans les options
        current_value = self.current_modele.get()
        if current_value not in options:
            self.current_modele.set(options[0] if options else '')
        
        self.modele_menu = tk.OptionMenu(
            modele_frame, 
            self.current_modele, 
            *options, 
            command=self._on_modele_change
        )
        self.modele_menu.pack(fill=tk.X)

    def _setup_canvas(self):
        self.canvas_manager.bind_resize(self._on_canvas_resize)

    def _on_canvas_resize(self, event):
        if event.width < 100 or event.height < 100:
            return
        self.canvas_manager.width = event.width
        self.canvas_manager.height = event.height
        self._load_background()
        for filename in list(self.selle_canvas_ids.keys()):
            self._refresh_selle(filename)

    @lru_cache(maxsize=64)
    def _load_image_cached(self, path: str, size: Tuple[int, int]) -> Optional[Image.Image]:
        try:
            with Image.open(path) as img:
                return img.resize(size, Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Erreur lors du chargement de l'image {path}: {e}")
            return None

    def _load_teeth_images(self):
        """Charger les images des dents pour le modèle actuel."""
        self.teeth_images.clear()
        
        # S'assurer qu'on a les bonnes positions pour le modèle actuel
        self.teeth_positions = self.backend.get_teeth_positions()
        
        for filename in self.teeth_positions.keys():
            path = os.path.join(self.image_folder, "dents", filename)
            try:
                img = self._load_image_cached(path, (self.dent_size, self.dent_size))
                if img is None:
                    img = Image.new('RGBA', (self.dent_size, self.dent_size), (255, 0, 0, 128))
                self.teeth_images[filename] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Erreur lors du chargement de l'image {path}: {e}")
                self.teeth_images[filename] = ImageTk.PhotoImage(
                    Image.new('RGBA', (self.dent_size, self.dent_size), (255, 0, 0, 128))
                )

    def _create_teeth_buttons(self):
        """Créer les boutons de contrôle des dents."""
        if self.teeth_frame:
            self.teeth_frame.destroy()
            
        self.teeth_frame = UIComponent(self.controls_frame, "Contrôle des Dents").frame
        self.teeth_frame.pack(fill=tk.X, pady=5)

        buttons_frame = tk.Frame(self.teeth_frame)
        buttons_frame.pack()
        
        # Récupérer les positions actuelles
        current_positions = self.backend.get_teeth_positions()
        
        for filename in sorted(current_positions.keys(), key=lambda x: x.split('_')[1]):
            num = filename.split('.')[0].split('_')[1]
            if num not in ['18', '28', '38', '48']:  # Exclure les dents de sagesse
                present = current_positions[filename][4]
                btn = tk.Button(
                    buttons_frame, 
                    text=num, 
                    width=4, 
                    bg="green" if present else "red", 
                    fg="white",
                    command=lambda f=filename: self._toggle_tooth(f)
                )
                btn.pack(side=tk.LEFT, padx=2)

        global_frame = tk.Frame(self.teeth_frame)
        global_frame.pack(pady=5)
        
        tk.Button(global_frame, text="Tout Afficher", command=self._display_all_teeth).pack(side=tk.LEFT, padx=2)
        tk.Button(global_frame, text="Tout Masquer", command=self._hide_all_teeth).pack(side=tk.LEFT, padx=2)
        tk.Button(global_frame, text="Afficher Positions", command=self._show_teeth_positions).pack(side=tk.LEFT, padx=2)
        tk.Button(global_frame, text="Exporter Arcade PNG", command=self._export_canvas).pack(side=tk.LEFT, padx=2)

    def _show_teeth_positions(self):
        positions = []
        for filename, obj_id in self.teeth_objects.items():
            coords = self.canvas_manager.coords(obj_id)
            if coords:
                positions.append(f"{filename}: ({coords[0]:.1f}, {coords[1]:.1f})")
        
        if positions:
            messagebox.showinfo("Positions des Dents", "\n".join(positions))
        else:
            messagebox.showwarning("Aucune Dent Visible", "Aucune dent affichée.")

    def _toggle_tooth(self, filename: str):
        """Basculer la visibilité d'une dent spécifique."""
        if filename not in self.teeth_positions:
            return
        
        # Obtenir l'état actuel
        x, y, scale, rotation, present = self.teeth_positions[filename]
        
        # Inverser l'état de présence
        new_present = not present
        self.backend.set_tooth_present(filename, new_present)
        
        # Mettre à jour les positions locales
        self.teeth_positions = self.backend.get_teeth_positions()
        
        # Mettre à jour l'affichage
        if new_present:
            # Afficher la dent si elle devient présente
            if filename not in self.teeth_objects:
                self._display_tooth(filename)
        else:
            # Masquer la dent si elle devient absente
            if filename in self.teeth_objects:
                self._hide_tooth(filename)
        
        # Recréer les boutons pour mettre à jour les couleurs
        self._create_teeth_buttons()

    def _adjust_teeth_positions(self, x: float, y: float) -> Tuple[float, float]:
        """Ajuster les positions des dents en fonction de l'échelle du fond."""
        scaled_x = x * self.canvas_manager.bg_scale_factor
        scaled_y = y * self.canvas_manager.bg_scale_factor
        offset_x = (self.canvas_manager.width - self.canvas_manager.bg_width) // 2
        offset_y = (self.canvas_manager.height - self.canvas_manager.bg_height) // 2
        return offset_x + scaled_x, offset_y + scaled_y

    def _display_tooth(self, filename: str):
        """Afficher une dent sur le canvas."""
        if filename in self.teeth_objects:
            return
        
        if filename not in self.teeth_positions:
            return
            
        x, y, scale, rotation, present = self.teeth_positions[filename]
        
        if not present:
            return
            
        if hasattr(self.canvas_manager, 'bg_scale_factor'):
            x, y = self._adjust_teeth_positions(x, y)
        
        try:
            img = Image.open(os.path.join(self.image_folder, "dents", filename)).convert("RGBA")
            img = img.resize((int(self.dent_size * scale), int(self.dent_size * scale)), Image.Resampling.LANCZOS)
            img = img.rotate(rotation, expand=True, resample=Image.BICUBIC)
            self.teeth_images[filename] = ImageTk.PhotoImage(img)
            img_id = self.canvas_manager.create_image(
                x, y, 
                image=self.teeth_images[filename], 
                tags=("tooth", filename), 
                anchor=tk.CENTER
            )
            self.teeth_objects[filename] = img_id
        except Exception as e:
            print(f"Erreur lors de l'affichage de la dent {filename}: {e}")

    def _update_teeth_positions(self):
        """Mettre à jour les positions des dents après redimensionnement."""
        for filename in list(self.teeth_objects.keys()):
            self._hide_tooth(filename)
        self._display_all_teeth()

    def _hide_tooth(self, filename: str):
        """Masquer une dent du canvas."""
        if filename in self.teeth_objects:
            self.canvas_manager.delete(self.teeth_objects[filename])
            del self.teeth_objects[filename]
            self.selected_teeth.discard(filename)

    def _display_all_teeth(self):
        """Afficher toutes les dents présentes."""
        # Rafraîchir les positions depuis le backend
        self.teeth_positions = self.backend.get_teeth_positions()
        
        for filename, (x, y, scale, rotation, present) in self.teeth_positions.items():
            if present:
                self._display_tooth(filename)

    def _hide_all_teeth(self):
        """Masquer toutes les dents affichées."""
        for filename in list(self.teeth_objects.keys()):
            self._hide_tooth(filename)

    def _import_selle(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if file_path:
            try:
                dest_path = os.path.join(self.image_folder, self.backend.model_manager.current_model['folder'], os.path.basename(file_path))
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(file_path, 'rb') as src, open(dest_path, 'wb') as dst:
                    dst.write(src.read())
                self._update_selle_menu(os.path.basename(file_path))
                self.backend.load_selle_properties(os.path.basename(file_path))
                messagebox.showinfo("Succès", f"Selle importée : {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'importer la selle: {e}")

    def _rename_selle(self):
        current_selle = self.selected_selle.get()
        if not current_selle or current_selle == "(aucune selle)":
            messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
            return
            
        new_name = simpledialog.askstring("Renommer", "Nouveau nom pour la selle :", initialvalue=current_selle)
        if new_name and new_name != current_selle:
            try:
                old_path = os.path.join(self.image_folder, self.backend.model_manager.current_model['folder'], current_selle)
                new_path = os.path.join(self.image_folder, self.backend.model_manager.current_model['folder'], new_name)
                os.rename(old_path, new_path)
                self._update_selle_after_rename(current_selle, new_name)
                messagebox.showinfo("Succès", f"Selle renommée en {new_name}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de renommer la selle: {e}")

    def _update_selle_after_rename(self, old_name: str, new_name: str):
        if old_name in self.selle_canvas_ids:
            self.selle_tk_images[new_name] = self.selle_tk_images.pop(old_name)
            self.selle_canvas_ids[new_name] = self.selle_canvas_ids.pop(old_name)
            self.canvas_manager.itemconfig(self.selle_canvas_ids[new_name], tags=("selle", new_name))
            if old_name in self.backend.model_manager.selles_props:
                self.backend.model_manager.selles_props[new_name] = self.backend.model_manager.selles_props.pop(old_name)
                self.backend.model_manager.selles_props[new_name].image = new_name
            if self.active_selle == old_name:
                self.active_selle = new_name
        self._update_selle_menu(new_name)

    def _update_selle_menu(self, selected: str = ""):
        """Mettre à jour le menu des selles."""
        self.selle_files = self._get_selle_files()
        self.selle_menu["menu"].delete(0, "end")
        for f in self.selle_files:
            self.selle_menu["menu"].add_command(label=f, command=tk._setit(self.selected_selle, f))
        if selected and selected in self.selle_files:
            self.selected_selle.set(selected)
        elif self.selle_files:
            self.selected_selle.set(self.selle_files[0])
        else:
            self.selected_selle.set("(aucune selle)")

    def _delete_selle(self):
        current_selle = self.selected_selle.get()
        if not current_selle or current_selle == "(aucune selle)":
            messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
            return
            
        if messagebox.askyesno("Confirmer", f"Voulez-vous vraiment supprimer {current_selle} ?"):
            try:
                path = os.path.join(self.image_folder, self.backend.model_manager.current_model['folder'], current_selle)
                os.remove(path)
                self._remove_selle_from_canvas(current_selle)
                self._update_selle_menu()
                messagebox.showinfo("Succès", f"Selle {current_selle} supprimée.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer la selle: {e}")

    def _remove_selle_from_canvas(self, selle: str):
        if selle in self.selle_canvas_ids:
            self.canvas_manager.delete(self.selle_canvas_ids[selle])
            del self.selle_canvas_ids[selle]
            if selle in self.selle_tk_images:
                del self.selle_tk_images[selle]
            if selle in self.backend.model_manager.selles_props:
                del self.backend.model_manager.selles_props[selle]
            if self.active_selle == selle:
                self.active_selle = None

    def load_selle(self, filename: Optional[str] = None):
        filename = filename or self.selected_selle.get()
        if not filename or filename == "(aucune selle)":
            messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
            return

        try:
            print(f"🔄 Chargement de l'élément: {filename}")

            # Charger les propriétés depuis la base de données
            props = self.backend.load_selle_properties(filename)

            # Vérifier que les propriétés sont correctement chargées
            if props and hasattr(props, 'x') and hasattr(props, 'y'):
                print(f"📍 Position chargée: x={props.x:.1f}, y={props.y:.1f}")

                # S'assurer que le type_element est correct selon le type sélectionné
                current_element_type = self.element_type.get()
                props.type_element = current_element_type

                # Mettre à jour le type d'élément sélectionné si nécessaire
                self.element_type.set(current_element_type)
                print(f"🔧 Type d'élément changé en: {current_element_type}")

                # Rafraîchir l'affichage
                self._refresh_selle(filename)

                # Sélectionner l'élément
                self._select_selle(filename)

                print(f"✅ Élément {filename} chargé avec succès")
            else:
                print(f"⚠️ Propriétés non trouvées pour {filename}, création de nouvelles propriétés")
                # Créer de nouvelles propriétés par défaut avec le bon type
                current_element_type = self.element_type.get()
                props = ElementProperties(image=filename, x=400, y=300, type_element=current_element_type)
                self.backend.model_manager.selles_props[filename] = props
                print(f"✅ Nouvelles propriétés créées pour {filename} avec type: {current_element_type}")
                self._refresh_selle(filename)
                self._select_selle(filename)

        except Exception as e:
            print(f"❌ Erreur lors du chargement de {filename}: {e}")
            messagebox.showerror("Erreur", f"Impossible de charger l'élément: {e}")

    def _refresh_selle(self, filename: str):
        try:
            # Utiliser les propriétés actuelles de selles_props plutôt que recharger de la BD
            props = self.backend.model_manager.selles_props.get(filename)
            if props is None:
                props = self.backend.load_selle_properties(filename)

            img = self._load_transformed_image(props)
            if img:
                # Supprimer l'ancienne image du canvas si elle existe encore
                if filename in self.selle_canvas_ids:
                    try:
                        self.canvas_manager.delete(self.selle_canvas_ids[filename])
                    except tk.TclError:
                        # L'élément n'existe plus, c'est normal
                        pass

                # Créer la nouvelle image
                self.selle_tk_images[filename] = ImageTk.PhotoImage(img)
                self.selle_canvas_ids[filename] = self.canvas_manager.create_image(
                    props.x, props.y, image=self.selle_tk_images[filename], tags=("selle", filename), anchor=tk.CENTER
                )

                # Re-bind les événements
                self._bind_selle_events(filename)
        except Exception as e:
            print(f"Erreur lors du rafraîchissement de la selle {filename}: {e}")

    def _select_selle(self, filename: str):
        if filename in self.backend.model_manager.selles_props and filename in self.selle_canvas_ids:
            self.active_selle = filename
            props = self.backend.model_manager.selles_props[filename]
            for fname in self.selle_canvas_ids:
                if fname != filename:
                    self.canvas_manager.tag_lower(self.selle_canvas_ids[fname])
            self.canvas_manager.tag_raise(self.selle_canvas_ids[filename])
            self.root.after(0, lambda: self._update_sliders(props))

    def _update_sliders(self, props):
        # Prevent saves during UI update
        self._suppress_slider_callbacks = True
        try:
            if hasattr(self, 'rotation_slider'):
                self.rotation_slider.set(props.angle)
            if hasattr(self, 'scale_slider'):
                self.scale_slider.set(props.scale)
            if hasattr(self, 'selle_x_var'):
                self.selle_x_var.set(props.x)
            if hasattr(self, 'selle_y_var'):
                self.selle_y_var.set(props.y)
        finally:
            self._suppress_slider_callbacks = False

    def _clear_selle(self):
        """Effacer toutes les selles du canvas."""
        for filename in list(self.selle_canvas_ids.keys()):
            self._remove_selle_from_canvas(filename)
        self.backend.model_manager.save_state()

    def _clear_canvas(self):
        """Effacer tout le canvas."""
        self.canvas_manager.delete("all")
        self.teeth_objects.clear()
        self.selle_canvas_ids.clear()
        self.selle_tk_images.clear()
        self.teeth_images.clear()

    def _bind_selle_events(self, filename: str):
        canvas_id = self.selle_canvas_ids[filename]
        self.canvas_manager.tag_bind(canvas_id, "<Button-1>", lambda e, fname=filename: self._start_drag(e, fname))
        self.canvas_manager.tag_bind(canvas_id, "<B1-Motion>", self._do_drag)
        self.canvas_manager.tag_bind(canvas_id, "<ButtonRelease-1>", self._stop_drag)

    def _setup_transformation_controls(self):
        """Configuration optimisée des contrôles de transformation."""
        transform_frame = UIComponent(self.controls_frame, "Transformations").frame
        transform_frame.pack(fill=tk.X, pady=10)

        # Boutons principaux en haut
        main_buttons_frame = tk.Frame(transform_frame)
        main_buttons_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Button(main_buttons_frame, text="💾 Enregistrer", command=self._save_to_database, bg="#4CAF50", fg="white",
                  font=("Arial", 10, "bold"), pady=6).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        tk.Button(main_buttons_frame, text="📷 Exporter PNG", command=self._export_canvas, bg="#2196F3", fg="white",
                  font=("Arial", 10)).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # Sliders avec layout optimisé
        self._setup_selle_sliders(transform_frame)

        # Boutons d'action en bas
        action_buttons_frame = tk.Frame(transform_frame)
        action_buttons_frame.pack(fill=tk.X, pady=(10, 0))

        self._setup_flip_buttons(action_buttons_frame)
        self._setup_undo_redo_buttons(action_buttons_frame)

    def _setup_selle_sliders(self, parent):
        selle_frame = tk.Frame(parent)
        selle_frame.pack(fill=tk.X, pady=5)

        x_frame = tk.Frame(selle_frame)
        x_frame.pack(fill=tk.X, pady=2)
        self.selle_x_var = tk.DoubleVar(value=400)
        tk.Label(x_frame, text="Position X :").pack(side=tk.LEFT, padx=5)
        self.selle_x_slider = tk.Scale(x_frame, from_=0, to=800, orient=tk.HORIZONTAL, variable=self.selle_x_var,
                                       command=lambda _: self._move_selle())
        self.selle_x_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        y_frame = tk.Frame(selle_frame)
        y_frame.pack(fill=tk.X, pady=2)
        self.selle_y_var = tk.DoubleVar(value=300)
        tk.Label(y_frame, text="Position Y :").pack(side=tk.LEFT, padx=5)
        self.selle_y_slider = tk.Scale(y_frame, from_=0, to=600, orient=tk.HORIZONTAL, variable=self.selle_y_var,
                                       command=lambda _: self._move_selle())
        self.selle_y_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        rotation_frame = tk.Frame(selle_frame)
        rotation_frame.pack(fill=tk.X, pady=2)
        tk.Label(rotation_frame, text="Rotation (°) :").pack(side=tk.LEFT, padx=5)
        self.rotation_slider = tk.Scale(rotation_frame, from_=-180, to=180, orient=tk.HORIZONTAL,
                                        command=lambda _: self._apply_transform())
        self.rotation_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        scale_frame = tk.Frame(selle_frame)
        scale_frame.pack(fill=tk.X, pady=2)
        tk.Label(scale_frame, text="Échelle :").pack(side=tk.LEFT, padx=5)
        self.scale_slider = tk.Scale(scale_frame, from_=0.3, to=2.0, resolution=0.01, orient=tk.HORIZONTAL,
                                     command=lambda _: self._apply_transform())
        self.scale_slider.set(1.0)
        self.scale_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

    def _setup_flip_buttons(self, parent):
        flip_frame = tk.Frame(parent)
        flip_frame.pack(fill=tk.X, pady=5)
        tk.Button(flip_frame, text="↔ Retourner H", command=self._flip_x).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(flip_frame, text="↕ Retourner V", command=self._flip_y).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def _setup_undo_redo_buttons(self, parent):
        undo_frame = tk.Frame(parent)
        undo_frame.pack(fill=tk.X, pady=5)
        tk.Button(undo_frame, text="↩ Annuler (Ctrl+Z)", command=self.undo).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(undo_frame, text="↪ Rétablir (Ctrl+Y)", command=self.redo).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def _apply_transform(self):
        # Don't save if this is triggered by UI update
        if self._suppress_slider_callbacks:
            return

        if self.active_selle:
            try:
                self.backend.update_selle_angle(self.active_selle, self.rotation_slider.get())
                self.backend.update_selle_scale(self.active_selle, self.scale_slider.get())
                self._refresh_selle(self.active_selle)
            except Exception as e:
                print(f"Erreur lors de l'application de la transformation: {e}")

    def _flip_x(self):
        if self.active_selle:
            try:
                self.backend.flip_selle_x(self.active_selle)
                self._refresh_selle(self.active_selle)
            except Exception as e:
                print(f"Erreur lors du retournement horizontal: {e}")

    def _flip_y(self):
        if self.active_selle:
            try:
                self.backend.flip_selle_y(self.active_selle)
                self._refresh_selle(self.active_selle)
            except Exception as e:
                print(f"Erreur lors du retournement vertical: {e}")

    def _start_drag(self, event, filename: str):
        self.active_selle = filename
        props = self.backend.model_manager.selles_props[filename]
        self.drag_offset = (event.x - props.x, event.y - props.y)
        self._select_selle(filename)

    def _do_drag(self, event):
        if self.drag_offset and self.active_selle:
            new_x = max(50, min(self.canvas_manager.width - 50, event.x - self.drag_offset[0]))
            new_y = max(50, min(self.canvas_manager.height - 50, event.y - self.drag_offset[1]))
            try:
                self.canvas_manager.set_coords(self.selle_canvas_ids[self.active_selle], new_x, new_y)
                # Mettre à jour les sliders en temps réel
                self.selle_x_var.set(new_x)
                self.selle_y_var.set(new_y)
            except Exception as e:
                print(f"Erreur lors du déplacement: {e}")

    def _stop_drag(self, event):
        if self.drag_offset and self.active_selle:
            try:
                final_coords = self.canvas_manager.coords(self.selle_canvas_ids[self.active_selle])
                if final_coords:
                    self.backend.update_selle_position(self.active_selle, final_coords[0], final_coords[1])
            except Exception as e:
                print(f"Erreur lors de l'enregistrement de la position: {e}")
        self.drag_offset = None

    def _move_selle(self):
        # Don't save if this is triggered by UI update
        if self._suppress_slider_callbacks:
            return

        if self.active_selle:
            try:
                new_x = self.selle_x_var.get()
                new_y = self.selle_y_var.get()
                self.backend.update_selle_position(self.active_selle, new_x, new_y)
                self._refresh_selle(self.active_selle)
            except Exception as e:
                print(f"Erreur lors du déplacement de la selle: {e}")

    def undo(self):
        try:
            if self.backend.undo():
                for filename in self.backend.get_selles_props():
                    if filename in self.selle_canvas_ids:
                        self._refresh_selle(filename)
                if self.active_selle:
                    self._select_selle(self.active_selle)
        except Exception as e:
            print(f"Erreur lors de l'annulation: {e}")

    def redo(self):
        try:
            if self.backend.redo():
                for filename in self.backend.get_selles_props():
                    if filename in self.selle_canvas_ids:
                        self._refresh_selle(filename)
                if self.active_selle:
                    self._select_selle(self.active_selle)
        except Exception as e:
            print(f"Erreur lors du rétablissement: {e}")

    def _save_to_database(self):
        try:
            if self.active_selle:
                # Sauvegarder seulement l'élément actif
                self.backend.model_manager.save_single_selle_to_db(self.active_selle)
                messagebox.showinfo("Succès", f"Élément '{self.active_selle}' enregistré dans la base de données!")
            else:
                messagebox.showwarning("Avertissement", "Aucun élément actif sélectionné pour la sauvegarde.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer: {e}")

    def _export_canvas(self):
        try:
            img = Image.new("RGBA", (self.canvas_manager.width, self.canvas_manager.height), (255, 255, 255, 255))
            
            # Fond
            bg_path = os.path.join(self.image_folder, "fonds", self.backend.model_manager.current_model['background'])
            with Image.open(bg_path) as bg_img:
                bg_img = bg_img.convert("RGBA")
                bg_resized = bg_img.resize((self.canvas_manager.bg_width, self.canvas_manager.bg_height), Image.Resampling.LANCZOS)
                offset_x = (self.canvas_manager.width - self.canvas_manager.bg_width) // 2
                offset_y = (self.canvas_manager.height - self.canvas_manager.bg_height) // 2
                img.paste(bg_resized, (offset_x, offset_y), bg_resized)

            temp_img = Image.new("RGBA", img.size, (0, 0, 0, 0))

            # Dents
            for filename, obj_id in self.teeth_objects.items():
                coords = self.canvas_manager.coords(obj_id)
                if not coords:
                    continue
                    
                x, y = coords
                tooth_img = Image.open(os.path.join(self.image_folder, "dents", filename)).convert("RGBA")
                scale, rotation = self.teeth_positions.get(filename, (0, 0, 1.0, 0.0, True))[2:4]
                tooth_img = tooth_img.resize((int(self.dent_size * scale), int(self.dent_size * scale)), Image.Resampling.LANCZOS)
                tooth_img = tooth_img.rotate(rotation, expand=True)
                pos_x = int(x - tooth_img.width // 2)
                pos_y = int(y - tooth_img.height // 2)
                temp_img.alpha_composite(tooth_img, (pos_x, pos_y))

            # Selles
            for filename in self.selle_canvas_ids:
                props = self.backend.model_manager.selles_props.get(filename, ElementProperties(image=filename))
                selle_img = self._load_transformed_image(props)
                if selle_img:
                    pos_x = int(props.x - selle_img.width // 2)
                    pos_y = int(props.y - selle_img.height // 2)
                    temp_img.alpha_composite(selle_img, (pos_x, pos_y))

            img.alpha_composite(temp_img)

            # Nom du fichier
            all_teeth = set(self.backend.model_manager.current_model['teeth'])
            present_teeth = {f for f, (_, _, _, _, p) in self.teeth_positions.items() if p}
            missing_teeth = sorted(int(f.split('_')[1].split('.')[0]) for f in all_teeth - present_teeth)
            
            missing_str = ""
            if missing_teeth:
                ranges = []
                start = missing_teeth[0]
                prev = start
                for current in missing_teeth[1:] + [None]:
                    if current != prev + 1:
                        if start == prev:
                            ranges.append(str(start))
                        else:
                            ranges.append(f"{start}-{prev}")
                        start = current
                    prev = current
                missing_str = "_" + "_".join(ranges) if ranges else ""

            output_path = os.path.join(self.json_dir, f"design_{self.current_modele.get()}{missing_str}_{self.active_selle or 'sans_nom'}.png")
            img.save(output_path)
            messagebox.showinfo("Succès", f"Design exporté vers {output_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'exporter le design: {e}")

    def _load_background(self):
        bg_path = os.path.join(self.image_folder, "fonds", self.backend.model_manager.current_model['background'])
        try:
            with Image.open(bg_path) as img:
                img_copy = img.copy()
                self._resize_background(img_copy)
                resized_img = img_copy.resize((self.canvas_manager.bg_width, self.canvas_manager.bg_height), Image.Resampling.LANCZOS)
                self.canvas_manager.bg_photo = ImageTk.PhotoImage(resized_img)
                if self.canvas_manager.bg_id:
                    self.canvas_manager.delete(self.canvas_manager.bg_id)
                self.canvas_manager.bg_id = self.canvas_manager.create_image(
                    self.canvas_manager.width // 2, 
                    self.canvas_manager.height // 2,
                    image=self.canvas_manager.bg_photo, 
                    tags=("background",), 
                    anchor=tk.CENTER
                )
                self.canvas_manager.tag_lower(self.canvas_manager.bg_id)
                self._update_teeth_positions()
        except Exception as e:
            print(f"Erreur chargement fond: {e}")
            messagebox.showerror("Erreur", f"Impossible de charger le fond {self.backend.model_manager.current_model['background']}")

    def _resize_background(self, img: Image.Image):
        self.canvas_manager.original_bg_width, self.canvas_manager.original_bg_height = img.width, img.height
        max_width = 700
        img_ratio = img.width / img.height
        new_width = min(img.width, max_width)
        new_height = int(new_width / img_ratio)
        if new_height > self.canvas_manager.height:
            new_height = self.canvas_manager.height
            new_width = int(new_height * img_ratio)
        self.canvas_manager.bg_scale_factor = new_width / self.canvas_manager.original_bg_width
        self.canvas_manager.bg_width, self.canvas_manager.bg_height = new_width, new_height

    def _on_modele_change(self, *_):
        """Gérer le changement de modèle avec protection contre les appels multiples."""
        if self._is_changing_model:
            return
            
        if hasattr(self, '_modele_timer') and self._modele_timer:
            self._modele_timer.cancel()
            
        self._modele_timer = Timer(0.2, self._apply_modele_change)
        self._modele_timer.start()

    def _apply_modele_change(self):
        """Appliquer le changement de modèle."""
        if self._is_changing_model:
            return

        try:
            self._is_changing_model = True

            # Sauvegarder le modèle actuel
            self._save_current_modele()

            # Nettoyer l'interface
            self._clear_canvas()
            self._clear_selle()

            # Changer le modèle dans le backend
            new_model = self.current_modele.get()
            self.backend.set_current_model(new_model)

            # Recharger les données pour le nouveau modèle
            self.teeth_positions = self.backend.get_teeth_positions()

            # Reconstruire l'interface
            self._load_background()
            self._load_teeth_images()
            self._create_teeth_buttons()
            self._update_selle_menu()
            self._display_all_teeth()

            # Important: Recharger les éléments sauvegardés pour ce modèle
            self._reload_saved_elements_for_model()

            print(f"🔄 Modèle changé vers: {new_model}")

        except Exception as e:
            print(f"Erreur lors du changement de modèle: {e}")
            messagebox.showerror("Erreur", f"Impossible de changer de modèle: {e}")
        finally:
            self._is_changing_model = False

            # S'assurer que l'interface est réactive après le changement
            self.root.after(100, self._ensure_interface_responsive)

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
        try:
            self._apply_modele_change()
        except Exception as e:
            print(f"Erreur lors du rafraîchissement: {e}")

    def _show_help(self):
        messagebox.showinfo("Guide de l'Utilisateur", 
            "1. Sélectionnez un type d'arcade\n"
            "2. Choisissez une selle\n"
            "3. Ajustez position/rotation/échelle\n"
            "4. Enregistrez\n\n"
            "Raccourcis :\n"
            "Ctrl+Z: Annuler\n"
            "Ctrl+Y: Rétablir\n"
            "Ctrl+S: Enregistrer")

    def _show_about(self):
        messagebox.showinfo("À Propos", 
            "Conception d'Arcades Dentaires - PFE\n"
            "Version 1.0\n\n"
            "Développé pour le projet de fin d'études.")

    def _show_all_selles(self):
        try:
            self._clear_selle()
            for filename in self.selle_files:
                if filename != "(aucune selle)":
                    props = self.backend.load_selle_properties(filename)
                    if props:
                        self._refresh_selle(filename)
        except Exception as e:
            print(f"Erreur lors de l'affichage de toutes les selles: {e}")
            messagebox.showerror("Erreur", f"Impossible d'afficher toutes les selles: {e}")

    def _toggle_element_type_selector(self):
        """Afficher une boîte de dialogue pour changer le type d'élément."""
        # Créer une boîte de dialogue simple au lieu d'un frame dans la hiérarchie
        from tkinter import simpledialog

        element_types = [
            "Selles",
            "Appuis Cingulaires Bleus",
            "Appuis Cingulaires Noirs",
            "Crochets Ackers",
            "Crochets Bonwill",
            "Crochets Nally",
            "Lignes d'Arrêt"
        ]

        # Créer une liste avec indices pour simpledialog
        choices = {str(i+1): element_types[i] for i in range(len(element_types))}
        choice_list = [f"{k}. {v}" for k, v in choices.items()]

        # Afficher la boîte de dialogue
        choice = simpledialog.askstring(
            "Changer Type d'Élément",
            "Sélectionnez un type d'élément:\n\n" + "\n".join(choice_list) + "\n\nEntrez le numéro:",
            initialvalue="1"
        )

        if choice and choice in choices:
            selected_type = choices[choice]
            self.element_type.set(selected_type)
            self._on_element_type_change()
            messagebox.showinfo("Type changé", f"Type d'élément changé en: {selected_type}")

    def _toggle_advanced_actions(self):
        """Afficher/masquer les actions avancées."""
        if hasattr(self, 'advanced_frame'):
            if self.advanced_frame.winfo_ismapped():
                self.advanced_frame.pack_forget()
                self.advanced_actions_visible = False
            else:
                self.advanced_frame.pack(fill=tk.X, pady=2)
                self.advanced_actions_visible = True

    def _save_current_modele(self):
        """Sauvegarder le modèle actuel."""
        try:
            with open(os.path.join(self.json_dir, 'last_modele.dat'), 'w') as f:
                f.write(self.current_modele.get())
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du modèle: {e}")

    def _load_last_modele(self) -> str:
        """Charger le dernier modèle utilisé ou retourner le modèle par défaut."""
        try:
            with open(os.path.join(self.json_dir, 'last_modele.dat'), 'r') as f:
                content = f.read().strip()
                if content in self.backend.model_manager.models:
                    return content
        except Exception:
            pass
        return self.model_type

    def _show_advanced_menu(self):
        """Afficher un menu des actions avancées."""
        current_selle = self.selected_selle.get()
        if not current_selle or current_selle == "(aucune selle)":
            messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
            return

        # Créer une fenêtre de menu avancé
        advanced_window = tk.Toplevel(self.root)
        advanced_window.title("Actions Avancées")
        advanced_window.geometry("300x200")
        advanced_window.grab_set()  # Modal

        tk.Label(advanced_window, text=f"Actions pour: {current_selle}", font=("Arial", 10, "bold")).pack(pady=10)

        # Boutons d'actions avancées
        button_frame = tk.Frame(advanced_window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Button(button_frame, text="✏️ Renommer", command=lambda: self._rename_selle_advanced(advanced_window)).pack(fill=tk.X, pady=2)
        tk.Button(button_frame, text="🗑️ Supprimer", command=lambda: self._delete_selle_advanced(advanced_window)).pack(fill=tk.X, pady=2)
        tk.Button(button_frame, text="📋 Dupliquer", command=lambda: self._duplicate_selle_advanced(advanced_window)).pack(fill=tk.X, pady=2)

        # Bouton de fermeture
        tk.Button(advanced_window, text="Fermer", command=advanced_window.destroy).pack(pady=10)

    def _rename_selle_advanced(self, window):
        """Renommer une selle depuis le menu avancé."""
        current_selle = self.selected_selle.get()
        if not current_selle or current_selle == "(aucune selle)":
            return

        new_name = simpledialog.askstring("Renommer", "Nouveau nom pour la selle :", initialvalue=current_selle)
        if new_name and new_name != current_selle:
            try:
                old_path = os.path.join(self.image_folder, self.backend.model_manager.current_model['folder'], current_selle)
                new_path = os.path.join(self.image_folder, self.backend.model_manager.current_model['folder'], new_name)
                os.rename(old_path, new_path)
                self._update_selle_after_rename(current_selle, new_name)
                messagebox.showinfo("Succès", f"Selle renommée en {new_name}")
                window.destroy()
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de renommer la selle: {e}")

    def _delete_selle_advanced(self, window):
        """Supprimer une selle depuis le menu avancé."""
        current_selle = self.selected_selle.get()
        if not current_selle or current_selle == "(aucune selle)":
            return

        if messagebox.askyesno("Confirmer", f"Voulez-vous vraiment supprimer {current_selle} ?"):
            try:
                path = os.path.join(self.image_folder, self.backend.model_manager.current_model['folder'], current_selle)
                os.remove(path)
                self._remove_selle_from_canvas(current_selle)
                self._update_selle_menu()
                messagebox.showinfo("Succès", f"Selle {current_selle} supprimée.")
                window.destroy()
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer la selle: {e}")

    def _duplicate_selle_advanced(self, window):
        """Dupliquer une selle depuis le menu avancé."""
        current_selle = self.selected_selle.get()
        if not current_selle or current_selle == "(aucune selle)":
            return

        new_name = simpledialog.askstring("Dupliquer", "Nom pour la copie :", initialvalue=f"{current_selle}_copy")
        if new_name and new_name != current_selle:
            try:
                old_path = os.path.join(self.image_folder, self.backend.model_manager.current_model['folder'], current_selle)
                new_path = os.path.join(self.image_folder, self.backend.model_manager.current_model['folder'], new_name)

                # Copier le fichier
                with open(old_path, 'rb') as src, open(new_path, 'wb') as dst:
                    dst.write(src.read())

                # Créer de nouvelles propriétés pour la copie avec un léger décalage
                if current_selle in self.backend.model_manager.selles_props:
                    original_props = self.backend.model_manager.selles_props[current_selle]
                    new_props = ElementProperties(
                        image=new_name,
                        x=original_props.x + 20,  # Décalage de 20 pixels
                        y=original_props.y + 20,
                        angle=original_props.angle,
                        scale=original_props.scale,
                        flip_x=original_props.flip_x,
                        flip_y=original_props.flip_y,
                        type_element=original_props.type_element
                    )
                    self.backend.model_manager.selles_props[new_name] = new_props
                    self.backend.save_selle_properties(new_name, new_props.to_dict())

                self._update_selle_menu(new_name)
                self._refresh_selle(new_name)
                messagebox.showinfo("Succès", f"Selle dupliquée en {new_name}")
                window.destroy()
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de dupliquer la selle: {e}")

    def _reload_saved_elements_for_model(self):
        """Recharger les éléments sauvegardés pour le modèle actuel."""
        try:
            import sqlite3

            # Connexion à la base de données
            db_path = os.path.join(self.json_dir, 'dental_database.db')
            if not os.path.exists(db_path):
                print("⚠️ Base de données non trouvée")
                return

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Récupérer TOUS les éléments de la table elements (qui contient maintenant tous les types)
            cursor.execute("SELECT image, x, y, angle, scale, flip_x, flip_y, type_element FROM elements")
            rows = cursor.fetchall()

            elements_loaded = 0
            for row in rows:
                image, x, y, angle, scale, flip_x, flip_y, type_element = row
                type_element = type_element or 'Selles'  # Valeur par défaut

                # Vérifier si l'élément existe dans les fichiers disponibles du type actuel
                current_element_type = self.element_type.get()
                if type_element == current_element_type:
                    # Créer les propriétés
                    props = ElementProperties(
                        image=image,
                        x=float(x),
                        y=float(y),
                        angle=float(angle),
                        scale=float(scale),
                        flip_x=bool(flip_x),
                        flip_y=bool(flip_y),
                        type_element=type_element
                    )

                    # Ajouter aux propriétés du backend (sans affichage automatique)
                    self.backend.model_manager.selles_props[image] = props
                    elements_loaded += 1

            conn.close()

            if elements_loaded > 0:
                print(f"✅ {elements_loaded} éléments de type '{self.element_type.get()}' rechargés pour le modèle {self.current_modele.get()}")
            else:
                print(f"ℹ️ Aucun élément de type '{self.element_type.get()}' trouvé pour le modèle {self.current_modele.get()}")

        except Exception as e:
            print(f"❌ Erreur lors du rechargement des éléments: {e}")

    def _search_matching_selles(self):
        """Rechercher et afficher les selles correspondantes aux dents masquées."""
        try:
            # Obtenir la liste des dents masquées
            hidden_teeth = self.backend.get_hidden_teeth()

            if not hidden_teeth:
                messagebox.showinfo("Recherche de Selles",
                                  "Aucune dent masquée détectée.\nToutes les dents sont présentes.")
                return

            # Trouver les selles correspondantes
            sella_names = self.backend.find_matching_selles(hidden_teeth)

            if not sella_names:
                messagebox.showinfo("Recherche de Selles",
                                  f"Dents masquées: {', '.join(map(str, hidden_teeth))}\n\n"
                                  f"Aucune selle correspondante trouvée.")
                return

            # Vérifier quelles selles existent
            exists_results = self.backend.check_selles_exists(sella_names)
            found_selles = [name for name, exists in zip(sella_names, exists_results) if exists]
            missing_selles = [name for name, exists in zip(sella_names, exists_results) if not exists]

            # Construire le message
            result_message = f"Dents masquées: {', '.join(map(str, hidden_teeth))}\n\n"

            if found_selles:
                result_message += f"✅ Selles trouvées et chargées ({len(found_selles)}):\n"
                for name in found_selles:
                    result_message += f"  • {name}\n"

                # Charger les selles trouvées
                self._clear_selle()  # Effacer les selles existantes
                for name in found_selles:
                    props = self.backend.load_selle_properties(name)
                    self._refresh_selle(name)

            if missing_selles:
                result_message += f"\n⚠️ Selles introuvables (non recommandées en PPA) ({len(missing_selles)}):\n"
                for name in missing_selles:
                    result_message += f"  • {name}\n"

            # Afficher le résultat
            if found_selles and missing_selles:
                messagebox.showwarning("Résultat de la Recherche", result_message)
            elif found_selles:
                messagebox.showinfo("Selles Trouvées", result_message)
            else:
                messagebox.showerror("❌ Aucune selle trouvée (cas non recommandé en PPA)", result_message)

        except Exception as e:
            print(f"Erreur lors de la recherche de selles: {e}")
            messagebox.showerror("Erreur", f"Impossible de rechercher les selles: {e}")

    def _ensure_interface_responsive(self):
        """S'assurer que l'interface est réactive après un changement de modèle."""
        try:
            # Mettre à jour les menus des selles
            self._update_selle_menu()

            # Forcer la mise à jour de l'interface
            self.root.update_idletasks()

            # Réactiver les événements
            self.root.bind("<Button-1>", lambda e: None)  # Réinitialiser les bindings

            print("✅ Interface réactive après changement de modèle")

        except Exception as e:
            print(f"❌ Erreur lors de la réactivation de l'interface: {e}")
