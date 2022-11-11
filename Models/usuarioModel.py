from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
import hashlib
Base = declarative_base()

# MONTA TABELA "PARTE"
class UsuarioTable(Base):
    __tablename__ = "usuario"
    usr_id = Column(BIGINT, primary_key=True, autoincrement=True)
    usr_nome = Column(VARCHAR(255))
    usr_login = Column(VARCHAR(100))
    usr_senha = Column(VARCHAR(255))

class Usuario():

    # ATUALIZA DADOS DOS PROCESSOS
    @staticmethod
    def login(base, usr_login, usr_senha):
        '''
        :param int prc_id: id do processo
        :param int plt_id: id do plataforma
        :param bool localizado: o processo foi localizado na varredura?
        :param dict dados: dados do processo
        '''
        usr_senha = hashlib.md5(usr_senha.encode())
        usr_senha = usr_senha.hexdigest()
        s = select([UsuarioTable]).where(column("usr_login") == usr_login).where(column("usr_senha") == usr_senha)
        result = base.execute(s)
        result = result.fetchdict()
        if len(result) == 0:
            return False

        return result[0]
