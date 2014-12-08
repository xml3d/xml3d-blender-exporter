import os, io, re
from . import xml_writer, export_asset
from bpy_extras.io_utils import create_derived_objects, free_derived_objects
from .tools import Stats, isIdentity

ASSETDIR = "assets"

def dump(obj):
    for attr in dir(obj):
        print("obj %s", attr)

def clamp_color(col):
    return tuple([max(min(c, 1.0), 0.0) for c in col])

class XML3DExporter:
    def __init__(self, context, dirname):
        self._context = context
        self._output = io.StringIO()
        self._writer = xml_writer.XMLWriter(self._output, 0)
        self._resource = {}
        self._dirname = dirname
        self._stats = Stats(assets = [], lights = 0, views = 0, groups = 0)

    def create_asset_directory(self):
        assetDir = os.path.join(self._dirname, ASSETDIR)
        if not os.path.exists(assetDir):
            os.makedirs(assetDir)
        return assetDir

    def create_resource_from_mesh(self, mesh_object, derived_object = None):
        mesh_data_name = mesh_object.data.name
        path = self.create_asset_directory()
        path = os.path.join(path, mesh_data_name + ".xml")
        url  = "./%s/%s.xml" % (ASSETDIR, mesh_data_name)

        exporter = export_asset.AssetExporter(path, self._context.scene)
        exporter.addMesh(mesh_object, derived_object)
        stats = exporter.save()

        stats.assets[0]["url"] = url
        self._stats.join(stats)
        return url + "#root"

    def create_resource(self, obj):
        free = None
        url = ""

        if obj.type == "MESH":
            meshData = obj.data
            key = "mesh." + meshData.name
            if key in self._resource:
                return self._resource[key]

            free, derived = create_derived_objects(self._context.scene, obj)

            if derived is None:
                return url

            url = self.create_resource_from_mesh(obj, derived)
            self._resource[key] = url

        if free:
            free_derived_objects(obj)
        return url

    def build_hierarchy(self, objects):
        """ returns parent child relationships, skipping
        """
        objects_set = set(objects)
        par_lookup = {}

        def test_parent(parent):
            while (parent is not None) and (parent not in objects_set):
                parent = parent.parent
            return parent

        for obj in objects:
            par_lookup.setdefault(test_parent(obj.parent), []).append((obj, []))

        for parent, children in par_lookup.items():
            for obj, subchildren in children:
                subchildren[:] = par_lookup.get(obj, [])

        return par_lookup.get(None, [])


    def write_id(self, obj, prefix = ""):
        id = prefix + obj.name
        # HTML: ID tokens must begin with a letter ([A-Za-z])
        if not id[:1].isalpha():
            id = "a" + id

        # and may be followed by any number of letters, digits ([0-9]),
        # hyphens ("-"), underscores ("_"), colons (":"), and periods (".")
        id = re.sub('[^a-zA-Z0-9-_:\.]+', '-', id)
        self._writer.attribute("id", id)

    def write_CSS_transform(self, obj) :
        #try:
        matrix = obj.matrix_basis

        if isIdentity(matrix):
            return

        # TODO: Write individual transformations instead (make matrix notation optional)
        transform = "matrix3d("
        transform += ",".join(["%.6f,%.6f,%.6f,%.6f" % (col[0],col[1],col[2],col[3])
                for col in matrix.col])
        transform += ")"
        self._writer.attribute("style", "transform:" + transform + ";")

    def write_class(self,obj):
        layers = []
        for i in range(len(obj.layers)):
            if obj.layers[i] == True:
                layers.append("layer-%d" % i)
        className = " ".join(layers)
        self._writer.attribute("class", className)

    def write_defaults(self, obj, prefix = ""):
        self.write_id(obj, prefix)
        self.write_class(obj)
        self.write_CSS_transform(obj)

    def create_camera(self, obj):
        self._writer.startElement("view")
        self.write_id(obj, "v_")
        self._writer.endElement("view")
        self._stats.views += 1

    def create_geometry(self, obj):
        self._writer.startElement("model")
        self._writer.attribute("src", self.create_resource(obj))
        self._writer.endElement("model")

    def create_lamp(self, obj):

        lightModel = None
        lightdata = obj.data
        if lightdata.type == "POINT":
            lightModel = "point"
        elif lightdata.type == "SPOT":
            lightModel = "spot"
        elif lightdata.type == "SUN":
            lightModel = "directional"
        else:
            print("Warning: Unknown light type '%s'." % lightdata.type)
            return

        self._writer.startElement("light", model=lightModel, id=obj.name)
        self.write_defaults(obj)
        self._writer.element("float3", name="color", _content="%.4f %.4f %.4f" % tuple(lightdata.color))
        self._writer.element("float", name="energy", _content="%.4f" % lightdata.energy)
        self._writer.endElement("light")
        self._stats.lights += 1


    def create_object(self, this_object, parent, children):
        self._writer.startElement("group")
        self.write_defaults(this_object, prefix="")

        if this_object.type == "CAMERA":
            self.create_camera(this_object)
        elif this_object.type in {'MESH', 'CURVE', 'SURFACE', 'FONT'}:
            self.create_geometry(this_object)
        elif this_object.type == "LAMP":
            self.create_lamp(this_object)
        else:
            print("Warning: Unhandled type '%s'.", this_object.type)

        for obj, object_children in children:
            self.create_object(obj, this_object, object_children)

        self._writer.endElement("group")
        self._stats.groups += 1

    def create_scene(self, scene):
        self._writer.startElement("xml3d", id=scene.name)
        if scene.camera:
            self._writer.attribute("activeView", "#v_%s" % scene.camera.name)

        render = scene.render
        resolution = render.resolution_x * render.resolution_percentage / 100, render.resolution_y * render.resolution_percentage / 100
        style = "width: 100%; height: 100%;" #% (resolution[1])
        if scene.world :
            bgColor = scene.world.horizon_color
            style += " background-color:rgb(%i,%i,%i);" % (bgColor[0] * 255, bgColor[1] * 255, bgColor[2] * 255)

        self._writer.attribute("style", style)

        hierarchy = self.build_hierarchy(scene.objects)
        for obj, children in hierarchy:
            self.create_object(obj, None, children)

        #xml3dElem.writexml(output)
        self._writer.endElement("xml3d")

    def scene(self):
        self.create_scene(self._context.scene)
        return self._output.getvalue()

def save(operator,
         context, filepath="",
         use_selection=True,
         global_matrix=None,
         ):

    import bpy
    import mathutils

    import time
    from bpy_extras.io_utils import create_derived_objects, free_derived_objects
    from string import Template

    """Save the Blender scene to a XML3D/HTML file."""

    # Time the export
    time1 = time.clock()

    dirName = os.path.dirname(__file__)
    templatePath = os.path.join(dirName, 'templates\\index.html')
    with open (templatePath, "r") as templateFile:
        data=Template(templateFile.read())
        file = open(filepath, 'w')
        xml3d_exporter = XML3DExporter(context, os.path.dirname(filepath))
        scene = xml3d_exporter.scene()
        file.write(data.substitute(title=context.scene.name,xml3d=scene))
        file.close()

        print(xml3d_exporter._stats.to_JSON())

    return {'FINISHED'}