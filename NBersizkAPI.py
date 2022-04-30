"""
Version: v1.0.0
Author: YinMo0913 (WEDeach)
DateTime: 2022-04-23
"""

import re
import requests

class ObjectContent(object): 

    def __init__(self, contentType: str, content: any):
        self.contentType = contentType
        self.content = content

    def __repr__(self):
        L = ['%s=%r' % (key, value)
             for key, value in self.__dict__.items()]
        return '%s(%s)' % (self.__class__.__name__, ', '.join(L))


class NBersizkAPI(object):
    GUEST_SESSION_KEY_REGEX = re.compile(r"guestJs=([0-9]+);")

    POST_TITLE_REGEX = re.compile(r"<h1 class='x'>(.*?)<\/h1>")
    POST_DATE_REGEX = re.compile(r"<span id='postdate0' title='reply time'>(.*?)<\/span>")
    POST_CONTENT_REGEX = re.compile(r"<p id='postcontent0' class='postcontent ubbcode'>(.*?)<\/p>")

    BBCODE_IMG_REGEX = re.compile(r"\[img](.*?)\[\/img]")

    def __init__(self):
        self._session = requests.Session()
        self._sessionCookies = {}

    def get_post(self, post_id: str):
        raw = self.get_post_raw(post_id)
        POST_TITLE = re.findall(self.POST_TITLE_REGEX, raw)[0]
        POST_DATE = re.findall(self.POST_DATE_REGEX, raw)[0]
        POST_CONTENT = re.findall(self.POST_CONTENT_REGEX, raw)[0]
        text, objects = self.decode_ubbcode(POST_CONTENT)
        return {
            "title": POST_TITLE,
            "date": POST_DATE,
            "text": text,
            "objects": objects
        }

    def get_post_raw(self, post_id: str):
        path = f"/read.php?tid={post_id}"
        res = self.read("GET", path)
        if res.status_code == 403:
            if self.handle_guest_session(res):
                return self.get_post_raw(post_id)
        return res.text

    def handle_guest_session(self, res: requests.Response):
        html_raw = res.text
        
        GUEST_SESSION_KEY = re.findall(self.GUEST_SESSION_KEY_REGEX, html_raw)[0]
        print(f"guestJs: {GUEST_SESSION_KEY}")
        self._sessionCookies.update({
            "guestJs": GUEST_SESSION_KEY
        })
        return True
    
    def decode_ubbcode(self, ubbcode:str):
        text = ''
        objects = []
        curr_obj_id = 0
        ubbcode = ubbcode.replace('<br/>', '\n')
        imgs = re.findall(self.BBCODE_IMG_REGEX, ubbcode)
        for img in imgs:
            img_bbcode = f"[img]{img}[/img]"
            curr_obj_id += 1
            ubbcode = ubbcode.replace(img_bbcode, f'(查閱附件{curr_obj_id})')
            objects.append(
                ObjectContent("IMG", f"https://img.nga.178.com/attachments/{img}")
            )

        text = re.sub('\[.*?]', '', ubbcode)
        return text, objects
    
    def read(self, method: str, path: str):
        url = f"https://bbs.nga.cn{path}"
        return self._session.request(method, url, cookies=self._sessionCookies)

if __name__ == '__main__':
    a = NBersizkAPI()
    print(a.get_post(31581719))