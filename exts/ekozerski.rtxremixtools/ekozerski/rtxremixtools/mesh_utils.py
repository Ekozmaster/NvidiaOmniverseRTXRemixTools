from pxr import UsdGeom
import omni.usd as usd

from .commons import log_info


def get_selected_mesh_prims():
    
    
    ctx = usd.get_context()
    current_stage = ctx.get_stage()
    selection = ctx.get_selection().get_selected_prim_paths()
    selected_prims = {
        path: current_stage.GetPrimAtPath(path)
        for path in selection
    }
    meshes = {
        prim_path: prim
        for prim_path, prim in selected_prims.items()
        if UsdGeom.Mesh(prim)
    }

    return meshes


def convert_face_varying_to_vertex_interpolation(usd_file_path):
    from pxr import Usd
    stage = Usd.Stage.Open(usd_file_path)
    mesh_prims = [prim for prim in stage.TraverseAll() if UsdGeom.Mesh(prim)]
    for prim in mesh_prims:
        mesh = UsdGeom.Mesh(prim)
        indices = prim.GetAttribute("faceVertexIndices")
        points = prim.GetAttribute("points")
        points_arr = points.Get()

        modified_points = [points_arr[i] for i in indices.Get()]
        points.Set(modified_points)

        indices.Set([i for i in range(len(indices.Get()))])

        mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
        primvar_api = UsdGeom.PrimvarsAPI(prim)
        for var in primvar_api.GetPrimvars():
            if var.GetInterpolation() == UsdGeom.Tokens.faceVarying:
                var.SetInterpolation(UsdGeom.Tokens.vertex)

    stage.Export(usd_file_path)


def is_mesh_editable(mesh):
    """
    Returns false if the Mesh's defining USD file isn't located in the mods folder, thus, ignoring "captures/" ones.
    """
    return 'gameReadyAssets' in mesh.GetPrimStack()[-1].layer.realPath



def fix_meshes_geometry():
    meshes = {k: v for k,v in get_selected_mesh_prims().items() if is_mesh_editable(v)}
    for path, mesh in meshes.items():
        source_layer = mesh.GetPrimStack()[-1].layer
        convert_face_varying_to_vertex_interpolation(source_layer.realPath)
        source_layer.Reload()
