
"""
View Component for MVC Architecture

This module contains the UI components and views for the dental design application.
"""

import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from PIL import Image, ImageTk, ImageOps
from typing import Dict, Tuple, Set, Optional, List, Callable
from ..ui_components import UIComponent, CanvasManager
from ..config import get_config
from ..error_handler import handle_error, ImageProcessingError

class DentalDesignView:
    """Main view class for the dental design application."""

    def __init__(self, root: tk.Tk):
        """Initialize the dental design view.

        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.config = get_config()

        # Set up window properties
        self.root.title(self.config.window_title)
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.root.minsize(self.config.window_min_width, self.config.window_min_height)

        # Initialize UI components
        self.main_frame = None
        self.controls_frame = None
        self.canvas_frame = None
        self.canvas_manager = None

        # Image and object dictionaries
        self.selle_tk_images: Dict[str, ImageTk.PhotoImage] = {}
        self.selle_canvas_ids: Dict[str, int] = {}
        self.teeth_images: Dict[str, ImageTk.PhotoImage] = {}
        self.teeth_objects: Dict[str, int] = {}
        self.selected_teeth: Set[str] = set()

        # UI state
        self.teeth_frame = None
        self.active_selle: Optional[str] = None
        self.drag_offset: Optional[Tuple[float, float]] = None

        # Callbacks
        self.callbacks = {}

        # Set up the UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the main user interface."""
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create controls frame
        self.controls_frame = UIComponent(self.main_frame, "Contrôles").frame
        self.controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Create canvas frame
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create canvas manager
        self.canvas_manager = CanvasManager(self.canvas_frame)
        self.canvas_manager.bind_resize(self._on_canvas_resize)

    def register_callback(self, event_name: str, callback: Callable):
        """Register a callback for a specific event.

        Args:
            event_name: Name of the event
            callback: Function to call when the event occurs
        """
        if event_name not in self.callbacks:
            self.callbacks[event_name] = []
        self.callbacks[event_name].append(callback)

    def trigger_callback(self, event_name: str, *args, **kwargs):
        """Trigger all callbacks for a specific event.

        Args:
            event_name: Name of the event
            *args: Arguments to pass to the callback
            **kwargs: Keyword arguments to pass to the callback
        """
        if event_name in self.callbacks:
            for callback in self.callbacks[event_name]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    handle_error(e, f"Error in callback for {event_name}")

    def _on_canvas_resize(self, event):
        """Handle canvas resize events."""
        if event.width < 100 or event.height < 100:
            return

        self.canvas_manager.width = event.width
        self.canvas_manager.height = event.height

        # Trigger resize callback
        self.trigger_callback("canvas_resized", event.width, event.height)

    def set_model_type(self, model_type: str):
        """Set the current dental arch model type.

        Args:
            model_type: Type of dental arch model
        """
        self.trigger_callback("model_changed", model_type)

    def create_model_selector(self, models: List[str]):
        """Create a model selector UI element.

        Args:
            models: List of available model names
        """
        modele_frame = UIComponent(self.controls_frame, "Type d'Arcade").frame
        modele_frame.pack(fill=tk.X, pady=10)

        self.model_var = tk.StringVar(value=models[0] if models else "")
        self.model_menu = tk.OptionMenu(
            modele_frame, 
            self.model_var, 
            *models, 
            command=lambda value: self.set_model_type(value)
        )
        self.model_menu.pack(fill=tk.X)

    def create_teeth_buttons(self, teeth_positions: Dict[str, Tuple[float, float, float, float, bool]]):
        """Create buttons for controlling teeth visibility.

        Args:
            teeth_positions: Dictionary of tooth positions and visibility
        """
        if self.teeth_frame:
            self.teeth_frame.destroy()

        self.teeth_frame = UIComponent(self.controls_frame, "Contrôle des Dents").frame
        self.teeth_frame.pack(fill=tk.X, pady=5)

        buttons_frame = tk.Frame(self.teeth_frame)
        buttons_frame.pack()

        for filename in sorted(teeth_positions.keys(), key=lambda x: x.split('_')[1]):
            num = filename.split('.')[0].split('_')[1]
            if num not in ['18', '28', '38', '48']:
                present = teeth_positions[filename][4]
                btn = tk.Button(
                    buttons_frame, 
                    text=num, 
                    width=4, 
                    bg="green" if present else "red", 
                    fg="white",
                    command=lambda f=filename: self.toggle_tooth(f)
                )
                btn.pack(side=tk.LEFT, padx=2)

        global_frame = tk.Frame(self.teeth_frame)
        global_frame.pack(pady=5)

        tk.Button(
            global_frame, 
            text="Tout Afficher", 
            command=self.display_all_teeth
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            global_frame, 
            text="Tout Masquer", 
            command=self.hide_all_teeth
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            global_frame, 
            text="Afficher Positions", 
            command=self.show_teeth_positions
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            global_frame, 
            text="Exporter Arcade PNG", 
            command=self.export_canvas
        ).pack(side=tk.LEFT, padx=2)

    def toggle_tooth(self, filename: str):
        """Toggle the visibility of a tooth.

        Args:
            filename: Name of the tooth image file
        """
        self.trigger_callback("tooth_toggled", filename)

    def display_all_teeth(self):
        """Display all teeth."""
        self.trigger_callback("display_all_teeth")

    def hide_all_teeth(self):
        """Hide all teeth."""
        self.trigger_callback("hide_all_teeth")

    def show_teeth_positions(self):
        """Show the positions of all teeth."""
        positions = []
        for filename, obj_id in self.teeth_objects.items():
            coords = self.canvas_manager.coords(obj_id)
            if coords:
                positions.append(f"{filename}: ({coords[0]:.1f}, {coords[1]:.1f})")

        if positions:
            messagebox.showinfo("Positions des Dents", "\n".join(positions))
        else:
            messagebox.showwarning("Aucune Dent Visible", "Aucune dent affichée.")

    def create_selle_controls(self, selle_files: List[str]):
        """Create controls for dental saddles.

        Args:
            selle_files: List of available dental saddle files
        """
        selle_frame = UIComponent(self.controls_frame, "Gestion des Selles").frame
        selle_frame.pack(fill=tk.X, pady=10)

        self.selected_selle = tk.StringVar(value=selle_files[0] if selle_files else "")
        tk.Label(selle_frame, text="Sélectionner une selle :").pack(anchor=tk.W)

        self.selle_menu = tk.OptionMenu(
            selle_frame, 
            self.selected_selle, 
            *selle_files, 
            command=lambda filename: self.load_selle(filename)
        )
        self.selle_menu.pack(fill=tk.X)

        manage_frame = tk.Frame(selle_frame)
        manage_frame.pack(fill=tk.X, pady=5)

        tk.Button(
            manage_frame, 
            text="Importer", 
            command=self.import_selle
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            manage_frame, 
            text="Renommer", 
            command=self.rename_selle
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            manage_frame, 
            text="Supprimer", 
            command=self.delete_selle
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            manage_frame, 
            text="Effacer les Selles", 
            command=self.clear_selle
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            manage_frame, 
            text="Afficher Toutes les Selles", 
            command=self.show_all_selles
        ).pack(side=tk.LEFT, padx=2)

    def load_selle(self, filename: str):
        """Load a dental saddle.

        Args:
            filename: Name of the dental saddle file
        """
        self.trigger_callback("selle_loaded", filename)

    def import_selle(self):
        """Import a new dental saddle."""
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if file_path:
            self.trigger_callback("selle_imported", file_path)

    def rename_selle(self):
        """Rename the selected dental saddle."""
        current_selle = self.selected_selle.get()
        if not current_selle or current_selle == "(aucune selle)":
            messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
            return

        new_name = simpledialog.askstring(
            "Renommer", 
            "Nouveau nom pour la selle :", 
            initialvalue=current_selle
        )

        if new_name and new_name != current_selle:
            self.trigger_callback("selle_renamed", current_selle, new_name)

    def delete_selle(self):
        """Delete the selected dental saddle."""
        current_selle = self.selected_selle.get()
        if not current_selle or current_selle == "(aucune selle)":
            messagebox.showwarning("Avertissement", "Aucune selle sélectionnée.")
            return

        if messagebox.askyesno("Confirmer", f"Voulez-vous vraiment supprimer {current_selle} ?"):
            self.trigger_callback("selle_deleted", current_selle)

    def clear_selle(self):
        """Clear all dental saddles from the canvas."""
        self.trigger_callback("clear_selles")

    def show_all_selles(self):
        """Show all available dental saddles."""
        self.trigger_callback("show_all_selles")

    def create_transformation_controls(self):
        """Create controls for transforming dental saddles."""
        transform_frame = UIComponent(self.controls_frame, "Transformations").frame
        transform_frame.pack(fill=tk.X, pady=10)

        tk.Button(
            transform_frame, 
            text="💾 Enregistrer Configuration", 
            command=self.save_to_database,
            bg="#4CAF50", 
            fg="white",
            font=("Arial", 12, "bold"), 
            pady=8
        ).pack(fill=tk.X, pady=(0, 10), padx=5)

        self._setup_selle_sliders(transform_frame)
        self._setup_flip_buttons(transform_frame)
        self._setup_undo_redo_buttons(transform_frame)

        tk.Button(
            transform_frame, 
            text="Exporter en PNG", 
            command=self.export_canvas,
            bg="#2196F3", 
            fg="white"
        ).pack(fill=tk.X, pady=5, padx=5)

    def _setup_selle_sliders(self, parent):
        """Set up sliders for dental saddle transformations.

        Args:
            parent: Parent widget for the sliders
        """
        selle_frame = tk.Frame(parent)
        selle_frame.pack(fill=tk.X, pady=5)

        self.selle_x_var = tk.DoubleVar(value=0)
        self.selle_x_slider = tk.Scale(
            selle_frame, 
            from_=-200, 
            to=800, 
            orient=tk.HORIZONTAL, 
            variable=self.selle_x_var,
            command=lambda _: self.move_selle()
        )
        tk.Label(selle_frame, text="Décalage X (Selle) :").pack(side=tk.LEFT, padx=5)
        self.selle_x_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        self.selle_y_var = tk.DoubleVar(value=0)
        self.selle_y_slider = tk.Scale(
            selle_frame, 
            from_=-200, 
            to=600, 
            orient=tk.HORIZONTAL, 
            variable=self.selle_y_var,
            command=lambda _: self.move_selle()
        )
        tk.Label(selle_frame, text="Décalage Y (Selle) :").pack(side=tk.LEFT, padx=5)
        self.selle_y_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        self.rotation_slider = tk.Scale(
            selle_frame, 
            from_=-180, 
            to=180, 
            orient=tk.HORIZONTAL,
            command=lambda _: self.apply_transform()
        )
        tk.Label(selle_frame, text="Rotation (°) :").pack(side=tk.LEFT, padx=5)
        self.rotation_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        self.scale_slider = tk.Scale(
            selle_frame, 
            from_=0.3, 
            to=2.0, 
            resolution=0.01, 
            orient=tk.HORIZONTAL,
            command=lambda _: self.apply_transform()
        )
        self.scale_slider.set(1.0)
        tk.Label(selle_frame, text="Échelle :").pack(side=tk.LEFT, padx=5)
        self.scale_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

    def _setup_flip_buttons(self, parent):
        """Set up buttons for flipping dental saddles.

        Args:
            parent: Parent widget for the buttons
        """
        flip_frame = tk.Frame(parent)
        flip_frame.pack(fill=tk.X, pady=5)

        tk.Button(
            flip_frame, 
            text="Retourner Horizontalement", 
            command=self.flip_x
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        tk.Button(
            flip_frame, 
            text="Retourner Verticalement", 
            command=self.flip_y
        ).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def _setup_undo_redo_buttons(self, parent):
        """Set up undo and redo buttons.

        Args:
            parent: Parent widget for the buttons
        """
        undo_frame = tk.Frame(parent)
        undo_frame.pack(fill=tk.X, pady=5)

        tk.Button(
            undo_frame, 
            text="↩ Annuler (Ctrl+Z)", 
            command=self.undo
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        tk.Button(
            undo_frame, 
            text="↪ Rétablir (Ctrl+Y)", 
            command=self.redo
        ).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def apply_transform(self):
        """Apply transformation to the active dental saddle."""
        self.trigger_callback("transform_applied")

    def flip_x(self):
        """Flip the active dental saddle horizontally."""
        self.trigger_callback("flip_x")

    def flip_y(self):
        """Flip the active dental saddle vertically."""
        self.trigger_callback("flip_y")

    def move_selle(self):
        """Move the active dental saddle."""
        self.trigger_callback("move_selle")

    def undo(self):
        """Undo the last action."""
        self.trigger_callback("undo")

    def redo(self):
        """Redo the last undone action."""
        self.trigger_callback("redo")

    def save_to_database(self):
        """Save the current configuration to the database."""
        self.trigger_callback("save_to_database")

    def export_canvas(self):
        """Export the canvas as a PNG image."""
        self.trigger_callback("export_canvas")

    def display_tooth(self, filename: str, x: float, y: float, scale: float, rotation: float):
        """Display a tooth on the canvas.

        Args:
            filename: Name of the tooth image file
            x: X coordinate
            y: Y coordinate
            scale: Scale factor
            rotation: Rotation angle in degrees
        """
        try:
            img = Image.open(os.path.join(self.config.get_teeth_folder(), filename)).convert("RGBA")
            img = img.resize((int(self.config.default_dent_size * scale), int(self.config.default_dent_size * scale)), Image.Resampling.LANCZOS)
            img = img.rotate(rotation, expand=True, resample=Image.BICUBIC)

            self.teeth_images[filename] = ImageTk.PhotoImage(img)
            img_id = self.canvas_manager.create_image(
                x, y, 
                image=self.teeth_images[filename], 
                tags=("tooth", filename), 
                anchor=tk.CENTER
            )
            self.teeth_objects[filename] = img_id

            # Bind events
            self.canvas_manager.tag_bind(img_id, "<Button-1>", lambda e, fname=filename: self.select_tooth(fname))
        except Exception as e:
            handle_error(e, f"Erreur lors de l'affichage de la dent {filename}", show_traceback=True)

    def hide_tooth(self, filename: str):
        """Hide a tooth from the canvas.

        Args:
            filename: Name of the tooth image file
        """
        if filename in self.teeth_objects:
            self.canvas_manager.delete(self.teeth_objects[filename])
            del self.teeth_objects[filename]
            self.selected_teeth.discard(filename)

    def select_tooth(self, filename: str):
        """Select a tooth.

        Args:
            filename: Name of the tooth image file
        """
        self.trigger_callback("tooth_selected", filename)

    def display_selle(self, filename: str, x: float, y: float, angle: float, scale: float, flip_x: bool, flip_y: bool):
        """Display a dental saddle on the canvas.

        Args:
            filename: Name of the dental saddle image file
            x: X coordinate
            y: Y coordinate
            angle: Rotation angle in degrees
            scale: Scale factor
            flip_x: Whether to flip horizontally
            flip_y: Whether to flip vertically
        """
        try:
            img = self._load_transformed_selle_image(filename, angle, scale, flip_x, flip_y)
            if img:
                self.selle_tk_images[filename] = ImageTk.PhotoImage(img)
                img_id = self.canvas_manager.create_image(
                    x, y, 
                    image=self.selle_tk_images[filename], 
                    tags=("selle", filename), 
                    anchor=tk.CENTER
                )
                self.selle_canvas_ids[filename] = img_id

                # Bind events
                self.canvas_manager.tag_bind(img_id, "<Button-1>", lambda e, fname=filename: self.select_selle(fname))
                self.canvas_manager.tag_bind(img_id, "<B1-Motion>", lambda e, fname=filename: self.drag_selle(e, fname))
                self.canvas_manager.tag_bind(img_id, "<ButtonRelease-1>", lambda e: self.stop_drag())
        except Exception as e:
            handle_error(e, f"Erreur lors de l'affichage de la selle {filename}", show_traceback=True)

    def _load_transformed_selle_image(self, filename: str, angle: float, scale: float, flip_x: bool, flip_y: bool) -> Optional[Image.Image]:
        """Load and transform a dental saddle image.

        Args:
            filename: Name of the dental saddle image file
            angle: Rotation angle in degrees
            scale: Scale factor
            flip_x: Whether to flip horizontally
            flip_y: Whether to flip vertically

        Returns:
            Transformed image or None if an error occurred
        """
        try:
            model = self.model_manager.get_current_model()
            selle_folder = self.config.get_selles_folder(model.name)
            path = os.path.join(selle_folder, filename)

            if not os.path.exists(path):
                print(f"Fichier non trouvé: {path}")
                return None

            with Image.open(path) as img:
                img = img.copy().convert("RGBA")

                if flip_x:
                    img = ImageOps.mirror(img)
                if flip_y:
                    img = ImageOps.flip(img)

                w, h = img.size
                img = img.resize((int(w * scale), int(h * scale)), getattr(Image.Resampling, self.config.image_resampling_method))
                img = img.rotate(angle, expand=True, resample=Image.BICUBIC)

                return img
        except Exception as e:
            handle_error(e, f"Erreur lors du chargement de {path}", show_traceback=True)
            return None

    def select_selle(self, filename: str):
        """Select a dental saddle.

        Args:
            filename: Name of the dental saddle image file
        """
        self.active_selle = filename

        # Raise selected selle to top
        for fname in self.selle_canvas_ids:
            if fname != filename:
                self.canvas_manager.tag_lower(self.selle_canvas_ids[fname])
        self.canvas_manager.tag_raise(self.selle_canvas_ids[filename])

        # Update sliders with selected selle properties
        self.update_sliders_for_selle(filename)

        self.trigger_callback("selle_selected", filename)

    def update_sliders_for_selle(self, filename: str):
        """Update slider values for a selected dental saddle.

        Args:
            filename: Name of the dental saddle image file
        """
        # This method would need to get the properties of the selected selle
        # and update the slider values accordingly
        pass

    def drag_selle(self, event, filename: str):
        """Drag a dental saddle.

        Args:
            event: Mouse event
            filename: Name of the dental saddle image file
        """
        if filename not in self.selle_canvas_ids:
            return

        # Calculate new position
        new_x = max(50, min(self.canvas_manager.width - 50, event.x))
        new_y = max(50, min(self.canvas_manager.height - 50, event.y))

        # Update position
        self.canvas_manager.set_coords(self.selle_canvas_ids[filename], new_x, new_y)

    def stop_drag(self):
        """Stop dragging a dental saddle."""
        if self.active_selle and self.active_selle in self.selle_canvas_ids:
            final_coords = self.canvas_manager.coords(self.selle_canvas_ids[self.active_selle])
            if final_coords:
                self.trigger_callback("selle_moved", self.active_selle, final_coords[0], final_coords[1])

    def update_sliders(self, props):
        """Update slider values with the given properties.

        Args:
            props: Properties object containing values for sliders
        """
        if hasattr(self, 'rotation_slider'):
            self.rotation_slider.set(props.angle)
        if hasattr(self, 'scale_slider'):
            self.scale_slider.set(props.scale)
        if hasattr(self, 'selle_x_var'):
            self.selle_x_var.set(props.x)
        if hasattr(self, 'selle_y_var'):
            self.selle_y_var.set(props.y)

    def load_background(self, background_file: str):
        """Load a background image for the canvas.

        Args:
            background_file: Name of the background image file
        """
        try:
            bg_path = os.path.join(self.config.get_backgrounds_folder(), background_file)
            with Image.open(bg_path) as img:
                img_copy = img.copy()
                self._resize_background(img_copy)
                resized_img = img_copy.resize(
                    (self.canvas_manager.bg_width, self.canvas_manager.bg_height), 
                    getattr(Image.Resampling, self.config.image_resampling_method)
                )

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

                # Trigger background loaded callback
                self.trigger_callback("background_loaded")
        except Exception as e:
            handle_error(e, f"Erreur lors du chargement du fond {background_file}", show_traceback=True)

    def _resize_background(self, img: Image.Image):
        """Resize the background image to fit the canvas.

        Args:
            img: PIL Image object to resize
        """
        self.canvas_manager.original_bg_width, self.canvas_manager.original_bg_height = img.width, img.height

        max_width = self.config.max_image_width
        img_ratio = img.width / img.height
        new_width = min(img.width, max_width)
        new_height = int(new_width / img_ratio)

        if new_height > self.canvas_manager.height:
            new_height = self.canvas_manager.height
            new_width = int(new_height * img_ratio)

        self.canvas_manager.bg_scale_factor = new_width / self.canvas_manager.original_bg_width
        self.canvas_manager.bg_width, self.canvas_manager.bg_height = new_width, new_height

    def clear_canvas(self):
        """Clear all items from the canvas."""
        self.canvas_manager.delete("all")
        self.teeth_objects.clear()
        self.selle_canvas_ids.clear()
        self.teeth_images.clear()

    def remove_selle(self, filename: str):
        """Remove a dental saddle from the canvas.

        Args:
            filename: Name of the dental saddle image file
        """
        if filename in self.selle_canvas_ids:
            self.canvas_manager.delete(self.selle_canvas_ids[filename])
            del self.selle_canvas_ids[filename]
            del self.selle_tk_images[filename]
            if self.active_selle == filename:
                self.active_selle = None

    def update_selle_menu(self, selected: str, selle_files: List[str]):
        """Update the dental saddle selection menu.

        Args:
            selected: Currently selected dental saddle
            selle_files: List of available dental saddle files
        """
        self.selle_menu["menu"].delete(0, "end")
        for f in selle_files:
            self.selle_menu["menu"].add_command(label=f, command=tk._setit(self.selected_selle, f))
        self.selected_selle.set(selected)

    def show_help(self):
        """Show the help dialog."""
        messagebox.showinfo(
            "Guide de l'Utilisateur", 
            "1. Sélectionnez un type d'arcade\n2.Choisissez une selle\n3. Ajustez position/rotation/échelle\n4. Enregistrez\n\nRaccourcis :\nCtrl+Z: Annuler\nCtrl+Y: Rétablir\nCtrl+S: Enregistrer"
        )

    def show_about(self):
        """Show the about dialog."""
        messagebox.showinfo(
            "À Propos", 
            "Conception d'Arcades Dentaires - PFE\nVersion 2.0\n\nDéveloppé pour le projet de fin d'études."
        )

    def create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Actualiser", command=self.refresh)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Guide de l'Utilisateur", command=self.show_help)
        help_menu.add_command(label="À Propos", command=self.show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)

        self.root.config(menu=menubar)

    def refresh(self):
        """Refresh the application."""
        self.trigger_callback("refresh")

    def export_canvas_to_file(self, output_path: str):
        """Export the canvas to a file.

        Args:
            output_path: Path to save the exported image
        """
        try:
            print(f"Exporting canvas to {output_path}")

            # Create a new image with the canvas size
            img = Image.new("RGBA", (self.canvas_manager.width, self.canvas_manager.height), (255, 255, 255, 255))

            # Get the current model
            model = self.model_manager.get_current_model()

            # Draw background
            bg_path = os.path.join(self.config.get_backgrounds_folder(), model.background)
            with Image.open(bg_path) as bg_img:
                bg_img = bg_img.convert("RGBA")
                bg_resized = bg_img.resize((self.canvas_manager.bg_width, self.canvas_manager.bg_height), getattr(Image.Resampling, self.config.image_resampling_method))

                offset_x = (self.canvas_manager.width - self.canvas_manager.bg_width) // 2
                offset_y = (self.canvas_manager.height - self.canvas_manager.bg_height) // 2
                img.paste(bg_resized, (offset_x, offset_y), bg_resized)

            # Create a temporary image for compositing teeth and selles
            temp_img = Image.new("RGBA", img.size, (0, 0, 0, 0))

            # Draw teeth
            for filename, obj_id in self.teeth_objects.items():
                coords = self.canvas_manager.coords(obj_id)
                if not coords:
                    continue

                x, y = coords
                tooth_img = Image.open(os.path.join(self.config.get_teeth_folder(), filename)).convert("RGBA")

                # Get tooth properties
                tooth_props = None  # This would need to be retrieved from the model
                if tooth_props:
                    scale, rotation = tooth_props.scale, tooth_props.rotation
                    tooth_img = tooth_img.resize((int(self.config.default_dent_size * scale), int(self.config.default_dent_size * scale)), getattr(Image.Resampling, self.config.image_resampling_method))
                    tooth_img = tooth_img.rotate(rotation, expand=True)

                pos_x = int(x - tooth_img.width // 2)
                pos_y = int(y - tooth_img.height // 2)
                temp_img.alpha_composite(tooth_img, (pos_x, pos_y))

            # Draw selles
            for filename in self.selle_canvas_ids:
                # Get selle properties from the model
                selle_props = None  # This would need to be retrieved from the model
                if selle_props:
                    if filename in self.selle_tk_images:
                        selle_img = ImageTk.getimage(self.selle_tk_images[filename])
                    else:
                        selle_img = self._load_transformed_selle_image(
                            filename, 
                            selle_props.angle, 
                            selle_props.scale, 
                            selle_props.flip_x, 
                            selle_props.flip_y
                        )

                    if selle_img:
                        pos_x = int(selle_props.x - selle_img.width // 2)
                        pos_y = int(selle_props.y - selle_img.height // 2)
                        temp_img.alpha_composite(selle_img, (pos_x, pos_y))

            # Composite the temporary image onto the main image
            img.alpha_composite(temp_img)

            # Save the image
            img.save(output_path, quality=self.config.export_quality)
            print(f"Export completed successfully")

            # Show success message
            messagebox.showinfo("Succès", f"Design exporté vers {output_path}")
        except Exception as e:
            handle_error(e, "Impossible d'exporter le design", show_traceback=True)
