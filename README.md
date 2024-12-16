# Export Layers from GIMP Grid Generator

**Version:** 1.0.0  
**Website:** [Check our website](https://www.brundisium.org/recursos/plugins)

## Overview
This plugin helps you detect and export cells from an existing grid layer in a GIMP project. It scans your image for grid lines, identifies the cells formed, and exports the contents of each non-empty cell. Unlike simply slicing an image, this plugin intelligently looks for the top contributing layer of each cell and names the output files accordingly. It’s perfect for extracting assets from a templated grid, sprite sheets, or other structured images.

## Features
- Automatically detect horizontal and vertical grid lines from a specified grid layer.
- Identify non-empty cells and export them as individual PNG files.
- Determine the topmost contributing layer for each cell and name the file after that layer.
- Works with grayscale and RGBA images.
- Allows selective ignoring of background and grid layers during export.

## Installation
> [Download the latest release now](https://github.com/NICNE0/gimp-grid-exporter/archive/refs/tags/v1.0.0.zip)

1. Save the plugin script `export_grid_cells_plugin.py` (rename the provided code if necessary) into your GIMP plug-ins directory:
   - On macOS: `~/Library/Application Support/GIMP/2.10/plug-ins`
   - On Linux: `~/.config/GIMP/2.10/plug-ins`
   - On Windows: `%AppData%\GIMP\2.10\plug-ins`
   
2. Make the script executable:
   ```bash
   chmod +x export_grid_cells_plugin.py
   ```
   
3. Restart GIMP.
   
4. The plugin will appear under: `Toolbox > Filters > Custom > Export Grid Cells`.

## Usage
1. Prepare an image with a detected grid layer (e.g., a layer named "Grid") and optionally a background layer (e.g., named "Background").
2. Navigate to `Toolbox > Filters > Custom > Export Grid Cells`.
3. Configure the plugin parameters:
   
   - **Save Directory:** Specify the folder where exported cells will be saved.
   - **Grid Layer Name:** Enter the name of the layer containing the grid lines (default "Grid").
   - **Background Layer Name:** Enter the name of the background layer if present (default "Background").

4. Click "OK" to run the plugin.  
   The plugin will:
   - Detect grid cells.
   - Identify non-empty cells.
   - Determine the top layer contributing pixels to that cell.
   - Export each non-empty cell as a PNG file, named after the top contributing layer.
   
**Note:**  
If multiple cells come from the same top contributing layer, files will be uniquely suffixed to avoid overwriting.

## Example Configurations
- **Basic Export:**
  - Save Directory: `/path/to/export`
  - Grid Layer Name: `Grid`
  - Background Layer Name: `Background`
  
  This setup will scan your grid, ignore the background and grid layers, and export all non-empty cells.

## Troubleshooting
- **Plugin Doesn’t Appear in the Menu:**
  - Ensure the script is in your GIMP plug-ins directory.
  - Verify that the file has execution permissions.
  - Restart GIMP after installation.
  
- **Grid Detection Failed:**
  - Make sure the grid layer is correctly named and consists of visible, solid grid lines.
  - Check that the grid lines are not too faint (adjust intensity_threshold within the code if needed).

- **No Suitable Cells Found:**
  - Confirm that your grid layer forms clear, distinct cells.
  - Ensure that layers above the grid have visible pixels in their cells.

## Contributing
Feel free to contribute by suggesting new features, reporting issues, or submitting pull requests on [GitHub](https://github.com/NICNE0/gimp-grid-exporter).

## Licensing and Additional Information
This project is licensed under the MIT License. See the LICENSE file for more details.

You can include additional examples, tips, or frequently asked questions in this README as the project evolves.
