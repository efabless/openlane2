# Class Programming Guidelines

## Mutability

OpenLane 2 classes are based on the principle that objects that are passed between contexts are either **immutable** on termination of construction or **replicably modifiable**.

Immutable objects are just as described: they cannot be modified in-place. They may be updated only by creating a copy. This is to prevent surprises resulting from referential passing endemic to imperative and object-oriented programming.

They may, however, offer any number of read-only functions for convenience.

On the other hand, the replicably modifiable objects are those that handle non-trivial computation, e.g. Steps or Flows. Classes in this hierarchy may have a maximum of **one** public modifier adhering to these properties:
* This modifier may alter one or more properties of a class
    * The modifier shall not depend on the initial values of any altered
      property and may overwrite them if called again
    * If called again, it is expected to return the same result (within reason- not every aspect can be controlled, for example external filesystem modification and/or timestamps.)
* This modifier may depend on any number of private or internal modifiers
* This modifier's implementation shall be split into two:
    * A **public** part that is marked `@final`, i.e., it is not overridable.
      This will handle validation of inputs and outputs and thus must not be
      left to the whims of subclassers. It is responsible for calling the the
      internal part.
    * An **internal** part that is freely subclassable, however, it cannot be
      called from outside the public part.

For {py:class}`openlane.flows.Flow`, for example, the public and internal parts
are {py:meth}`openlane.flows.Flow.start` and {py:meth}`openlane.flows.Flow.run` respectively.


## Hierarchy

Classes in OpenLane rely on heavy use of polymorphism to define interface by
which multiple classes can interact with each other.

Object-orientation in Python is more akin to that of C++ than that of Java. For
example, what is an interface in Java is an abstract class with no properties
in C++ or Python.

The "interfaces" are not limited to methods- public properties are also part of
the interface. By our immutability standard, setters are by definition not in
consideration for this codebase. The choice of whether to use a getter or a
variable, however, is more involved and objects the following taxonomy:

```{digraph} taxonomy

start [label="Is the value expected to remain constant across all instances of a class?"]
class_dependent [label="Is the value computed from any other class variables or getters?"]

class_method [label="Class Method", peripheries=2]
class_property [label="Class Property", peripheries=2]

start -> class_dependent [label="Yes"]
class_dependent -> class_method [label="Yes"]
class_dependent -> class_property [label="No"]

dynamic [label="Is the value computed from any other instance variables or getters?"]
method [label="Instance Method", peripheries=2]
property [label="Instance Property", peripheries=2]

start -> dynamic [label="No"]
dynamic -> method [label="Yes"]
dynamic -> property [label="No"]

```

Furthermore, if the method is not useful in a base class, the method
(whether for class or instance) must be declared abstract using the
`@abstractmethod` decorator. Similarly, properties must be assigned
`NotImplemented` to declare that they are abstract. The former
is programmatically enforced, but the latter is currently not due to
technical limitations.