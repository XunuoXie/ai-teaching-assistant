
import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'outputs')
    SANDBOX_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sandbox_temp')
    
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_API_BASE_URL = os.getenv('OPENAI_API_BASE_URL', 'https://api.deepseek.com/v1/chat/completions')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'deepseek-v4-flash')
    
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', 300))
    CODE_EXECUTION_TIMEOUT = int(os.getenv('CODE_EXECUTION_TIMEOUT', 600))

    DEFAULT_TEACHER_USERNAME = os.getenv('DEFAULT_TEACHER_USERNAME', '')
    XUETANG_TEACHER_CPIS = os.getenv('XUETANG_TEACHER_CPIS', '')
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        os.makedirs(Config.SANDBOX_BASE, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
