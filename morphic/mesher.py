'''
This module contains the higher level functions for creating and
manipulating meshes.

Todo:

Fix values for fitting purposes.

MapNode - ability to map values from other nodes. Essentially, use their
parameters.

DepNode with calculation of derivatives to allow calculating derivatives
on lagrange elements to be used by a hanging node for a cubic-Hermite
element. Might also allow the flipping of derivatives in case the
hanging element has an opposite orientation. This is included here
because it already does calculations.

Field class to describe the field structure. Maybe we can access values
using node.x or node.x.0 for values and node.x.1 for other components.

Different interpolation types for each field. For example, one might
have x, y, z and Temperature field. Could describe x, y, z using a
bilinear interpolation but temperature as a bicubic-Hermite
interpolation.


'''
import os
import sys
import numpy

import core
import discretizer

class Values(numpy.ndarray):
    '''
    This is a temporary object passed to the user when setting node
    values.
    '''
    def __new__(cls, input_array, node, cids):
        obj = numpy.asarray(input_array).view(cls)
        obj.node = node
        obj.cids = cids
        return obj

    def __setitem__(self, name, values):
        flat_cids = numpy.array(self.cids).reshape(self.shape)[name].flatten()
        self.node._set_values(flat_cids, values)


class NodeValues(object):
    
    def __get__(self, instance, owner):
        x = instance.mesh._core.P[instance.cids].reshape(instance.shape)
        return Values(x, instance, instance.cids)
    
    def __set__(self, instance, values):
        if values.shape != instance.shape:
            raise IndexError('Cannot set values with a different shaped'
                    + ' array. User node.set_values(values) instead') 
        instance.mesh._core.P[instance.cids] = values.reshape(-1)
        


class Node(object):
    '''
    This is the super-class for StdNode and DepNode.
    '''
    
    values = NodeValues()
    
    def __init__(self, mesh, uid):
        self._type = 'standard'
        self.mesh = mesh 
        self.id = uid
        self.fixed = None
        self.cids = None
        self.num_values = 0
        self.num_fields = 0
        self.num_components = 0
        self.num_modes = 0
        self.shape = (0, 0, 0)
        self._added = False
        self._uptodate = False
        self.mesh._regenerate = True
        self.mesh._reupdate = True
        
    @property
    def field_cids(self):
        return self._get_param_indicies()
    
    def _save_dict(self):
        node_dict = {}
        node_dict['id'] = self.id
        node_dict['fixed'] = self.fixed
        node_dict['cids'] = self.cids
        node_dict['num_values'] = self.num_values
        node_dict['num_fields'] = self.num_fields
        node_dict['num_components'] = self.num_components
        node_dict['shape'] = self.shape
        return node_dict
        
    def _load_dict(self, node_dict):
        if node_dict['id'] != self.id:
            raise 'Ids do not match'
        self.fixed = node_dict['fixed']
        self.cids = node_dict['cids'] 
        self.num_values = node_dict['num_values']
        self.num_fields = node_dict['num_fields']
        self.num_components = node_dict['num_components']
        if 'shape' in node_dict.keys():
            self.shape = node_dict['shape']
        else:
            self.shape = (self.num_fields, self.num_components)
        self._added = True
        
    def _set_values(self, pids, values):
        self.mesh._core.P[pids] = values
        
    def set_values(self, values):
        '''
        Sets the values for the node by adding them to core.
        If the nodes values have already been set, it will update the
        values. Note, the number of fields
        and components cannot change when updating the values.
        
        ``values`` can be of the form:
            - [0.2, 0.5] or [[0.2], [0.5]] which sets two field values
            - [[0.2 1, 0], [0.5, .3, 1]] which sets two fields with two components each.
        '''
        # Sets the number of values, fields and components.
        values = numpy.array(values, dtype='float')
        self.num_values = values.size
        self.num_fields = values.shape[0]
        self.num_components = 1
        self.shape = values.shape
        
        if len(values.shape) >= 2:
            self.num_components = values.shape[1]
        
        if len(values.shape) >= 3:
            self.num_modes = values.shape[2]
        
        # Updates the values in core if they exist otherwise adds them.
        params = values.reshape(self.num_values) 
        if self._added:
            self.mesh._core.update_params(self.cids, params)
        else:
            self.cids = self.mesh._core.add_params(params)
        
        self._added = True
        self.mesh._regenerate = True
        self.mesh._reupdate = True
        
    def get_values(self, index=None):
        if index == None:
            return self.mesh._core.P[self.cids].reshape(
                    (self.num_fields, self.num_components))
    
    def fix(self, fix):
        '''
        This function will the values of the node, which is used for
        fitting. The values can be fixed in three forms:
          - node.fix(True) will fix all the values
          - node.fix([False, True, False]) will fix all the values in 
            field 2 and unfix all others.
          - node.fix([[True, False], [False, True]] will fix the first 
            component in field 1 and the second component in field 2.
        
        '''
        if isinstance(fix, bool):
            self.fixed = fix * numpy.ones(self.num_values, dtype=bool)
        elif isinstance(fix, list):
            fixed = []
            for f1 in fix:
                if isinstance(f1, bool):
                    fixed.extend([f1 for ncomp in range(self.num_components)])
                else:
                    fixed.extend([f2 for f2 in f1])
            self.fixed = fixed
        self.mesh._core.fix_parameters(self.cids, self.fixed)
        
    def _get_param_indicies(self):
        pi = []
        ind = 0
        for f in range(self.num_fields):
            pi.append(self.cids[ind:ind+self.num_components])
            ind += self.num_components
        return pi
        
    
