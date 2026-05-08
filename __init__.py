"""
UkkeyHG-ImageSelector
=====================

Width-aware (image, mask) pair selector custom node for ComfyUI.

Routes one of multiple pre-processed (Image + Mask) pairs to the output
based on a reference image's width.

Install: copy this folder into ComfyUI/custom_nodes/ and restart ComfyUI.
After restart, find "Image Selector (3-way by width)" under the right-click
> Add Node > UkkeyHG/ menu.

Author: UkkeyHG
"""

from .nodes import UkkeyHGImageSelector

NODE_CLASS_MAPPINGS = {
    "UkkeyHGImageSelector": UkkeyHGImageSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UkkeyHGImageSelector": "Image Selector (3-way by width)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
