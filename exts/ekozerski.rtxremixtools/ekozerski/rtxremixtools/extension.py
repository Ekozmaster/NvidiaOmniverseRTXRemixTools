import omni.ext
import omni.ui as ui
from omni.kit import context_menu

from . import commons
from .rtx_context_menu import build_rtx_remix_menu


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class RtxRemixTools(omni.ext.IExt):
    def on_startup(self, ext_id):
        commons.log_info(f"Starting Up")

        menu = {"name": "RTX Remix", "populate_fn": build_rtx_remix_menu}
        self._context_menu_subscription = context_menu.add_menu(menu, "MENU", "")

    def on_shutdown(self):
        commons.log_info(f"Shutting Down")
        # remove event
        self._context_menu_subscription.release()
