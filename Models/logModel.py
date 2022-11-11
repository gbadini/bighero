from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
import hashlib
Base = declarative_base()

# MONTA TABELA "PARTE"
class LogTable(Base):
    __tablename__ = "log"
    # log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    log_data = Column(DATETIME, primary_key=True)
    log_nivel = Column(VARCHAR(15))
    log_mensagem = Column(VARCHAR(100))
    log_usuario = Column(VARCHAR(30))
    log_login = Column(VARCHAR(20))
    log_sistema = Column(VARCHAR(20))
    log_uf = Column(VARCHAR(2))
    log_escritorio = Column(VARCHAR(10))
    log_prc_id = Column(INTEGER)
    log_ip = Column(VARCHAR(20))

class Log():

    # ATUALIZA DADOS DOS PROCESSOS
    @staticmethod
    def insert(base, dados):
        '''
        :param dict dados: dados do processo
        '''
        log_data = []
        for dt in dados:
            log_prc_id = None if dt[8] == '' else dt[8]
            log_data.append({'log_data': datetime.strptime(dt[0], '%Y-%m-%d %H:%M:%S,%f'), 'log_nivel': dt[1], 'log_mensagem': dt[2], 'log_usuario': dt[3], 'log_login': dt[4], 'log_sistema': dt[5], 'log_uf': dt[6], 'log_escritorio': dt[7], 'log_prc_id': log_prc_id})

        base.execute(
            LogTable.__table__.insert(),
            log_data
        )
        base.commit()

    # CAPTURA DADOS DO SQLITE
    @staticmethod
    def select_sqlite(base):
        '''
        :param dict dados: dados do processo
        '''
        try:
            cur = base.cursor()
            cur.execute("SELECT * FROM log")
        except:
            return []

        return cur.fetchall()

    # ATUALIZA DADOS DOS PROCESSOS
    @staticmethod
    def clear(base):
        '''
        :param dict dados: dados do processo
        '''
        cur = base.cursor()
        cur.execute("DELETE FROM log")
        base.commit()
        base.close()