/* ------------------------------------------------------------------------- */

/* (C) Copyright 2010-2011 New Relic Inc. All rights reserved. */

/* ------------------------------------------------------------------------- */

#include "py_settings.h"

#include "globals.h"
#include "logging.h"

#include "daemon_protocol.h"

/* ------------------------------------------------------------------------- */

static PyObject *NRTracerSettings_new(PyTypeObject *type, PyObject *args,
                                      PyObject *kwds)
{
    NRTracerSettingsObject *self;

    self = (NRTracerSettingsObject *)type->tp_alloc(type, 0);

    if (!self)
        return NULL;

    self->transaction_threshold = 0;
    self->transaction_threshold_is_apdex_f = 1;

    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static void NRTracerSettings_dealloc(NRTracerSettingsObject *self)
{
    PyObject_Del(self);
}

/* ------------------------------------------------------------------------- */

static PyObject *NRTracerSettings_get_enabled(NRTracerSettingsObject *self,
                                              void *closure)
{
    return PyBool_FromLong(nr_per_process_globals.tt_enabled);
}

/* ------------------------------------------------------------------------- */

static int NRTracerSettings_set_enabled(NRTracerSettingsObject *self,
                                        PyObject *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "can't delete enabled attribute");
        return -1;
    }

    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "expected bool for enabled");
        return -1;
    }

    if (value == Py_True)
        nr_per_process_globals.tt_enabled = 1;
    else
        nr_per_process_globals.tt_enabled = 0;

    return 0;
}

/* ------------------------------------------------------------------------- */

static PyObject *NRTracerSettings_get_threshold(NRTracerSettingsObject *self,
                                                void *closure)
{
    /*
     * We use a None value to indicate that threshold is being
     * calculated from apdex_f value.
     */

    /*
     * TODO Use of global for transaction_threshold is broken in the
     * PHP agent core. We need to workaround that by storing the
     * values in this object and updating transaction threshold
     * values on each request before distilling metrics. See
     * https://www.pivotaltracker.com/story/show/12771611.
     */

#if 0
    if (nr_per_process_globals.tt_threshold_is_apdex_f) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    return PyFloat_FromDouble((double)
            nr_per_process_globals.tt_threshold/1000000.0);
#endif

    if (self->transaction_threshold_is_apdex_f) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    return PyFloat_FromDouble((double)self->transaction_threshold/1000000.0);
}

/* ------------------------------------------------------------------------- */

static int NRTracerSettings_set_threshold(NRTracerSettingsObject *self,
                                          PyObject *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError,
                        "can't delete transaction_threshold attribute");
        return -1;
    }

    if (value != Py_None && !PyFloat_Check(value) && !PyInt_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "expected int, float or None for "
                        "transaction_threshold");
        return -1;
    }

    /*
     * We use a None value to indicate that threshold should be
     * set based on apdex_f calculation. Need to ensure flag it
     * is apdex calculation so that retreival of value also
     * returns None in that case. For case where actual time
     * value is used, we accept value in seconds and PHP agent
     * core expects microseconds so need to adjust appropriately.
     */

    /*
     * TODO Use of global for transaction_threshold is broken in the
     * PHP agent core. We need to workaround that by storing the
     * values in this object and updating transaction threshold
     * values on each request before distilling metrics. See
     * https://www.pivotaltracker.com/story/show/12771611.
     */

#if 0
    if (value == Py_None) {
        nr_per_process_globals.tt_threshold_is_apdex_f = 1;
        nr_initialize_global_tt_threshold_from_apdex(NULL);
    }
    else {
        nr_per_process_globals.tt_threshold_is_apdex_f = 0;
        if (PyFloat_Check(value))
            nr_per_process_globals.tt_threshold = PyFloat_AsDouble(value) * 1000000;
        else
            nr_per_process_globals.tt_threshold = PyInt_AsLong(value) * 1000000;
        if (nr_per_process_globals.tt_threshold < 0)
            nr_per_process_globals.tt_threshold = 0;
    }
#endif

    if (value == Py_None) {
        self->transaction_threshold_is_apdex_f = 1;
        self->transaction_threshold = 0;
    }
    else {
        self->transaction_threshold_is_apdex_f = 0;
        if (PyFloat_Check(value))
            self->transaction_threshold = PyFloat_AsDouble(value) * 1000000;
        else
            self->transaction_threshold = PyInt_AsLong(value) * 1000000;
        if (self->transaction_threshold < 0)
            self->transaction_threshold = 0;
    }

    return 0;
}

