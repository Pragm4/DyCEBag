import logging
import threading
import time
import six

def add_method(cls):
    return lambda f: (setattr(cls, f.__name__, f) or f)

class AutoMixinMeta(type):
    def __call__(cls, *args, **kwargs):
        try:
            mixins = kwargs.pop('mixins')
            print(mixins)
            if mixins:
                bases = mixins + (cls,)
            else:
                bases = (cls,)
            name = "Actions"
            cls = type(name, bases, dict(cls.__dict__))
        except KeyError:
            pass
        return type.__call__(cls, *args, **kwargs)

@six.add_metaclass(AutoMixinMeta)
class Actions(object):

    def __init__(self, engine, context):
        format = "%(asctime)s %(threadName)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO,
                            datefmt="%H:%M:%S")
        self.context = context
        self.engine = engine

    def set_context(self, context):
        self.context = context

    def print_msg(self, msg):
        self.aprint(msg)

    def reportVuln(self, newMsg):
        self.aprint("reportVuln: {}".format(newMsg))
        return True

    def setConstraint(self, **kwargs):
        msg = kwargs["inter_check"]
        self.aprint("setConstraint: intercheck: {}".format(msg))
        return True

    def set_fact(self, **kwargs):
        for k in kwargs:
            v = kwargs[k]
            if isinstance(v, list):
                self.context.set(k, v[0], v[1])
            else:
                self.context.set(k, v)

    def aprint(self, text):
        print(">> " + text)

    def show_context(self, scope=None):
        self.context.show(scope=scope)


