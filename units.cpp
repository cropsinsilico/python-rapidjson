// -*- coding: utf-8 -*-
// :Project:   python-rapidjson -- Python extension module
// :Author:    Meagan Lang <langmm.astro@gmail.com>
// :License:   BSD License
//

#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif

#include <Python.h>

#include "rapidjson/units.h"
#include "rapidjson/precision.h"
#include "rapidjson/rapidjson.h"
#include <numpy/arrayobject.h>
#include <numpy/ufuncobject.h>

using namespace rapidjson;
using namespace rapidjson::units;


static PyObject* units_error = NULL;

#define QUANTITY_ARRAY_OFFSET_BUFFER 256

//////////////////////////
// Forward declarations //
//////////////////////////

// Units
static void units_dealloc(PyObject* self);
static PyObject* units_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static PyObject* units_str(PyObject* self);
static PyObject* units_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* units_is_dimensionless(PyObject* self, PyObject* args);
static PyObject* units_richcompare(PyObject *self, PyObject *other, int op);
static PyObject* units_multiply(PyObject *a, PyObject *b);
static PyObject* units_divide(PyObject *a, PyObject *b);
static PyObject* units_power(PyObject *base, PyObject *exp, PyObject *mod);
static PyObject* units_multiply_inplace(PyObject *a, PyObject *b);
static PyObject* units_divide_inplace(PyObject *a, PyObject *b);
static PyObject* units_power_inplace(PyObject *base, PyObject *exp, PyObject *mod);

// Quantity
static void quantity_dealloc(PyObject* self);
static PyObject* quantity_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static PyObject* quantity_str(PyObject* self);
static PyObject* quantity_repr(PyObject* self);
static PyObject* quantity_units_get(PyObject* self, void* closure);
static int quantity_units_set(PyObject* self, PyObject* value, void* closure);
static PyObject* quantity_value_get(PyObject* type, void* closure);
static int quantity_value_set(PyObject* self, PyObject* value, void* closure);
static PyObject* quantity_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* quantity_is_dimensionless(PyObject* self, PyObject* args);
static PyObject* quantity_is_equivalent(PyObject* self, PyObject* args);
static PyObject* quantity_to(PyObject* self, PyObject* args);
static PyObject* quantity_richcompare(PyObject *self, PyObject *other, int op);
static PyObject* quantity_add(PyObject *a, PyObject *b);
static PyObject* quantity_subtract(PyObject *a, PyObject *b);
static PyObject* quantity_multiply(PyObject *a, PyObject *b);
static PyObject* quantity_divide(PyObject *a, PyObject *b);
static PyObject* quantity_modulo(PyObject *a, PyObject *b);
static PyObject* quantity_power(PyObject *base, PyObject *exp, PyObject *mod);
static PyObject* quantity_floor_divide(PyObject *a, PyObject *b);
static PyObject* quantity_add_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_subtract_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_multiply_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_divide_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_modulo_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_floor_divide_inplace(PyObject *a, PyObject *b);
static PyObject* quantity_power_inplace(PyObject *base, PyObject *exp, PyObject *mod);

