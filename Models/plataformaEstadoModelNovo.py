from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
Base = declarative_base()

# MONTA TABELA "PLATAFORMA ESTADO"
class PlataformaEstadoTable(Base) :
    __tablename__ = "plataforma_estado"
    ple_id = Column(INTEGER, primary_key=True, autoincrement=True)
    ple_plt_id = Column(INTEGER)
    ple_uf = Column(VARCHAR(2))
    ple_login = Column(VARCHAR(30))
    ple_senha = Column(VARCHAR(30))
    ple_data = Column(DATETIME)


class PlataformaEstado():
    # CAPTURA USAURIO E SENHA DA PLATAFORMA SELECIONADA
    @staticmethod
    def get_plataforma_estado(uf, plataforma):
        s = select([PlataformaEstadoTable]).where(column("ple_plt_id") == plataforma).where(column("ple_uf") == uf)
        result = conn['titanium_dev'].execute(s)
        result = result.fetchdict()
        return result[0]
