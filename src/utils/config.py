from pathlib import Path

class AppConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.project_root = self.set_project_root_env_var()
        self._initialized = True

    def set_project_root_env_var(self) -> str:
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[1]
        return str(project_root)

    def get_config(self) -> dict:
        return {
            "root": self.project_root
        }