// QuantityArray
static void quantity_array_dealloc(PyObject* self);
static PyObject* quantity_array_new(PyTypeObject* type, PyObject* args, PyObject* kwargs);
static PyObject* quantity_array_str(PyObject* self);
static PyObject* quantity_array_repr(PyObject* self);
static PyObject* quantity_array_get_converted_value(PyObject* self, PyObject* units);
static PyObject* quantity_array_units_get(PyObject* self, void* closure);
static int quantity_array_units_set(PyObject* self, PyObject* value, void* closure);
static PyObject* quantity_array_value_get(PyObject* type, void* closure);
static PyObject* quantity_array_value_get_copy(PyObject* type, void* closure);
static int quantity_array_value_set(PyObject* self, PyObject* value, void* closure);
static PyObject* quantity_array_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* quantity_array_is_dimensionless(PyObject* self, PyObject* args);
static PyObject* quantity_array_is_equivalent(PyObject* self, PyObject* args);
static PyObject* quantity_array_to(PyObject* self, PyObject* args);
static PyObject* quantity_array__array_ufunc__(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* quantity_array__array_finalize__(PyObject* self, PyObject* args);
static PyObject* quantity_array__array_wrap__(PyObject* self, PyObject* args);
static PyObject* quantity_array__array_function__(PyObject* self, PyObject* args, PyObject* kwargs);
static PyObject* quantity_array_subscript(PyObject* self, PyObject* key);
static int quantity_array_ass_subscript(PyObject* self, PyObject* key, PyObject* val);


///////////////
// Utilities //
///////////////

enum BinaryOps {
    binaryOpAdd,
    binaryOpSubtract,
    binaryOpMultiply,
    binaryOpDivide,
    binaryOpModulo,
    binaryOpFloorDivide
};


static PyObject* _get_units(PyObject* x,
			    bool dont_allow_empty = false,
			    bool force_copy = false);
static int _has_units(PyObject* x);
static PyObject* _convert_units(PyObject* x, PyObject* units,
				bool stripUnits=false);
static int _compare_units(PyObject* x0, PyObject* x1,
			  bool allowCompat = false,
			  bool dimensionlessCompat = false);
static int _compare_units_tuple(PyObject* x, bool allowCompat = false,
				bool dimensionlessCompat = false,
				PyObject** out_units=NULL);

#define SET_ERROR(errno, msg, ret)			\
    {							\
	PyObject* error = Py_BuildValue("s", msg);	\
	PyErr_SetObject(errno, error);			\
	Py_XDECREF(error);				\
	return ret;					\
    }

#define CALL_BASE_METHOD_NOARGS(method, out)				\
    {									\
	PyObject* base_cls = (PyObject*)(self->ob_type->tp_base);	\
	PyObject* base_fnc = PyObject_GetAttrString(base_cls, #method);	\
	if (base_fnc) {							\
	    out = PyObject_CallFunctionObjArgs(base_fnc, self, NULL);	\
	    Py_DECREF(base_fnc);					\
	}								\
    }

#define CALL_BASE_METHOD(method, out, ...)				\
    {									\
	PyObject* base_cls = (PyObject*)(self->ob_type->tp_base);	\
	PyObject* base_fnc = PyObject_GetAttrString(base_cls, #method);	\
	if (base_fnc) {							\
	    out = PyObject_CallFunctionObjArgs(base_fnc, self, __VA_ARGS__, NULL); \
	    Py_DECREF(base_fnc);					\
	}								\
    }

#define CALL_BASE_METHOD_ARGS_KWARGS(method, out, args, kwargs)		\
    {									\
	PyObject* base_cls = (PyObject*)(self->ob_type->tp_base);	\
	PyObject* base_fnc = PyObject_GetAttrString(base_cls, #method);	\
	if (base_fnc) {							\
	    PyObject* new_args = PyTuple_New(PyTuple_Size(args) + 1);	\
	    if (new_args) {						\
		Py_INCREF(self);					\
		PyTuple_SetItem(new_args, 0, self);			\
		bool failure = false;					\
		for (Py_ssize_t i = 0; i < PyTuple_Size(args); i++) {	\
		    PyObject* item = PyTuple_GetItem(args, i);		\
		    if (item == NULL) {					\
			failure = true;					\
			break;						\
		    }							\
		    Py_INCREF(item);					\
		    PyTuple_SetItem(new_args, i + 1, item);		\
		}							\
		if (!failure) {						\
		    out = PyObject_Call(base_fnc, new_args, kwargs);	\
		}							\
		Py_DECREF(new_args);					\
	    }								\
	    Py_DECREF(base_fnc);					\
	}								\
    }

///////////
// Units //
///////////


typedef struct {
    PyObject_HEAD
    Units *units;
} UnitsObject;


PyDoc_STRVAR(units_doc,
             "Units(expression)\n"
             "\n"
             "Create and return a new Units instance from the given"
             " `expression` string.");


static PyMethodDef units_methods[] = {
    {"is_compatible", (PyCFunction) units_is_compatible, METH_VARARGS,
     "Check if a set of units are compatible with another set."},
    {"is_dimensionless", (PyCFunction) units_is_dimensionless, METH_NOARGS,
     "Check if the units are dimensionless."},
    {NULL}  /* Sentinel */
};


static PyNumberMethods units_number_methods = {
    0,                              /* nb_add */
    0,                              /* nb_subtract */
    units_multiply,                 /* nb_multiply */
    0,                              /* nb_remainder */
    0,                              /* nb_divmod */
    units_power,                    /* nb_power */
    0,                              /* nb_negative */
    0,                              /* nb_positive */
    0,                              /* nb_absolute */
    0,                              /* nb_bool */
    0,                              /* nb_invert */
    0,                              /* nb_lshift */
    0,                              /* nb_rshift */
    0,                              /* nb_and */
    0,                              /* nb_xor */
    0,                              /* nb_or */
    0,                              /* nb_int */
    0,                              /* nb_reserved */
    0,                              /* nb_float */
    //
    0,                              /* nb_inplace_add */
    0,                              /* nb_inplace_subtract */
    units_multiply_inplace,         /* nb_inplace_multiply */
    0,                              /* nb_inplace_remainder */
    units_power_inplace,            /* nb_inplace_power */
    0,                              /* nb_inplace_lshift */
    0,                              /* nb_inplace_rshift */
    0,                              /* nb_inplace_and */
    0,                              /* nb_inplace_xor */
    0,                              /* nb_inplace_or */
    //
    0,                              /* nb_floor_divide */
    units_divide,                   /* nb_true_divide */
    0,                              /* nb_inplace_floor_divide */
    units_divide_inplace,           /* nb_inplace_true_divide */
    //
    0,                              /* nb_index */
    //
    0,                              /* nb_matrix_multiply */
    0,                              /* nb_inplace_matrix_multiply */
};


static PyTypeObject Units_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.Units",              /* tp_name */
    sizeof(UnitsObject),            /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor) units_dealloc,     /* tp_dealloc */
    0,                              /* tp_print */
    0,                              /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_compare */
    0,                              /* tp_repr */
    &units_number_methods,          /* tp_as_number */
    0,                              /* tp_as_sequence */
    0,                              /* tp_as_mapping */
    0,                              /* tp_hash */
    0,                              /* tp_call */
    units_str,                      /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,             /* tp_flags */
    units_doc,                      /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    units_richcompare,              /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    0,                              /* tp_iter */
    0,                              /* tp_iternext */
    units_methods,                  /* tp_methods */
    0,                              /* tp_members */
    0,                              /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    0,                              /* tp_init */
    0,                              /* tp_alloc */
    units_new,                      /* tp_new */
    PyObject_Del,                   /* tp_free */
};


static PyObject*
get_empty_units(PyObject* units = NULL) {
    PyObject* out = NULL;
    PyObject* units_args = NULL;
    if (units == NULL) {
	units = PyUnicode_FromString("");
	if (units == NULL) {
	    return NULL;
	}
	units_args = PyTuple_Pack(1, units);
	Py_DECREF(units);
    } else {
	units_args = PyTuple_Pack(1, units);
    }
    if (units_args == NULL) {
	return NULL;
    }
    out = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
    Py_DECREF(units_args);
    return out;
}

static UnitsObject* units_coerce(PyObject* x) {
    PyObject* out = NULL;
    if (PyObject_IsInstance(x, (PyObject*)&Units_Type)) {
	Py_INCREF(x);
	return (UnitsObject*)x;
    }
    PyObject* args = PyTuple_Pack(1, x);
    if (args == NULL) return NULL;
    out = PyObject_Call((PyObject*)&Units_Type, args, NULL);
    Py_DECREF(args);
    return (UnitsObject*)out;
}


static void units_dealloc(PyObject* self)
{
    UnitsObject* s = (UnitsObject*) self;
    delete s->units;
    Py_TYPE(self)->tp_free(self);
}


static PyObject* units_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    PyObject* exprObject;

    if (!PyArg_ParseTuple(args, "O:Units", &exprObject))
	return NULL;

    const char* exprStr = 0;
    const UnitsObject* other;

    if (PyBytes_Check(exprObject)) {
        exprStr = PyBytes_AsString(exprObject);
        if (exprStr == NULL)
            return NULL;
    } else if (PyUnicode_Check(exprObject)) {
        exprStr = PyUnicode_AsUTF8(exprObject);
        if (exprStr == NULL)
            return NULL;
    } else if (PyObject_IsInstance(exprObject, (PyObject*)&Units_Type)) {
	other = (UnitsObject*)exprObject;
    } else {
        PyErr_SetString(PyExc_TypeError, "Expected string or UTF-8 encoded bytes");
        return NULL;
    }

    UnitsObject* v = (UnitsObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;

    if (exprStr)
	v->units = new Units(exprStr);
    else
	v->units = new Units(*other->units);
    if (v->units->is_empty()) {
	PyObject* error = Py_BuildValue("s", "Failed to parse units.");
	PyErr_SetObject(units_error, error);
	Py_XDECREF(error);
	return NULL;
    }

    return (PyObject*) v;
}


static PyObject* units_str(PyObject* self) {
    UnitsObject* v = (UnitsObject*) self;
    std::string s = v->units->str();
    return PyUnicode_FromString(s.c_str());
}

static PyObject* units_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* otherObject;
    const UnitsObject* other;
    
    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;

    if (PyObject_IsInstance(otherObject, (PyObject*)&Units_Type)) {
	other = (UnitsObject*)otherObject;
	Py_INCREF(otherObject);
    } else {
	other = (UnitsObject*)PyObject_Call((PyObject*)&Units_Type, args, NULL);
    }
    if (other == NULL)
        return NULL;
    
    UnitsObject* v = (UnitsObject*) self;
    bool result = v->units->is_compatible(*other->units);
    Py_DECREF(other);
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
    
}


static PyObject* units_is_dimensionless(PyObject* self, PyObject* args) {
    UnitsObject* v = (UnitsObject*) self;
    bool result = v->units->is_dimensionless();
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
}


static PyObject* units_richcompare(PyObject *self, PyObject *other, int op) {
    UnitsObject* vself = (UnitsObject*) self;
    UnitsObject* vsolf = (UnitsObject*) other;
    switch (op) {
    case (Py_EQ): {
	if (*(vself->units) == *(vsolf->units)) {
	    Py_INCREF(Py_True);
	    return Py_True;
	}
	Py_INCREF(Py_False);
	return Py_False;
    }
    case (Py_NE): {
	if (*(vself->units) != *(vsolf->units)) {
	    Py_INCREF(Py_True);
	    return Py_True;
	}
	Py_INCREF(Py_False);
	return Py_False;
    }
    default:
	Py_INCREF(Py_NotImplemented);
	return Py_NotImplemented;
    }
}

static PyObject* do_units_op(PyObject* a, PyObject *b, BinaryOps op,
			     bool inplace=false) {
    if (!(PyObject_IsInstance(a, (PyObject*)&Units_Type) &&
	  PyObject_IsInstance(b, (PyObject*)&Units_Type))) {
	PyErr_SetString(PyExc_TypeError, "This operation is only valid for two rapidjson.units.Units instances.");
	return NULL;
    }
    PyObject* out;
    if (inplace) {
	out = a;
    } else {
	out = (PyObject*) Units_Type.tp_alloc(&Units_Type, 0);
	((UnitsObject*)out)->units = new Units();
    }
    switch (op) {
    case (binaryOpMultiply): {
	if (inplace)
	    *(((UnitsObject*)out)->units) *= *(((UnitsObject*)b)->units);
	else
	    *(((UnitsObject*)out)->units) = (*(((UnitsObject*)a)->units) *
					     *(((UnitsObject*)b)->units));
	break;
    }
    case (binaryOpDivide): {
	if (inplace)
	    *(((UnitsObject*)out)->units) /= *(((UnitsObject*)b)->units);
	else
	    *(((UnitsObject*)out)->units) = (*(((UnitsObject*)a)->units) /
					     *(((UnitsObject*)b)->units));
	break;
    }
    default: {
	if (!inplace) {
	    Py_DECREF(out);
	}
	PyErr_SetString(PyExc_NotImplementedError, "rapidjson.units.Units do not support this operation.");
	return NULL;
    }
    }
    return out;
}

static PyObject* do_units_pow(PyObject* a, PyObject *b, PyObject* mod,
			      bool inplace=false) {
    if (PyObject_IsInstance(b, (PyObject*)&Units_Type)) {
	PyErr_SetString(PyExc_TypeError, "Cannot raise to a rapidjson.units.Units power");
	return NULL;
    }
    if (!PyObject_IsInstance(a, (PyObject*)&Units_Type)) {
	PyErr_SetString(PyExc_TypeError, "Base doesn't have units, why is this being called?");
	return NULL;
    }
    if (mod != Py_None) {
	PyErr_SetString(PyExc_NotImplementedError, "'mod' power argument not supported for rapidjson.units.Units instances.");
	return NULL;
    }
    PyObject* exp = PyNumber_Float(b);
    if (exp == NULL) return NULL;
    double expV = PyFloat_AsDouble(exp);
    Py_DECREF(exp);
    PyObject* out;
    if (inplace) {
	out = a;
	((UnitsObject*)out)->units->inplace_pow(expV);
    } else {
	out = (PyObject*) Units_Type.tp_alloc(&Units_Type, 0);
	((UnitsObject*)out)->units = new Units();
	*(((UnitsObject*)out)->units) = ((UnitsObject*)a)->units->pow(expV);
    }
    return out;
}

static PyObject* units_multiply(PyObject *a, PyObject *b)
{ return do_units_op(a, b, binaryOpMultiply); }
static PyObject* units_divide(PyObject *a, PyObject *b)
{ return do_units_op(a, b, binaryOpDivide); }
static PyObject* units_power(PyObject *base, PyObject *exp, PyObject *mod)
{ return do_units_pow(base, exp, mod); }
static PyObject* units_multiply_inplace(PyObject *a, PyObject *b)
{ return do_units_op(a, b, binaryOpMultiply, true); }
static PyObject* units_divide_inplace(PyObject *a, PyObject *b)
{ return do_units_op(a, b, binaryOpDivide, true); }
static PyObject* units_power_inplace(PyObject *base, PyObject *exp, PyObject *mod)
{ return do_units_pow(base, exp, mod, true); }


//////////////
// Quantity //
//////////////

enum QuantitySubType {
    kFloatQuantitySubType,
    kDoubleQuantitySubType,
    kUint8QuantitySubType,
    kUint16QuantitySubType,
    kUint32QuantitySubType,
    kUint64QuantitySubType,
    kInt8QuantitySubType,
    kInt16QuantitySubType,
    kInt32QuantitySubType,
    kInt64QuantitySubType,
    kComplexFloatQuantitySubType,
    kComplexDoubleQuantitySubType
};


template<typename T>
PyObject* PyObject_FromScalarYgg(T& v) {
    return NULL;
}
#define NUMPY_FROMSCALARYGG(npT, T)				\
    template<>							\
    PyObject* PyObject_FromScalarYgg(T& v) {			\
	PyArray_Descr* desc = PyArray_DescrNewFromType(npT);	\
	if (desc == NULL)					\
	    return NULL;					\
	return PyArray_Scalar((void*)(&v), desc, NULL);		\
    }
// template<>
// PyObject* PyObject_FromScalarYgg(float& v) {
//     return PyFloat_FromDouble((double)v);
// }
// template<>
// PyObject* PyObject_FromScalarYgg(double& v) {
//     return PyFloat_FromDouble(v);
// }
NUMPY_FROMSCALARYGG(NPY_INT8, int8_t)
NUMPY_FROMSCALARYGG(NPY_INT16, int16_t)
NUMPY_FROMSCALARYGG(NPY_INT32, int32_t)
NUMPY_FROMSCALARYGG(NPY_INT64, int64_t)
NUMPY_FROMSCALARYGG(NPY_UINT8, uint8_t)
NUMPY_FROMSCALARYGG(NPY_UINT16, uint16_t)
NUMPY_FROMSCALARYGG(NPY_UINT32, uint32_t)
NUMPY_FROMSCALARYGG(NPY_UINT64, uint64_t)
NUMPY_FROMSCALARYGG(NPY_FLOAT32, float)
NUMPY_FROMSCALARYGG(NPY_FLOAT64, double)
NUMPY_FROMSCALARYGG(NPY_COMPLEX64, std::complex<float>)
NUMPY_FROMSCALARYGG(NPY_COMPLEX128, std::complex<double>)

#undef NUMPY_FROMSCALARYGG

#define NUMPY_GETSCALARYGG_BODY(pyObj, cObj, npT, T, args)	\
    if (PyArray_CheckScalar(pyObj)) {				\
	PyArray_Descr* desc = PyArray_DescrFromScalar(pyObj);	\
	if (desc->type_num == npT) {				\
	    cObj = new T args;					\
	    PyArray_ScalarAsCtype(pyObj, cObj);			\
	}							\
    }
#define NUMPY_GETSCALARYGG(npT, T, subT, args)				\
    template<>								\
    T* PyObject_GetScalarYgg<T>(PyObject* v, QuantitySubType& subtype) { \
	subtype = subT;							\
	T* out = NULL;							\
	NUMPY_GETSCALARYGG_BODY(v, out, npT, T, args)			\
	return out;							\
    }

template<typename T>
T* PyObject_GetScalarYgg(PyObject*, QuantitySubType&) {
    return NULL;
}
NUMPY_GETSCALARYGG(NPY_FLOAT32, float, kFloatQuantitySubType, (0.0))
template<>
double* PyObject_GetScalarYgg<double>(PyObject* v, QuantitySubType& subtype) {
    subtype = kDoubleQuantitySubType;
    if (PyFloat_AsDouble(v)) {
	double d = PyFloat_AsDouble(v);
	if (d == -1.0 && PyErr_Occurred())
	    return NULL;
	return new double(d);
    }
    double *out = NULL;
    NUMPY_GETSCALARYGG_BODY(v, out, NPY_FLOAT64, double, (0.0))
    return out;
}
NUMPY_GETSCALARYGG(NPY_INT8, int8_t, kInt8QuantitySubType, (0))
NUMPY_GETSCALARYGG(NPY_INT16, int16_t, kInt16QuantitySubType, (0))
#define _PyLong_GetScalarYgg(T)						\
    if ((sizeof(T) == sizeof(long long)) && PyLong_Check(v)) {		\
        int overflow;							\
	long long i = PyLong_AsLongLongAndOverflow(v, &overflow);	\
	if (i == -1 && PyErr_Occurred())				\
	    return NULL;						\
	if (overflow == 0) {						\
	    return new T(i);						\
	} else {							\
	    unsigned long long ui = PyLong_AsUnsignedLongLong(v);	\
	    if (PyErr_Occurred())					\
		return NULL;						\
	    return new T(ui);						\
	}								\
    }
template<>
int32_t* PyObject_GetScalarYgg<int32_t>(PyObject* v, QuantitySubType& subtype) {
    subtype = kInt32QuantitySubType;
    _PyLong_GetScalarYgg(int32_t);
    int32_t *out = NULL;
    NUMPY_GETSCALARYGG_BODY(v, out, NPY_INT32, int32_t, (0))
    return out;
}
template<>
int64_t* PyObject_GetScalarYgg<int64_t>(PyObject* v, QuantitySubType& subtype) {
    subtype = kInt64QuantitySubType;
    _PyLong_GetScalarYgg(int64_t);
    int64_t *out = NULL;
    NUMPY_GETSCALARYGG_BODY(v, out, NPY_INT64, int64_t, (0))
    return out;
}
NUMPY_GETSCALARYGG(NPY_UINT8, uint8_t, kUint8QuantitySubType, (0))
NUMPY_GETSCALARYGG(NPY_UINT16, uint16_t, kUint16QuantitySubType, (0))
NUMPY_GETSCALARYGG(NPY_UINT32, uint32_t, kUint32QuantitySubType, (0))
NUMPY_GETSCALARYGG(NPY_UINT64, uint64_t, kUint64QuantitySubType, (0))
NUMPY_GETSCALARYGG(NPY_COMPLEX64, std::complex<float>, kComplexFloatQuantitySubType, (0, 0))
NUMPY_GETSCALARYGG(NPY_COMPLEX128, std::complex<double>, kComplexDoubleQuantitySubType, (0, 0))

#undef NUMPY_GETSCALARYGG
#undef NUMPY_GETSCALARYGG_BODY


#define CASE_QX_SUBTYPE(cls, var, lhs, rhs, value, type)		\
    case (value): { lhs ((cls<type>*) var->quantity) rhs; break; }

#define SWITCH_QX_SUBTYPE(cls, var, lhs, rhs)				\
    switch(var->subtype) {						\
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kFloatQuantitySubType, float)	\
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kDoubleQuantitySubType, double)  \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kUint8QuantitySubType, uint8_t)  \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kUint16QuantitySubType, uint16_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kUint32QuantitySubType, uint32_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kUint64QuantitySubType, uint64_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kInt8QuantitySubType, int8_t)  \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kInt16QuantitySubType, int16_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kInt32QuantitySubType, int32_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kInt64QuantitySubType, int64_t) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kComplexFloatQuantitySubType, std::complex<float>) \
    CASE_QX_SUBTYPE(cls, var, lhs, rhs, kComplexDoubleQuantitySubType, std::complex<double>) \
    }

#define CASE_QX_SUBTYPE_CALL(cls, var, lhs, value, type, ...)	\
    case (value): { lhs (((cls<type>*) var->quantity), __VA_ARGS__); break; }

