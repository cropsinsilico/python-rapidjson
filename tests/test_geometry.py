# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- Normalizer class tests
# :Author:    Meagan Lang <langmm.astro@gmail.com>
# :License:   MIT License
# :Copyright: © 2017, 2019, 2020 Lele Gaifax
#

import pytest
import copy
import numpy as np

from rapidjson import geometry


@pytest.fixture(scope="session")
def mesh_base():
    r"""Complex example 3D structure dictionary of arrays."""
    base = {'vertices': np.array([[0, 0, 0, 0, 1, 1, 1, 1],
                                  [0, 0, 1, 1, 0, 0, 1, 1],
                                  [0, 1, 1, 0, 0, 1, 1, 0]], 'float32').T,
            'vertex_colors': np.array(
                [[255, 255, 255, 255, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 255, 255, 255, 255]], 'uint8').T,
            'faces': np.array([[0, 0, 7, 0, 1, 2, 3],
                               [1, 2, 6, 4, 5, 6, 7],
                               [2, 3, 5, 5, 6, 7, 4],
                               [-1, -1, 4, 1, 2, 3, 0]], 'int32').T,
            'edges': np.array([[0, 1, 2, 3, 2],
                               [1, 2, 3, 0, 0]], 'int32').T,
            'edge_colors': np.array([[255, 255, 255, 255, 0],
                                     [255, 255, 255, 255, 0],
                                     [255, 255, 255, 255, 0]], 'uint8').T,
            'mesh': [[0, 0, 0, 0, 0, 1, 0, 1, 1],
                     [0, 0, 0, 0, 1, 1, 0, 1, 0],
                     [1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0],
                     [0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1],
                     [0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1],
                     [0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0],
                     [0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0]]}
    bounds = (base['vertices'].min(axis=0),
              base['vertices'].max(axis=0))

    def wrapped_mesh_base(stack=1, obj=False):
        zero = 0
        if obj:
            zero = 1
        out = {'bounds': bounds}
        nvert = base['vertices'].shape[0]
        for k, v in base.items():
            if k in ['faces', 'edges']:
                arrs = []
                for i in range(stack):
                    ibase = copy.deepcopy(base[k])
                    ibase[ibase >= 0] += (i * nvert)
                    arrs.append(ibase)
                out[k] = np.vstack(arrs) + zero
            elif k in ['mesh']:
                out[k] = copy.deepcopy(base[k])
                for _ in range(1, stack):
                    out[k] += base[k]
            else:
                out[k] = np.vstack([base[k] for i in range(stack)])
        if obj:
            out.pop("edge_colors", False)
        return out

    return wrapped_mesh_base


# TODO: Allow material to be passed
@pytest.fixture(scope="session")
def mesh_dict():
    r"""Complex example Mesh dictionary of elements."""

    def wrapped_mesh_dict(base, with_colors=False, obj=False):
        ignore = -1
        if obj:
            ignore = 0
        out = {'vertices': [], 'edges': [], 'faces': []}
        # 'material': 'fake_material',
        for i in range(len(base['vertices'])):
            ivert = {}
            for j, k in enumerate('xyz'):
                ivert[k] = base['vertices'][i, j]
            if with_colors:
                for j, k in enumerate(['red', 'green', 'blue']):
                    ivert[k] = base['vertex_colors'][i, j]
            out['vertices'].append(ivert)
        for i in range(len(base['edges'])):
            iedge = {}
            if obj:
                iedge['vertex_index'] = [
                    x for x in base['edges'][i] if x != ignore]
            else:
                for j, k in enumerate(['vertex1', 'vertex2']):
                    iedge[k] = base['edges'][i, j]
                if with_colors:
                    for j, k in enumerate(['red', 'green', 'blue']):
                        iedge[k] = base['edge_colors'][i, j]
            out['edges'].append(iedge)
        for i in range(len(base['faces'])):
            out['faces'].append({'vertex_index': [
                x for x in base['faces'][i] if x != ignore]})
        for f in out['faces']:
            f['vertex_index'] = [np.int32(x) for x in f['vertex_index']]
        return out

    return wrapped_mesh_dict


