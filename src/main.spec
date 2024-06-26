import os
from PyInstaller.utils.hooks import collect_submodules

# Manually set the absolute path to your project directory
project_dir = 'C:/Users/pedro.neto/PycharmProjects/avaliadorRetiradaDoIcmsBC/src'

block_cipher = None

a = Analysis(
    [os.path.join(project_dir, 'app.py')],
    pathex=[project_dir],
    binaries=[],
    datas=[
        (os.path.join(project_dir, 'utils', 'docs', '*'), 'utils/docs'),
        (os.path.join(project_dir, 'utils', 'extractor', '*'), 'utils/extractor'),
        (os.path.join(project_dir, 'utils', 'speds', '*'), 'utils/speds'),
        (os.path.join(project_dir, 'assets', 'icon.ico'), 'assets'),
        (os.path.join(project_dir, 'assets', 'LOGOS_KOMBUSINESS_FUNDOESCURO_V2.png'), 'assets')
    ],
    hiddenimports=collect_submodules('openpyxl'),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Retirada ICMS da base de Cálculo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=os.path.join(project_dir, 'assets', 'icon.ico')
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Retirada ICMS da base de Cálculo'
)
