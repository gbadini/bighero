from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
import Config.customMethods
import math
from Config.helpers import *
from Models.recursoModel import *
from configparser import ConfigParser

Base = declarative_base()

# MONTA TABELA "PROCESSO"
class ProcessoTable(Base):
    __tablename__ = "processo"
    prc_id = Column(BIGINT, primary_key=True, autoincrement=True)
    prc_sequencial = Column(VARCHAR(25))
    prc_numero = Column(VARCHAR(35))
    prc_numero2 = Column(VARCHAR(35))
    prc_autor = Column(VARCHAR(100))
    prc_carteira = Column(INTEGER)
    prc_promovente = Column(VARCHAR(150))
    prc_promovido = Column(VARCHAR(150))
    prc_recorrente = Column(VARCHAR(150))
    prc_recorrido = Column(VARCHAR(150))
    prc_cnpj_promovido = Column(VARCHAR(25))
    prc_cpf_cnpj = Column(VARCHAR(25))
    prc_comarca = Column(VARCHAR(45))
    prc_comarca2 = Column(VARCHAR(50))
    prc_estado = Column(VARCHAR(2))
    prc_serventia = Column(VARCHAR(120))
    prc_juizo = Column(VARCHAR(150))
    prc_custa = Column(VARCHAR(20))
    prc_serventia_recurso = Column(VARCHAR(120))
    prc_status = Column(VARCHAR(50))
    prc_situacao = Column(VARCHAR(60))
    prc_objeto1 = Column(VARCHAR(80))
    prc_objeto2 = Column(VARCHAR(80))
    prc_objeto3 = Column(VARCHAR(80))
    prc_objeto4 = Column(VARCHAR(80))
    prc_valor_causa = Column(VARCHAR(20))
    prc_valor_condenacao = Column(VARCHAR(20))
    prc_proc_origem = Column(VARCHAR(45))
    prc_fase = Column(VARCHAR(55))
    prc_data_cadastro = Column(DATETIME)
    prc_classe = Column(VARCHAR(100))
    prc_classe_recurso = Column(VARCHAR(100))
    prc_assunto = Column(VARCHAR(500))
    prc_assunto_recurso = Column(VARCHAR(500))
    prc_codigo = Column(VARCHAR(50))
    prc_distribuicao = Column(DATETIME)
    prc_segredo = Column(BOOLEAN)
    prc_suspensivo = Column(BOOLEAN)
    prc_area = Column(INTEGER)
    prc_penhora_rosto = Column(BOOLEAN)
    prc_grau = Column(INTEGER)
    prc_data_transito = Column(DATETIME)
    prc_data_pje = Column(DATETIME)
    prc_pje = Column(BOOLEAN)
    prc_data_projudi = Column(DATETIME)
    prc_projudi = Column(BOOLEAN)
    prc_data_eproc = Column(DATETIME)
    prc_eproc = Column(BOOLEAN)
    prc_data_fisico = Column(DATETIME)
    prc_fisico = Column(BOOLEAN)
    prc_data_esaj = Column(DATETIME)
    prc_esaj = Column(BOOLEAN)
    prc_ppe = Column(BOOLEAN)
    prc_data_ppe = Column(DATETIME)
    prc_tucujuris = Column(BOOLEAN)
    prc_data_tucujuris = Column(DATETIME)
    prc_autuacao_recurso = Column(DATETIME)
    prc_migrado = Column(BOOLEAN)
    prc_prioridade = Column(BOOLEAN)
    prc_data_2g = Column(DATETIME)
    prc_numero_2g = Column(VARCHAR(45))
    prc_numero_processum = Column(VARCHAR(50))
    prc_numero_antigo = Column(VARCHAR(35))
    prc_pai = Column(BIGINT)
    prc_data = Column(DATETIME)
    prc_data_update = Column(DATETIME)
    prc_data_update1 = Column(DATETIME)
    prc_terceiro = Column(BOOLEAN)
    prc_filtro = Column(BOOLEAN)
    prc_penhora = Column(BOOLEAN)
    prc_favorito = Column(INTEGER)
    prc_valor_provavel = Column(FLOAT)
    prc_valor_possivel = Column(FLOAT)
    prc_valor_sentenca = Column(FLOAT)
    prc_modulo = Column(VARCHAR(50))
    prc_divisao = Column(VARCHAR(50))
    prc_empresa = Column(VARCHAR(50))
    prc_canal = Column(VARCHAR(50))
    prc_data_citacao = Column(DATETIME)
    prc_data_envio = Column(DATETIME)
    prc_data_encerramento = Column(DATETIME)
    prc_produto = Column(VARCHAR(400))
    prc_vinculo = Column(VARCHAR(100))
    prc_conta = Column(VARCHAR(20))
    prc_fone = Column(VARCHAR(15))
    prc_localizacao = Column(VARCHAR(150))
    prc_pessoa = Column(INTEGER)
    prc_trf = Column(INTEGER)

