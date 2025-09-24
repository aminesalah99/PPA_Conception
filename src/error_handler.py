
"""
Error Handler Module

This module provides centralized error handling for the application.
"""

import logging
import sys
import traceback
from tkinter import messagebox
from typing import Optional, Callable, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dental_design_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DentalDesignError(Exception):
    """Base exception class for the dental design application."""
    pass

class DatabaseError(DentalDesignError):
    """Exception raised for database-related errors."""
    pass

class ImageProcessingError(DentalDesignError):
    """Exception raised for image processing errors."""
    pass

class ConfigurationError(DentalDesignError):
    """Exception raised for configuration-related errors."""
    pass

class UserInputError(DentalDesignError):
    """Exception raised for invalid user input."""
    pass

def handle_error(error: Exception, 
                message: str = "Une erreur est survenue", 
                show_traceback: bool = False,
                logger: Optional[logging.Logger] = None) -> None:
    """
    Handle an error by logging it and showing a user-friendly message.

    Args:
        error: The exception that was raised
        message: User-friendly error message
        show_traceback: Whether to show the full traceback to the user
        logger: Logger instance to use (defaults to module logger)
    """
    if logger is None:
        logger = globals().get('logger')

    # Log the full error details
    error_details = f"{type(error).__name__}: {str(error)}"
    logger.error(error_details, exc_info=True)

    # Show user-friendly message
    if show_traceback:
        full_message = f"{message}\n\nDétails techniques:\n{error_details}"
        messagebox.showerror("Erreur", full_message)
    else:
        messagebox.showerror("Erreur", message)

def safe_execute(func: Callable, 
                error_message: str = "Une erreur est survenue lors de l'exécution de cette opération",
                default_return: Any = None,
                logger: Optional[logging.Logger] = None,
                show_traceback: bool = False) -> Any:
    """
    Execute a function with error handling.

    Args:
        func: The function to execute
        error_message: User-friendly error message if the function fails
        default_return: Value to return if the function fails
        logger: Logger instance to use
        show_traceback: Whether to show the full traceback to the user

    Returns:
        The result of the function or default_return if an error occurred
    """
    try:
        return func()
    except Exception as e:
        handle_error(e, error_message, show_traceback, logger)
        return default_return

def log_and_continue(error: Exception, 
                    message: str = "Une erreur mineure est survenue, l'opération continue",
                    logger: Optional[logging.Logger] = None) -> None:
    """
    Log an error but continue execution.

    Args:
        error: The exception that was raised
        message: User-friendly error message
        logger: Logger instance to use
    """
    if logger is None:
        logger = globals().get('logger')

    # Log the error
    logger.warning(f"{message}: {str(error)}", exc_info=True)

    # Optionally show a non-intrusive message to the user
    # This could be implemented as a status bar message or a small notification
