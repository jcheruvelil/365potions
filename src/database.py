import os
import dotenv
import sqlalchemy
from sqlalchemy import create_engine

def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)

def get_gold():
    with engine.begin() as connection:
        return connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).one()[0]

def get_green_potions():
    with engine.begin() as connection:
        return connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).one()[0]
    
def get_red_potions():
    with engine.begin() as connection:
        return connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).one()[0]
    
def get_blue_potions():
    with engine.begin() as connection:
        return connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).one()[0]
    
def get_green_ml():
    with engine.begin() as connection:
        return connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).one()[0]

def get_red_ml():
    with engine.begin() as connection:
        return connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).one()[0]
    
def get_blue_ml():
    with engine.begin() as connection:
        return connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).one()[0]
