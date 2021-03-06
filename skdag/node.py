# AUTOGENERATED! DO NOT EDIT! File to edit: notebooks_dev/node.ipynb (unless otherwise specified).

__all__ = ['BaseNode', 'BaseInputNode', 'Input', 'Target', 'NodeEstimator', 'ConcatenateNode']

# Cell

import os
from pathlib import Path
from warnings import warn
from collections import defaultdict

from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.exceptions import NotFittedError
from sklearn.preprocessing import FunctionTransformer
import joblib

from scipy import sparse
import numpy as np

from .utils import SimpleCacher, EstimatorCacher

# Cell
#TODO: define node name validaton rules
def _validate_name(name):
    '''
    function to validate node names.
    for now, any name is accepeted.
    '''
    return name


# Cell
def _validate_input_nodes(input_nodes, child_name):
    '''
    checks if input nodes are valid (NodeTransformer).
    If not NodeTransformer but valid BaseEstimator instance, wrapps BaseEstimator in NodeTransformer
    '''

    processed_nodes = []
    for node in input_nodes:
        if isinstance(node, NodeTransformer):
            processed_nodes.append(node)

        elif isinstance(node, BaseEstimator):
            node = NodeTransformer(node, 'Parent' + child_name)
            process_nodes.append()

# Cell
class BaseNode(BaseEstimator):
    '''
    Base class for nodes
    must have attribute name
    '''
    def __str__(self,):
        return self.name



# Cell
class BaseInputNode(BaseNode):

    def __init__(self, name = None):

        self.name = self._validate_name(name)
        #private attrs
        self.__value = None
        self.__has_value = False
        return

    @property
    def value(self,):

        if not self.has_value:
            raise NotFittedError(f'{self.name} has no value set to it. Call set_value with its respective input value prior to acessing value')

        return self.__value

    @property
    def has_value(self,):
        return self.__has_value

    def set_value(self, value):
        self.__value = value
        self.__has_value = True
        return self

    def get_value(self):
        return self.value

    def clear_value(self):
        self.__value = None
        self.__has_value = False
        return self


    def transform(self,X = None, **kwargs):
        return self.get_value()

    def fit(self,X = None, y = None, **kwargs):
        self.set_value(X)
        return self



# Cell
class Input(BaseInputNode):

    '''
    An input node for X values
    '''
    def _validate_name(self, name):

        #implements validation logic
        if name is None:
            name = 'X_' + str(id(self))
        else:
            name = name

        return name

class Target(BaseInputNode):

    '''
    An input node for y values
    '''
    def _validate_name(self, name):

        #implements validation logic
        if name is None:
            name = 'y_' + str(id(self))
        else:
            name = name

        return name

# Cell
class NodeEstimator(BaseNode, TransformerMixin):

    def __init__(self, estimator, name = None, transform_method = 'transform', cached_estimator = False, cachedir = './_skdag_cache'):


        self.cachedir = Path(cachedir)
        self.cached_estimator = cached_estimator
        self.name = self._validate_name(name)

        self.estimator = None
        if not cached_estimator:
            self.estimator = clone(estimator)
        else:
            self.estimator = EstimatorCacher(clone(estimator), serializer = joblib, dirpath = self.cachedir)

        self.transform_method = transform_method
        #private attributes
        self.__frozen = False
        self.__input_nodes = ()
        self.__target_node = None
        return

    def __call__(self, *input_nodes):
        self._set_input_nodes(*input_nodes)
        return self


    def _set_input_nodes(self, *input_nodes):

        '''
        sets self.inputs_nodes
        '''

        for node in input_nodes:
            if not isinstance(node, (NodeEstimator, BaseInputNode)):
                raise TypeError(f'All input nodes should be instances of NodeEstimator or Target')

        self.__input_nodes = input_nodes

        return

    def _set_target_node(self, target_node):

        if not isinstance(target_node, (NodeEstimator, Input)):
            raise TypeError(f'All input nodes should be instances of NodeEstimator or Input')

        self.__target_node = target_node
        return

    def __getattr__(self, attr):
        '''
        returns self.estimator attribute, if it does not exist in parent class
        '''
        return getattr(self.estimator, attr)

    def freeze(self,):
        '''
        freezes node, that is, when fit is called, no fitting is performed and self is returned.
        After running fit once, the node is automatically unfreezed
        '''
        self.__frozen = True
        return self

    def unfreeze(self,):
        '''
        freezes node, that is, when fit is called, no fitting is performed and self is returned.
        After running fit once, the node is automatically unfreezed
        '''
        self.__frozen = False
        return self

    @property
    def frozen(self,):
        return self.__frozen

    @property
    def input_nodes(self,):
        return self.__input_nodes

    @property
    def target_node(self,):
        return self.__target_node

    def _validate_name(self, name):

        #implements validation logic
        if name is None:
            name = 'Task' + str(id(self))
        else:
            name = name

        return name

    def transform(self, X, **kwargs):
        return getattr(self.estimator, self.transform_method)(X, **kwargs)

    def fit(self, X, y = None, **kwargs):

        if self.frozen:
            self.unfreeze()
            return self

        else:
            self.estimator.fit(X, y = None, **kwargs)
            return self


    def __del__(self,):
        '''
        implemetns logic to delete cached estimator files
        '''

        self.estimator = None
        return

    def __getstate__(self,):
        '''handles cached attriutes when pickling'''

        if self.cached_estimator:
            self.estimator = self.estimator.load()

        return self.__dict__

    def __setstate__(self, d):

        '''Caches cached serialized estimator'''

        if d['cached_estimator']:
            self.estimator = EstimatorCacher(d['estimator'], serializer = joblib, dirpath = d['cachedir'])

        return



# Cell

def _concat(X):

    '''
    concatenate function, handles mixed sparse and dense
    '''

    if not isinstance(X, (tuple, list)):
        raise TypeError(f'X must be list or tuple, got {type(X)}')

    X = list(X)
    for i in range(len(X)):
        if len(X[i].shape) < 2:
            X[i] = X[i].reshape(-1,1)

    if any([sparse.issparse(x) for x in X]):
        X = sparse.hstack(X)
    else:
        X = np.hstack(X)

    return X

class ConcatenateNode(NodeEstimator):
    '''
    transformer to concatenate (hstack) arrays in a tuple or list
    '''
    def __init__(self, name = None):
        super().__init__(FunctionTransformer(_concat), name = name)
        return