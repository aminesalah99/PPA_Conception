#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de lancement pour l'application de Conception d'Arcades Dentaires
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Ajouter le répertoire src au PYTHONPATH
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

def check_dependencies():
    """Vérifier que toutes les dépendances sont installées."""
    missing_deps = []
    
    # Vérifier PIL/Pillow
    try:
        from PIL import Image, ImageTk
    except ImportError:
        missing_deps.append("Pillow")
    
    # Vérifier numpy (optionnel mais recommandé)
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy (optionnel)")
    
    if missing_deps:
        print("Dépendances manquantes détectées :")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPour installer les dépendances manquantes, exécutez :")
        print("  pip install -r requirements.txt")
        
        if "Pillow" in missing_deps:
            return False
    
    return True

def check_database():
    """Vérifier que la base de données existe, sinon la créer."""
    db_path = os.path.join(src_dir, 'elements_valides', 'dental_database.db')
    
    if not os.path.exists(db_path):
        print("Base de données non trouvée. Création en cours...")
        
        # Importer et exécuter le script d'initialisation
        try:
            from init_database_script import create_database
            create_database(db_path)
            print("Base de données créée avec succès !")
        except Exception as e:
            print(f"Erreur lors de la création de la base de données : {e}")
            return False
    else:
        print("Base de données trouvée.")
    
    return True

def check_image_folders():
    """Vérifier que les dossiers d'images existent."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.join(base_dir, 'data', 'images')
    
    required_folders = [
        'dents',
        'fonds',
        'selles/selles_inf',
        'selles/selles_sup',
        'crochets',
        'appuis_cingulaires',
        'lignes_arret'
    ]
    
    missing_folders = []
    for folder in required_folders:
        folder_path = os.path.join(image_dir, folder)
        if not os.path.exists(folder_path):
            missing_folders.append(folder_path)
            # Créer le dossier manquant
            os.makedirs(folder_path, exist_ok=True)
    
    if missing_folders:
        print("Dossiers créés :")
        for folder in missing_folders:
            print(f"  - {folder}")
    
    return True

def launch_application():
    """Lancer l'application principale."""
    try:
        # Importer l'application principale
        from main import DentalAppLauncher
        
        # Créer et lancer l'application
        root = tk.Tk()
        app = DentalAppLauncher(root)
        root.mainloop()
        
    except ImportError as e:
        print(f"Erreur d'importation : {e}")
        messagebox.showerror(
            "Erreur d'importation",
            f"Impossible d'importer les modules nécessaires :\n{e}\n\n"
            "Vérifiez que tous les fichiers sont présents dans le répertoire src/"
        )
        return False
    
    except Exception as e:
        print(f"Erreur lors du lancement : {e}")
        messagebox.showerror(
            "Erreur",
            f"Une erreur est survenue lors du lancement de l'application :\n{e}"
        )
        return False
    
    return True

def main():
    """Fonction principale."""
    print("="*60)
    print("Application de Conception d'Arcades Dentaires - PFE")
    print("="*60)
    print()
    
    # Vérifier les dépendances
    print("Vérification des dépendances...")
    if not check_dependencies():
        print("\n❌ Des dépendances essentielles sont manquantes.")
        print("Veuillez installer les dépendances avant de continuer.")
        input("\nAppuyez sur Entrée pour quitter...")
        return 1
    print("✓ Dépendances vérifiées")
    
    # Vérifier/créer la base de données
    print("\nVérification de la base de données...")
    if not check_database():
        print("❌ Impossible de créer ou d'accéder à la base de données.")
        input("\nAppuyez sur Entrée pour quitter...")
        return 1
    print("✓ Base de données prête")
    
    # Vérifier/créer les dossiers d'images
    print("\nVérification des dossiers d'images...")
    if not check_image_folders():
        print("❌ Problème avec les dossiers d'images.")
        input("\nAppuyez sur Entrée pour quitter...")
        return 1
    print("✓ Structure des dossiers vérifiée")
    
    # Lancer l'application
    print("\n" + "="*60)
    print("Lancement de l'application...")
    print("="*60 + "\n")
    
    if not launch_application():
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nApplication interrompue par l'utilisateur.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nErreur fatale : {e}")
        import traceback
        traceback.print_exc()
        input("\nAppuyez sur Entrée pour quitter...")
        sys.exit(1)