/* ------------------------------------------------------------------------- */

static PyObject *NRTracerSettings_get_record_sql(NRTracerSettingsObject *self,
                                                 void *closure)
{
    return PyInt_FromLong(nr_per_process_globals.tt_recordsql);
}

/* ------------------------------------------------------------------------- */

static int NRTracerSettings_set_record_sql(NRTracerSettingsObject *self,
                                           PyObject *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "can't delete record_sql attribute");
        return -1;
    }

    if (!PyInt_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "expected int for record_sql");
        return -1;
    }

    nr_per_process_globals.tt_recordsql = PyInt_AsLong(value);

    return 0;
}

/* ------------------------------------------------------------------------- */

static PyObject *NRTracerSettings_get_sql_threshold(
        NRTracerSettingsObject *self, void *closure)
{
    return PyFloat_FromDouble((double)
            nr_per_process_globals.slow_sql_stacktrace/1000000.0);
}

/* ------------------------------------------------------------------------- */

static int NRTracerSettings_set_sql_threshold(NRTracerSettingsObject *self,
                                              PyObject *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError,
                        "can't delete stack_trace_threshold attribute");
        return -1;
    }

    if (!PyFloat_Check(value) && !PyInt_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "expected int or float for "
                        "stack_transaction_threshold");
        return -1;
    }

    if (PyFloat_Check(value)) {
        nr_per_process_globals.slow_sql_stacktrace =
                PyFloat_AsDouble(value) * 1000000;
    }
    else {
        nr_per_process_globals.slow_sql_stacktrace =
                PyInt_AsLong(value) * 1000000;
    }

    if (nr_per_process_globals.slow_sql_stacktrace < 0)
        nr_per_process_globals.slow_sql_stacktrace = 0;

    return 0;
}

/* ------------------------------------------------------------------------- */

#ifndef PyVarObject_HEAD_INIT
#define PyVarObject_HEAD_INIT(type, size) PyObject_HEAD_INIT(type) size,
#endif

static PyMethodDef NRTracerSettings_methods[] = {
    { NULL, NULL }
};

static PyGetSetDef NRTracerSettings_getset[] = {
    { "enabled",            (getter)NRTracerSettings_get_enabled,
                            (setter)NRTracerSettings_set_enabled, 0 },
    { "transaction_threshold", (getter)NRTracerSettings_get_threshold,
                            (setter)NRTracerSettings_set_threshold, 0 },
    { "record_sql",         (getter)NRTracerSettings_get_record_sql,
                            (setter)NRTracerSettings_set_record_sql, 0 },
    { "stack_trace_threshold", (getter)NRTracerSettings_get_sql_threshold,
                            (setter)NRTracerSettings_set_sql_threshold, 0 },
    { NULL },
};

PyTypeObject NRTracerSettings_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_newrelic.TracerSettings", /*tp_name*/
    sizeof(NRTracerSettingsObject), /*tp_basicsize*/
    0,                      /*tp_itemsize*/
    /* methods */
    (destructor)NRTracerSettings_dealloc, /*tp_dealloc*/
    0,                      /*tp_print*/
    0,                      /*tp_getattr*/
    0,                      /*tp_setattr*/
    0,                      /*tp_compare*/
    0,                      /*tp_repr*/
    0,                      /*tp_as_number*/
    0,                      /*tp_as_sequence*/
    0,                      /*tp_as_mapping*/
    0,                      /*tp_hash*/
    0,                      /*tp_call*/
    0,                      /*tp_str*/
    0,                      /*tp_getattro*/
    0,                      /*tp_setattro*/
    0,                      /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,     /*tp_flags*/
    0,                      /*tp_doc*/
    0,                      /*tp_traverse*/
    0,                      /*tp_clear*/
    0,                      /*tp_richcompare*/
    0,                      /*tp_weaklistoffset*/
    0,                      /*tp_iter*/
    0,                      /*tp_iternext*/
    NRTracerSettings_methods,     /*tp_methods*/
    0,                      /*tp_members*/
    NRTracerSettings_getset,      /*tp_getset*/
    0,                      /*tp_base*/
    0,                      /*tp_dict*/
    0,                      /*tp_descr_get*/
    0,                      /*tp_descr_set*/
    0,                      /*tp_dictoffset*/
    0,                      /*tp_init*/
    0,                      /*tp_alloc*/
    NRTracerSettings_new,         /*tp_new*/
    0,                      /*tp_free*/
    0,                      /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */

