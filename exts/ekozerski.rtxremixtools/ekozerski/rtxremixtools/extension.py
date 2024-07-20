import omni.ext
import omni.ui as ui
from omni.kit import context_menu
from omni.kit.hotkeys.core import get_hotkey_registry
from omni.kit.actions.core import get_action_registry
from omni.paint.system.core import register_brush, unregister_brush
from omni.paint.brush.scatter.brush import get_ext_path

from . import commons
from .rtx_context_menu import build_rtx_remix_menu
from .brush import RemixScatterBrush


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class RtxRemixTools(omni.ext.IExt):
    def on_startup(self, ext_id):
        self.ext_id = ext_id
        commons.log_info(f"Starting Up")

        menu = {"name": "RTX Remix", "populate_fn": build_rtx_remix_menu}
        self._context_menu_subscription = context_menu.add_menu(menu, "MENU", "")
        self.hotkey_registry = get_hotkey_registry()

        register_actions(self.ext_id)
        self.select_source_mesh_hotkey = self.hotkey_registry.register_hotkey(
            self.ext_id,
            "SHIFT + F",
            self.ext_id,
            "select_source_mesh",
            filter=None,
        )

        register_brush(RemixScatterBrush.get_type(), __package__, RemixScatterBrush.__name__)
        

    def on_shutdown(self):
        commons.log_info(f"Shutting Down")
        # remove event
        self._context_menu_subscription.release()
        self.hotkey_registry.deregister_hotkey(
            self.select_source_mesh_hotkey,
        )
        deregister_actions(self.ext_id)
        unregister_brush(RemixScatterBrush.get_type(), __package__, RemixScatterBrush.__name__)


def register_actions(extension_id):
    from . import select_source_mesh

    action_registry = get_action_registry()
    actions_tag = "RTX Remix Tools Actions"

    action_registry.register_action(
        extension_id,
        "select_source_mesh",
        select_source_mesh.select_source_meshes,
        display_name="Select Source Mesh",
        description="Selects the corresponding mesh_HASH the prim is related to.",
        tag=actions_tag,
    )


def deregister_actions(extension_id):
    action_registry = get_action_registry()
    action_registry.deregister_all_actions_for_extension(extension_id)

