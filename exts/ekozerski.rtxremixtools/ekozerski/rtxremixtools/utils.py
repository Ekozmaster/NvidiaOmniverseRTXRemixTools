from pxr import Usd
from omni import usd


def find_source_mesh_hash_prim(current_stage, prim):
    if not current_stage.GetPrimAtPath('/RootNode/meshes'):
        return prim
    
    search_prim = prim
    valid_paths = ['/RootNode/meshes', '/RootNode/instances']
    while search_prim.GetParent().IsValid() and search_prim.GetParent().GetPath().pathString not in valid_paths:
        search_prim = search_prim.GetParent()
    
    if not search_prim:
        return None
    
    prim_name = Usd.Prim.GetName(search_prim)
    if 'mesh_' in prim_name:
        return search_prim

    # Expected format: inst_HASH_N or similar with at least 2 underscores
    parts = prim_name.split('_')
    if len(parts) >= 2:
        mesh_hash = parts[1]
        mesh_prim_path = f'/RootNode/meshes/mesh_{mesh_hash}'
        return current_stage.GetPrimAtPath(mesh_prim_path)
    
    return None
    

def find_inst_hash_prim(instance_mesh):
    search_prim = instance_mesh
    root_path = '/RootNode/instances'
    while search_prim.GetParent().IsValid() and search_prim.GetParent().GetPath().pathString != root_path:
        search_prim = search_prim.GetParent()

    if not search_prim:
        return None
    
    return search_prim
