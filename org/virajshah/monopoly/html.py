from typing import Dict, List, Union


class DOMElement:
    def __init__(self, element: str, **kwargs):
        """
        Initialize an HTML/XML element.
        Equivalent to document.createElement(element).

        :param element: The element tag name
        :param kwargs: Attributes belonging the the element
            autoclose=True: for <elem/>
            classname=str: for <elem class=str>
            children=List[Union[DOMElement, str]] for children
        """
        self.element = element
        self.attributes: Dict[str, str] = {}
        self.children: List[Union[DOMElement, str]] = []
        self.autoclose: bool = False

        for key in kwargs:
            if key not in ["children", "autoclose", "classname"]:
                self.attributes[key] = kwargs[key]

        self.children = kwargs["children"] if "children" in kwargs else []

        if "autoclose" in kwargs and kwargs["autoclose"] and len(self.children) == 0:
            self.autoclose = True
        if "classname" in kwargs:
            self.attributes["class"] = kwargs["classname"]

    def append_child(self, child: Union["DOMElement", str]) -> None:
        """
        Add a child to a DOMElement.
        Equivalent to HTMLObject.appendChild(child)

        :param child: The child to append to the list of the element's children
        :return: None
        """
        self.children.append(child)
        if self.autoclose:
            self.autoclose = False

    def __str__(self):
        """
        :return: The HTML representation of the DOM (recursively includes all children)
        """
        buffer: str = "<" + self.element
        for attr in self.attributes:
            buffer += ' {}="{}"'.format(attr, self.attributes[attr])
        if self.autoclose:
            buffer += "/>"
        else:
            buffer += ">"
        if len(self.children) > 0:
            for child in self.children:
                buffer += str(child)
        buffer += "</{}>".format(self.element)
        return buffer
