# backend/app/tests/test_variable_resolver.py
import pytest
from app.services.variable_resolver import VariableResolver


def test_resolve_simple_variable():
    resolver = VariableResolver()
    context = {"username": "test_user"}
    result = resolver.resolve("{username}", context)
    assert result == "test_user"


def test_resolve_nested_variable():
    resolver = VariableResolver()
    context = {"user": {"id": "123"}}
    result = resolver.resolve("{user.id}", context)
    assert result == "123"


def test_resolve_missing_variable():
    resolver = VariableResolver()
    context = {}
    result = resolver.resolve("{missing}", context)
    assert result == "{missing}"


def test_resolve_multiple_variables():
    resolver = VariableResolver()
    context = {"name": "Alice", "age": 25}
    result = resolver.resolve("{name} is {age} years old", context)
    assert result == "Alice is 25 years old"


def test_resolve_non_string_values():
    resolver = VariableResolver()
    context = {"count": 10, "price": 9.99}
    result = resolver.resolve("Total: {count} items at {price} each", context)
    assert result == "Total: 10 items at 9.99 each"