#define SWITCH_QX_SUBTYPE_CALL(cls, var, lhs, ...)		\
    switch(var->subtype) {						\
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kFloatQuantitySubType, float, __VA_ARGS__)	\
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kDoubleQuantitySubType, double, __VA_ARGS__)  \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kUint8QuantitySubType, uint8_t, __VA_ARGS__)  \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kUint16QuantitySubType, uint16_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kUint32QuantitySubType, uint32_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kUint64QuantitySubType, uint64_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kInt8QuantitySubType, int8_t, __VA_ARGS__)  \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kInt16QuantitySubType, int16_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kInt32QuantitySubType, int32_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kInt64QuantitySubType, int64_t, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kComplexFloatQuantitySubType, std::complex<float>, __VA_ARGS__) \
    CASE_QX_SUBTYPE_CALL(cls, var, lhs, kComplexDoubleQuantitySubType, std::complex<double>, __VA_ARGS__) \
    }

#define SWITCH_QUANTITY_SUBTYPE(var, lhs, rhs)	\
    SWITCH_QX_SUBTYPE(Quantity, var, lhs, rhs)
#define SWITCH_QUANTITY_SUBTYPE_CALL(var, lhs, ...)	\
    SWITCH_QX_SUBTYPE_CALL(Quantity, var, lhs, __VA_ARGS__)

#define EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, T) \
    if (T* tmp = tempMethod<T>tempArgs) {				\
	method<T> args;							\
    }

#define EXTRACT_PYTHON_QX(tmp, tempMethod, tempArgs, method, args, error) \
    EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, float)	\
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, double) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, int8_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, int16_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, int32_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, int64_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, uint8_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, uint16_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, uint32_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, uint64_t) \
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, std::complex<float>)	\
    else EXTRACT_PYTHON_QX_TYPE(tmp, tempMethod, tempArgs, method, args, std::complex<double>) \
    else { error; }
    
#define EXTRACT_PYTHON_VALUE(var, pyObj, tmp, method, args, error)	\
    EXTRACT_PYTHON_QX(tmp, PyObject_GetScalarYgg, (pyObj, var), method, args, error)



typedef struct {
    PyObject_HEAD
    QuantitySubType subtype;
    void *quantity;
} QuantityObject;


PyDoc_STRVAR(quantity_doc,
             "Quantity(value, units)\n"
             "\n"
             "Create and return a new Quantity instance from the given"
             " `value` and `units` string or Units instance.");


static PyMethodDef quantity_methods[] = {
    {"is_compatible", (PyCFunction) quantity_is_compatible, METH_VARARGS,
     "Check if a set of units or quantity is compatible with another set."},
    {"is_dimensionless", (PyCFunction) quantity_is_dimensionless, METH_NOARGS,
     "Check if the quantity has dimensionless units."},
    {"to", (PyCFunction) quantity_to, METH_VARARGS,
     "Convert the quantity to another set of units."},
    {"is_equivalent", (PyCFunction) quantity_is_equivalent, METH_VARARGS,
     "Check if another Quantity is equivalent when convert to the same units/"},
    {NULL}  /* Sentinel */
};


static PyGetSetDef quantity_properties[] = {
    {"units", quantity_units_get, quantity_units_set,
     "The rapidjson.Units units for the quantity.", NULL},
    {"value", quantity_value_get, quantity_value_set,
     "The quantity's value (in the current unit system).", NULL},
    {NULL}
};


static PyNumberMethods quantity_number_methods = {
    quantity_add,                   /* nb_add */
    quantity_subtract,              /* nb_subtract */
    quantity_multiply,              /* nb_multiply */
    quantity_modulo,                /* nb_remainder */
    0,                              /* nb_divmod */
    quantity_power,                 /* nb_power */
    0,                              /* nb_negative */
    0,                              /* nb_positive */
    0,                              /* nb_absolute */
    0,                              /* nb_bool */
    0,                              /* nb_invert */
    0,                              /* nb_lshift */
    0,                              /* nb_rshift */
    0,                              /* nb_and */
    0,                              /* nb_xor */
    0,                              /* nb_or */
    0,                              /* nb_int */
    0,                              /* nb_reserved */
    0,                              /* nb_float */
    //
    quantity_add_inplace,           /* nb_inplace_add */
    quantity_subtract_inplace,      /* nb_inplace_subtract */
    quantity_multiply_inplace,      /* nb_inplace_multiply */
    quantity_modulo_inplace,        /* nb_inplace_remainder */
    quantity_power_inplace,         /* nb_inplace_power */
    0,                              /* nb_inplace_lshift */
    0,                              /* nb_inplace_rshift */
    0,                              /* nb_inplace_and */
    0,                              /* nb_inplace_xor */
    0,                              /* nb_inplace_or */
    //
    quantity_floor_divide,          /* nb_floor_divide */
    quantity_divide,                /* nb_true_divide */
    quantity_floor_divide_inplace,  /* nb_inplace_floor_divide */
    quantity_divide_inplace,        /* nb_inplace_true_divide */
    //
    0,                              /* nb_index */
    //
    0,                              /* nb_matrix_multiply */
    0,                              /* nb_inplace_matrix_multiply */
};


static PyTypeObject Quantity_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.Quantity",           /* tp_name */
    sizeof(QuantityObject),         /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor) quantity_dealloc,  /* tp_dealloc */
    0,                              /* tp_print */
    0,                              /* tp_getattr */
    0,                              /* tp_setattr */
    0,                              /* tp_compare */
    quantity_repr,                  /* tp_repr */
    &quantity_number_methods,       /* tp_as_number */
    0,                              /* tp_as_sequence */
    0,                              /* tp_as_mapping */
    0,                              /* tp_hash */
    0,                              /* tp_call */
    quantity_str,                   /* tp_str */
    0,                              /* tp_getattro */
    0,                              /* tp_setattro */
    0,                              /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,             /* tp_flags */
    quantity_doc,                   /* tp_doc */
    0,                              /* tp_traverse */
    0,                              /* tp_clear */
    quantity_richcompare,           /* tp_richcompare */
    0,                              /* tp_weaklistoffset */
    0,                              /* tp_iter */
    0,                              /* tp_iternext */
    quantity_methods,               /* tp_methods */
    0,                              /* tp_members */
    quantity_properties,            /* tp_getset */
    0,                              /* tp_base */
    0,                              /* tp_dict */
    0,                              /* tp_descr_get */
    0,                              /* tp_descr_set */
    0,                              /* tp_dictoffset */
    0,                              /* tp_init */
    0,                              /* tp_alloc */
    quantity_new,                   /* tp_new */
    PyObject_Del,                   /* tp_free */
};


static void quantity_dealloc(PyObject* self)
{
    QuantityObject* s = (QuantityObject*) self;
    SWITCH_QUANTITY_SUBTYPE(s, delete, );
    Py_TYPE(self)->tp_free(self);
}


template<typename T>
void assign_scalar_(QuantityObject* v, T* val, Units* units=nullptr) {
    if (units)
	v->quantity = (void*)(new Quantity<T>(*val, *units));
    else
	v->quantity = (void*)(new Quantity<T>(*val));
    delete val;
}


static PyObject* quantity_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    PyObject* valueObject;
    PyObject* unitsObject = NULL;
    static char const* kwlist[] = {
	"value",
	"units",
	NULL
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|O:Quantity",
				     (char**) kwlist,
				     &valueObject, &unitsObject))
	return NULL;

    QuantityObject* v = (QuantityObject*) type->tp_alloc(type, 0);
    if (v == NULL)
        return NULL;

    if (valueObject == NULL) {
	PyErr_SetString(PyExc_TypeError, "Invalid value");
	return NULL;
    }

    if (PyObject_IsInstance(valueObject, (PyObject*)&Quantity_Type)) {
	QuantityObject* vother = (QuantityObject*)valueObject;
	v->subtype = vother->subtype;
	SWITCH_QUANTITY_SUBTYPE(vother, v->quantity = , ->copy_void());
    } else if (unitsObject != NULL) {
	PyObject* units_args = PyTuple_Pack(1, unitsObject);
	unitsObject = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
	Py_DECREF(units_args);
	if (unitsObject == NULL)
	    return NULL;
	EXTRACT_PYTHON_VALUE(v->subtype, valueObject, val, assign_scalar_,
			     (v, val, ((UnitsObject*)unitsObject)->units),
			     { PyErr_SetString(PyExc_TypeError, "Expected scalar integer, floating point, or complex value"); return NULL; })
    } else {
	EXTRACT_PYTHON_VALUE(v->subtype, valueObject, val, assign_scalar_,
			     (v, val),
			     { PyErr_SetString(PyExc_TypeError, "Expected scalar integer, floating point, or complex value"); return NULL; })
    }
	
    return (PyObject*) v;
}


static PyObject* quantity_str(PyObject* self) {
    QuantityObject* v = (QuantityObject*) self;
    std::string s;
    SWITCH_QUANTITY_SUBTYPE(v, s = , ->str());
    return PyUnicode_FromString(s.c_str());
}


static PyObject* quantity_repr(PyObject* self) {
    QuantityObject* v = (QuantityObject*) self;
    std::basic_stringstream<char> ss;
    SWITCH_QUANTITY_SUBTYPE(v, , ->display(ss));
    return PyUnicode_FromString(ss.str().c_str());
}


static PyObject* quantity_units_get(PyObject* self, void*) {
    QuantityObject* v = (QuantityObject*) self;
    UnitsObject* vu = (UnitsObject*) Units_Type.tp_alloc(&Units_Type, 0);
    if (vu == NULL)
        return NULL;
    vu->units = new Units();
    bool vEmpty = false;
    SWITCH_QUANTITY_SUBTYPE(v, vEmpty = , ->units().is_empty());
    SWITCH_QUANTITY_SUBTYPE(v, *(vu->units) = , ->units());
    if (!vEmpty && vu->units->is_empty()) {
	PyObject* error = Py_BuildValue("s", "Failed to parse units.");
	PyErr_SetObject(units_error, error);
	Py_XDECREF(error);
	return NULL;
    }
    
    return (PyObject*) vu;
}

static int quantity_units_set(PyObject* self, PyObject* value, void*) {
    PyObject* units_args = PyTuple_Pack(1, value);
    PyObject* unitsObject = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
    Py_DECREF(units_args);
    if (unitsObject == NULL)
	return -1;
    
    QuantityObject* v = (QuantityObject*) self;
    SWITCH_QUANTITY_SUBTYPE(v, , ->convert_to(*(((UnitsObject*)unitsObject)->units)));
    return 0;
}

template<typename T>
static PyObject* do_quantity_value_get(Quantity<T>* x, void*) {
    T val = x->value();
    return PyObject_FromScalarYgg(val);
}

static PyObject* quantity_value_get(PyObject* self, void*) {
    QuantityObject* v = (QuantityObject*) self;
    SWITCH_QUANTITY_SUBTYPE_CALL(v, return do_quantity_value_get, NULL);
    return NULL;
}

template<typename T, typename Tval>
static int do_quantity_value_set_lvl2(Quantity<T>* x, Tval& value,
				      RAPIDJSON_ENABLEIF((YGGDRASIL_IS_CASTABLE(Tval, T)))) {
    x->set_value((T)value);
    return 0;
}
template<typename T, typename Tval>
static int do_quantity_value_set_lvl2(Quantity<T>* x, Tval& value,
				      RAPIDJSON_DISABLEIF((YGGDRASIL_IS_CASTABLE(Tval, T)))) {
    return -1;
}

template<typename Tval>
static int do_quantity_value_set_lvl1(QuantityObject* v, Tval& value) {
    SWITCH_QUANTITY_SUBTYPE_CALL(v, return do_quantity_value_set_lvl2, value)
    return -1;
}

static int quantity_value_set(PyObject* self, PyObject* value, void*) {
    QuantityObject* v = (QuantityObject*) self;
    QuantitySubType value_subtype;
    EXTRACT_PYTHON_VALUE(value_subtype, value, val,
			 return do_quantity_value_set_lvl1,
			 (v, *val), return -1)
}

static PyObject* quantity_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* otherObject;
    const UnitsObject* other;
    
    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;

    if (PyObject_IsInstance(otherObject, (PyObject*)&Quantity_Type)) {
	other = (UnitsObject*)quantity_units_get(otherObject, NULL);
    } else if (PyObject_IsInstance(otherObject, (PyObject*)&Units_Type)) {
	other = (UnitsObject*)otherObject;
	Py_INCREF(otherObject);
    } else {
	other = (UnitsObject*)PyObject_Call((PyObject*)&Units_Type, args, NULL);
    }
    if (other == NULL)
        return NULL;
    
    QuantityObject* v = (QuantityObject*) self;
    bool result = false;
    SWITCH_QUANTITY_SUBTYPE(v, result = , ->is_compatible(*other->units));
    Py_DECREF(other);
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
    
}


static PyObject* quantity_is_dimensionless(PyObject* self, PyObject* args) {
    QuantityObject* v = (QuantityObject*) self;
    bool result;
    SWITCH_QUANTITY_SUBTYPE(v, result = , ->is_dimensionless());
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
}


