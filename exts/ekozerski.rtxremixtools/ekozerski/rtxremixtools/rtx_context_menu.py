from omni.kit.ui import get_custom_glyph_code
import omni.ui as ui

from . import mesh_utils


def build_rtx_remix_menu(event):
    icon = get_custom_glyph_code("${glyphs}/menu_create.svg")
    with ui.Menu(f' {icon}  RTX Remix'):
        fix_meshes_geometry_tooltip = ''.join([
            'Interpolation Mode\n',
            '    RTX Remix runtime only supports "vertex" interpolation mode, in which "points", "normals" and "uvs" arrays ',
            'must have the same length, but DCCs usually export the mesh using "faceVarying" interpolation mode.',
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
            tooltip=fix_meshes_geometry_tooltip
        )
