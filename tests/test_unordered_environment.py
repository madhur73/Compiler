import pytest
import bmc.unordered_environment as ue

def create_placeholder():
    return []
def assign(object, value):
    object.extend(value)

def test_assignment_before_use():
    with ue.UnorderedEnvironment(create_placeholder, assign) as e:
        e.x = ["x"]
        e.y = ["y"]
        e.z = [e.x, e.y]
    assert e.z == [["x"], ["y"]]
    
def test_use_before_assignment():
    with ue.UnorderedEnvironment(create_placeholder, assign) as e:
        e.z = [e.x, e.y]
        e.x = ["x"]
        e.y = ["y"]
    assert e.z == [["x"], ["y"]]

def test_circular_reference():
    with ue.UnorderedEnvironment(create_placeholder, assign) as e:
        e.x = [e.y]
        e.y = [e.x]
    assert e.x[0] is e.y
    assert e.y[0] is e.x

def test_every_name_must_be_assigned_eventually():
    with pytest.raises(NameError):
        with ue.UnorderedEnvironment(create_placeholder, assign) as e:
            e.z = [e.x, e.y]
            e.x = ["x"]
            # y unassiged.

def test_unordered_only_in_with_statement():
    e = ue.UnorderedEnvironment(create_placeholder, assign)
    with pytest.raises(AttributeError):
        x = [e.x]

def test_reassignments_forbidden():
    with pytest.raises(NameError):
        with ue.UnorderedEnvironment(create_placeholder, assign) as e:
            e.x = [1]
            e.x = [2]