static PyObject *NRErrorsSettings_new(PyTypeObject *type, PyObject *args,
                                      PyObject *kwds)
{
    NRErrorsSettingsObject *self;

    self = (NRErrorsSettingsObject *)type->tp_alloc(type, 0);

    if (!self)
        return NULL;

    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static void NRErrorsSettings_dealloc(NRErrorsSettingsObject *self)
{
    PyObject_Del(self);
}

/* ------------------------------------------------------------------------- */

static PyObject *NRErrorsSettings_get_enabled(NRErrorsSettingsObject *self,
                                              void *closure)
{
    return PyBool_FromLong(nr_per_process_globals.tt_enabled);
}

/* ------------------------------------------------------------------------- */

static int NRErrorsSettings_set_enabled(NRErrorsSettingsObject *self,
                                        PyObject *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "can't delete enabled attribute");
        return -1;
    }

    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "expected bool for enabled");
        return -1;
    }

    if (value == Py_True)
        nr_per_process_globals.errors_enabled = 1;
    else
        nr_per_process_globals.errors_enabled = 0;

    return 0;
}

/* ------------------------------------------------------------------------- */

#ifndef PyVarObject_HEAD_INIT
#define PyVarObject_HEAD_INIT(type, size) PyObject_HEAD_INIT(type) size,
#endif

static PyMethodDef NRErrorsSettings_methods[] = {
    { NULL, NULL }
};

static PyGetSetDef NRErrorsSettings_getset[] = {
    { "enabled",            (getter)NRErrorsSettings_get_enabled,
                            (setter)NRErrorsSettings_set_enabled, 0 },
    { NULL },
};

PyTypeObject NRErrorsSettings_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_newrelic.ErrorsSettings", /*tp_name*/
    sizeof(NRErrorsSettingsObject), /*tp_basicsize*/
    0,                      /*tp_itemsize*/
    /* methods */
    (destructor)NRErrorsSettings_dealloc, /*tp_dealloc*/
    0,                      /*tp_print*/
    0,                      /*tp_getattr*/
    0,                      /*tp_setattr*/
    0,                      /*tp_compare*/
    0,                      /*tp_repr*/
    0,                      /*tp_as_number*/
    0,                      /*tp_as_sequence*/
    0,                      /*tp_as_mapping*/
    0,                      /*tp_hash*/
    0,                      /*tp_call*/
    0,                      /*tp_str*/
    0,                      /*tp_getattro*/
    0,                      /*tp_setattro*/
    0,                      /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,     /*tp_flags*/
    0,                      /*tp_doc*/
    0,                      /*tp_traverse*/
    0,                      /*tp_clear*/
    0,                      /*tp_richcompare*/
    0,                      /*tp_weaklistoffset*/
    0,                      /*tp_iter*/
    0,                      /*tp_iternext*/
    NRErrorsSettings_methods,     /*tp_methods*/
    0,                      /*tp_members*/
    NRErrorsSettings_getset,      /*tp_getset*/
    0,                      /*tp_base*/
    0,                      /*tp_dict*/
    0,                      /*tp_descr_get*/
    0,                      /*tp_descr_set*/
    0,                      /*tp_dictoffset*/
    0,                      /*tp_init*/
    0,                      /*tp_alloc*/
    NRErrorsSettings_new,         /*tp_new*/
    0,                      /*tp_free*/
    0,                      /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */

static PyObject *NRSettingsObject_instance = NULL;

/* ------------------------------------------------------------------------- */

PyObject *NRSettings_Singleton(void)
{
    if (!NRSettingsObject_instance) {
        NRSettingsObject_instance = PyObject_CallFunctionObjArgs(
                (PyObject *)&NRSettings_Type, NULL);

        if (NRSettingsObject_instance == NULL)
            return NULL;
    }

    Py_INCREF(NRSettingsObject_instance);

    return NRSettingsObject_instance;
}

/* ------------------------------------------------------------------------- */

