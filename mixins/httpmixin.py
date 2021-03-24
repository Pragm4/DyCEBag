import requests
import logging
import threading
import time
from bs4 import BeautifulSoup
from six.moves.urllib.parse import urljoin

class HttpMixin(object):

    def compare(self, fact, value):
        self.aprint("compare fact: {} value: {}".format(self.context.get(fact), value))
        self.context.show()
        return self.context.get(fact) == value

    def is_new_page(self, visited, url=None):
        if not visited or not url:
            return True
        return url in visited

    def is_html_page(self, response):
        content_type = response.headers['content-type']
        self.aprint("grab_links content-type: {}".format(content_type))
        if "text/html" not in  content_type:
            return False
        return True

    def grab_links(self, base_url, response):
        if not self.is_html_page(response):
            return False

        html = BeautifulSoup(response.content, 'html.parser')
        url_list = []
        for link in html.find_all('a'):
            # links.append(link)
            url = link.get('href')

            if not url:
                continue
            if url:
                if "tel:" in url or "@" in url:
                    continue
                if url.startswith('#'):
                    continue
                if url.startswith('javascript'):
                    continue

            print("HREF: {}".format(url))
            if not url.startswith('http'):
                full_url = urljoin(base_url, url)
            else:
                full_url = link.get('href')

            if full_url not in self.context.get("sitemap"):
                url_list.append(full_url)

        self.context.set("url_list", url_list, "page")

        return bool(url_list)

    def text_search(self, value, response):
        print("text_search: {}".format(value))
        if not self.is_html_page(response):
            return False

        if value in response.text:
            print("string {} found in the response".format(value))
            return True
        return False

    def threaded_sender(self, url_list=None, breadth_limit=None):
        """
        - Stop engine
        - Copy engine
        - Pass new context as argument
        """
        self.aprint("Sending threaded requests")

        if breadth_limit and url_list:
            url_list = url_list[:breadth_limit]

        for url in url_list:
            if url in self.context.get("sitemap"):
                self.aprint("Already visited this url: {}".format(url))
                continue
            engine = self.engine.copy()

            engine.context.set("request_url", url)

            x = threading.Thread(target=engine.actions.send_request, args=(url, engine,))
            x.start()

    def send_request(self, url, engine):
        try:
            logging.info("Sending request: {}".format(url))
            response = requests.get(url)
            engine.context.set("response", response, scope="page")
        except Exception as e:
            logging.error("Exception: {} trying to get {}".format(str(e), url))

        engine.context.set("url", url, scope="page")
        engine.context.append("visited", url, "global")
        engine.context.append("sitemap", url, "singletons")

        time.sleep(1)
        engine.run()

    def is_new_link(self, url, sitemap):
        if url not in sitemap:
            return True
        return False

    def stop_sending(self):
        self.engine.finished_series()

    def next_request(self, visited, depth_limit):
        if len(visited) >= depth_limit:
            self.aprint("Depth limit reached: {}".format(visited))
            self.context.show("singletons")
            self.engine.finished_series()
        else:
            current = self.engine.get_rule(self.engine.rules_def,
                                           self.context.get("current_rule"))
            self.engine.element_traverse("test", current["test"])
