from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PROCESSO PLATAFORMA"
class SentencaTable(Base):
    __tablename__ = "sentenca"
    stc_id = Column(Integer, primary_key=True, autoincrement=True)
    stc_prc_id = Column(INTEGER)
    stc_tipo = Column(INTEGER)
    stc_valor = Column(FLOAT)
    stc_resultado = Column(VARCHAR(25))
    stc_data = Column(DATE)
    stc_recorrente = Column(VARCHAR(40))
    stc_data_cadastro = Column(DATETIME)
    stc_usr_id = Column(INTEGER)
    stc_motivo = Column(VARCHAR(500))
    stc_dano_moral = Column(FLOAT)
    stc_dano_material = Column(FLOAT)
    stc_lucros_cessantes = Column(FLOAT)
    stc_restituicao = Column(FLOAT)
    stc_multa = Column(FLOAT)
    stc_honorarios = Column(FLOAT)
    stc_motivo_arquivamento = Column(VARCHAR(80))

class Sentenca():

    # SELECIONA SENTENCA DO PROCESSO
    @staticmethod
    def select_by_prc_id(base, prc_id):
        '''
        :param Session base: conexão de destino
        '''
        query = """select s1.stc_resultado resultado_principal, s1.stc_motivo motivo_principal,s2.stc_motivo motivo_julgamento, s1.stc_motivo_arquivamento motivo_arquivamento 
                        from sentenca s1
						inner join sentenca s2 on s2.stc_tipo=1 and s2.stc_prc_id = s1.stc_prc_id
						where s1.stc_tipo=3 and s1.stc_prc_id="""+str(prc_id)

        result = base.execute(query)
        return result.fetchdict()


