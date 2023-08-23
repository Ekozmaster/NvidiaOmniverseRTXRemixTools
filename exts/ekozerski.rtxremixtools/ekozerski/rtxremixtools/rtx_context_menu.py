from omni.kit.ui import get_custom_glyph_code
import omni.ui as ui

from . import mesh_utils
from . import setup_for_mesh_replacements


def _build_fix_mesh_geometry_menu_item():
    tooltip = ''.join([
        'Interpolation Mode\n',
        'OBS: Operation Can\'t be undone\n',
        '    RTX Remix runtime only supports "vertex" interpolation mode, in which "points", "normals" and "uvs" arrays ',
        'must have the same length, but DCC tools usually export the mesh using "faceVarying" interpolation mode.',
        'This operation reorganizes the geometry to be compatible with the runtime. See:\n',
        '    "Interpolation of Geometric Primitive Variables" - https://openusd.org/dev/api/class_usd_geom_primvar.html',
        '\n\nThis operation only applies for meshes inside the mods folder, not the captured ones.',
    ])
    ui.MenuItem(
        "Fix Meshes Geometry",
        triggered_fn=mesh_utils.fix_meshes_geometry,
        enabled=any([
            mesh_utils.is_mesh_editable(mesh)
            for mesh in mesh_utils.get_selected_mesh_prims().values()
        ]),
        tooltip=tooltip
    )


def _build_setup_for_mesh_replacement_menu_item():
    tooltip = ''.join([
        "Copies the original captured mesh and textures from its USD file to a chosen location and redefines it's ",
        " materials in the authoring layer, so it can be imported and remodeled using your favorite DCC tool."
    ])
    ui.MenuItem(
        "Setup for Mesh Replacement",
        triggered_fn=setup_for_mesh_replacements.open_file_export_dialog_for_selected_meshes,
        enabled=any([
            mesh_utils.is_a_captured_mesh(mesh)
            for mesh in mesh_utils.get_selected_mesh_prims().values()
        ]),
        tooltip=tooltip
    )


def build_rtx_remix_menu(event):
    icon = get_custom_glyph_code("${glyphs}/menu_create.svg")
    with ui.Menu(f' {icon}  RTX Remix'):
        _build_fix_mesh_geometry_menu_item()
        _build_setup_for_mesh_replacement_menu_item()
