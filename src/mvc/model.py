
"""
Model Component for MVC Architecture

This module contains the data models and business logic for the dental design application.
"""

import os
import sqlite3
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Optional, List
from abc import ABC, abstractmethod
from ..config import get_config
from ..error_handler import DatabaseError, handle_error

@dataclass
class ToothProperties:
    """Properties of a tooth in the dental arch."""
    filename: str
    x: float = 0.0
    y: float = 0.0
    scale: float = 1.0
    rotation: float = 0.0
    present: bool = True

@dataclass
class SelleProperties:
    """Properties of a dental saddle."""
    image: str
    x: float = 400.0
    y: float = 300.0
    angle: float = 0.0
    scale: float = 1.0
    flip_x: bool = False
    flip_y: bool = False

    def to_dict(self):
        """Convert to dictionary for database storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary."""
        if 'image' not in data:
            raise ValueError("Missing required field 'image' in SelleProperties data")
        return cls(**data)

class DentalArchModel:
    """Abstract base class for dental arch models."""

    def __init__(self, name: str, background: str, teeth: List[str]):
        self.name = name
        self.background = background
        self.teeth = teeth
        self.selles_props: Dict[str, SelleProperties] = {}

    def get_tooth_filenames(self) -> List[str]:
        """Get list of tooth filenames for this model."""
        return self.teeth

class DentalArchModelManager:
    """Manages different dental arch models."""

    def __init__(self, image_folder: str, db_manager):
        self.image_folder = image_folder
        self.db_manager = db_manager
        self.models = {
            'arcade_inf': DentalArchModel(
                name='arcade_inf',
                background='fond_inferieur.png',
                teeth=[
                    'dent_31.png', 'dent_32.png', 'dent_33.png', 'dent_34.png',
                    'dent_35.png', 'dent_36.png', 'dent_37.png',
                    'dent_41.png', 'dent_42.png', 'dent_43.png', 'dent_44.png',
                    'dent_45.png', 'dent_46.png', 'dent_47.png'
                ]
            ),
            'arcade_sup': DentalArchModel(
                name='arcade_sup',
                background='fond_superieur.png',
                teeth=[
                    'dent_11.png', 'dent_12.png', 'dent_13.png', 'dent_14.png',
                    'dent_15.png', 'dent_16.png', 'dent_17.png',
                    'dent_21.png', 'dent_22.png', 'dent_23.png', 'dent_24.png',
                    'dent_25.png', 'dent_26.png', 'dent_27.png'
                ]
            )
        }
        self.current_model = self.models['arcade_inf']

    def set_current_model(self, model_name: str):
        """Set the current dental arch model."""
        self.current_model = self.models.get(model_name, self.models['arcade_inf'])
        self.selles_props.clear()

    def get_current_model(self) -> DentalArchModel:
        """Get the current dental arch model."""
        return self.current_model

    def get_model_names(self) -> List[str]:
        """Get list of available model names."""
        return list(self.models.keys())

