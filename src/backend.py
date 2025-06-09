import os
import sqlite3
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, List, Optional
import math
from collections import deque

@dataclass
class SelleProperties:
    image: str
    x: float = 400.0
    y: float = 300.0
    angle: float = 0.0
    scale: float = 1.0
    flip_x: bool = False
    flip_y: bool = False

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

class Backend:
    def __init__(self, image_folder: str, json_dir: str):
        self.image_folder = image_folder
        self.json_dir = json_dir
        self.db_path = os.path.join(self.json_dir, 'dental_database.db')
        os.makedirs(self.json_dir, exist_ok=True)
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
        self.selles_props: Dict[str, SelleProperties] = {}
        self.undo_stack: deque = deque(maxlen=50)
        self.redo_stack: deque = deque(maxlen=50)
        self._init_database()
        self._load_initial_data()

    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT,
                    fichier TEXT,
                    x REAL,
                    y REAL,
                    scale REAL,
                    rotation REAL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Selles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image TEXT,
                    x REAL,
                    y REAL,
                    angle REAL,
                    scale REAL,
                    flip_x INTEGER,
                    flip_y INTEGER
                )
            ''')
            conn.commit()

    def _load_initial_data(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM dents")
            if cursor.fetchone()[0] == 0:
                center_x, center_y = 400.0, 300.0
                radius = 150.0
                angle_step = 360.0 / 12
                for i, filename in enumerate(self.models['arcade_inf']['teeth']):
                    angle = i * angle_step - 90
                    x = center_x + radius * math.cos(math.radians(angle))
                    y = center_y + radius * math.sin(math.radians(angle))
                    nom = filename.split('.')[0]
                    cursor.execute(
                        "INSERT INTO dents (nom, fichier, x, y, scale, rotation) VALUES (?, ?, ?, ?, ?, ?)",
                        (nom, filename, x, y, 1.0, 0.0)
                    )
                for i, filename in enumerate(self.models['arcade_sup']['teeth']):
                    angle = i * angle_step - 90
                    x = center_x + radius * math.cos(math.radians(angle))
                    y = center_y + radius * math.sin(math.radians(angle))
                    nom = filename.split('.')[0]
                    cursor.execute(
                        "INSERT INTO dents (nom, fichier, x, y, scale, rotation) VALUES (?, ?, ?, ?, ?, ?)",
                        (nom, filename, x, y, 1.0, 0.0)
                    )
                conn.commit()
            cursor.execute("SELECT COUNT(*) FROM Selles")
            if cursor.fetchone()[0] == 0:
                folder = os.path.join(self.image_folder, self.current_model['folder'])
                selle_files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                for selle in selle_files:
                    cursor.execute(
                        "INSERT INTO Selles (image, x, y, angle, scale, flip_x, flip_y) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (selle, 400.0, 300.0, 0.0, 1.0, 0, 0)
                    )
                conn.commit()

    def get_teeth_positions(self) -> Dict[str, Tuple[float, float, float, float]]:
        positions = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fichier, x, y, scale, rotation FROM dents")
            for row in cursor.fetchall():
                fichier, x, y, scale, rotation = row
                if self.current_model['name'] == 'arcade_inf':
                    tooth_number = fichier.split('_')[1].split('.')[0]
                    if tooth_number.startswith(('3', '4')) and tooth_number != '38' and tooth_number != '48':
                        positions[fichier] = (x, y, scale, rotation)
                elif self.current_model['name'] == 'arcade_sup':
                    tooth_number = fichier.split('_')[1].split('.')[0]
                    if tooth_number.startswith(('1', '2')) and tooth_number != '18' and tooth_number != '28':
                        positions[fichier] = (x, y, scale, rotation)
        return positions

    def set_current_model(self, model_name: str):
        self.current_model = self.models.get(model_name, self.models['arcade_inf'])
        self.selles_props.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

    def load_selle_properties(self, filename: str) -> SelleProperties:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT x, y, angle, scale, flip_x, flip_y FROM Selles WHERE image = ?",
                (filename,)
            )
            result = cursor.fetchone()
            if result:
                x, y, angle, scale, flip_x, flip_y = result
                props = SelleProperties(
                    image=filename,
                    x=x,
                    y=y,
                    angle=angle,
                    scale=scale,
                    flip_x=bool(flip_x),
                    flip_y=bool(flip_y)
                )
            else:
                props = SelleProperties(image=filename)
                cursor.execute(
                    "INSERT INTO Selles (image, x, y, angle, scale, flip_x, flip_y) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (filename, props.x, props.y, props.angle, props.scale, int(props.flip_x), int(props.flip_y))
                )
                conn.commit()
            self.selles_props[filename] = props
            self.save_state()
        return props

    def save_selle_properties(self, filename: str):
        if filename in self.selles_props:
            props = self.selles_props[filename]
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE Selles SET x=?, y=?, angle=?, scale=?, flip_x=?, flip_y=? WHERE image=?",
                    (props.x, props.y, props.angle, props.scale, int(props.flip_x), int(props.flip_y), filename)
                )
                conn.commit()

    def save_global_config(self, name: str):
        pass

    def save_state(self):
        self.undo_stack.append({k: v.to_dict() for k, v in self.selles_props.items()})
        self.redo_stack.clear()

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        self.redo_stack.append({k: v.to_dict() for k, v in self.selles_props.items()})
        state = self.undo_stack.pop()
        self.selles_props.clear()
        for filename, props_dict in state.items():
            self.selles_props[filename] = SelleProperties.from_dict(props_dict)
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        self.undo_stack.append({k: v.to_dict() for k, v in self.selles_props.items()})
        state = self.redo_stack.pop()
        self.selles_props.clear()
        for filename, props_dict in state.items():
            self.selles_props[filename] = SelleProperties.from_dict(props_dict)
        return True

    def update_selle_position(self, filename: str, x: float, y: float):
        if filename in self.selles_props:
            self.selles_props[filename].x = x
            self.selles_props[filename].y = y

    def update_selle_angle(self, filename: str, angle: float):
        if filename in self.selles_props:
            self.selles_props[filename].angle = angle

    def update_selle_scale(self, filename: str, scale: float):
        if filename in self.selles_props:
            self.selles_props[filename].scale = scale

    def flip_selle_x(self, filename: str):
        if filename in self.selles_props:
            self.selles_props[filename].flip_x = not self.selles_props[filename].flip_x

    def flip_selle_y(self, filename: str):
        if filename in self.selles_props:
            self.selles_props[filename].flip_y = not self.selles_props[filename].flip_y

    def get_selles_props(self) -> Dict[str, SelleProperties]:
        return self.selles_props