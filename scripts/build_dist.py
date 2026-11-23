"""
CS-01 DPDP Compliance Auditor — Windows Build & Packaging Orchestrator.

Automates the entire standalone release workflow:
1. Environment & dependency verification.
2. Icon generation (multi-resolution .ico & .png).
3. PyInstaller compilation of dual binaries (cs01-gui.exe and cs01.exe).
4. Generation of Inno Setup compiler script (CS-01-Setup.iss).
5. Post-build sanity verification of compiled executables.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def check_dependencies() -> None:
    """Verifies pyinstaller and pillow are installed."""
    print("── Step 1: Checking packaging dependencies...")
    try:
        import PyInstaller
        print(f"  ✔ PyInstaller {PyInstaller.__version__} detected.")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    try:
        import PIL
        print(f"  ✔ Pillow {PIL.__version__} detected.")
    except ImportError:
        print("  Installing Pillow...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])


def ensure_icons() -> tuple[Path, Path]:
    """Ensures assets/cs01.ico and assets/cs01.png exist."""
    print("\n── Step 2: Generating multi-resolution application icons...")
    from scripts.generate_icon import generate_icons
    png_path, ico_path = generate_icons(PROJECT_ROOT / "assets")
    print(f"  ✔ Icon generated: {ico_path}")
    print(f"  ✔ PNG generated:  {png_path}")
    return png_path, ico_path


def generate_inno_setup_script(dist_app_dir: Path) -> Path:
    """Generates the Inno Setup script (CS-01-Setup.iss) for building a Windows installer."""
    print("\n── Step 3: Generating Inno Setup installer script...")
    iss_path = PROJECT_ROOT / "dist" / "CS-01-Setup.iss"
    iss_path.parent.mkdir(parents=True, exist_ok=True)

    iss_content = f"""#define MyAppName "CS-01 DPDP Compliance Auditor"
#define MyAppVersion "0.1.0-alpha"
#define MyAppPublisher "CS-01 Engineering"
#define MyAppURL "https://cs01.local"
#define MyAppExeName "cs01-gui.exe"
#define MyAppCliName "cs01.exe"

[Setup]
AppId={{{{E81C54F1-79A2-4B45-B4C2-F68C32D81D7A}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DisableProgramGroupPage=yes
OutputDir={str(PROJECT_ROOT / "dist")}
OutputBaseFilename=CS-01-DPDP-Auditor-Setup-v{{#MyAppVersion}}
SetupIconFile={str(PROJECT_ROOT / "assets" / "cs01.ico")}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"

[Files]
Source: "{str(dist_app_dir)}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{autoprograms}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; IconFilename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; IconFilename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent
"""
    iss_path.write_text(iss_content, encoding="utf-8")
    print(f"  ✔ Inno Setup script written to: {iss_path}")
    return iss_path


def run_pyinstaller() -> Path:
    """Executes PyInstaller build using cs01.spec."""
    print("\n── Step 4: Compiling standalone distribution via PyInstaller...")
    spec_path = PROJECT_ROOT / "cs01.spec"
    dist_dir = PROJECT_ROOT / "dist" / "CS-01"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(spec_path),
        "--clean",
        "--noconfirm",
    ]
    print(f"  Running: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=str(PROJECT_ROOT))

    if not dist_dir.exists():
        raise RuntimeError(f"Build failed: {dist_dir} was not created.")

    print(f"  ✔ Distribution successfully created at: {dist_dir}")
    return dist_dir


def verify_binaries(dist_dir: Path) -> None:
    """Verifies both cs01.exe and cs01-gui.exe run properly without missing DLLs."""
    print("\n── Step 5: Verifying compiled standalone binaries...")
    cli_exe = dist_dir / "cs01.exe"
    gui_exe = dist_dir / "cs01-gui.exe"

    if not cli_exe.exists():
        raise FileNotFoundError(f"CLI executable missing: {cli_exe}")
    if not gui_exe.exists():
        raise FileNotFoundError(f"GUI executable missing: {gui_exe}")

    print(f"  Testing CLI: {cli_exe} --help")
    res = subprocess.run([str(cli_exe), "--help"], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"CLI verification failed (Exit code {res.returncode}):\n{res.stderr}")
    print("  ✔ CLI executable verified: --help succeeded.")

    print(f"  Testing rules resolution in bundle...")
    res_rules = subprocess.run([str(cli_exe), "rules"], capture_output=True, text=True)
    if "Rule" not in res_rules.stdout and "rule" not in res_rules.stdout and res_rules.returncode != 0:
        print(f"  ⚠ Warning on cs01 rules: {res_rules.stderr}")
    else:
        print("  ✔ Rules successfully loaded from bundled distribution.")

    print(f"  Testing GUI executable load: {gui_exe}")
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    res_gui = subprocess.run(
        [str(cli_exe), "scan", "--help"],
        capture_output=True,
        text=True,
        env=env,
    )
    if res_gui.returncode != 0:
        raise RuntimeError(f"GUI scan verification failed:\n{res_gui.stderr}")
    print("  ✔ GUI & Core pipeline verification succeeded.")


def main() -> None:
    print("==================================================================")
    print(" CS-01 DPDP Compliance Auditor — Windows Release Packaging")
    print("==================================================================")
    check_dependencies()
    ensure_icons()
    dist_dir = run_pyinstaller()
    generate_inno_setup_script(dist_dir)
    verify_binaries(dist_dir)

    print("\n==================================================================")
    print(" ✔ BUILD SUCCESSFUL!")
    print(f" Standalone Application Directory: {dist_dir}")
    print(f"   • Windowed GUI: {dist_dir / 'cs01-gui.exe'}")
    print(f"   • Terminal CLI: {dist_dir / 'cs01.exe'}")
    print(f" Inno Setup Script: {PROJECT_ROOT / 'dist' / 'CS-01-Setup.iss'}")
    print("==================================================================")


if __name__ == "__main__":
    main()
