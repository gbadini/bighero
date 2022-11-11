from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PROCESSO PARTE"
class ProcessoParteTable(Base):
    __tablename__ = "processo_parte"
    ppt_id = Column(BIGINT, primary_key=True, autoincrement=True)
    ppt_prt_id = Column(BIGINT)
    ppt_prc_id = Column(BIGINT)
    ppt_tipo = Column(VARCHAR(30))
    ppt_polo = Column(VARCHAR(20))
    ppt_plt_id = Column(INTEGER)


class ProcessoParte():
    # INSERE VINCULO ENTRE PROCESSO E PARTES
    @staticmethod
    def insert(base, partes):
        base.execute(
            ProcessoParteTable.__table__.insert(),
            partes
        )
        base.commit()

    # APAGA VINCULO ENTRE PROCESSO E PARTES
    @staticmethod
    def delete(base, ids):
        '''
        :param Session base: conexão de destino
        :param list ids: lista de ids que será apagados
        '''
        delete_q = ProcessoParteTable.__table__.delete().where(ProcessoParteTable.ppt_id.in_(ids))
        base.execute(delete_q)
        base.commit()
