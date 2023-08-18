import os
from typing import List

from pxr import UsdGeom
from omni.kit.window.file_exporter import get_file_exporter
from pxr import Usd
import omni.usd as usd

from .commons import log_info
from . import mesh_utils



def open_export_dialog_for_mesh(prim_path, mesh):
    def file_export_handler(filename: str, dirname: str, extension: str = "", selections: List[str] = []):
        stage = Usd.Stage.CreateInMemory()
        UsdGeom.Xform.Define(stage, '/root')
        new_mesh = UsdGeom.Mesh.Define(stage, f'/root/{prim_path.rsplit("/", 1)[-1]}')

        for attr in mesh.GetAttributes():
            destAttr = new_mesh.GetPrim().CreateAttribute(attr.GetName(), attr.GetTypeName())
            if attr.Get():
                destAttr.Set(attr.Get())
        
        ctx = usd.get_context()
        current_stage = ctx.get_stage()
        upAxis = UsdGeom.GetStageUpAxis(current_stage)
        UsdGeom.SetStageUpAxis(stage, upAxis)

        stage.Export(dirname + filename + extension)
        log_info(f"> Exporting {prim_path} in '{dirname}{filename}{extension}'")

    source_layer = mesh.GetPrimStack()[-1].layer
    rtx_remix_path_parts = source_layer.realPath.split(os.path.join("rtx-remix"), 1)
    if len(rtx_remix_path_parts) > 1:
        rtx_remix_path = os.path.join(rtx_remix_path_parts[0], "rtx-remix", "mods", "gameReadyAssets")
    else:
        rtx_remix_path = source_layer.realPath
    
    rtx_remix_path = os.path.join(rtx_remix_path, "CustomMesh")
    
    # Get the singleton extension object, but as weakref to guard against the extension being removed.
    file_exporter = get_file_exporter()
    file_exporter.show_window(
        title=f'Export "{prim_path}"',
        export_button_label="Save",
        # The callback function called after the user has selected an export location.
        export_handler=file_export_handler,
        filename_url=rtx_remix_path,
    )


def open_file_export_dialog_for_selected_meshes():
    meshes = {k: v for k,v in mesh_utils.get_selected_mesh_prims().items() if mesh_utils.is_a_captured_mesh(v)}
    for path, mesh in meshes.items():
        open_export_dialog_for_mesh(path, mesh)
