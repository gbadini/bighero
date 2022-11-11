from sqlalchemy import *
import urllib.parse
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

#CONECTA NA BASE SELECIONADA E RETORNA A SESSÃO
def connect_db(db, ip='45.178.181.49,1535',user='sa',senha='BEC@db521'):
# def connect_db(db, ip='201.47.170.196',user='sa',senha='BEC@db521'):
    '''
    :param str db: Nome da Base
    '''

    params = urllib.parse.quote_plus("DRIVER={ODBC Driver 17 for SQL Server};"
                                     "SERVER="+ip+";"
                                     "DATABASE="+db+";"
                                     "UID="+user+";"
                                     "PWD="+senha+""
                                     )

    engine = create_engine("mssql+pyodbc:///?odbc_connect={}".format(params), fast_executemany=True)
    return sessionmaker(bind=engine)

#CONECTA NA BASE DE LOG EM SQLITE
def connect_sqlite(db):
    '''
    :param str db: Nome da Base
    '''
    import sqlite3
    try:
        return sqlite3.connect(db)
    except:
        return False

