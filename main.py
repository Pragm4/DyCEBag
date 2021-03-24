import json
import re
import time
from collections import OrderedDict
from context import Context
from actions import Actions, add_method
from rulesengine import RulesEngine
from mixins.actionsmixin import TextUtilsMixin
from mixins.httpmixin import HttpMixin

"""
TODO:
    - Decorators for engine control
    - Run all non-testable rules during testing
"""

def openFile(fileName):
    with open(fileName, "r") as reader:
        data = json.loads(reader.read(), object_pairs_hook=OrderedDict)
        return data

@add_method(Actions)
def aprint(self, text):
    print(">> " + text)

if __name__ == "__main__":
    starting_facts = {
        "base_url": "http://www.webscantest.com/",
        "visited": []
    }
    data = openFile("./examples/multicrawler-example.json")

    rules_engine = RulesEngine(data[0], mixins=(TextUtilsMixin, HttpMixin,))
    rules_engine.context.add_facts(starting_facts, "global")
    rules_engine.context.add_facts({"sitemap": []}, "singletons")
    rules_engine.context.set_scope("page", {})

    rules_engine.run()
    rules_engine.context.show()
    print("Final path: {}\n\n".format(rules_engine.context.get("path")))

