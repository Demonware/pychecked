"""Python type checking for annotated function signatures.

This will raise SyntaxErrors if you use it with Python2, however, there are no
checks in place to prevent you from trying (maybe the syntax will be backported
someday, who knows).

Usage is through the wrap @type_checked and configuration through the static
object Config.

Please see the tests in the test directory or the README.md for usage examples.

Copyright (c) 2014, Activision Publishing, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of Activision Publishing, Inc. nor the names of its
  contributors may be used to endorse or promote products derived from this
  software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


import sys
import inspect
import functools


class ConfigDict(dict):
    """Subclass dict to ensure we don't allow additional keys.

    It is still possible, but not through kwargs to the wrap. You could however
    import this dict somewhere else and call .update() on it to run tests on it
    """

    def __setitem__(self, key, value):
        if not key in self:
            raise ValueError("{} is not a valid config key.".format(key))

        # might have to define these somewhere should more options come in
        if isinstance(value, bool):
            return dict.__setitem__(self, key, value)
        else:
            raise ValueError("{} is not a valid config value.".format(value))


class Config(object):
    """The @type_checked static Config object.

    You can access the config dictionary through Config.config(). Typically
    speaking though, you would pass kwargs to the wrap on the first function
    your application runs, then from there the settings will be stored.

    Configuration Keys::

        coerce: boolean to try to mutate the values into the type requested
        debug: boolean to print to stderr Value or Type errors that were caught
    """

    @staticmethod
    def get(key, default=None):
        """Return the value for a key."""

        return Config.config().get(key, default)

    @staticmethod
    def set(key, value):
        """Set a value for a key."""

        Config.config()[key] = value

    @staticmethod
    def config():
        """Returns the static config dictionary object. Mutate at will."""

        if not hasattr(Config, "_config"):
            # default settings as kwargs
            Config._config = ConfigDict(active=True, coerce=True, debug=False)

        return Config._config


def type_checked(func=None, **kwargs):
    """Wrapper to indicate we want to have the function type checked.

    KWargs:
        Any of the Config options can be passed at any time as kwargs.
    """

    if func is None:
        return functools.partial(type_checked, **kwargs)

    @functools.wraps(func)
    def _type_checked(*args, **kwargs):
        """Go through the function's passed arguments and validate them."""

        if not Config.get("active"):
            # shortcut to facilitate easier performance testing
            return func(*args, **kwargs)

        v_args = []
        v_kwargs = {}

        annotations = getattr(func, "__annotations__", {})
        func_sig = inspect.getfullargspec(func)

        for i, arg in enumerate(args):
            try:
                arg_name = func_sig.args[i]
            except IndexError:
                arg_name = func_sig.varargs  # this arg is a *arg

            if arg_name in annotations:
                v_args.append(_do_validation(annotations[arg_name], arg))
            else:
                v_args.append(arg)

        for kwarg, kwvalue in kwargs.items():
            if kwarg in annotations:  # any kwarg may or may not be annotated
                v_kwargs[kwarg] = _do_validation(annotations[kwarg], kwvalue)
            elif kwarg not in func_sig.args and func_sig.varkw in annotations:
                # if this isnt a defined kwarg but **kwargs is annotated
                v_kwargs[kwarg] = _do_validation(
                    annotations[func_sig.varkw],
                    kwvalue,
                )

        kwargs.update(v_kwargs)
        return func(*v_args, **kwargs)

    # allows the passing through kwargs to the wrap to adjust config that way
    for key, value in kwargs.items():
        Config.set(key, value)

    return _type_checked


def _do_validation(type_, value):
    """Perform the actual type checking validation using settings in Config.

    Args::

        type_: the type or callable to compare value against
        value: the object to compare with

    Returns:
        value, possible coerced to type_

    Raises::

        ValueError on incorrect/not-callable type_ to validate with
        TypeError when value is not type_ and/or cannot be coerced
    """

    def _raise_error():
        if hasattr(type_, "__name__"):
            type_name = type_.__name__
        elif hasattr(type_, "__iter__"):
            type_name = "a {} of {}".format(
                type_.__class__.__name__,
                ", ".join([subtype.__name__ for subtype in type_]),
            )
        else:
            type_name = type_.__class__.__name__

        raise TypeError("{} is of type {}, expecting {}.".format(
            value, type(value).__name__, type_name))

    def _log(message):
        if Config.get("debug"):
            print(message, file=sys.stderr)

    # need to check for built in syntically defined type first
    if type_ == []:
        type_ = list
    elif type_ == {}:
        type_ = dict

    # short circut for builtins and metaclasses
    if isinstance(type_, type):
        # check for boolean first b/c isinstance(False, int) == True
        is_bool = isinstance(value, bool)
        if (is_bool and value is type_) or \
           (not is_bool and isinstance(value, type_)):
            return value
        elif not Config.get("coerce"):
            # depending how strict you want to be you might want to raise
            _raise_error()

    if isinstance(type_, dict) and isinstance(value, dict):
        for key_, value_ in type_.items():
            key_type = key_
            value_type = value_
            break
        else:
            # only required to match value to dict, not dict key/values as well
            return value

        validated_values = {}
        for key_, value_ in value.items():
            validated_values[_do_validation(key_type, key_)] = _do_validation(
                value_type, value_)
        return type(type_)(validated_values)
    elif isinstance(type_, (list, tuple)):
        if not isinstance(value, (list, tuple)):
            if Config.get("coerce"):
                if isinstance(value, (str, int, bytes, complex)):
                    value = [value]
                else:
                    try:
                        value = list(value)
                    except (ValueError, TypeError) as error:
                        _log(error)
                        _raise_error()
            else:
                _raise_error()
        if len(type_) == len(value):
            validated_values = []
            for _type, _value in zip(type_, value):
                validated_values.append(_do_validation(_type, _value))
            return type(type_)(validated_values)
        elif len(type_) == 1:  # allows for list of ints, eg `foo:[int]`
            validated_values = []
            for val in value:
                validated_values.append(_do_validation(type_[0], val))
            return validated_values
        else:
            raise TypeError(
                "Argument length mismatch. Expected a {} of {}.".format(
                    type_.__class__.__name__,
                    ", ".join([t.__name__ for t in type_]),
                ))
    elif type_ is str and isinstance(value, bytes):
        return value.decode()
    elif callable(type_):  # last chance try with callable coercion
        try:
            return type_(value)
        except (ValueError, TypeError) as error:
            _log(error)
            # shim in flexability for float->int coercion
            if type_ is int and Config.get("coerce"):
                try:
                    return int(float(value))
                except (ValueError, TypeError) as error_:
                    _log(error_)
            _raise_error()
    elif type(type_) in [list, tuple]:  # if we make it this far it's an error
        _raise_error()
    else:
        raise ValueError("type {} is not a type or callable.".format(type_))
