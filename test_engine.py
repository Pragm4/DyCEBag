import json
import re
import time
import pytest
from collections import OrderedDict
from rulesengine import RulesEngine
from context import Context
from actions import Actions, add_method
from mixins.actionsmixin import TextUtilsMixin
from mixins.httpmixin import HttpMixin


print("Running tests")

def openFile(fileName):
    with open(fileName, "r") as reader:
        data = json.loads(reader.read(), object_pairs_hook=OrderedDict)
        return data

@pytest.fixture
def base_url():
    return "http://www.webscantest.com/"

@pytest.fixture
def starting_facts(base_url):
    return {
        "base_url": base_url,
        "visited": []
    }

@pytest.fixture
def starting_engine():
    return RulesEngine(openFile("rules-def.json")[0], mixins=(TextUtilsMixin, HttpMixin,))

@pytest.fixture
def engine(starting_facts):
    rules_engine = RulesEngine(openFile("rules-def.json")[0], mixins=(TextUtilsMixin, HttpMixin,))
    rules_engine.context.add_facts(starting_facts, "global")
    rules_engine.context.add_facts({"sitemap": []}, "singletons")
    rules_engine.context.set_scope("page", {})
    return rules_engine


def test_context_add_facts(starting_engine, starting_facts, base_url):
    starting_engine.context.add_facts(starting_facts, "global")
    starting_engine.context.add_facts({"sitemap": []}, "singletons")
    assert starting_engine.context.singletons["sitemap"] == []
    assert starting_engine.context.contexts["global"]["visited"] == []
    assert starting_engine.context.contexts["global"]["base_url"] == base_url

def test_context_has(engine):
    assert engine.context.has("engine_id") == True

def test_context_set_scope(engine):
    assert engine.context.contexts["page"] == {}

def test_context_pop_scope(engine):
    engine.context.pop_scope("page")
    assert "page" not in engine.context.contexts

def test_context_get(engine, base_url):
    assert engine.context.get("base_url") == base_url
    assert engine.context.get("sitemap") == []
    assert engine.context.get("nonexistent") == None
    assert engine.context.get("nonexistent", default=[]) == []
    assert engine.context.get("base_url", scope="global") == base_url
    assert engine.context.get("base_url", scope="singletons") == None

def test_context_set_default(engine):
    engine.context.set("new_key", ["foo", "bar"])
    engine.context.set("another_key", set(), "singletons")
    assert engine.context.contexts["global"]["new_key"] == ["foo", "bar"]
    assert engine.context.singletons["another_key"] == set()

def test_context_set_invalid_scope(engine, capsys):
    engine.context.set("new_key", 42, "invalid_scope")
    captured = capsys.readouterr()
    assert captured.out == "context[invalid_scope] doesn't exist\n"

def test_context_append(engine):
    engine.context.append("visited", "page1")
    assert engine.context.contexts["global"]["visited"] == ["page1"]

def test_context_pop(engine):
    engine.context.append("visited", "page1")
    engine.context.pop("visited")
    assert engine.context.contexts["global"]["visited"] == []

def test_context_copy(engine):
    new_context = engine.context.copy()
    assert new_context.contexts == engine.context.contexts
    assert new_context.singletons == engine.context.singletons
    assert new_context.contexts is not engine.context.contexts
    assert new_context is not engine.context

def test_context_clear_contexts(engine):
    print("foo")

print("Testing completed.")