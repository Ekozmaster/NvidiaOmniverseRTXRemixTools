from omni import usd

from ekozerski.rtxremixtools.utils import find_source_mesh_hash_prim


def select_source_meshes():
    ctx = usd.get_context()
    current_stage = ctx.get_stage()
    selection = ctx.get_selection().get_selected_prim_paths()
    selected_prims = {
        path: current_stage.GetPrimAtPath(path)
        for path in selection
    }

    source_meshes = [find_source_mesh_hash_prim(current_stage, prim) for prim in selected_prims.values()]
    source_meshes = set([mesh for mesh in source_meshes if mesh is not None])
    paths = [mesh.GetPath().pathString for mesh in source_meshes]
    selection = usd.get_context().get_selection()
    selection.clear_selected_prim_paths()
    selection.set_selected_prim_paths(paths, False)
