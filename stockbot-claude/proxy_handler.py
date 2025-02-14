from typing import Optional, List
import random
import requests
from datetime import datetime, timedelta

class ProxyHandler:
    def __init__(self):
        self.proxies = []
        self.last_update = None
        self.update_interval = timedelta(hours=1)
        
    def _fetch_proxies(self) -> None:
        """Fetch fresh proxies from free proxy lists"""
        try:
            # Add multiple proxy sources for redundancy
            sources = [
                "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
            ]
            
            new_proxies = set()
            for source in sources:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxies = response.text.strip().split('\n')
                    new_proxies.update(proxies)
            
            self.proxies = list(new_proxies)
            self.last_update = datetime.now()
            print(f"Updated proxy list with {len(self.proxies)} proxies")
            
        except Exception as e:
            print(f"Error fetching proxies: {str(e)}")
    
    def get_proxy(self) -> Optional[dict]:
        """Get a random proxy from the list"""
        if not self.proxies or (self.last_update and datetime.now() - self.last_update > self.update_interval):
            self._fetch_proxies()
        
        if not self.proxies:
            return None
            
        proxy = random.choice(self.proxies)
        return {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
    
    def remove_proxy(self, proxy: dict) -> None:
        """Remove a failed proxy from the list"""
        if proxy:
            proxy_addr = proxy["http"].replace("http://", "")
            if proxy_addr in self.proxies:
                self.proxies.remove(proxy_addr)
                print(f"Removed failed proxy: {proxy_addr}") 