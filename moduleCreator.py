import os
from datetime import date


def create_module_structure(base_category, module_name):
    today = date.today().isoformat()

    # Format names
    root_dir = os.path.join(base_category, module_name)
    module_dir = os.path.join(root_dir, module_name)
    examples_dir = os.path.join(module_dir, "Examples")

    # Create directories
    os.makedirs(examples_dir, exist_ok=True)

    # File paths
    module_file = os.path.join(module_dir, f"{module_name}.py")
    example_file = os.path.join(examples_dir, f"{module_name}_Example.py")

    # Template contents
    module_content = f"""# FILE: {module_name}.py 
# AUTHOR: Soldered
# BRIEF: 
# LAST UPDATED: {today} 
"""

    example_content = f"""# FILE: {module_name}-example.py 
# AUTHOR: Soldered
# BRIEF:  
# WORKS WITH: COMPONENT NAME: www.solde.red/SKU
# LAST UPDATED: {today} 
"""

    # Write files
    with open(module_file, "w") as f:
        f.write(module_content)
    with open(example_file, "w") as f:
        f.write(example_content)

    print(f"\nCreated module structure for '{module_name}' in category '{base_category}':")
    print(f"  - {module_file}")
    print(f"  - {example_file}")


if __name__ == "__main__":
    categories = {
        "1": "Sensors",
        "2": "Actuators",
        "3": "Communication",
        "4": "Displays"
    }

    try:
        print("Select a category for the module:")
        for key, name in categories.items():
            print(f"  {key}. {name}")

        choice = input("Enter the number corresponding to the category: ").strip()
        base_category = categories.get(choice)

        if not base_category:
            print("Invalid category selection.")
        else:
            module_name = input("Enter the module name: ").strip()
            if not module_name:
                print("Module name cannot be empty.")
            else:
                create_module_structure(base_category, module_name)
    except Exception as e:
        print(f"Error: {e}")
