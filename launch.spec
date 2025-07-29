# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all
import os
import gradio_client

block_cipher = None

# Get package paths for explicit data inclusion
gradio_client_path = os.path.dirname(gradio_client.__file__)

# Try to get other package paths safely
try:
    import safehttpx
    safehttpx_path = os.path.dirname(safehttpx.__file__)
except ImportError:
    safehttpx_path = None

try:
    import groovy
    groovy_path = os.path.dirname(groovy.__file__)
except ImportError:
    groovy_path = None

# Collect all data and hidden imports for problematic packages
inquirer_datas, inquirer_binaries, inquirer_hiddenimports = collect_all('inquirer')
readchar_datas, readchar_binaries, readchar_hiddenimports = collect_all('readchar')
keyring_datas, keyring_binaries, keyring_hiddenimports = collect_all('keyring')
gradio_datas, gradio_binaries, gradio_hiddenimports = collect_all('gradio')

# Collect additional packages
safehttpx_datas, safehttpx_binaries, safehttpx_hiddenimports = collect_all('safehttpx') if safehttpx_path else ([], [], [])
groovy_datas, groovy_binaries, groovy_hiddenimports = collect_all('groovy') if groovy_path else ([], [], [])

# Explicitly add critical data files
additional_datas = [
    (os.path.join(gradio_client_path, 'types.json'), 'gradio_client'),
    (os.path.join(gradio_client_path, 'package.json'), 'gradio_client'),
]

# Add safehttpx version.txt if available
if safehttpx_path and os.path.exists(os.path.join(safehttpx_path, 'version.txt')):
    additional_datas.append((os.path.join(safehttpx_path, 'version.txt'), 'safehttpx'))

# Add groovy version.txt if available
if groovy_path and os.path.exists(os.path.join(groovy_path, 'version.txt')):
    additional_datas.append((os.path.join(groovy_path, 'version.txt'), 'groovy'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[] + inquirer_binaries + readchar_binaries + keyring_binaries + gradio_binaries + safehttpx_binaries + groovy_binaries,
    datas=[] + inquirer_datas + readchar_datas + keyring_datas + gradio_datas + safehttpx_datas + groovy_datas + additional_datas,
    hiddenimports=[
        'keyring.backends.macOS',
        'keyring.backends.OS_X',
        'keyring.backends.SecretService',
        'inquirer',
        'inquirer.themes',
        'inquirer.themes.GreenPassion',
        'inquirer.render.console',
        'inquirer.events',
        'readchar',
        'readchar.readkey',
        'blessed',
        'blessed.terminal',
        'blessed.keyboard',
        'blessed.sequences',
        'importlib.metadata',
        'importlib_metadata',
        # Gradio dependencies
        'gradio',
        'gradio.interface',
        'gradio.components',
        'gradio.utils',
        'gradio.blocks',
        'gradio.routes',
        'gradio.processing_utils',
        'gradio.external',
        'gradio.flagging',
        'gradio.interpretation',
        'gradio.mix',
        'gradio.outputs',
        'gradio.inputs',
        'gradio_client',
        'gradio_client.utils',
        'fastapi',
        'uvicorn',
        'starlette',
        'httpx',
        'websockets',
        'typing_extensions',
        'pydantic',
        'jinja2',
        'markupsafe',
        'pkg_resources',
        'safehttpx',
        'groovy',
    ] + inquirer_hiddenimports + readchar_hiddenimports + keyring_hiddenimports + gradio_hiddenimports + safehttpx_hiddenimports + groovy_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Explicitly exclude user config and backup files/folders
        '.ssh_manager_config.json',
        'backup',
        'backup/*',
        '*.json',  # Exclude any JSON config files
        '.git',
        '.git/*',
        '.venv',
        '.venv/*',
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '.DS_Store',
        'Thumbs.db',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='launch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)