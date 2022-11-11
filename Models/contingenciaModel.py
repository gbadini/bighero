from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PROCESSO PLATAFORMA"
class ContingenciaTable(Base):
    __tablename__ = "contingencia"
    ctg_id = Column(Integer, primary_key=True, autoincrement=True)
    ctg_prc_id = Column(INTEGER)
    ctg_jan_id = Column(INTEGER)
    ctg_valor_possivel = Column(FLOAT)
    ctg_valor_remoto = Column(FLOAT)
    ctg_lancado = Column(BOOLEAN)
    ctg_erro = Column(VARCHAR(100))
    ctg_data_insert = Column(DATETIME)
    ctg_data_lancamento = Column(DATETIME)
    ctg_data_aprovacao = Column(DATETIME)
    ctg_arq_id = Column(INTEGER)
    ctg_usr_id = Column(INTEGER)
    ctg_data_citacao = Column(DATETIME)
    ctg_lancar = Column(BOOLEAN)

class Contingencia():
    # SELECIONA CONTINGENCIAS NÃO LANÇADAS
    @staticmethod
    def select_nao_lancados(base, prc_id):
        '''
        :param Session base: conexão de destino
        '''
        s = select([ContingenciaTable]).where(column("ctg_prc_id") == prc_id)\
            .where(or_(column("ctg_lancado") == False, column("ctg_lancado") == None))

        result = base.execute(s)
        return result.fetchdict()

    # SELECIONA CONTINGENCIAS NÃO LANÇADAS
    @staticmethod
    def select_by_data_citacao(base, prc_id, data_citacao):
        '''
        :param Session base: conexão de destino
        '''
        data_citacao = data_citacao.strftime('%Y-%m-%d %H:%M:%S')
        query = """	select * from contingencia 
                    where ((ctg_data_citacao is NULL and (ctg_lancado is NULL or (ctg_lancado=0 and ctg_erro is NULL))) or ctg_data_citacao = '"""+data_citacao+"""')
                    and ctg_prc_id="""+str(prc_id)

        result = base.execute(query)
        return result.fetchdict()

        # s = select([ContingenciaTable]).where(column("ctg_prc_id") == prc_id)\
        #     .where(or_(column("ctg_data_citacao") == data_citacao, column("ctg_data_citacao") == None))
        #
        # result = base.execute(s)
        # return result.fetchdict()

    # INSERE CONTINGENCIA
    @staticmethod
    def insert(base, dados):
        '''
        :param Session base: conexão de destino
        :param list dados: lista de audiencias
        '''
        if len(dados) == 0:
            return

        for d in dados:
            d['ctg_data_insert'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        base.execute(
            ContingenciaTable.__table__.insert(),
            dados
        )
        base.commit()

    # ATUALIZA CONTINGENCIA
    @staticmethod
    def update(base, ctg_id, dados):
        upd = ContingenciaTable.__table__.update().values(dados).\
            where(column("ctg_id") == ctg_id)
        base.execute(upd)
        base.commit()