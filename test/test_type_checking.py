"""Tests for pychecked.

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
import pytest

from pychecked.type_checking import Config
from pychecked.type_checking import type_checked


# some dummy objects to test with
class TestObj(object): pass

class NestObj(TestObj): pass

class MyObject(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

class MySubClassedObject(MyObject):
    def __init__(self, x_y):
        super(MySubClassedObject, self).__init__(*x_y)


@pytest.fixture(autouse=True)
def reset_config():
    """Ensure the default config settings are in place prior to a test run."""

    Config.config().update({"coerce": True, "debug": True, "active": True})


def test_nested():
    """If there is a len mismatch, the first type is used for all values."""

    @type_checked
    def _run_test(something:[str]):
        for item in something:
            assert isinstance(item, str)

    _run_test(["some", "thing", "and", 23, "stuff", 11])


def test_tuples():
    """Should be able to specify all positional elements in a tuple."""

    @type_checked
    def _run_test(something:(str, int, bool)):
        assert isinstance(something[0], str)
        assert isinstance(something[1], int)
        assert isinstance(something[2], bool)

    _run_test(something=(None, "12", 1))


def test_list_of_equal_len():
    """Should be able to do the same with a list."""

    @type_checked
    def _run_test(something:[str, int, bool]):
        assert isinstance(something[0], str)
        assert isinstance(something[1], int)
        assert isinstance(something[2], bool)

    _run_test(something=[None, "12", 1])


def test_dictionary_coerce():
    """We should be able to coerce both keys and values."""

    @type_checked
    def _run_test(something:{int: str}):
        for key, value in something.items():
            assert isinstance(key, int)
            assert isinstance(value, str)

    _run_test(something={123: "abc", 2314: 12312, "123": "abc"})


def test_multiple_recursion():
    """Should be able to go all the way down to cheese."""

    @type_checked
    def _run_test(something:{str: (bool, int, {str: int}, str)}):
        assert something == {"1234": (True, 50, {"5678": 99}, "False")}

    _run_test({1234: ("True", "50", {5678: "99"}, False)})


def test_validation_can_fail():
    """Ensure we raise TypeError and the exc string is correct."""

    @type_checked
    def _run_test(something:int): pass

    with pytest.raises(TypeError) as error:
        _run_test("abc")

    assert "abc is of type str, expecting int." in error.value.args


def test_float_to_int():
    """Ints should be able to coerce through from float->int."""

    @type_checked
    def _run_test(something:int):
        assert something == 10

    _run_test("10.4")


def test_no_coercion():
    """Ensure you can turn off coercion and have a TypeError raise."""

    @type_checked(coerce=False)
    def _run_test(something:str): pass

    with pytest.raises(TypeError) as error:
        _run_test(1234)

    assert "1234 is of type int, expecting str." in error.value.args


def test_no_coerce_set_once():
    """Settings are 'sticky'."""

    @type_checked(coerce=False)
    def _run_test(something:str): pass

    @type_checked
    def _run_test2(something:str): pass

    @type_checked
    def _run_test3(something:bool): pass

    test_expectations = zip(
        (_run_test, _run_test2, _run_test3),
        (1234, 5678, "False"),
        (str, str, bool),
        (int, int, str),
    )
    for test, args, expected, isactually in test_expectations:
        with pytest.raises(TypeError) as error:
            test(args)

        assert "{} is of type {}, expecting {}.".format(
            args, isactually.__name__, expected.__name__) in error.value.args


@pytest.mark.parametrize(
    "obj",
    (object, TestObj, NestObj),
    ids=("base", "inherit", "nested")
)
def test_objects(obj):
    """Ensure we don't reinstantiate any objects."""

    @type_checked
    def _run_test(something:obj):
        return something

    orig = obj()
    tested = _run_test(orig)
    assert orig == tested
    # py.test will alse ensure the ID doesn't change... but, being explict
    assert id(orig) == id(tested)


