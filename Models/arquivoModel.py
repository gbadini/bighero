from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PROCESSO PLATAFORMA"
class ArquivoTable(Base):
    __tablename__ = "arquivo"
    arq_id = Column(Integer, primary_key=True, autoincrement=True)
    arq_tipo = Column(VARCHAR(150))
    arq_data = Column(DATETIME)
    arq_url = Column(VARCHAR(150))
    arq_formato = Column(VARCHAR(100))
    arq_descricao = Column(VARCHAR(100))
    arq_status = Column(VARCHAR(45))
    arq_prc_id = Column(INTEGER)
    arq_modelo = Column(INTEGER)
    arq_adc_id = Column(INTEGER)
    arq_agn_id = Column(INTEGER)
    arq_spc_id = Column(INTEGER)
    arq_pagamento = Column(INTEGER)
    arq_area = Column(VARCHAR(255))
    arq_acp = Column(INTEGER)
    arq_data_upload = Column(DATETIME)
    arq_usr_id = Column(INTEGER)
    arq_consultivo = Column(INTEGER)
    arq_evento = Column(INTEGER)
    arq_processo = Column(INTEGER)
    arq_flw_id = Column(INTEGER)
    arq_ftp = Column(BOOLEAN)
    arq_del = Column(BOOLEAN)

class Arquivo():
    # ATUALIZA ARQUIVOS
    @staticmethod
    def update(base, dados):
        for pra in dados:
            arq_id = pra['arq_id']
            del pra['arq_id']

            upd = ArquivoTable.__table__.update().values(pra).\
                where(column("arq_id") == arq_id)
            base.execute(upd)
            base.commit()

    # SELECIONA ARQUIVOS DO PAGAMENTO
    @staticmethod
    def select_by_pagamento(base, pag_id, ignora_guias=False):
        '''
        :param Session base: conexão de destino
        '''
        s = select([ArquivoTable]).where(column("arq_pagamento") == pag_id)

        if ignora_guias:
            s.where(or_(column("arq_descricao") != 'Guia', column("arq_descricao") == None))

        result = base.execute(s)
        return result.fetchdict()

    # SELECIONA ARQUIVOS DO ARQUIVAMENTO
    @staticmethod
    def select_by_processo(base, arq_processo):
        '''
        :param Session base: conexão de destino
        '''
        s = select([ArquivoTable]).where(column("arq_processo") == arq_processo)

        result = base.execute(s)
        return result.fetchdict()