class StdNode(Node):
    '''
    .. autoclass:: morphic.mesher.Node
    '''
    
    def __init__(self, mesh, uid, values):
        Node.__init__(self, mesh, uid)
        self._type = 'standard'
        if values != None:
            self.set_values(values)
        
    def _save_dict(self):
        node_dict = Node._save_dict(self)
        node_dict['type'] = self._type
        return node_dict
        
    def _load_dict(self, node_dict):
        Node._load_dict(self, node_dict)
        
        
class DepNode(Node):

    def __init__(self, mesh, uid, element, node):
        Node.__init__(self, mesh, uid)
        self._type = 'dependent'
        self.element = element
        self.node = node
     
    def _save_dict(self):
        node_dict = Node._save_dict(self)
        node_dict['type'] = self._type   
        node_dict['element'] = self.element   
        node_dict['node'] = self.node
        return node_dict
    
    def _load_dict(self, node_dict):
        Node._load_dict(self, node_dict)
        self.element = node_dict['element']
        self.node = node_dict['node'] 
    
class PCANode(Node):

    def __init__(self, mesh, uid, node_id, weights_id, variance_id):
        Node.__init__(self, mesh, uid)
        self._type = 'pca'
        self.node_id = node_id
        self.weights_id = weights_id
        self.variance_id = variance_id
        
        OK = True
        if OK and node_id in self.mesh.nodes:
            self.node = self.mesh.nodes[self.node_id]
        else:
            print 'Warning: PCA node not initialised'
            OK = False
        
        if OK and weights_id in self.mesh.nodes:
            self.weights = self.mesh.nodes[self.weights_id]
        else:
            print 'Warning: PCA node not initialised'
            OK = False
        
        if OK and variance_id in self.mesh.nodes:
            self.variance = self.mesh.nodes[self.variance_id]
        else:
            print 'Warning: PCA node not initialised'
            OK = False
        
        if OK:
            self.set_values(self.node.values[:,:,0])
            self._pca_id = self.mesh._core.add_pca_node(self)
            self._added = self._pca_id > -1
        
        #~ if self._added:
            #~ self._uptodate = self.mesh._core.update_pca_node(self._pca_id)
    
    #~ @property
    #~ def values(self):
        #~ Xn = self.mesh.nodes[self.node_id].values
        #~ W = self.mesh.nodes[self.weights_id].values
        #~ V = self.mesh.nodes[self.variance_id].values
        #~ return numpy.dot(Xn, W*V)
     
    #~ def _save_dict(self):
        #~ node_dict = Node._save_dict(self)
        #~ node_dict['type'] = self._type   
        #~ node_dict['element'] = self.element   
        #~ node_dict['node'] = self.node
        #~ return node_dict
    #~ 
    #~ def _load_dict(self, node_dict):
        #~ Node._load_dict(self, node_dict)
        #~ self.element = node_dict['element']
        #~ self.node = node_dict['node'] 
    
    
