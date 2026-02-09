import os
import sys

from pxr import UsdGeom, Gf, Usd
import omni
from omni.paint.brush.scatter import ScatterBrush, AssetEraser, PAINT_TOOL_ROOT_KIT
from omni.paint.brush.scatter.brush.utils import get_default_root, get_stage_up, get_paint_asset_path, get_paint_root, PointInstancePainter
from omni.paint.brush.scatter.brush import INSTANCING
from omni.paint.brush.scatter.brush.ui import ParamsUi
from omni import usd

from . import commons
from .utils import find_source_mesh_hash_prim


BRUSH_TYPE = "Remix Scatter"
ORIGINAL_GET_DEFAULT_ROOT = get_default_root
ORIGINAL_GET_STAGE_UP = get_stage_up
FLIP_UP_AXIS = False
ANCHOR_PRIM_PATH = ""
INST_SELECTION = None


def select_source_mesh(selection) -> str:
    ctx = usd.get_context()
    current_stage = ctx.get_stage()
    selected_prims = {
        path: current_stage.GetPrimAtPath(path)
        for path in selection
    }

    return find_source_mesh_hash_prim(current_stage, list(selected_prims.values())[0]).GetPath().pathString


def get_inst_selection_path(prim_path: str) -> str:
    if not INST_SELECTION:
        return prim_path
    
    _, mesh_prim_rest = '/'.join(prim_path.split('/', 4)[:-1]), '/'.join(prim_path.split('/', 4)[4:])
    inst_prim_path = '/'.join((INST_SELECTION.rstrip('/') + '/').split('/', 4)[:-1])
    return f"{inst_prim_path}"


def custom_get_default_root(stage):
    ctx = usd.get_context()
    current_stage = ctx.get_stage()
    anchor = ANCHOR_PRIM_PATH
    if not anchor:
        selection = ctx.get_selection().get_selected_prim_paths()
        if selection:
            anchor = selection[0]

    if anchor and current_stage.GetPrimAtPath(anchor.rstrip('/')):
        global INST_SELECTION
        INST_SELECTION = anchor.rstrip('/')
        # return ANCHOR_PRIM_PATH.rstrip('/')
        return select_source_mesh([anchor.rstrip('/')])

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
    elif property_name == 'anchor_prim_path':
        val: str = property_value.as_string
        if val and not val.endswith('/'):
            val += '/'
        global ANCHOR_PRIM_PATH
        ANCHOR_PRIM_PATH = val
        

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
            "options": ["None", "Point Instancing"],
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
        brush["anchor_prim_path_ui"] = {
            "key": "anchor_prim_path",
            "type": "str",
            "label": "Anchor Prim Path",
            "tooltip": "[Optional]: Defines a custom anchor to parent your painted meshes",
            "read_only": False,
        }
        brush["anchor_prim_path"] = ANCHOR_PRIM_PATH
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
        try:
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
        except Exception as e:
                commons.log_error(f"Error in begin_stroke: {e}")
                self._stroke_started = False
                return False
    
    # called once at the end of a stroke
    def end_stroke(self, *args, **kwargs):
        # Only remove pointInstancer prims when NOT using Point Instancing mode
        if self._brush.get("instancing") == INSTANCING.NONE:
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
    
    def _get_asset_parameters(self, stage, asset_url):
        asset_prim_path = get_paint_asset_path(stage, asset_url)
        asset_prim_path = get_inst_selection_path(asset_prim_path)
        asset_prim = stage.GetPrimAtPath(asset_prim_path)
        xformable = UsdGeom.Xformable(asset_prim)
        parent_transform = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default()).GetInverse()

        up_attr = asset_prim.GetAttribute("up_rot_axis")
        asset_up_axis = up_attr.Get() if up_attr else None

        return (parent_transform, asset_up_axis)
    
    def erase(self, position, *arg, **kwargs):
        """
        Reimplementing the erase method to support inst_<->mesh_ transform translation.
        """
        stage = self._usd_context.get_stage()
        height = self._painter.get_upAxis() * self._brush["vertical_offset"]
        radius = self._brush["size"]
        active_erasers = {}
        for asset in self._brush["assets"]:
            if asset["enabled"]:
                asset_prim_path = get_paint_asset_path(stage, asset["path"])
                asset_prim_path = get_inst_selection_path(asset_prim_path)
                asset_prim = stage.GetPrimAtPath(asset_prim_path)
                xformable = UsdGeom.Xformable(asset_prim)
                parent_transform = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default()).GetInverse()
                new_pos = parent_transform.GetTranspose() * Gf.Vec4d(position[0], position[1], position[2], 1)
                new_pos = Gf.Vec3d(new_pos[0], new_pos[1], new_pos[2])
                erase = AssetEraser(stage, asset["path"])
                if erase.prepare_erase(new_pos, height=height, radius=radius, **kwargs):
                    active_erasers[asset["path"]] = erase

        if len(active_erasers) > 0:
            omni.kit.commands.execute("ScatterBrushEraseCommand", erasers=active_erasers)
            return True
        return False
    
    def _preload_assets(self, stage):
        if stage:
            paint_root = custom_get_default_root(stage) + PAINT_TOOL_ROOT_KIT
            stage.DefinePrim(paint_root, "Xform")
            for asset in self._brush["assets"]:
                if asset["enabled"]:
                    asset_url = asset["path"]
                    asset_paint_root = get_paint_root(stage, asset_url)
                    stage.DefinePrim(asset_paint_root, "Xform")
                    PointInstancePainter(stage, asset_url)

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