def test_unchecked_args():
    """You can have a mixture of checked and unchecked args."""

    @type_checked
    def _run_test(something:str, something_else):
        assert isinstance(something, str)
        assert isinstance(something_else, bool)

    _run_test(1234, True)


def test_adding_config_keys():
    """Ensure new keys are not allowed in the Config."""

    with pytest.raises(ValueError) as error:
        Config.config()["something_fake"] = True

    assert "something_fake is not a valid config key." in error.value.args


def test_noncallable():
    """Strings or modules don't work."""

    @type_checked
    def _run_test(something:sys): pass

    with pytest.raises(ValueError) as error:
        _run_test(True)

    err = error.value.args
    assert "type <module 'sys' (built-in)> is not a type or callable." in err

    @type_checked
    def _run_test(something:"else"): pass

    with pytest.raises(ValueError) as error:
        _run_test(True)


def test_kwarg_nonbool():
    """Config values are all booleans."""

    with pytest.raises(ValueError) as error:
        # because this happens in the wrap, but before the wrap, we don't need
        # a test function, we just have to not be None
        type_checked(func=False, debug="abc")

    assert "abc is not a valid config value." in error.value.args


def test_config():
    """Should be able to get and set the static dict's value."""

    assert Config.get("abc") is None
    assert Config.get(1234) is None

    for key in ("coerce", "debug"):
        assert Config.get(key) is True
        Config.set(key, False)
        assert Config.get(key) is False

        with pytest.raises(ValueError):
            Config.set(key, "something")

        with pytest.raises(ValueError):
            Config.set(key, int)


def test_nested_fail():
    """Ensure the error message received when a value should be an iterable."""

    @type_checked
    def _run_test(thing:(float, float)): pass

    with pytest.raises(TypeError) as error:
        _run_test(12)

    assert error.exconly() == (
        "TypeError: Argument length mismatch. Expected a tuple of float, float."
    )


def test_nested_one_arg_short():
    """Should be raising if we're short on ...."""

    @type_checked
    def _run_test(thing:(float, int, str)): pass

    with pytest.raises(TypeError) as error:
        _run_test(("123", 123.12))

    assert error.exconly() == (
        "TypeError: Argument length mismatch. "
        "Expected a tuple of float, int, str."
    )


def test_iter_of_many():
    """If the iter type has len(1) it is enforced on all members."""

    @type_checked
    def _run_test(thing:(float,)):
        for item in thing:
            assert isinstance(item, float)
        assert len(thing) == 3

    _run_test(thing=("10", 1, 5 / 6))

    # should work with lists too
    @type_checked
    def _run_test(thing:[str]):
        for item in thing:
            assert isinstance(item, str)
        assert len(thing) == 3

    _run_test(thing=("10", 1, 5 / 6))


def test_defined_in_iter():
    """Check that we can do repeated defined tuples in a list."""

    @type_checked
    def _run_test(thing:[(int, str, str)]):
        for group in thing:
            assert isinstance(group[0], int)
            assert isinstance(group[1], str)
            assert isinstance(group[2], str)
        assert len(thing) == 4

    _run_test(thing=[
        (12.3, None, False),
        ("12.1", True, 1),
        (False, 10, 12.1),
        (True, 14.9, None),
    ])


def test_star_args():
    """*args can be used and all members should validate to that type."""

    @type_checked
    def _run_test(wat:int, *args:float, **kwargs:str):
        assert wat == 0
        for arg in args:
            assert isinstance(arg, float)
        assert len(args) == 4
        for _, value in kwargs.items():
            assert isinstance(value, str)

    _run_test(False, False, True, 14, "10.2", foo=False, bar=17, ok=None)


def test_star_kwargs():
    """Ensure non-annotated kwargs arn't affected by annotated **kwargs."""

    @type_checked
    def _run_test(nothing, special=None, going:int=12, on="here", **kw:str):
        assert nothing == "hello"
        assert special == 50.12
        assert going == 1999
        assert on is True
        assert kw["other"] == "False"
        assert kw["thing"] == "15"

    _run_test("hello", 50.12, going="1999", on=True, other=False, thing=15)


