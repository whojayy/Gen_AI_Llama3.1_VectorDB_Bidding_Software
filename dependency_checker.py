# improved_dependency_checker.py
import sys
import os
import importlib
import subprocess
import re

def get_installed_packages():
    """Get all installed packages using pip list"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'], 
                               capture_output=True, text=True, check=True)
        import json
        packages = json.loads(result.stdout)
        return {pkg['name'].lower(): pkg['version'] for pkg in packages}
    except Exception as e:
        print(f"Error getting installed packages: {e}")
        return {}

def scan_imports_in_file(file_path):
    """Scan a file for import statements and return a list of package names"""
    print(f"Scanning {file_path}...")
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find all import statements
            import_pattern = re.compile(r'^import\s+([\w\s,\.]+)', re.MULTILINE)
            from_pattern = re.compile(r'^from\s+([\w\.]+)\s+import', re.MULTILINE)
            
            # Process 'import x' statements
            for match in import_pattern.finditer(content):
                packages = match.group(1).split(',')
                for pkg in packages:
                    pkg = pkg.strip()
                    if ' as ' in pkg:
                        pkg = pkg.split(' as ')[0].strip()
                    if '.' in pkg:
                        pkg = pkg.split('.')[0].strip()
                    imports.add(pkg)
            
            # Process 'from x import y' statements
            for match in from_pattern.finditer(content):
                pkg = match.group(1)
                if '.' in pkg:
                    pkg = pkg.split('.')[0].strip()
                imports.add(pkg)
                
        print(f"  Found imports: {', '.join(imports)}")
        return imports
        
    except Exception as e:
        print(f"  Error scanning {file_path}: {e}")
        return set()

def is_standard_library(package_name):
    """Check if a package is part of the Python standard library"""
    if package_name in sys.builtin_module_names:
        return True
    
    standard_lib_dir = os.path.dirname(os.__file__)
    
    try:
        module_path = importlib.util.find_spec(package_name)
        if module_path is None:
            return False
        
        if hasattr(module_path, 'origin') and module_path.origin:
            return module_path.origin.startswith(standard_lib_dir)
        return False
    except (ImportError, AttributeError):
        return False

def create_requirements_file():
    """Create requirements.txt file based on imports in Python files"""
    # Get all installed packages
    installed_packages = get_installed_packages()
    print(f"Found {len(installed_packages)} installed packages")
    
    # Find all Python files
    python_files = []
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files")
    
    # Scan imports
    all_imports = set()
    for file_path in python_files:
        imports = scan_imports_in_file(file_path)
        all_imports.update(imports)
    
    print(f"Total unique imports found: {len(all_imports)}")
    
    # Filter out standard library modules
    third_party_imports = set()
    for pkg in all_imports:
        if not is_standard_library(pkg):
            third_party_imports.add(pkg)
    
    print(f"Third-party packages found: {len(third_party_imports)}")
    print(f"Packages: {', '.join(sorted(third_party_imports))}")
    
    # Create requirements.txt
    with open('requirements.txt', 'w') as f:
        for pkg_name in sorted(third_party_imports):
            pkg_lower = pkg_name.lower()
            if pkg_lower in installed_packages:
                f.write(f"{pkg_name}=={installed_packages[pkg_lower]}\n")
                print(f"Added {pkg_name}=={installed_packages[pkg_lower]}")
            else:
                # Try common variations of the package name
                found = False
                variations = [
                    pkg_name.replace('_', '-').lower(),
                    pkg_name.replace('-', '_').lower()
                ]
                
                for var in variations:
                    if var in installed_packages:
                        f.write(f"{pkg_name}=={installed_packages[var]}\n")
                        print(f"Added {pkg_name}=={installed_packages[var]}")
                        found = True
                        break
                
                if not found:
                    print(f"Warning: Could not find version for {pkg_name}")
                    f.write(f"{pkg_name}\n")
    
    print("\nRequirements file created successfully!")

# Add these known packages explicitly
def add_known_dependencies():
    """Add known dependencies that might be missed by the scanner"""
    with open('requirements.txt', 'a') as f:
        f.write("\n# Known dependencies\n")
        
        # Check if pandas is already in the file
        with open('requirements.txt', 'r') as check:
            content = check.read()
            if 'pandas' not in content:
                try:
                    import pandas
                    version = pandas.__version__
                    f.write(f"pandas=={version}\n")
                    print(f"Added pandas=={version}")
                except ImportError:
                    f.write("pandas\n")
                    print("Added pandas (version unknown)")
        
        # Add other known dependencies if needed
        try:
            import requests
            version = requests.__version__
            if 'requests' not in content:
                f.write(f"requests=={version}\n")
                print(f"Added requests=={version}")
        except ImportError:
            pass

if __name__ == "__main__":
    create_requirements_file()
    add_known_dependencies()