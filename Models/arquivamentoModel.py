from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PROCESSO PLATAFORMA"
class ArquivamentoTable(Base):
    __tablename__ = "arquivamento"
    aqm_id = Column(Integer, primary_key=True, autoincrement=True)
    aqm_prc_id = Column(INTEGER)
    aqm_data_aprovacao = Column(DATETIME)
    aqm_data_lancamento = Column(DATETIME)
    aqm_lancado = Column(BOOLEAN)
    aqm_erro = Column(VARCHAR(100))

class Arquivamento():

    # ATUALIZA ARQUIVAMENTO
    @staticmethod
    def update(base, aqm_id, dados):
        dados['aqm_data_lancamento'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        upd = ArquivamentoTable.__table__.update().values(dados).\
            where(column("aqm_id") == aqm_id)
        base.execute(upd)
        base.commit()
