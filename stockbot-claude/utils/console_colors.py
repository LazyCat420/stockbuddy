from colorama import init, Fore, Back, Style

# Initialize colorama
init()

class ConsoleColors:
    @staticmethod
    def title(text: str) -> str:
        """Green bold text for titles"""
        return f"{Fore.GREEN}{Style.BRIGHT}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def success(text: str) -> str:
        """Green text for success messages"""
        return f"{Fore.GREEN}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def error(text: str) -> str:
        """Red text for errors"""
        return f"{Fore.RED}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def warning(text: str) -> str:
        """Yellow text for warnings"""
        return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def info(text: str) -> str:
        """Cyan text for info messages"""
        return f"{Fore.CYAN}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def highlight(text: str) -> str:
        """Magenta text for highlighting important info"""
        return f"{Fore.MAGENTA}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def ticker(text: str) -> str:
        """Blue text for ticker symbols"""
        return f"{Fore.BLUE}{Style.BRIGHT}{text}{Style.RESET_ALL}"
    
    @staticmethod
    def metric(text: str) -> str:
        """Yellow bright text for metrics/numbers"""
        return f"{Fore.YELLOW}{Style.BRIGHT}{text}{Style.RESET_ALL}"

# Create a global instance for easy import
console = ConsoleColors() 