template <typename Ta, typename Tb>
static PyObject* do_is_equivalent(Quantity<Ta>* a, Quantity<Tb>* b,
				  RAPIDJSON_DISABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    SET_ERROR(units_error, "Incompatible Quantity value types.", NULL);
    return NULL;
}
template <typename Ta, typename Tb>
static PyObject* do_is_equivalent(Quantity<Ta>* a, Quantity<Tb>* b,
				  RAPIDJSON_ENABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    if (a->equivalent_to(*b)) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
}


template<typename T>
static PyObject* quantity_is_equivalent_nested(Quantity<T>* b,
					       QuantityObject* va) {
    SWITCH_QUANTITY_SUBTYPE_CALL(va, return do_is_equivalent, b)
}


static PyObject* quantity_is_equivalent(PyObject* self, PyObject* args) {
    PyObject* otherObject;

    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;
    
    if (!PyObject_IsInstance(otherObject, (PyObject*)&Quantity_Type)) {
	PyErr_SetString(PyExc_TypeError, "expected a Quantity instance");
	return NULL;
    }
    
    QuantityObject* va = (QuantityObject*) self;
    QuantityObject* vb = (QuantityObject*) otherObject;

    SWITCH_QUANTITY_SUBTYPE_CALL(vb, return quantity_is_equivalent_nested, va)
}


static PyObject* quantity_to(PyObject* self, PyObject* args) {
    PyObject* unitsObject;

    if (!PyArg_ParseTuple(args, "O", &unitsObject))
	return NULL;

    PyObject* units_args = PyTuple_Pack(1, unitsObject);
    unitsObject = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
    Py_DECREF(units_args);
    if (unitsObject == NULL)
	return NULL;

    QuantityObject* v = (QuantityObject*) self;
    bool compat = false;
    SWITCH_QUANTITY_SUBTYPE(v, compat = , ->is_compatible(*(((UnitsObject*)unitsObject)->units)));
    if (!compat) {
	PyObject* error = Py_BuildValue("s", "Incompatible units");
	PyErr_SetObject(units_error, error);
	Py_XDECREF(error);
	return NULL;
    }

    PyObject* quantity_args = PyTuple_Pack(1, self);
    PyObject* out = quantity_new(&Quantity_Type, quantity_args, NULL);
    Py_DECREF(quantity_args);
    if (out == NULL)
	return NULL;

    QuantityObject* vout = (QuantityObject*) out;
    SWITCH_QUANTITY_SUBTYPE(vout, , ->convert_to(*(((UnitsObject*)unitsObject)->units)));
    return out;
}


template<typename T>
static PyObject* quantity_richcompare_nest(Quantity<T>* vself,
					   QuantityObject* vsolf0,
					   int op) {
    Quantity<T>* vsolf = (Quantity<T>*)(vsolf0->quantity);
    switch (op) {
    case (Py_LT):
    case (Py_LE):
    case (Py_GT):
    case (Py_GE): {
	if (vsolf->units() != vself->units()) {
	    PyObject* error = Py_BuildValue("s", "Comparison invalid for Quantity instances with different units, convert one first.");
	    PyErr_SetObject(units_error, error);
	    Py_XDECREF(error);
	    return NULL;
	}
	Py_RETURN_RICHCOMPARE(*vself, *vsolf, op);
    }
    case (Py_EQ):
    case (Py_NE):
	Py_RETURN_RICHCOMPARE(*vself, *vsolf, op);
    default:
	Py_INCREF(Py_NotImplemented);
	return Py_NotImplemented;
    }
}


static PyObject* quantity_richcompare(PyObject *self, PyObject *other, int op) {
    QuantityObject* vself = (QuantityObject*) self;
    QuantityObject* vsolf = (QuantityObject*) other;
    if (vself->subtype != vsolf->subtype) {
	Py_INCREF(Py_False);
	return Py_False;
    }
    SWITCH_QUANTITY_SUBTYPE_CALL(vself, return quantity_richcompare_nest,
				 vsolf, op)
}


// Number operations
static QuantityObject* get_quantity(PyObject *a) {
    QuantityObject* va = NULL;
    if (PyObject_IsInstance(a, (PyObject*)&Quantity_Type)) {
	va = (QuantityObject*)a;
    } else {
	PyObject* quantity_args = PyTuple_Pack(1, a);
	va = (QuantityObject*)quantity_new(&Quantity_Type, quantity_args, NULL);
	Py_DECREF(quantity_args);
	if (va == NULL)
	    return NULL;
    }
    return va;
}


template <typename Ta, typename Tb>
static void* do_quantity_op(Quantity<Ta>* a, Quantity<Tb>* b, BinaryOps op,
			    bool inplace=false,
			    RAPIDJSON_DISABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    SET_ERROR(units_error, "Incompatible Quantity value types.", NULL);
}
template <typename Ta, typename Tb>
static void* do_quantity_op(Quantity<Ta>* a, Quantity<Tb>* b, BinaryOps op,
			    bool inplace=false,
			    RAPIDJSON_ENABLEIF((YGGDRASIL_IS_CASTABLE(Tb, Ta)))) {
    Quantity<Ta>* out;
    if (inplace)
	out = a;
    else
	out = new Quantity<Ta>();
    switch (op) {
    case (binaryOpAdd): {
	if (!a->is_compatible(*b))
	    SET_ERROR(units_error, "Cannot add Quantity instances with incompatible units", NULL)
	if (inplace)
	    *out += *b;
	else
	    *out = *a + *b;
	break;
    }
    case (binaryOpSubtract): {
	if (!a->is_compatible(*b))
	    SET_ERROR(units_error, "Cannot subtract Quantity instances with incompatible units", NULL)
	if (inplace)
	    *out -= *b;
	else
	    *out = *a - *b;
	break;
    }
    case (binaryOpMultiply): {
	if (inplace)
	    *out *= *b;
	else
	    *out = *a * *b;
	break;
    }
    case (binaryOpDivide): {
	if (inplace)
	    *out /= *b;
	else
	    *out = *a / *b;
	break;
    }
    case (binaryOpModulo): {
	if (inplace)
	    *out %= *b;
	else
	    *out = *a % *b;
	break;
    }
    case (binaryOpFloorDivide): {
	if (inplace)
	    *out /= *b;
	else
	    *out = *a / *b;
	out->floor_inplace();
	break;
    }
    }
    return (void*)out;
}


template <typename Tb>
static void* do_quantity_op_lvl2(Quantity<Tb>* b, QuantityObject* va, BinaryOps op,
				 bool inplace=false) {
    SWITCH_QUANTITY_SUBTYPE_CALL(va, return do_quantity_op, b, op, inplace)
}


static PyObject* do_quantity_op_lvl1(PyObject *a, PyObject *b, BinaryOps op,
				     bool inplace=false) {
    // if (inplace && !PyObject_IsInstance(a, (PyObject*)&Quantity_Type) && PyObject_IsInstance(b, (PyObject*)&Quantity_Type))
    // 	return do_quantity_op_lvl1(b, a, op, true);
    QuantityObject* va = get_quantity(a);
    QuantityObject* vb = get_quantity(b);
    if ((va == NULL) || (vb == NULL))
	return NULL;
    QuantityObject* out;
    if (inplace && PyObject_IsInstance(a, (PyObject*)&Quantity_Type)) {
	out = va;
	Py_INCREF(a);
    } else {
	out = (QuantityObject*) Quantity_Type.tp_alloc(&Quantity_Type, 0);
	out->subtype = va->subtype;
    }
    SWITCH_QUANTITY_SUBTYPE_CALL(vb, out->quantity = do_quantity_op_lvl2, va, op, inplace)
    if (out->quantity == NULL)
	return NULL;
    return (PyObject*) out;
}
    

static PyObject* quantity_add(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpAdd); }
static PyObject* quantity_subtract(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpSubtract); }
static PyObject* quantity_multiply(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpMultiply); }
static PyObject* quantity_divide(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpDivide); }
static PyObject* quantity_floor_divide(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpFloorDivide); }
static PyObject* quantity_modulo(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpModulo); }
static PyObject* quantity_add_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpAdd, true); }
static PyObject* quantity_subtract_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpSubtract, true); }
static PyObject* quantity_multiply_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpMultiply, true); }
static PyObject* quantity_divide_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpDivide, true); }
static PyObject* quantity_modulo_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpModulo, true); }
static PyObject* quantity_floor_divide_inplace(PyObject *a, PyObject *b)
{ return do_quantity_op_lvl1(a, b, binaryOpFloorDivide, true); }

template<typename Tbase, typename Tmod, typename T>
static void* quantity_power_lvl4(Quantity<Tbase>* base, Quantity<Tmod>* mod, T* val,
				 bool inplace=false) {
    Quantity<Tbase>* out;
    if (inplace) {
	out = base;
	out->inplace_pow(*val);
    } else {
	out = new Quantity<Tbase>();
	*out = base->pow(*val);
    }
    *out %= *mod;
    return (void*)out;
}
template<typename Tbase, typename Tmod, typename T>
static void* quantity_power_lvl4(Quantity<Tbase>* base, Quantity<Tmod>* mod, std::complex<T>* val,
				 bool inplace=false) {
    PyErr_SetString(PyExc_TypeError, "Complex exponent not supported");
    return NULL;
}
template<typename Tmod, typename T>
static void* quantity_power_lvl3(Quantity<Tmod>* mod, T* val, QuantityObject* vbase,
				 bool inplace=false) {
    SWITCH_QUANTITY_SUBTYPE_CALL(vbase, return quantity_power_lvl4, mod, val, inplace);
}
template<typename T>
static void* quantity_power_lvl2(T* val, QuantityObject* vbase, QuantityObject* vmod,
				 bool inplace=false) {
    SWITCH_QUANTITY_SUBTYPE_CALL(vmod, return quantity_power_lvl3, val, vbase, inplace);
}
static PyObject* quantity_power_lvl1(PyObject *base, PyObject *exp, PyObject *mod,
				     bool inplace=false) {
    QuantityObject* vbase = get_quantity(base);
    QuantityObject* vmod = get_quantity(mod);
    if ((vbase == NULL) || (vmod == NULL))
	return NULL;
    if (PyObject_IsInstance(exp, (PyObject*)&Quantity_Type))
	SET_ERROR(units_error, "Raising to a Quantity power not supported", NULL);
    QuantityObject* out;
    if (inplace && PyObject_IsInstance(base, (PyObject*)&Quantity_Type)) {
	out = vbase;
	Py_INCREF(base);
    } else {
	out = (QuantityObject*) Quantity_Type.tp_alloc(&Quantity_Type, 0);
	out->subtype = vbase->subtype;
    }
    QuantitySubType subtype_exp;
    EXTRACT_PYTHON_VALUE(subtype_exp, exp, tmp,
			 out->quantity = quantity_power_lvl2,
			 (tmp, vbase, vmod, inplace),
			 { PyErr_SetString(PyExc_TypeError, "Expected scalar integer, floating point, or complex value"); return NULL; })
    if (out->quantity == NULL)
	return NULL;
    return (PyObject*) out;
}
static PyObject* quantity_power(PyObject *base, PyObject *exp, PyObject *mod)
{ return quantity_power_lvl1(base, exp, mod); }
static PyObject* quantity_power_inplace(PyObject *base, PyObject *exp, PyObject *mod)
{ return quantity_power_lvl1(base, exp, mod, true); }


///////////////////
// QuantityArray //
///////////////////

typedef struct {
    PyArrayObject_fields base;
    char buffer[QUANTITY_ARRAY_OFFSET_BUFFER];
    UnitsObject* units;
} QuantityArrayObject;


PyDoc_STRVAR(quantity_array_doc,
             "QuantityArray(value, units)\n"
             "\n"
             "Create and return a new QuantityArray instance from the given"
             " `value` and `units` string or Units instance.");


static PyMethodDef quantity_array_methods[] = {
    {"is_compatible", (PyCFunction) quantity_array_is_compatible, METH_VARARGS,
     "Check if a set of units or quantity is compatible with another set."},
    {"is_dimensionless", (PyCFunction) quantity_array_is_dimensionless, METH_NOARGS,
     "Check if the quantity has dimensionless units."},
    {"to", (PyCFunction) quantity_array_to, METH_VARARGS,
     "Convert the quantity to another set of units."},
    {"is_equivalent", (PyCFunction) quantity_array_is_equivalent, METH_VARARGS,
     "Check if another QuantityArray is equivalent when convert to the same units/"},
    {"__array_ufunc__", (PyCFunction) quantity_array__array_ufunc__, METH_VARARGS | METH_KEYWORDS,
     "UFuncs"},
    {"__array_wrap__", (PyCFunction) quantity_array__array_wrap__, METH_VARARGS,
     "array wrapper for numpy views"},
    {"__array_finalize__", (PyCFunction) quantity_array__array_finalize__, METH_VARARGS,
     "finalize array "},
    {"__array_function__", (PyCFunction) quantity_array__array_function__,
     METH_VARARGS | METH_KEYWORDS,
     "numpy array function handling"},
    {NULL}  /* Sentinel */
};


