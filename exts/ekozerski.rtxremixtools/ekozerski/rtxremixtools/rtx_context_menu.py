from omni.kit.ui import get_custom_glyph_code
from omni import usd
import omni.ui as ui

from . import mesh_utils
from . import add_model
from . import add_material
from . import preserve_draw_calls
from . import select_source_mesh


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
            not mesh_utils.is_a_captured_mesh(mesh)
            for mesh in mesh_utils.get_selected_mesh_prims().values()
        ]),
        tooltip=tooltip
    )


def _build_setup_for_mesh_replacements_menu_item():
    tooltip = ''.join([
        "Export the original mesh to a selected location and setup the references to work within the runtime so you",
        " can focus on remodeling the mesh and export back at the same location."
    ])
    ui.MenuItem(
        "Setup for Mesh Replacement",
        triggered_fn=add_model.open_mesh_replacement_setup_dialog,
        enabled=any([
            mesh_utils.is_a_captured_mesh(mesh)
            for mesh in mesh_utils.get_selected_mesh_prims().values()
        ]),
        tooltip=tooltip
    )


def _build_add_model_menu_item():
    tooltip = ''.join([
        "Add external authored meshes to the prim, setting up properly to work within the runtime."
    ])
    ui.MenuItem(
        "Add Model",
        triggered_fn=add_model.open_add_model_dialog,
        tooltip=tooltip,
        enabled=bool(usd.get_context().get_selection().get_selected_prim_paths())
    )


def _build_add_material_menu_item():
    tooltip = ''.join([
        "Add a material defined from an external MDL file to the selected prim."
    ])
    ui.MenuItem(
        "Add Material",
        triggered_fn=add_material.open_add_material_dialog,
        tooltip=tooltip,
        enabled=bool(usd.get_context().get_selection().get_selected_prim_paths())
    )


def _build_preserve_original_draw_call_menu_item():
    tooltip = ''.join([
        "Add a 'custom int preserveOriginalDrawCall' attribute set to '1' to the mesh_HASH prim. Used to indicate to",
        " the runtime whether it should keep rendering the original mesh or not. Should be set when adding custom ",
        " lights without removing the original mesh from rendering."
    ])
    ui.MenuItem(
        "Preserve",
        triggered_fn=lambda: preserve_draw_calls.set_preserve_original_draw_call(True),
        tooltip=tooltip,
        enabled=bool(usd.get_context().get_selection().get_selected_prim_paths())
    )


def _build_dont_preserve_original_draw_call_menu_item():
    tooltip = ''.join([
        "Add a 'custom int preserveOriginalDrawCall' attribute set to '0' to the mesh_HASH prim. Used to indicate to",
        " the runtime whether it should keep rendering the original mesh or not. Should be set when adding custom ",
        " lights without removing the original mesh from rendering."
    ])
    ui.MenuItem(
        "Don't Preserve",
        triggered_fn=lambda: preserve_draw_calls.set_preserve_original_draw_call(False),
        tooltip=tooltip,
        enabled=bool(usd.get_context().get_selection().get_selected_prim_paths())
    )


def _build_select_source_meshes_menu():
    tooltip = ''.join([
        "Selects the corresponding mesh_HASH the prim is related to."
    ])
    ui.MenuItem(
        "Select Source Mesh (Shift + F)",
        triggered_fn=select_source_mesh.select_source_meshes,
        tooltip=tooltip,
        enabled=bool(usd.get_context().get_selection().get_selected_prim_paths())
    )


def build_rtx_remix_menu(event):
    icon = get_custom_glyph_code("${glyphs}/menu_create.svg")
    with ui.Menu(f' {icon}  RTX Remix'):
        _build_fix_mesh_geometry_menu_item()
        _build_setup_for_mesh_replacements_menu_item()
        _build_add_model_menu_item()
        _build_add_material_menu_item()
        with ui.Menu(f'Original Draw Call Preservation'):
            _build_preserve_original_draw_call_menu_item()
            _build_dont_preserve_original_draw_call_menu_item()
        _build_select_source_meshes_menu()
