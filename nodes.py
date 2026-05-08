"""
UkkeyHGImageSelector node implementation.

Selects one (image, mask) pair out of three based on a reference image's width.
"""

from __future__ import annotations

import torch


class UkkeyHGImageSelector:
    """
    Detects the width of `reference_image` and routes one of three
    pre-processed (image, mask) pairs to the output.

    Use case:
      - Load Image -> split into 3 adjustment branches,
        each producing an Image + Mask suitable for outpainting.
      - This node compares the original Load Image's width against
        three configured target widths and outputs the matching pair.
      - Output (image, mask) feeds into VAE Encode (for Inpainting),
        then KSampler completes the outpaint.

    Matching:
      - Width within `tolerance` pixels of width_a/b/c selects that pair.
      - If no match within tolerance, falls back to the closest one
        (and emits a console warning so the user notices).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "reference_image": ("IMAGE",),

                "image_a": ("IMAGE",),
                "mask_a": ("MASK",),
                "width_a": ("INT", {"default": 1376, "min": 32, "max": 8192, "step": 1}),

                "image_b": ("IMAGE",),
                "mask_b": ("MASK",),
                "width_b": ("INT", {"default": 1264, "min": 32, "max": 8192, "step": 1}),

                "image_c": ("IMAGE",),
                "mask_c": ("MASK",),
                "width_c": ("INT", {"default": 2752, "min": 32, "max": 8192, "step": 1}),

                "tolerance": ("INT", {
                    "default": 8,
                    "min": 0,
                    "max": 256,
                    "step": 1,
                    "tooltip": "Allowed pixel difference between reference width and target width. Use ~8 to absorb Gemini's slight output variations.",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image", "mask", "selected_branch")
    FUNCTION = "select"
    CATEGORY = "UkkeyHG"
    OUTPUT_NODE = False

    def select(
        self,
        reference_image: torch.Tensor,
        image_a: torch.Tensor, mask_a: torch.Tensor, width_a: int,
        image_b: torch.Tensor, mask_b: torch.Tensor, width_b: int,
        image_c: torch.Tensor, mask_c: torch.Tensor, width_c: int,
        tolerance: int,
    ):
        # ComfyUI passes images as torch.Tensor with shape (B, H, W, C).
        # Reference width is the third dimension.
        ref_width = int(reference_image.shape[2])

        candidates = [
            ("A", width_a, image_a, mask_a),
            ("B", width_b, image_b, mask_b),
            ("C", width_c, image_c, mask_c),
        ]

        # Phase 1: try exact (within tolerance) match
        for label, target_w, img, msk in candidates:
            if abs(ref_width - target_w) <= tolerance:
                selected = f"Branch {label} (ref_width={ref_width}, target={target_w}, diff={abs(ref_width - target_w)})"
                print(f"[UkkeyHG-ImageSelector] {selected}")
                return (img, msk, selected)

        # Phase 2: no exact match → pick closest, warn loudly
        distances = [(abs(ref_width - tw), label, tw, img, msk)
                     for label, tw, img, msk in candidates]
        distances.sort(key=lambda t: t[0])
        diff, label, target_w, img, msk = distances[0]

        warning = (
            f"[UkkeyHG-ImageSelector] WARNING: no width match within tolerance={tolerance}. "
            f"ref_width={ref_width}, candidates=({width_a}, {width_b}, {width_c}). "
            f"Falling back to closest: Branch {label} (target={target_w}, diff={diff})."
        )
        print(warning)

        selected = f"Branch {label} [FALLBACK] (ref_width={ref_width}, target={target_w}, diff={diff})"
        return (img, msk, selected)


# Optional: when ComfyUI re-evaluates the graph, this hint tells it
# the node's output depends on inputs (no caching surprises).
UkkeyHGImageSelector.IS_CHANGED = lambda *args, **kwargs: float("nan")
