# blender-object-inspector
blender-object-inspector

═══════════════════════════════════════════════════════════════
ASTE THIS INTO BLENDER'S PYTHON CONSOLE TO REGISTER ADDON
═══════════════════════════════════════════════════════════════


import bpy, os, sys, importlib.util
script_dir = "./blender"  # UPDATE THIS PATH
spec = importlib.util.spec_from_file_location("functions", os.path.join(script_dir, "functions.py"))
functions_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(functions_module)
functions_module.load_and_register()


═══════════════════════════════════════════════════════════════
UTILS
═══════════════════════════════════════════════════════════════

- Select both bounding box and 3D object
- Add Modifier - Modifier Properties
- Add Modifier - Boolean
- Select the 3D mesh and click Apply from the dropdown