import os
from pathlib import Path
from typing import List

import omni
from omni.client import make_relative_url
from omni.kit.window.file_importer import get_file_importer
from omni.kit.window.file_exporter import get_file_exporter
import omni.usd as usd
from pxr import UsdGeom, Usd, Sdf

from ekozerski.rtxremixtools.utils import find_inst_hash_prim
from ekozerski.rtxremixtools.commons import log_info
from ekozerski.rtxremixtools import mesh_utils


class UserCache:
    LAST_OPENED_MODEL = None


def open_export_dialog_for_captured_mesh(prim_path, mesh):
    def setup_references_in_stage(current_stage, reference_file_location):
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
        source_layer = mesh.GetPrimStack()[-1].layer
        source_layer.Reload()
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
        setup_references_in_stage(current_stage, save_location)
        
        log_info(f"> Exporting {prim_path} in '{save_location}'")

    source_layer = mesh.GetPrimStack()[-1].layer
    rtx_remix_path_parts = source_layer.realPath.split(os.path.join("rtx-remix"), 1)
    if len(rtx_remix_path_parts) > 1:
        rtx_remix_path = os.path.join(rtx_remix_path_parts[0], "rtx-remix", "mods", "gameReadyAssets")
    else:
        rtx_remix_path = source_layer.realPath
    
    rtx_remix_path = os.path.join(rtx_remix_path, "CustomMesh")
    
    file_exporter = get_file_exporter()
    file_exporter.show_window(
        title=f'Export "{prim_path}"',
        export_button_label="Save",
        export_handler=file_export_handler,
        filename_url=rtx_remix_path,
    )


def copy_original_mesh(prim_path, mesh, output_path):
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

    stage.Export(output_path)


def setup_references_in_stage(mesh, current_stage, reference_file_location):
    inst_hash_prim = find_inst_hash_prim(mesh)
    _, mesh_hash, __ = Usd.Prim.GetName(inst_hash_prim).split('_')
    export_prim_name = os.path.basename(reference_file_location).split('.', 1)[0]
    xform_prim_path = f'/RootNode/meshes/mesh_{mesh_hash}/{export_prim_name}'
    omni.kit.commands.execute('CreatePrim', prim_type='Xform', prim_path=xform_prim_path)

    editing_layer = current_stage.GetEditTarget().GetLayer()
    relative_file_path = make_relative_url(editing_layer.realPath, reference_file_location)
    omni.kit.commands.execute('AddReference',
        stage=current_stage,
        prim_path=Sdf.Path(xform_prim_path),
        reference=Sdf.Reference(relative_file_path)
    )
    source_layer = mesh.GetPrimStack()[-1].layer
    source_layer.Reload()
    selection = omni.usd.get_context().get_selection()
    selection.clear_selected_prim_paths()
    selection.set_selected_prim_paths([xform_prim_path], False)


def open_export_dialog_for_captured_mesh(prim_path, mesh):
    def export_mesh(filename: str, dirname: str, extension: str = "", selections: List[str] = []):
        file_location = dirname + filename + extension
        copy_original_mesh(prim_path, mesh, file_location)
        ctx = usd.get_context()
        current_stage = ctx.get_stage()
        setup_references_in_stage(mesh, current_stage, file_location)
        
    source_layer = mesh.GetPrimStack()[-1].layer
    rtx_remix_path_parts = source_layer.realPath.split(os.path.join("rtx-remix"), 1)
    rtx_remix_path = source_layer.realPath
    if len(rtx_remix_path_parts) > 1:
        rtx_remix_path = os.path.join(rtx_remix_path_parts[0], "rtx-remix", "mods", "gameReadyAssets")
    
    rtx_remix_path = os.path.join(rtx_remix_path, "CustomMesh")
    
    file_exporter = get_file_exporter()
    file_exporter.show_window(
        title=f'Export "{prim_path}"',
        export_button_label="Save",
        export_handler=export_mesh,
        filename_url=rtx_remix_path,
    )


def open_import_dialog_for_add_models(prim_path):
    def import_mesh(filename: str, dirname: str, selections: List[str] = []):
        # TODO: Loop through all selections and add them all to the mesh_HASH with their respective xforms correctly named without collisions.
        mesh_path = mesh.GetPath().pathString
        new_selection = list()
        counter = 0
        for reference_file in selections:
            xform_name = Path(reference_file).stem
            new_mesh_path = mesh_path + f'/{xform_name}_{counter}'
            while current_stage.GetPrimAtPath(new_mesh_path).IsValid():
                counter += 1
                new_mesh_path = mesh_path + f'/{xform_name}_{counter}'

            omni.kit.commands.execute('CreatePrim', prim_type='Xform', prim_path=new_mesh_path)

            editing_layer = current_stage.GetEditTarget().GetLayer()
            relative_file_path = make_relative_url(editing_layer.realPath, reference_file)
            omni.kit.commands.execute('AddReference',
                stage=current_stage,
                prim_path=Sdf.Path(new_mesh_path),
                reference=Sdf.Reference(relative_file_path)
            )
            new_selection.append(new_mesh_path)
            UserCache.LAST_OPENED_MODEL = os.path.dirname(reference_file)
            counter += 1
        source_layer = mesh.GetPrimStack()[-1].layer
        source_layer.Reload()
        selection = omni.usd.get_context().get_selection()
        selection.clear_selected_prim_paths()
        selection.set_selected_prim_paths(new_selection, False)
        

    ctx = usd.get_context()
    current_stage = ctx.get_stage()
    mesh = current_stage.GetPrimAtPath(prim_path)  # find_source_mesh_hash_prim(current_stage, instance_mesh)

    source_layer = mesh.GetPrimStack()[-1].layer
    filename_url = UserCache.LAST_OPENED_MODEL if UserCache.LAST_OPENED_MODEL is not None else source_layer.realPath

    file_importer = get_file_importer()
    file_importer.show_window(
        title=f'Import Models',
        import_button_label="Import",
        import_handler=import_mesh,
        filename_url=filename_url,
    )


def open_add_model_dialog():
    for path in usd.get_context().get_selection().get_selected_prim_paths():
        open_import_dialog_for_add_models(path)


def open_mesh_replacement_setup_dialog():
    for path, mesh in mesh_utils.get_selected_mesh_prims().items():
        if mesh_utils.is_a_captured_mesh(mesh):
            open_export_dialog_for_captured_mesh(path, mesh)
