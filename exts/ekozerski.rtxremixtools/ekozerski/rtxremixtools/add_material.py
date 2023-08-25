import os
from typing import List
from omni import usd, kit
from omni.kit.window.file_importer import get_file_importer
from omni.client import make_relative_url

from ekozerski.rtxremixtools.utils import find_source_mesh_hash_prim


def open_add_material_dialog_for_prim(mesh_hash, ctx, current_stage):
    def create_material_from_mdl_file(filename: str, dirname: str, selections: List[str] = []):
        if not filename.endswith('mdl'):
            raise ValueError(f"The selected file '{filename}' doesn't have a mdl extension.")
        
        mesh_hash_path = mesh_hash.GetPath().pathString
        counter = 0
        new_material_path = mesh_hash_path + f'/NewMaterial_{counter}'
        while current_stage.GetPrimAtPath(new_material_path).IsValid():
            counter += 1
            new_material_path = mesh_hash_path + f'/NewMaterial_{counter}'

        # TODO: Get material name by inspecting the MDL file rather than guessing from it's name, so users can  
              # rename it at will.
        mtl_name = 'AperturePBR_Opacity' if 'Opacity' in filename else 'AperturePBR_Translucent'
        editing_layer = current_stage.GetEditTarget().GetLayer()
        relative_file_path = make_relative_url(editing_layer.realPath, os.path.join(dirname, filename))
        success, _ = kit.commands.execute('CreateMdlMaterialPrimCommand',
            mtl_url=relative_file_path,
            mtl_name=mtl_name,
            mtl_path=new_material_path,
            select_new_prim=True,
        )

    file_importer = get_file_importer()
    file_importer.show_window(
        title=f'Select MDL File',
        import_button_label="Select",
        import_handler=create_material_from_mdl_file,
    )


def open_add_material_dialog():
    ctx = usd.get_context()
    current_stage = ctx.get_stage()
    selection = ctx.get_selection().get_selected_prim_paths()
    selected_prims = {
        path: current_stage.GetPrimAtPath(path)
        for path in selection
    }
    source_meshes = [find_source_mesh_hash_prim(current_stage, prim) for prim in selected_prims.values()]
    source_meshes = set([mesh for mesh in source_meshes if mesh is not None])

    for mesh_hash in list(source_meshes):
        open_add_material_dialog_for_prim(mesh_hash, ctx, current_stage)
