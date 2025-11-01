#!/usr/bin/env python3
"""
Blender Python script to create scene "object_1" and import object1.glb
This script is executed by Blender when starting via the shell script.
It works with the main.blend file that is opened.
"""

import bpy
import os
import sys

# Force output to be visible immediately
sys.stdout.flush()
sys.stderr.flush()

# Get the project root directory
# The script is in blender/load_object1.py, so go up one level to get project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Go up from blender/ to project root
glb_path = os.path.join(project_root, "3d", "object1.glb")

def create_scene_and_import():
    """Create new scene called 'object_1' and import the .glb file"""
    
    # Check if the .glb file exists
    if not os.path.exists(glb_path):
        print(f"ERROR: GLB file not found at {glb_path}")
        return False
    
    # Get or create the scene
    scene_name = "object_1"
    
    # If scene already exists, switch to it and clear it
    if scene_name in bpy.data.scenes:
        scene = bpy.data.scenes[scene_name]
        bpy.context.window.scene = scene
        # Clear existing objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
    else:
        # Create new scene
        scene = bpy.data.scenes.new(name=scene_name)
        bpy.context.window.scene = scene
    
    # Clear the default cube, light, and camera
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Import the .glb file
    try:
        print(f"Importing GLB file: {glb_path}")
        # Use bpy.ops.import_scene.gltf to import .glb/.gltf files
        bpy.ops.import_scene.gltf(filepath=glb_path)
        print("Successfully imported GLB file!")
        
        # Frame the imported objects in the viewport
        bpy.ops.view3d.view_all()
        
        return True
    except Exception as e:
        print(f"ERROR importing GLB file: {str(e)}")
        return False

if __name__ == "__main__":
    # Flush output immediately so it's visible
    sys.stdout.flush()
    sys.stderr.flush()
    
    print("\n" + "="*60, flush=True)
    print("LOAD_OBJECT1.PY: Starting Blender startup script", flush=True)
    print("="*60, flush=True)
    sys.stdout.flush()
    
    # Create scene and import object
    print("\n[STEP 1] Creating scene and importing GLB file", flush=True)
    sys.stdout.flush()
    create_scene_and_import()
    sys.stdout.flush()
    
    print("\n" + "="*60, flush=True)
    print("LOAD_OBJECT1.PY: Startup script completed!", flush=True)
    print("="*60, flush=True)
    print("\nNote: Addon is NOT automatically loaded.", flush=True)
    print("To load the addon, paste the code from README.md into Blender's Python console.", flush=True)
    sys.stdout.flush()

