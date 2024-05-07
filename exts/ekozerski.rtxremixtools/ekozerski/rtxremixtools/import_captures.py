from collections import defaultdict
from typing import List

from pxr import Usd, Sdf, UsdGeom, Gf
from omni.usd import get_context
from omni.kit.window.file_importer import get_file_importer
from omni.kit import commands
from omni.client import make_relative_url

from ekozerski.rtxremixtools.commons import log_info


def copy_instances(source_stage: Usd.Stage, dest_stage: Usd.Stage):
    def parse_instance_hash(inst):
        return inst.GetName().split('_')[1]

    def get_instance_transform(inst):
        xform = UsdGeom.Xformable(inst)
        time = Usd.TimeCode.Default()
        return xform.ComputeLocalToWorldTransform(time)
    
    dest_instances_prim = dest_stage.GetPrimAtPath('/RootNode/instances')
    dest_instances = dest_instances_prim.GetAllChildren() if dest_instances_prim else list()
    source_instances_prim = source_stage.GetPrimAtPath('/RootNode/instances')
    source_instances = source_instances_prim.GetAllChildren() if source_instances_prim else list()

    # HASH + Transform data used as dict key to resolve duplicate instances
    instances_map = {
        (parse_instance_hash(inst), get_instance_transform(inst)): (inst, inst.GetStage().GetRootLayer())
        for inst in source_instances + dest_instances
    }
    # Group by mesh hash
    hash_groups = defaultdict(list)
    for (hash_key, _), prim_data in instances_map.items():
        hash_groups[hash_key].append(prim_data)
    
    temp_stage = Usd.Stage.CreateInMemory()
    temp_stage.DefinePrim("/RootNode")
    temp_stage.DefinePrim("/RootNode/instances")
    temp_inst_merge_layer = temp_stage.GetRootLayer()
    for hash, prims_data in hash_groups.items():
        inst_count = 0
        for prim, prim_layer in prims_data:
            new_inst_prim_path = f'/RootNode/instances/inst_{hash}_{inst_count}'
            Sdf.CopySpec(prim_layer, prim.GetPath(), temp_inst_merge_layer, Sdf.Path(new_inst_prim_path))
            inst_count += 1
    
    dest_layer = dest_stage.GetRootLayer()
    # temp_instances_merge_layer instances counts will always be >= dest_layer's, so we can just copy and replace on top.
    Sdf.CopySpec(temp_inst_merge_layer, Sdf.Path('/RootNode/instances'), dest_layer, Sdf.Path('/RootNode/instances'))


def import_capture_usd(capture_path):
    def copy_child_prims_specs(parent_path: str):
        # Performin one Sdf.CopySpec on parents like RootNode/meshes won't merge prims
        # Instead, will remove destination mesh_HASH and add source's prims on top. So we copy one by one ;)
        for prim in capture_stage.GetPrimAtPath(parent_path).GetAllChildren():
            Sdf.CopySpec(capture_layer, prim.GetPath(), current_layer, prim.GetPath())

    ctx = get_context()
    current_stage = ctx.get_stage()
    current_layer = current_stage.GetRootLayer()
    capture_stage = Usd.Stage.Open(capture_path)
    capture_layer = capture_stage.GetRootLayer()

    capture_layer.subLayerPaths = []

    # This is needed or else Sdf.CopySpec gets iffy on non-capture scenes.
    current_stage.DefinePrim("/RootNode")
    current_stage.DefinePrim("/RootNode/meshes")
    copy_child_prims_specs('/RootNode/meshes')
    current_stage.DefinePrim("/RootNode/lights")
    copy_child_prims_specs('/RootNode/lights')
    current_stage.DefinePrim("/RootNode/Looks")
    copy_child_prims_specs('/RootNode/Looks')
    if capture_stage.GetPrimAtPath('/RootNode/cameras'):
        current_stage.DefinePrim("/RootNode/cameras")
        copy_child_prims_specs('/RootNode/cameras')
    copy_instances(capture_stage, current_stage)

def import_captures():
    def import_selected_captures(filename: str, dirname: str, selections: List[str] = []):
        for capture_usd in selections:
            import_capture_usd(capture_usd)
    
    filename_url = get_context().get_stage().GetRootLayer().realPath
    file_importer = get_file_importer()
    file_importer.show_window(
        title=f'Import Models',
        import_button_label="Import",
        import_handler=import_selected_captures
    )
