from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
Base = declarative_base()

# MONTA TABELA "PROCESSO PLATAFORMA"
class ProcessoArquivoTable(Base):
    __tablename__ = "processo_arquivo"
    pra_id = Column(Integer, primary_key=True, autoincrement=True)
    pra_prc_id = Column(INTEGER)
    pra_rec_id = Column(INTEGER)
    pra_acp_id = Column(INTEGER)
    pra_id_tj = Column(VARCHAR(30))
    pra_plt_id = Column(INTEGER)
    pra_plp_id = Column(INTEGER)
    pra_tentativas = Column(INTEGER)
    pra_arquivo = Column(VARCHAR(100))
    pra_original = Column(VARCHAR(100))
    pra_descricao = Column(NVARCHAR(200))
    pra_erro = Column(BOOLEAN)
    pra_usuario = Column(NVARCHAR(100))
    pra_grau = Column(INTEGER)
    pra_excluido = Column(BOOLEAN)
    pra_sigilo = Column(BOOLEAN)
    pra_data = Column(DATETIME)
    pra_data_insert = Column(DATETIME)
    pra_ocorrencia = Column(BOOLEAN)
    pra_legado = Column(BOOLEAN)


class ProcessoArquivo():
    # INSERE ARQUIVOS
    @staticmethod
    def insert(base, arquivos):
        '''
        :param Session base: conexão de destino
        :param list partes: lista de partes
        '''
        if len(arquivos) == 0:
            return

        upd_list = []
        for arq in arquivos[:]:
            arq['pra_plp_id'] = None
            arq['pra_legado'] = None
            if 'pra_arquivo' in arq:
                if arq['pra_arquivo'] is not None:
                    arq['pra_arquivo'] = corta_string(arq['pra_arquivo'],100)
            if 'pra_original' in arq:
                if arq['pra_original'] is not None:
                    arq['pra_original'] = corta_string(arq['pra_original'], 100)
            if 'pra_descricao' in arq:
                if arq['pra_descricao'] is not None:
                    arq['pra_descricao'] = corta_string(arq['pra_descricao'], 200)
            if 'pra_usuario' in arq:
                if arq['pra_usuario'] is not None:
                    arq['pra_usuario'] = corta_string(arq['pra_usuario'], 100)

            if 'pra_tentativas' not in arq or arq['pra_tentativas'] is None:
                arq['pra_tentativas'] = 1

            if arq['pra_erro']:
                if arq['pra_tentativas'] == 12:
                    arq['pra_erro'] = False
                    arq['pra_excluido'] = True

            arq['pra_data_insert'] = datetime.now()
            if 'pra_id' in arq:
                if arq['pra_id'] is None:
                    del arq['pra_id']
                else:
                    upd_list.append(arq)
                    arquivos.remove(arq)
                continue

        for upd in upd_list:
            pra_id = upd['pra_id']
            del upd['pra_id']
            qry = ProcessoArquivoTable.__table__.update().values(upd). \
                where(column("pra_id") == pra_id)
            base.execute(qry)
            base.commit()

        if len(arquivos) > 0:
            base.execute(
                ProcessoArquivoTable.__table__.insert(),
                arquivos
            )
            base.commit()

    # BUSCA ARQUIVOS VINCULADOS AO PROCESSO
    @staticmethod
    def select(base, prc_id, pra_plt_id, pra_grau=None, pra_rec_id=None):
        # print(prc_id, pra_plt_id, pra_grau, pra_rec_id)
        s = select([ProcessoArquivoTable]).where(column("pra_prc_id") == prc_id).where(column("pra_plt_id") == pra_plt_id)
        if pra_grau is not None:
            s = s.where(column("pra_grau") == pra_grau)
        if pra_rec_id is not None:
            s = s.where(column("pra_rec_id") == pra_rec_id)

        s = s.order_by(desc(column("pra_data")))
        result = base.execute(s)
        # print(result)
        return result.fetchdict()

    # BUSCA ARQUIVOS VINCULADOS AO ACOMPANHAMENTO
    @staticmethod
    def select_by_acp(base, acp_id, somente_casos_com_erro=False):
        if somente_casos_com_erro:
            s = select([ProcessoArquivoTable]).where(column("pra_acp_id") == acp_id).where(column("pra_erro") == 1)

        else:
            s = select([ProcessoArquivoTable]).where(column("pra_acp_id") == acp_id)

        result = base.execute(s)
        return result.fetchdict()

    # BUSCA ARQUIVOS VINCULADOS AO ACOMPANHAMENTO
    @staticmethod
    def select_by_date(base, acp_id, plataforma, considerar_segundos=True):

        if considerar_segundos:
            query = "select * from processo_arquivo pa "\
                    "inner join acompanhamento a on acp_processo=pra_prc_id and pra_data = acp_cadastro "\
                    "where (pra_ocorrencia is NULL or pra_ocorrencia = 0) and (pra_erro is NULL or pra_erro = 0) and pra_arquivo is not NULL and (pra_excluido is NULL or pra_excluido = 0) and pra_plt_id = "+str(plataforma)+" and acp_id="+str(acp_id)
        else:
            query = "select * from processo_arquivo pa " \
                    "inner join acompanhamento a on acp_processo=pra_prc_id and DATEADD(MINUTE, DATEDIFF(MINUTE, 0, pra_data), 0) = DATEADD(MINUTE, DATEDIFF(MINUTE, 0, acp_cadastro), 0)" \
                    "where (pra_ocorrencia is NULL or pra_ocorrencia = 0) and pra_arquivo is not NULL and (pra_erro is NULL or pra_erro = 0) and (pra_excluido is NULL or pra_excluido = 0) and pra_plt_id = " + str(
                plataforma) + " and acp_id=" + str(acp_id)

        # print(query)
        result = base.execute(query)
        return result.fetchdict()

    # SELECIONA TODOS OS ARQUIVOS VÁLIDOS JÁ EXISTENTES DO PROCESSO
    @staticmethod
    def select_arquivos_entrantes(base, prc_id):
        query = """select * from processo_arquivo pa 
                    where pra_prc_id = """+str(prc_id)+""" 
                    and pra_plt_id not in (1,8,11) and (pra_excluido is NULL or pra_excluido=0) and (pra_sigilo is NULL or pra_sigilo=0) 
                    and (pra_erro is NULL or pra_erro=0) order by pra_data asc"""
        result = base.execute(query)
        result = result.fetchdict()
        return result

    # CONFERE SE EXISTE ALGUM ARQUIVO JA LANÇADO
    @staticmethod
    def confere_arquivos_entrantes(base, prc_id):
        query = """select * from processo_arquivo pa 
                    where pra_prc_id = """+str(prc_id)+""" 
                    and pra_plt_id not in (1,8,11) order by pra_data"""
        result = base.execute(query)
        result = result.fetchdict()

        if len(result) == 0:
            return False

        quant_erro = 0
        primeiro_nulo = False
        inicio = True
        for i, r in enumerate(result):
            if r['pra_erro'] is not None and r['pra_erro']:
                quant_erro += 1

            if i <= 8 and quant_erro >= 5:
                return 'não varrer'

            if inicio and ((r['pra_ocorrencia'] is not None and not r['pra_ocorrencia']) or (r['pra_erro'] is not None and r['pra_erro'])):
                continue

            if inicio and r['pra_ocorrencia'] is None:
                primeiro_nulo = True

            inicio = False

            if not primeiro_nulo:
                if r['pra_ocorrencia'] is not None:
                    return False

        return result[-1]


    # BUSCA ARQUIVOS VINCULADOS AO ACOMPANHAMENTO
    @staticmethod
    def select_arquivos_vinculados(base, prc_id, prc_estado=''):
        query = """select * from processo_arquivo pa 
                    where pra_prc_id = """+str(prc_id)+""" 
                    and pra_plt_id not in (1,8,11) order by pra_data"""


        # and pra_ocorrencia is NULL
        # print(query)
        result = base.execute(query)
        result = result.fetchdict()
        procs = {}
        for r in result:
            if r['pra_data'] is None and (r['pra_excluido'] or r['pra_erro']):
                continue

            if r['pra_data'] is None:
                continue

            if r['pra_plt_id'] not in procs:
                procs[r['pra_plt_id']] = {}

            if r['pra_plt_id'] in (5,) or (prc_estado == 'BA' and r['pra_plt_id'] == 3) or (prc_estado == 'RS' and r['pra_plt_id'] == 9):
                r['pra_data'] = r['pra_data'].replace(hour=00, minute=00, second=00)
            d = r['pra_data'].strftime('%d/%m/%Y')
            h = r['pra_data'].strftime('%H:%M')
            if d not in procs[r['pra_plt_id']]:
                procs[r['pra_plt_id']][d] = {}

            if h not in procs[r['pra_plt_id']][d]:
                procs[r['pra_plt_id']][d][h] = {'1':[],'2':[]}

            if r['pra_grau'] == 1:
                procs[r['pra_plt_id']][d][h]['1'].append(r)
            else:
                procs[r['pra_plt_id']][d][h]['2'].append(r)


        return procs

    # ATUALIZA ARQUIVOS
    @staticmethod
    def update(base, dados):
        for pra in dados:
            acp_id = pra['pra_id']
            del pra['pra_id']

            upd = ProcessoArquivoTable.__table__.update().values(pra).\
                where(column("pra_id") == acp_id)
            base.execute(upd)
            base.commit()

    # ATUALIZA DADOS ESPECIFICOS DOS PROCESSOS
    @staticmethod
    def update_batch(base, pras, dados):
        if len(pras) == 0:
            return

        pra_ids = []
        for arq in pras:
            pra_ids.append(arq['pra_id'])
        for i in range(0, len(pra_ids), 800):
            ids_para_update = pra_ids[i:i + 800]
            upd = ProcessoArquivoTable.__table__.update().values(dados). \
                where(column("pra_id").in_(ids_para_update))

            base.execute(upd)
            base.commit()

    # ATUALIZA ARQUIVOS
    @staticmethod
    def update_by_date(base, prc_id, pra_data, plataforma, dados):
        upd = ProcessoArquivoTable.__table__.update().values(dados)\
            .where(column("pra_prc_id") == prc_id)\
            .where(column("pra_plt_id") == plataforma)\
            .where(column("pra_data") == pra_data)
        base.execute(upd)
        base.commit()

    # ATUALIZA ARQUIVOS ANTIGOS
    @staticmethod
    def update_old(base, prc_id, pra_data, plataforma, dados):
        upd = ProcessoArquivoTable.__table__.update().values(dados)\
            .where(column("pra_prc_id") == prc_id)\
            .where(column("pra_plt_id") == plataforma)\
            .where(column("pra_data") < pra_data)
        base.execute(upd)
        base.commit()

    # ATUALIZA ARQUIVOS ANTIGOS
    @staticmethod
    def update_sem_ocorrencia(base, prc_id, dados):
        upd = ProcessoArquivoTable.__table__.update().values(dados) \
            .where(column("pra_prc_id") == prc_id) \
            .where(column("pra_plt_id").notin_([0,1, 8, 11]))
        base.execute(upd)
        base.commit()


    # ATUALIZA ARQUIVOS ANTIGOS
    @staticmethod
    def update_arquivos_lancados(base, prc_id, dados, pra_data):
        upd = ProcessoArquivoTable.__table__.update().values(dados) \
            .where(column("pra_prc_id") == prc_id) \
            .where(column("pra_plt_id").notin_([0,1, 8, 11])) \
            .where(column("pra_data") <= pra_data) \
            .where(or_(column("pra_erro") == False, column("pra_erro") == None)) \
            .where(or_(column("pra_excluido") == False, column("pra_excluido") == None)) \
            .where(or_(column("pra_sigilo") == False, column("pra_sigilo") == None)) \
            .where(column("pra_ocorrencia") == None)

        base.execute(upd)
        base.commit()