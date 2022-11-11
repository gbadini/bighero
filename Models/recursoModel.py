from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PARTE"
class RecursoTable(Base):
    __tablename__ = "recurso"
    rec_id = Column(BIGINT, primary_key=True, autoincrement=True)
    rec_prc_id = Column(INTEGER)
    rec_numero = Column(VARCHAR(50))
    rec_codigo = Column(VARCHAR(50))
    rec_recorrente = Column(VARCHAR(100))
    rec_recorrido = Column(VARCHAR(100))
    rec_orgao = Column(VARCHAR(60))
    rec_assunto = Column(VARCHAR(100))
    rec_status = Column(VARCHAR(50))
    rec_valor = Column(VARCHAR(50))
    rec_segredo = Column(BOOLEAN)
    rec_relator = Column(VARCHAR(100))
    rec_distribuicao = Column(DATETIME)
    rec_plt_id = Column(INTEGER)
    rec_data_update = Column(DATETIME)
    rec_classe = Column(VARCHAR(100))

class Recurso():

    # INSERE NOVO PROCESSO NA BASE
    @staticmethod
    def insert(base, rec_data):
        rec_id = base.execute(
            RecursoTable.__table__.insert(),
            rec_data
        ).inserted_primary_key[0]
        base.commit()

        return rec_id

    # ATUALIZA DADOS DOS PROCESSOS
    @staticmethod
    def update(base, prc_id, rec_id, plataforma, dados):
        '''
        :param int prc_id: id do processo
        :param int plt_id: id do plataforma
        :param bool localizado: o processo foi localizado na varredura?
        :param dict dados: dados do processo
        '''
        dados['rec_plt_id'] = plataforma
        dados['rec_data_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if 'rec_assunto' in dados:
            dados['rec_assunto'] = corta_string(dados['rec_assunto'], 500)
        if 'rec_orgao' in dados:
            dados['rec_orgao'] = corta_string(dados['rec_orgao'], 60)
        if 'rec_classe' in dados:
            dados['rec_classe'] = corta_string(dados['rec_classe'], 100)

        if rec_id is None:
            dados['rec_prc_id'] = prc_id
            rec_id = Recurso.insert(base, dados)
        else:
            upd = RecursoTable.__table__.update().values(dados). \
                where(column("rec_id") == rec_id)
            base.execute(upd)
            base.commit()

        return rec_id

    # ATUALIZA DADOS ESPECIFICOS DOS PROCESSOS
    @staticmethod
    def update_simples(base, rec_id, dados):
        upd = RecursoTable.__table__.update().values(dados). \
            where(column("rec_id") == rec_id)
        base.execute(upd)
        base.commit()

    # LOCALIZA RECURSO NA BASE
    @staticmethod
    def select(base, prc_id=None, rec_codigo=None, rec_numero=None, like=False, rec_plt_id=None):
        where = '1=1 '
        if prc_id is not None:
            where += " and rec_prc_id="+str(prc_id)

        if rec_codigo is not None:
            if like:
                where += " and rec_codigo like '%" + str(rec_codigo) + "%'"
            else:
                where += " and rec_codigo = '" + str(rec_codigo) + "'"

        if rec_numero is not None:
            if like:
                where += " and rec_numero like '%" + str(rec_numero) + "%'"
            else:
                p = rec_numero.lstrip("0")
                p = p.replace('-', '').replace('.', '').replace('/', '')
                where += " and (REPLACE(REPLACE(SUBSTRING(rec_numero, PATINDEX('%[^0]%', rec_numero + '.'), LEN(rec_numero)), '.', ''), '-', '')='" + p + "')"

        if rec_plt_id is not None:
            where += " and rec_plt_id = '" + str(rec_plt_id) + "'"

        query = "select * from recurso dp WITH (NOLOCK) where "+where+" OPTION(QUERYTRACEON 8649)"
        # print(query)
        result = base.execute(query)
        result = result.fetchdict()
        # print(result)
        # s = select([RecursoTable])
        # if prc_id is not None:
        #     s = s.where(column("rec_prc_id") == prc_id)
        #
        # if rec_codigo is not None:
        #     if like:
        #         s = s.where(column('rec_codigo').like('%' + rec_codigo + '%'))
        #     else:
        #         s = s.where(column('rec_codigo') == rec_codigo)
        #
        # if rec_numero is not None:
        #     if like:
        #         s = s.where(column('rec_numero').like('%' + rec_numero + '%'))
        #     else:
        #         s = s.where(column('rec_numero') == rec_numero)
        #
        # if rec_plt_id is not None:
        #     s = s.where(column('rec_plt_id') == rec_plt_id)
        #
        # result = base.execute(s)
        # result = result.fetchdict()

        return result

    # ATUALIZA DADOS ESPECIFICOS DOS PROCESSOS
    @staticmethod
    def delete_rec(base, rec_id):
        upd = RecursoTable.__table__.delete(). \
            where(column("rec_id") == rec_id)
        base.execute(upd)
        base.commit()