pychecked
=========

Python Type Checking Library.

Python3.0 introduced the acceptance of [PEP3107](http://legacy.python.org/dev/peps/pep-3107); which gives python developers the option of annotating their funtion signatures. What it very distinctly does not deliver, is any enforcement of those annotations. Pychecked provides a wrapper, `type_checked` which you can decorate your annotated functions with to enforce those annotations. If the object being passed in does not match the expected type, pychecked will try to coerce the object into the correct type. This behavior is adjustable, through the `Config` object in pychecked, or by passing `coerce=False` as a kwarg to the wrap function `type_checked`. Note that the wrap `type_checked`; which lives in the `pychecked.type_checking` module, is exported as the top level module callable as well. Meaning, using this is as simple as:

<pre>import pychecked

@pychecked
def my_function(something:str):
    print(type(something))

my_function(11.1)
my_function(bytes("hello", "utf-8"))
my_function(False)</pre>

Examples
========

Say you had the following function, which you only ever wanted to accept integers:

<pre>@pychecked
def and_one(number:int):
    return number + 1</pre>

Simple, right? What if it was a list of integers though? Easy!

<pre>@pychecked
def average(numlist:[int]):
    return (sum(numlist) / len(numlist)) * 100</pre>

Neat! OK. Tricky one now, I want to accept a dictionary of {int: string}

<pre>@pychecked
def my_func(input_obj:{int: str}):
    for number, string in input_obj.items():
        assert isinstance(number, int)
        assert isinstance(string, str)</pre>

What if you want to accept a list of tuples? Sure thing.

<pre>@pychecked
def accept_many(things:[(int, int, bool, str, MyCustomObject)]):
    pass</pre>

In the above instance, you can see how even custom objects can be used in the type checking. This can be very handy if you know that you're not passing the correct type and you want to shortcut the creation of the correct objects for the function.

As an example, consider a game object, and a function which adds player objects to that game:

<pre>class Game(object):
    def __init__(self):
        self.players = []

class Player(object):
    def __init__(self, name):
        self.name = name

@pychecked
def add_player_to_game(game:Game, player:Player):
    game.players.append(player)

if __name__ == "__main__":
    game = Game()
    add_player_to_game(game, "paul")
    add_player_to_game(game, "rufus")
    print(game.players)</pre>


So now, what happens when things go wrong. Sometimes, it will be impossible to coerce the input into the requested type. In these cases a `TypeError` will be raised by `pychecked`. A `ValueError` will be raised if the type requested isn't actually a `type` type or callable.

An example of failure and how to overcome it:

<pre>>>> import pychecked
>>> class MyClass(object):
...   def __init__(self, x, y):
...     self.x = x
...     self.y = y
...
>>> @pychecked
... def my_function(something:MyClass):
...   pass
...
>>> my_function(2)
Traceback (most recent call last):
  File "/Users/adam/venv/3.4.32/src/pychecked/pychecked/type_checking.py", line 225, in _do_validation
    return type_(value)
TypeError: __init__() missing 1 required positional argument: 'y'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/adam/venv/3.4.32/src/pychecked/pychecked/type_checking.py", line 130, in _type_checked
    v_args.append(_do_validation(annotations[arg_name], arg))
  File "/Users/adam/venv/3.4.32/src/pychecked/pychecked/type_checking.py", line 234, in _do_validation
    _raise_error()
  File "/Users/adam/venv/3.4.32/src/pychecked/pychecked/type_checking.py", line 176, in _raise_error
    value, type(value).__name__, type_.__name__))
TypeError: 2 is of type int, expecting MyClass.
>>> try:
...   my_function(2)
... except TypeError:
...   print("errored")
...
errored</pre>

Easy, right? Sort of. Having an object that requires multiple args in it's init will always be difficult to coerce into. You can make a proxy/subclass object that can receive a single arg and instatiate the base object with other defaults or using the single arg (exploding a tuple, for instance). There's a gotcha in that you need to modify the isinstance magic method to respond True to the base class as well so the proxies arnt reinstantiated with a base object being passed in. An example:

<pre>import pychecked

class XYObject(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

class XYObjectProxyMeta(type):
    # instancecheck overrides are only allowed on metaclasses
    def __instancecheck__(cls, instance):
        return instance.__class__.__name__ in ["XYObjectProxy", "XYObject"]

class XYObjectProxy(XYObject, metaclass=XYObjectProxyMeta):
    def __init__(self, arg):
        super(XYObjectProxy, self).__init__(*arg)

@pychecked
def my_function(something:XYObjectProxy):
    print(type(something))
    print(something)

orig = XYObject(1, 2)
my_function(orig)
ret = my_function((1, 1))
my_function(ret)</pre>


Config
======

Pychecked operates off of a sticky style config. Meaning, if you set or change an option in the `Config`, that option will stay until changed again.

This is so that if you want your application to raise `TypeErrors` on annotation mismatches instead of coercion, you can set the config once in your appliation's init method.

An example:

<pre>from pychecked.type_checking import type_checked, Config

@type_checked
def do_things(name:str):
    pass

@type_checked(coerce=False)
def main():
    do_things(123)  # raises TypeError
    Config.set("coerce", True)
    do_things(123)  # does not raise

if __name__ == "__main__":
    main()</pre>

As you can see in the above, you can set `Config` options through kwargs to the wrap, or through `pychecked.Config.set`.


Copyright and License
---------------------

pychecked was written by Adam Talsma <adam@demonware.net>.

Copyright (c) 2014, Activision Publishing, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list
of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

* Neither the name of Activision Publishing, Inc. nor the names of its
contributors may be used to endorse or promote products derived from this
software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