@pytest.fixture(scope="session")
def mesh_array():
    r"""Complex example Mesh dictionary of element arrays."""

    def wrapped_mesh_array(base, with_colors=False):
        out = copy.deepcopy(base)
        if not with_colors:
            out.pop('vertex_colors')
            out.pop('edge_colors', None)
        return out

    return wrapped_mesh_array


@pytest.fixture(scope="session")
def mesh_args_factory(mesh_base, mesh_array, mesh_dict):
    r"""Factory to create arguments for testing Mesh construction."""
    aliases = {'vertices': 'vertex',
               'vertexes': 'vertex',
               'edges': 'edge',
               'faces': 'face'}
    result = {'bounds': mesh_base()['bounds']}

    def args_factory(args=["vertices", "faces", "edges"], kwargs=[],
                     as_array=False, as_list=False, with_colors=False,
                     stack=1, obj=False):
        zero = 0
        if obj:
            zero = 1
        base_ = mesh_base(stack=stack, obj=obj)
        mesh_array_ = mesh_array(base_, with_colors=with_colors)
        mesh_dict_ = mesh_dict(base_, with_colors=with_colors, obj=obj)
        colors = []
        if with_colors:
            colors = [aliases.get(k, k) + '_colors' for k in args + kwargs
                      if aliases.get(k, k) + '_colors' in mesh_array_]
        oresult = copy.deepcopy(result)
        oresult.update(base_)
        oresult.update({
            'arr': {aliases.get(k, k): copy.deepcopy(mesh_array_[k])
                    for k in args + kwargs + colors},
            'dict': {aliases.get(k, k): copy.deepcopy(mesh_dict_[k])
                     for k in args + kwargs}})
        if as_array or as_list:
            base = copy.deepcopy(oresult['arr'])
            kwargs = kwargs + colors
            if as_array and with_colors == 'in_array':
                if 'vertex' in base:
                    base['vertex'] = np.hstack([base['vertex'],
                                                base.pop('vertex_colors')])
                if 'edge' in base and not obj:
                    base['edge'] = np.hstack([base['edge'],
                                              base.pop('edge_colors')])
                for k in ['vertex_colors', 'edge_colors']:
                    if k in kwargs:
                        kwargs.remove(k)
        else:
            base = copy.deepcopy(oresult['dict'])
        if "faces" in args + kwargs:
            oresult['mesh'] = copy.deepcopy(base_['mesh'])
        else:
            oresult['mesh'] = []
        if as_list:
            oargs = [base[aliases.get(k, k)].tolist() for k in args]
            okwargs = {k: base[aliases.get(k, k)].tolist() for k in kwargs}
            if "faces" in kwargs:
                okwargs['faces'] = [[x for x in element if x != (zero - 1)]
                                    for element in okwargs['faces']]
                if obj:
                    okwargs['faces'][-1] = [
                        {"vertex_index": x} for x in
                        okwargs['faces'][-1]['vertex_index']]
            elif "faces" in args:
                idx_faces = args.index("faces")
                oargs[idx_faces] = [[x for x in element if x != (zero - 1)]
                                    for element in oargs[idx_faces]]
                if obj:
                    oargs[idx_faces][-1] = [
                        {"vertex_index": x} for x in
                        oargs[idx_faces][-1]]
        else:
            oargs = [base[aliases.get(k, k)] for k in args]
            okwargs = {k: base[aliases.get(k, k)] for k in kwargs}
        return tuple(oargs), okwargs, oresult

    return args_factory


