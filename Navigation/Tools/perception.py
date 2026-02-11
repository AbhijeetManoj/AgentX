#from Navigation.Browser.manager import BrowserManager
#from Navigation.Tools.Models.element import Element, ElementStore
#from Navigation.Tools.change_observer import ChangeObserver
#from Navigation.Tools.ToolHelpers.perception_helper import _parse_and_store_logic, format_planner_line, strip_none
#
#class PerceptionTools:
#    def __init__(self, session: BrowserManager, element_store: ElementStore):
#        self.session = session
#        self.element_store = element_store
#        self.change_observer = ChangeObserver(element_store)
#
#    def take_snapshot(self) -> str:
#        """
#        Full reset. Clears memory, creates fresh IDs 1..N.
#        """
#        try:
#            page = self.session.get_page()
#            raw_snapshot = page.locator("body").aria_snapshot()
#            # print(raw_snapshot)
#            
#            self.element_store.clear()
#            fresh_elements = self.change_observer._parse_fresh_dom(raw_snapshot)
#            
#            for i, el in enumerate(fresh_elements, 1):
#                el.id = str(i)
#                self.element_store.add(el)
#            
#            planner_lines = [format_planner_line(el) for el in fresh_elements]
#            print("snapshot:", planner_lines)
#            return (
#                f"status: success\n"
#                f"snapshot_type: full\n"
#                f"elements:\n{planner_lines}"
#            )
#        except Exception as e:
#            return f"status: error\nreason: {str(e)}"
#
#    def observe(self) -> str:
#        try:
#            page = self.session.get_page()
#            raw_snapshot = page.locator("body").aria_snapshot()
#            
#            result = self.change_observer.reconcile(raw_snapshot)
#            
#            final_elements = result["elements"]
#            new_ids = result["new_ids"]
#            updated_ids = result["updated_ids"]
#            removed_count = result["removed_count"]
#            stability = result["stability_score"]
#
#            
#            IS_NAVIGATION = False
#            
#            if stability >= 0.8:
#                IS_NAVIGATION = False
#                
#            elif stability < 0.6:
#                IS_NAVIGATION = True
#                
#            else:
#                 
#                 if removed_count > len(new_ids):
#                     IS_NAVIGATION = True
#
#            if IS_NAVIGATION:
#                self.element_store.clear()
#                for i, el in enumerate(final_elements, 1):
#                    el.id = str(i)
#                    self.element_store.add(el)
#                
#                planner_lines = [format_planner_line(el) for el in final_elements]
#                return (
#                    f"status: success\n"
#                    f"observation: Major page content change detected (Navigation). IDs reset.\n"
#                    f"elements:\n" + "\n".join(planner_lines)
#                )
#
#           
#            self.element_store.clear()
#            for el in final_elements:
#                self.element_store.add(el)
#            
#            parts = []
#            
#            if updated_ids:
#                parts.append(f"Values updated in {len(updated_ids)} fields.")
#
#            if new_ids or removed_count > 0:
#                parts.append(f"Layout updated: {len(new_ids)} new items, {removed_count} removed.")
#                
#                if new_ids:
#                    # Only show new IDs
#                    new_objs = [self.element_store.get(nid) for nid in new_ids]
#                    lines = [format_planner_line(el) for el in new_objs]
#                    parts.append("New Elements (Use these IDs):\n" + "\n".join(lines))
#            
#            if not parts:
#                return "status: success\nobservation: No significant visual changes."
#                
#            return f"status: success\nobservation: {' '.join(parts)}"
#
#        except Exception as e:
#            return f"status: error\nreason: {str(e)}"
#
#NEW PERCEPTION TOOL

from Navigation.Browser.manager import BrowserManager
from Navigation.Tools.Models.element import Element, ElementStore
from Navigation.Tools.change_observer import ChangeObserver
from Navigation.Tools.ToolHelpers.perception_helper import _parse_and_store_logic, format_planner_line, strip_none

