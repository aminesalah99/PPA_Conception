"""
Dental Design Application - Main Entry Point

This module implements the main application using the MVC (Model-View-Controller) pattern.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from mvc.model import DentalDesignModel
from mvc.view import DentalDesignView
from mvc.controller import DentalDesignController
from config import get_config
from error_handler import handle_error

class DentalDesignApp:
    """Main application class that integrates the MVC components."""

    def __init__(self, root: tk.Tk, model_type: str = 'arcade_inf'):
        """Initialize the dental design application.

        Args:
            root: The root Tkinter window
            model_type: Type of dental arch model to initialize
        """
        self.root = root
        self.model_type = model_type

        # Get configuration
        self.config = get_config()

        # Initialize MVC components
        self._initialize_mvc()

        # Set up UI
        self._setup_ui()

        # Bind keyboard shortcuts
        self._bind_shortcuts()

    def _initialize_mvc(self):
        """Initialize the MVC components."""
        # Get paths from configuration
        image_folder = self.config.get_image_folder()
        json_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elements_valides")

        # Create model
        self.model = DentalDesignModel(image_folder, json_dir)
        self.model.set_current_model(self.model_type)

        # Create view
        self.view = DentalDesignView(self.root)

        # Create controller
        self.controller = DentalDesignController(self.root, self.model, self.view)

    def _setup_ui(self):
        """Set up the user interface."""
        # Create main menu
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

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.root.bind("<Control-z>", lambda e: self.controller.undo())
        self.root.bind("<Control-y>", lambda e: self.controller.redo())
        self.root.bind("<Control-s>", lambda e: self.controller.save_to_database())

    def _refresh(self):
        """Refresh the application."""
        try:
            self.controller.refresh()
        except Exception as e:
            handle_error(e, "Erreur lors du rafraîchissement")

    def _show_help(self):
        """Show help information."""
        messagebox.showinfo(
            "Guide de l'Utilisateur", 
            "1. Sélectionnez un type d'arcade\n2. Choisissez une selle\n3. Ajustez position/rotation/échelle\n4. Enregistrez\n\nRaccourcis :\nCtrl+Z: Annuler\nCtrl+Y: Rétablir\nCtrl+S: Enregistrer"
        )

    def _show_about(self):
        """Show about information."""
        messagebox.showinfo(
            "À Propos", 
            "Conception d'Arcades Dentaires - PFE\nVersion 2.0\n\nDéveloppé pour le projet de fin d'études."
        )

class InferiorDentalApp(DentalDesignApp):
    """Application for designing inferior dental arches."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the inferior dental arch application.
        
        Args:
            root: The root Tkinter window
        """
        super().__init__(root, model_type="arcade_inf")
        self.root.title("Conception d'Arcade Dentaire Inférieure - PFE")


class SuperiorDentalApp(DentalDesignApp):
    """Application for designing superior dental arches."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the superior dental arch application.
        
        Args:
            root: The root Tkinter window
        """
        super().__init__(root, model_type="arcade_sup")
        self.root.title("Conception d'Arcade Dentaire Supérieure - PFE")

class DentalAppLauncher:
    """Launcher for the dental design applications."""

    def __init__(self, root):
        """Initialize the dental app launcher."""
        self.root = root
        self.root.title("Conception d'Arcades Dentaires - PFE")
        self.root.geometry("800x700")
        self.root.minsize(800, 700)
        self.root.configure(bg="#f8f9fa")
        self.root.resizable(True, True)

        # Set up styles
        self.setup_styles()

        # Create main frame with gradient background
        self.main_frame = tk.Frame(self.root, bg="#f8f9fa")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Create header
        self.create_header()

        # Create content
        self.create_content()

        # Create footer
        self.create_footer()

    def setup_styles(self):
        """Configure ttk styles for a modern look."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure button style with gradient effect
        style.configure('Title.TLabel', font=('Segoe UI', 28, 'bold'), background="#f8f9fa", foreground="#2c3e50")
        style.configure('Subtitle.TLabel', font=('Segoe UI', 14), background="#f8f9fa", foreground="#7f8c8d")
        style.configure('Description.TLabel', font=('Segoe UI', 11), background="#ffffff", foreground="#34495e", wraplength=250)
        style.configure('Action.TButton', font=('Segoe UI', 12, 'bold'), padding=12)
        style.map('Action.TButton',
                 background=[('active', '#3498db'), ('!disabled', '#ecf0f1')],
                 foreground=[('active', 'white'), ('!disabled', '#7f8c8d')])

        # Configure card frame style
        style.configure('Card.TFrame', background='#ffffff', relief='flat', borderwidth=0)

        # Configure footer label style
        style.configure('Footer.TLabel', font=('Segoe UI', 10), background="#f8f9fa", foreground="#95a5a6")

    def create_header(self):
        """Create the header section with title and subtitle."""
        header_frame = tk.Frame(self.main_frame, bg="#f8f9fa")
        header_frame.pack(fill=tk.X, pady=(0, 40))

        # Add logo placeholder (you can replace with an actual logo)
        logo_frame = tk.Frame(header_frame, bg="#3498db", width=60, height=60)
        logo_frame.pack(side=tk.LEFT, padx=(0, 20))
        logo_frame.pack_propagate(False)

        tk.Label(
            logo_frame, 
            text="CD", 
            bg="#3498db", 
            fg="white",
            font=("Segoe UI", 24, "bold")
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Title and subtitle container
        text_container = tk.Frame(header_frame, bg="#f8f9fa")
        text_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(text_container, text="Conception d'Arcades Dentaires", style='Title.TLabel')
        title_label.pack(anchor=tk.W, pady=(0, 5))

        # Subtitle
        subtitle_label = ttk.Label(text_container, text="Système de conception prothétique dentaire", style='Subtitle.TLabel')
        subtitle_label.pack(anchor=tk.W)

    def create_content(self):
        """Create the main content with arcade selection cards."""
        content_frame = tk.Frame(self.main_frame, bg="#f8f9fa")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Create a frame for the cards with better spacing
        cards_frame = tk.Frame(content_frame, bg="#f8f9fa")
        cards_frame.pack(expand=True)

        # Create cards for each arcade type with enhanced design
        self.create_arcade_card(
            cards_frame,
            "Arcade Supérieure",
            "Conception d'arcades dentaires supérieures avec précision et efficacité",
            self.launch_superior,
            0,
            "Dentition supérieure"
        )

        self.create_arcade_card(
            cards_frame,
            "Arcade Inférieure",
            "Conception d'arcades dentaires inférieures adaptées à chaque patient",
            self.launch_inferior,
            1,
            "Dentition inférieure"
        )

    def create_arcade_card(self, parent, title, description, command, column, image_alt):
        """Create a card for an arcade type with enhanced design."""
        # Create card container with shadow effect
        card_container = tk.Frame(parent, bg="#ecf0f1", highlightthickness=0)
        card_container.grid(row=0, column=column, padx=15, pady=15, sticky="nsew")

        # Create inner card with white background
        card = ttk.Frame(card_container, style='Card.TFrame', padding=25)
        card.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Configure grid weights for responsive design
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # Image placeholder frame (you can replace with actual images)
        image_frame = tk.Frame(card, bg="#3498db", width=200, height=120)
        image_frame.pack(pady=(0, 20))
        image_frame.pack_propagate(False)

        # Image placeholder text
        tk.Label(
            image_frame, 
            text=image_alt, 
            bg="#3498db", 
            fg="white",
            font=("Segoe UI", 14)
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Card title
        title_label = ttk.Label(card, text=title, font=('Segoe UI', 18, 'bold'))
        title_label.pack(pady=(0, 15))

        # Card description
        desc_label = ttk.Label(card, text=description, style='Description.TLabel')
        desc_label.pack(pady=(0, 25))

        # Card action button with icon
        button_frame = tk.Frame(card, bg="#ffffff")
        button_frame.pack(fill=tk.X)

        action_btn = ttk.Button(
            button_frame,
            text="Lancer l'application →",
            style='Action.TButton',
            command=command
        )
        action_btn.pack(side=tk.RIGHT)

        # Add enhanced hover effect
        self.add_hover_effect(card_container, card, action_btn)

    def add_hover_effect(self, card_container, card, button):
        """Add enhanced hover effects to the card and button."""
        def on_enter(e):
            card_container.configure(bg="#d5dbdb")
            button.configure(style='Hover.TButton')

        def on_leave(e):
            card_container.configure(bg="#ecf0f1")
            button.configure(style='Action.TButton')

        # Configure hover button style
        style = ttk.Style()
        style.configure('Hover.TButton', font=('Segoe UI', 12, 'bold'), padding=12)
        style.map('Hover.TButton',
                 background=[('active', '#2980b9'), ('!disabled', '#2980b9')],
                 foreground=[('active', 'white'), ('!disabled', 'white')])

        card_container.bind("<Enter>", on_enter)
        card_container.bind("<Leave>", on_leave)
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    def create_footer(self):
        """Create the footer with information and links."""
        footer_frame = tk.Frame(self.main_frame, bg="#f8f9fa")
        footer_frame.pack(fill=tk.X, pady=(30, 0))

        # Add separator line
        separator = ttk.Separator(footer_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 15))

        # Footer content
        footer_content = tk.Frame(footer_frame, bg="#f8f9fa")
        footer_content.pack(fill=tk.X)

        # Version info
        version_label = ttk.Label(footer_content, text="Version 2.0 - PFE", style='Footer.TLabel')
        version_label.pack(side=tk.LEFT)

        # Navigation links (placeholder for future features)
        links_frame = tk.Frame(footer_content, bg="#f8f9fa")
        links_frame.pack(side=tk.RIGHT)

        help_link = ttk.Label(links_frame, text="Aide", style='Footer.TLabel', cursor="hand2")
        help_link.pack(side=tk.LEFT, padx=(0, 15))

        about_link = ttk.Label(links_frame, text="À propos", style='Footer.TLabel', cursor="hand2")
        about_link.pack(side=tk.LEFT, padx=(0, 15))

        contact_link = ttk.Label(links_frame, text="Contact", style='Footer.TLabel', cursor="hand2")
        contact_link.pack(side=tk.LEFT)

        # Copyright info
        copyright_label = ttk.Label(footer_content, text="© 2025 - Tous droits réservés", style='Footer.TLabel')
        copyright_label.pack(side=tk.RIGHT)

    def launch_superior(self):
        """Launch the superior arcade application."""
        try:
            self.root.destroy()
            new_root = tk.Tk()
            app = SuperiorDentalApp(new_root)
            new_root.mainloop()
        except Exception as e:
            handle_error(e, "Impossible de lancer l'application Arcade Supérieure")

    def launch_inferior(self):
        """Launch the inferior arcade application."""
        try:
            self.root.destroy()
            new_root = tk.Tk()
            app = InferiorDentalApp(new_root)
            new_root.mainloop()
        except Exception as e:
            handle_error(e, "Impossible de lancer l'application Arcade Inférieure")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = DentalAppLauncher(root)
        root.mainloop()
    except Exception as e:
        handle_error(e, "L'application n'a pas pu démarrer")
