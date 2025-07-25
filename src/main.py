from tui.app import DockernautsApp
from config import AppConfig

def main():
    AppConfig()
    DockernautsApp().run()

if __name__ == "__main__":
    main()