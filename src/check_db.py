import sqlite3
import os
import random

# Vérifier et modifier la structure de la base de données
db_path = os.path.join('elements_valides', 'dental_database.db')

# Chemin vers les images réelles
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
images_root = os.path.join(project_root, "data", "images")

print(f"🔍 Vérification des chemins:")
print(f"   Projet racine: {project_root}")
print(f"   Images: {images_root}")

# Lister les fichiers disponibles par type
available_files = {
    'Appuis Cingulaires Noirs': [],
    'Appuis Cingulaires Bleus': [],
    'Crochets Ackers': [],
    'Crochets Bonwill': [],
    'Crochets Nally': [],
    'Lignes dArrêt': [],
    'Selles': []
}

# Scanner les dossiers d'images
if os.path.exists(images_root):
    print("\n📁 Structure des images trouvée:")

    # Appuis Cingulaires Noirs
    noirs_path = os.path.join(images_root, "appuis_cingulaires", "noirs")
    if os.path.exists(noirs_path):
        available_files['Appuis Cingulaires Noirs'] = [f for f in os.listdir(noirs_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"   Appuis Cingulaires Noirs: {len(available_files['Appuis Cingulaires Noirs'])} fichiers")

    # Appuis Cingulaires Bleus
    bleus_path = os.path.join(images_root, "appuis_cingulaires", "bleus")
    if os.path.exists(bleus_path):
        available_files['Appuis Cingulaires Bleus'] = [f for f in os.listdir(bleus_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"   Appuis Cingulaires Bleus: {len(available_files['Appuis Cingulaires Bleus'])} fichiers")

    # Crochets
    crochets_path = os.path.join(images_root, "crochets")
    if os.path.exists(crochets_path):
        for subfolder in ['ackers', 'bonwill', 'nally']:
            subfolder_path = os.path.join(crochets_path, subfolder)
            if os.path.exists(subfolder_path):
                files = [f for f in os.listdir(subfolder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                type_name = f"Crochets {subfolder.title()}"
                available_files[type_name] = files
                print(f"   {type_name}: {len(files)} fichiers")

    # Lignes d'Arrêt
    lignes_path = os.path.join(images_root, "lignes_arret")
    if os.path.exists(lignes_path):
        available_files['Lignes dArrêt'] = [f for f in os.listdir(lignes_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"   Lignes d'Arrêt: {len(available_files['Lignes dArrêt'])} fichiers")

    # Selles (arcade_inf et arcade_sup)
    for arcade in ['selles_inf', 'selles_sup']:
        selles_path = os.path.join(images_root, "selles", arcade)
        if os.path.exists(selles_path):
            files = [f for f in os.listdir(selles_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            available_files['Selles'].extend(files)

    available_files['Selles'] = list(set(available_files['Selles']))  # Supprimer les doublons
    print(f"   Selles: {len(available_files['Selles'])} fichiers")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Nettoyer la base de données et la recharger avec les vrais fichiers
    print("\n🧹 Nettoyage de la base de données...")

    # Supprimer tous les éléments sauf les Selles existantes
    cursor.execute("DELETE FROM Selles WHERE type_element != 'Selles'")

    # Ajouter les vrais fichiers pour chaque type
    for elem_type, files in available_files.items():
        if files and elem_type != 'Selles':  # Les Selles sont déjà dans la base
            print(f"   Ajout de {len(files)} éléments de type '{elem_type}'")
            for i, filename in enumerate(files[:5]):  # Limiter à 5 éléments par type
                x = 300 + (i * 50)  # Position variable
                y = 300 + (i * 30)
                try:
                    cursor.execute(
                        "INSERT INTO Selles (image, x, y, angle, scale, flip_x, flip_y, type_element) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (filename, x, y, 0, 1.0, 0, 0, elem_type)
                    )
                except Exception as e:
                    print(f"     Erreur avec {filename}: {e}")

    conn.commit()

    # Afficher la nouvelle répartition
    print("\n📊 Nouvelle répartition des éléments:")
    cursor.execute("SELECT type_element, COUNT(*) FROM Selles GROUP BY type_element")
    type_counts = cursor.fetchall()
    for type_name, count in type_counts:
        print(f"  {type_name}: {count} éléments")

    # Afficher quelques exemples
    print("\n📋 Exemples d'éléments par type:")
    for elem_type in available_files.keys():
        cursor.execute("SELECT image FROM Selles WHERE type_element = ? LIMIT 3", (elem_type,))
        examples = cursor.fetchall()
        if examples:
            print(f"  {elem_type}: {[ex[0] for ex in examples]}")

    total_count = sum(count for _, count in type_counts)
    print(f"\n✅ Total d'éléments dans la base: {total_count}")

    conn.close()

    print("\n🎉 Base de données mise à jour avec les vrais fichiers!")
else:
    print(f"❌ Base de données non trouvée: {db_path}")

print("\n💡 Instructions:")
print("   1. Redémarrez l'application")
print("   2. Changez le type d'élément vers 'Appuis Cingulaires Noirs'")
print("   3. Vous devriez maintenant voir les éléments correspondants!")
