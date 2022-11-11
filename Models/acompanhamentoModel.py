from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
from Config.helpers import *
from Models.processoModel import *
Base = declarative_base()

# MONTA TABELA "ACOMPANHAMENTO"
class AcompanhamentoTable(Base):
    __tablename__ = "acompanhamento"
    acp_id = Column(BIGINT, primary_key=True, autoincrement=True)
    acp_processo = Column(BIGINT)
    acp_tipo = Column(VARCHAR(200))
    acp_esp = Column(VARCHAR(2000))
    acp_cadastro = Column(DATETIME)
    acp_data_evento = Column(DATETIME)
    acp_cumprimento = Column(DATETIME)
    acp_audiencia = Column(DATETIME)
    acp_prazo = Column(DATETIME)
    acp_data = Column(DATETIME)
    acp_plataforma = Column(INTEGER)
    acp_grau = Column(INTEGER)
    acp_rec_id = Column(INTEGER)
    acp_ignorar = Column(BOOLEAN)
    acp_sentenca = Column(BOOLEAN)
    acp_sem_doc = Column(BOOLEAN)
    acp_agenda = Column(BOOLEAN)
    acp_usuario = Column(VARCHAR(100))
    acp_ocorrencia = Column(INTEGER)

class Acompanhamento():
    # INSERE ACOMPANHAMENTOS
    @staticmethod
    def insert(base, prc_id, plataforma, grau, acompanhamentos, rec_id=None, chaves_agenda=()):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param int plataforma: id do processo
        :param list acompanhamentos: lista de acompanhamentos
        '''

        grau_alterado = False
        for acp in acompanhamentos:
            if acp['acp_tipo'] is not None:
                acp['acp_tipo'] = corta_string(acp['acp_tipo'], 199)
                if find_string(acp['acp_tipo'], ('Correição', 'Expedição de Termo')):
                    acp['acp_ignorar'] = True

            acp['acp_esp'] = corta_string(acp['acp_esp'], 1999)
            if 'acp_data_evento' not in acp:
                acp['acp_data_evento'] = acp['acp_cadastro']
            if 'acp_plataforma' not in acp or ('acp_plataforma' in acp and acp['acp_plataforma'] is None):
                acp['acp_plataforma'] = plataforma
            acp['acp_processo'] = prc_id
            acp['acp_data'] = datetime.now()
            acp['acp_grau'] = grau
            acp['acp_rec_id'] = rec_id
            acp['acp_ignorar'] = None
            acp['acp_sentenca'] = False

            if 'acp_usuario' in acp and acp['acp_usuario'] is not None:
                acp['acp_usuario'] = corta_string(acp['acp_usuario'], 100)

            status_mov = get_status([{'acp_esp': acp['acp_esp'], 'acp_tipo': acp['acp_tipo']},],'Ativo')
            if status_mov == 'Arquivado':
                acp['acp_sentenca'] = None

            if not acp['acp_sentenca'] and plataforma not in (1, 8, 11):

                # if grau == 1 and not grau_alterado:
                #     if find_string(acp['acp_esp'], ('Turma Recursal', 'Turma de Recursos', 'Remetidos os Autos', 'Segunda Instância', 'Recurso Eletrônico', 'INSTÂNCIA SUPERIOR', 'Recurso Inominado','Apelação' 'Agravo de Instrumento')):
                #         Processo.update_simples(base, prc_id, {'prc_grau': 2,})
                #         grau_alterado = True

                acp_tipo = '' if acp['acp_tipo'] is None else acp['acp_tipo']
                # CONFERE SE POSSUI ALGUM TERMO NA ESP QUE INDICA NÃO SER SENTENÇA
                if find_string(acp['acp_esp'],('provimento judicial declaratório','houve decurso do prazo','TRANSITADO EM JULGADO EM','manifestar-se acerca da contestação','julgamento (presencial ou não presencial)','Expedição de Carta','Expedida/Certificada','Juntada de AR','LINK DE AUDIÊNCIA','implicará na extinção','Realizada Distribuição do processo','- Petição (','Certidão Provimento','Referente à Mov','Intimação lid','Aguardar trânsito','AGUARDAR TRANS','Correição','provimento n.','provimento nº','133 do Provimento','- PROVIMENTO N','termos do Provimento','Audiência realizada com Despacho','Provimento-CSM','Distribuído por Sorteio','Provimento COGER','PROVIMENTO DE AUDITAGEM','Certifico o link de acesso à plataforma')):
                    acp['acp_ignorar'] = True
                # CONFERE SE POSSUI ALGUM TERMO NO TIPO QUE INDICA NÃO SER SENTENÇA
                elif find_string(acp_tipo,('CONCLUSOS PARA JULGAMENTO','decurso do prazo','TRÂNSITO EM JULGADO','TRANSITO EM JULGADO','TRANSITADO EM JULGADO','Expedição de Carta','Expedida/Certificada','Juntada de AR','Audiência Designada','Ato ordinatório','Realizada Distribuição do processo','Certidão Provimento','Referente à Mov','Intimação lid','Correição','provimento n.','provimento nº','133 do Provimento','- PROVIMENTO N','termos do Provimento','Audiência realizada com Despacho','Provimento-CSM','Distribuição','Aguardando','Remessa Interna','Juntada de Mandados','Provimento COGER','PROVIMENTO DE AUDITAGEM')):
                    acp['acp_ignorar'] = True
                else:
                    # CONFERE SE POSSUI ALGUM TERMO NO TIPO QUE INDICA SER SENTENÇA
                    if find_string(acp_tipo,('ACORDO EM', 'HOMOLOGADA A TRANSAÇÃO', 'Homologação - Sentença', 'JULGAD', 'Embargos de Declaração Aco','Registro de Sentença','Homologação - sentença')):
                        acp['acp_sentenca'] = None
                    # CONFERE SE POSSUI ALGUM TERMO NA ESP QUE INDICA SER SENTENÇA
                    elif find_string(acp['acp_esp'],('JULGADO - MÉRITO','Julgamento -', 'ACORDO EM', 'Ante o exposto, julgo', 'HOMOLOGO, por sentença', 'HOMOLOGO a sentença', 'HOMOLOGO o acordo', 'HOMOLOGADO O ACORDO', 'HOMOLOGADA A TRANSAÇÃO','JULGADO EM','JULGADA EM','JULGADO NA','JULGADA NO','JULGADO PROCED','JULGADA IMPRO','JULGADA PROCED','JULGADO IMPRO','JULGADA(S) PROCED','JULGADO(S) PROCED','JULGADA(S) IMPROCED','JULGADO(S) IMPROCED','Registro de Sentença','EXTINTO O PROCESSO','EXTINÇÃO DO PROCESSO','INDEFERIDA A PETIÇÃO','Resolução do M','Resolução de M', 'Sentença de ','Sentença Proferida', 'Sentença Julgada', 'Audiência Realizada Com', 'Sentença Homologada', 'Despacho Homologação', 'Sentença Extinto', 'CONHECIDO O RECURSO', 'Leitura de Sentença', 'Não-Provimento', 'Provimento', 'JUNTADA DE ACÓRDÃO', 'Conhecido e ', 'Juntada - Documento - Acórdão','PROVIMENTO DE AUDITAGEM')):
                        acp['acp_sentenca'] = None
                    else:
                        # CONFERE SE POSSUI ALGUM TERMO NA INICIO DA ESP QUE INDICA SER SENTENÇA
                        pos = find_string(acp['acp_esp'],('Julgad',))
                        if pos and pos[1] == 0:
                            acp['acp_sentenca'] = None


            prev_mes = mes_anterior()
            if 'acp_agenda' not in acp or acp['acp_agenda'] is None:
                if plataforma in (1,8,11):
                    acp['acp_agenda'] = False
                    acp['acp_ocorrencia'] = False
                    acp['acp_sentenca'] = False
                else:
                    acp['acp_agenda'] = False if acp['acp_cadastro'] < prev_mes else None
                    acp['acp_ocorrencia'] = False if acp['acp_cadastro'] < prev_mes else None
                    for ch in chaves_agenda:
                        if str(acp['acp_esp']).find(ch) == 0:
                            acp['acp_agenda'] = False

        to_update = []
        return_key = []
        # IDENTIFICA OS ACOMPANHAMENTO QUE PRECISAM SER INSERIDOS INDIVIDUALMENTE PARA RETORNAR SEUS RESPECTIVOS IDS
        for acp in acompanhamentos[:]:
            if 'acp_id' in acp:
                if acp['acp_id'] is not None:
                    if str(acp['acp_id']).find('tmp') > -1:
                        return_key.append(acp)
                    else:
                        to_update.append(acp)

                    acompanhamentos.remove(acp)

                else:
                    del acp['acp_id']

        if len(to_update) > 0:
            Acompanhamento.update(base, to_update)

        # INSERE OS ACOMPANHAMENTOS EM LOTE
        if len(acompanhamentos) > 0:
            base.execute(
                AcompanhamentoTable.__table__.insert(),
                acompanhamentos
            )
            base.commit()

        # INSERE OS ACOMPANHAMENTOS INDIVIDUALMENTE E RETORNA SEUS IDS
        to_return = {}
        for acp in return_key:
            uid = acp['acp_id']
            del acp['acp_id']
            acp_id = base.execute(
                AcompanhamentoTable.__table__.insert(),
                acp
            ).inserted_primary_key[0]
            base.commit()
            to_return[uid] = acp_id

        return to_return

    # ATUALIZA ACOMPANHAMENTOS
    @staticmethod
    def update(base, dados):
        for acp in dados:
            acp_id = acp['acp_id']
            del acp['acp_id']
            # print(acp)
            upd = AcompanhamentoTable.__table__.update().values(acp).\
                where(column("acp_id") == acp_id)
            base.execute(upd)
            base.commit()

    # ATUALIZA DADOS ESPECIFICOS DOS PROCESSOS
    @staticmethod
    def update_batch(base, acp_ids, dados):
        for i in range(0, len(acp_ids), 800):
            ids_para_update = acp_ids[i:i + 800]
            upd = AcompanhamentoTable.__table__.update().values(dados). \
                where(column("acp_id").in_(ids_para_update))

            base.execute(upd)
            base.commit()

    # CONFERE SE A A ÚLTIMA MOVIMENTAÇÃO JÁ CONSTA NA BASE
    @staticmethod
    def compara_mov(base, prc_id, acp_esp, acp_cadastro, acp_plataforma, acp_grau=1, campo='acp_esp', rec_id=None):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param int plataforma: id do processo
        :param list acompanhamentos: lista de acompanhamentos
        '''
        if acp_grau == 2 and rec_id is None:
            return []

        acp_esp = corta_string(acp_esp, 120)

        s = select([AcompanhamentoTable]).where(column("acp_processo") == prc_id)\
            .where(column("acp_cadastro") == acp_cadastro)\
            .where(column("acp_plataforma") == acp_plataforma)
        if campo=='acp_esp':
            s = s.where(column(campo).like('%'+acp_esp+'%'))
        else:
            s = s.where(column(campo) == acp_esp)

        if rec_id is not None:
            s = s.where(column("acp_rec_id") == rec_id)
        else:
            s = s.where(column("acp_grau") == 1)

        result = base.execute(s)
        result = result.fetchdict()

        return len(result) > 0

    # CONFERE SE A A ÚLTIMA MOVIMENTAÇÃO JÁ CONSTA NA BASE
    @staticmethod
    def delete_acp(base, acp_id=None, prc_id=None, acp_plataforma=2):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param int plataforma: id do processo
        :param list acompanhamentos: lista de acompanhamentos
        '''
        if acp_id is not None:
            s = delete([AcompanhamentoTable]).where(column("acp_id") == acp_id)
            query = "DELETE FROM acompanhamento where acp_id = " + acp_id
        else:
            # s = delete([AcompanhamentoTable]).where(column("acp_processo") == prc_id).where(column("acp_plataforma") == acp_plataforma)
            # s = AcompanhamentoTable.delete().where(column("acp_processo") == prc_id).where(column("acp_plataforma") == acp_plataforma)
            query = "DELETE FROM acompanhamento where acp_processo = " + str(prc_id) + " and acp_plataforma = " + str(acp_plataforma)

        base.execute(query)
        base.commit()

    # CONFERE SE A A ÚLTIMA MOVIMENTAÇÃO JÁ CONSTA NA BASE
    @staticmethod
    def lista_movs(base, prc_id, acp_plataforma, ignora_cliente=True, ocorrencia=False, acp_grau = 1, rec_id=None, order_by=False):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param int plataforma: id do processo
        :param bool ignora_cliente: se captura somente movimentações dos tribunais
        :param bool ocorrencia: se confere o status dos casos que precisam ser lançados no cliente
        '''

        if acp_plataforma not in (0, 1, 8, 11):
            if rec_id is None and acp_grau > 1:
                return []

        s = select([AcompanhamentoTable]).where(column("acp_processo") == prc_id)

        if acp_plataforma is None:
            if ignora_cliente:
                # CAPTURA TODAS AS MOVIMENTAÇÕES DE TODOS OS TRIBUNAIS, MENOS DOS SISTEMAS DOS CLIENTES
                s = s.where(column("acp_plataforma").notin_([0,1, 8, 11]))
        else:
            if acp_plataforma not in (0, 1, 8, 11):
                s = s.where(column("acp_grau") == acp_grau)

            # CAPTURA TODAS AS MOVIMENTAÇÕES DE UMA PLATAFORMA ESPECIFICA
            s = s.where(column("acp_plataforma") == acp_plataforma)

        # s = s.where(column("acp_grau") == acp_grau)

        if ocorrencia:
            s = s.where(column("acp_ocorrencia") == None)

        if rec_id is not None:
            s = s.where(column("acp_rec_id") == rec_id)

        if order_by:
            s = s.order_by(text('acp_cadastro asc'))

        result = base.execute(s)
        return result.fetchdict()

        # CONFERE SE A A ÚLTIMA MOVIMENTAÇÃO JÁ CONSTA NA BASE

    @staticmethod
    def lista_movs_tj(base, prc_id, acp_plataforma=None, semente_sem_ocorrencia=False):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param int plataforma: id do processo
        :param bool ignora_cliente: se captura somente movimentações dos tribunais
        :param bool ocorrencia: se confere o status dos casos que precisam ser lançados no cliente
        '''

        s = select([AcompanhamentoTable]).where(column("acp_processo") == prc_id)

        if acp_plataforma is None:
            s = s.where(column("acp_plataforma").notin_([0, 1, 8, 11]))
        else:
            s = s.where(column("acp_plataforma") == acp_plataforma)

        if semente_sem_ocorrencia:
            s = s.where(column("acp_ocorrencia") == None)

        s = s.order_by(text('acp_cadastro asc'))

        result = base.execute(s)
        return result.fetchdict()

    # CONFERE SE A A ÚLTIMA MOVIMENTAÇÃO JÁ CONSTA NA BASE
    @staticmethod
    def lista_movs_docs(base, prc_id, acp_plataforma, retornar_valores_unicos=False):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        :param int plataforma: id do processo
        '''

        query = """	select * from acompanhamento a 
                    left join processo_arquivo on pra_acp_id=acp_id
                       where acp_processo = """ + str(prc_id) + """ and acp_plataforma = """ + str(acp_plataforma)

        result = base.execute(query)
        acps = result.fetchdict()
        novo = []
        # REMOVE TUPLAS DUPLICADAS
        if not retornar_valores_unicos:
            novo = acps
        else:
            for acp in acps:
                incluir = True
                for n in novo[:]:
                    if n['acp_id'] == acp['acp_id']:
                        if acp['pra_erro'] is None or not acp['pra_erro']:
                            incluir = False
                        else:
                            novo.remove(n)
                        break

                if incluir:
                    novo.append(acp)


        # select * from acompanhamento a
        #             outer apply (select top 1 * from processo_arquivo pa where pra_prc_id=acp_processo and pra_plt_id="""+str(acp_plataforma)+""") pra
        #             where acp_processo = """ + str(prc_id)

        return novo

    # CONFERE SE A A ÚLTIMA MOVIMENTAÇÃO JÁ CONSTA NA BASE
    @staticmethod
    def lista_movs_teste_acp(base):
        s = select([AcompanhamentoTable])
        s = s.where(column("acp_plataforma").notin_([0,1, 8, 11]))
        # s = s.where(column("acp_esp") == 'Audiência - sem Conciliação - Realizada - Local SALA DE CONCILIAÇÃO - 27/03/2018 14:00. Refer. Evento 10')
        s = s.where(column("acp_ocorrencia") == 0).limit(1000)

        result = base.execute(s)
        return result.fetchdict()