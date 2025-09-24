#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎨 Dental Design Application Launcher
Modern, professional interface for dental arcade design system
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add src to PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_frontend import BaseDentalApp

class SuperiorDentalApp(BaseDentalApp):
    """Superior dental arcade design application."""
    def __init__(self, root):
        super().__init__(root, model_type="arcade_sup")
        self.root.title("🦷 Conception d'Arcade Dentaire Supérieure - PFE")

class InferiorDentalApp(BaseDentalApp):
    """Inferior dental arcade design application."""
    def __init__(self, root):
        super().__init__(root, model_type="arcade_inf")
        self.root.title("🦷 Conception d'Arcade Dentaire Inférieure - PFE")

class DentalAppLauncher:
    def __init__(self, root):
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
        """🎨 Configure modern ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Modern color palette
        colors = {
            'primary': '#3498db',
            'secondary': '#2ecc71',
            'accent': '#e74c3c',
            'background': '#f8f9fa',
            'surface': '#ffffff',
            'text_primary': '#2c3e50',
            'text_secondary': '#7f8c8d',
            'text_muted': '#95a5a6'
        }

        # Configure all styles at once
        styles_config = {
            'Title.TLabel': {
                'font': ('Segoe UI', 32, 'bold'),
                'background': colors['background'],
                'foreground': colors['text_primary']
            },
            'Subtitle.TLabel': {
                'font': ('Segoe UI', 16),
                'background': colors['background'],
                'foreground': colors['text_secondary']
            },
            'Description.TLabel': {
                'font': ('Segoe UI', 12),
                'background': colors['surface'],
                'foreground': colors['text_primary'],
                'wraplength': 280
            },
            'Card.TFrame': {
                'background': colors['surface'],
                'relief': 'flat',
                'borderwidth': 0
            },
            'Footer.TLabel': {
                'font': ('Segoe UI', 10),
                'background': colors['background'],
                'foreground': colors['text_muted']
            }
        }

        # Apply all styles
        for style_name, config in styles_config.items():
            style.configure(style_name, **config)

        # Enhanced button styles
        style.configure('Action.TButton',
                       font=('Segoe UI', 13, 'bold'),
                       padding=(20, 12))

        style.map('Action.TButton',
                 background=[('active', colors['primary']), ('!disabled', '#f1f8ff')],
                 foreground=[('active', 'white'), ('!disabled', colors['primary'])])

        # Store colors for use in other methods
        self.colors = colors
    
    def create_header(self):
        """Create the header section with title and subtitle"""
        header_frame = tk.Frame(self.main_frame, bg="#f8f9fa")
        header_frame.pack(fill=tk.X, pady=(0, 40))
        
        # Add logo placeholder (you can replace with an actual logo)
        logo_frame = tk.Frame(header_frame, bg="#3498db", width=60, height=60)
        logo_frame.pack(side=tk.LEFT, padx=(0, 20))
        logo_frame.pack_propagate(False)
        
        tk.Label(logo_frame, text="CD", bg="#3498db", fg="white", 
                 font=("Segoe UI", 24, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        
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
        """Create the main content with arcade selection cards"""
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
        """🎨 Create a modern card for an arcade type with enhanced design"""
        # Create card container with enhanced shadow effect
        card_container = tk.Frame(parent, bg="#e8f4f8", highlightthickness=2,
                                 highlightbackground="#d1ecf1", highlightcolor="#a8e6cf")
        card_container.grid(row=0, column=column, padx=20, pady=20, sticky="nsew")

        # Create inner card with modern styling
        card = ttk.Frame(card_container, style='Card.TFrame', padding=30)
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Configure grid weights for responsive design
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # Enhanced image placeholder with gradient effect
        image_frame = tk.Frame(card, bg=self.colors['primary'], width=220, height=140)
        image_frame.pack(pady=(0, 25))
        image_frame.pack_propagate(False)

        # Create gradient effect background
        gradient_canvas = tk.Canvas(image_frame, width=220, height=140,
                                   bg=self.colors['primary'], highlightthickness=0)
        gradient_canvas.pack(fill=tk.BOTH, expand=True)

        # Add icon based on arcade type
        icon_emoji = "⬆️" if "Supérieure" in title else "⬇️"
        tk.Label(image_frame, text=f"{icon_emoji}\n{image_alt}",
                 bg=self.colors['primary'], fg="white",
                 font=("Segoe UI", 16, "bold"), justify="center").place(relx=0.5, rely=0.5, anchor="center")

        # Card title with enhanced typography
        title_label = ttk.Label(card, text=title, font=('Segoe UI', 20, 'bold'),
                               foreground=self.colors['text_primary'])
        title_label.pack(pady=(0, 10))

        # Add subtitle with feature highlights
        features = "✨ Précision | ⚡ Efficacité | 🎯 Personnalisé" if "Supérieure" in title else "🔧 Adapté | 🛡️ Sécurisé | 📊 Analytique"
        features_label = ttk.Label(card, text=features,
                                  font=('Segoe UI', 10),
                                  foreground=self.colors['text_secondary'])
        features_label.pack(pady=(0, 15))

        # Enhanced description with better formatting
        desc_label = ttk.Label(card, text=description, style='Description.TLabel')
        desc_label.pack(pady=(0, 30))

        # Modern action button with enhanced styling
        button_frame = tk.Frame(card, bg=self.colors['surface'])
        button_frame.pack(fill=tk.X, pady=(10, 0))

        action_btn = ttk.Button(
            button_frame,
            text=f"🚀 {title.split()[-1]} →",
            style='Action.TButton',
            command=command
        )
        action_btn.pack(side=tk.RIGHT, padx=(0, 5))

        # Add modern hover and click effects
        self.add_hover_effect(card_container, card, action_btn)
    
    def add_hover_effect(self, card_container, card, button):
        """Add enhanced hover effects to the card and button"""
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
        """Create the footer with information and links"""
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
        """Launch the superior arcade application"""
        try:
            self.root.destroy()
            new_root = tk.Tk()
            app = SuperiorDentalApp(new_root)
            new_root.mainloop()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer l'application Arcade Supérieure: {str(e)}")
    
    def launch_inferior(self):
        """Launch the inferior arcade application"""
        try:
            self.root.destroy()
            new_root = tk.Tk()
            app = InferiorDentalApp(new_root)
            new_root.mainloop()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer l'application Arcade Inférieure: {str(e)}")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = DentalAppLauncher(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Erreur Fatale", f"L'application n'a pas pu démarrer: {str(e)}")
