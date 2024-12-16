#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gimpfu import *
import struct
import os

def detect_grid(img, grid_layer_name):
    grid_layer = None
    for layer in img.layers:
        if grid_layer_name in layer.name:
            grid_layer = layer
            break

    if not grid_layer:
        pdb.gimp_message("Grid layer not found! Make sure the layer name is correct.")
        return None, None, None, None, None, None, None

    grid_width, grid_height = grid_layer.width, grid_layer.height
    region = grid_layer.get_pixel_rgn(0, 0, grid_width, grid_height, False, False)
    pixel_data = region[:, :]

    bytes_per_pixel = region.bpp
    is_grayscale = (bytes_per_pixel == 1)

    unpack_format = "%dB" % len(pixel_data)
    pixels = struct.unpack(unpack_format, pixel_data)

    intensity_threshold = 50
    transparency_threshold = 250

    def group_consecutive_lines(lines):
        grouped_lines = []
        thicknesses = []
        if not lines:
            return grouped_lines, 1
        start = lines[0]
        count = 1
        for i in range(1, len(lines)):
            if lines[i] == lines[i - 1] + 1:
                count += 1
            else:
                grouped_lines.append(start)
                thicknesses.append(count)
                start = lines[i]
                count = 1
        grouped_lines.append(start)
        thicknesses.append(count)
        avg_thickness = sum(thicknesses) // len(thicknesses) if thicknesses else 1
        return grouped_lines, avg_thickness

    # Detect horizontal lines
    horizontal_lines = []
    for y in range(grid_height):
        is_line = True
        for x in range(grid_width):
            idx = (y * grid_width + x) * bytes_per_pixel
            if is_grayscale:
                intensity = pixels[idx]
                alpha = None
            else:
                r, g, b, a = pixels[idx:idx+4]
                intensity = (r + g + b) // 3
                alpha = a
            if intensity > intensity_threshold or (alpha is not None and alpha < transparency_threshold):
                is_line = False
                break
        if is_line:
            horizontal_lines.append(y)

    # Detect vertical lines
    vertical_lines = []
    for x in range(grid_width):
        is_line = True
        for y in range(grid_height):
            idx = (y * grid_width + x) * bytes_per_pixel
            if is_grayscale:
                intensity = pixels[idx]
                alpha = None
            else:
                r, g, b, a = pixels[idx:idx+4]
                intensity = (r + g + b) // 3
                alpha = a
            if intensity > intensity_threshold or (alpha is not None and alpha < transparency_threshold):
                is_line = False
                break
        if is_line:
            vertical_lines.append(x)

    horizontal_lines, horizontal_thickness = group_consecutive_lines(horizontal_lines)
    vertical_lines, vertical_thickness = group_consecutive_lines(vertical_lines)

    if len(horizontal_lines) > 1 and len(vertical_lines) > 1:
        cell_height = horizontal_lines[1] - horizontal_lines[0] - horizontal_thickness
        cell_width = vertical_lines[1] - vertical_lines[0] - vertical_thickness
        rows = len(horizontal_lines) - 1
        cols = len(vertical_lines) - 1
        return rows, cols, cell_width, cell_height, (horizontal_thickness, vertical_thickness), horizontal_lines, vertical_lines

    return None, None, None, None, None, None, None

def copy_visible_pixels(img, x, y, width, height):
    pdb.gimp_rect_select(img, x, y, width, height, CHANNEL_OP_REPLACE, False, 0)
    pdb.gimp_edit_copy_visible(img)
    temp_img = pdb.gimp_edit_paste_as_new()
    pasted_layer = temp_img.layers[0]
    hist = pdb.gimp_histogram(pasted_layer, HISTOGRAM_VALUE, 0, 255)
    pixel_count = hist[0]
    pdb.gimp_image_delete(temp_img)
    pdb.gimp_selection_none(img)
    return pixel_count