class DatabaseManager:
    """Manages database operations for the application."""

    def __init__(self, db_path: str):
        self.db_path = os.path.abspath(db_path)
        self._test_connection()

    def _test_connection(self):
        """Test database connection."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                print("Successfully connected to database")
        except sqlite3.Error as e:
            error_msg = f"Database connection error: {e}"
            print(error_msg)
            raise DatabaseError(error_msg)

    def load_teeth_positions(self) -> Dict[str, Tuple[float, float, float, float, bool]]:
        """Load teeth positions from the database."""
        positions = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT fichier, x, y, scale, rotation, present FROM dents")
                for fichier, x, y, scale, rotation, present in cursor.fetchall():
                    positions[fichier] = (x, y, scale, rotation, bool(present))
        except sqlite3.Error as e:
            error_msg = f"Error loading teeth positions: {e}"
            print(error_msg)
            raise DatabaseError(error_msg)
        return positions

    def set_tooth_present(self, filename: str, present: bool):
        """Update the presence status of a tooth in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE dents SET present = ? WHERE fichier = ?", (int(present), filename))
                conn.commit()
        except sqlite3.Error as e:
            error_msg = f"Error setting tooth presence: {e}"
            print(error_msg)
            raise DatabaseError(error_msg)

    def load_selle_properties(self, filename: str) -> Optional[dict]:
        """Load properties of a dental saddle from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT image, x, y, angle, scale, flip_x, flip_y FROM Selles WHERE image = ?",
                    (filename,)
                )
                result = cursor.fetchone()
                if result:
                    image, x, y, angle, scale, flip_x, flip_y = result
                    return {
                        'image': image,
                        'x': x, 'y': y, 'angle': angle, 'scale': scale,
                        'flip_x': bool(flip_x), 'flip_y': bool(flip_y)
                    }
        except sqlite3.Error as e:
            error_msg = f"Error loading selle properties: {e}"
            print(error_msg)
            raise DatabaseError(error_msg)
        return None

    def save_selle_properties(self, filename: str, props: dict):
        """Save properties of a dental saddle to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO Selles (image, x, y, angle, scale, flip_x, flip_y) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (filename, props['x'], props['y'], props['angle'], props['scale'], int(props['flip_x']), int(props['flip_y']))
                )
                conn.commit()
        except sqlite3.Error as e:
            error_msg = f"Error saving selle properties: {e}"
            print(error_msg)
            raise DatabaseError(error_msg)

    def initialize_database(self):
        """Initialize the database with required tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create teeth table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS dents (
                    fichier TEXT PRIMARY KEY,
                    x REAL,
                    y REAL,
                    scale REAL,
                    rotation REAL,
                    present INTEGER
                )
                """)

                # Create Selles table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS Selles (
                    image TEXT PRIMARY KEY,
                    x REAL,
                    y REAL,
                    angle REAL,
                    scale REAL,
                    flip_x INTEGER,
                    flip_y INTEGER
                )
                """)

                conn.commit()
                print("Database initialized successfully")
        except sqlite3.Error as e:
            error_msg = f"Error initializing database: {e}"
            print(error_msg)
            raise DatabaseError(error_msg)

class DentalDesignModel:
    """Main model class for the dental design application."""

    def __init__(self, image_folder: str, json_dir: str):
        """Initialize the dental design model.

        Args:
            image_folder: Path to the folder containing images
            json_dir: Path to the directory for JSON configuration files
        """
        self.config = get_config()
        self.image_folder = image_folder
        self.json_dir = json_dir

        # Initialize database
        db_path = os.path.join(json_dir, self.config.database_path)
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.initialize_database()

        # Initialize model manager
        self.model_manager = DentalArchModelManager(image_folder, self.db_manager)

        # State management
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_redo = self.config.undo_redo_max_size

    def set_current_model(self, model_name: str):
        """Set the current dental arch model."""
        self.model_manager.set_current_model(model_name)
        self.clear_history()

    def get_current_model_name(self) -> str:
        """Get the name of the current dental arch model."""
        return self.model_manager.get_current_model().name

    def get_teeth_positions(self) -> Dict[str, Tuple[float, float, float, float, bool]]:
        """Get positions of all teeth in the current model."""
        all_positions = self.db_manager.load_teeth_positions()
        current_model = self.model_manager.get_current_model()
        return {f: p for f, p in all_positions.items() if f in current_model.get_tooth_filenames()}

    def set_tooth_present(self, filename: str, present: bool):
        """Update the presence status of a tooth."""
        self.db_manager.set_tooth_present(filename, present)
        self.save_state()

    def load_selle_properties(self, filename: str) -> SelleProperties:
        """Load properties of a dental saddle."""
        props_dict = self.db_manager.load_selle_properties(filename)
        if props_dict:
            return SelleProperties.from_dict(props_dict)
        else:
            return SelleProperties(image=filename)

    def save_selle_properties(self, filename: str, props: SelleProperties):
        """Save properties of a dental saddle."""
        self.db_manager.save_selle_properties(filename, props.to_dict())
        self.save_state()

    def update_selle_position(self, filename: str, x: float, y: float):
        """Update position of a dental saddle."""
        if filename in self.model_manager.selles_props:
            self.model_manager.selles_props[filename].x = x
            self.model_manager.selles_props[filename].y = y
            self.save_selle_properties(filename, self.model_manager.selles_props[filename])

    def update_selle_angle(self, filename: str, angle: float):
        """Update rotation angle of a dental saddle."""
        if filename in self.model_manager.selles_props:
            self.model_manager.selles_props[filename].angle = angle
            self.save_selle_properties(filename, self.model_manager.selles_props[filename])

    def update_selle_scale(self, filename: str, scale: float):
        """Update scale of a dental saddle."""
        if filename in self.model_manager.selles_props:
            self.model_manager.selles_props[filename].scale = scale
            self.save_selle_properties(filename, self.model_manager.selles_props[filename])

    def flip_selle_x(self, filename: str):
        """Flip a dental saddle horizontally."""
        if filename in self.model_manager.selles_props:
            self.model_manager.selles_props[filename].flip_x = not self.model_manager.selles_props[filename].flip_x
            self.save_selle_properties(filename, self.model_manager.selles_props[filename])

    def flip_selle_y(self, filename: str):
        """Flip a dental saddle vertically."""
        if filename in self.model_manager.selles_props:
            self.model_manager.selles_props[filename].flip_y = not self.model_manager.selles_props[filename].flip_y
            self.save_selle_properties(filename, self.model_manager.selles_props[filename])

    def get_selles_props(self) -> Dict[str, SelleProperties]:
        """Get properties of all dental saddles."""
        return self.model_manager.selles_props

    def save_state(self):
        """Save current state for undo functionality."""
        self.undo_stack.append({k: v.to_dict() for k, v in self.model_manager.selles_props.items()})
        self.redo_stack.clear()

        # Limit stack size
        if len(self.undo_stack) > self.max_undo_redo:
            self.undo_stack.pop(0)

    def undo(self) -> bool:
        """Undo the last action."""
        if not self.undo_stack:
            return False

        self.redo_stack.append({k: v.to_dict() for k, v in self.model_manager.selles_props.items()})
        state = self.undo_stack.pop()
        self.model_manager.selles_props.clear()
        for filename, props_dict in state.items():
            self.model_manager.selles_props[filename] = SelleProperties.from_dict(props_dict)
        return True

    def redo(self) -> bool:
        """Redo the last undone action."""
        if not self.redo_stack:
            return False

        self.undo_stack.append({k: v.to_dict() for k, v in self.model_manager.selles_props.items()})
        state = self.redo_stack.pop()
        self.model_manager.selles_props.clear()
        for filename, props_dict in state.items():
            self.model_manager.selles_props[filename] = SelleProperties.from_dict(props_dict)
        return True

    def clear_history(self):
        """Clear undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
