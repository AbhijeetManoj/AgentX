from typing import List, Dict, Optional, Any
import re
from Navigation.Tools.Models.element import Element

def strip_none(d: dict) -> dict:
        return {k: v for k, v in d.items() if v is not None}

def format_planner_line(el: Element) -> str:
    """Compact format for planner: id:role|name|flags"""
    primary = el.name or el.text or ""

    primary = primary.replace("\n", " ").replace("|", "")[:40] 
    
    parts = [f"{el.id}:{el.role}|{primary}"]
    if el.parent:
        parts.append(f"p={el.parent}")
        
    return "|".join(parts)

def _parse_and_store_logic(snapshot_text: str) -> List[Element]:
    
    lines = snapshot_text.split('\n')
    parent_stack: List[tuple[int, str]] = []
    seen_counters: Dict[tuple, int] = {}
    pattern = re.compile(r'^(\s*)-\s+(\w+)(?:\s+"([^"]*)")?(?:\s+(.*))?$')
    
    elements = []
    element_counter = 1

    for line in lines:
        if not line.strip(): continue

        match = pattern.match(line)
        if match:
            indent_str, role, quoted_name, remainder_text = match.groups()
            indent_level = len(indent_str)

            while parent_stack and parent_stack[-1][0] >= indent_level:
                parent_stack.pop()
            
            parent_id = parent_stack[-1][1] if parent_stack else None
            name = quoted_name if quoted_name else ""
            raw_text = remainder_text.strip() if remainder_text else ""
            text_content = raw_text if raw_text and raw_text != name else None

            # Locator logic
            key = (role, name)
            current_index = seen_counters.get(key, 0)
            seen_counters[key] = current_index + 1
            safe_name = name.replace('"', '\\"')
            base_locator = f'role={role}[name="{safe_name}"]' if safe_name else f'role={role}'
            precise_locator = f'{base_locator} >> nth={current_index}'

            el_id = str(element_counter)
            
            el = Element(
                id=el_id,
                role=role,
                locator=precise_locator,
                scope="global",
                name=name if name else None,
                text=text_content,
                parent=parent_id
            )
            elements.append(el)
            parent_stack.append((indent_level, el_id))
            element_counter += 1
            
    return elements
