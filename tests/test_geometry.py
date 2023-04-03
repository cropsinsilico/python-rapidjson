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
                     [0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0]],
            'comments': ['Test comment 1', 'Test comment 2']}
    bounds = (base['vertices'].min(axis=0),
              base['vertices'].max(axis=0))

    def wrapped_mesh_base(stack=1, obj=False, types={},
                          only_triangles=False):
        zero = 0
        # if obj:
        #     zero = 1
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
                if only_triangles:
                    out[k] = out[k][:, :3]
            elif k in ['mesh']:
                out[k] = copy.deepcopy(base[k])
                for _ in range(1, stack):
                    out[k] += base[k]
            elif k in ['comments']:
                if obj:
                    out[k] = stack * base['comments']
                else:
                    # Ply preserve unique set of comments
                    out[k] = copy.deepcopy(base['comments'])
            else:
                out[k] = np.vstack([base[k] for i in range(stack)])
        if obj:
            out.pop("edge_colors", False)
        for k, v in types.items():
            if k in out:
                out[k] = out[k].astype(v)
        return out

    return wrapped_mesh_base


# TODO: Allow material to be passed
@pytest.fixture(scope="session")
def mesh_dict():
    r"""Complex example Mesh dictionary of elements."""

    def wrapped_mesh_dict(base, with_colors=False, obj=False):
        ignore = -1
        # if obj:
        #     ignore = 0
        out = {'vertices': [], 'edges': [], 'faces': [],
               'comments': base['comments']}
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
               'faces': 'face',
               'comments': 'comment'}
    result = {'bounds': mesh_base()['bounds']}

    def args_factory(args=["vertices", "faces", "edges", "comments"],
                     kwargs=[], as_array=False, as_list=False,
                     with_colors=False, stack=1, obj=False, types={},
                     only_triangles=False):
        zero = 0
        # if obj:
        #     zero = 1
        base_ = mesh_base(stack=stack, obj=obj, types=types,
                          only_triangles=only_triangles)
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


