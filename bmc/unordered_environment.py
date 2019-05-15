"""
Allows referring to an object before it is initialized, in a limited way.

::
    def create_placeholder():
        return [None]
    def assign(placeholder_object, real_value):
        placeholder_object[0] = real_value
    with UnorderedEnvironment(create_placeholder, assign) as e:
        e.x = ["a", "b", "c", e.y]
        e.y = ["d"]
    
The user must provide two functions: ``create_placeholder()``, and ``assign(object, value)``.
``create_placeholder()`` returns an empty placeholder object that can later be assigned
a real value.  ``assign(placeholder_object, value)`` is called to set the real value of
a placeholder object once the real value is known.  Note that the real value may contain
other placeholder objects.

This also allows circular references to be created::

    with UnorderedEnvironment(create_placeholder, assign) as e:
        e.x = [e.y]
        e.y = [e.x]
    assert e.x[0] is e.y and e.y[0] is e.x
"""

class UnorderedEnvironment:
    def __init__(self, create_placeholder, assign):
        super().__setattr__("_create_placeholder", create_placeholder)
        super().__setattr__("_assign", assign)
        super().__setattr__("_namespace", {})
        super().__setattr__("_used_names", set())
        super().__setattr__("_assigned_names", set())
        super().__setattr__("_in_with_statement", False)
    def __getattr__(self, name):
        if self._in_with_statement:
            # When name lookup fails, assume the name will be assigned later, and return a placeholder.
            new_placeholder = self._create_placeholder()
            super().__setattr__(name, new_placeholder)
            self._used_names.add(name)
            return new_placeholder
        else:
            return super().__getattribute__(name)
    def __setattr__(self, name, value):
        if name in self._assigned_names:
            raise NameError(name + " is already assigned.")
        self._assign(getattr(self, name), value)
        self._assigned_names.add(name)
    def __enter__(self):
        super().__setattr__("_in_with_statement", True)
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        super().__setattr__("_in_with_statement", False)
        unassigned_names = self._used_names - self._assigned_names
        if (unassigned_names):
            raise NameError("Names used but never assigned: " + str(unassigned_names))
