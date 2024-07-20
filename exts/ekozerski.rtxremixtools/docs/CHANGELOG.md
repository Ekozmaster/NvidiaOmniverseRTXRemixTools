# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.0.5] - 2024-07-20
- Adding support for Omniverse's Paint Tool scatter brush, to hand paint assets on mesh surfaces and being Remix-compatible.

## [0.0.4] - 2024-05-08
- Added tool to multi-select and import captures, merging repeated instances by transform matrix (position, rotation, scale...).

## [0.0.3] - 2023-12-22
- "Add Model", "Add Material" and "Fix Mesh Geometry" also works when not in a capture scene now.
- Fixed somes errors when using "Fix Mesh Geometry" option in some meshes.
- Added "Shift + F" hotkey to "Select Source Mesh".
- Fixed error when using "Setup for Mesh Replacement" on captures which nests original game meshes inside a "ref" Xform.
- Added convertion of many "primvar:*" name variations for UV-related primvars to "primvars:st" while discarding extra UV maps.
- Removing unused primvars "displayColor" and "displayOpacity".
- Xforms from added models and materials now are named according to the imported file rather than Xform_HASH_x

## [0.0.2] - 2023-08-28
- Fixing relative paths converted to absolute on the "Fix Meshes Geometry" function.
- Picking best UV map available between all primvars and discarding everything else in the "Fix Meshes Geometry"
- Removing unused primvars when using the "Fix Meshes Geometry".
- Few more bugfixes.

## [0.0.1] - 2023-08-25
- Initial version
- Added "Fix Meshes Geometry" option converting interpolation mode to "vertex".
- Added "Setup for Mesh Replacement" option to export the original mesh for remodeling by external DCC tools.
- Added "Add Model" option to add external authored .USD models to the mesh_HASH prim.
- Added "Add Material" option to add MDL materials to the mesh_HASH prim.
- Added "Original Draw Call Preservation" submenu to set.
- Added "Select Source Mesh" option to quickly select the mesh_HASH prim.
