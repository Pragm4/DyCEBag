import pprint
import copy


class Context(object):
    """Contains the overall state of the rules engine

    Attributes:
        contexts: Contains the state of everything
    """
    def __init__(self, contexts=None):
        self.contexts = {}
        self.contexts["engine"] = {
            "stop_engine": False,
            "stopped_rule": None,
            "engine_id": None,
            "current_rule": []
        }
        self.contexts["_rules_filter"] = {"_filter": []}
        self.contexts["traversal"] = {"path": []}
        self.contexts["global"] = {"_rules": {}}
        self.contexts["rules"] = {}
        self.singletons = {}

    def pop_scope(self, scope, default=None):
        if scope in self.contexts:
            return self.contexts.pop(scope, default)

    def clear_contexts(self, engine_id=None, preserve=("global")):
        mapping = {
            "engine": {
                "stop_engine": False,
                "stopped_rule": None,
                "engine_id": None,
                "current_rule": []
            },
            "traversal": {"path": []}
        }

        for c in self.contexts:
            if c == "_rules_filter":
                continue
            if c in preserve:
                continue
            if c in mapping:
                self.contexts[c] = mapping[c]
            else:
                self.contexts[c] = {}

        if engine_id:
            self.contexts["engine"]["engine_id"] = engine_id

    def get_current_rule(self):
        if "current_rule" in self.contexts["engine"]:
            return '.'.join(self.contexts["engine"]["current_rule"])
        else:
            return "[]"

    def set_filter(self, filter_list):
        self.set("_filter", filter_list, "_rules_filter")

    def set_scope(self, scope, value):
        if scope == "singletons":
            self.singletons = value
        else:
            self.contexts[scope] = value

    def get(self, key, default=None, scope=None):
        if scope == "singletons":
            if key in self.singletons:
                return self.singletons[key]
            return default
        elif scope and key in self.contexts[scope]:
            return self.contexts[scope][key]

        for c in self.contexts:
            if key in self.contexts[c]:
                return self.contexts[c][key]
        if key in self.singletons:
            return self.singletons[key]
        return default

    def add_facts(self, facts, scope):
        for f in facts:
            if scope == "singletons" and f not in self.singletons:
                self.singletons[f] = facts[f]
            elif f not in self.contexts[scope]:
                self.contexts[scope][f] = facts[f]
            else:
                print("Fact already exists: {}".format(f))

    def add_scope(self, scope):
        if scope not in self.contexts:
            self.contexts[scope] = {}
        else:
            return self.contexts[scope]

    def has(self, key):
        """
        For falsey value cases. Ex. "zero": 0
        if self.context.get("zero") yields False
        if self.context.has("zero") yields True
        """
        for c in self.contexts:
            if key in self.contexts[c]:
                return True
        if key in self.singletons:
            return True
        return False

    def set(self, key, value, scope="global"):
        if scope == "singletons":
            self.singletons[key] = value
        else:
            try:
                self.contexts[scope][key] = value
            except KeyError:
                print("context[{}] doesn't exist".format(scope))
                return

        print("[C] context[{}][{}] set as {}".format(scope, key, value))

    def append(self, key, value, scope="global"):
        v = self.get(key, scope=scope)

        if v is None:
            print("{} doesn't exist".format(key))
            return

        if isinstance(v, list):
            v.append(value)
            self.set(key, v, scope)
        else:
            print("{} is not a list".format(key))

    def pop(self, key, scope="global"):
        if not self.has(key):
            print("{} doesn't exist".format(key))
            return

        if isinstance(self.contexts[scope][key], list):
            self.contexts[scope][key].pop()
        else:
            print("{} is not a list".format(key))

    def show(self, scope=None, exclude=["traversal"]):
        if scope == "singletons":
            pprint.pprint(self.singletons)
        elif scope:
            pprint.pprint(self.contexts[scope])
        else:
            for c in self.contexts:
                if c not in exclude:
                    str_obj = pprint.pformat(self.contexts[c])
                    print("{}:{}".format(c, str_obj))

    def copy(self):
        new_context = copy.copy(self)
        new_context.contexts = copy.deepcopy(self.contexts)
        new_context.singletons = copy.copy(self.singletons)

        return new_context
