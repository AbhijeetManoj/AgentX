import time
from Navigation.Browser.manager import BrowserManager
from Navigation.Tools.Models.element import ElementStore
from Navigation.Tools.perception import PerceptionTools
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

def _observe_and_report(action_results: dict, perception: PerceptionTools) -> dict:
        
        try:
        
            page = perception.session.get_page()
            try:
                page.wait_for_load_state("networkidle", timeout=4000)
            except :
                print("[Wait] Network busy, falling back to domcontentloaded...")
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=2000)
                except PlaywrightTimeoutError:
                    pass
            
            observation_response = perception.observe()
            
            obs_text = observation_response
            if "observation:" in observation_response:
                obs_text = observation_response.split("observation:")[1].strip()
            
            action_results["observation"] = obs_text
            return action_results
        except Exception as e:
            action_results["observation"] = f"error taking observation: {str(e)}"
            return action_results