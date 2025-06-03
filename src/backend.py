import os
import json
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional

@dataclass
class SelleProperties:
    """Propriétés d'un objet selle."""
    nom: str = ""
    image: str = ""
    x: float = 400
    y: float = 300
    angle: float = 0
    scale: float = 1.0
    flip_x: bool = False
    flip_y: bool = False

class Backend:
    """Gestion de la logique métier pour les arcades dentaires."""
    def __init__(self, image_folder: str, json_dir: str):
        self.image_folder = image_folder
        self.json_dir = json_dir
        self.models = {
            'arcade_inf': {
                'name': "Arcade Inférieure",
                'folder': 'selles_inf',
                'background': 'fond_inferieur.png',
                'teeth': {
                    'dent_31.png': (419, 448), 'dent_32.png': (467, 432),
                    'dent_33.png': (502, 408), 'dent_34.png': (533, 373),
                    'dent_35.png': (555, 332), 'dent_36.png': (581, 289),
                    'dent_37.png': (596, 242), 'dent_38.png': (606, 194),
                    'dent_41.png': (366, 448), 'dent_42.png': (318, 433),
                    'dent_43.png': (284, 407), 'dent_44.png': (262, 369),
                    'dent_45.png': (243, 328), 'dent_46.png': (228, 283),
                    'dent_47.png': (216, 237), 'dent_48.png': (200, 190)
                },
                'selles': {}
            },
            'arcade_sup': {
                'name': "Arcade Supérieure",
                'folder': 'selles_sup',
                'background': 'fond_superieur.png',
                'teeth': {
                    'dent_11.png': (419, 150), 'dent_12.png': (467, 165),
                    'dent_13.png': (502, 190), 'dent_14.png': (533, 225),
                    'dent_15.png': (555, 265), 'dent_16.png': (581, 310),
                    'dent_17.png': (596, 355), 'dent_18.png': (606, 400),
                    'dent_21.png': (366, 150), 'dent_22.png': (318, 165),
                    'dent_23.png': (284, 190), 'dent_24.png': (262, 225),
                    'dent_25.png': (243, 265), 'dent_26.png': (228, 310),
                    'dent_27.png': (216, 355), 'dent_28.png': (200, 400)
                },
                'selles': {}
            }
        }
        self._calculate_default_selle_positions()
        self.current_model_key = 'arcade_inf'
        self.current_model = self.models['arcade_inf']
        self.teeth_positions = self.current_model['teeth'].copy()
        self.selles_props: Dict[str, SelleProperties] = {}
        self.history: List[Dict[str, SelleProperties]] = []
        self.history_index: int = -1

    def _calculate_default_selle_positions(self):
        """Calcule les positions par défaut des selles basées sur les positions des dents."""
        dents_inf = self.models['arcade_inf']['teeth']
        self.models['arcade_inf']['selles'] = {
            'selle_36_37_38.png': (
                (dents_inf['dent_36.png'][0] + dents_inf['dent_37.png'][0] + dents_inf['dent_38.png'][0]) / 3,
                (dents_inf['dent_36.png'][1] + dents_inf['dent_37.png'][1] + dents_inf['dent_38.png'][1]) / 3
            ),
            'selle_38.png': dents_inf['dent_38.png'],
            'selle_45-48.png': (
                sum(dents_inf[f'dent_{i}.png'][0] for i in range(45, 49)) / 4,
                sum(dents_inf[f'dent_{i}.png'][1] for i in range(45, 49)) / 4
            ),
            "selle_48'.png": dents_inf['dent_48.png'],
            'selle_test.png': (400, 300),
        }
        dents_sup = self.models['arcade_sup']['teeth']
        self.models['arcade_sup']['selles'] = {
            'selle_11_12.png': (
                (dents_sup['dent_11.png'][0] + dents_sup['dent_12.png'][0]) / 2,
                (dents_sup['dent_11.png'][1] + dents_sup['dent_12.png'][1]) / 2
            ),
        }

    def set_current_model(self, model_key: str):
        """Change le modèle actuel et charge les données correspondantes."""
        if model_key in self.models:
            self.current_model_key = model_key
            self.current_model = self.models[model_key]
            self.load_teeth_positions()
            self.selles_props = {}
            self.history = []
            self.history_index = -1

    def load_teeth_positions(self):
        """Charge les positions des dents depuis un fichier JSON si disponible."""
        save_path = os.path.join(self.json_dir, f"teeth_positions_{self.current_model_key}.json")
        if os.path.exists(save_path):
            with open(save_path, "r", encoding='utf-8') as f:
                adjusted_positions = json.load(f)
            for filename in self.current_model['teeth']:
                if filename in adjusted_positions:
                    self.current_model['teeth'][filename] = tuple(adjusted_positions[filename])
            self.teeth_positions = self.current_model['teeth'].copy()
        else:
            self.teeth_positions = self.current_model['teeth'].copy()

    def get_teeth_positions(self) -> Dict[str, Tuple[float, float]]:
        """Retourne les positions des dents pour le modèle actuel."""
        return self.teeth_positions

    def load_selle_properties(self, filename: str) -> SelleProperties:
        """Charge les propriétés d'une selle depuis un fichier JSON ou utilise les valeurs par défaut."""
        config_path = os.path.join(self.json_dir, f"{self.current_model_key}_{os.path.splitext(filename)[0]}.json")
        default_pos = self.current_model['selles'].get(filename, (400, 300))
        if os.path.exists(config_path):
            with open(config_path, "r", encoding='utf-8') as f:
                config = json.load(f)
                props = SelleProperties(
                    nom=config.get('nom', os.path.splitext(filename)[0]),
                    image=filename,
                    x=config.get('x', default_pos[0]),
                    y=config.get('y', default_pos[1]),
                    angle=config.get('angle', 0),
                    scale=config.get('scale', 1.0),
                    flip_x=config.get('flip_x', False),
                    flip_y=config.get('flip_y', False)
                )
        else:
            props = SelleProperties(
                nom=os.path.splitext(filename)[0],
                image=filename,
                x=default_pos[0],
                y=default_pos[1]
            )
        self.selles_props[filename] = props
        return props

    def update_selle_position(self, filename: str, x: float, y: float):
        """Met à jour la position d'une selle."""
        if filename in self.selles_props:
            self.selles_props[filename].x = x
            self.selles_props[filename].y = y

    def update_selle_angle(self, filename: str, angle: float):
        """Met à jour l'angle d'une selle."""
        if filename in self.selles_props:
            self.selles_props[filename].angle = angle

    def update_selle_scale(self, filename: str, scale: float):
        """Met à jour l'échelle d'une selle."""
        if filename in self.selles_props:
            self.selles_props[filename].scale = scale

    def flip_selle_x(self, filename: str):
        """Retourne une selle horizontalement."""
        if filename in self.selles_props:
            self.selles_props[filename].flip_x = not self.selles_props[filename].flip_x

    def flip_selle_y(self, filename: str):
        """Retourne une selle verticalement."""
        if filename in self.selles_props:
            self.selles_props[filename].flip_y = not self.selles_props[filename].flip_y

    def save_selle_properties(self, filename: str):
        """Sauvegarde les propriétés d'une selle dans un fichier JSON."""
        if filename in self.selles_props:
            props = self.selles_props[filename]
            config = {key: val for key, val in vars(props).items()}
            path = os.path.join(self.json_dir, f"{self.current_model_key}_{os.path.splitext(filename)[0]}.json")
            with open(path, "w", encoding='utf-8') as f:
                json.dump(config, f, indent=2)

    def save_global_config(self, name: str):
        """Sauvegarde toutes les selles dans un fichier JSON global."""
        config = {k: {key: val for key, val in vars(v).items()} for k, v in self.selles_props.items()}
        path = os.path.join(self.json_dir, f"{self.current_model_key}_{name}.json")
        with open(path, "w", encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    def save_state(self):
        """Enregistre l'état actuel des selles pour l'historique."""
        if not self.selles_props:
            return
        self.history = self.history[:self.history_index + 1]
        state = {k: SelleProperties(**vars(v)) for k, v in self.selles_props.items()}
        self.history.append(state)
        self.history_index = len(self.history) - 1
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1

    def undo(self) -> bool:
        """Annule la dernière action sur les selles."""
        if self.history_index > 0:
            self.history_index -= 1
            self.selles_props = {k: SelleProperties(**vars(v)) for k, v in self.history[self.history_index].items()}
            return True
        return False

    def redo(self) -> bool:
        """Rétablit la dernière action annulée sur les selles."""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.selles_props = {k: SelleProperties(**vars(v)) for k, v in self.history[self.history_index].items()}
            return True
        return False

    def get_selles_props(self) -> Dict[str, SelleProperties]:
        """Retourne les propriétés actuelles des selles."""
        return self.selles_props