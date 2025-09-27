import os
import sqlite3
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Optional, List
from collections import deque

# PAS D'IMPORT DE backend ICI ! (c'était l'erreur)

@dataclass
class ElementProperties:
    image: str
    x: float = 400.0
    y: float = 300.0
    angle: float = 0.0
    scale: float = 1.0
    flip_x: bool = False
    flip_y: bool = False
    type_element: str = 'selle'  # Nouveau champ pour le type d'élément

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        if 'image' not in data:
            raise ValueError("Missing required field 'image' in ElementProperties data")
        return cls(**data)

class DatabaseManager:
    def __init__(self, db_path: str):
        # Use absolute path
        self.db_path = os.path.abspath(db_path)
        # Test connection
        self._test_connection()

    def _test_connection(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                print("Successfully connected to database")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise

    def load_teeth_positions(self) -> Dict[str, Tuple[float, float, float, float, bool]]:
        positions = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT fichier, x, y, scale, rotation, present FROM dents")
                for fichier, x, y, scale, rotation, present in cursor.fetchall():
                    positions[fichier] = (x, y, scale, rotation, bool(present))
        except sqlite3.Error as e:
            print(f"Error loading teeth positions: {e}")
        return positions

    def set_tooth_present(self, filename: str, present: bool):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE dents SET present = ? WHERE fichier = ?", (int(present), filename))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error setting tooth presence: {e}")

    def load_selle_properties(self, filename: str) -> Optional[dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT image, x, y, angle, scale, flip_x, flip_y, type_element FROM elements WHERE image = ?",
                    (filename,)
                )
                result = cursor.fetchone()
                if result:
                    image, x, y, angle, scale, flip_x, flip_y, type_element = result
                    return {
                        'image': image,
                        'x': x, 'y': y, 'angle': angle, 'scale': scale,
                        'flip_x': bool(flip_x), 'flip_y': bool(flip_y),
                        'type_element': type_element or 'selle'  # Valeur par défaut si NULL
                    }
        except sqlite3.Error as e:
            print(f"Error loading selle properties: {e}")
        return None

    def save_selle_properties(self, filename: str, props: dict):
        """Sauvegardement optimisé des propriétés des selles avec vérification d'intégrité."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Récupérer le type d'élément depuis les propriétés ou utiliser 'selle' par défaut
                element_type = props.get('type_element', 'selle')

                # Vérifier d'abord si l'élément existe déjà
                cursor.execute("SELECT id FROM elements WHERE image = ?", (filename,))
                existing = cursor.fetchone()

                if existing:
                    # Mise à jour de l'élément existant (pas de changement d'ID)
                    cursor.execute(
                        "UPDATE elements SET x=?, y=?, angle=?, scale=?, flip_x=?, flip_y=?, type_element=? WHERE image=?",
                        (props['x'], props['y'], props['angle'], props['scale'],
                         int(props['flip_x']), int(props['flip_y']), element_type, filename)
                    )
                    print(f"✅ Élément {filename} mis à jour (ID: {existing[0]})")
                else:
                    # Insertion d'un nouvel élément (laissant SQLite gérer l'auto-incrémentation)
                    cursor.execute(
                        "INSERT INTO elements (image, x, y, angle, scale, flip_x, flip_y, type_element) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (filename, props['x'], props['y'], props['angle'], props['scale'],
                         int(props['flip_x']), int(props['flip_y']), element_type)
                    )
                    new_id = cursor.lastrowid
                    print(f"✅ Élément {filename} inséré (Nouvel ID: {new_id})")

                conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            raise

class ModelManager:
    def __init__(self, image_folder: str, db_manager):
        self.image_folder = image_folder
        self.db_manager = db_manager
        self.models = {
            'arcade_inf': {
                'name': 'arcade_inf',
                'background': 'fond_inferieur.png',
                'folder': os.path.join('selles', 'selles_inf'),
                'teeth': [
                    'dent_31.png', 'dent_32.png', 'dent_33.png', 'dent_34.png',
                    'dent_35.png', 'dent_36.png', 'dent_37.png',
                    'dent_41.png', 'dent_42.png', 'dent_43.png', 'dent_44.png',
                    'dent_45.png', 'dent_46.png', 'dent_47.png'
                ]
            },
            'arcade_sup': {
                'name': 'arcade_sup',
                'background': 'fond_superieur.png',
                'folder': os.path.join('selles', 'selles_sup'),
                'teeth': [
                    'dent_11.png', 'dent_12.png', 'dent_13.png', 'dent_14.png',
                    'dent_15.png', 'dent_16.png', 'dent_17.png',
                    'dent_21.png', 'dent_22.png', 'dent_23.png', 'dent_24.png',
                    'dent_25.png', 'dent_26.png', 'dent_27.png'
                ]
            }
        }
        self.current_model = self.models['arcade_inf']
        self.selles_props: Dict[str, ElementProperties] = {}
        self.undo_stack: deque = deque(maxlen=50)
        self.redo_stack: deque = deque(maxlen=50)

    def set_current_model(self, model_name: str):
        self.current_model = self.models.get(model_name, self.models['arcade_inf'])
        self.selles_props.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

    def update_selle_position(self, filename: str, x: float, y: float):
        """Mettre à jour la position d'une selle."""
        if filename not in self.selles_props:
            self.selles_props[filename] = ElementProperties(image=filename)
        else:
            self.selles_props[filename].x = x
            self.selles_props[filename].y = y
            # Supprimé : sauvegarde automatique

    def update_selle_angle(self, filename: str, angle: float):
        """Mettre à jour l'angle de rotation d'une selle."""
        if filename not in self.selles_props:
            self.selles_props[filename] = ElementProperties(image=filename)

        self.selles_props[filename].angle = angle
        # Supprimé : sauvegarde automatique

    def update_selle_scale(self, filename: str, scale: float):
        """Mettre à jour l'échelle d'une selle."""
        if filename not in self.selles_props:
            self.selles_props[filename] = ElementProperties(image=filename)

        # Limiter l'échelle pour éviter les valeurs extrêmes
        scale = max(0.3, min(2.0, scale))
        self.selles_props[filename].scale = scale
        # Supprimé : sauvegarde automatique

    def flip_selle_x(self, filename: str):
        if filename not in self.selles_props:
            self.selles_props[filename] = ElementProperties(image=filename)

        self.selles_props[filename].flip_x = not self.selles_props[filename].flip_x
        # Supprimé : sauvegarde automatique

    def flip_selle_y(self, filename: str):
        if filename not in self.selles_props:
            self.selles_props[filename] = ElementProperties(image=filename)

        self.selles_props[filename].flip_y = not self.selles_props[filename].flip_y
        # Supprimé : sauvegarde automatique

    def save_selle_properties(self, filename: str):
        """Sauvegarder les propriétés d'une selle dans la base de données."""
        if filename in self.selles_props:
            props = self.selles_props[filename]
            self.db_manager.save_selle_properties(filename, props.to_dict())
            print(f"✅ Élément {filename} sauvegardé automatiquement")

    def save_single_selle_to_db(self, filename: str):
        """Sauvegarder une seule selle dans la base de données."""
        if filename in self.selles_props:
            props = self.selles_props[filename]
            self.db_manager.save_selle_properties(filename, props.to_dict())
            print(f"✅ Élément {filename} sauvegardé individuellement")
        else:
            print(f"⚠️ Élément {filename} non trouvé dans les propriétés")

    def save_state(self):
        self.undo_stack.append({k: v.to_dict() for k, v in self.selles_props.items()})
        self.redo_stack.clear()

    def undo(self) -> bool:
        if len(self.undo_stack) > 1:  # Garder au moins un état
            self.redo_stack.append(self.undo_stack.pop())
            state = self.undo_stack[-1]
            self.selles_props.clear()
            for filename, props_dict in state.items():
                self.selles_props[filename] = ElementProperties.from_dict(props_dict)
            return True
        return False

    def redo(self) -> bool:
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            self.selles_props.clear()
            for filename, props_dict in state.items():
                self.selles_props[filename] = ElementProperties.from_dict(props_dict)
            return True
        return False

    def get_selles_props(self) -> Dict[str, ElementProperties]:
        return self.selles_props

    def set_tooth_present(self, filename: str, present: bool):
        self.db_manager.set_tooth_present(filename, present)

    def get_hidden_teeth(self, teeth_positions: Dict[str, Tuple[float, float, float, float, bool]]) -> List[int]:
        """Obtenir la liste des dents masquées pour le modèle actuel."""
        all_teeth = {f: p for f, p in teeth_positions.items() if not p[4]}
        return sorted([int(f.split('_')[1].split('.')[0]) for f in all_teeth.keys()])

    def find_matching_selles(self, hidden_teeth: List[int]) -> List[str]:
        """Trouver les selles correspondantes avec filtre strict : uniquement les fichiers qui ne couvrent que des dents masquées."""
        if not hidden_teeth:
            return []

        # Étape 1: Lister tous les fichiers de selles disponibles
        folder = os.path.join(self.image_folder, self.current_model['folder'])
        if not os.path.exists(folder):
            return []

        available_selles = []
        for filename in os.listdir(folder):
            if filename.startswith('selle_') and filename.endswith('.png'):
                available_selles.append(filename)

        # Étape 2: Filtrer les fichiers valides (ceux qui ne couvrent QUE des dents masquées)
        hidden_teeth_set = set(hidden_teeth)
        valid_selles = []

        for filename in available_selles:
            teeth_in_file = set(self._extract_teeth_from_selle_filename(filename))
            # Filtre strict : les dents couvertes par le fichier doivent TOUTES être masquées
            if teeth_in_file <= hidden_teeth_set:  # ⊆ (sous-ensemble)
                valid_selles.append(filename)

        # Étape 3: Chercher une correspondance exacte parfaite (si elle existe)
        for filename in valid_selles:
            teeth_in_file = set(self._extract_teeth_from_selle_filename(filename))
            if teeth_in_file == hidden_teeth_set:
                return [filename]  # Correspondance parfaite trouvée

        # Étape 4: Algorithme glouton sur les fichiers valides
        exact_matches = []
        covered_teeth = set()

        # Tant qu'il reste des dents à couvrir
        while len(covered_teeth) < len(hidden_teeth):
            best_selle = None
            best_new_coverage = 0

            # Trouver le fichier qui couvre le plus de nouvelles dents masquées
            for filename in valid_selles:
                if filename in exact_matches:
                    continue  # Déjà utilisé

                teeth_in_file = set(self._extract_teeth_from_selle_filename(filename))
                new_coverage = len(teeth_in_file - covered_teeth)  # Nouvelles dents couvertes

                if new_coverage > best_new_coverage:
                    best_new_coverage = new_coverage
                    best_selle = filename

            if best_selle:
                exact_matches.append(best_selle)
                teeth_covered = set(self._extract_teeth_from_selle_filename(best_selle))
                covered_teeth.update(teeth_covered)
            else:
                # Plus aucun fichier ne couvre de nouvelles dents masquées
                break

        # Étape 5: Validation finale stricte
        if exact_matches:
            # Vérifier que TOUTES les dents masquées sont couvertes
            covered_teeth = set()
            for filename in exact_matches:
                teeth_in_selle = set(self._extract_teeth_from_selle_filename(filename))
                covered_teeth.update(teeth_in_selle)

            # Vérifier que chaque dent masquée est couverte et qu'aucune dent présente n'est couverte
            all_covered = covered_teeth == hidden_teeth_set

            # Vérification supplémentaire : aucune dent présente ne doit être couverte par erreur
            present_teeth_covered = covered_teeth - hidden_teeth_set

            # Cas particuliers à interdire
            # Calcul du nombre de dents présentes : total - masquées
            present_count = len(self.current_model['teeth']) - len(hidden_teeth_set)

            # Interdire si seulement 2 dents présentes maximum (PP implicite impossible)
            if present_count <= 2:
                return []

            # Interdire les combinaisons volontairement non recommandées
            invalid_patterns = [
                '11-17_21', '11-17_21-22', '21-27_11', '21-27_11-12'
            ]

            for match in exact_matches:
                sella_name = match.replace('selle_', '').replace('.png', '')
                for invalid in invalid_patterns:
                    if invalid in sella_name:
                        return []

            # Validation finale : couverture complète et aucune erreur
            if all_covered and not present_teeth_covered:
                return exact_matches
            else:
                return []
        else:
            return []

    def _extract_teeth_from_selle_filename(self, filename: str) -> List[int]:
        """Extraire la liste des dents depuis le nom du fichier de selle."""
        # Enlever "selle_" et ".png"
        name_part = filename.replace('selle_', '').replace('.png', '')

        teeth = []
        for part in name_part.split('_'):
            if '-' in part:
                # Plage de dents
                start, end = map(int, part.split('-'))
                teeth.extend(range(start, end + 1))
            else:
                # Dent individuelle
                teeth.append(int(part))

        return teeth
        
    def load_selle_properties(self, filename: str) -> ElementProperties:
        """Charger les propriétés d'une selle depuis la BD ou créer de nouvelles."""
        props_dict = self.db_manager.load_selle_properties(filename)
        if props_dict:
            self.selles_props[filename] = ElementProperties.from_dict(props_dict)
        else:
            # Nouvelles propriétés par défaut
            self.selles_props[filename] = ElementProperties(image=filename, x=400, y=300)
        return self.selles_props[filename]