class Element(object):

    def __init__(self, mesh, uid, interp, node_ids):
        self.mesh = mesh 
        self.interp = interp 
        self.basis = interp 
        self.id = uid
        self.node_ids = node_ids
        self.cid = None
        
        self._set_shape()
        
        self.mesh._regenerate = True
        self.mesh._reupdate = True
    
    @property
    def nodes(self):
        return self.mesh.nodes[self.node_ids]
        
    @nodes.setter
    def nodes(self, nodes):
        self.node_ids = [node.id for node in nodes]
    
    def _set_shape(self):
        if self.interp:
            if len(self.interp) == 1:
                self.shape = 'line'
            else:
                self.shape = 'quad'
            if self.interp[0][0] == 'T':
                self.shape = 'tri'
    
    def _save_dict(self):
        elem_dict = {}
        elem_dict['id'] = self.id
        elem_dict['interp'] = self.interp
        elem_dict['nodes'] = self.node_ids
        elem_dict['shape'] = self.shape
        return elem_dict
     
    def _load_dict(self, elem_dict):
        if elem_dict['id'] != self.id:
            raise 'Ids do not match'
        self.interp = elem_dict['interp']
        self.node_ids = elem_dict['nodes'] 
        self.shape = elem_dict['shape']
        self._set_shape()
        
    def _get_param_indicies(self):
        PI = None
        for node in self:
            if PI == None:
                self.num_fields = node.num_fields
                PI = []
                for i in range(node.num_fields):
                    PI.append([])
            npi = node._get_param_indicies()
            for i, pi in enumerate(npi):
                PI[i].extend(pi)
        
        return PI
        
    def set_core_id(self, cid):
        self.cid = cid
        
    def grid(self, res=[8, 8]):
        return discretizer.xi_grid(
                shape=self.shape, res=res, units='div')[0]
                
    def weights(self, xi, deriv=None):
        return self.mesh._core.weights(self.cid, xi, deriv=deriv)
        
    def interpolate(self, xi, deriv=None):
        xi = numpy.asarray(xi)
        xi_dims = len(xi.shape)
        if xi_dims == 1:
            xi = numpy.array([xi])
            return self.mesh._core.interpolate(
                    self.cid, xi, deriv=deriv)[0]
        else:
            return self.mesh._core.interpolate(
                    self.cid, xi, deriv=deriv)
    
    def normal(self, Xi):
        '''
        Calculates the surface normals at xi locations on an element.
        
        Xi is an ``mxn`` ndarray where ``m`` is the number of element
        locations and ``n`` is the number of element dimensions.
        
        For example,
        
        .. code-block:: python
        
            Xi = numpy.array([[0.1, 0.1], [0.3, 0.2], [0.7, 0.2]])
        
        '''
        dx1 = self.mesh._core.interpolate(self.cid, Xi, deriv=[1, 0])
        dx2 = self.mesh._core.interpolate(self.cid, Xi, deriv=[0, 1])
        return numpy.cross(dx1, dx2)
    
    def _project_objfn(self, xi, *args):
        x = args[0]
        xe = self.interpolate(xi)
        dx = xe - x
        return numpy.sum(dx * dx)
    
    def project(self, x, xi=None, xtol=1e-4, ftol=1e-4):
        from scipy.optimize import fmin
        if xi == None:
            if self.shape == 'line':
                xi = 0.5
            else:
                xi = [0.5, 0.5]
        xi_opt = fmin(self._project_objfn, xi, args=(x),
                xtol=xtol, ftol=ftol, disp=False)
        return xi_opt
        
    def __iter__(self):
        return self.nodes.__iter__()
        
    
