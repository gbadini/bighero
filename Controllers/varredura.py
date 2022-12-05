from Config.helpers import *
from Config.database import *
from Models.processoModel import *
from Models.plataformaModel import *
from Models.usuarioModel import *
from Models.logModel import *
from Models.acompanhamentoModel import *
from Models.parteModel import *
from Models.processoPendenciaModel import *
from Models.processoResponsavelModel import *
from Config.customMethods import *
from Models.processoArquivoModel import *
from Config.logger import *
from selenium.common.exceptions import *
from selenium.webdriver.common.keys import Keys
from configparser import ConfigParser
import time
import traceback
import psutil, os, uuid


# CLASSE PRINCIPAL DA VARREDURA
class Varredura():
    # METODO CONSTRUTOR
    def __init__(self):
        self.init_vars()
        self.uf = self.__class__.__name__
        self.uf = self.uf.replace('2g','')
        f = self.uf.find('_')
        if f > -1:
            self.uf = self.uf[f+1:]

        self.conn = {}
        self.reiniciar_navegador = True
        self.kill_nao_localizado = False
        self.driver = None
        config = ConfigParser()
        caminho = get_full_path(r'local.ini')
        config.read(caminho)
        self.interromper = config.getboolean('varredura', 'interromper')
        self.console_log = config.getboolean('varredura', 'console_log')
        self.campos_usuario = (('plt_usuario','plt_senha'), ('plt_usuario2','plt_senha2'), ('plt_usuario3','plt_senha3'),)
        self.ordem_usuario = 0
        self.tempo_nao_iniciado_download = 45
        self.diferenciar_id_download_2g = False
        self.browser = 'Chrome'
        self.primeiro_ciclo = True

    # INICIA VARIÁVEIS DA CLASSE
    def init_vars(self):
        self.plataforma = 0
        self.nome_plataforma = ''
        self.conn = []
        self.pagina_inicial = ''
        self.pagina_busca = ''
        self.pagina_processo = ''
        self.pid = 0
        self.intervalo = 0
        self.prc_id = 0
        self.rec_id = None
        self.proc_data = []
        self.conn_atual = None
        self.wait_loading = True
        self.apagar_partes_inexistentes = True
        self.tratar_tamanhos = False
        self.process_children = []
        self.logger = None

    def __del__(self):
        self.kill_children()

    # CAPTURA OS IDS DOS PROCESSOS VINCULADOS A SESSÃO DO WEBDRIVER
    def get_children(self):
        if self.driver and self.browser != 'IE':
            p = psutil.Process(self.driver.service.process.pid)
            self.process_children = p.children(recursive=True)
            self.process_main_child = self.process_children[:]
        # try:
        #
        # except:
        #     pass


    # ELIMINA OS PROCESSOS VINCULADOS A SESSÃO DO WEBDRIVER
    def kill_children(self):
        try:
            self.driver.quit()
        except:
            pass

        for child in self.process_children:
            try:
                child.kill()
            except:
                pass

    # CONFERE USUARIO E SENHA PARA LOGAR NO SISTEMA
    @staticmethod
    def autentica_user(usuario, senha):
        try:
            Session = connect_db('bec')
            result = Usuario.login(Session(), usuario, senha)
        except:
            return False

        return result

    # CONFERE USUARIO E SENHA PARA LOGAR NO SISTEMA
    @staticmethod
    def vincula_logs():
        sqlite_conn = connect_sqlite('log_bighero.db')
        if not sqlite_conn:
            return False

        rows = Log.select_sqlite(sqlite_conn)

        # try:
        if len(rows) > 0:
            Session = connect_db('log', '201.47.170.196,1535')
            # Session = connect_db('log', '186.195.37.158,1535')
            Log.insert(Session(), rows)
            Log.clear(sqlite_conn)

        sqlite_conn.close()
        # except:
        #     return False

    # CAPTURA INTERVALOS QUE SERÃO DIVIDIDAS AS THREADS
    @staticmethod
    def intervalos(uf, plataforma, dia, tipo=2, query_and='', base='Todas', qtd=1, arquivo_morto=False, grau=1, tipo_mod=None, area=1):
        down_pen = tipo == 1
        if uf == '*':
            if base == 'Todas':
                bases = get_bases(uf)
            else:
                bases = [base,]
        else:
            bases = get_bases(uf)

        # print(uf, plataforma, dia, tipo, query_and, base, qtd, arquivo_morto, grau, tipo_mod, area)
        id_plat = id_plataforma(plataforma, uf == '*')
        ids = {}
        for b in bases:
            if base != 'Todas' and base != b:
                continue

            Session = connect_db(b)
            r = Processo.intervalo_varredura(Session(), uf, id_plat, area, dia, query_and=query_and, somente_download_pendente=down_pen, arquivo_morto=arquivo_morto, threads=qtd, grau=grau, tipo=tipo_mod)
            ids[b] = r

        return ids

    # INICIA O CICLO DA VARREDURRA: INICIA O NAVEGADOR, CAPTURA ERROS E ITERA ATÉ QUE OS PROCESSOS SEJAM ESGOTADOS
    def ciclo(self, dia, tipo=2, query_and='', base='Todas', categoria=1, headless=False, arquivo_morto=False, intervalo=[], grau=1, usuario='', area=1, vespertino=False):
        '''
        :param datetime dia: dia de referrncia para a varredura
        :param str tipo: tipo de varredura: 1 para apenas Downloads, 2 para apenas coleta de dados, e 3 para ambos.
        :param bol completo: Se captura os dados de todos os processos ou somente os dados dos processos com novas movimentações
        :param bol headless: O navagador será executado de maneira headless(invisível para o usuário)? - Utilizar como False se precisar realizar downloads
        '''
        self.tipo = tipo
        self.completo = False
        self.nao_varrer = False
        self.arquivo_morto = arquivo_morto
        self.range = intervalo
        self.area = area
        self.varredura_vespertina = vespertino
        self.nome_plataforma = nome_plataforma(self.plataforma, self.uf)
        if categoria == 2:
            self.completo = True

        if categoria == 3:
            self.nao_varrer = True

        self.dia = dia
        self.grau = grau
        self.query_and = query_and
        if self.uf == '*':
            if base == 'Todas':
                bases = get_bases(self.uf)
            else:
                bases = [base,]
        else:
            bases = get_bases(self.uf)

        for b in bases:
            if base != 'Todas' and base != b:
                continue
            self.conn[b] = None

        # ENQUANTO O METODO "VARREDURA" NÃO RETORNAR TRUE, O CICLO DE VARREDURA SERA REINICIADO EM CASO DE ERRO
        for c in self.conn:
            print('conectando em', c)
            pasta_uid = str(uuid.uuid1())
            uf_pasta = 'cliente' if self.uf == '*' else self.uf
            self.pasta_download = 'C:\\downloads\\swap\\' + c + '\\' + uf_pasta + '\\temp\\' + pasta_uid
            self.pasta_intermediaria = 'C:\\downloads\\swap\\' + c + '\\' + uf_pasta + '\\mc\\' + pasta_uid

            fim = False
            while not fim:
                try:
                    Session = connect_db(c)
                    self.conn[c] = Session()
                    plt = Plataforma.select(self.conn[c], self.plataforma, self.uf)
                    login = None
                    senha = None
                    token = None
                    if len(plt) > 0:
                        login = plt[0][self.campos_usuario[self.ordem_usuario][0]]
                        senha = plt[0][self.campos_usuario[self.ordem_usuario][1]]
                        token = plt[0]['plt_token']

                    login_plt = login if login is not None else 'Certificado'
                    if self.logger is None:
                        self.logger = create_logger(usuario, login_plt, self.nome_plataforma, self.uf, c)

                    if self.driver is None or self.reiniciar_navegador or self.primeiro_ciclo:
                        self.driver = create_browser_instance(self.pasta_download, headless, self.wait_loading, browser=self.browser)

                    self.get_children()

                    if token is None:
                        fim = self.varrer(c, login, senha)
                    else:
                        fim = self.varrer(c, login, senha, token)

                except Exception as e:
                    tb = traceback.format_exc()
                    # print(tb)
                    self.logger.exception(tb, extra={'log_prc_id':self.prc_id})
                    # save_log(tb, self.uf, self.plataforma, self.prc_id)
                    if self.interromper:
                        time.sleep(9999)
                    time.sleep(30)

                if self.reiniciar_navegador or self.primeiro_ciclo or fim:
                    self.kill_children()

                engine = self.conn[c].get_bind()
                engine.dispose()

    # GERENCIA A CAPTURA DE DADOS, DOWNLOADS E SALVA NA BASE
    def varrer(self, c, login, senha, token=None):
        pass

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        pass

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None, base=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca, pasta=None):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        return

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        return

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_proc, codigo=None):
        self.confere_cnj(numero_proc)
        return False

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        return False

    # FECHA A JANELA DO PROCESSO ABERTO ATUALMENTE
    def fecha_processo(self):
        return False

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        return []

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        return []

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        return []

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        return {'ativo': [], 'passivo': [], 'terceiro':[]}

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual='Ativo'):
        '''
        :param str status_atual: Status atual
        '''
        return {}

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, target_dir):
        return []

    # ALTERNA ENTRE AS JANELAS ABERTAS
    def alterna_janela(self, indice_janela=1, quantidade_atual=1, tempo=30):
        wh = self.driver.window_handles
        inicio = time.time()
        while len(wh) == quantidade_atual:
            tempoTotal = time.time() - inicio
            if tempoTotal >= tempo:
                raise MildException("Timeout abrindo processo", self.uf, self.plataforma, self.prc_id)
            try:
                self.driver.switch_to.alert.accept()
            except NoAlertPresentException:
                pass

            wh = self.driver.window_handles

        self.driver.switch_to.window(wh[indice_janela])

    def insere_novo_processo(self, numero_busca):
        if not Processo.processo_existe(self.conn_atual, numero_busca):
            prc_pai = self.proc_data['prc_pai'] if self.proc_data['prc_pai'] is not None and self.proc_data[
                'prc_pai'] > 0 else self.proc_data['prc_id']
            print("inserindo processo anexo")
            np = [{'prc_numero': numero_busca, 'prc_estado': self.uf, 'prc_autor': self.proc_data['prc_autor'],
                   'prc_pai': prc_pai, 'prc_area': 1, 'prc_carteira': self.proc_data['prc_carteira']}, ]
            Processo.insert(self.conn_atual, np)

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def confere_arquivos_novos(self, arquivos_base):
        return False