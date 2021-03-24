import re
import uuid
import inspect
import six
from context import Context
from actions import Actions


class RulesEngine(object):
    def __init__(self, rules_def, context=None, mixins=None):
        # pylint: disable=unexpected-keyword-arg
        self.mixins = mixins
        self.rules_def = rules_def
        self.context = context or Context()
        self.actions = Actions(self, self.context, mixins=mixins)
        self.current_rule = []
        self.properties = {}

        self.context.show("engine")
        self.context.set("engine_id", uuid.uuid4(), "engine")
        print("[+] New rules engine instance created {}".format(
            self.context.get("engine_id")))
        self.context.show("engine")

    def copy(self):
        self.context.set("stopped_rule", self.get_current_rule(), "engine")
        return RulesEngine(self.rules_def, self.context.copy(), mixins=self.mixins)

    def get_current_rule(self):
        if self.current_rule:
            return '.'.join(self.current_rule)
        else:
            return "[]"

    def get_engine_id(self):
        return self.context.get("engine_id")

    def finished_series(self):
        if self.current_rule:
            self.set_done(self.get_current_rule(), "finished_series")
            self.context.set_scope(self.get_current_rule(), {})

    def restart(self, context=None, rules=None, preserve=("global",)):
        self.stop()
        self.context.clear_contexts(self.context.get("engine_id"), preserve)
        self.current_rule = []
        self.run(context, rules)

    def run(self, context=None, rules=None):
        if context:
            self.context = context

        print("\n\n[+] Running rules engine: {}".format(
            self.context.get("engine_id")))

        self.context.set("stop_engine", False, "engine")
        self.current_rule = []
        self.context.set("current_rule", [], "engine")
        self.context.show()

        self.rules_traverse(rules)
        print("[+] Finished with all rules for engine {}".format(
            self.context.get("engine_id")))
        self.context.show("rules")

    def stop(self):
        print("[+] Stopping rules_engine {} at {}".format(
            self.get_engine_id(), self.get_current_rule()))
        self.context.set("stopped_rule", self.get_current_rule(), "engine")
        self.context.set("stop_engine", True, "engine")

    def get_rule(self, dic, keys):
        for key in keys:
            dic = dic[key]
        return dic

    def pop_current_rule(self):
        if self.current_rule:
            self.current_rule.pop()
            self.context.pop("current_rule", "engine")
            self.properties = {}
            self.context.pop_scope(self.context.get_current_rule(), None)
        else:
            print("current_rule is empty")

    def is_filtered(self, str_rule):
        return str_rule in self.context.get("_filter")

    def group_traverse(self, rules):

        if not isinstance(rules, dict):
            return

        action_choice = "true-action"

        for k, v in rules.items():
            if self.context.get("stop_engine"):
                return

            if isinstance(v, dict):
                print("[R] current_rule: {} {}".format(self.current_rule, k))
                self.context.append("path", k, "traversal")
                self.current_rule.append(k)
                self.context.append("current_rule", k, "engine")
                self.context.add_scope(self.get_current_rule())

                if "properties" in v and self.properties == {}:
                    self.properties = self.process_properties(
                        k, v["properties"])

                if "conditions" in v:
                    print("This is a rule: {}".format(self.get_current_rule()))

                    if self.is_filtered(self.get_current_rule()):
                        if not self.is_rule_done(self.get_current_rule()):
                            self.set_done(self.get_current_rule())

                    if "true-action" not in v:
                        v["true-action"] = []
                    if "false-action" not in v:
                        v["false-action"] = []

                    if "test" in v and not self.is_testable(v):
                        self.pop_current_rule()
                        continue

                    if self.is_rule_done(self.get_current_rule()):
                        print("[R]    Rule is done, skipping: {}".format(
                            self.get_current_rule()))
                        self.pop_current_rule()

                        continue

                self.group_traverse(v)

                # Set group as 'done'
                if "conditions" not in v:
                    print("[R] current group: {}".format(self.current_rule))
                    self.set_done(self.get_current_rule(), "conditions")

                self.pop_current_rule()

            elif isinstance(v, list):
                if k == "properties":
                    if self.properties.get("disabled"):
                        self.set_done(self.get_current_rule(), "disabled")
                        return

                if self.check_element(k, v, self.properties, action_choice):
                    print("  <>{}.{} - {}".format(
                        self.get_current_rule(), k, [list(i.keys())[0] for i in v]))
                    result = self.element_traverse(k, v)

                    if k == "conditions" and not result:
                        print("        Conditions not met, skipping rule\n")
                        self.set_done(self.get_current_rule(),
                                      "conditions not met")
                        return
                    if k == "expect" and not result:
                        action_choice = "false-action"
                    if k == "true-action":
                        if self.properties.get("run-once"):
                                self.set_done(self.get_current_rule(),
                                              "run-once", scope="global")
                        else:
                            self.set_done(self.get_current_rule(),
                                          "true-action")
                    if k == "false-action":
                        if not self.properties.get("repeatable"):
                            if self.properties.get("run-once"):
                                self.set_done(self.get_current_rule(),
                                              "run-once", scope="global")
                            else:
                                self.set_done(self.get_current_rule(),
                                              "repeatable")

    def rules_traverse(self, rules=None):
        print("rules_traverse: {}\n\n".format(self.rules_def))
        rules = rules or self.rules_def
        self.group_traverse(rules)
        return ""

    def set_done(self, str_rule, msg=None, scope="rules"):
        if str_rule:
            if msg:
                print(msg)
            if scope == "global":
                _rules = self.context.get("_rules")
                _rules[str_rule] = "done"
                self.context.set("_rules", _rules, "global")
            else:
                self.context.set(str_rule, "done", scope)

    def is_rule_done(self, current_rule):
        if self.context.get(current_rule) == "done":
            return True
        _rules = self.context.get("_rules")
        if _rules and _rules.get(current_rule) == "done":
            return True
        return False

    def is_testable(self, rule):
        stopped_rule = self.context.get("stopped_rule")
        if stopped_rule:
            if stopped_rule == self.get_current_rule():
                return True
            else:
                print("Need to finish {} before this rule can be tested {}".format(
                    stopped_rule, self.get_current_rule()))
                return False
        return True

    def check_element(self, name, elem, properties, action_choice=True):
        elem_names_list = [
            "properties",
            "conditions",
            "test",
            "expect",
            "true-action",
            "false-action"
        ]
        # print("elem - {}:{}".format(name, str(elem)))

        if name not in elem_names_list:
            print("    Skipping this element because it's not in the elem_names_list")
            return False
        if name in ["true-action", "false-action"] and name != action_choice:
            return False
        if name == "test" and self.context.get("stopped_rule") == self.get_current_rule():
