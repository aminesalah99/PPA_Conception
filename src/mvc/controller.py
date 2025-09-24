
"""
Controller Component for MVC Architecture

This module contains the controller logic that coordinates between the model and view.
"""

import os
from typing import Dict, Tuple, Optional, List, Set
from PIL import Image, ImageTk, ImageOps
from mvc.model import DentalDesignModel, ToothProperties, SelleProperties
from mvc.view import DentalDesignView
from config import get_config
from error_handler import handle_error, ImageProcessingError, DatabaseError, safe_execute
from collections import deque

class DentalDesignController:
    """Controller class that coordinates between the model and view."""

    def __init__(self, root: tk.Tk, model: DentalDesignModel, view: DentalDesignView):
        """Initialize the dental design controller.

        Args:
            root: The root Tkinter window
            model: The dental design model
            view: The dental design view
        """
        self.root = root
        self.model = model
        self.view = view
        self.config = get_config()

        # Set up initial state
        self.dent_size = self.config.default_dent_size
        self.teeth_positions: Dict[str, Tuple[float, float, float, float, bool]] = {}

        # Register view callbacks
        self._register_view_callbacks()

        # Initialize the application
        self._initialize_application()

    def _register_view_callbacks(self):
        """Register callbacks for view events."""
        self.view.register_callback("model_changed", self._on_model_changed)
        self.view.register_callback("tooth_toggled", self._on_tooth_toggled)
        self.view.register_callback("display_all_teeth", self._on_display_all_teeth)
        self.view.register_callback("hide_all_teeth", self._on_hide_all_teeth)
        self.view.register_callback("selle_loaded", self._on_selle_loaded)
        self.view.register_callback("selle_imported", self._on_selle_imported)
        self.view.register_callback("selle_renamed", self._on_selle_renamed)
        self.view.register_callback("selle_deleted", self._on_selle_deleted)
        self.view.register_callback("clear_selles", self._on_clear_selles)
        self.view.register_callback("show_all_selles", self._on_show_all_selles)
        self.view.register_callback("canvas_resized", self._on_canvas_resized)
        self.view.register_callback("export_canvas", self._on_export_canvas)
        self.view.register_callback("save_to_database", self._on_save_to_database)

    def _initialize_application(self):
        """Initialize the application with default settings."""
        # Load the last used model
        last_model = self._load_last_model()
        self.model.set_current_model(last_model)

        # Update view with current model
        self.view.create_model_selector(self.model.model_manager.get_model_names())
        self.view.model_var.set(last_model)

        # Load teeth positions
        self.teeth_positions = self.model.get_teeth_positions()

        # Load background
        self._load_background()

        # Load teeth images
        self._load_teeth_images()

        # Create teeth buttons
        self.view.create_teeth_buttons(self.teeth_positions)

        # Display all teeth
        self._on_display_all_teeth()

        # Set up selle controls
        self._update_selle_menu()

        # Create transformation controls
        self.view.create_transformation_controls()

        # Set up menu
        self.view.create_menu()

    def _load_last_model(self) -> str:
        """Load the last used model from file."""
        try:
            with open(os.path.join(self.model.json_dir, self.config.last_model_file), 'r') as f:
                content = f.read().strip()
                return content if content in self.model.model_manager.models else self.model.get_current_model_name()
        except Exception:
            return self.model.get_current_model_name()

    def _save_last_model(self):
        """Save the current model to file."""
        try:
            with open(os.path.join(self.model.json_dir, self.config.last_model_file), 'w') as f:
                f.write(self.model.get_current_model_name())
        except Exception as e:
            handle_error(e, "Erreur lors de la sauvegarde du modèle")

    def _on_model_changed(self, model_name: str):
        """Handle model change event."""
        try:
            self._save_last_model()
            self.model.set_current_model(model_name)
            self.teeth_positions = self.model.get_teeth_positions()

            # Clear and reload UI
            self.view.canvas_manager.delete("all")
            self.view.teeth_objects.clear()
            self.view.selle_canvas_ids.clear()
            self.view.teeth_images.clear()

            # Reload background
            self._load_background()

            # Reload teeth images
            self._load_teeth_images()

            # Recreate teeth buttons
            self.view.create_teeth_buttons(self.teeth_positions)

            # Display all teeth
            self._on_display_all_teeth()

            # Update selle menu
            self._update_selle_menu()
        except Exception as e:
            handle_error(e, "Erreur lors du changement de modèle")

    def _on_canvas_resized(self, width: int, height: int):
        """Handle canvas resize event."""
        try:
            self._load_background()
            for filename in self.view.selle_canvas_ids:
                self._refresh_selle(filename)
        except Exception as e:
            handle_error(e, "Erreur lors du redimensionnement du canevas")

    def _load_teeth_images(self):
        """Load tooth images."""
        self.view.teeth_images.clear()
        teeth_folder = self.config.get_teeth_folder()

        for filename in self.teeth_positions.keys():
            path = os.path.join(teeth_folder, filename)
            try:
                img = self._load_image_cached(path, (self.dent_size, self.dent_size))
                if img is None:
                    img = Image.new('RGBA', (self.dent_size, self.dent_size), (255, 0, 0, 128))
                self.view.teeth_images[filename] = ImageTk.PhotoImage(img)
            except Exception as e:
                handle_error(e, f"Erreur lors du chargement de l'image de dent {filename}")
                self.view.teeth_images[filename] = ImageTk.PhotoImage(
                    Image.new('RGBA', (self.dent_size, self.dent_size), (255, 0, 0, 128))
                )

    @staticmethod
    def _load_image_cached(path: str, size: Tuple[int, int]) -> Optional[Image.Image]:
        """Load an image with caching."""
        try:
            with Image.open(path) as img:
                return img.resize(size, getattr(Image.Resampling, config.image_resampling_method))
        except Exception as e:
            handle_error(e, f"Erreur lors du chargement de l'image {path}", show_traceback=False)
            return None

    def _display_tooth(self, filename: str):
        """Display a tooth on the canvas."""
        if filename in self.view.teeth_objects:
            return

        x, y, scale, rotation, present = self.teeth_positions.get(
            filename, 
            (self.view.canvas_manager.width // 2, self.view.canvas_manager.height // 2, 1.0, 0.0, True)
        )

        if not present:
            return

        if hasattr(self.view.canvas_manager, 'bg_scale_factor'):
            x, y = self._adjust_teeth_positions(x, y)

        try:
            img = Image.open(os.path.join(self.config.get_teeth_folder(), filename)).convert("RGBA")
            img = img.resize((int(self.dent_size * scale), int(self.dent_size * scale)), Image.Resampling.LANCZOS)
            img = img.rotate(rotation, expand=True, resample=Image.BICUBIC)
            self.view.teeth_images[filename] = ImageTk.PhotoImage(img)
            img_id = self.view.canvas_manager.create_image(
                x, y, 
                image=self.view.teeth_images[filename], 
                tags=("tooth", filename), 
                anchor=tk.CENTER
            )
            self.view.teeth_objects[filename] = img_id
        except Exception as e:
            handle_error(e, f"Erreur lors de l'affichage de la dent {filename}")

    def _hide_tooth(self, filename: str):
        """Hide a tooth from the canvas."""
        if filename in self.view.teeth_objects:
            self.view.canvas_manager.delete(self.view.teeth_objects[filename])
            del self.view.teeth_objects[filename]
            self.view.selected_teeth.discard(filename)

    def _adjust_teeth_positions(self, x: float, y: float) -> Tuple[float, float]:
        """Adjust teeth positions based on canvas scaling."""
        scaled_x = x * self.view.canvas_manager.bg_scale_factor
        scaled_y = y * self.view.canvas_manager.bg_scale_factor
        offset_x = (self.view.canvas_manager.width - self.view.canvas_manager.bg_width) // 2
        offset_y = (self.view.canvas_manager.height - self.view.canvas_manager.bg_height) // 2
        return offset_x + scaled_x, offset_y + scaled_y

    def _on_tooth_toggled(self, filename: str):
        """Handle tooth toggle event."""
        try:
            if filename not in self.teeth_positions:
                return

            present = self.teeth_positions[filename][4]
            self.model.set_tooth_present(filename, not present)
            self.teeth_positions = self.model.get_teeth_positions()

            if filename in self.view.teeth_objects:
                self._hide_tooth(filename)
            else:
                self._display_tooth(filename)

            self._load_teeth_images()
            self.view.create_teeth_buttons(self.teeth_positions)
        except Exception as e:
            handle_error(e, "Erreur lors du basculement de la visibilité de la dent")

    def _on_display_all_teeth(self):
        """Display all teeth."""
        for filename in self.teeth_positions.keys():
            if self.teeth_positions[filename][4]:
                self._display_tooth(filename)

    def _on_hide_all_teeth(self):
        """Hide all teeth."""
        for filename in list(self.view.teeth_objects.keys()):
            self._hide_tooth(filename)

    def _load_background(self):
        """Load the background image."""
        bg_path = os.path.join(
            self.config.get_backgrounds_folder(), 
            self.model.model_manager.get_current_model().background
        )

        try:
            with Image.open(bg_path) as img:
                img_copy = img.copy()
                self._resize_background(img_copy)
                resized_img = img_copy.resize(
                    (self.view.canvas_manager.bg_width, self.view.canvas_manager.bg_height), 
                    Image.Resampling.LANCZOS
                )
                self.view.canvas_manager.bg_photo = ImageTk.PhotoImage(resized_img)

                if self.view.canvas_manager.bg_id:
                    self.view.canvas_manager.delete(self.view.canvas_manager.bg_id)

                self.view.canvas_manager.bg_id = self.view.canvas_manager.create_image(
                    self.view.canvas_manager.width // 2,
                    self.view.canvas_manager.height // 2,
                    image=self.view.canvas_manager.bg_photo,
                    tags=("background",),
                    anchor=tk.CENTER
                )
                self.view.canvas_manager.tag_lower(self.view.canvas_manager.bg_id)

                # Update teeth positions
                self._update_teeth_positions()
        except Exception as e:
            handle_error(e, f"Impossible de charger le fond {self.model.model_manager.get_current_model().background}")

    def _resize_background(self, img: Image.Image):
        """Resize the background image to fit the canvas."""
        self.view.canvas_manager.original_bg_width, self.view.canvas_manager.original_bg_height = img.width, img.height
        max_width = self.config.max_image_width
        img_ratio = img.width / img.height
        new_width = min(img.width, max_width)
        new_height = int(new_width / img_ratio)

        if new_height > self.view.canvas_manager.height:
            new_height = self.view.canvas_manager.height
            new_width = int(new_height * img_ratio)

        self.view.canvas_manager.bg_scale_factor = new_width / self.view.canvas_manager.original_bg_width
        self.view.canvas_manager.bg_width, self.view.canvas_manager.bg_height = new_width, new_height

    def _update_teeth_positions(self):
        """Update teeth positions after canvas resize."""
        for filename in list(self.view.teeth_objects.keys()):
            self._hide_tooth(filename)
        self._on_display_all_teeth()

    def _update_selle_menu(self, selected: str = ""):
        """Update the selle selection menu."""
        selle_files = self._get_selle_files()

        # Update the menu options
        menu = self.view.selle_menu["menu"]
        menu.delete(0, "end")

        for f in selle_files:
            menu.add_command(label=f, command=tk._setit(self.view.selected_selle, f))

        # Set the selected value
        selected_value = selected or selle_files[0] if selle_files else ""
        self.view.selected_selle.set(selected_value)

    def _get_selle_files(self) -> List[str]:
        """Get list of available dental saddle files."""
        folder = self.config.get_selles_folder(self.model.get_current_model_name())

        try:
            files = []
            if os.path.exists(folder):
                files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            return files if files else ["(aucune selle)"]
        except Exception as e:
            handle_error(e, f"Erreur lors de la lecture du dossier {folder}")
            return ["(aucune selle)"]

    def _on_selle_loaded(self, filename: str):
        """Handle selle loading event."""
        try:
            if not filename or filename == "(aucune selle)":
                messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
                return

            props = self.model.load_selle_properties(filename)
            self._refresh_selle(filename)
            self._select_selle(filename)
        except Exception as e:
            handle_error(e, f"Impossible de charger la selle: {filename}")

    def _refresh_selle(self, filename: str):
        """Refresh a selle on the canvas."""
        try:
            props = self.model.load_selle_properties(filename)
            img = self._load_transformed_image(props)

            if img:
                self.view.selle_tk_images[filename] = ImageTk.PhotoImage(img)

                if filename in self.view.selle_canvas_ids:
                    self.view.canvas_manager.delete(self.view.selle_canvas_ids[filename])

                self.view.selle_canvas_ids[filename] = self.view.canvas_manager.create_image(
                    props.x, props.y, 
                    image=self.view.selle_tk_images[filename], 
                    tags=("selle", filename), 
                    anchor=tk.CENTER
                )

                self._bind_selle_events(filename)
        except Exception as e:
            handle_error(e, f"Erreur lors du rafraîchissement de la selle {filename}")

    def _load_transformed_image(self, props: SelleProperties) -> Optional[Image.Image]:
        """Load and transform a selle image."""
        path = os.path.join(
            self.config.get_selles_folder(self.model.get_current_model_name()), 
            props.image
        )

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
            handle_error(e, f"Impossible de charger l'image {props.image}")
            return None

    def _select_selle(self, filename: str):
        """Select a selle on the canvas."""
        if filename in self.view.selle_canvas_ids:
            self.view.active_selle = filename

            # Lower other selles
            for fname in self.view.selle_canvas_ids:
                if fname != filename:
                    self.view.canvas_manager.tag_lower(self.view.selle_canvas_ids[fname])

            # Raise selected selle
            self.view.canvas_manager.tag_raise(self.view.selle_canvas_ids[filename])

            # Update transformation controls
            self._update_sliders(self.model.load_selle_properties(filename))

    def _update_sliders(self, props: SelleProperties):
        """Update transformation sliders with selle properties."""
        if hasattr(self.view, 'rotation_slider'):
            self.view.rotation_slider.set(props.angle)
        if hasattr(self.view, 'scale_slider'):
            self.view.scale_slider.set(props.scale)
        if hasattr(self.view, 'selle_x_var'):
            self.view.selle_x_var.set(props.x)
        if hasattr(self.view, 'selle_y_var'):
            self.view.selle_y_var.set(props.y)

    def _bind_selle_events(self, filename: str):
        """Bind mouse events to a selle."""
        canvas_id = self.view.selle_canvas_ids[filename]
        self.view.canvas_manager.tag_bind(
            canvas_id, 
            "<Button-1>", 
            lambda e, fname=filename: self._start_drag(e, fname)
        )
        self.view.canvas_manager.tag_bind(
            canvas_id, 
            "<B1-Motion>", 
            self._do_drag
        )
        self.view.canvas_manager.tag_bind(
            canvas_id, 
            "<ButtonRelease-1>", 
            self._stop_drag
        )

    def _start_drag(self, event, filename: str):
        """Start dragging a selle."""
        self.view.active_selle = filename
        props = self.model.load_selle_properties(filename)
        self.view.drag_offset = (event.x - props.x, event.y - props.y)
        self._select_selle(filename)

    def _do_drag(self, event):
        """Handle dragging motion."""
        if self.view.drag_offset and self.view.active_selle:
            new_x = max(50, min(self.view.canvas_manager.width - 50, event.x - self.view.drag_offset[0]))
            new_y = max(50, min(self.view.canvas_manager.height - 50, event.y - self.view.drag_offset[1]))

            try:
                self.view.canvas_manager.set_coords(
                    self.view.selle_canvas_ids[self.view.active_selle], 
                    new_x, 
                    new_y
                )
            except Exception as e:
                handle_error(e, "Erreur lors du déplacement")

    def _stop_drag(self, event):
        """Stop dragging a selle."""
        if self.view.drag_offset and self.view.active_selle:
            try:
                final_coords = self.view.canvas_manager.coords(self.view.selle_canvas_ids[self.view.active_selle])
                if final_coords:
                    self.model.update_selle_position(
                        self.view.active_selle, 
                        final_coords[0], 
                        final_coords[1]
                    )
            except Exception as e:
                handle_error(e, "Erreur lors de l'enregistrement de la position")

        self.view.drag_offset = None

    def _on_selle_imported(self, file_path: str):
        """Handle selle import event."""
        try:
            if not file_path:
                return

            dest_path = os.path.join(
                self.config.get_selles_folder(self.model.get_current_model_name()), 
                os.path.basename(file_path)
            )

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            with open(file_path, 'rb') as src, open(dest_path, 'wb') as dst:
                dst.write(src.read())

            self._update_selle_menu(os.path.basename(file_path))
            self.model.load_selle_properties(os.path.basename(file_path))

            messagebox.showinfo("Succès", f"Selle importée : {os.path.basename(file_path)}")
        except Exception as e:
            handle_error(e, "Impossible d'importer la selle")

    def _on_selle_renamed(self, old_name: str, new_name: str):
        """Handle selle rename event."""
        try:
            if not old_name or old_name == "(aucune selle)":
                messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
                return

            if not new_name or new_name == old_name:
                return

            old_path = os.path.join(
                self.config.get_selles_folder(self.model.get_current_model_name()), 
                old_name
            )
            new_path = os.path.join(
                self.config.get_selles_folder(self.model.get_current_model_name()), 
                new_name
            )

            os.rename(old_path, new_path)
            self._update_selle_after_rename(old_name, new_name)

            messagebox.showinfo("Succès", f"Selle renommée en {new_name}")
        except Exception as e:
            handle_error(e, "Impossible de renommer la selle")

    def _update_selle_after_rename(self, old_name: str, new_name: str):
        """Update internal data structures after selle rename."""
        if old_name in self.view.selle_canvas_ids:
            self.view.selle_tk_images[new_name] = self.view.selle_tk_images.pop(old_name)
            self.view.selle_canvas_ids[new_name] = self.view.selle_canvas_ids.pop(old_name)
            self.view.canvas_manager.itemconfig(
                self.view.selle_canvas_ids[new_name], 
                tags=("selle", new_name)
            )

            props = self.model.load_selle_properties(old_name)
            props.image = new_name
            self.model.save_selle_properties(new_name, props)

            if old_name in self.model.model_manager.selles_props:
                self.model.model_manager.selles_props[new_name] = self.model.model_manager.selles_props.pop(old_name)
                self.model.model_manager.selles_props[new_name].image = new_name

            if self.view.active_selle == old_name:
                self.view.active_selle = new_name

        self._update_selle_menu(new_name)

    def _on_selle_deleted(self, filename: str):
        """Handle selle deletion event."""
        try:
            if not filename or filename == "(aucune selle)":
                messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
                return

            if messagebox.askyesno("Confirmer", f"Voulez-vous vraiment supprimer {filename} ?"):
                path = os.path.join(
                    self.config.get_selles_folder(self.model.get_current_model_name()), 
                    filename
                )

                os.remove(path)
                self._remove_selle_from_canvas(filename)
                self._update_selle_menu(self._get_selle_files()[0] if self._get_selle_files() else "")

                messagebox.showinfo("Succès", f"Selle {filename} supprimée.")
        except Exception as e:
            handle_error(e, "Impossible de supprimer la selle")

    def _remove_selle_from_canvas(self, selle: str):
        """Remove a selle from the canvas."""
        if selle in self.view.selle_canvas_ids:
            self.view.canvas_manager.delete(self.view.selle_canvas_ids[selle])
            del self.view.selle_canvas_ids[selle]
            del self.view.selle_tk_images[selle]

            if selle in self.model.model_manager.selles_props:
                del self.model.model_manager.selles_props[selle]

            if self.view.active_selle == selle:
                self.view.active_selle = None

    def _on_clear_selles(self):
        """Clear all selles from the canvas."""
        for filename in list(self.view.selle_canvas_ids.keys()):
            self._remove_selle_from_canvas(filename)

        self.model.model_manager.selles_props.clear()

    def _on_show_all_selles(self):
        """Show all available selles."""
        try:
            self._on_clear_selles()

            for filename in self._get_selle_files():
                if filename != "(aucune selle)":
                    props = self.model.load_selle_properties(filename)
                    if props:
                        self._refresh_selle(filename)
        except Exception as e:
            handle_error(e, "Impossible d'afficher toutes les selles")

    def _on_export_canvas(self):
        """Export the canvas content to an image file."""
        try:
            print("Début de l'exportation - Vérification des selles:", len(self.view.selle_canvas_ids), "selles chargées")

            img = Image.new("RGBA", (self.view.canvas_manager.width, self.view.canvas_manager.height), (255, 255, 255, 255))

            bg_path = os.path.join(
                self.config.get_backgrounds_folder(), 
                self.model.model_manager.get_current_model().background
            )

            with Image.open(bg_path) as bg_img:
                bg_img = bg_img.convert("RGBA")
                bg_resized = bg_img.resize(
                    (self.view.canvas_manager.bg_width, self.view.canvas_manager.bg_height), 
                    Image.Resampling.LANCZOS
                )

                offset_x = (self.view.canvas_manager.width - self.view.canvas_manager.bg_width) // 2
                offset_y = (self.view.canvas_manager.height - self.view.canvas_manager.bg_height) // 2

                img.paste(bg_resized, (offset_x, offset_y), bg_resized)

            temp_img = Image.new("RGBA", img.size, (0, 0, 0, 0))

            # Draw teeth
            for filename, obj_id in self.view.teeth_objects.items():
                coords = self.view.canvas_manager.coords(obj_id)
                if not coords:
                    continue

                x, y = coords
                tooth_img = Image.open(os.path.join(self.config.get_teeth_folder(), filename)).convert("RGBA")

                scale, rotation = self.teeth_positions.get(filename, (0, 0, 1.0, 0.0, True))[2:4]
                tooth_img = tooth_img.resize((int(self.dent_size * scale), int(self.dent_size * scale)), Image.Resampling.LANCZOS)
                tooth_img = tooth_img.rotate(rotation, expand=True)

                pos_x = int(x - tooth_img.width // 2)
                pos_y = int(y - tooth_img.height // 2)
                temp_img.alpha_composite(tooth_img, (pos_x, pos_y))

            # Draw selles
            for filename in self.view.selle_canvas_ids:
                props = self.model.load_selle_properties(filename)

                if filename in self.view.selle_tk_images:
                    selle_img = ImageTk.getimage(self.view.selle_tk_images[filename])
                else:
                    path = os.path.join(
                        self.config.get_selles_folder(self.model.get_current_model_name()), 
                        filename
                    )

                    with Image.open(path) as img_selle:
                        selle_img = img_selle.convert("RGBA").resize(
                            (int(img_selle.width * props.scale),
                             int(img_selle.height * props.scale)),
                            Image.Resampling.LANCZOS
                        )
                        selle_img = selle_img.rotate(props.angle, expand=True)

                pos_x = int(props.x - selle_img.width // 2)
                pos_y = int(props.y - selle_img.height // 2)
                temp_img.alpha_composite(selle_img, (pos_x, pos_y))

            img.alpha_composite(temp_img)

            # Generate filename based on missing teeth
            all_teeth = set(self.model.model_manager.get_current_model().teeth)
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

            output_path = os.path.join(
                self.model.json_dir, 
                f"design_{self.model.get_current_model_name()}{missing_str}_{self.view.active_selle or 'sans_nom'}.png"
            )

            img.save(output_path)
            print(f"Exportation terminée - Selles après exportation:", len(self.view.selle_canvas_ids))
            messagebox.showinfo("Succès", f"Design exporté vers {output_path}")
        except Exception as e:
            handle_error(e, "Impossible d'exporter le design")

    def _on_save_to_database(self):
        """Save current configuration to database."""
        try:
            if not self.model.model_manager.selles_props:
                messagebox.showwarning("Avertissement", "Aucune selle à enregistrer.")
                return

            coords_info = []
            for filename, props in self.model.model_manager.selles_props.items():
                coords_info.append(
                    f"{filename}: (x={props.x:.1f}, y={props.y:.1f}, angle={props.angle:.1f}, scale={props.scale:.2f})"
                )

            messagebox.showinfo(
                "Coordonnées des Selles",
                "\n".join(coords_info) + "\n\nUtilisez ces valeurs pour remplir la base de données manuellement."
            )
        except Exception as e:
            handle_error(e, "Impossible d'afficher les coordonnées")

    def create_undo_redo_system(self):
        """Create an undo/redo system for the application."""
        self.undo_stack = deque(maxlen=self.config.undo_redo_max_size)
        self.redo_stack = deque(maxlen=self.config.undo_redo_max_size)

    def save_state(self):
        """Save current state for undo functionality."""
        self.undo_stack.append({k: v.to_dict() for k, v in self.model.model_manager.selles_props.items()})
        self.redo_stack.clear()

    def undo(self):
        """Undo the last action."""
        if not self.undo_stack:
            return False

        self.redo_stack.append({k: v.to_dict() for k, v in self.model.model_manager.selles_props.items()})
        state = self.undo_stack.pop()

        self.model.model_manager.selles_props.clear()
        for filename, props_dict in state.items():
            self.model.model_manager.selles_props[filename] = SelleProperties.from_dict(props_dict)

        # Refresh UI
        for filename in self.view.selle_canvas_ids:
            self._refresh_selle(filename)

        if self.view.active_selle:
            self._select_selle(self.view.active_selle)

        return True

    def redo(self):
        """Redo the last undone action."""
        if not self.redo_stack:
            return False

        self.undo_stack.append({k: v.to_dict() for k, v in self.model.model_manager.selles_props.items()})
        state = self.redo_stack.pop()

        self.model.model_manager.selles_props.clear()
        for filename, props_dict in state.items():
            self.model.model_manager.selles_props[filename] = SelleProperties.from_dict(props_dict)

        # Refresh UI
        for filename in self.view.selle_canvas_ids:
            self._refresh_selle(filename)

        if self.view.active_selle:
            self._select_selle(self.view.active_selle)

        return True

    def clear_history(self):
        """Clear undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