@pytest.mark.parametrize('factory_options', [
    ({'args': []}),
    ({'args': ['vertices']}),
    ({'args': ['vertices'], 'with_colors': True}),
    ({'args': ['vertices', 'faces']}),
    ({'args': ['vertices', 'faces', 'edges']}),
    ({'args': ['vertices', 'faces', 'edges'], 'with_colors': True}),
    ({'args': ['vertices'], 'kwargs': ['edges']}),
    ({'args': ['vertices'], 'as_array': True}),
    ({'args': ['vertices'], 'as_array': True, 'with_colors': True}),
    ({'args': ['vertices', 'faces'], 'as_array': True}),
    ({'args': ['vertices', 'faces', 'edges'], 'as_array': True}),
    ({'args': ['vertices', 'faces', 'edges'],
      'as_array': True, 'with_colors': True}),
    ({'args': ['vertices', 'faces', 'edges'],
      'as_array': True, 'with_colors': 'in_array'}),
    ({'args': ['vertices'], 'kwargs': ['edges'], 'as_array': True}),
    ({'args': ['vertices'], 'as_list': True}),
    ({'args': ['vertices', 'faces'], 'as_list': True}),
    ({'args': ['vertices', 'faces', 'edges'], 'as_list': True}),
    ({'args': ['vertices'], 'kwargs': ['edges'], 'as_list': True}),
])
def test_Ply(mesh_args_factory, factory_options):
    args, kwargs, result = mesh_args_factory(**factory_options)
    x = geometry.Ply(*args, **kwargs)
    with pytest.raises(KeyError):
        x['invalid']
    assert 'invalid' not in x
    assert x.as_dict() == result['dict']
    if 'vertex' in result['dict']:
        assert x.items()
        assert 'vertex' in x
        np.testing.assert_array_equal(x.as_dict(as_array=True)['vertex'],
                                      result['arr']['vertex'])
        assert x.get_elements("vertex") == result['dict']['vertex']
        assert x.count_elements("vertices") == len(result['dict']['vertex'])
        assert x["vertex"] == result['dict']['vertex']
        np.testing.assert_array_equal(x.bounds[0], result['bounds'][0])
        np.testing.assert_array_equal(x.bounds[1], result['bounds'][1])
        assert(x.mesh == result['mesh'])
    y = geometry.Ply()
    for k, v in zip(['vertex', 'face', 'edge'], args):
        y.add_elements(k, v)
    for k, v in kwargs.items():
        y.add_elements(k, v)
    assert y.as_dict() == result['dict']
    if 'vertex' in result['dict']:
        np.testing.assert_array_equal(y.as_dict(as_array=True)['vertex'],
                                      result['arr']['vertex'])
        assert y.get_elements("vertex") == result['dict']['vertex']
        assert y.count_elements("vertices") == len(result['dict']['vertex'])
        assert y["vertex"] == result['dict']['vertex']
        np.testing.assert_array_equal(y.bounds[0], result['bounds'][0])
        np.testing.assert_array_equal(y.bounds[1], result['bounds'][1])
        assert(y.mesh == result['mesh'])
    assert x == y
    assert x.as_dict() == y.as_dict()
    assert x != 0
    assert x is not None
    x_arr = x.as_dict(as_array=True)
    y_arr = y.as_dict(as_array=True)
    assert list(x_arr.keys()) == list(y_arr.keys())
    for k in x_arr.keys():
        np.testing.assert_array_equal(x_arr[k], y_arr[k])
    if args:
        np.testing.assert_array_equal(x.bounds[0], y.bounds[0])
        np.testing.assert_array_equal(x.bounds[1], y.bounds[1])
    assert x.mesh == y.mesh
    if args:
        assert x != geometry.Ply()
        for k, v in zip(['vertex', 'face', 'edge'], args):
            kwargs[k] = v
    z = geometry.Ply.from_dict(kwargs)
    assert z == x
    assert z.as_dict() == y.as_dict()
    if args:
        np.testing.assert_array_equal(z.bounds[0], y.bounds[0])
        np.testing.assert_array_equal(z.bounds[1], y.bounds[1])
    assert z.mesh == y.mesh


@pytest.mark.parametrize('factory_options', [
    ({'args': []}),
    ({'args': ['vertices', 'faces', 'edges'], 'as_array': True}),
])
def test_Ply_serialize(dumps, loads, mesh_args_factory, factory_options):
    args, kwargs, _ = mesh_args_factory(**factory_options)
    value = geometry.Ply(*args, **kwargs)
    dumped = dumps(value)
    loaded = loads(dumped)
    assert loaded.as_dict() == value.as_dict()
    assert loaded == value


@pytest.mark.parametrize('factory_options', [
    ({'args': []}),
    ({'args': ['vertices', 'faces', 'edges'], 'as_array': True}),
])
def test_Ply_str(mesh_args_factory, factory_options):
    args, kwargs, _ = mesh_args_factory(**factory_options)
    value = geometry.Ply(*args, **kwargs)
    dumped = str(value)
    loaded = geometry.Ply(dumped)
    assert loaded.as_dict() == value.as_dict()
    assert loaded == value


