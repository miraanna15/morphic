import numpy

# Some systems have the mayavi2 module referenced by diffrent names.
try:
    from mayavi import mlab
    mlab_loaded = True
except:
    mlab_loaded = False

if not mlab_loaded :
    try:
        from mayavi import mlab
    except ImportError:
        print 'Enthought Mayavi mlab module not found'
        raise

def set_offscreen(offscreen):
    mlab.options.offscreen = offscreen

class Figure:
    
    def __init__(self, figure='Default', bgcolor=(.5,.5,.5)):
        self.figure = mlab.figure(figure, bgcolor=bgcolor)
        self.plots = {}
        
    def clear(self, label=None):
        if label == None:
            labels = self.plots.keys()
        else:
            labels = [label]
            
        mlab.figure(self.figure.name)
        
        for label in labels:
            mlab_obj = self.plots.get(label)
            if mlab_obj != None:
                if mlab_obj.name == 'Surface':
                    mlab_obj.parent.parent.parent.remove()
                else:
                    mlab_obj.parent.parent.remove()
                self.plots.pop(label)

    def get_camera(self):
        return (mlab.view(), mlab.roll())

    def set_camera(self, camera):
        mlab.view(*camera[0])
        mlab.roll(camera[1])

    def hide(self, label):
        if label in self.plots.keys():
            self.plots[label].visible = False

    def show(self, label):
        if label in self.plots.keys():
            self.plots[label].visible = True

    def plot_surfaces(self, label, X, T, scalars=None, color=None, rep='surface', opacity=1.0):
        
        mlab.figure(self.figure.name)
        
        if color == None:
            color = (1,0,0)
        
        mlab_obj = self.plots.get(label)
        if mlab_obj == None:
            if scalars==None:
                self.plots[label] = mlab.triangular_mesh(X[:,0], X[:,1], X[:,2], T, color=color, opacity=opacity, representation=rep)
            else:
                self.plots[label] = mlab.triangular_mesh(X[:,0], X[:,1], X[:,2], T, scalars=scalars, opacity=opacity)
        
        else:
            self.figure.scene.disable_render = True
            view = mlab.view()
            roll = mlab.roll()
            
            if X.shape[0] == mlab_obj.mlab_source.x.shape[0]:
                if scalars==None:
                    mlab_obj.mlab_source.set(x=X[:,0], y=X[:,1], z=X[:,2])
                    mlab_obj.actor.property.color = color
                    mlab_obj.actor.property.opacity = opacity
                else:
                    mlab_obj.mlab_source.set(x=X[:,0], y=X[:,1], z=X[:,2], scalars=scalars, opacity=opacity)
                
                
            else:
                self.clear(label)
                if scalars==None:
                    self.plots[label] = mlab.triangular_mesh(X[:,0], X[:,1], X[:,2], T, color=color, opacity=opacity, representation=rep)
                else:
                    self.plots[label] = mlab.triangular_mesh(X[:,0], X[:,1], X[:,2], T, scalars=scalars, opacity=opacity)
                
            mlab.view(*view)
            mlab.roll(roll)
            self.figure.scene.disable_render = False
            
    def plot_lines(self, label, X, color=None, size=0, opacity=1.):
        
        nPoints = 0
        for x in X:
            nPoints += x.shape[0]
        
        Xl = numpy.zeros((nPoints, 3))
        connections = []
        
        ind = 0
        for x in X:
            Xl[ind:ind+x.shape[0],:] = x
            for l in range(x.shape[0]-1):
                connections.append([ind + l, ind + l + 1])
            ind += x.shape[0]
        connections = numpy.array(connections)
        
        mlab.figure(self.figure.name)
        
        if color == None:
            color = (1,0,0)
        if size == None:
            size = 1
        
        mlab_obj = self.plots.get(label)
        if mlab_obj == None:
            self.plots[label] = mlab.points3d(Xl[:,0], Xl[:,1], Xl[:,2], color=color, scale_factor=0)
            self.plots[label].mlab_source.dataset.lines = connections
            mlab.pipeline.surface(self.plots[label], color=(1, 1, 1),
                              representation='wireframe',
                              line_width=size,
                              name='Connections', opacity=opacity)
        else:
            self.figure.scene.disable_render = True
            self.clear(label)
            self.plots[label] = mlab.points3d(Xl[:,0], Xl[:,1], Xl[:,2], color=color, scale_factor=0)
            self.plots[label].mlab_source.dataset.lines = connections
            #~ self.plots[label].mlab_source.update()
            mlab.pipeline.surface(self.plots[label], color=color,
                              representation='wireframe',
                              line_width=size,
                              name='Connections', opacity=opacity)
            self.figure.scene.disable_render = False
        
            
    def plot_lines2(self, label, X, scalars=None, color=None, size=0):
        
        mlab.figure(self.figure.name)
        
        if color == None:
            color = (1,0,0)
        
        mlab_obj = self.plots.get(label)
        if mlab_obj == None:
            if scalars==None:
                self.plots[label] = mlab.plot3d(X[:,0], X[:,1], X[:,2], color=color, tube_radius=size)
            else:
                self.plots[label] = mlab.plot3d(X[:,0], X[:,1], X[:,2], scalars, tube_radius=size)
        
        else:
            self.figure.scene.disable_render = True
            #~ view = mlab.view()
            
            #~ if X.shape[0] == mlab_obj.mlab_source.x.shape[0]:
                #~ if scalars==None:
                    #~ mlab_obj.mlab_source.set(x=X[:,0], y=X[:,1], z=X[:,2])
                    #~ mlab_obj.actor.property.color = color
                #~ else:
                    #~ mlab_obj.mlab_source.set(x=X[:,0], y=X[:,1], z=X[:,2], scalars=scalars)
                #~ 
            #~ else:
                #~ self.clear(label)
                #~ if scalars==None:
                    #~ self.plots[label] = mlab.plot3d(X[:,0], X[:,1], X[:,2], color=color, line_width=size)
                #~ else:
                    #~ self.plots[label] = mlab.plot3d(X[:,0], X[:,1], X[:,2], scalars, line_width=size)
            
            self.clear(label)
            if scalars==None:
                self.plots[label] = mlab.plot3d(X[:,0], X[:,1], X[:,2], color=color, tube_radius=size, reset_zoom=False)
            else:
                self.plots[label] = mlab.plot3d(X[:,0], X[:,1], X[:,2], scalars, tube_radius=size, reset_zoom=False)
            
            #~ mlab.view(*view)
            self.figure.scene.disable_render = False
            
    def plot_points(self, label, X, color=None, size=None, mode=None):
        
        mlab.figure(self.figure.name)
        
        if color==None:
            color=(1,0,0)
        
        if size == None and mode == None or size == 0:
            size = 1
            mode = 'point'
        if size == None:
            size = 1
        if mode==None:
            mode='sphere'
        
        if isinstance(X, list):
            X = numpy.array(X)
        
        if len(X.shape) == 1:
            X = numpy.array([X])
        
        mlab_obj = self.plots.get(label)
        if mlab_obj == None:
            if isinstance(color, tuple):
                self.plots[label] = mlab.points3d(X[:,0], X[:,1], X[:,2], color=color, scale_factor=size, mode=mode)
            else:
                self.plots[label] = mlab.points3d(X[:,0], X[:,1], X[:,2], color, scale_factor=size, scale_mode='none', mode=mode)
        
        else:
            self.figure.scene.disable_render = True
            view = mlab.view()
            roll = mlab.roll()
            
            ### Commented out since VTK gives an error when using mlab_source.set
            #~ if X.shape[0] == mlab_obj.mlab_source.x.shape[0]:
                #~ if isinstance(color, tuple):
                    #~ mlab_obj.mlab_source.set(x=X[:,0], y=X[:,1], z=X[:,2])
                    #~ mlab_obj.actor.property.color = color
                #~ else:
                    #~ mlab_obj.mlab_source.set(x=X[:,0], y=X[:,1], z=X[:,2], scalars=color)
                #~ 
                #~ 
            #~ else:
                #~ self.clear(label)
                #~ if isinstance(color, tuple):
                    #~ self.plots[label] = mlab.points3d(X[:,0], X[:,1], X[:,2], color=color, scale_factor=size, mode=mode)
                #~ else:
                    #~ self.plots[label] = mlab.points3d(X[:,0], X[:,1], X[:,2], color, scale_factor=size, scale_mode='none', mode=mode)
            
            self.clear(label)
            if isinstance(color, tuple):
                self.plots[label] = mlab.points3d(X[:,0], X[:,1], X[:,2], color=color, scale_factor=size, mode=mode)
            else:
                self.plots[label] = mlab.points3d(X[:,0], X[:,1], X[:,2], color, scale_factor=size, scale_mode='none', mode=mode)
                
            mlab.view(*view)
            mlab.roll(roll)
            self.figure.scene.disable_render = False
            
            
    def plot_text(self, label, X, text, size=1, color=(1,1,1)):
        view = mlab.view()
        roll = mlab.roll()
        self.figure.scene.disable_render = True
        
        scale = (size, size, size)
        mlab_objs = self.plots.get(label)
        
        if mlab_objs != None:
            if len(mlab_objs) != len(text):
                for obj in mlab_objs:
                    obj.remove()
            self.plots.pop(label)
        
        mlab_objs = self.plots.get(label)
        if mlab_objs == None:
            text_objs = []
            for x, t in zip(X, text):
                text_objs.append(mlab.text3d(x[0], x[1], x[2], str(t), scale=scale, color=color))
            self.plots[label] = text_objs
        elif len(mlab_objs) == len(text):
            for i, obj in enumerate(mlab_objs):
                obj.position = X[i,:]
                obj.text = str(text[i])
                obj.scale = scale
        else:
            print "HELP, I shouldn\'t be here!!!!!"
        
        mlab.view(*view)
        mlab.roll(roll)
        self.figure.scene.disable_render = False

    def plot_element_ids(self, label, mesh, size=1, color=(1,1,1)):
        Xecids = mesh.get_element_cids()
        for idx, element in enumerate(mesh.elements):
            Xp = element.evaluate([0.5,0.5], deriv=None)
            self.plot_text('{0}{1}'.format(
                label, element.id), [Xp], [element.id], size=5, color=color)

    def plot_image_data(self, label, scan, src, vis_object):

        mlab.figure(self.figure.name)
        
        mlab_objs = self.plots.get(label)
        if mlab_objs == None:
            self.plots[label] = {}
            self.plots[label]['src'] = src
            self.plots[label]['plane'] = vis_object
            self.plots[label]['filepaths'] = scan.filepaths
        else:
            #self.plots[label]['src'].origin = scan.origin
            self.plots[label]['src'].spacing = scan.spacing
            self.plots[label]['src'].scalar_data = scan.values
            self.plots[label]['plane'].update_pipeline()
            self.plots[label]['filepaths'] = scan.filepaths

    def visualise_dicom_plane(self, fig, scan, src, op):
        plane = mlab.pipeline.image_plane_widget(src,
                            plane_orientation='z_axes',
                            slice_index=int(0.5 * scan.num_slices),
                            colormap='black-white')
        fig.plot_image_data(op.volunteer, scan, src, plane)
        return plane

    def visualise_dicom_outline(self, scan, src):
        outline = mlab.pipeline.outline(src)
        return outline

    def visualise_dicom_volume(self, scan, src):
        volume = mlab.pipeline.volume(src)
        return volume

    def plot_vector(self, pt, vector, size=1, color=(1,0,0), scale=1):
          mlab.figure(self.figure.name)
          mlab.quiver3d(pt[0], pt[1], pt[2],
              vector[0], vector[1], vector[2],
              line_width=size, color=color, scale_factor=scale)
    

def define_scalar_field(x,y,z,scan):
    #import ipdb; ipdb.set_trace()
    #print scan.values.shape
    src = mlab.pipeline.scalar_field(x,y,z,scan.values)
#    src = mlab.pipeline.scalar_field(scan.values)
    #src.spacing = scan.spacing
    #import ipdb; ipdb.set_trace()
    return src
