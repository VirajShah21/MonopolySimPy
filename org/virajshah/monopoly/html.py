from typing import Dict, List, Union


class DOMElement:
    def __init__(self, element: str, **kwargs):
        self.element = element
        self.attributes: Dict[str, str] = {}
        self.children: List[Union[DOMElement, str]] = []
        self.autoclose = False

        for key in kwargs:
            if key not in ["children", "autoclose"]:
                self.attributes[key] = kwargs[key]

        self.children = kwargs["children"] if "children" in kwargs else []

        if "autoclose" in kwargs and kwargs["autoclose"] and len(self.children) == 0:
            self.autoclose = True

    def append_child(self, child):
        self.children.append(child)
        if self.autoclose: self.autoclose = False

    def __str__(self):
        buffer: str = "<" + self.element
        for attr in self.attributes:
            buffer += " {}={}".format(attr, self.attributes[attr])
        if self.autoclose:
            buffer += "/>"
        else:
            buffer += ">"
        if len(self.children) > 0:
            for child in self.children:
                buffer += str(child)
        buffer += "</{}>".format(self.element)
        return buffer