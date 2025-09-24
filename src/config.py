
"""
Configuration Management Module

This module handles application configuration settings.
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

@dataclass
class AppConfig:
    """Application configuration data class."""
    # UI Settings
    window_title: str = "Conception d'Arcades Dentaires - PFE"
    window_width: int = 1200
    window_height: int = 800
    window_min_width: int = 800
    window_min_height: int = 600
    default_dent_size: int = 60

    # Canvas Settings
    canvas_width: int = 800
    canvas_height: int = 600
    canvas_bg_color: str = "white"

    # Image Processing Settings
    image_resampling_method: str = "LANCZOS"
    max_image_width: int = 700

    # Database Settings
    database_path: str = "elements_valides/dental_database.db"
    last_model_file: str = "elements_valides/last_modele.dat"

    # Export Settings
    export_quality: int = 95
    export_format: str = "PNG"

    # Undo/Redo Settings
    undo_redo_max_size: int = 50

    # Logging Settings
    log_level: str = "INFO"
    log_file: str = "dental_design_app.log"

    # File Paths
    image_folder: str = "data/images"
    backgrounds_folder: str = "fonds"
    teeth_folder: str = "dents"
    selles_inf_folder: str = "selles/selles_inf"
    selles_sup_folder: str = "selles/selles_sup"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create an AppConfig instance from a dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the AppConfig instance to a dictionary."""
        return asdict(self)

class ConfigManager:
    """Manages application configuration settings."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration manager.

        Args:
            config_file: Path to the configuration file. If None, uses default path.
        """
        self.config_file = config_file or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "..", 
            "config", 
            "app_config.json"
        )

        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        # Load or create default configuration
        self.config = self._load_config()

    def _load_config(self) -> AppConfig:
        """Load configuration from file or return default if file doesn't exist."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return AppConfig.from_dict(data)
            else:
                # Create default config file
                config = AppConfig()
                self.save_config(config)
                return config
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return AppConfig()

    def save_config(self, config: Optional[AppConfig] = None) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save. If None, saves current configuration.
        """
        try:
            if config is None:
                config = self.config

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=4)
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def get_config(self) -> AppConfig:
        """Get the current configuration."""
        return self.config

    def update_config(self, **kwargs) -> None:
        """Update configuration values.

        Args:
            **kwargs: Configuration values to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                print(f"Warning: Unknown configuration key: {key}")

        # Save updated configuration
        self.save_config()

    def get_image_folder(self) -> str:
        """Get the absolute path to the images folder."""
        return os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            self.config.image_folder
        ))

    def get_backgrounds_folder(self) -> str:
        """Get the absolute path to the backgrounds folder."""
        return os.path.join(self.get_image_folder(), self.config.backgrounds_folder)

    def get_teeth_folder(self) -> str:
        """Get the absolute path to the teeth images folder."""
        return os.path.join(self.get_image_folder(), self.config.teeth_folder)

    def get_selles_folder(self, model_type: str) -> str:
        """Get the absolute path to the dental saddles folder for a specific model.

        Args:
            model_type: Type of dental arch model ('arcade_inf' or 'arcade_sup')
        """
        if model_type == 'arcade_inf':
            return os.path.join(self.get_image_folder(), self.config.selles_inf_folder)
        elif model_type == 'arcade_sup':
            return os.path.join(self.get_image_folder(), self.config.selles_sup_folder)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

# Global configuration manager instance
config_manager = ConfigManager()

def get_config() -> AppConfig:
    """Get the global application configuration."""
    return config_manager.get_config()

def update_config(**kwargs) -> None:
    """Update the global application configuration."""
    config_manager.update_config(**kwargs)