static PyGetSetDef quantity_array_properties[] = {
    {"units", quantity_array_units_get, quantity_array_units_set,
     "The rapidjson.Units units for the quantity.", NULL},
    {"value", quantity_array_value_get, quantity_array_value_set,
     "The quantity's value (in the current unit system)."},
    {NULL}
};


static PyMappingMethods quantity_array_map = {
    0,                           // mp_length
    quantity_array_subscript,    // mp_subscript
    quantity_array_ass_subscript // mp_ass_subscript
};


static PyTypeObject QuantityArray_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "rapidjson.QuantityArray",            /* tp_name */
    sizeof(QuantityArrayObject),          /* tp_basicsize */
    0,                                    /* tp_itemsize */
    (destructor) quantity_array_dealloc,  /* tp_dealloc */
    0,                                    /* tp_print */
    0,                                    /* tp_getattr */
    0,                                    /* tp_setattr */
    0,                                    /* tp_compare */
    quantity_array_repr,                  /* tp_repr */
    0,                                    /* tp_as_number */
    0,                                    /* tp_as_sequence */
    &quantity_array_map,                  /* tp_as_mapping */
    0,                                    /* tp_hash */
    0,                                    /* tp_call */
    quantity_array_str,                   /* tp_str */
    0,                                    /* tp_getattro */
    0,                                    /* tp_setattro */
    0,                                    /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                   /* tp_flags */
    quantity_array_doc,                   /* tp_doc */
    0,                                    /* tp_traverse */
    0,                                    /* tp_clear */
    0,                                    /* tp_richcompare */
    0,                                    /* tp_weaklistoffset */
    0,                                    /* tp_iter */
    0,                                    /* tp_iternext */
    quantity_array_methods,               /* tp_methods */
    0,                                    /* tp_members */
    quantity_array_properties,            /* tp_getset */
    0,                                    /* tp_base */
    0,                                    /* tp_dict */
    0,                                    /* tp_descr_get */
    0,                                    /* tp_descr_set */
    0,                                    /* tp_dictoffset */
    0,                                    /* tp_init */
    0,                                    /* tp_alloc */
    quantity_array_new,                   /* tp_new */
    PyObject_Del,                         /* tp_free */
};


/////////////////////////////
// QuantityArray Utilities //
/////////////////////////////

static PyObject* quantity_array_pull_factor(PyObject* x) {
    double factor = ((QuantityArrayObject*)x)->units->units->pull_factor();
    if (!internal::values_eq(factor, 1)) {
	PyObject* py_factor;
	if (internal::values_eq(floor(factor), factor))
	    py_factor = PyLong_FromDouble(factor);
	else
	    py_factor = PyFloat_FromDouble(factor);
	if (py_factor == NULL) {
	    Py_DECREF(x);
	    return NULL;
	}
	PyObject* out = PyNumber_InPlaceMultiply(x, py_factor);
	Py_DECREF(py_factor);
	// Py_DECREF(x);
	return out;
    }
    return x;
}

static QuantityArrayObject* quantity_array_coerce(PyObject* x) {
    PyObject* out = NULL;
    if (PyObject_IsInstance(x, (PyObject*)&QuantityArray_Type)) {
	Py_INCREF(x);
	return (QuantityArrayObject*)x;
    }
    PyObject* args = NULL;
    if (PyObject_HasAttrString(x, "units")) {
	PyObject* units = PyObject_GetAttrString(x, "units");
	if (units == NULL) return NULL;
	args = PyTuple_Pack(2, x, units);
	Py_DECREF(units);
    } else {
	args = PyTuple_Pack(1, x);
    }
    if (args == NULL) return NULL;
    out = PyObject_Call((PyObject*)&QuantityArray_Type, args, NULL);
    Py_DECREF(args);
    return (QuantityArrayObject*)out;
}


static PyObject* quantity_array_numpy_tuple(PyObject* args,
					    bool as_view = false,
					    PyObject* convert_to = NULL) {
    Py_ssize_t Nargs = PyTuple_Size(args);
    Py_ssize_t i = 0;
    PyObject *item, *new_item, *item_array, *out = NULL;
    bool error = false;
    PyArrayObject* arr_cast = NULL;
    PyArray_Descr* dtype = NULL;
    out = PyTuple_New(Nargs);
    if (out == NULL) {
	return NULL;
    }
    for (i = 0; i < Nargs; i++) {
	new_item = NULL;
	item = PyTuple_GetItem(args, i);
	if (item == NULL) {
	    error = true;
	    goto cleanup;
	}
	if (convert_to != NULL) {
	    item_array = (PyObject*)quantity_array_coerce(item);
	    if (item_array == NULL) {
		error = true;
		goto cleanup;
	    }
	    new_item = quantity_array_get_converted_value(item_array,
							  convert_to);
	    Py_DECREF(item_array);
	} else if (as_view) {
	    if (!PyArray_Check(item)) {
		error = true;
		goto cleanup;
	    }
	    new_item = PyArray_View((PyArrayObject*)item, NULL, &PyArray_Type);
	} else {
	    if (PyArray_Check(item)) {
		arr_cast = (PyArrayObject*)item;
		dtype = PyArray_DESCR(arr_cast);
		Py_INCREF(dtype);
		new_item = PyArray_NewFromDescr(
		    &PyArray_Type, dtype,
		    PyArray_NDIM(arr_cast),
		    PyArray_DIMS(arr_cast),
		    PyArray_STRIDES(arr_cast),
		    NULL,
		    PyArray_FLAGS(arr_cast),
		    NULL);
		if (new_item != NULL) {
		    if (PyArray_CopyInto((PyArrayObject*)new_item, arr_cast) < 0) {
			Py_DECREF(new_item);
			error = true;
			goto cleanup;
		    }
		}
	    } else {
		if (!PyArray_Converter(item, &new_item)) {
		    error = true;
		    goto cleanup;
		}
	    }
	}
	if (new_item == NULL) {
	    error = true;
	    goto cleanup;
	}
	if (PyTuple_SetItem(out, i, new_item) < 0) {
	    error = true;
	    goto cleanup;
	}
    }
cleanup:
    if (error) {
	Py_DECREF(out);
	out = NULL;
    }
    return out;
}


///////////////////////////
// QuantityArray Methods //
///////////////////////////


static void quantity_array_dealloc(PyObject* self)
{
    QuantityArrayObject* s = (QuantityArrayObject*) self;
    Py_XDECREF(s->units);
    PyArray_Type.tp_dealloc(self);
}


static PyObject* quantity_array_new(PyTypeObject* type, PyObject* args, PyObject* kwargs)
{
    // TODO: Allow dtype to be passed?
    PyObject *valueObject = NULL, *unitsObject = NULL, *units = NULL,
	*arr = NULL, *out = NULL;
    static char const* kwlist[] = {
	"value",
	"units",
	NULL
    };
    bool nullUnits = false, dont_pull = false;
    PyArrayObject* arr_cast = NULL;
    PyArray_Descr *dtype = NULL;
    int ret = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|O:QuantityArray",
				     (char**) kwlist,
				     &valueObject, &unitsObject))
	return NULL;

    nullUnits = (unitsObject == NULL);
    units = get_empty_units(unitsObject);
    if (units == NULL) {
	return NULL;
    }

    if ((!nullUnits) &&
	PyObject_IsInstance(valueObject, (PyObject*)&QuantityArray_Type)) {
	valueObject = quantity_array_get_converted_value(valueObject, units);
	if (valueObject == NULL) {
	    goto fail;
	}
	dont_pull = true;
    } else {
	Py_INCREF(valueObject);
    }
    
    arr = PyArray_FromAny(valueObject, NULL, 0, 0, 0, NULL);
    if (arr != valueObject)
	Py_DECREF(valueObject);
    if (arr == NULL) {
	goto fail;
    }
    arr_cast = (PyArrayObject*)arr;
    dtype = PyArray_DescrNew(PyArray_DESCR(arr_cast));
    if (dtype == NULL) {
	goto fail;
    }
    out = PyArray_NewFromDescr(
	&QuantityArray_Type, dtype,
	PyArray_NDIM(arr_cast),
	PyArray_DIMS(arr_cast),
	PyArray_STRIDES(arr_cast),
	NULL,
	0, 
	NULL);
    if (out == NULL) {
	Py_DECREF(dtype);
	goto fail;
    }
    ret = PyArray_CopyInto((PyArrayObject*)out, (PyArrayObject*)arr);
    if (ret < 0) {
	goto fail;
    }

    ((QuantityArrayObject*)out)->units = (UnitsObject*)units;
    if (!dont_pull) {
	out = quantity_array_pull_factor(out);
    }

    Py_XDECREF(arr);
    return out;
fail:
    Py_XDECREF(units);
    Py_XDECREF(arr);
    Py_XDECREF(out);
    return NULL;
}


static PyObject* quantity_array_str(PyObject* self) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    PyObject* view = quantity_array_value_get(self, NULL);
    if (view == NULL) return NULL;
    PyObject* base_out = PyObject_Str(view);
    Py_DECREF(view);
    if (base_out == NULL) return NULL;
    std::string units = v->units->units->str();
    PyObject* out = PyUnicode_FromFormat("%U %s", base_out, units.c_str());
    Py_DECREF(base_out);
    return out;
}


static PyObject* quantity_array_repr(PyObject* self) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    PyObject* view = quantity_array_value_get(self, NULL);
    if (view == NULL) return NULL;
    PyObject* base_out = PyObject_Repr(view);
    Py_DECREF(view);
    if (base_out == NULL) return NULL;
    Py_ssize_t len = PyUnicode_GetLength(base_out);
    PyObject* base_sub = PyUnicode_Substring(base_out, 0, len - 1);
    Py_DECREF(base_out);
    if (base_sub == NULL) return NULL;
    std::string units = v->units->units->str();
    PyObject* out = NULL;
    PyObject* eq = PyUnicode_FromString("=");
    if (eq == NULL) return NULL;
    int ret = PySequence_Contains(base_sub, eq);
    Py_DECREF(eq);
    if (ret < 0) return NULL;
    if (ret)
	out = PyUnicode_FromFormat("%U, units='%s')", base_sub, units.c_str());
    else
	out = PyUnicode_FromFormat("%U, '%s')", base_sub, units.c_str());
    Py_DECREF(base_sub);
    return out;
}


static PyObject* quantity_array_units_get(PyObject* self, void*) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    UnitsObject* vu = (UnitsObject*) Units_Type.tp_alloc(&Units_Type, 0);
    if (vu == NULL)
        return NULL;
    vu->units = new Units(*(v->units->units));
    bool vEmpty = v->units->units->is_empty();
    if (!vEmpty && vu->units->is_empty()) {
	PyObject* error = Py_BuildValue("s", "Failed to parse units.");
	PyErr_SetObject(units_error, error);
	Py_XDECREF(error);
	return NULL;
    }
    
    return (PyObject*) vu;
}

static PyObject* quantity_array_get_converted_value(PyObject* self,
						    PyObject* units) {
    PyObject* unitsObject = NULL;
    if (PyObject_IsInstance(units, (PyObject*)&Units_Type)) {
	unitsObject = units;
	Py_INCREF(unitsObject);
    } else {
	PyObject* units_args = PyTuple_Pack(1, units);
	if (units_args == NULL) return NULL;
	unitsObject = PyObject_Call((PyObject*)&Units_Type, units_args, NULL);
	Py_DECREF(units_args);
    }
    if (unitsObject == NULL)
	return NULL;
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    
    if (!v->units->units->is_compatible(*(((UnitsObject*)unitsObject)->units))) {
	std::string u0 = v->units->units->str();
	std::string u1 = ((UnitsObject*)unitsObject)->units->str();
	PyErr_Format(units_error, "Incompatible units: '%s' and '%s'",
		     u0.c_str(), u1.c_str());
	Py_DECREF(unitsObject);
	return NULL;
    }
    std::vector<double> factor = v->units->units->conversion_factor(*(((UnitsObject*)unitsObject)->units));
    Py_DECREF(unitsObject);
    PyObject* arr = quantity_array_value_get_copy(self, NULL);
    if (arr == NULL) {
	return NULL;
    }
    PyObject* tmp = NULL;
    if (!internal::values_eq(factor[1], 0)) {
	PyObject* offset;
	if (internal::values_eq(floor(factor[1]), factor[1]))
	    offset = PyLong_FromDouble(factor[1]);
	else
	    offset = PyFloat_FromDouble(factor[1]);
	if (offset == NULL) {
	    Py_DECREF(arr);
	    return NULL;
	}
	tmp = PyNumber_Subtract(arr, offset);
	Py_DECREF(offset);
	Py_DECREF(arr);
	if (tmp == NULL) {
	    return NULL;
	}
	arr = tmp;
    }
    if (!internal::values_eq(factor[0], 1)) {
	PyObject* scale;
	if (internal::values_eq(floor(factor[0]), factor[0]))
	    scale = PyLong_FromDouble(factor[0]);
	else
	    scale = PyFloat_FromDouble(factor[0]);
	if (scale == NULL) {
	    Py_DECREF(arr);
	    return NULL;
	}
	tmp = PyNumber_Multiply(arr, scale);
	Py_DECREF(scale);
	Py_DECREF(arr);
	if (tmp == NULL) {
	    return NULL;
	}
	arr = tmp;
    }
    return arr;
}

