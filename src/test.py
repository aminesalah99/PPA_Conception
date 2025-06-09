import sqlite3
import json
import os

PROJECT_ROOT = r'C:\Projets\PPA_Conception'
DB_PATH = os.path.join(PROJECT_ROOT, 'dental_database.db')
JSON_PATH = os.path.join(PROJECT_ROOT, 'elements_valides', 'teeth_positions_arcade_inf.json')

with open(JSON_PATH, "r", encoding="utf-8") as f:
    teeth_data = json.load(f)

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

def get_nom_from_fichier(fichier):
    return fichier.replace(".png", "")

c.execute("SELECT fichier FROM dents")
fichiers_existants = {row[0] for row in c.fetchall()}

ajoutees = 0
for fichier, coords in teeth_data.items():
    if fichier not in fichiers_existants:
        nom = get_nom_from_fichier(fichier)
        x, y = coords
        scale = 1.0
        rotation = 0.0
        c.execute(
            "INSERT INTO dents (nom, fichier, x, y, scale, rotation) VALUES (?, ?, ?, ?, ?, ?)",
            (nom, fichier, x, y, scale, rotation)
        )
        ajoutees += 1

conn.commit()
conn.close()

print(f"Importation terminée ! {ajoutees} dents ajoutées.")
