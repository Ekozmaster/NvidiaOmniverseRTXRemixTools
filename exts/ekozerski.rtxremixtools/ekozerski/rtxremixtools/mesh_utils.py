from pxr import UsdGeom, Usd
import omni.usd as usd


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


def convert_mesh_to_vertex_interpolation_mode(mesh):
    """
    This method attemps to convert Remix meshes' interpolation mode from constant or faceVarying to vertex.
    If there is any faceVarying attribute, it means the data arrays (points, uvs, normals...) will have different
    lengths, so this script will copy data around using the faceVertexIndices array to ensure they all end up with the
    same length.
    """
    # TODO: Study interpolation modes in depth to implement a decent conversion script.
    prim = mesh.GetPrim()
    primvar_api = UsdGeom.PrimvarsAPI(prim)
    primvars = {var for var in primvar_api.GetPrimvars()}
    face_varying_primvars = [v for v in primvars if v.GetInterpolation() == UsdGeom.Tokens.faceVarying]
    if face_varying_primvars or mesh.GetNormalsInterpolation() == UsdGeom.Tokens.faceVarying:
        non_face_varying_primvars = list(primvars.difference(face_varying_primvars))
        indices = prim.GetAttribute("faceVertexIndices")

        # Settings points separately since it doesn't have a "SetInterpolation" like primvars.
        points = prim.GetAttribute("points")
        points_arr = points.Get()
        new_arr = [points_arr[i] for i in indices.Get()]
        points.Set(new_arr)

        for var in non_face_varying_primvars:
            original_arr = var.Get()
            if original_arr:
                new_arr = [original_arr[i] for i in indices.Get()]
                var.Set(new_arr)
        
        indices.Set([i for i in range(len(indices.Get()))])
    
    [var.SetInterpolation(UsdGeom.Tokens.vertex) for var in primvars]
    mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)


def convert_face_varying_to_vertex_interpolation(usd_file_path):
    stage = Usd.Stage.Open(usd_file_path)
    mesh_prims = [prim for prim in stage.TraverseAll() if UsdGeom.Mesh(prim)]
    for prim in mesh_prims:
        convert_mesh_to_vertex_interpolation_mode(UsdGeom.Mesh(prim))

    stage.Export(usd_file_path)


def is_mesh_editable(mesh):
    """
    Returns False if the Mesh's defining USD file isn't located in the mods folder, thus, ignoring "captures/" ones.
    """
    return 'gameReadyAssets' in mesh.GetPrimStack()[-1].layer.realPath


def is_a_captured_mesh(mesh):
    """
    Returns True if the Mesh's defining USD file is located in the captures folder.
    """
    return 'captures' in mesh.GetPrimStack()[-1].layer.realPath



def fix_meshes_geometry():
    meshes = {k: v for k,v in get_selected_mesh_prims().items() if is_mesh_editable(v)}
    for path, mesh in meshes.items():
        source_layer = mesh.GetPrimStack()[-1].layer
        convert_face_varying_to_vertex_interpolation(source_layer.realPath)
        source_layer.Reload()
