import requests

class TextUtilsMixin(object):
    def text_search2(self, value, text):
        print("text_search: {}".format(value))
        if value in text:
            print("string {} found in the response".format(value))
            return True
        return False