class Backend:
    def __init__(self, image_folder: str, json_dir: str):
        # Construct the database path properly
        db_path = os.path.join(json_dir, 'dental_database.db')
        self.db_manager = DatabaseManager(db_path)
        self.model_manager = ModelManager(image_folder, self.db_manager)
        self.image_folder = image_folder
        self.json_dir = json_dir

        # Debug: Print paths to verify
        print(f"🔍 Backend initialized with:")
        print(f"   Image folder: {self.image_folder}")
        print(f"   JSON dir: {self.json_dir}")
        print(f"   DB path: {db_path}")

    def set_current_model(self, model_name: str):
        self.model_manager.set_current_model(model_name)

    def get_teeth_positions(self) -> Dict[str, Tuple[float, float, float, float, bool]]:
        all_positions = self.db_manager.load_teeth_positions()
        return {f: p for f, p in all_positions.items() if f in self.model_manager.current_model['teeth']}

    def load_selle_properties(self, filename: str) -> ElementProperties:
        return self.model_manager.load_selle_properties(filename)

    def save_selles_to_db(self):
        """Sauvegarder toutes les selles actives dans la base de données."""
        saved_count = 0
        for filename, props in self.model_manager.selles_props.items():
            self.db_manager.save_selle_properties(filename, props.to_dict())
            saved_count += 1
            
        print(f"✅ {saved_count} éléments enregistrés dans la base de données")
        
        # Afficher les coordonnées pour vérification
        print("\n📍 Coordonnées enregistrées:")
        for filename, props in self.model_manager.selles_props.items():
            print(f"  {filename}: x={props.x:.1f}, y={props.y:.1f}, angle={props.angle:.1f}°, échelle={props.scale:.2f}")
        
        return saved_count

    def update_selle_position(self, filename: str, x: float, y: float):
        self.model_manager.update_selle_position(filename, x, y)

    def update_selle_angle(self, filename: str, angle: float):
        self.model_manager.update_selle_angle(filename, angle)

    def update_selle_scale(self, filename: str, scale: float):
        self.model_manager.update_selle_scale(filename, scale)

    def flip_selle_x(self, filename: str):
        self.model_manager.flip_selle_x(filename)

    def flip_selle_y(self, filename: str):
        self.model_manager.flip_selle_y(filename)

    def undo(self) -> bool:
        return self.model_manager.undo()

    def redo(self) -> bool:
        return self.model_manager.redo()

    def get_selles_props(self) -> Dict[str, ElementProperties]:
        return self.model_manager.get_selles_props()

    def set_tooth_present(self, filename: str, present: bool):
        self.model_manager.set_tooth_present(filename, present)

    def get_hidden_teeth(self) -> List[int]:
        """Obtenir la liste des dents masquées."""
        teeth_positions = self.get_teeth_positions()
        return self.model_manager.get_hidden_teeth(teeth_positions)

    def find_matching_selles(self, hidden_teeth: List[int]) -> List[str]:
        """Trouver les selles correspondantes aux dents masquées."""
        return self.model_manager.find_matching_selles(hidden_teeth)

    def check_selles_exists(self, sella_names: List[str]) -> List[bool]:
        """Vérifier si les selles existent dans le dossier des images."""
        results = []
        for name in sella_names:
            folder = os.path.join(self.image_folder, self.model_manager.current_model['folder'])
            path = os.path.join(folder, name)
            results.append(os.path.exists(path))
        return results

    def find_associated_selle(self, la_filename: str) -> Optional[str]:
        """Trouver la selle associée à une ligne d'arrêt."""
        # Remplacer LA_ par sella_
        sella_name = la_filename.replace('LA_', 'selle_')
        return sella_name if sella_name in self.model_manager.selles_props else None

    def find_associated_la(self, sella_filename: str) -> Optional[str]:
        """Trouver la ligne d'arrêt associée à une selle."""
        # Remplacer sella_ par LA_
        la_name = sella_filename.replace('selle_', 'LA_')
        # Vérifier si le fichier LA existe dans le dossier approprié
        return la_name if self._la_file_exists(la_name) else None

    def _la_file_exists(self, la_name: str) -> bool:
        """Vérifier si un fichier LA existe dans le dossier approprié."""
        model_folder = self.model_manager.current_model['folder']
        if 'selles_sup' in model_folder:
            la_folder = 'LA_sup'
        elif 'selles_inf' in model_folder:
            la_folder = 'LA_inf'
        else:
            return False

        path = os.path.join(self.image_folder, 'lignes_arret', la_folder, la_name)
        return os.path.exists(path)

    def get_elements_summary(self) -> str:
        """Obtenir un résumé des éléments pour affichage."""
        props = self.model_manager.get_selles_props()
        if not props:
            return "Aucun élément chargé"
        
        summary = []
        for filename, prop in props.items():
            summary.append(f"{filename}:\n  Position: ({prop.x:.0f}, {prop.y:.0f})\n  Angle: {prop.angle:.0f}°\n  Échelle: {prop.scale:.2f}")
        
        return "\n\n".join(summary)

# Test simple si exécuté directement
if __name__ == "__main__":
    print("Backend module loaded successfully!")
    print("Classes disponibles: Backend, ElementProperties, DatabaseManager, ModelManager")