class Processo():

    # INSERE NOVO PROCESSO NA BASE
    @staticmethod
    def insert(base, proc_data):
        prc_id = base.execute(
            ProcessoTable.__table__.insert(),
            proc_data
        ).inserted_primary_key[0]
        base.commit()

        return prc_id

    # INSERE NOVO PROCESSO NA BASE
    @staticmethod
    def insert_batch(base, procs):
        if len(procs) == 0:
            return

        base.execute(
            ProcessoTable.__table__.insert(),
            procs
        )
        base.commit()

    # CONFERE SE A A ÚLTIMA MOVIMENTAÇÃO JÁ CONSTA NA BASE
    @staticmethod
    def get_processo_by_id(base, prc_id):
        '''
        :param Session base: conexão de destino
        :param int prc_id: id do processo
        '''

        s = select([ProcessoTable]).where(column("prc_id") == prc_id)

        result = base.execute(s)
        return result.fetchdict()

    # CAPTURA PROCESSOS QUE SERÃO VARRIDOS
    @staticmethod
    def get_processo_by_numero(base, prc_numero=None, prc_sequencial=None):
        '''
        :param Session base: conexão de destino
        :param str prc_numero: numero do processo
        :param str prc_sequencial: sequencial do processo
        '''
        where_nro = ''
        where_seq = ''
        if prc_numero is not None:
            prc_numero_limpo = ajusta_numero(prc_numero)
            where_nro = "prc_numero in ('"+prc_numero+"','"+prc_numero_limpo+"')"

        if prc_sequencial is not None:
            where_seq = "prc_sequencial = '"+prc_sequencial+"'"

        where = ''
        if where_nro != '' and where_seq != '':
            where = "("+where_nro+" or "+where_seq+")"
        else:
            where = where_nro if where_nro != '' else where_seq


        result = base.execute("SELECT prc_id, prc_sequencial, prc_autor, prc_numero FROM processo where "+where)
        return result.fetchdict()

    # CAPTURA PROCESSOS PELO SEQUENCIAL
    @staticmethod
    def get_processos_by_sequencial(base, sequenciais):
        '''
        :param Session base: conexão de destino
        :param str uf: estado dos processos a serem localizados
        :param int area: 1=civel 2=trabalhista
        :param datetime data_referencia: data de referencia para varredura
        :param int grau: grau dos processos a serem localizados
        :param int quantidade: quantidade de processos a serem retornados
        '''

        sequenciais = "','".join(sequenciais)
        result = base.execute("SELECT prc_id, prc_sequencial, prc_autor, prc_numero, prc_numero_processum, prc_data_update1, prc_valor_causa FROM processo where prc_sequencial in ('"+sequenciais+"')")
        return result.fetchdict()

    # CAPTURA PROCESSOS PELO NUMERO DE CADASTRO
    @staticmethod
    def get_processos_by_numero_cadastro(base, numeros):
        '''
        :param Session base: conexão de destino
        :param str uf: estado dos processos a serem localizados
        :param int area: 1=civel 2=trabalhista
        :param datetime data_referencia: data de referencia para varredura
        :param int grau: grau dos processos a serem localizados
        :param int quantidade: quantidade de processos a serem retornados
        '''

        numeros = "','".join(numeros)
        result = base.execute("SELECT prc_id, prc_sequencial, prc_autor, prc_numero, prc_numero_processum, prc_data_update1, prc_valor_causa FROM processo where prc_numero_processum in ('"+numeros+"')")
        return result.fetchdict()

    # CAPTURA PROCESSOS QUE SERÃO VARRIDOS
    @staticmethod
    def get_processos_varredura(base, uf, plataforma, area, data_referencia, query_and='', grau = 1, quantidade=80, somente_download_pendente=False, arquivo_morto=False, intervalo=[]):
        '''
        :param Session base: conexão de destino
        :param str uf: estado dos processos a serem localizados
        :param int area: 1=civel 2=trabalhista
        :param datetime data_referencia: data de referencia para varredura
        :param int grau: grau dos processos a serem localizados
        :param int quantidade: quantidade de processos a serem retornados
        '''
        if area == 1:
            if uf.upper().find('TRF') > -1:
                query = Processo.format_query_federal(uf, plataforma, area, data_referencia, query_and, grau, quantidade, somente_download_pendente, arquivo_morto, intervalo=intervalo)
            else:
                query = Processo.format_query(uf, plataforma, area, data_referencia, query_and, grau, quantidade, somente_download_pendente, arquivo_morto, intervalo=intervalo)
        else:
            query = Processo.format_query_trabalhista(uf, plataforma, area, data_referencia, query_and, grau, quantidade, somente_download_pendente, arquivo_morto, intervalo=intervalo)

        result = base.execute(query)
        result_dict = result.fetchdict()
        base.close()
        return result_dict

    @staticmethod
    def format_query_trabalhista(trt, plataforma, area, data_referencia, query_and, grau, quantidade, somente_download_pendente, arquivo_morto, count=False, random=True, intervalo=False):
        join = "outer apply (select top 1 * from processo_arquivo where prc_id=pra_prc_id and pra_plt_id=" + str(plataforma) + ") pra "
        if somente_download_pendente:
            join = "cross apply (select top 1 * from processo_arquivo where prc_id=pra_prc_id and pra_plt_id=" + str(plataforma) + " and pra_erro=1) pra "
            hoje = datetime.now()
            data_referencia = hoje.strftime('%Y-%m-%d %H:%M')

        if query_and.strip() != '':
            query_and = " and " + query_and

        # campos = "top " + str(quantidade) + " prc_sequencial, prc_numero,prc_numero2,prc_id,prc_estado,prc_status,prc_situacao,prc_carteira, prc_data_pje,prc_pje,cadastro,prc_grau,prc_codigo, prc_autor, CASE WHEN prc_data_pje is null THEN 0 ELSE 1 END AS OrderBy"
        # order_by = " order by OrderBy, newid()"

        if grau == 1:
            campos = "top " + str(quantidade) + " prc_sequencial, prc_numero, prc_numero2, prc_estado, prc_situacao, prc_id, prc_status, cadastro, prc_grau, prc_autor, prc_carteira, prc_migrado, prc_cpf_cnpj, prc_cnpj_promovido, prc_pai, prc_codigo,prc_data_pje,prc_pje, CASE WHEN prc_data_pje is null THEN 0 ELSE 1 END AS OrderBy"
            order_by = " order by OrderBy, newid()"
        else:
            campos = "top " + str(quantidade) + " prc_id,rec_id,prc_numero, prc_numero2, prc_estado, prc_situacao, prc_autor,prc_carteira, prc_migrado, prc_cpf_cnpj, prc_cnpj_promovido, prc_pai, prc_numero_2g,prc_data_2g,rec_numero,rec_status,cadastro,cadastro2,rec_codigo,rec_data_update"
            order_by = " order by newid()"

        situacao = "'Removido da Base','Arquivo Morto','Morto','Encerrado'"
        if arquivo_morto:
            situacao = "'Removido da Base','Morto','Encerrado'"

        if not random:
            campos = "prc_sequencial, prc_numero,prc_id,prc_estado,prc_status,prc_situacao,prc_carteira, prc_data_pje,prc_pje,cadastro,prc_grau,prc_codigo, prc_migrado, prc_pai, prc_autor, CASE WHEN prc_data_pje is null THEN 0 ELSE 1 END AS OrderBy"
            order_by = " order by prc_id"

        if count:
            campos = "count(*) as total"
            order_by = ""

        if intervalo:
            query_and += " and prc_id >= "+str(intervalo[0])
            if intervalo[1]:
                query_and += " and prc_id <= " + str(intervalo[1])

        estados = trt_estado(trt)
        ufs = "','".join(estados)
        if grau == 1:
            query = "SELECT "+campos+" FROM processo  " \
                    "" + join + "" \
                    "left join (select acp_processo,max(acp_cadastro) as cadastro from acompanhamento where " \
                    "acp_plataforma=2 and (acp_grau is NULL or acp_grau=1) group by acp_processo) acp on acp_processo=prc_id " \
                     "WHERE prc_area = 2 and (prc_data_pje is null or " \
                    "prc_data_pje <= '" + data_referencia + "') " \
                    "and (prc_situacao <> 'Removido da Base' or prc_situacao is NULL) and (prc_situacao is null or prc_situacao not in (" + situacao + ") or prc_data_pje is null) " \
                    "and len(prc_numero)>12 and (prc_estado in ('"+ufs+"'))" + query_and + " "+order_by

        else:
            # print('query_and',query_and)
            # print('order_by', order_by)
            # "and (prc_status not in ('Arquivado Definitivamente','Arquivado Provisoriamente','ARQUIVADO','Baixado','Removido da Base','Trabalhista') or prc_status is null) " \
            query = "select "+campos+" from processo WITH (NOLOCK)" \
                "" + join + "" \
                "left join recurso on rec_prc_id = prc_id and rec_plt_id = " + str(plataforma) + "" \
                "outer apply( select top 1 acp_cadastro as cadastro,acp_esp from acompanhamento WITH (NOLOCK) where acp_rec_id=rec_id order by acp_cadastro desc) as acp " \
                "outer apply (select top 1 acp_processo,acp_cadastro as cadastro2,acp_esp, acp_data as data_mov  from acompanhamento WITH (NOLOCK) where  " \
                "acp_plataforma not in (0,1,8,11) and acp_grau = 1 " \
                "and (acp_esp like '%Turma Recursal%' or acp_esp like '%Turma de Recursos%' or acp_esp like '%%Remetidos os Autos%' or acp_esp like '%Segunda Instância%' or acp_esp like '%Recurso Eletrônico%' or acp_esp like '%INSTÂNCIA SUPERIOR%' or acp_esp like '%Recurso Inominado%' or acp_esp like '%Apelação%' or acp_esp like '%Agravo de Instrumento%') and acp_processo=prc_id " \
                "order by acp_cadastro desc) acp2 " \
                "where (cadastro2 is not null or rec_id is not null or prc_grau = 2 or prc_numero2 is NULL) and (prc_estado in ('"+ufs+"')) and prc_area = 2 " \
                "and (rec_data_update<='" + data_referencia + "' or rec_data_update is null) and (rec_status is null or rec_status <> 'Encerrado' or (DATEADD(DAY, 3, data_mov) > prc_data_2g and prc_data_2g<'" + data_referencia + "') or prc_data_2g is NULL)  " \
                "and (prc_situacao <> 'Removido da Base' or prc_situacao is NULL) and (prc_situacao is null or prc_situacao not in (" + situacao + ")) " \
                "and (prc_numero_2g <> '0' or (DATEADD(DAY, 3, data_mov) > prc_data_2g and prc_data_2g<'" + data_referencia + "') or prc_data_2g is null or rec_id is not null)" \
                " " + query_and + " " + order_by
        print(query)
        return query

    @staticmethod
    def format_query_federal(uf, plataforma, area, data_referencia, query_and, grau, quantidade, somente_download_pendente, arquivo_morto, count=False, random=True, intervalo=False):
        join = "outer apply (select top 1 * from processo_arquivo where prc_id=pra_prc_id and pra_plt_id=" + str(plataforma) + ") pra "
        if somente_download_pendente:
            join = "cross apply (select top 1 * from processo_arquivo where prc_id=pra_prc_id and pra_plt_id=" + str(plataforma) + " and pra_erro=1) pra "
            hoje = datetime.now()
            data_referencia = hoje.strftime('%Y-%m-%d %H:%M')

        if query_and.strip() != '':
            query_and = " and " + query_and

        # query_and += get_and(uf, plataforma)

        estados = trf_estado(uf)
        ufs = "','".join(estados)

        plt = nome_plataforma(plataforma)
        campo_data = 'prc_data_' + plt
        campo_plt = 'prc_' + plt
        situacao = "'Removido da Base','Arquivo Morto','Morto','Encerrado'"
        if arquivo_morto:
            situacao = "'Removido da Base','Morto','Encerrado'"

        if grau == 1:
            campos = "top " + str(quantidade) + " prc_sequencial, prc_numero, prc_id, prc_estado, prc_status, cadastro, prc_grau, prc_autor, prc_migrado, prc_codigo," + campo_data + "," + campo_plt + ", CASE WHEN " + campo_data + " is null THEN 0 ELSE 1 END AS OrderBy"
            order_by = " order by OrderBy, newid()"
        else:
            campos = "top " + str(quantidade) + " prc_id,rec_id,prc_numero,prc_autor,prc_numero_2g,prc_data_2g,rec_numero,rec_status,cadastro,rec_codigo,rec_data_update"
            order_by = " order by newid()"

        if not random:
            if grau == 1:
                campos = "prc_sequencial, prc_numero,prc_id,prc_estado,prc_status,cadastro,prc_grau,prc_codigo, prc_autor, prc_migrado, " + campo_data + "," + campo_plt + ", CASE WHEN " + campo_data + " is null THEN 0 ELSE 1 END AS OrderBy"
            else:
                campos = "prc_id,rec_id,prc_numero,prc_numero_2g,prc_data_2g,prc_autor,rec_numero,rec_status,cadastro,rec_codigo,rec_data_update"
            order_by = " order by prc_id"

        if count:
            campos = "count(*) as total"
            order_by = ""

        if intervalo:
            query_and += " and prc_id >= "+str(intervalo[0])
            if intervalo[1]:
                query_and += " and prc_id <= " + str(intervalo[1])

        if grau == 1:
            query = "SELECT "+campos+" FROM processo WITH (NOLOCK) " \
                    "left join (select acp_processo,max(acp_cadastro) as cadastro from acompanhamento WITH (NOLOCK) where " \
                    "acp_plataforma=" + str(plataforma) + " and acp_grau = 1 group by acp_processo) acp on acp_processo=prc_id " \
                    "" + join + "" \
                    "where prc_estado in ('"+ufs+"') and (" + campo_data + "<='" + data_referencia + "' or " + campo_data + " is null) and len(prc_numero)>12 and len(prc_numero)<30 and prc_numero not like '%MIGRADO%' " \
                    "and (prc_situacao <> 'Removido da Base' or prc_situacao is NULL) and (prc_status not in ('Removido da Base','Trabalhista') or prc_status is null) " \
                    "and (prc_procon = 0 or prc_procon is null) and ((prc_numero2 is NULL and (prc_trf is NULL or prc_trf=1)) or prc_trf=" + str(plataforma) + ") " \
                    "and (prc_situacao is null or prc_situacao not in (" + situacao + ")) " \
                    "and (prc_modulo <> 'PROCON' or prc_modulo is null) and prc_numero not like '%DF%' and prc_numero not like '%CTAT%' " \
                    " " + query_and + " "+order_by
        else:
            query = "select "+campos+" from processo WITH (NOLOCK)" \
                "" + join + "" \
                "left join recurso on rec_prc_id = prc_id and rec_plt_id = " + str(plataforma) + "" \
                "outer apply( select top 1 acp_cadastro as cadastro,acp_esp from acompanhamento WITH (NOLOCK) where acp_rec_id=rec_id order by acp_cadastro desc) as acp " \
                "outer apply (select top 1 acp_processo,acp_cadastro as cadastro2,acp_esp, acp_data as data_mov  from acompanhamento WITH (NOLOCK) where  " \
                "acp_plataforma not in (0,1,8,11) and acp_grau = 1 " \
                "and (acp_esp like '%Turma Recursal%' or acp_esp like '%Turma de Recursos%' or acp_esp like '%%Remetidos os Autos%' or acp_esp like '%Segunda Instância%' or acp_esp like '%Recurso Eletrônico%' or acp_esp like '%INSTÂNCIA SUPERIOR%' or acp_esp like '%Recurso Inominado%' or acp_esp like '%Apelação%' or acp_esp like '%Agravo de Instrumento%') and acp_processo=prc_id " \
                "order by acp_cadastro desc) acp2 " \
                "where (cadastro2 is not null or rec_id is not null or prc_grau = 2) and prc_estado in ('"+ufs+"') prc_trf=" + str(plataforma) + " " \
                "and (rec_data_update<='" + data_referencia + "' or rec_data_update is null) and (rec_status is null or rec_status <> 'Encerrado' or (DATEADD(DAY, 3, data_mov) > prc_data_2g and prc_data_2g<'" + data_referencia + "') or prc_data_2g is NULL) " \
                "and (prc_situacao <> 'Removido da Base' or prc_situacao is NULL) and (prc_situacao is null or prc_situacao not in (" + situacao + ")) " \
                "and (prc_numero_2g <> '0' or (DATEADD(DAY, 3, data_mov) > prc_data_2g and prc_data_2g<'" + data_referencia + "') or prc_data_2g is null or rec_id is not null)" \
                " " + query_and + " "+order_by

        print(query)
        return query

    @staticmethod
    def format_query(uf, plataforma, area, data_referencia, query_and, grau, quantidade, somente_download_pendente, arquivo_morto, count=False, random=True, intervalo=False):
        join = "outer apply (select top 1 * from processo_arquivo WITH (NOLOCK) where prc_id=pra_prc_id and pra_plt_id=" + str(plataforma) + ") pra "
        if somente_download_pendente:
            join = "cross apply (select top 1 * from processo_arquivo WITH (NOLOCK) where prc_id=pra_prc_id and pra_plt_id=" + str(plataforma) + " and pra_erro=1 and (pra_legado is NULL or pra_legado=0)) pra "
            hoje = datetime.now()
            data_referencia = hoje.strftime('%Y-%m-%d %H:%M')

        if query_and.strip() != '':
            query_and = " and " + query_and

        query_and += get_and(uf, plataforma, grau)

        plt = nome_plataforma(plataforma)
        campo_data = 'prc_data_' + plt
        campo_plt = 'prc_' + plt
        situacao = "'Removido da Base','Arquivo Morto','Morto','Encerrado'"
        if arquivo_morto:
            situacao = "'Removido da Base','Morto','Encerrado'"

        if somente_download_pendente:
            situacao = "'Removido da Base','Arquivo Morto','Morto','Encerrado'"

        if grau == 1:
            campos = "top " + str(quantidade) + " prc_sequencial, prc_numero, prc_numero2, prc_situacao, prc_id, prc_estado, prc_status, prc_pai, cadastro, prc_grau, prc_data, prc_autor, prc_carteira, prc_migrado, prc_cpf_cnpj, prc_cnpj_promovido, prc_codigo," + campo_data + "," + campo_plt + ", CASE WHEN " + campo_data + " is null THEN 0 ELSE 1 END AS OrderBy"
            order_by = " order by OrderBy, newid()"
        else:
            campos = "top " + str(quantidade) + " prc_id,rec_id, prc_numero, prc_estado, prc_numero2, prc_situacao, prc_autor,prc_carteira, prc_pai, prc_numero_2g,prc_data_2g,rec_numero,rec_status,cadastro,cadastro2,rec_codigo,rec_data_update"
            order_by = " order by newid()"

        if not random:
            if grau == 1:
                campos = "prc_sequencial, prc_numero,prc_id,prc_estado,prc_status, prc_situacao,cadastro,prc_grau,prc_codigo, prc_data, prc_autor, prc_carteira, prc_migrado, prc_cpf_cnpj, prc_cnpj_promovido, " + campo_data + "," + campo_plt + ", CASE WHEN " + campo_data + " is null THEN 0 ELSE 1 END AS OrderBy"
            else:
                campos = "prc_id,prc_status, prc_situacao,prc_estado,rec_id,prc_numero,prc_numero_2g,prc_carteira, prc_data_2g,prc_autor,rec_numero,rec_status,cadastro,cadastro2,rec_codigo,rec_data_update"
            order_by = " order by prc_id"

        if count:
            campos = "count(*) as total"
            order_by = ""

        if intervalo:
            query_and += " and prc_id >= "+str(intervalo[0])
            if intervalo[1]:
                query_and += " and prc_id <= " + str(intervalo[1])

        qry_area = " and prc_area = " + str(area)
        prc_estado = "prc_estado = '" + uf + "'"
        if area == 3:
            qry_area = ''
            query_and = " and prc_numero2 is NULL "
            estados = trf_estado(uf)
            ufs = "','".join(estados)
            prc_estado = "prc_estado in ('" + ufs + "')"

        if grau == 1:
            query = "SELECT "+campos+" FROM processo WITH (NOLOCK) " \
                    "left join (select acp_processo,max(acp_cadastro) as cadastro from acompanhamento WITH (NOLOCK) where " \
                    "acp_plataforma=" + str(plataforma) + " and acp_grau = 1 group by acp_processo) acp on acp_processo=prc_id " \
                    "" + join + "" \
                    "where " + prc_estado + " and (" + campo_data + "<='" + data_referencia + "' or " + campo_data + " is null) and len(prc_numero)>12 and len(prc_numero)<30 and prc_numero not like '%MIGRADO%' " \
                    "and (prc_situacao <> 'Removido da Base' or prc_situacao is NULL) and (prc_status not in ('Removido da Base','Trabalhista') or prc_status is null) " + qry_area + " " \
                    "and (prc_procon = 0 or prc_procon is null) " \
                    "and (prc_situacao is null or prc_situacao not in (" + situacao + ")) " \
                    "and (prc_modulo <> 'PROCON' or prc_modulo is null) and prc_numero not like '%DF%' and prc_numero not like '%CTAT%' " \
                    " " + query_and + " "+order_by
        else:
            '''
                    "outer apply( select top 1 rec_id,rec_codigo,rec_data_update,rec_numero,rec_status,acp_cadastro as cadastro,acp_esp from recurso WITH (NOLOCK)" \
                    "left join acompanhamento WITH (NOLOCK) on acp_rec_id=rec_id  where rec_prc_id=prc_id and rec_plt_id = " + str(plataforma) + " order by acp_cadastro desc	) as acp " \
            '''
            # "and (prc_status not in ('Arquivado Definitivamente','Arquivado Provisoriamente','ARQUIVADO','Baixado','Removido da Base','Trabalhista') or prc_status is null or (rec_id is not NULL and rec_status is NULL)) "
            query = "select "+campos+" from processo WITH (NOLOCK)" \
                "" + join + "" \
                "left join recurso WITH (NOLOCK) on rec_prc_id = prc_id and rec_plt_id = " + str(plataforma) + "" \
                "outer apply( select top 1 acp_cadastro as cadastro,acp_esp from acompanhamento WITH (NOLOCK) where acp_rec_id=rec_id order by acp_cadastro desc) as acp " \
                "outer apply (select top 1 acp_processo,acp_cadastro as cadastro2,acp_esp, acp_data as data_mov from acompanhamento WITH (NOLOCK) where  " \
                "acp_plataforma not in (0,1,8,11) and acp_grau = 1 " \
                "and (acp_esp like '%Turma Recursal%' or acp_esp like '%Turma de Recursos%' or acp_esp like '%%Remetidos os Autos%' or acp_esp like '%Segunda Instância%' or acp_esp like '%Recurso Eletrônico%' or acp_esp like '%INSTÂNCIA SUPERIOR%' or acp_esp like '%Recurso Inominado%' or acp_esp like '%Apelação%' or acp_esp like '%Agravo de Instrumento%') and acp_processo=prc_id " \
                "order by acp_cadastro desc) acp2 " \
                "where (cadastro2 is not null or rec_id is not null or prc_grau = 2) " + qry_area + " and " + prc_estado + " " \
                "and (rec_data_update<='" + data_referencia + "' or rec_data_update is null) and (rec_status is null or rec_status <> 'Encerrado' or (DATEADD(DAY, 3, data_mov) > prc_data_2g and prc_data_2g<'" + data_referencia + "') or prc_data_2g is NULL) " \
                "and (prc_situacao <> 'Removido da Base' or prc_situacao is NULL) and (prc_situacao is null or prc_situacao not in (" + situacao + ")) " \
                "and (prc_numero_2g <> '0' or (DATEADD(DAY, 3, data_mov) > prc_data_2g and prc_data_2g<'" + data_referencia + "') or prc_data_2g is null or rec_id is not null)" \
                " " + query_and + " "+order_by

        print(query)
        return query

    # ATUALIZA DADOS DOS PROCESSOS
    @staticmethod
    def update(base, prc_id, plt_id, localizado, dados, grau=1, cliente=False):
        '''
        :param int prc_id: id do processo
        :param int plt_id: id do plataforma
        :param bool localizado: o processo foi localizado na varredura?
        :param dict dados: dados do processo
        '''
        if grau == 2:
            if not localizado:
                dados['prc_numero_2g'] = '0'
            else:
                plt = nome_plataforma(plt_id)
                dados['prc_' + plt] = True

            dados['prc_data_2g'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        else:
            if cliente:
                dados['prc_data_update1'] = datetime.now()
            else:
                if localizado:
                    for p in plataformas:
                        plt = nome_plataforma(p)
                        dados['prc_' + plt] = False
                plt = nome_plataforma(plt_id)
                # dados['prc_id'] = prc_id
                dados['prc_' + plt] = localizado
                dados['prc_data_' + plt] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                dados['prc_data_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if 'prc_segredo' not in dados and localizado:
                    dados['prc_segredo'] = False

            # del dados['prc_id']
            if 'prc_classe' in dados:
                dados['prc_classe'] = corta_string(dados['prc_classe'], 100)

            if 'prc_assunto' in dados:
                dados['prc_assunto'] = corta_string(dados['prc_assunto'], 500)

            if 'prc_juizo' in dados:
                dados['prc_juizo'] = corta_string(dados['prc_juizo'], 150)

            if 'prc_comarca2' in dados:
                dados['prc_comarca2'] = corta_string(dados['prc_comarca2'], 70)

            if 'prc_serventia' in dados:
                dados['prc_serventia'] = corta_string(dados['prc_serventia'], 120)

        upd = ProcessoTable.__table__.update().values(dados). \
            where(column("prc_id") == prc_id)
        base.execute(upd)
        base.commit()

    # ATUALIZA DADOS ESPECIFICOS DOS PROCESSOS
    @staticmethod
    def update_simples(base, prc_id, dados):
        upd = ProcessoTable.__table__.update().values(dados). \
            where(column("prc_id") == prc_id)
        base.execute(upd)
        base.commit()

    # ATUALIZA DADOS ESPECIFICOS DOS PROCESSOS
    @staticmethod
    def update_batch(base, prc_ids, dados):
        for i in range(0, len(prc_ids), 800):
            ids_para_update = prc_ids[i:i + 800]
            upd = ProcessoTable.__table__.update().values(dados). \
                where(column("prc_id").in_(ids_para_update))

            base.execute(upd)
            base.commit()

    # VERIFICA SE O PROCESSO EXISTE NA BASE
    @staticmethod
    def processo_existe(base, prc_numero):
        # prc_numero_limpo = ajusta_numero(prc_numero)
        numero = prc_numero.replace(' ', '').replace('-', '').replace('.', '').replace('\t', '').replace('\t', '').replace('\r', '').replace('/', '')
        numero = strip_html_tags(numero)
        prc_numero_limpo = numero.lstrip("0")
        query = "SELECT prc_id FROM processo where REPLACE(REPLACE(SUBSTRING(prc_numero, PATINDEX('%[^0]%', prc_numero + '.'), LEN(prc_numero)), '.', ''), '-', '') =  '"+prc_numero_limpo+"' or REPLACE(REPLACE(SUBSTRING(prc_numero2, PATINDEX('%[^0]%', prc_numero2 + '.'), LEN(prc_numero2)), '.', ''), '-', '') = '"+prc_numero_limpo+"'"
        result = base.execute(query)
        r = result.fetchdict()
        if len(r) > 0:
            return True

        return False

    # VERIFICA SE O PROCESSO JÁ FOI VARRIDO
    @staticmethod
    def ultimo_update(base, prc_id, plataforma, data_atual, grau=1, cliente=False):
        if cliente:
            campo_data = 'prc_data_update1'
            campo_busca = getattr(ProcessoTable, campo_data)
            s = select([campo_busca]).where(column("prc_id") == prc_id)
            result = base.execute(s)
            result = result.fetchdict()
        else:
            if grau == 1:
                plt = nome_plataforma(plataforma)
                campo_data = 'prc_data_' + plt
                campo_busca = getattr(ProcessoTable, 'prc_data_'+plt)

                s = select([campo_busca]).where(column("prc_id") == prc_id)
                result = base.execute(s)
                result = result.fetchdict()
            else:
                campo_data = 'rec_data_update'
                s = select([RecursoTable]).where(column("rec_id") == prc_id)
                result = base.execute(s)
                result = result.fetchdict()

        if len(result) == 0:
            return False

        if result[0][campo_data] is None:
            return False

        if data_atual is None and result[0][campo_data] is not None:
            return True

        if result[0][campo_data] > data_atual:
            return True

        return False

    # CAPTURA INTERVALOS DIVIDIDOS PELA NUMERO DE THREADS
    @staticmethod
    def intervalo_varredura(base, uf, plataforma, area, data_referencia, query_and='', grau = 1, quantidade=80, somente_download_pendente=False, arquivo_morto=False, threads=1, tipo=None):
        print('tipo',tipo)

        if area == 2:
            query = Processo.format_query_trabalhista(uf, plataforma, area, data_referencia, query_and, grau, quantidade, somente_download_pendente, arquivo_morto, count=True)
        elif uf == '*':
            if tipo == 'Entrantes' or tipo == 'EntrantesOcorrencia':
                return [1,]
            query = Processo.format_query_cliente(plataforma, data_referencia, query_and, quantidade, arquivo_morto, count=True, tipo=tipo, base=base)
        else:
            if uf.upper().find('TRF') > -1:
                query = Processo.format_query_federal(uf, plataforma, area, data_referencia, query_and, grau, quantidade, somente_download_pendente, arquivo_morto, count=True)
            else:
                query = Processo.format_query(uf, plataforma, area, data_referencia, query_and, grau, quantidade, somente_download_pendente, arquivo_morto, count=True)
        # print(query)
        result = base.execute(query)
        r = result.fetchdict()

        if r[0]['total'] == 0:
            return []

        if r[0]['total'] < threads:
            threads = r[0]['total']

        t = r[0]['total']/threads
        t = math.ceil(t)

        if uf == '*':
            query = Processo.format_query_cliente(plataforma, data_referencia, query_and, quantidade, arquivo_morto, random=False, tipo=tipo, base=base)
        else:
            if area == 1 or area == 3:
                query = Processo.format_query(uf, plataforma, area, data_referencia, query_and, grau, quantidade, somente_download_pendente, arquivo_morto, random=False)
            else:
                query = Processo.format_query_trabalhista(uf, plataforma, area, data_referencia, query_and, grau, quantidade, somente_download_pendente, arquivo_morto, random=False)

        ids = []
        for i in range(0, threads):
            qry = ";WITH pg AS ("+query+" "\
                  "OFFSET "+str(t*i)+" ROWS "\
                  "FETCH NEXT "+str(t)+" ROWS ONLY ) "\
                  "SELECT top 1 prc_id FROM pg "

            result = base.execute(qry)
            result = result.fetchdict()
            ids.append(result[0]['prc_id'])

        return ids

    # CAPTURA PROCESSOS QUE SERÃO VARRIDOS NO SISTEMA CLIENTE
    @staticmethod
    def get_processos_cliente(base, plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False, intervalo=[], tipo='Varredura'):
        '''
        :param Session base: conexão de destino
        :param str uf: estado dos processos a serem localizados
        :param int area: 1=civel 2=trabalhista
        :param datetime data_referencia: data de referencia para varredura
        :param int grau: grau dos processos a serem localizados
        :param int quantidade: quantidade de processos a serem retornados
        :param bol arquivo_morto: se varre os processos no arquivo morto
        :param list intervalo: intervalo dos processos a serem varridos
        '''

        query = Processo.format_query_cliente(plataforma, data_referencia, query_and, quantidade, arquivo_morto, intervalo=intervalo, tipo=tipo, base=base)

        result = base.execute(query)
        return result.fetchdict()

    # FORMATA QUERIES DOS SISTEMAS CLIENTES CONFORME O TIPO
    @staticmethod
    def format_query_cliente(plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False, count=False, intervalo=[], random=True, tipo='Varredura', base=None):
        query = ''

        if tipo == 'Varredura':
            query = Processo.query_cliente_varredura(plataforma, data_referencia, query_and, quantidade, arquivo_morto, count, intervalo, random)
        if tipo == 'OcorrenciasTJ':
            query = Processo.query_cliente_ocorrenciaTJ(plataforma, data_referencia, query_and, quantidade, arquivo_morto, count, intervalo, random)
        if tipo == 'OcorrenciasDJ':
            query = Processo.query_cliente_ocorrenciaDJ(plataforma, data_referencia, query_and, quantidade, arquivo_morto, count, intervalo, random)
        if tipo == 'OcorrenciasTitanium':
            query = Processo.query_cliente_ocorrenciaTitanium(plataforma, data_referencia, query_and, quantidade, arquivo_morto, count, intervalo, random)
        if tipo == 'Atas':
            query = Processo.query_cliente_atas(plataforma, data_referencia, query_and, quantidade, arquivo_morto, count, intervalo, random)
        if tipo == 'SPIC':
            query = Processo.query_cliente_spic(plataforma, data_referencia, query_and, quantidade, arquivo_morto, count, intervalo, random)
        if tipo == 'Pagamentos':
            query = Processo.query_cliente_pagamento(plataforma, data_referencia, query_and, quantidade, arquivo_morto, count, intervalo, random, base)
        if tipo == 'Contingencia':
            query = Processo.query_cliente_contingencia(plataforma, data_referencia, query_and, quantidade, arquivo_morto, count, intervalo, random)
        if tipo == 'Provisionamento':
            query = Processo.query_cliente_provisionamento(plataforma, data_referencia, query_and, quantidade, arquivo_morto, count, intervalo, random)
        if tipo == 'Arquivamento':
            query = Processo.query_cliente_arquivamento(plataforma, data_referencia, query_and, quantidade, arquivo_morto, count, intervalo, random)

        # print(query)
        return query

    # QUERY PARA DETECTAR CASOS QUE PRECISA LANÇAR OCORRENCIA NO SISTEMA
    @staticmethod
    def query_cliente_ocorrenciaTJ(plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False, count=False, intervalo=[], random=True):
        config = ConfigParser()
        config.read('local.ini')
        lanca_arquivos = config.getboolean('arquivos', 'lancar')

        if lanca_arquivos:
            campos = "top "+str(quantidade)+" prc_id, prc_sequencial, prc_autor, prc_carteira, prc_situacao, prc_pai, prc_estado, prc_area, acp_tipo, acp_esp, acp_cadastro, acp_ocorrencia, pra_id, CASE WHEN acp_id is null THEN 1 ELSE 0 END AS OrderBy"
        else:
            campos = "top " + str(quantidade) + " prc_id, prc_sequencial, prc_autor, prc_carteira, prc_situacao, prc_pai, prc_estado, prc_area, acp_tipo, acp_esp, acp_cadastro, acp_ocorrencia, CASE WHEN acp_id is null THEN 1 ELSE 0 END AS OrderBy"
        # order_by = " order by prc_id "
        order_by = " order by OrderBy, newid()"
        if count:
            campos = "count(*) as total"
            order_by = ""

        if not random:
            campos = "prc_id, prc_sequencial, prc_autor, prc_carteira, prc_situacao, prc_pai, prc_estado, prc_area, acp_tipo, acp_esp, acp_cadastro"
            order_by = " order by prc_id"

        if query_and.strip() != '':
            query_and = " and " + query_and

        if len(intervalo) > 0:
            query_and += " and prc_id >= "+str(intervalo[0])
            if intervalo[1]:
                query_and += " and prc_id <= " + str(intervalo[1])

        if lanca_arquivos:
            query = """SELECT """+campos+ """
                    from processo p1 WITH (NOLOCK)
                    outer apply (select top 1 * from acompanhamento a2 WITH (NOLOCK) where acp_processo = prc_id and acp_ocorrencia is NULL and acp_plataforma not in (0,1,8,11)) acp
                    outer apply (select top 1 * from processo_arquivo pa2 WITH (NOLOCK) where pra_prc_id = prc_id and pra_arquivo is not NULL and pra_plt_id not in (0,1,8,11) and (pra_excluido is NULL or pra_excluido=0) and (pra_erro is NULL or pra_erro=0) and pra_ocorrencia is NULL) pra
                    outer apply (select top 1 prc_situacao as situacao_pai from processo p2 WITH (NOLOCK) where p2.prc_id=p1.prc_pai) prc2
                    where p1.prc_carteira in (1,2) and (p1.prc_situacao in ('Ativo') or p1.prc_situacao is NULL) and (situacao_pai in ('Ativo') or situacao_pai is NULL)
                    and (pra_id is not NULL or acp_id is not NULL) """+query_and+order_by
            # query = """SELECT """+campos+"""
            #         from processo
            #         cross apply (select top 1 * from acompanhamento a2
            #         left join  processo_arquivo pa on DATEADD(MINUTE, DATEDIFF(MINUTE, 0, pra_data), 0) = DATEADD(MINUTE, DATEDIFF(MINUTE, 0, acp_cadastro), 0) and pra_prc_id = prc_id and pra_arquivo is not NULL and pra_plt_id not in (0,1,8,11) and (pra_excluido is NULL or pra_excluido=0) and (pra_erro is NULL or pra_erro=0) and pra_ocorrencia is NULL
            #         where (acp_processo = prc_id or acp_processo = prc_pai) and  (acp_ocorrencia is NULL or (acp_ocorrencia = 1 and pra_ocorrencia is NULL and pra_id is not NULL)) and acp_plataforma not in (0,1,8,11)) acp
            #         where prc_carteira in (1,2) and (prc_situacao in ('Ativo') or prc_situacao is NULL) """+query_and+order_by
        else:
            query = """SELECT """+campos+"""
                    from processo p1 WITH (NOLOCK)
                    outer apply (select top 1 * from acompanhamento a2 WITH (NOLOCK) where acp_processo = prc_id and acp_ocorrencia is NULL and acp_plataforma not in (0,1,8,11)) acp
                    outer apply (select top 1 prc_situacao as situacao_pai from processo p2 WITH (NOLOCK) where p2.prc_id=p1.prc_pai) prc2
                    where prc_carteira in (1,2) and (prc_situacao in ('Ativo') or prc_situacao is NULL) and (situacao_pai in ('Ativo') or situacao_pai is NULL) and (acp_id is not NULL) """+query_and+order_by
            # query = """SELECT """+campos+"""
            #         from processo
            #         cross apply (select top 1 * from acompanhamento a2 where (acp_processo = prc_id or acp_processo = prc_pai) and acp_ocorrencia is NULL and acp_plataforma not in (0,1,8,11)) acp
            #         where prc_carteira in (1,2) and (prc_situacao in ('Ativo') or prc_situacao is NULL) """+query_and+order_by

        print(query)
        return query

    # QUERY PARA DETECTAR CASOS QUE PRECISA LANÇAR OCORRENCIA CADASTRADAS NO TITANIUM NO SISTEMA
    @staticmethod
    def query_cliente_ocorrenciaTitanium(plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False, count=False, intervalo=[], random=True):
        config = ConfigParser()
        config.read('local.ini')
        lanca_arquivos = config.getboolean('arquivos', 'lancar')

        if lanca_arquivos:
            campos = "top "+str(quantidade)+" prc_id, prc_sequencial, prc_autor, prc_carteira, prc_situacao, prc_pai, prc_estado, prc_area, acp_id, acp_tipo, acp_esp, acp_data_evento, acp_prazo"
        else:
            campos = "top " + str(quantidade) + " prc_id, prc_sequencial, prc_autor, prc_carteira, prc_situacao, prc_pai, prc_estado, prc_area, acp_id, acp_tipo, acp_esp, acp_data_evento, acp_prazo"
        # order_by = " order by prc_id "
        order_by = " order by newid()"
        if count:
            campos = "count(*) as total"
            order_by = ""

        if not random:
            campos = "prc_id, prc_sequencial, prc_autor, prc_carteira, prc_situacao, prc_pai, prc_estado, prc_area, acp_tipo, acp_esp, acp_data_evento, acp_prazo"
            order_by = " order by prc_id"

        if query_and.strip() != '':
            query_and = " and " + query_and

        if len(intervalo) > 0:
            query_and += " and prc_id >= "+str(intervalo[0])
            if intervalo[1]:
                query_and += " and prc_id <= " + str(intervalo[1])

        query = """SELECT """+campos+"""
                    from processo
                    inner join acompanhamento a on acp_processo=prc_id and acp_plataforma=0 and acp_ocorrencia=0 """+query_and+order_by

        print(query)
        return query

    # QUERY PARA CAPTURAR SPICS NÃO ANALISADOS
    @staticmethod
    def query_cliente_spic(plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False, count=False, intervalo=[], random=True):
        campos = "top "+str(quantidade)+" prc_id, prc_sequencial, prc_autor, prc_carteira, prc_situacao, prc_pai, prc_estado, pra_descricao, pra_arquivo, pra_id, CASE WHEN adc_data is null THEN 0 ELSE 1 END AS OrderBy"
        order_by = " order by OrderBy desc,adc_data "
        # order_by = " order by newid()"
        if count:
            campos = "count(*) as total"
            order_by = ""

        if not random:
            campos = "prc_id, prc_sequencial, prc_autor, prc_carteira, prc_situacao, prc_pai, prc_estado, pra_descricao, pra_arquivo, pra_id, CASE WHEN adc_data is null THEN 0 ELSE 1 END AS OrderBy"
            order_by = " order by OrderBy desc,adc_data "

        if query_and.strip() != '':
            query_and = " and " + query_and

        # if len(intervalo) > 0:
        #     query_and += " and prc_id >= "+str(intervalo[0])
        #     if intervalo[1]:
        #         query_and += " and prc_id <= " + str(intervalo[1])

        hoje = datetime.now()
        data_referencia = hoje.strftime('%Y-%m-%d')

        query = """SELECT """+campos+"""
                from processo
                inner join processo_arquivo pa on pra_prc_id = prc_id and pra_plt_id = 1 and (pra_descricao like '%SPIC%' or pra_descricao like '%Emissão fatura Det%') and (pra_arquivo like '%.zip' or pra_arquivo like '%.pdf') and pra_ocorrencia is NULL
                inner join audiencia on adc_prc_id = prc_id and adc_data >= '"""+data_referencia+"""'
                where (pra_tentativas is NULL or pra_tentativas < 5) and  prc_situacao in ('Ativo','Pendente Citação') 
                """+query_and+order_by

        # query = """SELECT """+campos+"""
        #         from processo
        #         inner join processo_arquivo pa on pra_prc_id = prc_id and (pra_descricao like '%SPIC%') and (pra_arquivo like '%.zip' or pra_arquivo like '%.pdf') and pra_ocorrencia is NULL
        #         left join audiencia on adc_prc_id = prc_id
        #         where prc_situacao in ('Ativo','Pendente Citação') and adc_data > '"""+data_referencia+"""'
        #         """+query_and+order_by

        print(query)
        return query

    # QUERY PARA CAPTURAR PAGAMENTOS NÃO LANÇADOS
    @staticmethod
    def query_cliente_pagamento(plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False, count=False, intervalo=[], random=True, base=None):
        from Models.janelaModel import Janela
        carteira = '1,2'
        if plataforma == 11:
            carteira = '5'

        campos = "top "+str(quantidade)+" prc_id, prc_sequencial, prc_numero, prc_numero_processum, prc_autor, prc_carteira, prc_situacao, prc_estado, prc_area, pagamento.*"
        # order_by = " order by prc_id "
        order_by = " order by newid()"
        if count:
            campos = "count(*) as total"
            order_by = ""

        if not random:
            campos = "prc_id, prc_sequencial, prc_numero, prc_numero_processum, prc_autor, prc_carteira, prc_situacao, prc_estado, prc_area, pagamento.*"
            order_by = " order by prc_id"

        if query_and.strip() != '':
            query_and = " and " + query_and

        if plataforma != 11:
            jan = Janela.select_by_atual(base)
            if len(jan) > 0:
                jan_id = jan[0]['jan_id']
                jan_data_lancamento = jan[0]['jan_data_lancamento']
                if jan_data_lancamento is not None:
                    jan_data_lancamento = jan_data_lancamento.strftime('%Y-%m-%d')
                    query_and += "and (pag_jan_id in (-1,0) or (pag_jan_id="+str(jan_id)+" and pag_prazo = '"+jan_data_lancamento+"'))"
                else:
                    query_and += "and (pag_jan_id in (-1,0,"+str(jan_id)+"))"
            else:
                query_and += "and (pag_jan_id in (-1,0))"

        # if len(intervalo) > 0:
        #     query_and += " and prc_id >= "+str(intervalo[0])
        #     if intervalo[1]:
        #         query_and += " and prc_id <= " + str(intervalo[1])

        query = """SELECT """+campos+"""
                from processo
                inner join pagamento on pag_prc_id=prc_id
                where (pag_lancado is null or pag_lancado = 0) and (pag_subindo is null or pag_subindo = 0) and (pag_apagado = 0 
                or pag_apagado is null) and pag_liberado = 1 and prc_carteira in ("""+carteira+""")
                """+query_and+order_by
        # pag_Id = 31964
        print(query)
        return query

    # QUERY PARA CAPTURAR CONTINGENCIAMENTOS NÃO LANÇADOS
    @staticmethod
    def query_cliente_contingencia(plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False, count=False, intervalo=[], random=True):
        campos = "top "+str(quantidade)+" prc_id, prc_sequencial, prc_autor, prc_carteira, prc_situacao, prc_estado, contingencia.*"
        order_by = " order by prc_id "
        # order_by = " order by newid()"
        if count:
            campos = "count(*) as total"
            order_by = ""

        if not random:
            campos = "prc_id, prc_sequencial, prc_autor, prc_carteira, prc_situacao, prc_estado, contingencia.*"
            order_by = " order by prc_id"

        if query_and.strip() != '':
            query_and = " and " + query_and

        query = """SELECT """+campos+"""
                from processo 
                inner join contingencia on ctg_prc_id=prc_id and ctg_lancado = 0 and (ctg_erro is NULL or ctg_erro = '')
                where (prc_situacao is NULL or prc_situacao <> 'Removido da Base') and ctg_lancar = 1 and prc_area = 1
                """+query_and+order_by

        print(query)
        return query

    # QUERY PARA CAPTURAR PROVISIONAMENTOS NÃO LANÇADOS
    @staticmethod
    def query_cliente_provisionamento(plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False, count=False, intervalo=[], random=True):
        campos = "top "+str(quantidade)+" prc_id, prc_sequencial, prc_autor, prc_area, prc_carteira, prc_situacao, prc_estado, pagamento.*"
        # order_by = " order by prc_id "
        order_by = " order by newid()"
        if count:
            campos = "count(*) as total"
            order_by = ""

        if not random:
            campos = "prc_id, prc_sequencial, prc_autor, prc_area, prc_carteira, prc_situacao, prc_estado, pagamento.*"
            order_by = " order by prc_id"

        if query_and.strip() != '':
            query_and = " and " + query_and

        query = """SELECT """+campos+"""
                from processo 
                inner join janela on jan_futura = 1
                inner join pagamento on pag_prc_id = prc_id
                where (pag_provisionado is null or pag_provisionado = 0) and (pag_apagado is null or pag_apagado = 0) 
                and (pag_erro is null or pag_erro='') and pag_jan_id = jan_id
                """+query_and+order_by

        print(query)
        return query

    # QUERY PARA CAPTURAR ARQUIVAMENTOS NÃO LANÇADOS
    @staticmethod
    def query_cliente_arquivamento(plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False, count=False, intervalo=[], random=True):
        campos = "top "+str(quantidade)+" prc_id, prc_sequencial, prc_estado, prc_numero, prc_autor, prc_carteira, prc_situacao, prc_area, arquivamento.*"
        # order_by = " order by prc_id "
        order_by = " order by newid()"
        if count:
            campos = "count(*) as total"
            order_by = ""

        if not random:
            campos = "prc_id, prc_sequencial, prc_estado, prc_numero, prc_autor, prc_carteira, prc_situacao, prc_area, arquivamento.*"
            order_by = " order by prc_id"

        if query_and.strip() != '':
            query_and = " and " + query_and

        query = """SELECT """+campos+"""
                from processo 
                inner join arquivamento on aqm_prc_id=prc_id and aqm_lancado is NULL	
                where prc_situacao not in ('Arquivo Morto','Inativo','Removido da Base')
                """+query_and+order_by

        print(query)
        return query

    # QUERY PARA CAPTURAR ATAS NÃO LANÇADAS
    @staticmethod
    def query_cliente_atas(plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False,
                           count=False, intervalo=[], random=True):
        campos = "top " + str(
            quantidade) + " prc_id,arq_id,arq_acp,prc_sequencial,prc_estado,adc_status,arq_url,arq_status,adc_data,adc_obs"
        # order_by = " order by arq_id "
        order_by = " order by newid()"
        if count:
            campos = "count(*) as total"
            order_by = ""

        if not random:
            campos = "prc_id,arq_id,arq_acp,prc_sequencial,adc_status,arq_url,arq_status,adc_data,adc_obs"
            order_by = " order by arq_id"

        if query_and.strip() != '':
            query_and = " and " + query_and

        query = """SELECT """ + campos + """
                from processo
                inner join audiencia on adc_prc_id=prc_id
                inner join arquivo on adc_id=arq_adc_id
                where arq_status = 'pendente' and adc_status not in ('Revelia') and (prc_situacao is null or prc_situacao not in ('Arquivo Morto','Removido da Base')) 
                and (arq_acp is null or (arq_acp=1 and adc_status in ('Autos Conclusos','Ausência da Parte Autora','Desistência da Ação'))) and prc_area = 1 
                 """ + query_and + order_by

        print(query)
        return query

    # QUERY PARA DETECTAR CASOS QUE PRECISA LANÇAR OCORRENCIA NO SISTEMA
    @staticmethod
    def query_cliente_ocorrenciaDJ(plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False, count=False, intervalo=[], random=True):
        campos = "top "+str(quantidade)+" prc_id, prc_sequencial, dro_numero,dro_dia, drp_id, drp_processo, drp_titulo, drp_subtitulo,drp_enunciado, drp_conteudo, drp_extrato, drp_upload, drp_acompanhamento, prc_estado, prc_modulo"
        order_by = " order by newid()"
        if count:
            campos = "count(*) as total"
            order_by = ""

        if not random:
            campos = "prc_id, prc_sequencial, dro_numero,dro_dia, drp_id, drp_processo, drp_titulo, drp_subtitulo,drp_enunciado, drp_conteudo, drp_extrato, drp_upload, drp_acompanhamento, prc_estado, prc_modulo"
            order_by = " order by dro_id"

        if query_and.strip() != '':
            query_and = " and " + query_and

        # if len(intervalo) > 0:
        #     query_and += " and prc_id >= "+str(intervalo[0])
        #     if intervalo[1]:
        #         query_and += " and prc_id <= " + str(intervalo[1])

        query = """SELECT """+campos+"""
                from processo WITH (NOLOCK)
				inner join diario_processo WITH (NOLOCK) on prc_id=drp_prc_id 
				inner join diario WITH (NOLOCK) on drp_dro_id=dro_id
                where dro_dia > '2022-08-18' and prc_carteira in (1,2) and drp_revisado = 1 
                and (drp_upload is null or drp_acompanhamento is null) and (prc_situacao is null or prc_situacao not in ('Arquivo Morto','Removido da Base','Inativo', 'Encerrado'))
                 """+query_and+order_by

        print(query)
        return query

    # QUERY PARA DETECTAR CASOS QUE PRECISAM SER VARRIDOS
    @staticmethod
    def query_cliente_varredura(plataforma, data_referencia='', query_and='', quantidade=80, arquivo_morto=False, count=False, intervalo=[], random=True):
        campos = "top "+str(quantidade)+" prc_id,prc_sequencial, prc_comarca, prc_data_update1, prc_autor, prc_promovido, prc_cpf_cnpj, prc_numero,prc_numero_processum,prc_area,prc_estado,prc_vinculo,prc_conta,prc_produto,prc_status,cadastro,prc_codigo,prc_data_update, prc_carteira, prc_situacao, prc_data, CASE WHEN prc_data_update1 is null THEN 0 ELSE 1 END AS OrderBy, CASE WHEN ctg_valor_possivel = 0 THEN 0 ELSE 1 END AS OrderByCtg"
        order_by = " order by OrderBy, OrderByCtg, newid()"
        if count:
            campos = "count(*) as total"
            order_by = ""

        if not random:
            campos = "prc_id, prc_sequencial, prc_comarca, prc_data_update1, prc_autor, prc_promovido, prc_cpf_cnpj, prc_numero,prc_numero_processum,prc_area,prc_estado,prc_status,cadastro,prc_vinculo,prc_conta,prc_produto,prc_codigo,prc_data_update, prc_carteira, prc_situacao, prc_data, CASE WHEN prc_data_update1 is null THEN 0 ELSE 1 END AS OrderBy, CASE WHEN ctg_valor_possivel = 0 THEN 0 ELSE 1 END AS OrderByCtg"
            order_by = " order by prc_id"

        hoje = datetime.now()
        dia_da_semana = hoje.isoweekday()

        situacao = "'Removido da Base','Arquivo Morto','Morto','Encerrado'"

        if arquivo_morto or dia_da_semana in (5, 6, 7):
            situacao = "'Removido da Base','Morto','Encerrado'"

        carteiras = carteira_plataforma(plataforma)

        if query_and.strip() != '':
            query_and = " and " + query_and

        if plataforma == 11:
            query_and += " and prc_data_update1 is NULL"

        if len(intervalo) > 0:
            query_and += " and prc_id >= "+str(intervalo[0])
            if intervalo[1]:
                query_and += " and prc_id <= " + str(intervalo[1])

        query = """SELECT """+campos+"""
                FROM processo
                left join (select acp_processo,max(acp_cadastro) as cadastro from acompanhamento where
                acp_plataforma="""+str(plataforma)+""" group by acp_processo) acp on acp_processo=prc_id
                left join contingencia on ctg_prc_id=prc_id and (ctg_lancado is NULL or (ctg_lancado=0 and ctg_erro is NULL))
                left join plataforma on plt_codigo = """+str(plataforma)+"""
                where (prc_data_update1<=plt_ultima_consulta or prc_data_update1 is null) and prc_carteira in ("""+carteiras+""") and prc_sequencial is not null 
                and (prc_situacao not in ("""+situacao+""") or prc_situacao is null or prc_data_update1 is null) """+query_and+order_by

        print(query)
        return query

