import os
import sys

from pxr import UsdGeom, Gf
from omni.paint.brush.scatter import ScatterBrush
from omni.paint.brush.scatter.brush.utils import get_default_root, get_stage_up
from omni.paint.brush.scatter.brush import INSTANCING
from omni.paint.brush.scatter.brush.ui import ParamsUi
from omni import usd

from . import commons
from .utils import find_source_mesh_hash_prim


BRUSH_TYPE = "Remix Scatter"
ORIGINAL_GET_DEFAULT_ROOT = get_default_root
ORIGINAL_GET_STAGE_UP = get_stage_up
FLIP_UP_AXIS = False


def select_source_mesh(selection) -> str:
    ctx = usd.get_context()
    current_stage = ctx.get_stage()
    selected_prims = {
        path: current_stage.GetPrimAtPath(path)
        for path in selection
    }

    return find_source_mesh_hash_prim(current_stage, list(selected_prims.values())[0]).GetPath().pathString


def custom_get_default_root(stage):
    ctx = usd.get_context()
    selection = ctx.get_selection().get_selected_prim_paths()
    if selection:
        return select_source_mesh(selection)
    
    if stage.HasDefaultPrim():
        defaultPrim = stage.GetDefaultPrim()
        if defaultPrim:
            return defaultPrim.GetPath().pathString

    return ""


def custom_get_stage_up(stage):
    up_axis = UsdGeom.GetStageUpAxis(stage)
    if up_axis == "X":
        vec = Gf.Vec3d.XAxis()
    elif up_axis == "Y":
        vec = Gf.Vec3d.YAxis()
    else:
        vec = Gf.Vec3d.ZAxis()
    
    if FLIP_UP_AXIS:
        return -vec
    return vec


def on_param_changed(property_name, property_value):
    if property_name == 'flip_up_axis':
        global FLIP_UP_AXIS
        FLIP_UP_AXIS = property_value


class CustomParamsUi(ParamsUi):
    def _on_brush_setting_changed(self, key, value):
        on_param_changed(key, value)
        super()._on_brush_setting_changed(key, value)


class RemixScatterBrush(ScatterBrush):
    @classmethod
    def get_type(self) -> str:
        return BRUSH_TYPE
    
    def begin_brush(self, brush, *args, **kwargs):
        
        super().begin_brush(brush, *args, **kwargs)
        brush["type"] = BRUSH_TYPE
        brush["instancing_ui"] = {
            "key": "instancing",
            "type": "combo",
            "label": "Instancing",
            "tooltip": "Places assets with selected type",
            "options": ["None"],
            "read_only": False,
        }
        brush["instancing"] = INSTANCING.NONE
        brush['flip_up_axis_ui'] = {
            "key": "flip_up_axis",
            "type": "bool",
            "label": "Flip Up Axis",
            "tooltip": "If your capture has flipped normals and your meshes are painted upside down.",
            "read_only": False,
        }
        brush['flip_up_axis'] = FLIP_UP_AXIS
        commons.log_info(f"[RemixScatterBrush] Begin brush {brush.get('name')}")
        # Monkey patching "get_default_root" so we don't call the original anywhere.
        setattr(sys.modules['omni.paint.brush.scatter.brush.utils'], 'get_default_root', custom_get_default_root)
        setattr(sys.modules['omni.paint.brush.scatter.brush.utils'], 'get_stage_up', custom_get_stage_up)
        setattr(sys.modules['omni.paint.brush.scatter.brush.scatter_brush'], 'get_default_root', custom_get_default_root)
        setattr(sys.modules['omni.paint.brush.scatter.brush.scatter_brush'], 'get_stage_up', custom_get_stage_up)
        setattr(sys.modules['omni.paint.brush.scatter.brush.ui'], 'get_default_root', custom_get_default_root)
        setattr(sys.modules['omni.paint.brush.scatter.brush.ui'], 'get_stage_up', custom_get_stage_up)
    
    def end_brush(self, *args, **kwargs):
        super().end_brush(*args, **kwargs)
        commons.log_info(f"[RemixScatterBrush] End brush")
        # Reverting the monkey patching.
        setattr(sys.modules['omni.paint.brush.scatter.brush.utils'], 'get_default_root', ORIGINAL_GET_DEFAULT_ROOT)
        setattr(sys.modules['omni.paint.brush.scatter.brush.utils'], 'get_stage_up', ORIGINAL_GET_STAGE_UP)
        setattr(sys.modules['omni.paint.brush.scatter.brush.scatter_brush'], 'get_default_root', ORIGINAL_GET_DEFAULT_ROOT)
        setattr(sys.modules['omni.paint.brush.scatter.brush.scatter_brush'], 'get_stage_up', ORIGINAL_GET_STAGE_UP)
        setattr(sys.modules['omni.paint.brush.scatter.brush.ui'], 'get_default_root', ORIGINAL_GET_DEFAULT_ROOT)
        setattr(sys.modules['omni.paint.brush.scatter.brush.ui'], 'get_stage_up', ORIGINAL_GET_STAGE_UP)

    # called once at the beginning of a stroke, setup anything specific to the scripted brush functionality
    # return True if brush is valid, otherwise return False
    def begin_stroke(self, *args, **kwargs):
        ctx = usd.get_context()
        selection = ctx.get_selection().get_selected_prim_paths()
        if not selection:
            commons.log_error("You must have one scene mesh selected to paint on.")
            return False
        
        if len(selection) > 1:
            commons.log_error("You can only paint on a single mesh at a time.")
            return False
        
        current_stage = ctx.get_stage()
        if not custom_get_default_root(current_stage).startswith('/RootNode/meshes/mesh_'):
            commons.log_error(f"The selected mesh {selection[0]} is not valid. Is it a captured scene?")
            return False
        
        at_least_one_valid_asset = False
        for asset in self._brush["assets"]:
            # At least have one enabled asset
            if asset["enabled"]:
                if not os.path.isfile(asset["path"]):
                    asset["enabled"] = False
                    commons.log_error(f"Asset file {asset['path']} doesn't exist.")
                elif not 'rtx-remix/mods' in asset["path"]:
                    asset["enabled"] = False
                    commons.log_error(f"Asset file {asset['path']} is not a valid RTX Remix asset (Ex: Not located under rtx-remix/mods).")
                else:
                    at_least_one_valid_asset = True
        
        if not at_least_one_valid_asset:
            return False


        return super().begin_stroke(*args, **kwargs)
    
    # called once at the end of a stroke
    def end_stroke(self, *args, **kwargs):
        ctx = usd.get_context()
        current_stage = ctx.get_stage()
        prim_path = custom_get_default_root(current_stage)
        paint_tool_prim = current_stage.GetPrimAtPath(f"{prim_path}/PaintTool")
        if paint_tool_prim:
            for child in paint_tool_prim.GetAllChildren():
                point_instancer_path = f"{child.GetPath().pathString}/pointInstancer"
                if current_stage.GetPrimAtPath(point_instancer_path):
                    current_stage.RemovePrim(point_instancer_path)
        
        return super().end_stroke(*args, **kwargs)

    def create_params_ui(self, on_param_changed_fn, *args, **kwargs):
        """
        * call once for paint tool window to create ui for brush properties
        * use omni.paint.system.ui.create_standard_parameter_panel
        * or create custom ui by omni.ui
        * @ param on_param_changed_fn used to notify paint tool what brush parameter is changed:
        ** on_param_changed(property_name, property_value)
        """
        parent_window = kwargs.get("parent_window", None)
        self._params_ui = CustomParamsUi(self._brush, on_param_changed, parent_window=parent_window)
        return self._params_ui

