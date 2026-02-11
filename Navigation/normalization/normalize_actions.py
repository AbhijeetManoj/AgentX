import json
import ast
import re

def _clean_llm_string(text: str) -> str:
    text = re.sub(r"```[a-zA-Z]*", "", text)
    text = text.replace("```", "")
    return text.strip()

def _normalize_ids(ids) -> list[str]:
    
    if ids is None:
        return []

    if isinstance(ids, int):
        return [str(ids)]

    if isinstance(ids, str):
        ids = _clean_llm_string(ids)
        
        try:
            return [str(i) for i in json.loads(ids)]
        except (json.JSONDecodeError, TypeError):
            pass

        try:
            val = ast.literal_eval(ids)
            if isinstance(val, list):
                return [str(i) for i in val]
        except (ValueError, SyntaxError):
            pass

   
        if "," in ids:
            return [i.strip() for i in ids.split(",") if i.strip()]
        
        return [ids] if ids else []

    if isinstance(ids, list):
        return [str(i) for i in ids]
    
    if isinstance(ids, (tuple, set)):
        return [str(i) for i in ids]

    return []


def _normalize_actions(actions) -> list[dict]:
    if not actions:
        return []

    if isinstance(actions, str):
        actions = _clean_llm_string(actions)

        try:
            actions = json.loads(actions)
        except json.JSONDecodeError:
            try:
                actions = ast.literal_eval(actions)
            except Exception:
                raise ValueError(f"Could not parse actions: {actions}")

    if isinstance(actions, dict):
        actions = [actions]
    elif not isinstance(actions, list):
        raise ValueError(f"Unsupported actions type: {type(actions)}")

    normalized = []

    for action in actions:
        if not isinstance(action, dict):
            continue

        element_id = (
            action.get("element_id")
            or action.get("id")
            or action.get("elementId")
        )

        text = (
            action.get("text")
            or action.get("value")
            or action.get("input")
        )

        if element_id is not None and text is not None:
            normalized.append({
                "element_id": str(element_id),
                "text": str(text)
            })
            continue

        for key, value in action.items():
            normalized.append({
                "element_id": str(key),
                "text": str(value)
            })

    return normalized