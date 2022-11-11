from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.database import conn
from Config.helpers import parametros
Base = declarative_base()

# MONTA TABELA "PROCESSO"
class ProcessoTable(Base):
    __tablename__ = "processo"
    prc_id = Column(BIGINT, primary_key=True, autoincrement=True)
    prc_sequencial = Column(VARCHAR(25))
    prc_numero = Column(VARCHAR(35))
    prc_carteira = Column(BIGINT)
    prc_parte_ativa = Column(VARCHAR(100))
    prc_parte_passiva = Column(VARCHAR(100))
    prc_estado = Column(VARCHAR(2))
    prc_objeto1 = Column(VARCHAR(80))
    prc_objeto2 = Column(VARCHAR(80))
    prc_objeto3 = Column(VARCHAR(80))
    prc_objeto4 = Column(VARCHAR(80))
    prc_data_cadastro = Column(DATETIME)
    prc_area = Column(INTEGER)
    prc_penhora = Column(SMALLINT)
    prc_apto_pgto = Column(SMALLINT)
    prc_responsavel = Column(INTEGER)


class Processo():
    # CAPTURA PROCESSOS QUE SERÃO VARRIDOS
    @staticmethod
    def get_processos_varredura(quantidade = 80):
        join = 'left' if int(parametros['grau']) == 1 else 'inner'
        query = "SELECT top {} prc_numero, prc_id, prc_estado, plp_status, cadastro, plp_codigo, plp_data_update," \
            " plp_id, plp_numero,plp_localizado, CASE WHEN plp_data_update is null THEN 0 ELSE 1 END AS novo FROM processo" \
            " {} join processo_plataforma on plp_prc_id = prc_id and plp_plt_id = {} and plp_grau = {}" \
            " OUTER APPLY (select top 1 acp_plp_id,acp_data_cadastro as cadastro from acompanhamento " \
            " where acp_plp_id=plp_id order by acp_data_cadastro desc) acp" \
            " WHERE (plp_localizado is null or plp_localizado > 0) and (plp_data_update<='{}' or plp_data_update is null) and prc_estado = '{}' and  (prc_removido is null or prc_removido = 0) " \
            "  and len(prc_numero) > 12 and prc_area = {} order by plp_id".format(str(quantidade),join, str(parametros['plataforma']), str(parametros['grau'])
                                                                                  , str(parametros['data_varredura']), str(parametros['uf']), str(parametros['area']))
        result = conn['titanium_dev'].execute(query)

        return result.fetchdict()