def test_no_bleedthrough():
    """Ensure there's no bleedthrough from *args->regular kwargs."""

    @type_checked
    def _run_test(*args, ok:int, then:float, well:bool, **kwargs:str):
        assert args == ("12", 4, None, 19.9)
        assert ok == 90
        assert then == 17.2
        assert well is True
        assert kwargs == {"one": "111", "two": "22.2"}

    _run_test("12", 4, None, 19.9, ok="90", then="17.2", well="True", one=111,
              two=22.2)


def test_multi_arg_no_explode():
    """Regression test. Ensure the kwarg is not exploded into."""

    class MyOtherObject(object):
        def __init__(self, x_y, otherthing=None):
            self.x_y = x_y
            self.otherthing = otherthing

    @type_checked
    def _run_test(yep:MyOtherObject):
        assert yep.x_y == (1, 2)
        assert yep.otherthing is None

    _run_test((1, 2))


def test_deactivate():
    """Should be able to deactivate the library through Config."""

    @type_checked
    def _run_test(ok:int, then:str, sure:float):
        assert ok == "123"
        assert then == False
        assert sure == 40

    # you could use this to first annotate and wrap the functions you wanted,
    # then test your application with this library off and with it on.
    Config.set("active", False)
    _run_test("123", False, 40)


def test_multi_arg_object():
    """Shows the problem with multiple arg objects."""

    @type_checked
    def _run_test(ok:MyObject): pass

    with pytest.raises(TypeError) as error:
        _run_test((1, 2))

    assert error.exconly() == (
        "TypeError: (1, 2) is of type tuple, expecting MyObject."
    )


def test_multi_arg_workaround():
    """Demonstrates how to workaround an object that requires multiple args."""

    @type_checked
    def _run_test(ok:MySubClassedObject):
        assert ok.x == 1
        assert ok.y == 2

    _run_test((1, 2))


def test_bytes_to_string():
    """Ensure decode is called on the bytes object if coercing to string."""

    @type_checked
    def _run_test(something:str):
        assert something == "yep"

    _run_test(bytes("yep", "utf-8"))


def test_empty_dict():
    """Test the case of requesting a dict with no further spec."""

    @type_checked
    def _run_test(thing:{}):
        assert isinstance(thing, dict)

    _run_test({"foo": "bar"})


def test_empty_dict_by_name():
    """Same as the test above, but with the name dict rather than {} syntax."""

    @type_checked
    def _run_test(thing:dict):
        assert isinstance(thing, dict)

    _run_test({"baz": True})


def test_empty_dict_failure():
    """Ensure things which cannot coerce to dictionaries don't."""

    @type_checked
    def _run_test(thing:{}): pass

    with pytest.raises(TypeError):
        _run_test(1)


def test_empty_dict_coerce():
    """Ensure things which can be coerced to dictionaries are."""

    @type_checked
    def _run_test(thing:{}):
        assert isinstance(thing, dict)

    _run_test([("something", "is_true")])


def test_dict_keys_to_list():
    """Ensure we can convert dict.keys()/values() to a list."""

    @type_checked
    def _run_test(thing:[str]):
        assert isinstance(thing, list)
        assert "foo" in thing
        assert "bar" in thing
        assert len(thing) == 2

    _run_test({"foo": 1, "bar": 2}.keys())
    _run_test({1: "foo", 2: "bar"}.values())


def test_string_to_listed():
    """Ensure a single string is listed but not split."""

    @type_checked
    def _run_test(thing:[str]=None):
        assert thing == ["words"]

    _run_test("words")


def test_int_to_listed():
    """Ensure a single stringed integer is properly converted."""

    @type_checked
    def _run_test(thing:[int]=None):
        assert thing == [15]

    _run_test("15.0")


def test_complex_to_tuple():
    """Ensure complex numbers can be coerced into tuples."""

    @type_checked
    def _run_test(thing:(complex,)):
        assert thing == (complex(15, 2),)

    _run_test(complex(15, 2))


if __name__ == "__main__":
    pytest.main("-rx -v {}".format(__file__))