static int quantity_array_units_set(PyObject* self, PyObject* value, void*) {
    PyObject* unitsObject = (PyObject*)units_coerce(value);
    if (unitsObject == NULL)
	return -1;

    PyObject* arr = quantity_array_get_converted_value(self, unitsObject);
    if (arr == NULL) {
	Py_DECREF(unitsObject);
	return -1;
    }
    if (quantity_array_value_set(self, arr, NULL) < 0) {
	Py_DECREF(arr);
	Py_DECREF(unitsObject);
	return -1;
    }
    Py_DECREF(arr);
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    v->units->units[0] = *(((UnitsObject*)unitsObject)->units);
    Py_DECREF(unitsObject);
    return 0;
}


static PyObject* quantity_array_value_get(PyObject* self, void*) {
    return PyArray_View((PyArrayObject*)self, NULL, &PyArray_Type);
}


static PyObject* quantity_array_value_get_copy(PyObject* self, void*) {
    PyArrayObject* arr_cast = (PyArrayObject*)self;
    PyArray_Descr *dtype = PyArray_DESCR(arr_cast);
    Py_INCREF(dtype);
    PyObject* out = PyArray_NewFromDescr(
	&PyArray_Type, dtype,
	PyArray_NDIM(arr_cast),
	PyArray_DIMS(arr_cast),
	PyArray_STRIDES(arr_cast),
	NULL,
	PyArray_FLAGS(arr_cast),
	NULL);
    if (out != NULL) {
	if (PyArray_CopyInto((PyArrayObject*)out, arr_cast) < 0) {
	    Py_DECREF(out);
	    return NULL;
	}
    }
    return out;
}


static int quantity_array_value_set(PyObject* self, PyObject* value, void*) {
    // Cleanup out existing memory based on
    // numpy/core/src/multiarray/arrayobject.c::array_dealloc
    PyArrayObject_fields *fa = (PyArrayObject_fields *)self;
    int req = NPY_ARRAY_C_CONTIGUOUS | NPY_ARRAY_ENSUREARRAY | NPY_ARRAY_ALIGNED;
    PyArrayObject* arr = NULL;
    npy_intp *dims = NULL, *strides = NULL;
    PyArray_Descr* descr = NULL;
    int nbytes = 1, old_flags;
    char* data = NULL;
    // Should weakref's be freed?
    // if (fa->weakreflist != NULL) {
    // 	PyObject_ClearWeakRefs((PyObject *)self);
    // }
    
    // Rebuild array with new parameters based on
    // numpy/core/src/multiarray/ctors.c::PyArray_NewFromDescr_int
    arr = (PyArrayObject*)PyArray_FromAny(value, NULL, 0, 0, req, NULL);
    if (arr == NULL) {
	return -1;
    } else if ((PyObject*)arr == value) {
	Py_INCREF(arr);
    }
    old_flags = fa->flags;
    dims = PyArray_DIMS(arr);
    strides = PyArray_STRIDES(arr);
    descr = PyArray_DescrNew(PyArray_DESCR(arr));
    if (descr == NULL) {
	goto fail;
    }
    nbytes = PyArray_NBYTES(arr);
    // TODO: Preserve base or take action?
    fa->nd = PyArray_NDIM(arr);
    fa->flags = NPY_ARRAY_DEFAULT;
    if (fa->base) {
	if (old_flags & NPY_ARRAY_WRITEBACKIFCOPY) {
	    PyErr_SetString(units_error, "NPY_ARRAY_WRITEBACKIFCOPY detected and not currently supported");
	    goto fail;
	    // retval = PyArray_ResolveWritebackIfCopy(self);
	    // if (retval < 0)
	    // {
	    // 	PyErr_Print();
	    // 	PyErr_Clear();
	    // }
	}
	Py_XDECREF(fa->base);
    }
    fa->base = NULL; 
    Py_DECREF(fa->descr);
    fa->descr = descr;
    // Should weakref's be freed?
    // fa->weakreflist = (PyObject *)NULL;
    if (fa->nd > 0) {
	fa->dimensions = PyDimMem_RENEW((void*)(fa->dimensions), 2 * fa->nd);
	if (fa->dimensions == NULL) {
	    PyErr_NoMemory();
	    goto fail;
	}
	fa->strides = fa->dimensions + fa->nd;
	for (int i = 0; i < fa->nd; i++) {
	    fa->dimensions[i] = dims[i];
	    fa->strides[i] = strides[i];
	}
    } else {
	fa->flags |= NPY_ARRAY_C_CONTIGUOUS|NPY_ARRAY_F_CONTIGUOUS;
    }
    if ((old_flags & NPY_ARRAY_OWNDATA) && fa->data) {
	data = (char*)PyDataMem_RENEW(fa->data, nbytes);
    } else {
	data = (char*)PyDataMem_NEW(nbytes);
    }
    if (data == NULL) {
	PyErr_NoMemory();
	goto fail;
    }
    fa->flags |= NPY_ARRAY_OWNDATA;
    fa->data = data;
    if (PyArray_CopyInto((PyArrayObject*)self, arr) < 0) {
	goto fail;
    }
    Py_XDECREF(arr);
    return 0;
fail:
    Py_XDECREF(arr);
    return -1;
}


static PyObject* quantity_array_is_compatible(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject* otherObject;
    const UnitsObject* other;
    
    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;

    if (PyObject_IsInstance(otherObject, (PyObject*)&QuantityArray_Type)) {
	other = (UnitsObject*)quantity_array_units_get(otherObject, NULL);
    } else if (PyObject_IsInstance(otherObject, (PyObject*)&Units_Type)) {
	other = (UnitsObject*)otherObject;
	Py_INCREF(otherObject);
    } else {
	other = (UnitsObject*)PyObject_Call((PyObject*)&Units_Type, args, NULL);
    }
    if (other == NULL)
        return NULL;
    
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    bool result = v->units->units->is_compatible(*other->units);
    Py_DECREF(other);
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
    
}


static PyObject* quantity_array_is_dimensionless(PyObject* self, PyObject* args) {
    QuantityArrayObject* v = (QuantityArrayObject*) self;
    bool result = v->units->units->is_dimensionless();
    if (result) {
	Py_INCREF(Py_True);
	return Py_True;
    }
    Py_INCREF(Py_False);
    return Py_False;
}


static PyObject* quantity_array_is_equivalent(PyObject* self, PyObject* args) {
    PyObject* otherObject;

    if (!PyArg_ParseTuple(args, "O", &otherObject))
	return NULL;
    
    if (!PyObject_IsInstance(otherObject, (PyObject*)&QuantityArray_Type)) {
	PyErr_SetString(PyExc_TypeError, "expected a QuantityArray instance");
	return NULL;
    }
    QuantityArrayObject* va = (QuantityArrayObject*) self;
    QuantityArrayObject* vb = (QuantityArrayObject*) otherObject;
    if (!va->units->units->is_compatible(*vb->units->units)) {
	Py_INCREF(Py_False);
	return Py_False;
    }

    PyObject* a = quantity_array_value_get(self, NULL);
    if (a == NULL) {
	return NULL;
    }
    PyObject* b = quantity_array_get_converted_value(otherObject,
						     (PyObject*)(va->units));
    if (b == NULL) {
	Py_DECREF(a);
	return NULL;
    }
    PyObject* out_arr = NULL;
    out_arr = PyObject_CallMethod(a, "__eq__", "(O)", b);
    Py_DECREF(a);
    Py_DECREF(b);
    PyObject* out = NULL;
    if (out_arr != NULL) {
	out = PyObject_CallMethod(out_arr, "all", NULL);
    }
    return out;
}


static PyObject* quantity_array_to(PyObject* self, PyObject* args) {
    PyObject* unitsObject;

    if (!PyArg_ParseTuple(args, "O", &unitsObject))
	return NULL;

    PyObject* arr = quantity_array_get_converted_value(self, unitsObject);
    if (arr == NULL) {
	return NULL;
    }
    PyObject* quantity_array_args = PyTuple_Pack(2, arr, unitsObject);
    Py_DECREF(arr);
    if (quantity_array_args == NULL) {
	return NULL;
    }
    PyObject* out = PyObject_Call((PyObject*)&QuantityArray_Type, quantity_array_args, NULL);
    Py_DECREF(quantity_array_args);
    if (out == NULL)
	return NULL;

    return out;
}

