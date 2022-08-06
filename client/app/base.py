#there's probably a better way to do this, but the Base is needed in other files
from sqlalchemy.orm import declarative_base

Base = declarative_base()