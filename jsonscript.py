import os
import json

GITHUB_USER = "SolderedElectronics"
GITHUB_REPO = "Soldered-MicroPython-Modules"
GITHUB_REPO_PREFIX = "github:" + GITHUB_USER + "/" + GITHUB_REPO
QWIIC_PREFIX = "github:" + GITHUB_USER + "/" + GITHUB_REPO
VERSION = "0.2"
QWIIC_ENTRY_NAME = "Qwiic.py"

def contains_qwiic_reference(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return "qwiic" in f.read().lower()
    except Exception as e:
        print(f"Could not read {file_path}: {e}")
        return False

def build_package_json(base_dir):
    package_data = {
        "urls": [],
        "deps": [],
        "version": VERSION
    }

    qwiic_needed = False

    base_folder_name = os.path.basename(os.path.abspath(base_dir))
    github_prefix = f"{GITHUB_REPO_PREFIX}/{base_folder_name}"

    for entry in os.scandir(base_dir):
        if not entry.is_dir():
            continue

        module_name = entry.name
        module_path = entry.path

        if os.path.exists(os.path.join(module_path, "package.json")):
            print(f"Skipping '{module_name}': package.json exists inside.")
            continue

        for root, _, files in os.walk(module_path):
            for file in files:
                if file == "package.json":
                    continue

                full_path = os.path.join(root, file)
                rel_path_inside_module = os.path.relpath(full_path, module_path).replace("\\", "/")
                github_path = f"{github_prefix}/{module_name}/{rel_path_inside_module}"

                # 🛠 Detect if it's in an Examples folder
                if "examples" in os.path.normpath(root).lower().split(os.sep):
                    board_path = f"Examples/{file}"
                else:
                    board_path = f"{file}"
                    if file.lower().endswith(".py") and contains_qwiic_reference(full_path):
                        qwiic_needed = True

                package_data["urls"].append([board_path, github_path])

    if qwiic_needed:
        qwiic_github_path = f"{QWIIC_PREFIX}/Qwiic/Qwiic.py"
        if [QWIIC_ENTRY_NAME, qwiic_github_path] not in package_data["urls"]:
            package_data["urls"].append([QWIIC_ENTRY_NAME, qwiic_github_path])
            print("✅ Added Qwiic dependency due to reference in module(s).")

    return package_data

def write_package_json(base_dir, package_data):
    output_path = os.path.join(base_dir, "package.json")
    with open(output_path, "w") as f:
        json.dump(package_data, f, indent=2)
    print(f"📦 Created root package.json at '{output_path}'.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python create_root_package.py <base_folder>")
        sys.exit(1)

    base_folder = sys.argv[1]
    package_data = build_package_json(base_folder)
    write_package_json(base_folder, package_data)