class Mesh(object):
    '''
    This is the top level object for a mesh which allows:
    
        * building a mesh
        * analysis or rendering of a mesh
        * saving and loading meshes.
    
    A mesh consists of nodes and elements. There are two types of nodes
    that can be added to a mesh:
    
        * standard nodes, which is stores fields values, for example, 
          x, y, and z coordinates.
        
        * dependent nodes, which are embedded in an element. A hanging 
          node can be added to a mesh using a dependent node.
        
    There are many interpolation schemes that can be used to
    create an element:
        * 1D and 2D lagrange basis up to 4th order
        * 1D and 2D Hermite basis (cubic only)
        * 2D triangular elements up to 4th order.
    
    .. note::
    
        Higher order interpolants (3D) will be added in the future.
    
    
    **Building a 1D Mesh**
    
    Here is an example of a simple 1D mesh which consists of two 1D
    linear element. First, we initialise a mesh,
    
    >>> mesh = Mesh()
    
    Add a few nodes,
    
    >>> n = mesh.add_stdnode(1, [0, 0])
    >>> n = mesh.add_stdnode(2, [1, 0.5])
    >>> n = mesh.add_stdnode(3, [2, 0.3])
    
    Add two linear elements,
    
    >>> e = mesh.add_element(1, ['L1'], [1, 2])
    >>> e = mesh.add_element(2, ['L1'], [2, 3])
    
    >>> xi = [0, 0.25, 0.5, 0.75, 1.0]
    >>> X = mesh.interpolate(1, xi)
    >>> X
    array([[ 0.   ,  0.   ],
           [ 0.25 ,  0.125],
           [ 0.5  ,  0.25 ],
           [ 0.75 ,  0.375],
           [ 1.   ,  0.5  ]])
    
    
    **Building a 2D Mesh**
    
    Here is an example of a 2D mesh which consists of two quadratic-linear
    elements. First, we initialise a mesh,
    
    >>> mesh = Mesh()
    
    Add ten nodes,
    
    >>> n = mesh.add_stdnode(1, [0, 0, 0])
    >>> n = mesh.add_stdnode(2, [1, 0, 0.5])
    >>> n = mesh.add_stdnode(3, [2, 0, 0.3])
    >>> n = mesh.add_stdnode(4, [3, 0, 0.2])
    >>> n = mesh.add_stdnode(5, [4, 0, -0.1])
    >>> n = mesh.add_stdnode(6, [0, 1.2, 0])
    >>> n = mesh.add_stdnode(7, [1, 1.2, 0.5])
    >>> n = mesh.add_stdnode(8, [2, 1.2, 0.3])
    >>> n = mesh.add_stdnode(9, [3, 1.2, 0.2])
    >>> n = mesh.add_stdnode(10, [4, 1.2, -0.1])
    
    
    Add two quadratic-linear lagrange elements,
    
    >>> e = mesh.add_element(1, ['L2', 'L1'], [1, 2, 3, 6, 7, 8])
    >>> e = mesh.add_element(2, ['L2', 'L1'], [3, 4, 5, 8, 9, 10])
    
    >>> # Analyse (interpolate, calculate derivatives and normals)
    >>> xi = [[0.3, 0.5]]
    
    Interpolate coordinates at xi=[0.3, 0.5] on element 1,
    
    >>> X = mesh.interpolate(1, xi)
    
    Calculate derivatives at xi = [0.3, 0.5] on element 2,
    
    >>> dx1 = mesh.interpolate(2, xi, deriv=[1, 0]) # dx/dxi1
    >>> dx2 = mesh.interpolate(2, xi, deriv=[0, 1]) # dx/dxi2
    >>> dx12 = mesh.interpolate(2, xi, deriv=[1, 1]) # d2x/dxi1.dxi2
    
    Calculate the element normal vector at xi=[0.3, 0.5] on element 1,
    
    >>> dn = mesh.normal(1, xi) # normal vector
    
    
    '''
    
    def __init__(self, filepath=None, label='/', units='m'):
        self._version = 1
        self.label = label
        self.units = units
        self.nodes = core.ObjectList()
        self.elements = core.ObjectList()
        
        self._core = core.Core()
        self._regenerate = True
        self._reupdate = True
        
        self.filepath = filepath
        if filepath != None:
            self.load(filepath)
        
    def add_stdnode(self, uid, values, group='_default'):
        '''
        Adds a node to a mesh.
        
        If None is given for the uid, the mesh will automatically
        increment a counter (starting at 1) and assign a unique id. If
        you would like to start the counter at 1, create your mesh as
        follows:
        >>> mesh = Mesh()
        >>> mesh.nodes.set_counter(1)
        >>> id = mesh.nodes.get_unique_id()
        >>> print id
        1
        
        There are two forms for entering node values for the variable x:
        - Simple form for when there is one type of value for each
        dimension e.g., [x, y, z] or [xi1, xi2] values
        - Component form for when each dimension has different types of
        values, e.g., x = [[x, dx1, dx2, dx12], [y, dy1, dy2, dy12]]
        
        >>> mesh = Mesh()
        >>> node1 = mesh.add_stdnode(1, [0.2, 0.1, 3.], group='xyz')
        >>> node2 = mesh.add_stdnode(None, [0.1], group='xi')
        >>> node3 = mesh.add_stdnode(None, [0.2], group='xi')
        >>> print node1.id, node1.values
        1 [ 0.2  0.1  3. ]
        >>> print node2.id, node2.values
        0 [ 0.1]
        >>> print node3.id, node3.values
        2 [ 0.2]
        
        '''
        if uid==None:
            uid = self.nodes.get_unique_id()
        node = StdNode(self, uid, values)
        self.nodes.add(node, group=group)
        return node
    
    def add_depnode(self, uid, element, node_id, group='_default'):
        '''
        Adds a dependent node to a mesh. A dependent node is typically
        an interpolated location on an element. The location on the 
        element is defined by a node.
        
        >>> mesh = Mesh()
        >>> node1 = mesh.add_stdnode(1, [0, 0])
        >>> node2 = mesh.add_stdnode(2, [2, 1])
        >>> elem1 = mesh.add_element('elem1', ['L1'], [1, 2])
        >>> hang1 = mesh.add_stdnode('xi', [0.6]) # element location
        >>> node3 = mesh.add_depnode(3, 'elem1', 'xi') # hanging node
        >>> print mesh.get_nodes([3])
        [[ 1.2  0.6]]
        '''
        if uid==None:
            uid = self.nodes.get_unique_id()
        node = DepNode(self, uid, element, node_id)
        self.nodes.add(node, group=group)
        return node
    
    def fix_values(self, uids, fix):
        if not isinstance(uid, list):
            uids = [uids]
        for uid in uids:
            self.nodes[uid].fix(fix)
    
    
    def add_element(self, uid, interp, node_ids, group='_default'):
        '''
        Adds a element to a mesh.
        
        >>> mesh = Mesh()
        >>> n1 = mesh.add_stdnode(1, [0.1])
        >>> n2 = mesh.add_stdnode(2, [0.2])
        >>> elem = mesh.add_element(1, ['L1'], [1, 2])
        >>> print elem.id, elem.interp, elem.node_ids
        1 ['L1'] [1, 2]
        '''
        if uid==None:
            uid = self.elements.get_unique_id()
        if isinstance(node_ids, numpy.ndarray):
            node_ids = node_ids.tolist()
        elem = Element(self, uid, interp, node_ids)
        self.elements.add(elem, group=group)
        return elem
        
    def _save_dict(self):
        import datetime
        mesh_dict = {}
        mesh_dict['_version'] = self._version
        mesh_dict['_datetime'] = datetime.datetime.now()
        mesh_dict['label'] = self.label
        mesh_dict['units'] = self.units
        mesh_dict['nodes'] = []
        mesh_dict['elements'] = []
        for node in self.nodes:
            mesh_dict['nodes'].append(node._save_dict())
        for elem in self.elements:
            mesh_dict['elements'].append(elem._save_dict())
        mesh_dict['values'] = self._core.P
        return mesh_dict
        
    def save(self, filepath):
        '''
        Saves a mesh.
        
        >>> mesh = Mesh()
        >>> mesh.save('data/cube.mesh')
        
        '''
        import pickle
        mesh_dict = self._save_dict()
        pickle.dump(mesh_dict, open(filepath, "w"))
        
    def _load_dict(self, mesh_dict):
        self.label = mesh_dict['label']
        self.units = mesh_dict['units']
        for node_dict in mesh_dict['nodes']:
            if node_dict['type'] == 'standard':
                node = self.add_stdnode(node_dict['id'], None)
            elif node_dict['type'] == 'dependent':
                node = self.add_depnode(node_dict['id'], None, None)
            #~ else:
                #~ raise InputError()
            node._load_dict(node_dict)
        for elem_dict in mesh_dict['elements']:
            elem = self.add_element(elem_dict['id'], None, None)
            elem._load_dict(elem_dict)
        self._core.P = mesh_dict['values']
        
    
    def load(self, filepath):
        '''
        Loads a mesh.
        
        >>> mesh = Mesh('data/cube.mesh')
        
        or
        
        >>> mesh = Mesh()
        >>> mesh.load('data/cube.mesh')
        
        '''
        import pickle
        self._load_dict(pickle.load(open(filepath, "r")))
        self.generate(True)
        
    
    def generate(self, force=False):
        '''
        Generates a flat representation of the mesh for faster
        computation.
        '''
        if self._regenerate == True or force:
            self._update_dependent_nodes()
            self._core.generate_element_map(self)
            self._core.generate_dependent_node_map(self)
            self._regenerate = False
            self._reupdate = True
        
        if self._reupdate == True:
            self._core.update_dependent_nodes()
            self._reupdate = False
        
    def update(self, force=False):
        '''
        Updates the dependent node. This update may be required if some
        mesh nodes or parameters have been changed. This function can be
        called with `force=True` to force an update, e.g.,
        mesh.update(force=True)
        '''
        if self._reupdate == True or force:
            self._core.update_dependent_nodes()
            self._reupdate = False
    
    def _update_dependent_nodes(self):
        for node in self.nodes:
            if node._type == 'dependent' and node._added == False:
                elem = self.elements[node.element]
                for enode in elem:
                    if enode.num_values > 0:
                        node.set_values(numpy.zeros(enode.num_values))
                        break
    def update_pca_nodes(self):
        self._core.update_pca_nodes()
    
    def get_variables(self):
        return self._core.get_variables()
    
    def set_variables(self, variables):
        self._core.set_variables(variables)
    
    def update_parameters(self, param_ids, values):
        self._core.update_params(param_ids, values)
    
    def interpolate(self, element_ids, xi, deriv=None):
        self.generate()
        if isinstance(xi, list):
            xi = numpy.array(xi)
            if len(xi.shape) == 1:
                xi = numpy.array([xi]).T
        else:
            if len(xi.shape) == 1:
                xi = numpy.array([xi]).T
                
        if not isinstance(element_ids, list):
            element_ids = [element_ids]
        
        node0 = self.elements[element_ids[0]].nodes[0]
        num_fields = node0.num_fields
        num_elements = len(element_ids)
        num_xi = xi.shape[0]
        X = numpy.zeros((num_xi * num_elements, num_fields))
        
        ind = 0
        for element in self.elements[element_ids]:
            X[ind:ind+num_xi, :] = element.interpolate(xi, deriv=deriv)
            ind += num_xi
            
        return X
    
    def normal(self, element_ids, xi, normalise=False):
        self.generate()
        if isinstance(xi, list):
            xi = numpy.array(xi)
            if len(xi.shape) == 1:
                xi = numpy.array([xi]).T
        else:
            if len(xi.shape) == 1:
                xi = numpy.array([xi]).T
                
        if not isinstance(element_ids, list):
            element_ids = [element_ids]
        
        node0 = self.elements[element_ids[0]].nodes[0]
        num_fields = node0.num_fields
        num_elements = len(element_ids)
        num_xi = xi.shape[0]
        X = numpy.zeros((num_xi * num_elements, num_fields))
        
        ind = 0
        for element in self.elements[element_ids]:
            X[ind:ind+num_xi, :] = element.normal(xi)
            ind += num_xi
        
        if normalise:
            R = numpy.sqrt(numpy.sum(X * X, axis=1))
            for axis in range(X.shape[1]):
                X[:,axis] /= R
            
        return X
    
    def grid(self, res=[8, 8], shape='quad'):
        return discretizer.xi_grid(
                shape=shape, res=res, units='div')[0]
                
    def get_nodes(self, nodes=None, group='_default'):
        self.generate()
        if nodes != None:
            if not isinstance(nodes, list):
                nodes = [nodes]
            nodes = self.nodes[nodes]
        else:
            nodes = self.nodes(group)
        Xn = []
        for node in nodes:
            if len(node.shape) == 1:
                Xn.append(node.values)
            else:
                Xn.append(node.values[:, 0])
        return numpy.array([xn for xn in Xn])
    
    def get_lines(self, res=8, group='_default'):
        self.generate()
        Xl = []
        xi = numpy.array([numpy.linspace(0, 1, res)]).T
        for i, elem in enumerate(self.elements(group)):
            Xl.append(self._core.interpolate(elem.cid, xi))
        return Xl
        
    def get_surfaces(self, res=8, elements=None, groups=None):
        self.generate()
        
        if elements == None:
            Elements = self.elements
        else:
            Elements = self.elements[elements]
        
        XiT, TT = discretizer.xi_grid(shape='tri', res=res)
        XiQ, TQ = discretizer.xi_grid(shape='quad', res=res)
        NPT, NTT = XiT.shape[0], TT.shape[0]
        NPQ, NTQ = XiQ.shape[0], TQ.shape[0]
        
        NP, NT = 0, 0
        for elem in Elements:
            if elem.shape == 'tri':
                NP += NPT
                NT += NTT
            elif elem.shape == 'quad':
                NP += NPQ
                NT += NTQ
                
        X = numpy.zeros((NP, 3))
        T = numpy.zeros((NT, 3), dtype='uint32')
        np, nt = 0, 0
        for elem in Elements:
            if elem.shape == 'tri':
                X[np:np+NPT,:] = self._core.interpolate(elem.cid, XiT)
                T[nt:nt+NTT,:] = TT + np
                np += NPT
                nt += NTT
            elif elem.shape == 'quad':
                X[np:np+NPQ,:] = self._core.interpolate(elem.cid, XiQ)
                T[nt:nt+NTQ,:] = TQ + np
                np += NPQ
                nt += NTQ
                
        return X, T
        
        
        
        
