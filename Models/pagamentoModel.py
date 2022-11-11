from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PAGAMENTO"
class PagamentoTable(Base):
    __tablename__ = "pagamento"
    pag_id = Column(Integer, primary_key=True, autoincrement=True)
    pag_prc_id = Column(BIGINT)
    pag_conta_contabil = Column(VARCHAR(40))
    pag_descricao = Column(VARCHAR(200))
    pag_prazo = Column(DATE)
    pag_publicacao = Column(DATE)
    pag_tipo = Column(VARCHAR(40))
    pag_tipo_multa = Column(VARCHAR(50))
    pag_valor_multa = Column(FLOAT)
    pag_n_id = Column(VARCHAR(25))
    pag_favorecido = Column(VARCHAR(100))
    pag_cpf_favorecido = Column(VARCHAR(25))
    pag_tipo_pagamento = Column(VARCHAR(25))
    pag_esp_tipo = Column(VARCHAR(25))
    pag_banco = Column(VARCHAR(25))
    pag_agencia = Column(VARCHAR(25))
    pag_agencia_digito = Column(VARCHAR(5))
    pag_conta = Column(VARCHAR(25))
    pag_conta_digito = Column(VARCHAR(10))
    pag_jan_id = Column(INTEGER)
    pag_valor_pos = Column(FLOAT)
    pag_valor_rem = Column(FLOAT)
    pag_valor_op = Column(FLOAT)
    pag_valor_fin = Column(FLOAT)
    pag_valor = Column(FLOAT)
    pag_n_banco = Column(FLOAT)
    pag_data_fav = Column(DATE)
    pag_e_tipo = Column(INTEGER)
    pag_de_tipo = Column(INTEGER)
    pag_p_valor = Column(FLOAT)
    pag_data = Column(DATE)
    pag_tipo2 = Column(VARCHAR(50))
    pag_liberado = Column(VARCHAR(1))
    pag_contingenciamento = Column(VARCHAR(100))
    pag_prov_op = Column(FLOAT)
    pag_prov_fin = Column(FLOAT)
    pag_reavaliacao = Column(FLOAT)
    pag_data_cadastro = Column(DATE)
    pag_provisionado = Column(BOOLEAN)
    pag_pago = Column(BOOLEAN)
    pag_data_sentenca = Column(DATE)
    pag_data_tjulgado = Column(DATE)
    pag_data_limite = Column(DATE)
    pag_lancado = Column(BOOLEAN)
    pag_aprovado = Column(BOOLEAN)
    pag_executor = Column(INTEGER)
    pag_aguardando_guia = Column(BOOLEAN)
    pag_data_envio = Column(DATE)
    pag_pai = Column(VARCHAR(60))
    pag_apagado = Column(BOOLEAN)
    pag_usr_apagou = Column(INTEGER)
    pag_plan_op = Column(FLOAT)
    pag_plan_fin = Column(FLOAT)
    pag_confirmacao = Column(BOOLEAN)
    pag_erro = Column(VARCHAR(100))
    pag_subindo = Column(BOOLEAN)
    pag_pre_lancado = Column(BOOLEAN)
    pag_responsavel = Column(INTEGER)
    pag_data_lancamento = Column(DATETIME)

class Pagamento():
    # CONFERE SE O PAGAMENTO JA FOI/ ESTÁ SENDO LANÇADO
    @staticmethod
    def select_lancado(base, pag_id):
        '''
        :param Session base: conexão de destino
        :param int pag_id: id do pagamento
        '''

        s = select([PagamentoTable]).where(column("pag_id") == pag_id)\
            .where(or_(column("pag_lancado") == True, column("pag_subindo") == True))

        result = base.execute(s)
        return result.fetchdict()

    # SELECIONAS OUTRAS PAGAMENTOS QUE SERÃO LANÇADOS NO MESMO PRAZO
    @staticmethod
    def select_by_prazo(base, prc_id, pag_prazo):
        '''
        :param Session base: conexão de destino
        :param int pag_id: id do pagamento
        '''

        s = select([PagamentoTable]).where(column("pag_prc_id") == prc_id)\
            .where(column("pag_prazo") == pag_prazo) \
            .where(column("pag_liberado") == True) \
            .where(or_(column("pag_apagado") == None, column("pag_apagado") == True))

        result = base.execute(s)
        return result.fetchdict()


    # ATUALIZA PAGAMENTO
    @staticmethod
    def update(base, pag_id, dados):
        '''
        :param Session base: conexão de destino
        :param int pag_id: id do pagamento
        :param dict dados: dicionatio de dados
        '''

        upd = PagamentoTable.__table__.update().values(dados).\
            where(column("pag_id") == pag_id)
        base.execute(upd)
        base.commit()

    # CONFERE SE O PAGAMENTO JA FOI/ ESTÁ SENDO LANÇADO
    @staticmethod
    def select_by_provisionamento(base, prc_id, jan_id):
        '''
        :param Session base: conexão de destino
        :param int pag_id: id do pagamento
        '''
        query = """select * from pagamento
                    where (pag_provisionado is null or pag_provisionado = 0) and (pag_apagado is null or pag_apagado = 0) 
                    and (pag_erro is null or pag_erro='') and pag_jan_id = """+str(jan_id)+"""
                    and pag_prc_id = """ + str(prc_id)

        result = base.execute(query)
        return result.fetchdict()