from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PROCESSO PLATAFORMA"
class JanelaTable(Base):
    __tablename__ = "janela"
    jan_id = Column(Integer, primary_key=True, autoincrement=True)
    jan_prov_inicio = Column(DATE)
    jan_prov_fim = Column(DATE)
    jan_pre_fim = Column(DATE)
    jan_valor = Column(FLOAT)
    jan_mesano = Column(VARCHAR(10))
    jan_insercao = Column(VARCHAR(10))
    jan_planilha = Column(BOOLEAN)
    jan_data_insercao = Column(DATE)
    jan_data_evento = Column(DATE)
    jan_data_evento2 = Column(DATE)
    jan_data_evento3 = Column(DATE)
    jan_atual = Column(BOOLEAN)
    jan_data_lancamento = Column(DATE)


class Janela():
    # SELECIONA JANELA ATUAL
    @staticmethod
    def select_by_atual(base):
        '''
        :param Session base: conexão de destino
        '''
        s = select([JanelaTable]).where(column("jan_atual") == True)

        result = base.execute(s)
        return result.fetchdict()

    # SELECIONA JANELA FUTURA
    @staticmethod
    def select_by_futura(base):
        '''
        :param Session base: conexão de destino
        '''
        s = select([JanelaTable]).where(column("jan_futura") == True)

        result = base.execute(s)
        return result.fetchdict()