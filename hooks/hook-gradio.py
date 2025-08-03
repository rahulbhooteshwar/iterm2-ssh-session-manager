# PyInstaller runtime hook for Gradio
# This hook ensures Gradio frontend assets are properly loaded in bundled applications

import os
import sys
from pathlib import Path

# Ensure Gradio can find its frontend assets when bundled
def _setup_gradio_frontend():
    """Setup Gradio frontend assets for PyInstaller bundled applications"""
    try:
        import gradio

        # Get the base path for the bundled application
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_path = Path(sys._MEIPASS)
        else:
            # Running in normal Python environment
            base_path = Path(gradio.__file__).parent

        # Set environment variables to help Gradio find its assets
        os.environ.setdefault('GRADIO_FRONTEND_PATH', str(base_path / 'frontend'))
        os.environ.setdefault('GRADIO_TEMPLATES_PATH', str(base_path / 'templates'))
        os.environ.setdefault('GRADIO_THEMES_PATH', str(base_path / 'themes'))
        os.environ.setdefault('GRADIO_ASSETS_PATH', str(base_path / 'assets'))

        # Monkey patch Gradio's asset loading if needed
        try:
            from gradio import utils
            original_get_asset_path = utils.get_asset_path

            def patched_get_asset_path(asset_name):
                """Patched version that handles bundled assets"""
                try:
                    return original_get_asset_path(asset_name)
                except (FileNotFoundError, OSError):
                    # Try alternative paths in bundled environment
                    if getattr(sys, 'frozen', False):
                        for search_path in ['frontend', 'templates', 'themes', 'assets']:
                            alt_path = base_path / search_path / asset_name
                            if alt_path.exists():
                                return str(alt_path)
                    raise

            utils.get_asset_path = patched_get_asset_path
        except (ImportError, AttributeError):
            pass

    except ImportError:
        pass

# Call the setup function when this hook is loaded
_setup_gradio_frontend()