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

class Ocorrencia():

    # CAPTURA DADOS DO SQLITE
    @staticmethod
    def select_sqlite(base, ocr_plt_id=1):
        '''
        :param dict dados: dados do processo
        '''

        cur = base.cursor()
        cur.execute("SELECT ocr_tipo, ocr_esp, ocr_tipo_alt, ocr_esp_alt, ocr_documento, ocr_documento_alt, ocr_chave_inicio, ocr_chave_exata, ocr_chave_qualquer, ocr_chave_not FROM ocorrencia where ocr_plt_id="+str(ocr_plt_id))
        return cur.fetchall()
