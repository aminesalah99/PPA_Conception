#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'extraction du contenu de la base de données dental_database.db
"""

import sqlite3
import os
from datetime import datetime

def extract_database_content(db_path: str, output_file: str) -> None:
    """Extrait tout le contenu de la base de données vers un fichier texte."""

    if not os.path.exists(db_path):
        print(f"Erreur: Base de données '{db_path}' introuvable.")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Récupérer liste des tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            with open(output_file, 'w', encoding='utf-8') as f:
                # En-tête
                f.write("=" * 80 + "\n")
                f.write("EXTRACTION DU CONTENU DE LA BASE DE DONNÉES DENTAL_DATABASE.DB\n")
                f.write("=" * 80 + "\n")
                f.write(f"Date d'extraction: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Fichier base de données: {db_path}\n")
                f.write(f"Nombre de tables trouvées: {len(tables)}\n\n")

                for table_tuple in tables:
                    table_name = table_tuple[0]

                    f.write("-" * 60 + "\n")
                    f.write(f"TABLE: {table_name}\n")
                    f.write("-" * 60 + "\n")

                    # Récupérer la structure de la table
                    cursor.execute(f"PRAGMA table_info({table_name});")
                    columns = cursor.fetchall()

                    if columns:
                        f.write("Colonnes:\n")
                        for col in columns:
                            col_id, col_name, col_type, not_null, default_val, pk = col
                            null_info = "" if not_null else " (nullable)"
                            pk_info = " (PRIMARY KEY)" if pk else ""
                            f.write(f"  - {col_name} ({col_type}){pk_info}{null_info}\n")
                        f.write("\n")

                    # Récupérer les données
                    cursor.execute(f"SELECT * FROM {table_name};")
                    rows = cursor.fetchall()

                    if rows:
                        f.write(f"Données ({len(rows)} enregistrements):\n\n")

                        # Créer les en-têtes de tableau
                        col_names = [col[1] for col in columns]
                        col_widths = {}

                        # Calculer la largeur optimale pour chaque colonne
                        for j, col_name in enumerate(col_names):
                            max_width = len(str(col_name))
                            for row in rows:
                                value_str = str(row[j]) if j < len(row) else "NULL"
                                max_width = max(max_width, len(value_str))
                            col_widths[col_name] = min(max_width, 25)  # Limiter à 25 caractères

                        # Ligne de séparation supérieure
                        separator = "+"
                        header_line = "|"
                        for col_name in col_names:
                            separator += "-" * (col_widths[col_name] + 2) + "+"
                            header_line += f" {col_name[:col_widths[col_name]].ljust(col_widths[col_name])} |"

                        f.write(separator + "\n")
                        f.write(header_line + "\n")
                        f.write(separator + "\n")

                        # Données du tableau
                        for row in rows:
                            data_line = "|"
                            for j, col_name in enumerate(col_names):
                                value = row[j] if j < len(row) else "NULL"
                                value_str = str(value)
                                # Tronquer si trop long
                                if len(value_str) > col_widths[col_name]:
                                    value_str = value_str[:col_widths[col_name]-3] + "..."
                                data_line += f" {value_str.ljust(col_widths[col_name])} |"
                            f.write(data_line + "\n")

                        # Ligne de séparation inférieure
                        f.write(separator + "\n")
                        f.write("\n")
                    else:
                        f.write("Aucune donnée trouvée dans cette table.\n")

                    f.write("\n")

                f.write("=" * 80 + "\n")
                f.write("FIN DE L'EXTRACTION\n")
                f.write("=" * 80 + "\n")

        print(f"✅ Extraction terminée. Contenu sauvegardé dans '{output_file}'")

    except sqlite3.Error as e:
        print(f"❌ Erreur lors de l'extraction: {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    # Chemin relatif vers la base de données
    db_path = os.path.join(os.path.dirname(__file__), "elements_valides", "dental_database.db")
    output_file = os.path.join(os.path.dirname(__file__), "database_content.txt")

    print("🔍 Extraction du contenu de la base de données...")
    extract_database_content(db_path, output_file)
