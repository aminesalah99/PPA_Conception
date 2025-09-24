#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de correction de l'intégrité des IDs dans dental_database.db

Ce script corrige les problèmes de séquentialité des IDs dans la table elements
causés par INSERT OR REPLACE et des opérations de suppression.
"""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Tuple, Dict, Any

def backup_database(db_path: str) -> str:
    """Crée une sauvegarde de la base de données."""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Sauvegarde créée: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Erreur lors de la création de la sauvegarde: {e}")
        raise

def get_table_structure(db_path: str, table_name: str) -> List[str]:
    """Récupère la liste des colonnes d'une table."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        return [row[1] for row in cursor.fetchall()]

def get_all_elements(db_path: str) -> List[Tuple]:
    """Récupère toutes les données de la table elements."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM elements ORDER BY id;")
        return cursor.fetchall()

def rebuild_elements_table(db_path: str, original_data: List[Tuple]):
    """Reconstruit la table elements avec IDs séquentiels."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Commencer une transaction pour garantir la cohérence
        cursor.execute("BEGIN TRANSACTION;")

        try:
            # Créer une table temporaire
            cursor.execute("""
                CREATE TABLE elements_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image TEXT,
                    x REAL NOT NULL DEFAULT 400.0,
                    y REAL NOT NULL DEFAULT 300.0,
                    angle REAL NOT NULL DEFAULT 0.0,
                    scale REAL NOT NULL DEFAULT 1.0,
                    flip_x INTEGER NOT NULL DEFAULT 0,
                    flip_y INTEGER NOT NULL DEFAULT 0,
                    type_element TEXT
                );
            """)

            print(f"🛠️ Reconstruction de {len(original_data)} enregistrements...")

            # Insérer les données dans la table temporaire sans l'ID
            for row in original_data:
                # row[0] est l'ancien ID, on l'ignore
                image, x, y, angle, scale, flip_x, flip_y, type_element = row[1:]
                cursor.execute("""
                    INSERT INTO elements_temp
                    (image, x, y, angle, scale, flip_x, flip_y, type_element)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (image, x, y, angle, scale, flip_x, flip_y, type_element))

            # Remplacer la table originale par la table temporaire
            cursor.execute("DROP TABLE elements;")
            cursor.execute("ALTER TABLE elements_temp RENAME TO elements;")

            # Mettre à jour la séquence SQLite
            cursor.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'elements';",
                         (len(original_data),))

            # Valider la transaction
            conn.commit()

            print("✅ Reconstruction terminée avec succès")
            print(f"✅ Séquence mise à jour: {len(original_data)}")

        except Exception as e:
            cursor.execute("ROLLBACK;")
            print(f"❌ Erreur lors de la reconstruction: {e}")
            raise

def verify_integrity(db_path: str) -> bool:
    """Vérifie que les IDs sont maintenant séquentiels."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Vérifier que les IDs sont séquentiels
        cursor.execute("SELECT id FROM elements ORDER BY id;")
        ids = [row[0] for row in cursor.fetchall()]

        # Vérifier la séquentialité
        expected = list(range(1, len(ids) + 1))
        if ids == expected:
            print("✅ Intégrité des IDs vérifiée: séquence complète 1 à", len(ids))
            return True
        else:
            print("❌ Problème d'intégrité persistant")
            print(f"   Attendu: {expected}")
            print(f"   Réel: {ids}")
            return False

def test_database_functionality(db_path: str) -> bool:
    """Teste les fonctionnalités principales de la base de données."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Test 1: Compter les éléments
            cursor.execute("SELECT COUNT(*) FROM elements;")
            count = cursor.fetchone()[0]
            print(f"✅ Test 1 - Comptage: {count} éléments")

            # Test 2: Recherche par image
            cursor.execute("SELECT * FROM elements WHERE image LIKE 'selle_%' LIMIT 1;")
            result = cursor.fetchone()
            if result:
                print("✅ Test 2 - Recherche: fonctionnelle")
            else:
                print("⚠️ Test 2 - Recherche: aucun résultat trouvé")

            # Test 3: Ajout d'un élément de test
            test_image = "test_element.png"
            cursor.execute("""
                INSERT OR REPLACE INTO elements
                (image, x, y, angle, scale, flip_x, flip_y, type_element)
                VALUES (?, 100, 200, 45, 1.5, 0, 1, 'Test');
            """, (test_image,))

            # Vérifier que l'ajout fonctionne
            cursor.execute("SELECT * FROM elements WHERE image = ?;", (test_image,))
            added = cursor.fetchone()
            if added:
                print("✅ Test 3 - Ajout: fonctionnel")
                # Nettoyer
                cursor.execute("DELETE FROM elements WHERE image = ?;", (test_image,))
            else:
                print("❌ Test 3 - Ajout: échec")

            # Test 4: Vérifier la séquence mise à jour
            cursor.execute("SELECT seq FROM sqlite_sequence WHERE name = 'elements';")
            seq_result = cursor.fetchone()
            if seq_result:
                seq = seq_result[0]
                print(f"✅ Test 4 - Séquence: {seq}")
            else:
                print("⚠️ Test 4 - Séquence: non trouvée")

            conn.commit()
            return True

    except sqlite3.Error as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False

def main():
    """Fonction principale du script de correction."""
    print("=" * 70)
    print("SCRIPT DE CORRECTION D'INTÉGRITÉ DES IDs - DENTAL_DATABASE.DB")
    print("=" * 70)

    # Chemin de la base de données
    base_dir = os.path.dirname(__file__)
    db_path = os.path.join(base_dir, "elements_valides", "dental_database.db")

    if not os.path.exists(db_path):
        print(f"❌ Base de données introuvable: {db_path}")
        return False

    print(f"📍 Base de données: {db_path}")

    try:
        # Étape 1: Sauvegarde
        print("\n🔄 Étape 1: Création de la sauvegarde...")
        backup_path = backup_database(db_path)

        # Étape 2: Analyse du problème actuel
        print("\n🔍 Étape 2: Analyse des IDs existants...")
        original_data = get_all_elements(db_path)
        print(f"📊 Trouvé {len(original_data)} enregistrements")

        # Afficher les premiers et derniers IDs pour voir le problème
        if original_data:
            first_ids = [row[0] for row in original_data[:5]]
            last_ids = [row[0] for row in original_data[-5:]]
            print(f"📈 Premiers IDs: {first_ids}")
            print(f"📈 Derniers IDs: {last_ids}")

            # Identifier les trous dans la séquence
            all_ids = [row[0] for row in original_data]
            max_id = max(all_ids)
            expected_count = max_id
            actual_count = len(all_ids)
            gaps = expected_count - actual_count

            print(f"📊 ID maximum: {max_id}")
            print(f"📊 Nombre d'enregistrements: {actual_count}")
            print(f"📊 Nombre de trous dans la séquence: {gaps}")

        # Étape 3: Reconstruction
        print("\n🔧 Étape 3: Reconstruction de la table...")
        rebuild_elements_table(db_path, original_data)

        # Étape 4: Vérification
        print("\n✅ Étape 4: Vérification de l'intégrité...")
        if verify_integrity(db_path):
            print("🎉 Intégrité restaurée avec succès!")
        else:
            print("💥 Échec de la restauration de l'intégrité")
            return False

        # Étape 5: Tests fonctionnels
        print("\n🧪 Étape 5: Tests fonctionnels...")
        if test_database_functionality(db_path):
            print("🎯 Tous les tests fonctionnels réussis")
        else:
            print("⚠️ Certains tests ont échoué")
            return False

        print("\n" + "=" * 70)
        print("✅ CORRECTION TERMINÉE AVEC SUCCÈS")
        print(f"📁 Sauvegarde disponible: {backup_path}")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n💥 ERREUR FATALE: {e}")
        print("💡 Utilisez la sauvegarde créée pour restaurer l'état initial")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