def find_top_contributing_layer(img, x, y, width, height, background_layer, grid_layer):
    """
    Identify the topmost contributing layer.
    Strategy:
    - Hide background and grid layers.
    - We'll progressively reveal layers from top to bottom:
      1. Check each layer alone. If any single layer alone shows pixels, return it.
      2. If no single layer alone shows pixels, build up layers from top down:
         Start with the top layer visible. If no pixels, add the next layer below and check again.
         Repeat until pixels appear. The layer that was just added when pixels appear is the contributor.
    """

    # Save current visibility states
    layers_visibility = [(layer, layer.visible) for layer in img.layers]

    # Determine layers to consider (all visible layers except background and grid)
    candidate_layers = [l for l in img.layers if l != background_layer and l != grid_layer and l.visible]

    # Hide all layers initially
    for (l, orig_vis) in layers_visibility:
        pdb.gimp_layer_set_visible(l, False)

    # Phase 1: Check each layer alone
    for layer in candidate_layers:
        pdb.gimp_layer_set_visible(layer, True)
        if copy_visible_pixels(img, x, y, width, height) > 0:
            # Restore original visibility
            for (lyr, orig_vis) in layers_visibility:
                pdb.gimp_layer_set_visible(lyr, orig_vis)
            return layer.name
        # Hide again before next test
        pdb.gimp_layer_set_visible(layer, False)

    # Phase 2: Build up from the top layer down until pixels appear
    visible_stack = []
    for layer in candidate_layers:
        # Add this layer to the visible stack
        pdb.gimp_layer_set_visible(layer, True)
        visible_stack.append(layer)

        pixel_count = copy_visible_pixels(img, x, y, width, height)
        if pixel_count > 0:
            # The content appeared after adding this layer,
            # which means this layer is actually providing the visible pixels
            name = layer.name
            # Restore original visibility
            for (lyr, orig_vis) in layers_visibility:
                pdb.gimp_layer_set_visible(lyr, orig_vis)
            return name

    # If we reach here, no pixels even after showing all candidate layers
    for (lyr, orig_vis) in layers_visibility:
        pdb.gimp_layer_set_visible(lyr, orig_vis)
    return "UnnamedLayer"

def export_cells(img, drawable, save_dir, grid_layer_name, background_layer_name):
    pdb.gimp_message("Starting grid cell export...")

    rows, cols, cell_width, cell_height, grid_thickness, horizontal_lines, vertical_lines = detect_grid(img, grid_layer_name)
    if not rows or not cols:
        pdb.gimp_message("Grid detection failed. Cannot export cells.")
        return

    if not os.path.isdir(save_dir):
        pdb.gimp_message("Save directory does not exist: %s" % save_dir)
        return

    # Find background and grid layers
    background_layer = None
    for layer in img.layers:
        if background_layer_name in layer.name:
            background_layer = layer
            break

    grid_layer = None
    for layer in img.layers:
        if grid_layer_name in layer.name:
            grid_layer = layer
            break

    if background_layer:
        pdb.gimp_layer_set_visible(background_layer, False)
    if grid_layer:
        pdb.gimp_layer_set_visible(grid_layer, False)

    non_empty_cells = []

    for row in range(rows):
        for col in range(cols):
            x = vertical_lines[col] + grid_thickness[1]
            y = horizontal_lines[row] + grid_thickness[0]
            width = cell_width
            height = cell_height

            if x < 0 or y < 0 or x + width > img.width or y + height > img.height:
                continue

            # Check if cell is non-empty with all visible layers (except background and grid)
            pixel_count = copy_visible_pixels(img, x, y, width, height)
            if pixel_count > 0:
                # Find top contributing layer
                layer_name = find_top_contributing_layer(img, x, y, width, height, background_layer, grid_layer)
                if not layer_name:
                    layer_name = "UnnamedLayer"

                # Ensure filename uniqueness
                filename = "%s.png" % layer_name
                full_path = os.path.join(save_dir, filename)
                base_name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(full_path):
                    filename = "%s_%d%s" % (base_name, counter, ext)
                    full_path = os.path.join(save_dir, filename)
                    counter += 1

                # Re-copy the full visible cell (all except background and grid)
                pdb.gimp_rect_select(img, x, y, width, height, CHANNEL_OP_REPLACE, False, 0)
                pdb.gimp_edit_copy_visible(img)
                pasted_image = pdb.gimp_edit_paste_as_new()
                pasted_layer = pasted_image.layers[0]

                pdb.file_png_save(pasted_image, pasted_layer, full_path, full_path, 0, 9, 0, 0, 0, 0, 0)
                pdb.gimp_image_delete(pasted_image)
                pdb.gimp_selection_none(img)

                non_empty_cells.append(filename)
            else:
                # Cell is empty, do nothing
                pdb.gimp_selection_none(img)

    # Restore background and grid visibility
    if background_layer:
        pdb.gimp_layer_set_visible(background_layer, True)
    if grid_layer:
        pdb.gimp_layer_set_visible(grid_layer, True)

    if non_empty_cells:
        pdb.gimp_message("Saved cells: %s" % ", ".join(non_empty_cells))
    else:
        pdb.gimp_message("No suitable cells found.")

    pdb.gimp_message("Export completed.")

register(
    "python_fu_export_grid_cells",
    "Export Grid Cells",
    "Detect and export non-empty cells from a grid, ignoring background and grid layers, naming files after the topmost contributing layer.",
    "NICNE0",
    "MIT",
    "2024",
    "<Image>/Filters/Custom/Grid Exporter",
    "RGB*, GRAY*",
    [
        (PF_DIRNAME, "save_dir", "Save Directory", ""),
        (PF_STRING, "grid_layer_name", "Grid Layer Name", "Grid"),
        (PF_STRING, "background_layer_name", "Background Layer Name", "Background")
    ],
    [],
    export_cells
)

main()
