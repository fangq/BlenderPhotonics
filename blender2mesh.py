import bpy
import oct2py as op
import numpy as np
import scipy.io
import os
import tempfile


class scene2mesh(bpy.types.Operator):
    bl_label = 'Convert Scene to Mesh'
    bl_description = "Create 3-D tetrahedral meshes using Iso2Mesh and Octave (please save your Blender session first!)"
    bl_idname = 'blenderphotonics.create3dmesh'

    # creat a interface to set uesrs' model parameter.

    bl_options = {"REGISTER", "UNDO"}
    keepratio: bpy.props.FloatProperty(default=1.0,name="Percent of the edges to be kept (0-1)")
    maxvolum: bpy.props.FloatProperty(default=100.0, name="Maximum tetrahedron volume")

    def func(self):
        oc = op.Oct2Py()
        oc.addpath(oc.genpath(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/script'))
        
        #remove camera and light
        for ob in bpy.context.scene.objects:
            ob.select_set(False)
            if ob.type == 'CAMERA':
                ob.select_set(True)
            elif ob.type == 'LIGHT':
                ob.select_set(True)
            bpy.ops.object.delete()

        obj = bpy.context.view_layer.objects.active
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.convert(target='MESH')
        if len(bpy.context.selected_objects)>=2:
            bpy.ops.object.join()

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        bpy.ops.object.editmode_toggle()

        #output mesh data to Octave
        # this works only in object mode,
        bpy.ops.object.select_all(action='SELECT')
        obj = bpy.context.view_layer.objects.active
        verts = []
        for n in range(len(obj.data.vertices)):
            vert = obj.data.vertices[n].co
            v_global = obj.matrix_world @ vert
            verts.append(v_global)
        edges = [edge.vertices[:] for edge in obj.data.edges]
        faces = [face.vertices[:] for face in obj.data.polygons]
        #print("="*40) # printing marker

        oc = op.Oct2Py()
        #oc.addpath(oc.genpath(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/iso2mesh'))

        v = np.array(verts)
        f = np.array(faces)
        
        # Remove last .stl file
        in_dir_ply = tempfile.gettempdir()+'/iso2mesh-'+os.environ.get('USER')+'/blenderphotonics';
        if not os.path.isdir(in_dir_ply):
            os.mkdir(in_dir_ply)

        lst_ply = os.listdir(in_dir_ply)
        c=0
        for item in lst_ply:
            fileName, fileExtension = os.path.splitext(lst_ply[c])
            if fileExtension == ".stl":
                os.remove(os.path.join(in_dir_ply,item))
                print ("Delete File: " + os.path.join(in_dir_ply,item))
            c=c+1

        # Save file
        scipy.io.savemat(in_dir_ply+'/'+'blendermesh.mat', mdict={'v':v, 'f':f, 'ratio':self.keepratio, 'maxv':self.maxvolum})
        oc.run(bpy.utils.user_resource('SCRIPTS', "addons")+'/BlenderPhotonics/script/blender2mesh.m')
        
        # import volum mesh to blender(just for user to check the result)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        bpy.ops.import_mesh.stl(filepath=in_dir_ply+'/volumic_mesh.stl', files=[{'name': in_dir_ply+'/volumic_mesh.stl'}], directory=in_dir_ply, filter_glob="*.stl")

    def execute(self, context):
        print("begin to genert volumic mesh")
        self.func()
        return {"FINISHED"}
