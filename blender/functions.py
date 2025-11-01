"""
Blender Add-on: Smooth Object
Creates a smoothed clone of the selected object next to the original.
Based on Blender Add-on Tutorial: https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html
"""

bl_info = {
    "name": "Object Inspector Tools",
    "author": "Blender Object Inspector",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > object_inspector",
    "description": "Tools to add textures to meshes from image files",
    "category": "Object",
}

import bpy
from mathutils import Vector


class OBJECT_OT_AddTexture(bpy.types.Operator):
    """Add texture from image file to the selected mesh"""
    bl_idname = "object.add_texture"
    bl_label = "Add Texture"
    bl_options = {'REGISTER', 'UNDO'}

    image_path: bpy.props.StringProperty(
        name="Image Path",
        description="Path to the image file (jpg, png, etc.)",
        default="",
        subtype='FILE_PATH'
    )

    @classmethod
    def poll(cls, context):
        """Only enable if there's an active object and it's a mesh"""
        return (
            context.active_object is not None and
            context.active_object.type == 'MESH'
        )

    def execute(self, context):
        """Load image and apply as texture to the mesh"""
        try:
            import os
            
            obj = context.active_object
            
            if obj is None or obj.type != 'MESH':
                self.report({'ERROR'}, "Please select a mesh object!")
                return {'CANCELLED'}
            
            # Check if image path is provided
            if not self.image_path or not self.image_path.strip():
                self.report({'ERROR'}, "Please provide an image path!")
                return {'CANCELLED'}
            
            # Expand path (handle ~ and relative paths)
            image_path = os.path.expanduser(os.path.expandvars(self.image_path))
            image_path = os.path.abspath(image_path)
            
            # Check if file exists
            if not os.path.exists(image_path):
                self.report({'ERROR'}, f"Image file not found: {image_path}")
                return {'CANCELLED'}
            
            # Ensure we're in Object mode
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Load the image
            try:
                # Check if image is already loaded
                image_name = os.path.basename(image_path)
                image = None
                for img in bpy.data.images:
                    if img.filepath == image_path or (img.filepath_raw and os.path.abspath(bpy.path.abspath(img.filepath_raw)) == image_path):
                        image = img
                        break
                
                if image is None:
                    image = bpy.data.images.load(image_path)
                else:
                    # Reload if it exists
                    image.reload()
                
            except Exception as e:
                self.report({'ERROR'}, f"Failed to load image: {str(e)}")
                return {'CANCELLED'}
            
            # Create or get material
            material_name = f"{obj.name}_Material"
            if material_name in bpy.data.materials:
                material = bpy.data.materials[material_name]
            else:
                material = bpy.data.materials.new(name=material_name)
            
            # CRITICAL: Use nodes for the material (required for textures)
            material.use_nodes = True
            
            # Get the node tree (only available when use_nodes is True)
            nodes = material.node_tree.nodes
            links = material.node_tree.links
            
            # Clear all existing nodes and start fresh
            nodes.clear()
            
            # Create output node
            output = nodes.new(type='ShaderNodeOutputMaterial')
            output.location = (300, 0)
            
            # Create Principled BSDF node
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            bsdf.location = (0, 0)
            links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
            
            # Check if mesh has UV coordinates, create if needed
            mesh = obj.data
            current_mode = context.mode
            
            if not mesh.uv_layers:
                # No UV coordinates - create them
                # Ensure we're in Object mode
                if current_mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
                
                # Select object and enter Edit mode
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                
                # Select all faces
                bpy.ops.mesh.select_all(action='SELECT')
                
                # Unwrap using Smart Project or Angle Based
                try:
                    bpy.ops.uv.smart_project()
                except:
                    try:
                        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
                    except:
                        # Fallback: simple unwrap
                        bpy.ops.uv.unwrap(method='CONFORMAL', margin=0.001)
                
                # Return to original mode or Object mode
                bpy.ops.object.mode_set(mode='OBJECT')
                self.report({'INFO'}, "Created UV coordinates for mesh")
            
            # Create UV Map node (must come before Image Texture)
            uv_map_node = nodes.new(type='ShaderNodeUVMap')
            uv_map_node.location = (-600, 0)
            # Use the first UV layer
            if mesh.uv_layers:
                uv_map_node.uv_map = mesh.uv_layers[0].name
                self.report({'INFO'}, f"Using UV layer: {mesh.uv_layers[0].name}")
            
            # Create Image Texture node
            tex_node = nodes.new(type='ShaderNodeTexImage')
            tex_node.location = (-300, 0)
            tex_node.image = image
            
            # CRITICAL: Connect UV Map to Image Texture's Vector input
            # This tells the texture to use UV coordinates for mapping
            if "Vector" in tex_node.inputs and "UV" in uv_map_node.outputs:
                links.new(uv_map_node.outputs['UV'], tex_node.inputs['Vector'])
                self.report({'INFO'}, "Connected UV Map to Image Texture")
            
            # Connect texture Color output to BSDF Base Color input
            if "Color" in tex_node.outputs and "Base Color" in bsdf.inputs:
                links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
                self.report({'INFO'}, "Connected texture to Base Color")
            
            # Assign material to object (or replace existing)
            if obj.data.materials:
                obj.data.materials[0] = material
            else:
                obj.data.materials.append(material)
            
            # Set viewport shading to Material Preview to see the texture
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.shading.type = 'MATERIAL'
                            area.tag_redraw()
                            break
                    break
            
            self.report({'INFO'}, f"Texture applied: {os.path.basename(image_path)}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error adding texture: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


class OBJECT_OT_CreateFittingRectangle(bpy.types.Operator):
    """Create a box large enough to fit the selected mesh inside, placed beside it"""
    bl_idname = "object.create_fitting_rectangle"
    bl_label = "Create Fitting Box"
    bl_options = {'REGISTER', 'UNDO'}

    padding: bpy.props.FloatProperty(
        name="Padding",
        description="Extra space around the mesh",
        default=0.1,
        min=0.0,
        max=1.0
    )
    
    side_spacing: bpy.props.FloatProperty(
        name="Side Spacing",
        description="Space between mesh and box",
        default=1.0,
        min=0.0,
        max=10.0
    )

    @classmethod
    def poll(cls, context):
        """Only enable if there's an active object and it's a mesh"""
        return (
            context.active_object is not None and
            context.active_object.type == 'MESH'
        )

    def execute(self, context):
        """Create rectangle that fits the selected mesh"""
        try:
            obj = context.active_object
            
            if obj is None or obj.type != 'MESH':
                self.report({'ERROR'}, "Please select a mesh object!")
                return {'CANCELLED'}
            
            # Ensure we're in Object mode
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Calculate bounding box of the selected mesh
            # Get all corners in world space
            matrix_world = obj.matrix_world
            bbox_corners = [matrix_world @ Vector(corner) for corner in obj.bound_box]
            
            # Find min and max in each axis
            bbox_min = Vector((
                min(c.x for c in bbox_corners),
                min(c.y for c in bbox_corners),
                min(c.z for c in bbox_corners)
            ))
            bbox_max = Vector((
                max(c.x for c in bbox_corners),
                max(c.y for c in bbox_corners),
                max(c.z for c in bbox_corners)
            ))
            
            # Calculate size with padding (for all 3 dimensions to create a box)
            bbox_size = bbox_max - bbox_min
            box_width = bbox_size.x + (self.padding * 2)
            box_length = bbox_size.y + (self.padding * 2)
            box_height = bbox_size.z + (self.padding * 2)
            
            # Create a cube/box that fits the mesh
            # Create a unit cube (size=1 means 1 unit per side, so scale will be direct)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
            
            box_obj = context.active_object
            box_obj.name = f"{obj.name}_FittingBox"
            
            # Scale the cube to match the exact box dimensions
            # Since we start with size=1, we scale directly by the dimensions
            box_obj.scale.x = box_width
            box_obj.scale.y = box_length
            box_obj.scale.z = box_height
            
            # Calculate offset to place box beside the mesh (to the right on X axis)
            mesh_center_x = (bbox_min.x + bbox_max.x) / 2
            mesh_size_x = bbox_max.x - bbox_min.x
            box_center_x = mesh_center_x + (mesh_size_x / 2) + (box_width / 2) + self.side_spacing
            
            # Position the box (centered on mesh's Y and Z, offset on X)
            box_obj.location.x = box_center_x
            box_obj.location.y = (bbox_min.y + bbox_max.y) / 2
            box_obj.location.z = (bbox_min.z + bbox_max.z) / 2
            
            # Select both objects
            obj.select_set(True)
            box_obj.select_set(True)
            context.view_layer.objects.active = box_obj
            
            self.report({'INFO'}, f"Created fitting box: {box_obj.name}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating box: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}




class OBJECT_OT_CreateMouldBox(bpy.types.Operator):
    """Create a mould box with cavity of the mesh, cut in half to see inside"""
    bl_idname = "object.create_mould_box"
    bl_label = "Mould Box"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Only enable if there's an active object and it's a mesh, and a fitting box exists"""
        if context.active_object is None or context.active_object.type != 'MESH':
            return False
        
        # Check if there's a fitting box in the scene
        obj_name = context.active_object.name
        fitting_box_name = f"{obj_name}_FittingBox"
        return fitting_box_name in bpy.data.objects

    def execute(self, context):
        """Create mould box with cavity and cut in half"""
        try:
            obj = context.active_object  # Original mesh
            
            if obj is None or obj.type != 'MESH':
                self.report({'ERROR'}, "Please select the original mesh object!")
                return {'CANCELLED'}
            
            # Find the fitting box
            fitting_box_name = f"{obj.name}_FittingBox"
            if fitting_box_name not in bpy.data.objects:
                self.report({'ERROR'}, f"Fitting box '{fitting_box_name}' not found! Create it first.")
                return {'CANCELLED'}
            
            fitting_box = bpy.data.objects[fitting_box_name]
            
            # Ensure we're in Object mode
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Deselect all
            bpy.ops.object.select_all(action='DESELECT')
            
            # Calculate where mould box should be positioned (around the original mesh)
            # CRITICAL: The mould box must be positioned AROUND the mesh, not beside it
            # This is the key to making the boolean operation work - they must overlap
            # Get the original mesh center in world space
            obj_bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            obj_min = Vector((
                min(c.x for c in obj_bbox),
                min(c.y for c in obj_bbox),
                min(c.z for c in obj_bbox)
            ))
            obj_max = Vector((
                max(c.x for c in obj_bbox),
                max(c.y for c in obj_bbox),
                max(c.z for c in obj_bbox)
            ))
            obj_center = (obj_min + obj_max) / 2
            
            # Get fitting box dimensions (scale values)
            fitting_box_width = fitting_box.scale.x * 2  # Scale * 2 for size=1 cube
            fitting_box_length = fitting_box.scale.y * 2
            fitting_box_height = fitting_box.scale.z * 2
            
            # Create a SOLID box for the mould (following video technique at 3:57)
            # Create a new cube and position it around the mesh
            bpy.ops.mesh.primitive_cube_add(size=1, location=obj_center)
            
            mould_box = context.active_object
            mould_box.name = f"{obj.name}_MouldBox"
            
            # Scale the cube to match fitting box dimensions (solid box)
            fitting_box_scale = fitting_box.scale.copy()
            mould_box.scale = fitting_box_scale
            
            # Apply scale to make it a solid box (bake scale into geometry)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            
            # Get mould box top position to position mesh trespassing through it
            mould_box_bbox = [mould_box.matrix_world @ Vector(corner) for corner in mould_box.bound_box]
            mould_box_top_z = max(c.z for c in mould_box_bbox)
            mould_box_bottom_z = min(c.z for c in mould_box_bbox)
            mould_box_height = mould_box_top_z - mould_box_bottom_z
            
            # Get original mesh bounds to calculate how much it extends
            obj_bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            obj_bottom_z = min(c.z for c in obj_bbox)
            obj_top_z = max(c.z for c in obj_bbox)
            obj_height = obj_top_z - obj_bottom_z
            
            # Now duplicate the mesh and position it so it trespasses the top part of the box
            obj.select_set(True)
            mould_box.select_set(False)
            context.view_layer.objects.active = obj
            bpy.ops.object.duplicate()
            
            mesh_copy = context.active_object
            mesh_copy.name = f"{obj.name}_MouldMesh"
            
            # Copy mesh and position it relative to MOULD BOX (not original mesh)
            # Position it so it trespasses the top part of the box
            
            # Get mesh local bounds for positioning
            obj_local_bbox = [Vector(corner) for corner in obj.bound_box]
            obj_local_min_z = min(c.z for c in obj_local_bbox)
            obj_local_max_z = max(c.z for c in obj_local_bbox)
            obj_local_height = obj_local_max_z - obj_local_min_z
            obj_local_center_offset_z = (obj_local_min_z + obj_local_max_z) / 2
            
            # Position mesh copy relative to mould box - trespassing the top
            mesh_top_position_z = mould_box_top_z + (obj_local_height / 2) - obj_local_center_offset_z
            mesh_copy.location = Vector((
                mould_box.location.x,  # Centered on mould box
                mould_box.location.y,  # Centered on mould box
                mesh_top_position_z    # Extends above box top
            ))
            mesh_copy.rotation_euler = mould_box.rotation_euler.copy()
            mesh_copy.scale = mould_box.scale.copy()
            
            # Apply transforms on mesh copy
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            
            # Ensure both objects are visible
            mould_box.hide_set(False)
            mould_box.hide_viewport = False
            mesh_copy.hide_set(False)
            mesh_copy.hide_viewport = False
            
            # Make sure both are in the same collection
            if mould_box.users_collection:
                target_collection = mould_box.users_collection[0]
                if mesh_copy.name not in target_collection.objects:
                    target_collection.objects.link(mesh_copy)
            
            # Apply boolean difference to subtract mesh from box (creates cavity)
            bpy.ops.object.select_all(action='DESELECT')
            mould_box.select_set(True)
            mesh_copy.select_set(True)
            context.view_layer.objects.active = mould_box
            
            context.view_layer.update()
            bpy.context.view_layer.depsgraph.update()
            
            bool_mod = mould_box.modifiers.new(name="BooleanCavity", type='BOOLEAN')
            bool_mod.operation = 'DIFFERENCE'
            bool_mod.object = mesh_copy
            bool_mod.solver = 'FAST'
            bool_mod.use_self = False
            
            mould_box.update_tag()
            context.view_layer.update()
            bpy.context.view_layer.depsgraph.update()
            
            # Apply the boolean modifier to create the cavity
            result = bpy.ops.object.modifier_apply(modifier="BooleanCavity")
            
            if 'FINISHED' not in result:
                self.report({'WARNING'}, f"Boolean operation failed: {result}")
            else:
                self.report({'INFO'}, "Boolean cavity created successfully")
            
            # Keep the mesh copy visible inside the mould box (don't delete it)
            # The mesh copy stays inside the mould box to show the structure
            
            
            # Position mould box beside the fitting box (after boolean operations are done)
            # Calculate final position
            mould_box_bbox = [mould_box.matrix_world @ Vector(corner) for corner in mould_box.bound_box]
            mould_box_size = Vector((
                max(c.x for c in mould_box_bbox) - min(c.x for c in mould_box_bbox),
                max(c.y for c in mould_box_bbox) - min(c.y for c in mould_box_bbox),
                max(c.z for c in mould_box_bbox) - min(c.z for c in mould_box_bbox)
            ))
            
            # Calculate offset to move both mould box and mesh copy together
            offset_x = (fitting_box.location.x + mould_box_size.x + 1.0) - mould_box.location.x
            
            # Move both mould box and mesh copy together
            mould_box.location.x += offset_x
            mesh_copy.location.x += offset_x
            
            # Select mould box
            mould_box.select_set(True)
            context.view_layer.objects.active = mould_box
            
            self.report({'INFO'}, f"Created mould box: {mould_box.name}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating mould box: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


class VIEW3D_PT_ObjectInspector(bpy.types.Panel):
    """Panel with buttons for object inspector tools"""
    bl_label = "Object Inspector"
    bl_idname = "VIEW3D_PT_object_inspector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "object_inspector"  # Custom category name

    @classmethod
    def poll(cls, context):
        """Panel is always visible in the viewport"""
        return True

    def draw(self, context):
        layout = self.layout
        
        obj = context.active_object
        
        # Show object info - updates automatically on selection change
        if obj is None:
            layout.label(text="No object selected", icon='INFO')
            return
        
        if obj.type != 'MESH':
            layout.label(text=f"Selected: {obj.name} ({obj.type})", icon='INFO')
            layout.label(text="Select a mesh object to use tools", icon='MESH_DATA')
            return
        
        # Display current selected object - this updates automatically when selection changes
        box = layout.box()
        box.label(text=f"Object: {obj.name}", icon='MESH_DATA')
        
        # Show basic object info
        row = box.row()
        row.label(text=f"Type: {obj.type}")
        row.label(text=f"Mode: {context.mode}")
        
        layout.separator()
        
        # Texture section
        layout.label(text="Texture", icon='TEXTURE')
        
        # Image path input field
        row = layout.row()
        row.prop(context.scene, "object_inspector_texture_path", text="")
        row.label(text="", icon='FILE_IMAGE')
        
        # Add Texture button
        row = layout.row()
        row.scale_y = 1.5
        op = row.operator("object.add_texture", text="Add Texture", icon='TEXTURE_DATA')
        # Pass the scene property value to operator
        op.image_path = context.scene.object_inspector_texture_path
        
        layout.separator()
        
        # Create Fitting Box button
        layout.label(text="Utilities", icon='MODIFIER_ON')
        op_rect = layout.operator("object.create_fitting_rectangle", text="Create Fitting Box", icon='MESH_CUBE')
        op_rect.padding = 0.1
        op_rect.side_spacing = 1.0
        
        layout.separator()
        
        # Mould Box button
        op_mould = layout.operator("object.create_mould_box", text="Mould Box", icon='MODIFIER_ON')


def menu_func(self, context):
    """Add to Object menu"""
    self.layout.separator()
    self.layout.operator(OBJECT_OT_AddTexture.bl_idname)
    self.layout.operator(OBJECT_OT_CreateFittingRectangle.bl_idname)
    self.layout.operator(OBJECT_OT_CreateMouldBox.bl_idname)


class OBJECT_INSPECTOR_TexturePath(bpy.types.PropertyGroup):
    """Property group to store texture path in scene"""
    pass


def register():
    """Register the addon"""
    print("\n[FUNCTIONS] Starting registration...")
    try:
        # Register property group for texture path
        bpy.utils.register_class(OBJECT_INSPECTOR_TexturePath)
        
        # Add property to scene for texture path storage
        bpy.types.Scene.object_inspector_texture_path = bpy.props.StringProperty(
            name="Texture Image Path",
            description="Path to image file for texture",
            default="",
            subtype='FILE_PATH'
        )
        
        print("[FUNCTIONS] Registering OBJECT_OT_AddTexture...")
        bpy.utils.register_class(OBJECT_OT_AddTexture)
        print("[FUNCTIONS] Registering OBJECT_OT_CreateFittingRectangle...")
        bpy.utils.register_class(OBJECT_OT_CreateFittingRectangle)
        print("[FUNCTIONS] Registering OBJECT_OT_CreateMouldBox...")
        bpy.utils.register_class(OBJECT_OT_CreateMouldBox)
        print("[FUNCTIONS] Registering VIEW3D_PT_ObjectInspector...")
        bpy.utils.register_class(VIEW3D_PT_ObjectInspector)
        print("[FUNCTIONS] Adding menu items...")
        bpy.types.VIEW3D_MT_object.append(menu_func)
        
        # Force UI refresh to show the panel
        print("[FUNCTIONS] Refreshing UI...")
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        print("[FUNCTIONS] ✓ Registration complete!")
        print("✓ Registered: Object Inspector panel should appear in sidebar 'object_inspector' tab")
    except Exception as e:
        print(f"[FUNCTIONS] ERROR during registration: {e}")
        import traceback
        traceback.print_exc()


def unregister():
    """Unregister the addon"""
    bpy.utils.unregister_class(VIEW3D_PT_ObjectInspector)
    bpy.utils.unregister_class(OBJECT_OT_CreateMouldBox)
    bpy.utils.unregister_class(OBJECT_OT_CreateFittingRectangle)
    bpy.utils.unregister_class(OBJECT_OT_AddTexture)
    bpy.utils.unregister_class(OBJECT_INSPECTOR_TexturePath)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    
    # Remove scene property
    if hasattr(bpy.types.Scene, "object_inspector_texture_path"):
        del bpy.types.Scene.object_inspector_texture_path


# Global flag to prevent duplicate registration
_IS_REGISTERED = False

def load_and_register():
    """Function to load and register the addon - can be called from console"""
    print("\n[FUNCTIONS] load_and_register() called")
    global _IS_REGISTERED
    if not _IS_REGISTERED:
        print("[FUNCTIONS] Not registered yet, calling register()...")
        register()
        _IS_REGISTERED = True
        print("[FUNCTIONS] ✓ Object Inspector panel loaded!")
        print("  Press N to open the sidebar, then click 'object_inspector' tab")
        print("  Look for 'Object Inspector' panel in the 3D Viewport sidebar")
    else:
        print("[FUNCTIONS] Object Inspector already registered!")

if __name__ == "__main__":
    load_and_register()



