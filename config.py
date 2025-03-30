import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Meghana%4028@localhost/evchargingapp'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)
