XML3D-Blender
=============

This is a very early version of a XML3D exporter for Blender.
<p align="center">
<img src="http://xml3d.org/xml3d/material/images/xml3d-blender-preview-360.png"/>
<img src="http://xml3d.org/xml3d/material/images/xml3d-blender-stats-360.png"/>
<a href="http://www.youtube.com/watch?feature=player_embedded&v=sGsUhVLiUso
" target="_blank"><img src="http://img.youtube.com/vi/sGsUhVLiUso/0.jpg" 
alt="Blender XML3D Export" width="360" height="264" /></a>
</p>

## Installation

The add-on is not yet in the Blender repository. Find the [latest archive here](https://github.com/ksons/xml3d-blender-exporter/releases). It is called io_scene_xml3d-X.Y.Z.zip.

You can install the archive using the ``Install from File...`` button in ``File->User preferences...->Add-ons``.
After installing you have to find the add-on and activate it.
<p align="center"><img width="50%" src="./doc/addon-install.png"/></p>

After this procedure, the exporter is available from  ``File->Export->XML3D (.html)``.

## Changelog

### 0.4.0 (2015-07-08)

Features:
  - xml3d.js 4.9 support
  - Export barycentric coordinates
  - Spot light shadows

### 0.3.0 (2015-03-11)

Features:

  - Asset Clustering
  - Statistics in Preview template
  - Improved UI for exporter options
  - Bugfixed: #9, #10
  
### 0.2.0 (2015-02-05)

Features:

  - Basic Armature support
  - Basic Armature Animation support
  - Textures converted to PNG (contribution from @jasu0x58)

### 0.1.0 (2015-01-01)

Features:

  - Basic Geometry support (based on assets)
  - Basic Material support
  - Basic Light support
  - Export Templates
  - Preview Template
    - Layers
    - Warnings
