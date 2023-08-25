from omni import usd, kit
from pxr import Sdf

from ekozerski.rtxremixtools.utils import find_source_mesh_hash_prim


def set_preserve_original_draw_call(enabled: bool = False):
    ctx = usd.get_context()
    current_stage = ctx.get_stage()
    selection = ctx.get_selection().get_selected_prim_paths()
    selected_prims = {
        path: current_stage.GetPrimAtPath(path)
        for path in selection
    }

    source_meshes = [find_source_mesh_hash_prim(current_stage, prim) for prim in selected_prims.values()]
    source_meshes = set([mesh for mesh in source_meshes if mesh is not None])
    for mesh_prim in source_meshes:
        kit.commands.execute(
            'CreateUsdAttributeCommand',
            prim=mesh_prim,
            attr_name='preserveOriginalDrawCall',
            attr_type=Sdf.ValueTypeNames.Int,
            attr_value=1 if enabled else 0
        )
