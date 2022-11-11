from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()


# MONTA TABELA "ENDERECO"
class EnderecoTable(Base):
    __tablename__ = "endereco"
    end_id = Column(Integer, primary_key=True, autoincrement=True)
    end_prc_id = Column(INTEGER)
    end_contato = Column(NVARCHAR(100))
    end_logradouro = Column(NVARCHAR(100))
    end_numero = Column(NVARCHAR(30))
    end_complemento = Column(NVARCHAR(30))
    end_bairro = Column(NVARCHAR(60))
    end_cidade = Column(NVARCHAR(60))
    end_uf = Column(NVARCHAR(2))
    end_cep = Column(NVARCHAR(10))
    end_origem = Column(NVARCHAR(30))


class Endereco():
    @staticmethod
    def select(base, prc_id, end_cep = None, end_logradouro = None, end_numero = None):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        '''
        s = select([EnderecoTable]).where(column("end_prc_id") == prc_id)

        if end_cep is not None:
            s = s.where(column("end_cep") == end_cep)

        if end_logradouro is not None:
            s = s.where(column("end_logradouro") == end_logradouro)

        if end_numero is not None:
            s = s.where(column("end_numero") == end_numero)

        result = base.execute(s)
        return result.fetchdict()

    # INSERE ENDERECO
    @staticmethod
    def insert(base, dados):
        '''
        :param Session base: conexão de destino
        :param list dados: lista de audiencias
        '''
        if len(dados) == 0:
            return

        base.execute(
            EnderecoTable.__table__.insert(),
            dados
        )
        base.commit()