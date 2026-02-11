from typing import List, Dict, Any
import re
from Navigation.Tools.Models.element import Element, ElementStore

class ChangeObserver:
    def __init__(self, element_store: ElementStore):
        self.store = element_store

    def _get_stable_signature(self, el: Element) -> str:
        clean_name = el.name or ""
        if el.role in ["textbox", "combobox", "searchbox", "slider", "spinbutton"]:
            clean_name = clean_name.strip('"').strip("'")
            if ": " in clean_name:
                clean_name = clean_name.split(": ")[0]
            clean_name = clean_name.strip('"').strip("'")
        return f"{el.role}|{clean_name}"

    def reconcile(self, new_snapshot_text: str) -> Dict[str, Any]:
        fresh_elements = self._parse_fresh_dom(new_snapshot_text)
        old_elements = self.store.all()
        
        old_lookup = {}
        for el in old_elements:
            sig = self._get_stable_signature(el)
            if sig not in old_lookup: old_lookup[sig] = []
            old_lookup[sig].append(el)

        final_elements = []
        new_ids = []
        updated_ids = [] 
        matched_count = 0
        
        current_max_id = max([int(e.id) for e in old_elements if e.id.isdigit()] or [0])
        next_id = current_max_id + 1

        for fresh_el in fresh_elements:
            sig = self._get_stable_signature(fresh_el)
            
            if sig in old_lookup and old_lookup[sig]:
                matched_el = old_lookup[sig].pop(0)
                fresh_el.id = matched_el.id
                if (fresh_el.name != matched_el.name) or (fresh_el.text != matched_el.text):
                    updated_ids.append(fresh_el.id)
                final_elements.append(fresh_el)
                matched_count += 1
            else:
                fresh_el.id = str(next_id)
                next_id += 1
                final_elements.append(fresh_el)
                new_ids.append(fresh_el.id)

        # Stability = % of OLD elements that are still present
        total_old = len(old_elements)
        stability_score = 1.0
        if total_old > 0:
            stability_score = matched_count / total_old

        removed_count = sum(len(v) for v in old_lookup.values())

        return {
            "elements": final_elements,
            "new_ids": new_ids,
            "updated_ids": updated_ids,
            "stability_score": stability_score,
            "removed_count": removed_count
        }
    
    def _filter_redundant(self, elements: List[Element]) -> List[Element]:
        """
        Removes static text/headings if they are immediately followed by 
        an interactive element with the exact same (or containing) name.
        """
        if not elements: return []
        
        filtered = []
        skip_next = False
        
        # Define roles for comparison
        STATIC_ROLES = {'text', 'heading', 'paragraph', 'label'}
        INTERACTIVE_ROLES = {
            'textbox', 'checkbox', 'radio', 'combobox', 
            'listbox', 'radiogroup', 'link', 'button', 'slider'
        }

        for i in range(len(elements)):
            if skip_next:
                skip_next = False
                continue

            curr = elements[i]
            
            if i < len(elements) - 1:
                nxt = elements[i+1]
                
                # CHECK: Is Current = Static AND Next = Interactive?
                if curr.role in STATIC_ROLES and nxt.role in INTERACTIVE_ROLES:
                    
                    # Normalization for comparison
                    c_name = (curr.name or curr.text or "").strip().lower()
                    n_name = (nxt.name or nxt.text or "").strip().lower()
                    
                   
                    
                    if c_name and n_name:
                        if c_name == n_name:
                            continue 
                        
                        if len(c_name) > 2 and c_name in n_name:
                            continue 

            filtered.append(curr)
            
        return filtered

    def _parse_fresh_dom(self, snapshot_text: str) -> List[Element]:
        lines = snapshot_text.split('\n')
        parent_stack: List[tuple[int, str]] = []
        seen_counters: Dict[tuple, int] = {}
        
        # Regex handles optional quotes on role: - 'heading ...'
        pattern = re.compile(r'^(\s*)-\s+[\'"]?(\w+)[\'"]?(?:\s+"([^"]*)")?\s*(.*)?$')
        
        elements = []
        last_element = None

        IGNORED_ROLES = {
            "list", "listitem", "main", "contentinfo", 
            "banner", "navigation", "region", "paragraph", 
            "generic", "presentation", "WebArea"
        }
        
        for line in lines:
            if not line.strip(): continue
           
            if line.strip().endswith("'"): line = line.rstrip("'")

            match = pattern.match(line)
            if match:
                indent_str, role, quoted_name, remainder_text = match.groups()
                indent_level = len(indent_str)

                if role in IGNORED_ROLES:
                    while parent_stack and parent_stack[-1][0] >= indent_level:
                        parent_stack.pop()
                    continue

                while parent_stack and parent_stack[-1][0] >= indent_level:
                    parent_stack.pop()
                
                parent_id = parent_stack[-1][1] if parent_stack else None
                name = quoted_name if quoted_name else ""
                raw_text = remainder_text.strip() if remainder_text else ""

                if raw_text.startswith(":"): raw_text = raw_text.lstrip(":").strip()

                if not name and raw_text.startswith('"') and '":' in raw_text:
                     try:
                         parts = raw_text.split('":')
                         name = parts[0].strip('"')
                         raw_text = raw_text[len(parts[0])+2:].strip()
                     except: pass

                text_content = raw_text if raw_text and raw_text != name else None

                clean_text = (text_content or "").strip('"').strip()
                prev_name = (last_element.name if last_element else "").strip('"').strip()
                
                if role == "text" and last_element:
                    if clean_text and clean_text == prev_name:
                        continue
                
                if name in ["Privacy Policy", "Terms of Service", "Google Forms", "Report Abuse", "Google"]:
                    continue

                # Locator Logic
                key = (role, name)
                current_index = seen_counters.get(key, 0)
                seen_counters[key] = current_index + 1
                
                safe_name = name.replace('"', '\\"')
                base_locator = f'role={role}[name="{safe_name}"]' if safe_name else f'role={role}'
                precise_locator = f'{base_locator} >> nth={current_index}'
                

                el = Element(
                    id="", role=role, locator=precise_locator, scope="global",
                    name=name if name else None, text=text_content, parent=parent_id
                )
                # print("Parsed Element:", el)
                
                elements.append(el)
                parent_stack.append((indent_level, el.id))
                last_element = el
                
        return self._filter_redundant(elements)
