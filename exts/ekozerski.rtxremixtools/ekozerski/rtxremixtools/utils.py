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
    
    if 'mesh_' in Usd.Prim.GetName(search_prim):
        return search_prim

    _, mesh_hash, __ = Usd.Prim.GetName(search_prim).split('_')
    mesh_prim_path = f'/RootNode/meshes/mesh_{mesh_hash}'
    return current_stage.GetPrimAtPath(mesh_prim_path)
    

def find_inst_hash_prim(instance_mesh):
    search_prim = instance_mesh
    root_path = '/RootNode/instances'
    while search_prim.GetParent().IsValid() and search_prim.GetParent().GetPath().pathString != root_path:
        search_prim = search_prim.GetParent()

    if not search_prim:
        return None
    
    return search_prim
