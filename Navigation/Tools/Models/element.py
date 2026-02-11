from typing import Optional, Dict, Any, List

class Element:
    def __init__(
        self,
        id: str,
        role: str,
        locator: str,
        scope: str,
        tag: Optional[str] = None,
        name: Optional[str] = None,
        label: Optional[str] = None,
        text: Optional[str] = None,
        states: Optional[Dict[str, bool]] = None,
        parent: Optional[str] = None,
    ):
        self.id = id
        self.role = role
        self.selector = locator
        self.scope = scope
        self.tag_name = tag
        self.name = name or ""
        self.label = label
        self.text = text
        self.attributes: Dict[str, Any] = {}
        self.states = states if states is not None else {}
        self.parent = parent

    @property
    def signature(self) -> str:
        """
        Creates a semantic signature to track this element across snapshots
        even if the numeric ID changes.
        Format: role:name:text_snippet
        """
        text_sig = (self.text[:20] if self.text else "")
        return f"{self.role}:{self.name}:{text_sig}"

    def __repr__(self):
        return f"<Element id={self.id} role={self.role} name={self.name}>"

class ElementStore:
    def __init__(self):
        self._elements: Dict[str, Element] = {}

    def add(self, element: Element):
        self._elements[element.id] = element

    def get(self, element_id: str) -> Optional[Element]:
        return self._elements.get(element_id)
    
    def get_by_signature(self, signature: str) -> Optional[Element]:
        """Find an element by its semantic signature"""
        for el in self._elements.values():
            if el.signature == signature:
                return el
        return None

    def all(self) -> List[Element]:
        return list(self._elements.values())

    def clear(self):
        self._elements.clear()
        
    def get_state_map(self) -> Dict[str, Element]:
        """Returns a dict of signature -> Element for diffing"""
        return {el.signature: el for el in self.all()}
