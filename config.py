import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    USER_DB = os.path.join(os.path.dirname(__file__), 'database', 'users.db')
    CALC_DB = os.path.join(os.path.dirname(__file__), 'database', 'calculations.db')
    PLANTS_DB = os.path.join(os.path.dirname(__file__), 'database', 'plants.db')
    LANGUAGES = {'en': 'English', 'es': 'Español'}
    BABEL_DEFAULT_LOCALE = 'es'