class PerceptionTools:
    def __init__(self, session: BrowserManager, element_store: ElementStore):
        self.session = session
        self.element_store = element_store
        self.change_observer = ChangeObserver(element_store)

    def _compress_lines(self, elements: list[Element]) -> list[str]:
        """
        Groups sequential 'option' elements into their parent line to save vertical space.
        Returns a list of formatted strings.
        """
        lines = []
        i = 0
        while i < len(elements):
            el = elements[i]
            
            # Check if this element acts as a container (combobox/listbox)
            if el.role in ["combobox", "listbox"]:
                options = []
                j = i + 1
                
                # Look ahead for sequential options
                while j < len(elements):
                    next_el = elements[j]
                    if next_el.role == "option":
                        # Format: id:name (truncated for sanity)
                        opt_val = (next_el.name or next_el.text or "").strip().replace("\n", "")[:30]
                        options.append(f"{next_el.id}:{opt_val}")
                        j += 1
                    else:
                        break
                
                # Format the parent line
                base_line = format_planner_line(el)
                
                # If we found options, append them to the base line
                if options:
                    # Compressed format: ... | options[id:val, id:val]
                    base_line += f" | options[{', '.join(options)}]"
                    lines.append(base_line)
                    i = j  # Jump index past the processed options
                else:
                    lines.append(base_line)
                    i += 1
            
            # If it's a standalone option (orphaned), print it normally
            elif el.role == "option":
                lines.append(format_planner_line(el))
                i += 1
                
            else:
                lines.append(format_planner_line(el))
                i += 1
                
        return lines

    def take_snapshot(self) -> str:
        """
        Full reset. Clears memory, creates fresh IDs 1..N.
        """
        try:
            page = self.session.get_page()
            raw_snapshot = page.locator("body").aria_snapshot()
            
            self.element_store.clear()
            fresh_elements = self.change_observer._parse_fresh_dom(raw_snapshot)
            
            for i, el in enumerate(fresh_elements, 1):
                el.id = str(i)
                self.element_store.add(el)
            
            # --- CHANGED: Use _compress_lines instead of list comprehension ---
            planner_lines = self._compress_lines(fresh_elements)
            
            print("snapshot:", planner_lines)
            return (
                f"status: success\n"
                f"snapshot_type: full\n"
                f"elements: {planner_lines}" 
            )
        except Exception as e:
            return f"status: error\nreason: {str(e)}"

    def observe(self) -> str:
        try:
            page = self.session.get_page()
            raw_snapshot = page.locator("body").aria_snapshot()
            
            result = self.change_observer.reconcile(raw_snapshot)
            
            final_elements = result["elements"]
            new_ids = result["new_ids"]
            updated_ids = result["updated_ids"]
            removed_count = result["removed_count"]
            stability = result["stability_score"]

            IS_NAVIGATION = False
            
            if stability >= 0.8:
                IS_NAVIGATION = False
            elif stability < 0.6:
                IS_NAVIGATION = True
            else:
                 if removed_count > len(new_ids):
                     IS_NAVIGATION = True

            if IS_NAVIGATION:
                self.element_store.clear()
                for i, el in enumerate(final_elements, 1):
                    el.id = str(i)
                    self.element_store.add(el)
                
                # --- CHANGED: Use _compress_lines ---
                planner_lines = self._compress_lines(final_elements)
                
                return (
                    f"status: success\n"
                    f"observation: Major page content change detected (Navigation). IDs reset.\n"
                    f"elements:\n" + "\n".join(planner_lines)
                )

            self.element_store.clear()
            for el in final_elements:
                self.element_store.add(el)
            
            parts = []
            
            if updated_ids:
                parts.append(f"Values updated in {len(updated_ids)} fields.")

            if new_ids or removed_count > 0:
                parts.append(f"Layout updated: {len(new_ids)} new items, {removed_count} removed.")
                
                if new_ids:
                    # Only show new IDs
                    new_objs = [self.element_store.get(nid) for nid in new_ids]
                    # --- CHANGED: Use _compress_lines here as well ---
                    lines = self._compress_lines(new_objs)
                    parts.append("New Elements (Use these IDs):\n" + "\n".join(lines))
            
            if not parts:
                return "status: success\nobservation: No significant visual changes."
                
            return f"status: success\nobservation: {' '.join(parts)}"

        except Exception as e:
            return f"status: error\nreason: {str(e)}"
