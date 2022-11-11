from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PARTE"
class PlataformaTable(Base):
    __tablename__ = "plataforma"
    plt_id = Column(BIGINT, primary_key=True, autoincrement=True)
    plt_estado = Column(VARCHAR(2))
    plt_codigo = Column(INTEGER)
    plt_ultima_consulta = Column(DATETIME)
    plt_usuario = Column(VARCHAR(100))
    plt_senha = Column(VARCHAR(100))
    plt_usuario2 = Column(VARCHAR(100))
    plt_senha2 = Column(VARCHAR(100))
    plt_usuario3 = Column(VARCHAR(100))
    plt_senha3 = Column(VARCHAR(100))
    plt_token = Column(VARCHAR(100))

class Plataforma():
    # CONFERE E INSERE PARTES
    @staticmethod
    def select(base, plt_codigo, plt_estado):
        '''
        :param Session base: conexão de destino
        :param int plt_codigo: codigo da plataforma
        :param str plt_estado: sigla do estado (uf)
        '''
        if plt_estado == '*':
            s = select([PlataformaTable]).where(column("plt_codigo") == plt_codigo)
        else:
            if plt_estado.upper().find('TRT') > -1:
                plt_estado = 'TRT'

            s = select([PlataformaTable]).where(column("plt_codigo") == plt_codigo).where(column("plt_estado") == plt_estado)
        result = base.execute(s)
        return result.fetchdict()

    @staticmethod
    def update(base, plt_codigo, plt_estado):
        '''
        :param Session base: conexão de destino
        :param int plt_codigo: codigo da plataforma
        :param str plt_estado: sigla do estado (uf)
        '''
        dados = {}
        dados['plt_ultima_consulta'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        upd = PlataformaTable.__table__.update().values(dados). \
            where(column("plt_codigo") == plt_codigo).where(column("plt_estado") == plt_estado)
        base.execute(upd)
        base.commit()

    @staticmethod
    def update_password(base, plt_codigo, plt_estado, campo_senha, nova_senha):
        '''
        :param Session base: conexão de destino
        :param int plt_codigo: codigo da plataforma
        :param str plt_estado: sigla do estado (uf)
        :param str campo_senha: nome do campo de senha
        :param str nova_senha: nova senha
        '''
        dados = {}
        dados['plt_ultima_consulta'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        upd = PlataformaTable.__table__.update().values({campo_senha: nova_senha}). \
            where(column("plt_codigo") == plt_codigo).where(column("plt_estado") == plt_estado)

        while True:
            try:
                base.execute(upd)
                base.commit()
                return True
            except Exception as e:
                tb = traceback.format_exc()
                print('tb')
                if tb.find('vínculo de comunicação') > -1 or tb.find('tempo limite de espera') > -1:
                    print('Erro no vínculo da conexão. Aguardando para tentar novamente')
                    base.rollback()
                    time.sleep(30)
                    continue
                raise Exception

    # CONFERE E INSERE PARTES
    @staticmethod
    def check_data_user(base, plt_codigo, ordem_user):
        '''
        :param Session base: conexão de destino
        :param int plt_codigo: codigo da plataforma
        :param str plt_estado: sigla do estado (uf)
        '''
        trinta_dias = mes_anterior()
        print('trinta_dias',trinta_dias)
        s = select([PlataformaTable]).where(column("plt_codigo") == plt_codigo).where(column("plt_data_senha"+str(ordem_user)) <= trinta_dias)
        result = base.execute(s)

        return result.fetchdict()

