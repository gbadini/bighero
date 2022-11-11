from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import parametros
Base = declarative_base()

# MONTA TABELA "PROCESSO PLATAFORMA"
class ProcessoPlataformaTable(Base):
    __tablename__ = "processo_plataforma"
    plp_id = Column(Integer, primary_key=True, autoincrement=True)
    plp_prc_id = Column(INTEGER)
    plp_plt_id = Column(INTEGER)
    plp_numero = Column(VARCHAR(40))
    plp_status = Column(NVARCHAR(30))
    plp_comarca = Column(NVARCHAR(30))
    plp_serventia = Column(NVARCHAR(50))
    plp_juizo = Column(VARCHAR(150))
    plp_fase = Column(NVARCHAR(55))
    plp_diligencia = Column(NVARCHAR(55))
    plp_vara = Column(NVARCHAR(250))
    plp_filtro = Column(BOOLEAN)
    plp_penhora = Column(BOOLEAN)
    plp_valor_causa = Column(NUMERIC)
    plp_valor_condenacao = Column(NUMERIC)
    plp_classe = Column(VARCHAR(100))
    plp_assunto = Column(NVARCHAR(500))
    plp_processo_origem = Column(NVARCHAR(30))
    plp_data_distribuicao = Column(DATETIME)
    plp_data_transito_julgado = Column(DATETIME)
    plp_codigo = Column(VARCHAR(50))
    plp_segredo = Column(BOOLEAN)
    plp_efeito_suspensivo = Column(BOOLEAN)
    plp_prioridade = Column(BOOLEAN)
    plp_localizado = Column(BOOLEAN)
    plp_migrado = Column(BINARY)
    plp_grau = Column(INTEGER)
    plp_data_update = Column(DATETIME)

class ProcessoPlataforma():
    # CONFERE SE O PROCESSO JA FOI ATUALIZADO NA BASE
    @staticmethod
    def compara_ultimo_update(prc_id, data_comparacao):
        s = select([ProcessoPlataformaTable.plp_data_update]).where(column("plp_plt_id") == parametros['plataforma']).where(column("plp_prc_id") == prc_id).where(column("plp_grau") == parametros['grau'])
        result = conn['titanium_dev'].execute(s)
        result = result.fetchone()
        if result:
            if result[0] > data_comparacao:
                return True

        return False

    # ATUALIZA DADOS DO PROCESSO
    @staticmethod
    def update_processo_plataforma(prc_id, plp_id, localizado, dados = {}):
        if plp_id is None:
            s = select([ProcessoPlataformaTable.plp_id]).where(column("plp_plt_id") == parametros['plataforma']).where(column("plp_prc_id") == prc_id).where(column("plp_grau") == parametros['grau'])
            result = conn['titanium_dev'].execute(s)
            result = result.fetchone()
            if result:
                plp_id = result[0]

        if plp_id is None:
            #INSERIR NOVA TUPLA NA PROCESSO_PLATAFORMA
            print('INSERIR NOVA TUPLA NA PROCESSO_PLATAFORMA')
        else:
            #ATUALIZAR DADOS DA PROCESSO_PLATAFORMA
            print('ATUALIZAR DADOS DA PROCESSO_PLATAFORMA')