@pytest.mark.parametrize('factory_options', [
    ({'args': ['vertices', 'faces', 'edges'], 'as_array': True}),
])
def test_Ply_append(mesh_args_factory, factory_options):
    args, kwargs, _ = mesh_args_factory(**factory_options)
    value1 = geometry.Ply(*args, **kwargs)
    value2 = geometry.Ply(*args, **kwargs)
    args2, kwargs2, _ = mesh_args_factory(stack=2, **factory_options)
    value3 = geometry.Ply(*args2, **kwargs2)
    value1.append(value2)
    assert value1.as_dict() == value3.as_dict()
    assert value1 == value3
    value0 = geometry.Ply(*args, **kwargs)
    value0.append(value0)
    assert value0.as_dict() == value3.as_dict()
    assert value0 == value3


@pytest.mark.parametrize('factory_options', [
    ({'args': [], 'kwargs': ['faces']}),
    ({'args': [], 'kwargs': ['edges']}),
])
def test_Ply_invalid(mesh_args_factory, factory_options):
    args, kwargs, _ = mesh_args_factory(**factory_options)
    with pytest.raises(geometry.GeometryError):
        geometry.Ply(*args, **kwargs)


@pytest.mark.parametrize('factory_options', [
    ({'args': ['vertices', 'faces', 'edges'], 'as_array': True}),
])
def test_Ply_color(mesh_args_factory, factory_options):
    args, kwargs, result = mesh_args_factory(**factory_options)
    value = geometry.Ply(*args, **kwargs)
    argsC, kwargsC, _ = mesh_args_factory(with_colors=True, **factory_options)
    valueC = geometry.Ply(*argsC, **kwargsC)
    np.testing.assert_array_equal(valueC.get_colors("vertex", as_array=True),
                                  result['vertex_colors'])
    value.add_colors("vertex", result['vertex_colors'])


@pytest.mark.parametrize('factory_options', [
    ({'args': []}),
    ({'args': ['vertices']}),
    ({'args': ['vertices'], 'with_colors': True}),
    ({'args': ['vertices', 'faces']}),
    ({'args': ['vertices', 'faces', 'edges']}),
    ({'args': ['vertices', 'faces', 'edges'], 'with_colors': True}),
    ({'args': ['vertices'], 'kwargs': ['edges']}),
    ({'args': ['vertices'], 'as_array': True}),
    ({'args': ['vertices'], 'as_array': True, 'with_colors': True}),
    ({'args': ['vertices', 'faces'], 'as_array': True}),
    ({'args': ['vertices', 'faces', 'edges'], 'as_array': True}),
    ({'args': ['vertices', 'faces', 'edges'],
      'as_array': True, 'with_colors': True}),
    ({'args': ['vertices', 'faces', 'edges'],
      'as_array': True, 'with_colors': 'in_array'}),
    ({'args': ['vertices'], 'kwargs': ['edges'], 'as_array': True}),
    ({'args': ['vertices'], 'as_list': True}),
    ({'args': ['vertices', 'faces'], 'as_list': True}),
    ({'args': ['vertices', 'faces', 'edges'], 'as_list': True}),
    ({'args': ['vertices'], 'kwargs': ['edges'], 'as_list': True}),
])
def test_Obj(mesh_args_factory, factory_options):
    args, kwargs, result = mesh_args_factory(obj=True, **factory_options)
    x = geometry.ObjWavefront(*args, **kwargs)
    with pytest.raises(KeyError):
        x['invalid']
    assert 'invalid' not in x
    assert x.as_dict() == result['dict']
    if 'vertex' in result['dict']:
        assert x.items()
        assert 'vertex' in x
        np.testing.assert_array_equal(x.as_dict(as_array=True)['vertex'],
                                      result['arr']['vertex'])
        assert x.get_elements("vertex") == result['dict']['vertex']
        assert x.count_elements("vertices") == len(result['dict']['vertex'])
        assert x["vertex"] == result['dict']['vertex']
        np.testing.assert_array_equal(x.bounds[0], result['bounds'][0])
        np.testing.assert_array_equal(x.bounds[1], result['bounds'][1])
        assert(x.mesh == result['mesh'])
    y = geometry.ObjWavefront()
    for k, v in zip(['vertex', 'face', 'edge'], args):
        y.add_elements(k, v)
    for k, v in kwargs.items():
        y.add_elements(k, v)
    assert y.as_dict() == result['dict']
    if 'vertex' in result['dict']:
        np.testing.assert_array_equal(y.as_dict(as_array=True)['vertex'],
                                      result['arr']['vertex'])
        assert y.get_elements("vertex") == result['dict']['vertex']
        assert y.count_elements("vertices") == len(result['dict']['vertex'])
        assert y["vertex"] == result['dict']['vertex']
        np.testing.assert_array_equal(y.bounds[0], result['bounds'][0])
        np.testing.assert_array_equal(y.bounds[1], result['bounds'][1])
        assert(y.mesh == result['mesh'])
    assert x == y
    assert x.as_dict() == y.as_dict()
    assert x != 0
    assert x is not None
    x_arr = x.as_dict(as_array=True)
    y_arr = y.as_dict(as_array=True)
    assert list(x_arr.keys()) == list(y_arr.keys())
    for k in x_arr.keys():
        np.testing.assert_array_equal(x_arr[k], y_arr[k])
    if args:
        np.testing.assert_array_equal(x.bounds[0], y.bounds[0])
        np.testing.assert_array_equal(x.bounds[1], y.bounds[1])
    assert x.mesh == y.mesh
    if args:
        assert x != geometry.ObjWavefront()
        for k, v in zip(['vertex', 'face', 'edge'], args):
            kwargs[k] = v
    z = geometry.ObjWavefront.from_dict(kwargs)
    assert z == x
    assert z.as_dict() == y.as_dict()
    if args:
        np.testing.assert_array_equal(z.bounds[0], y.bounds[0])
        np.testing.assert_array_equal(z.bounds[1], y.bounds[1])
    assert z.mesh == y.mesh


