import asyncio
import os
from typing import List

from pxr import UsdGeom
from omni.kit.window.file_exporter import get_file_exporter
from omni.client import make_relative_url
import omni
from pxr import Usd, Sdf
import omni.usd as usd

from .commons import log_info
from . import mesh_utils


def open_export_dialog_for_mesh(prim_path, mesh):
    async def setup_replacement_references_in_stage(current_stage, reference_file_location):
        _, mesh_hash, __ = Usd.Prim.GetName(mesh.GetParent()).split('_')
        xform_prim_path = f'/RootNode/meshes/mesh_{mesh_hash}/Xform_{mesh_hash}_0'
        omni.kit.commands.execute('CreatePrim', prim_type='Xform', prim_path=xform_prim_path)
        editing_layer = current_stage.GetEditTarget().GetLayer()
        relative_file_path = make_relative_url(editing_layer.realPath, reference_file_location)
        omni.kit.commands.execute('AddReference',
            stage=current_stage,
            prim_path=Sdf.Path(xform_prim_path),
            reference=Sdf.Reference(relative_file_path)
        )
        selection = omni.usd.get_context().get_selection()
        selection.clear_selected_prim_paths()
        selection.set_selected_prim_paths([xform_prim_path], False)

    def file_export_handler(filename: str, dirname: str, extension: str = "", selections: List[str] = []):
        stage = Usd.Stage.CreateInMemory()
        root_xform = UsdGeom.Xform.Define(stage, '/root').GetPrim()
        stage.SetDefaultPrim(root_xform)
        new_mesh = UsdGeom.Mesh.Define(stage, f'/root/{prim_path.rsplit("/", 1)[-1]}')

        needed_attr_names = ['doubleSided', 'extent', 'faceVertexCounts', 'faceVertexIndices', 'normals', 'points', 'primvars:st']
        [
            new_mesh.GetPrim().CreateAttribute(attr.GetName(), attr.GetTypeName()).Set(attr.Get())
            for attr in mesh.GetAttributes()
            if attr.Get() and attr.GetName() in needed_attr_names
        ]
        mesh_utils.convert_mesh_to_vertex_interpolation_mode(new_mesh)
        
        ctx = usd.get_context()
        current_stage = ctx.get_stage()
        upAxis = UsdGeom.GetStageUpAxis(current_stage)
        UsdGeom.SetStageUpAxis(stage, upAxis)

        save_location = dirname + filename + extension
        stage.Export(save_location)
        asyncio.ensure_future(setup_replacement_references_in_stage(current_stage, save_location))
        
        log_info(f"> Exporting {prim_path} in '{save_location}'")

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
