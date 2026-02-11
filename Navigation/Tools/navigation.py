from Navigation.Browser.manager import BrowserManager
from Navigation.Tools.Models.element import ElementStore


class NavigationTools:
    def __init__(
            self,
            session: BrowserManager,
        ):
        
        self.session = session

    #open page tool
    def open_page(self, url: str):
        """
            Opens a web page given its URL.
            
            Args:
                url (str): The URL of the web page to open.
        """
        try:
            self.session.start()
            page = self.session.get_page()

            if not url.startswith("http"):
                url = "https://" + url
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )
        except Exception as e:
            print(f"Error starting session or getting page: {str(e)}")
            return {"status": "error", "reason": f"{str(e)}"}
        
    #close browser tool
    def close_browser(self):
        """
            Closes the browser session.
        """
        try:
            self.session.close()
        except Exception as e:
            print(f"Error closing browser session: {str(e)}")
            return {"status": "error", "reason": f"{str(e)}"}

