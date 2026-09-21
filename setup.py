"""
Configuración de cx_Freeze para YT Outlier Lab.
Detecta automáticamente las DLLs de Anaconda.
"""
import os
import sys
from pathlib import Path
from cx_Freeze import setup, Executable

# ── Detectar DLLs críticas (fix Anaconda) ───────────────────────
def find_dlls():
    """Busca DLLs necesarias en ubicaciones de Anaconda y Python estándar."""
    python_dir = Path(sys.executable).parent
    search_paths = [
        python_dir / "DLLs",
        python_dir / "Library" / "bin",
        python_dir / "Library" / "lib",
        python_dir,
        Path(sys.prefix) / "DLLs",
        Path(sys.prefix) / "Library" / "bin",
    ]

    # DLLs críticas a buscar
    critical = [
        "sqlite3.dll",
        "libcrypto-3-x64.dll",
        "libcrypto-1_1-x64.dll",
        "libssl-3-x64.dll",
        "libssl-1_1-x64.dll",
        "libffi-8.dll",
        "libffi-7.dll",
    ]

    include_files = []
    found = []

    for dll_name in critical:
        for path in search_paths:
            candidate = path / dll_name
            if candidate.exists():
                include_files.append((str(candidate), dll_name))
                found.append(dll_name)
                print(f"✅ DLL encontrada: {dll_name} → {candidate}")
                break

    # Agregar todas las DLLs de la carpeta DLLs
    dlls_dir = python_dir / "DLLs"
    if dlls_dir.exists():
        for dll in dlls_dir.glob("*.dll"):
            if dll.name not in found:
                include_files.append((str(dll), dll.name))
        for pyd in dlls_dir.glob("*.pyd"):
            include_files.append((str(pyd), pyd.name))

    # Anaconda Library/bin: agregar sqlite3 y crypto
    anaconda_bin = python_dir / "Library" / "bin"
    if anaconda_bin.exists():
        for pattern in ["sqlite3*.dll", "libcrypto*.dll", "libssl*.dll", "libffi*.dll"]:
            for dll in anaconda_bin.glob(pattern):
                if dll.name not in found:
                    include_files.append((str(dll), dll.name))
                    found.append(dll.name)
                    print(f"✅ DLL Anaconda: {dll.name}")

    return include_files


# ── Archivos y carpetas a incluir ───────────────────────────────
include_files = find_dlls()

# Carpetas de la aplicación
for folder in ["assets", "core", "dashboard", "connectors"]:
    if os.path.exists(folder):
        include_files.append((folder, folder))

# Archivos sueltos
for f in ["utils_app.py", "version.txt"]:
    if os.path.exists(f):
        include_files.append((f, f))

# ── Módulos ocultos que cx_Freeze no detecta ────────────────────
packages = [
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.sqlite.pysqlite",
    "dash",
    "dash.development",
    "dash.dcc",
    "dash.html",
    "plotly",
    "pandas",
    "numpy",
    "scipy", 
    "sklearn",
    "PIL",
    "requests",
    "dotenv",
    "langdetect",
    "google.auth",
    "googleapiclient",
]

includes = [
    "sqlite3",
    "sqlite3.dbapi2",
    "_sqlite3",
]

excludes = [
    "tkinter",
    "matplotlib",
    "IPython",
    "jupyter",
    "notebook",
    "pytest",
    "PyQt5", "PyQt6", "PySide2", "PySide6",
    "wx",
]

# ── Configuración de build ──────────────────────────────────────
build_exe_options = {
    "packages": packages,
    "includes": includes,
    "excludes": excludes,
    "include_files": include_files,
    "include_msvcr": False,  # Incluir Visual C++ Runtime
    "optimize": 2,
    "silent": 0,  # Mostrar progreso
}

# ── Ejecutable ──────────────────────────────────────────────────
base = None  # None = con consola (mejor para debug)
# base = "Win32GUI"  # Sin consola (descomenta cuando todo funcione)

executables = [
    Executable(
        script="run.py",
        base=base,
        target_name="YT-Outlier-Lab.exe",
        icon=None,  # Agrega "icon.ico" si tienes uno
        shortcut_name="YT Outlier Lab",
        shortcut_dir="DesktopFolder",
        copyright="YT Outlier Lab",
    )
]

# ── Setup ───────────────────────────────────────────────────────
setup(
    name="YT Outlier Lab",
    version="1.0.0",
    description="Herramienta de análisis de outliers de YouTube",
    options={"build_exe": build_exe_options},
    executables=executables,
)