static PyObject* quantity_array__array_ufunc__(PyObject* self, PyObject* args, PyObject* kwargs) {
    PyObject *ufunc, *method_name, *normal_args, *ufunc_method, *tmp, *tmp2,
	*i0, *i1, *i0_units, *i1_units, *out = NULL, *kw_key, *kw_val;
    PyObject *result = NULL, *result_type = NULL,
	*modified_args = NULL, *modified_kwargs = NULL, *modified_out = NULL;
    PyUFuncObject* ufunc_object;
    PyObject *result_units = NULL, *convert_units = NULL;
    std::string ufunc_name;
    int is_call, res;
    Py_ssize_t Nargs, kw_pos;
    bool inplace = false;

    assert(PyTuple_CheckExact(args));
    assert(kwargs == NULL || PyDict_CheckExact(kwargs));

    if (PyTuple_GET_SIZE(args) < 2) {
	PyErr_SetString(PyExc_TypeError,
			"__array_ufunc__ requires at least 2 arguments");
	return NULL;
    }
    normal_args = PyTuple_GetSlice(args, 2, PyTuple_GET_SIZE(args));
    if (normal_args == NULL) {
	return NULL;
    }
    
    ufunc = PyTuple_GET_ITEM(args, 0);
    method_name = PyTuple_GET_ITEM(args, 1);
    if (ufunc == NULL || method_name == NULL) {
	goto cleanup;
    }
    ufunc_object = (PyUFuncObject*)ufunc;
    ufunc_name.insert(0, ufunc_object->name);
    tmp = PyUnicode_FromString("__call__");
    is_call = PyObject_RichCompareBool(method_name, tmp, Py_EQ);
    Py_DECREF(tmp);
    if (is_call < 0) {
	goto cleanup;
    } else if (!is_call) {
	PyErr_SetString(units_error,
			    "Only the __call__ ufunc method is currently supported by rapidjson.units.QuantityArray");
	goto cleanup;
    }
    if (kwargs != NULL) {
	out = PyDict_GetItemString(kwargs, "out");
    }
    if (out != NULL && PyTuple_Check(out)) {
	modified_out = quantity_array_numpy_tuple(out, true);
	if (modified_out == NULL) {
	    goto cleanup;
	}
	if (PyTuple_Size(out) == 1) {
	    i0 = PyTuple_GET_ITEM(out, 0);
	    if (i0 == NULL) {
		goto cleanup;
	    }
	    result_type = PyObject_Type(i0);
	    Py_DECREF(i0);
	    i0 = NULL;
	    if (result_type == NULL) {
		goto cleanup;
	    }
	}
    }
    Nargs = PyTuple_GET_SIZE(normal_args);
    if (Nargs > 0) {
	i0 = PyTuple_GET_ITEM(normal_args, 0);
	if (i0 == NULL) {
	    goto cleanup;
	}
	if (out != NULL) {
	    inplace = true;
	}
	if (inplace && !PyObject_IsInstance(i0, (PyObject*)&QuantityArray_Type)) {
	    PyErr_Format(units_error,
			 "Inplace '%s' operation not supported by rapidjson.units.QuantityArray", ufunc_name.c_str());
	    goto cleanup;
	}
    }
    // std::cerr << "__array_ufunc__: " << ufunc_name << ", " << Nargs << ", inplace = " << inplace << std::endl;
    if (Nargs == 1) { // unary operators
	if (ufunc_name == "isfinite" ||
	    ufunc_name == "isinf" ||
	    ufunc_name == "isnan" ||
	    ufunc_name == "isnat" ||
	    ufunc_name == "sign" ||
	    ufunc_name == "signbit") {
	    // Strip units
	} else if (ufunc_name == "negative" ||
		   ufunc_name == "positive" ||
		   ufunc_name == "absolute" ||
		   ufunc_name == "fabs" ||
		   ufunc_name == "rint" ||
		   ufunc_name == "floor" ||
		   ufunc_name == "ceil" ||
		   ufunc_name == "trunc") {
	    if (_has_units(i0)) {
		result_units = _get_units(i0);
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "sqrt" ||
		   ufunc_name == "square" ||
		   ufunc_name == "cbrt" ||
		   ufunc_name == "reciprocal") {
	    double power = 0;
	    if (ufunc_name == "sqrt")
		power = 0.5;
	    else if (ufunc_name == "square")
		power = 2.0;
	    else if (ufunc_name == "cbrt")
		power = 1.0 / 3.0;
	    else if (ufunc_name == "reciprocal")
		power = -1.0;
	    if (_has_units(i0)) {
		i0_units = _get_units(i0);
		if (i0_units == NULL) {
		    goto cleanup;
		}
		tmp = PyFloat_FromDouble(power);
		if (tmp == NULL) {
		    Py_DECREF(i0_units);
		    goto cleanup;
		}
		result_units = PyNumber_Power(i0_units, tmp, Py_None);
		Py_DECREF(i0_units);
		Py_DECREF(tmp);
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "sin" ||
		   ufunc_name == "cos" ||
		   ufunc_name == "tan" ||
		   ufunc_name == "sinh" ||
		   ufunc_name == "cosh" ||
		   ufunc_name == "tanh") {
	    if (_has_units(i0)) {
		tmp = PyUnicode_FromString("radians");
		if (tmp == NULL) {
		    goto cleanup;
		}
		convert_units = (PyObject*)units_coerce(tmp);
		Py_DECREF(tmp);
		if (convert_units == NULL) {
		    goto cleanup;
		}
		result_units = get_empty_units();
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "arcsin" ||
		   ufunc_name == "arccos" ||
		   ufunc_name == "arctan" ||
		   ufunc_name == "arcsinh" ||
		   ufunc_name == "arccosh" ||
		   ufunc_name == "arctanh") {
	    if (_has_units(i0)) {
		tmp = PyUnicode_FromString("radians");
		if (tmp == NULL) {
		    goto cleanup;
		}
		result_units = (PyObject*)units_coerce(tmp);
		Py_DECREF(tmp);
		if (result_units == NULL) {
		    goto cleanup;
		}
		convert_units = get_empty_units();
		if (convert_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "degrees" ||
		   ufunc_name == "rad2deg") {
	    if (_has_units(i0)) {
		tmp = PyUnicode_FromString("radians");
		if (tmp == NULL) {
		    goto cleanup;
		}
		convert_units = (PyObject*)units_coerce(tmp);
		Py_DECREF(tmp);
		if (convert_units == NULL) {
		    goto cleanup;
		}
		tmp = PyUnicode_FromString("degrees");
		if (tmp == NULL) {
		    goto cleanup;
		}
		result_units = (PyObject*)units_coerce(tmp);
		Py_DECREF(tmp);
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "radians" ||
		   ufunc_name == "deg2rad") {
	    if (_has_units(i0)) {
		tmp = PyUnicode_FromString("degrees");
		if (tmp == NULL) {
		    goto cleanup;
		}
		convert_units = (PyObject*)units_coerce(tmp);
		Py_DECREF(tmp);
		if (convert_units == NULL) {
		    goto cleanup;
		}
		tmp = PyUnicode_FromString("radians");
		if (tmp == NULL) {
		    goto cleanup;
		}
		result_units = (PyObject*)units_coerce(tmp);
		Py_DECREF(tmp);
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else {
	    PyErr_Format(units_error,
			 "Unary operator '%s' not currently supported by rapidjson.units.QuantityArray.", ufunc_name.c_str());
	    goto cleanup;
	}
    } else if (Nargs == 2) { // binary operators
	i1 = PyTuple_GET_ITEM(normal_args, 1);
	if (i1 == NULL) {
	    goto cleanup;
	}
	if (ufunc_name == "copysign") {
	    // Strip units
	} else if (ufunc_name == "equal") {
	    res = _compare_units(i0, i1, true, true);
	    if (res < 0) {
		goto cleanup;
	    }
	    if (res != 1 &&
		PyObject_IsInstance(i0, (PyObject*)&PyArray_Type) &&
		PyObject_IsInstance(i1, (PyObject*)&PyArray_Type) &&
		PyArray_SAMESHAPE((PyArrayObject*)i0,
				  (PyArrayObject*)i1)) {
		result = PyArray_ZEROS(PyArray_NDIM((PyArrayObject*)i0),
				       PyArray_DIMS((PyArrayObject*)i0),
				       NPY_BOOL, 0);
		if (result == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "not_equal") {
	    res = _compare_units(i0, i1, true, true);
	    if (res < 0) {
		goto cleanup;
	    }
	    if (res != 1 &&
		PyObject_IsInstance(i0, (PyObject*)&PyArray_Type) &&
		PyObject_IsInstance(i1, (PyObject*)&PyArray_Type) &&
		PyArray_SAMESHAPE((PyArrayObject*)i0,
				  (PyArrayObject*)i1)) {
		tmp = PyArray_ZEROS(PyArray_NDIM((PyArrayObject*)i0),
				    PyArray_DIMS((PyArrayObject*)i0),
				    NPY_BOOL, 0);
		if (tmp == NULL) {
		    goto cleanup;
		}
		tmp2 = PyLong_FromLong(1);
		result = PyNumber_InPlaceAdd(tmp, tmp2);
		Py_DECREF(tmp);
		Py_DECREF(tmp2);
		if (result == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "greater" ||
		   ufunc_name == "greater_equal" ||
		   ufunc_name == "less" ||
		   ufunc_name == "less_equal" ||
		   ufunc_name == "hypot") {
	    // Require components have the same units
	    convert_units = _get_units(i0);
	    if (convert_units == NULL) {
		goto cleanup;
	    }
	} else if (ufunc_name == "add" ||
		   ufunc_name == "subtract" ||
		   ufunc_name == "maximum" ||
		   ufunc_name == "minimum" ||
		   ufunc_name == "fmax" ||
		   ufunc_name == "fmin") {
	    // Require components and result have the same units
	    result_units = _get_units(i0);
	    if (result_units == NULL) {
		goto cleanup;
	    }
	    convert_units = result_units;
	    Py_INCREF(result_units);
	} else if (ufunc_name == "multiply" ||
		   ufunc_name == "matmul" ||
		   ufunc_name == "divide" ||
		   ufunc_name == "true_divide" ||
		   ufunc_name == "floor_divide") {
	    i0_units = _get_units(i0);
	    if (i0_units == NULL) {
		goto cleanup;
	    }
	    if (!_has_units(i1)) {
		result_units = i0_units;
	    } else {
		i1_units = _get_units(i1);
		if (i1_units == NULL) {
		    Py_DECREF(i0_units);
		    goto cleanup;
		}
		if (ufunc_name.size() >= 6 &&
		    ufunc_name.substr(ufunc_name.size() - 6) == "divide") {
		    result_units = PyNumber_TrueDivide(i0_units, i1_units);
		} else {
		    result_units = PyNumber_Multiply(i0_units, i1_units);
		}
		Py_DECREF(i1_units);
		Py_DECREF(i0_units);
	    }
	    if (result_units == NULL) {
		goto cleanup;
	    }
	} else if (ufunc_name == "power" ||
		   ufunc_name == "float_power") {
	    if (_has_units(i1)) {
		PyErr_Format(units_error,
			     "Raise to a power with units not supported.");
		goto cleanup;
	    }
	    if (_has_units(i0)) {
		i0_units = _get_units(i0);
		if (i0_units == NULL) {
		    goto cleanup;
		}
		if (PyArray_Check(i1)) {
		    // TODO: Change to array of quantities with different units?
		    PyErr_Format(units_error,
				 "Cannot raise QuantityArray to heterogeneous"
				 " array of powers.");
		    Py_DECREF(i0_units);
		    goto cleanup;
		}
		result_units = PyNumber_Power(i0_units, i1, Py_None);
		Py_DECREF(i0_units);
		if (result_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "remainder" ||
		   ufunc_name == "mod" ||
		   ufunc_name == "fmod") {
	    if (_has_units(i0)) {
		result_units = _get_units(i0);
		if (result_units == NULL) {
		    goto cleanup;
		}
		if (_has_units(i1)) {
		    Py_INCREF(result_units);
		    convert_units = result_units;
		}
	    } else {
		convert_units = _get_units(i0);
		if (convert_units == NULL) {
		    goto cleanup;
		}
	    }
	} else if (ufunc_name == "arctan2") {
	    convert_units = _get_units(i0);
	    if (convert_units == NULL) {
		goto cleanup;
	    }
	    tmp = PyUnicode_FromString("radians");
	    if (tmp == NULL) {
		goto cleanup;
	    }
	    result_units = (PyObject*)units_coerce(tmp);
	    Py_DECREF(tmp);
	    if (result_units == NULL) {
		goto cleanup;
	    }
	} else {
	    PyErr_Format(units_error,
			 "Binary operator '%s' not currently supported by rapidjson.units.QuantityArray.", ufunc_name.c_str());
	    goto cleanup;
	}
    } else {
	PyErr_Format(units_error,
		     "Operator '%s' not currently supported by rapidjson.units.QuantityArray.", ufunc_name.c_str());
	goto cleanup;
    }
    if (result == NULL) {
	if (modified_args == NULL) {
	    modified_args = quantity_array_numpy_tuple(normal_args, false, convert_units);
	    if (modified_args == NULL) {
		goto cleanup;
	    }
	}
	if (modified_kwargs == NULL && kwargs != NULL) {
	    if (modified_out == NULL) {
		Py_INCREF(kwargs);
		modified_kwargs = kwargs;
	    } else {
		modified_kwargs = PyDict_New();
		if (modified_kwargs == NULL) {
		    goto cleanup;
		}
		kw_pos = 0;
		tmp = PyUnicode_FromString("out");
		while (PyDict_Next(kwargs, &kw_pos, &kw_key, &kw_val)) {
		    if (PyObject_RichCompareBool(kw_key, tmp, Py_EQ)) {
			if (PyDict_SetItem(modified_kwargs, kw_key, modified_out) < 0) {
			    Py_DECREF(tmp);
			    goto cleanup;
			}
		    } else {
			if (PyDict_SetItem(modified_kwargs, kw_key, kw_val) < 0) {
			    Py_DECREF(tmp);
			    goto cleanup;
			}
		    }
		}
		Py_DECREF(tmp);
	    }
	}
	ufunc_method = PyObject_GetAttr(ufunc, method_name);
	if (ufunc_method == NULL) {
	    goto cleanup;
	}
	result = PyObject_Call(ufunc_method, modified_args, modified_kwargs);
	Py_DECREF(ufunc_method);
    }
    if (result != NULL && result_units != NULL) {
	if (result_type == NULL) {
	    result_type = (PyObject*)&QuantityArray_Type;
	    Py_INCREF(result_type);
	}
	tmp = PyTuple_Pack(2, result, result_units);
	Py_DECREF(result);
	if (tmp == NULL) {
	    result = NULL;
	    goto cleanup;
	}
	result = PyObject_Call(result_type, tmp, NULL);
	Py_DECREF(tmp);
    }
cleanup:
    Py_DECREF(normal_args);
    Py_XDECREF(result_type);
    Py_XDECREF(result_units);
    Py_XDECREF(convert_units);
    Py_XDECREF(modified_out);
    Py_XDECREF(modified_args);
    Py_XDECREF(modified_kwargs);
    return result;
}

static PyObject* quantity_array__array_finalize__(PyObject* self, PyObject* args) {
    PyObject *attr = NULL;
    PyObject *parent = NULL;
    if (!PyArg_ParseTuple(args, "O", &parent)) {
	return NULL;
    }
    if (parent != NULL) {
	if (PyObject_HasAttrString(parent, "units")) {
	    attr = PyObject_GetAttrString(parent, "units");
	    if (attr == NULL) {
		return NULL;
	    }
	} else {
	    // parent has no 'units' so we make a new empty one
	    attr = get_empty_units();
	    if (attr == NULL) {
		return NULL;
	    }
	}
    } else {
	attr = get_empty_units();
    }
    
    ((QuantityArrayObject*)self)->units = (UnitsObject*)attr;
    Py_INCREF(Py_None);
    return Py_None;
}


static PyObject* quantity_array__array_wrap__(PyObject* self, PyObject* args) {
    PyObject *array = NULL, *context = NULL;
    if (!PyArg_ParseTuple(args, "OO", array, context)) {
	return NULL;
    }
    Py_INCREF(array);
    return array;
}

static PyObject* quantity_array__array_function__(PyObject* self, PyObject* c_args, PyObject* c_kwds) {
    PyObject *func, *func_name, *types, *args, *kwargs, *alt_c_args;
    PyObject* alt_args = NULL;
    PyObject *i0, *i1;
    int res;
    PyObject *result = NULL, *result_units = NULL, *convert_units = NULL;
    std::string func_nameS;
    static char const* kwlist[] = {"func", "types", "args", "kwargs", NULL};

    if (!PyArg_ParseTupleAndKeywords(
	    c_args, c_kwds, "OOOO:__array_function__", (char**) kwlist,
	    &func, &types, &args, &kwargs)) {
	return NULL;
    }
    
    func_name = PyObject_GetAttrString(func, "__name__");
    if (func_name == NULL) return NULL;
    func_nameS.insert(0, PyUnicode_AsUTF8(func_name));
    Py_DECREF(func_name);
    // std::cerr << "__array_function__: " << func_nameS << std::endl;
    if (func_nameS == "concatenate") {
	i0 = PyTuple_GetItem(args, 0);
	if (i0 == NULL) {
	    goto cleanup;
	}
	convert_units = _get_units(i0);
	if (convert_units == NULL) {
	    goto cleanup;
	}
	Py_INCREF(convert_units);
	result_units = convert_units;
    } else if (func_nameS == "array_equal" ||
	       func_nameS == "array_equiv" ||
	       func_nameS == "allclose") {
	res = _compare_units_tuple(args, true, true, &convert_units);
	if (res < 0) {
	    goto cleanup;
	} else if (res != 1) {
	    Py_INCREF(Py_False);
	    result = Py_False;
	    goto cleanup;
	}
    } else if (func_nameS == "isclose") {
	res = _compare_units_tuple(args, true, true, &convert_units);
	if (res < 0) {
	    goto cleanup;
	} else if (res != 1) {
	    i0 = PyTuple_GetItem(args, 0);
	    i1 = PyTuple_GetItem(args, 1);
	    if (i0 == NULL || i1 == NULL) {
		goto cleanup;
	    }
	    if (PyObject_IsInstance(i0, (PyObject*)&PyArray_Type) &&
		PyObject_IsInstance(i1, (PyObject*)&PyArray_Type) &&
		PyArray_SAMESHAPE((PyArrayObject*)i0,
				  (PyArrayObject*)i1)) {
		result = PyArray_ZEROS(PyArray_NDIM((PyArrayObject*)i0),
				       PyArray_DIMS((PyArrayObject*)i0),
				       NPY_BOOL, 0);
		goto cleanup;
	    }
	    // fallback to numpy for error if shapes mismatch
	}
    } else {
	    PyErr_Format(units_error,
			 "Array function '%s' not supported by rapidjson.units.QuantityArray", func_nameS.c_str());
	    goto cleanup;
    }
    if (result == NULL) {
	if (alt_args == NULL) {
	    alt_args = quantity_array_numpy_tuple(args, true, convert_units);
	    if (alt_args == NULL) {
		goto cleanup;
	    }
	}
	alt_c_args = PyTuple_Pack(4, func, types, alt_args, kwargs);
	if (alt_c_args == NULL) {
	    goto cleanup;
	}
	CALL_BASE_METHOD_ARGS_KWARGS(__array_function__, result,
				     alt_c_args, c_kwds);
	Py_DECREF(alt_c_args);
    }
    if (result != NULL && result_units != NULL) {
	PyObject* result_args = PyTuple_Pack(2, result, result_units);
	Py_DECREF(result);
	if (result_args == NULL) {
	    result = NULL;
	    goto cleanup;
	}
	// TODO: Determine out type to allow subclassing
	result = PyObject_Call((PyObject*)&QuantityArray_Type, result_args, NULL);
	Py_DECREF(result_args);
    }
cleanup:
    Py_XDECREF(result_units);
    Py_XDECREF(convert_units);
    Py_XDECREF(alt_args);
    return result;
}

static PyObject* quantity_array_subscript(PyObject* self, PyObject* key) {
    PyObject* out = NULL;
    CALL_BASE_METHOD(__getitem__, out, key)
    if (out == NULL || !PyObject_HasAttrString(out, "shape")) {
	return out;
    }
    PyObject* shape = PyObject_GetAttrString(out, "shape");
    if (shape == NULL) {
	Py_DECREF(out);
	return NULL;
    }
    Py_ssize_t ndim = PyTuple_Size(shape);
    Py_DECREF(shape);
    if (ndim != 0) {
	return out;
    }
    PyObject* units = quantity_array_units_get(self, NULL);
    if (units == NULL) {
	Py_DECREF(out);
	return NULL;
    }
    if (((UnitsObject*)units)->units->is_dimensionless() &&
	!((UnitsObject*)units)->units->has_factor()) {
	return out;
    }
    PyObject* args = PyTuple_Pack(2, out, units);
    Py_DECREF(out);
    Py_DECREF(units);
    PyObject* qout = PyObject_Call((PyObject*)&Quantity_Type, args, NULL);
    Py_DECREF(args);
    return qout;
}


static int quantity_array_ass_subscript(PyObject* self, PyObject* key, PyObject* val) {
    PyObject* mod_val = _convert_units(val, (PyObject*)(((QuantityArrayObject*)self)->units), true);
    PyObject* out_val = NULL;
    int out = 0;
    CALL_BASE_METHOD(__setitem__, out_val, key, mod_val);
    Py_DECREF(mod_val);
    if (out_val == NULL) {
	out = -1;
    }
    return out;
}


///////////////
// Utilities //
///////////////

static PyObject* _get_units(PyObject* x,
			    bool dont_allow_empty, bool force_copy) {
    PyObject* out = NULL;
    if (PyObject_IsInstance(x, (PyObject*)&QuantityArray_Type)) {
	if (force_copy) {
	    out = get_empty_units((PyObject*)(((QuantityArrayObject*)x)->units));
	    if (out == NULL) return NULL;
	} else {
	    out = (PyObject*)(((QuantityArrayObject*)x)->units);
	    Py_INCREF(out);
	}
    } else if (PyObject_IsInstance(x, (PyObject*)&Units_Type)) {
	if (force_copy) {
	    out = get_empty_units(x);
	    if (out == NULL) return NULL;
	} else {
	    out = (PyObject*)x;
	    Py_INCREF(out);
	}
    } else if (PyObject_HasAttrString(x, "units")) {
	PyObject* units_raw = PyObject_GetAttrString(x, "units");
	out = get_empty_units(units_raw);
	Py_DECREF(units_raw);
	if (out == NULL) return NULL;
    } else if (!dont_allow_empty) {
	out = get_empty_units();
	if (out == NULL) return NULL;
    }
    return out;
}


static int _has_units(PyObject* x) {
    return (int)(PyObject_IsInstance(x, (PyObject*)&Quantity_Type) ||
		 PyObject_IsInstance(x, (PyObject*)&QuantityArray_Type) ||
		 PyObject_IsInstance(x, (PyObject*)&Units_Type) ||
		 PyObject_HasAttrString(x, "units"));
}


static PyObject* _convert_units(PyObject* x, PyObject* units,
				bool stripUnits) {
    PyObject* out = NULL;
    if (PyObject_IsInstance(x, (PyObject*)&Quantity_Type)) {
	PyObject* args = PyTuple_Pack(1, units);
	if (args == NULL) {
	    return NULL;
	}
	out = quantity_to(x, args);
	Py_DECREF(args);
	if (out != NULL && stripUnits) {
	    PyObject* tmp = out;
	    out = quantity_value_get(tmp, NULL);
	    Py_DECREF(tmp);
	}
    } else if (PyObject_IsInstance(x, (PyObject*)&QuantityArray_Type)) {
	if (stripUnits) {
	    out = quantity_array_get_converted_value(x, units);
	} else {
	    PyObject* args = PyTuple_Pack(1, units);
	    if (args == NULL) {
		return NULL;
	    }
	    out = quantity_array_to(x, args);
	    Py_DECREF(args);
	}
    } else if (PyObject_HasAttrString(x, "units")) {
	PyErr_SetString(units_error, "Unknown unit type");
	return NULL;
    } else {
	Py_INCREF(x);
	out = x;
    }
    return out;
}


static int _compare_units(PyObject* x0, PyObject* x1, bool allowCompat,
			  bool dimensionlessCompat) {
    UnitsObject *x0_units = NULL, *x1_units = NULL;
    if (x0 != NULL && _has_units(x0)) {
	x0_units = (UnitsObject*)_get_units(x0);
	if (x0_units == NULL) return -1;
    }
    if (x1 != NULL && _has_units(x1)) {
	x1_units = (UnitsObject*)_get_units(x1);
	if (x1_units == NULL) {
	    Py_DECREF(x0_units);
	    return -1;
	}
    }
    int out = 0;
    if (x0_units != NULL && x1_units != NULL) {
	if (allowCompat) {
	    out = (int)(x0_units->units->is_compatible(*(x1_units->units)));
	} else {
	    out = (int)(*(x0_units->units) == *(x1_units->units));
	}
    } else if ((x0_units == NULL && x1_units == NULL) ||
	       dimensionlessCompat) {
	out = 1;
    } else if (x0_units != NULL && x1_units == NULL) {
	
	out = (int)(x0_units->units->is_null() && !x0_units->units->has_factor());
    } else if (x0_units == NULL && x1_units != NULL) {
	out = (int)(x1_units->units->is_null() && !x1_units->units->has_factor());
    }
    Py_XDECREF(x0_units);
    Py_XDECREF(x1_units);
    return out;
}


static int _compare_units_tuple(PyObject* x, bool allowCompat,
				bool dimensionlessCompat,
				PyObject** out_units) {
    UnitsObject* units = NULL;
    PyObject* item = NULL;
    int res;
    if (out_units != NULL) out_units[0] = NULL;
    for (Py_ssize_t i = 0; i < PyTuple_Size(x); i++) {
	item = PyTuple_GetItem(x, i);
	if (item == NULL) return -1;
	if (i == 0 && _has_units(item)) {
	    units = (UnitsObject*)_get_units(item);
	}
	res = _compare_units((PyObject*)units, item, allowCompat,
			     dimensionlessCompat);
	if (res < 0) {
	    Py_XDECREF(units);
	    return -1;
	} else if (res == 0) {
	    Py_XDECREF(units);
	    return 0;
	}
    }
    if (out_units != NULL && units != NULL) {
	out_units[0] = (PyObject*)units;
	Py_INCREF(units);
    }
    Py_XDECREF(units);
    return 1;
}


////////////
// Module //
////////////


static PyMethodDef units_functions[] = {
    {NULL, NULL, 0, NULL} /* sentinel */
};


static int
units_module_exec(PyObject* m)
{
    if (sizeof(PyArrayObject) > (size_t)QuantityArray_Type.tp_basicsize) {
	PyErr_SetString(PyExc_ImportError,
			"Binary incompatibility with NumPy, must recompile/update X.");
	return -1;
    }
    if (PyType_Ready(&Units_Type) < 0)
        return -1;

    if (PyType_Ready(&Quantity_Type) < 0)
        return -1;

    Py_INCREF(&PyArray_Type);
    QuantityArray_Type.tp_base = &PyArray_Type;
    if (PyType_Ready(&QuantityArray_Type) < 0)
        return -1;

#define STRINGIFY(x) XSTRINGIFY(x)
#define XSTRINGIFY(x) #x

    if (PyModule_AddStringConstant(m, "__version__",
				   STRINGIFY(PYTHON_RAPIDJSON_VERSION))
        || PyModule_AddStringConstant(m, "__author__",
				      "Meagan Lang <langmm.astro@gmail.com>")
        || PyModule_AddStringConstant(m, "__rapidjson_version__",
                                      RAPIDJSON_VERSION_STRING)
#ifdef RAPIDJSON_EXACT_VERSION
        || PyModule_AddStringConstant(m, "__rapidjson_exact_version__",
                                      STRINGIFY(RAPIDJSON_EXACT_VERSION))
#endif
        )
        return -1;

    Py_INCREF(&Units_Type);
    if (PyModule_AddObject(m, "Units", (PyObject*) &Units_Type) < 0) {
        Py_DECREF(&Units_Type);
        return -1;
    }

    Py_INCREF(&Quantity_Type);
    if (PyModule_AddObject(m, "Quantity", (PyObject*) &Quantity_Type) < 0) {
        Py_DECREF(&Quantity_Type);
        return -1;
    }

    Py_INCREF(&QuantityArray_Type);
    if (PyModule_AddObject(m, "QuantityArray", (PyObject*) &QuantityArray_Type) < 0) {
        Py_DECREF(&QuantityArray_Type);
        return -1;
    }

    units_error = PyErr_NewException("rapidjson.UnitsError",
				     PyExc_ValueError, NULL);
    if (units_error == NULL)
        return -1;
    Py_INCREF(units_error);
    if (PyModule_AddObject(m, "UnitsError", units_error) < 0) {
        Py_DECREF(units_error);
        return -1;
    }

    return 0;
}


static struct PyModuleDef_Slot units_slots[] = {
    {Py_mod_exec, (void*) units_module_exec},
    {0, NULL}
};


static PyModuleDef units_module = {
    PyModuleDef_HEAD_INIT,      /* m_base */
    "units",                    /* m_name */
    PyDoc_STR("Fast, simple units library developed for yggdrasil."),
    0,                          /* m_size */
    units_functions,            /* m_methods */
    units_slots,                /* m_slots */
    NULL,                       /* m_traverse */
    NULL,                       /* m_clear */
    NULL                        /* m_free */
};


PyMODINIT_FUNC
PyInit_units()
{
    return PyModuleDef_Init(&units_module);
}
