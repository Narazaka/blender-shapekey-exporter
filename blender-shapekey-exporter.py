import bpy
from bpy.props import *
from bpy.types import Scene
from bpy_extras.io_utils import ExportHelper, ImportHelper
import mathutils
import json

bl_info = {
    "name" : "Shapekey Exporter",
    "author" : "Narazaka",
    'category': 'Mesh',
    'location': 'View 3D > Tool Shelf(2.79) / Sidebar(2.80) > Shapekey Exporter',
    'description': 'Name based shapekey export and import tool',
    "version" : (0, 1, 0),
    "blender" : (2, 80, 0),
    'tracker_url': 'https://github.com/Narazaka/blender-shapekey-exporter/issues',
}

def version_2_79_or_older():
    return bpy.app.version < (2, 80)

class ShapekeyExporter_PT_Main(bpy.types.Panel):
    bl_idname = "shapekey_exporter.main"
    bl_label = "Shapekey Exporter"
    bl_category = "ShapekeyExporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS" if version_2_79_or_older() else "UI"
    bl_context = "objectmode"

    def draw(self, context):
        self.layout.operator(ShapekeyExporter_OT_Export.bl_idname)
        self.layout.operator(ShapekeyExporter_OT_Import.bl_idname)
        return {'FINISHED'}

class ShapekeyExporter_OT_Export(bpy.types.Operator, ExportHelper):
    bl_idname = "shapekey_exporter.export"
    bl_label = "Export"
    bl_options = {'REGISTER'}

    filename_ext = ".skx.json" 
    
    filter_glob = StringProperty( 
            default="*.skx.json", 
            options={'HIDDEN'}, 
            )

    def execute(self, context):
        if self.filepath == "":
            return {'FINISHED'}

        data = {}
        for object_name in bpy.data.objects.keys():
            obj = bpy.data.objects[object_name]
            if obj.type != 'MESH' or not obj.data.shape_keys:
                continue
            base_key_block = obj.data.shape_keys.reference_key
            base_key_values = [item.co for item in base_key_block.data.values()]

            key_blocks = obj.data.shape_keys.key_blocks
            data[object_name] = {
                "base": base_key_block.name,
                "diffs": {},
            }
            for key_block_name in key_blocks.keys():
                key_block = key_blocks[key_block_name]
                if base_key_block == key_block: # base
                    continue
                key_values = [item.co for item in key_block.data.values()]
                if len(key_values) != len(base_key_values):
                    raise RuntimeError("mesh vertex count is different: " + key_block_name)
                diff_key_values = []
                for i in range(len(key_values)):
                    diff_key_values.append((key_values[i] - base_key_values[i])[:])
                data[object_name]["diffs"][key_block_name] = diff_key_values
        
        with open(self.filepath, mode='w', encoding="utf8") as f:
            json.dump(data, f, sort_keys=True, indent=4, ensure_ascii=False)

        return {'FINISHED'}

class ShapekeyExporter_OT_Import(bpy.types.Operator, ImportHelper):
    bl_idname = "shapekey_exporter.import"
    bl_label = "Import"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".skx.json" 
    
    filter_glob = StringProperty( 
            default="*.skx.json", 
            options={'HIDDEN'}, 
            )

    def execute(self, context):
        data = None
        with open(self.filepath, mode='r', encoding="utf8") as f:
            data = json.load(f)

        for object_name in data.keys():
            if len(data[object_name]["diffs"]) == 0:
                continue
            obj = bpy.data.objects[object_name]
            if obj.type != 'MESH':
                continue

            # ensure base key
            if not obj.data.shape_keys:
                obj.shape_key_add()
                obj.data.shape_keys.key_blocks[-1].name = data[object_name]["base"]
            base_key_block = obj.data.shape_keys.reference_key
            base_key_values = [item.co for item in base_key_block.data.values()]

            key_blocks = obj.data.shape_keys.key_blocks
            # overwrite always (TODO: selectable)
            for key_block_name in data[object_name]["diffs"].keys():
                key_block = key_blocks.get(key_block_name)
                if not key_block:
                    obj.shape_key_add()
                    key_blocks[-1].name = key_block_name
                if base_key_block == key_block: # base
                    continue
                key_values = [mathutils.Vector(vec) for vec in data[object_name]["diffs"][key_block_name]]
                if len(key_values) != len(base_key_values):
                    raise RuntimeError("mesh vertex count is different: " + key_block_name)
                for i in range(len(key_values)):
                    key_blocks[key_block_name].data[i].co = key_values[i] + base_key_values[i]

        return {'FINISHED'}

classes = (
    ShapekeyExporter_PT_Main,
    ShapekeyExporter_OT_Export,
    ShapekeyExporter_OT_Import,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