class TestPly:
    @pytest.fixture(scope="class")
    def cls(self):
        return geometry.Ply

    @pytest.fixture(scope="class")
    def isObj(self, cls):
        return (cls == geometry.ObjWavefront)

    @pytest.fixture(scope="class", params=[
        ({'args': []}),
        ({'args': ['vertices']}),
        ({'args': ['vertices'], 'with_colors': True}),
        ({'args': ['vertices', 'faces']}),
        ({'args': ['vertices', 'faces', 'edges']}),
        ({'args': ['vertices', 'faces', 'edges'], 'with_colors': True}),
        ({'args': ['vertices'], 'kwargs': ['edges', 'comments']}),
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
    def factory_options(self, request, cls, isObj):
        return dict(request.param, obj=isObj)

    @pytest.fixture(scope="class")
    def parameters(self, mesh_args_factory, factory_options):
        return mesh_args_factory(**factory_options)

    @pytest.fixture(scope="class")
    def args(self, parameters):
        return parameters[0]

    @pytest.fixture(scope="class")
    def kwargs(self, parameters):
        return parameters[1]

    @pytest.fixture(scope="class")
    def result(self, parameters):
        return parameters[2]

    @pytest.fixture(scope="class")
    def x(self, cls, args, kwargs):
        return cls(*args, **kwargs)

    @pytest.fixture(scope="class")
    def y(self, cls, args, kwargs):
        y = cls()
        for k, v in zip(['vertex', 'face', 'edge'], args):
            y.add_elements(k, v)
        for k, v in kwargs.items():
            y.add_elements(k, v)
        return cls(*args, **kwargs)

    @pytest.fixture(scope="class")
    def requires_vertex(self, result):
        if 'vertex' not in result['dict']:
            pytest.skip("requires vertex data")

    @pytest.fixture(scope="class")
    def without_colors(self, factory_options):
        if factory_options.get('with_colors', False):
            pytest.skip("requires no colors")

    @pytest.fixture(scope="class")
    def without_array(self, factory_options):
        if factory_options.get('as_array', False):
            pytest.skip("requires no as_array")

    def test_key_access(self, x, y, result):
        with pytest.raises(KeyError):
            x['invalid']
        assert 'invalid' not in x
        if 'vertex' in result['dict']:
            assert 'vertex' in x
            assert x["vertex"] == result['dict']['vertex']
            assert x.items()
            assert 'vertex' in y
            assert y["vertex"] == result['dict']['vertex']
            assert y.items()

    def test_equality(self, cls, x, y, args):
        assert x == y
        assert x != 0
        assert x is not None
        if args:
            assert x != cls()

    def test_as_dict(self, x, y, result):
        assert x.as_dict() == result['dict']
        assert y.as_dict() == result['dict']
        assert x.as_dict() == y.as_dict()

    def test_as_dict_array(self, x, y, result, requires_vertex):
        np.testing.assert_array_equal(x.as_dict(as_array=True)['vertex'],
                                      result['arr']['vertex'])
        np.testing.assert_array_equal(y.as_dict(as_array=True)['vertex'],
                                      result['arr']['vertex'])
        x_arr = x.as_dict(as_array=True)
        y_arr = y.as_dict(as_array=True)
        assert list(x_arr.keys()) == list(y_arr.keys())
        for k in x_arr.keys():
            np.testing.assert_array_equal(x_arr[k], y_arr[k])

    def test_from_dict(self, cls, x, y, args, kwargs):
        if not args:
            pytest.skip("requires args")
        dict_kwargs = copy.deepcopy(kwargs)
        for k, v in zip(['vertex', 'face', 'edge'], args):
            dict_kwargs[k] = v
        z = cls.from_dict(dict_kwargs)
        assert z.as_dict() == y.as_dict()
        assert z == x
        if args:
            np.testing.assert_array_equal(z.bounds[0], y.bounds[0])
            np.testing.assert_array_equal(z.bounds[1], y.bounds[1])
        assert z.mesh == y.mesh

    def test_bounds(self, x, y, args, result, requires_vertex):
        np.testing.assert_array_equal(x.bounds[0], result['bounds'][0])
        np.testing.assert_array_equal(x.bounds[1], result['bounds'][1])
        np.testing.assert_array_equal(y.bounds[0], result['bounds'][0])
        np.testing.assert_array_equal(y.bounds[1], result['bounds'][1])
        if args:
            np.testing.assert_array_equal(x.bounds[0], y.bounds[0])
            np.testing.assert_array_equal(x.bounds[1], y.bounds[1])

    def test_mesh(self, x, y, result, requires_vertex):
        assert x.mesh == result['mesh']
        assert y.mesh == result['mesh']
        assert x.mesh == y.mesh

    def test_elements(self, x, y, result, requires_vertex):
        assert x.get_elements("vertex") == result['dict']['vertex']
        assert x.count_elements("vertices") == len(result['dict']['vertex'])
        assert y.get_elements("vertex") == result['dict']['vertex']
        assert y.count_elements("vertices") == len(result['dict']['vertex'])

    def test_array(self, without_array, x,
                   cls, mesh_args_factory, factory_options):
        argsA, kwargsA, _ = mesh_args_factory(as_array=True, **factory_options)
        xA = cls(*argsA, **kwargsA)
        assert xA.as_dict() == x.as_dict()
        assert xA == x

    def test_serialize(self, x, dumps, loads, args, kwargs):
        dumped = dumps(x)
        loaded = loads(dumped)
        assert loaded.as_dict() == x.as_dict()
        assert loaded == x

    def test_str(self, cls, x):
        try:
            dumped = str(x)
            loaded = cls(dumped)
            assert loaded.as_dict() == x.as_dict()
            assert loaded == x
        except geometry.GeometryError:
            raise

    def test_append(self, cls, args, kwargs,
                    mesh_args_factory, factory_options):
        x1 = cls(*args, **kwargs)
        x2 = cls(*args, **kwargs)
        args2, kwargs2, _ = mesh_args_factory(stack=2, **factory_options)
        x3 = cls(*args2, **kwargs2)
        x1.append(x2)
        assert x1.as_dict() == x3.as_dict()
        if factory_options.get('obj', False):
            assert x1.mesh == x3.mesh
        else:
            assert x1 == x3
        x2.append(x2)
        assert x2.as_dict() == x3.as_dict()
        if factory_options.get('obj', False):
            assert x2.mesh == x3.mesh
        else:
            assert x2 == x3

    def test_merge(self, cls, args, kwargs,
                   mesh_args_factory, factory_options):
        x1 = cls(*args, **kwargs)
        x2 = cls(*args, **kwargs)
        args2, kwargs2, _ = mesh_args_factory(stack=2, **factory_options)
        x3 = cls(*args2, **kwargs2)
        args3, kwargs3, _ = mesh_args_factory(stack=3, **factory_options)
        x4 = cls(*args3, **kwargs3)
        # 1 as argument
        x_merge1 = x1.merge(x2)
        assert x_merge1.as_dict() == x3.as_dict()
        if factory_options.get('obj', False):
            assert x_merge1.mesh == x3.mesh
        else:
            assert x_merge1 == x3
        # 2 as arguments
        x_merge2 = x1.merge(x1, x2)
        assert x_merge2.as_dict() == x4.as_dict()
        if factory_options.get('obj', False):
            assert x_merge2.mesh == x4.mesh
        else:
            assert x_merge2 == x4
        # 2 as list
        x_merge3 = x1.merge([x1, x2])
        assert x_merge3.as_dict() == x4.as_dict()
        if factory_options.get('obj', False):
            assert x_merge3.mesh == x4.mesh
        else:
            assert x_merge3 == x4
        # merge no copy
        x1.merge(x2, no_copy=True)
        assert x1.as_dict() == x3.as_dict()
        if factory_options.get('obj', False):
            assert x1.mesh == x3.mesh
        else:
            assert x1 == x3

    @pytest.mark.parametrize('invalid_factory_options', [
        ({'args': [], 'kwargs': ['faces']}),
        ({'args': [], 'kwargs': ['edges']}),
    ])
    def test_invalid(self, cls, isObj, mesh_args_factory,
                     invalid_factory_options):
        args, kwargs, _ = mesh_args_factory(obj=isObj,
                                            **invalid_factory_options)
        with pytest.raises(geometry.GeometryError):
            cls(*args, **kwargs)

    def test_pickle(self, x):
        import pickle
        dumped = pickle.dumps(x)
        loaded = pickle.loads(dumped)
        assert loaded.as_dict() == x.as_dict()
        assert loaded == x

    def test_colors(self, without_colors, requires_vertex, cls, x, result,
                    mesh_args_factory, factory_options):
        argsC, kwargsC, _ = mesh_args_factory(with_colors=True,
                                              **factory_options)
        xC = cls(*argsC, **kwargsC)
        np.testing.assert_array_equal(xC.get_colors("vertex", as_array=True),
                                      result['vertex_colors'])
        x.add_colors("vertex", result['vertex_colors'])

    def test_trimesh(self, cls, mesh_args_factory, dumps, loads,
                     factory_options, requires_vertex):
        if 'edges' in (factory_options.get('args', [])
                       + factory_options.get('kwargs', [])):
            pytest.skip("Edges not supported by trimesh")
        try:
            import trimesh
            opts = copy.deepcopy(factory_options)
            opts.update(types={'vertices': np.float64},
                        with_colors=True, only_triangles=True)
            param = mesh_args_factory(**opts)
            x = cls(*param[0], **param[1])
            x_trimesh = x.as_trimesh()
            dumped = dumps(x_trimesh)
            loaded = loads(dumped)
            if factory_options.get('obj', False):
                loaded = cls(loaded)
            assert loaded == x
            y = cls.from_trimesh(x_trimesh)
            assert y == x
            del trimesh
        except ImportError:
            pytest.skip("Trimesh not installed")


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


class TestObj(TestPly):
    @pytest.fixture(scope="class")
    def cls(self):
        return geometry.ObjWavefront


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