static PyObject *NRSettings_new(PyTypeObject *type, PyObject *args,
                                PyObject *kwds)
{
    NRSettingsObject *self;

    self = (NRSettingsObject *)type->tp_alloc(type, 0);

    if (!self)
        return NULL;

    self->tracer_settings = (NRTracerSettingsObject *)
            PyObject_CallFunctionObjArgs(
            (PyObject *)&NRTracerSettings_Type, NULL);
    self->errors_settings = (NRErrorsSettingsObject *)
            PyObject_CallFunctionObjArgs(
            (PyObject *)&NRErrorsSettings_Type, NULL);

    self->monitor_mode = 1;
    self->ignored_params = PyList_New(0);

    return (PyObject *)self;
}

/* ------------------------------------------------------------------------- */

static void NRSettings_dealloc(NRSettingsObject *self)
{
    Py_DECREF(self->ignored_params);

    Py_DECREF(self->tracer_settings);
    Py_DECREF(self->errors_settings);

    PyObject_Del(self);
}

/* ------------------------------------------------------------------------- */

static PyObject *NRSettings_get_app_name(NRSettingsObject *self, void *closure)
{
    if (nr_per_process_globals.appname)
        return PyString_FromString(nr_per_process_globals.appname);

    Py_INCREF(Py_None);
    return Py_None;
}

/* ------------------------------------------------------------------------- */

static int NRSettings_set_app_name(NRSettingsObject *self, PyObject *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "can't delete app_name attribute");
        return -1;
    }

    if (!PyString_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "expected string for app_name");
        return -1;
    }

    if (nr_per_process_globals.appname)
        nrfree(nr_per_process_globals.appname);

    nr_per_process_globals.appname = nrstrdup(PyString_AsString(value));

    return 0;
}

/* ------------------------------------------------------------------------- */

static PyObject *NRSettings_get_monitor_mode(NRSettingsObject *self,
                                             void *closure)
{
    return PyBool_FromLong(self->monitor_mode);
}

/* ------------------------------------------------------------------------- */

static int NRSettings_set_monitor_mode(NRSettingsObject *self, PyObject *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "can't delete monitor_mode attribute");
        return -1;
    }

    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "expected bool for monitor_mode");
        return -1;
    }

    if (value == Py_True)
        self->monitor_mode = 1;
    else
        self->monitor_mode = 0;

    return 0;
}

/* ------------------------------------------------------------------------- */

static PyObject *NRSettings_get_log_file(NRSettingsObject *self, void *closure)
{
    if (nr_per_process_globals.logfilename)
        return PyString_FromString(nr_per_process_globals.logfilename);

    Py_INCREF(Py_None);
    return Py_None;
}

/* ------------------------------------------------------------------------- */

static int NRSettings_set_log_file(NRSettingsObject *self, PyObject *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "can't delete log_file attribute");
        return -1;
    }

    if (!PyString_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "expected string for log_file");
        return -1;
    }

    if (nr_per_process_globals.logfilename)
        nrfree(nr_per_process_globals.logfilename);

    nr_per_process_globals.logfilename = nrstrdup(PyString_AsString(value));

    return 0;
}

/* ------------------------------------------------------------------------- */

static PyObject *NRSettings_get_log_level(NRSettingsObject *self, void *closure)
{
    return PyInt_FromLong(nr_per_process_globals.loglevel);
}

/* ------------------------------------------------------------------------- */

static int NRSettings_set_log_level(NRSettingsObject *self, PyObject *value)
{
    int log_level;

    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "can't delete log_level attribute");
        return -1;
    }

    if (!PyInt_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "expected integer for log_level");
        return -1;
    }

    log_level = PyInt_AsLong(value);

    /*
     * Constrain value as LOG_DUMP level in PHP code appears to
     * have problems and can get stuck in loop dumping lots of
     * blank lines into log file.
     */

    if (log_level < LOG_ERROR || log_level > LOG_VERBOSEDEBUG) {
        PyErr_SetString(PyExc_ValueError, "log level out of range");
        return -1;
    }

    nr_per_process_globals.loglevel = log_level;

    return 0;
}

/* ------------------------------------------------------------------------- */

static PyObject *NRSettings_get_capture_params(NRSettingsObject *self,
                                               void *closure)
{
    return PyInt_FromLong(nr_per_process_globals.enable_params);
}

/* ------------------------------------------------------------------------- */

static int NRSettings_set_capture_params(NRSettingsObject *self,
                                         PyObject *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError,
                        "can't delete capture_params attribute");
        return -1;
    }

    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "expected bool for capture_params");
        return -1;
    }

    if (value == Py_True)
        nr_per_process_globals.enable_params = 1;
    else
        nr_per_process_globals.enable_params = 0;

    return 0;
}

