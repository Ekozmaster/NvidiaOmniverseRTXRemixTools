from collections import OrderedDict
from pxr import UsdGeom, Usd, Sdf
import omni.usd as usd

from ekozerski.rtxremixtools.commons import log_error


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


def convert_uv_primvars_to_st(mesh):
    # https://github.com/NVIDIAGameWorks/dxvk-remix/blob/ebb0ecfd638d6a32ab5f10708b5b07bc763cf79b/src/dxvk/rtx_render/rtx_mod_usd.cpp#L696
    # https://github.com/Kim2091/RTXRemixTools/blob/8ae25224ef8d1d284f3e208f671b2ce6a35b82af/RemixMeshConvert/For%20USD%20Composer/RemixMeshConvert_OV.py#L4
    known_uv_names = [
        'primvars:st',
        'primvars:uv',
        'primvars:st0',
        'primvars:st1',
        'primvars:st2',
        'primvars:UVMap',
        'primvars:UVChannel_1',
        'primvars:map1',
    ]
    # Preserving the order of found primvars to use the first one, in case a primvars:st can't be found.
    primvar_api = UsdGeom.PrimvarsAPI(mesh)
    uv_primvars = OrderedDict(
        (primvar.GetName(), primvar)
        for primvar in primvar_api.GetPrimvars()
        if primvar.GetTypeName().role == 'TextureCoordinate'
        or primvar.GetName() in known_uv_names
    )
    if not uv_primvars:
        return
    
    # Picking only one UV and blowing up everything else as the runtime only reads the first anyway.
    considered_uv = uv_primvars.get('primvars:st') or next(iter(uv_primvars.values()))
    uv_data = considered_uv.Get()
    [primvar_api.RemovePrimvar(uv_name) for uv_name in uv_primvars.keys()]

    # Recreating the primvar with appropriate name, type and role
    new_uv_primvar = primvar_api.CreatePrimvar('primvars:st', Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.vertex)
    new_uv_primvar.Set(uv_data)


def remove_unused_primvars(mesh):
    unused_primvar_names = [
        'primvars:displayColor',
        'primvars:displayOpacity',
    ]
    primvar_api = UsdGeom.PrimvarsAPI(mesh)
    [primvar_api.RemovePrimvar(uv_name) for uv_name in unused_primvar_names]


def fix_meshes_in_file(usd_file_path):
    stage = Usd.Stage.Open(usd_file_path)
    mesh_prims = [prim for prim in stage.TraverseAll() if UsdGeom.Mesh(prim)]
    for prim in mesh_prims:
        faceVertices = prim.GetAttribute("faceVertexCounts").Get()
        if not faceVertices or not all({x == 3 for x in faceVertices}):
            log_error(f"Mesh {prim.GetPath()} in '{usd_file_path}' hasn't been triangulated and this tools doesn't do that for you yet :(")
            continue
        convert_mesh_to_vertex_interpolation_mode(UsdGeom.Mesh(prim))
        convert_uv_primvars_to_st(UsdGeom.Mesh(prim))
        remove_unused_primvars(UsdGeom.Mesh(prim))

    stage.Save()


def is_a_modded_mesh(mesh):
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
    meshes = {k: v for k,v in get_selected_mesh_prims().items() if is_a_modded_mesh(v)}
    for path, mesh in meshes.items():
        source_layer = mesh.GetPrimStack()[-1].layer
        fix_meshes_in_file(source_layer.realPath)
        source_layer.Reload()