@pytest.mark.parametrize('factory_options', [
    ({'args': []}),
    ({'args': ['vertices', 'faces', 'edges'], 'as_array': True}),
])
def test_Obj_serialize(dumps, loads, mesh_args_factory, factory_options):
    args, kwargs, _ = mesh_args_factory(obj=True, **factory_options)
    value = geometry.ObjWavefront(*args, **kwargs)
    dumped = dumps(value)
    loaded = loads(dumped)
    assert loaded.as_dict() == value.as_dict()
    assert loaded == value


@pytest.mark.parametrize('factory_options', [
    ({'args': ['vertices', 'faces', 'edges'], 'as_array': True}),
])
def test_Obj_append(mesh_args_factory, factory_options):
    args, kwargs, _ = mesh_args_factory(obj=True, **factory_options)
    value1 = geometry.ObjWavefront(*args, **kwargs)
    value2 = geometry.ObjWavefront(*args, **kwargs)
    args2, kwargs2, _ = mesh_args_factory(obj=True, stack=2, **factory_options)
    value3 = geometry.ObjWavefront(*args2, **kwargs2)
    value1.append(value2)
    assert value1.as_dict() == value3.as_dict()
    assert value1.mesh == value3.mesh
    value0 = geometry.ObjWavefront(*args, **kwargs)
    value0.append(value0)
    assert value0.as_dict() == value3.as_dict()
    assert value0.mesh == value3.mesh


@pytest.mark.parametrize('factory_options', [
    ({'args': [], 'kwargs': ['faces']}),
    ({'args': [], 'kwargs': ['edges']}),
])
def test_Obj_invalid(mesh_args_factory, factory_options):
    args, kwargs, _ = mesh_args_factory(obj=True, **factory_options)
    with pytest.raises(geometry.GeometryError):
        geometry.ObjWavefront(*args, **kwargs)


@pytest.mark.parametrize('factory_options', [
    ({'args': ['vertices', 'faces', 'edges'], 'as_array': True}),
])
def test_Obj_color(mesh_args_factory, factory_options):
    args, kwargs, result = mesh_args_factory(obj=True, **factory_options)
    value = geometry.ObjWavefront(*args, **kwargs)
    argsC, kwargsC, _ = mesh_args_factory(obj=True, with_colors=True,
                                          **factory_options)
    valueC = geometry.ObjWavefront(*argsC, **kwargsC)
    np.testing.assert_array_equal(valueC.get_colors("vertex", as_array=True),
                                  result['vertex_colors'])
    value.add_colors("vertex", result['vertex_colors'])
