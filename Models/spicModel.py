from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
import hashlib
Base = declarative_base()

# MONTA TABELA "PARTE"
class SpicTable(Base):
    __tablename__ = "spic"
    spc_id = Column(BIGINT, primary_key=True, autoincrement=True)
    spc_prc_id = Column(INTEGER)
    spc_numero = Column(VARCHAR(100))
    spc_data_min = Column(DATETIME)
    spc_data_max = Column(DATETIME)
    spc_voz = Column(INTEGER)
    spc_sms = Column(INTEGER)
    spc_tempo = Column(INTEGER)

class Spic():

    # INSERE SPIC
    @staticmethod
    def insert(base, dados):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param int plataforma: id do processo
        :param list acompanhamentos: lista de acompanhamentos
        '''

        to_update = []
        return_key = []
        # IDENTIFICA OS SPICS QUE PRECISAM SER ATUALIZADOS
        for spc in dados[:]:
            if spc['spc_id'] is not None:
                to_update.append(spc)
                dados.remove(spc)
            else:
                del spc['spc_id']

        # INSERE OS SPICS EM LOTE
        if len(dados) > 0:
            base.execute(
                SpicTable.__table__.insert(),
                dados
            )
            base.commit()

        # ATUALIZA OS SPICS
        if len(to_update) > 0:
            Spic.update(base, to_update)


    # ATUALIZA SPIC
    @staticmethod
    def update(base, dados):
        for spc in dados:
            acp_id = spc['spc_id']
            del spc['spc_id']

            upd = SpicTable.__table__.update().values(spc).\
                where(column("spc_id") == acp_id)
            base.execute(upd)
            base.commit()

    # LOCALIZA SPIC NA BASE
    @staticmethod
    def select(base, prc_id=None):
        s = select([SpicTable])
        s = s.where(column("spc_prc_id") == prc_id)

        result = base.execute(s)
        result = result.fetchdict()

        return result