#             print("check_element properties: {}".format(properties))
            print("    Test was performed previously. Skipping.")
            self.context.set("stopped_rule", None, "engine")
            return False

        return True

    def process_properties(self, name, elem):
        properties = {}
        for e in elem:
            (k, v), = e.items()
            # print("rule_filter: {}:{}".format(k, v))
            # print("type(v): {}", type(v))
            if k == "disabled" and v == True:
                print("[R]    Rule is disabled. Skipping {}".format(self.current_rule))
            properties[k] = v
        print("properties: {}".format(properties))
        return properties

    def element_traverse(self, name, elem):
        item_results = []
        item_names = []

        for e in elem:
            if name in ["conditions", "expect"]:
                result = self.call_item(e)
                item_results.append(result)
                item_names.append(list(e.items())[0][0])
            else:
                self.call_item(e)

        if name == "test":
            self.stop()

        if item_results:
            print("        [T/F]: {}.{} - {} {}".format(
                self.get_current_rule(), name, item_names, item_results))

        return all(item_results)

    def call_item(self, item):
        (k, v), = item.items()

        if hasattr(self.actions, k):
            func = getattr(self.actions, k)
            if callable(func):
                new_args = self.get_args(func, v)
                # print("new_args: {}".format(new_args))
                print("    Executing - {}: {}".format(k, new_args))
                result = func(**new_args)

                # print("call_item: {} == {}".format(k, result))
                return result
        else:
            return self.context.get(k) == v

        return True

    def get_arg_list(self, func):
        return inspect.getargspec(func)[0]

    def get_args(self, func, rule_args):
        new_args = {}
        print("rule_args: {}".format(rule_args))
        func_arg_list = self.get_arg_list(func)
        print("func_arg_list: {}".format(func_arg_list))

        for arg in func_arg_list:
            if arg == "self":
                continue
            elif arg in rule_args:
                v = rule_args[arg]
#                 print("arg {}:{}".format(arg, v))
                if isinstance(v, six.string_types):
                    value = self.get_arg_value(v)
                else:
                    value = v
                # print("         got arg value: {}".format(value))
                new_args[arg] = value
            elif self.context.has(arg):
                new_args[arg] = self.context.get(arg)
            else:
                print("No match for {}".format(arg))

        if inspect.getargspec(func).keywords:
            for arg in rule_args:
                new_args[arg] = rule_args[arg]

        return new_args

    def get_arg_value(self, arg):
        # print("get_arg_value: {}".format(arg))
        def repl(matchobj):
            value = self.context.get(matchobj.group(1))
            return value or "None"

        # Single variable can be any type
        m = re.search(r"^\${(\S+?)}$", arg)
        if m:
            # print("m: {}".format(m.group(1)))
            value = self.context.get(m.group(1))
            return value
        # Non-single variable must be a string
        return re.sub(r"\${(\S+?)}", repl, arg)