/* ------------------------------------------------------------------------- */

static PyObject *NRSettings_get_ignored_params(NRSettingsObject *self,
                                               void *closure)
{
    Py_INCREF(self->ignored_params);
    return self->ignored_params;
}

/* ------------------------------------------------------------------------- */

static int NRSettings_set_ignored_params(NRSettingsObject *self,
                                         PyObject *value)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError,
                        "can't delete ignored_params attribute");
        return -1;
    }

    if (!PyList_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "expected list for ignored_params");
        return -1;
    }

    Py_INCREF(value);
    Py_DECREF(self->ignored_params);
    self->ignored_params = value;

    return 0;
}

/* ------------------------------------------------------------------------- */

static PyObject *NRSettings_get_transaction_tracer(NRSettingsObject *self,
                                                   void *closure)
{
    Py_INCREF(self->tracer_settings);
    return (PyObject *)self->tracer_settings;
}

/* ------------------------------------------------------------------------- */

static PyObject *NRSettings_get_error_collector(NRSettingsObject *self,
                                                void *closure)
{
    Py_INCREF(self->errors_settings);
    return (PyObject *)self->errors_settings;
}

/* ------------------------------------------------------------------------- */

#ifndef PyVarObject_HEAD_INIT
#define PyVarObject_HEAD_INIT(type, size) PyObject_HEAD_INIT(type) size,
#endif

static PyMethodDef NRSettings_methods[] = {
    { NULL, NULL }
};

static PyGetSetDef NRSettings_getset[] = {
    { "app_name",           (getter)NRSettings_get_app_name,
                            (setter)NRSettings_set_app_name, 0 },
    { "monitor_mode",       (getter)NRSettings_get_monitor_mode,
                            (setter)NRSettings_set_monitor_mode, 0 },
    { "log_file",           (getter)NRSettings_get_log_file,
                            (setter)NRSettings_set_log_file, 0 },
    { "log_level",          (getter)NRSettings_get_log_level,
                            (setter)NRSettings_set_log_level, 0 },
    { "capture_params",     (getter)NRSettings_get_capture_params,
                            (setter)NRSettings_set_capture_params, 0 },
    { "ignored_params",     (getter)NRSettings_get_ignored_params,
                            (setter)NRSettings_set_ignored_params, 0 },
    { "transaction_tracer", (getter)NRSettings_get_transaction_tracer,
                            NULL, 0 },
    { "error_collector",    (getter)NRSettings_get_error_collector,
                            NULL, 0 },
    { NULL },
};

PyTypeObject NRSettings_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "_newrelic.Settings", /*tp_name*/
    sizeof(NRSettingsObject), /*tp_basicsize*/
    0,                      /*tp_itemsize*/
    /* methods */
    (destructor)NRSettings_dealloc, /*tp_dealloc*/
    0,                      /*tp_print*/
    0,                      /*tp_getattr*/
    0,                      /*tp_setattr*/
    0,                      /*tp_compare*/
    0,                      /*tp_repr*/
    0,                      /*tp_as_number*/
    0,                      /*tp_as_sequence*/
    0,                      /*tp_as_mapping*/
    0,                      /*tp_hash*/
    0,                      /*tp_call*/
    0,                      /*tp_str*/
    0,                      /*tp_getattro*/
    0,                      /*tp_setattro*/
    0,                      /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,     /*tp_flags*/
    0,                      /*tp_doc*/
    0,                      /*tp_traverse*/
    0,                      /*tp_clear*/
    0,                      /*tp_richcompare*/
    0,                      /*tp_weaklistoffset*/
    0,                      /*tp_iter*/
    0,                      /*tp_iternext*/
    NRSettings_methods,     /*tp_methods*/
    0,                      /*tp_members*/
    NRSettings_getset,      /*tp_getset*/
    0,                      /*tp_base*/
    0,                      /*tp_dict*/
    0,                      /*tp_descr_get*/
    0,                      /*tp_descr_set*/
    0,                      /*tp_dictoffset*/
    0,                      /*tp_init*/
    0,                      /*tp_alloc*/
    NRSettings_new,         /*tp_new*/
    0,                      /*tp_free*/
    0,                      /*tp_is_gc*/
};

/* ------------------------------------------------------------------------- */

/*
 * vim: set cino=>2,e0,n0,f0,{2,}0,^0,\:2,=2,p2,t2,c1,+2,(2,u2,)20,*30,g2,h2 ts=8
 */
