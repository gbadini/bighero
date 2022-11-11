from Controllers.Clientes._cliente import *
from Models.diarioprocessoModel import DiarioProcesso
import json

# CLASSE DE LANÇAMENTO DE OCORRÊNCIA NOS SISTEMAS CLIENTES
class OcorrenciasDJCliente(Cliente):

    def __init__(self):
        super().__init__()
        self.movs = []
        self.ordem_usuario = 2


    # GERENCIA A CAPTURA DE DADOS, DOWNLOADS E SALVA NA BASE
    def varrer(self, db, login, senha):
        campo_data = 'prc_data_update1'

        self.driver.get(self.pagina_inicial)
        try:
            if not self.login(login, senha, db):
                return False
        except:
            tb = traceback.format_exc()
            print(tb)
            print('Erro no Login')
            time.sleep(60)
            return False

        # CAPTURA CONFIG
        config = ConfigParser()
        config.read('local.ini')
        url_arquivos = config.get('arquivos', 'url_'+db)
        print('url_arquivos', url_arquivos)

        self.logger.info('Login realizado')

        # ENQUANTO A QUERY RETORNAR PROCESSOS, A VARREDURA CONTINUA
        procs = [1]
        ignorar_id = []
        while len(procs) > 0:
            query_and = self.query_and
            if len(ignorar_id) > 0:
                ids_txt = ",".join(ignorar_id)
                query_and = ''
                if self.query_and.strip() != '':
                    query_and = self.query_and + " and"
                query_and = query_and + " prc_id not in (" + ids_txt + ") "

            procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=query_and, intervalo=self.range, tipo='OcorrenciasDJ')

            for proc in procs:
                # print('proc', proc)
                status_atual = DiarioProcesso.check_upload(self.conn[db], proc['drp_id'])
                if status_atual[0]['drp_upload'] and status_atual[0]['drp_acompanhamento']:
                    print('Diário já lançado')
                    continue

                drps = DiarioProcesso.get_drp_by_date(self.conn[db], proc['prc_id'], proc['dro_dia'])
                self.prc_id = proc['prc_id']
                print('prc_id ', proc['prc_id'])
                print(self.campo_busca, proc[self.campo_busca])
                self.logger.info('Iniciando Lançamento de Diário', extra={'log_prc_id': self.prc_id})

                try:
                    numero_busca = proc[self.campo_busca]
                    if self.pagina_busca != '':
                        self.driver.get(self.pagina_busca)
                    busca = self.busca_processo(numero_busca)

                    if not busca:
                        Processo.update_simples(self.conn[db], proc['prc_id'], {'prc_data_update1': None})
                        raise FatalException("Processo Removido da Base", self.uf, self.plataforma, self.prc_id)
                        # print('Removido da Base')
                        # continue

                    # CONFERE SE O PROCESSO ESTÁ ATIVO
                    status_proc = self.captura_status()
                    if status_proc in ('Arquivo Morto', ):
                        Processo.update_simples(self.conn[db], proc['prc_id'], {'prc_data_update1': None})
                        raise FatalException('Processo Inativo', self.uf, self.plataforma, self.prc_id)

                    if status_atual[0]['drp_upload'] is None or not status_atual[0]['drp_upload']:
                        url_arquivo = url_arquivos
                        dro_dia = proc['dro_dia'].strftime('%d/%m/%Y')
                        arquivo = {'data_arquivo': dro_dia, 'obs_arquivo': "Publicação - DJE "+dro_dia, 'pra': [], 'drp': drps, 'arquivo': ['Publicação', ]}
                        if self.confere_arquivo(arquivo, False, False):
                            print('Arquivo existente')
                            DiarioProcesso.update_batch(self.conn[db], drps, {'drp_upload': 1, })

                        print('Lançando Arquivo')
                        if not self.lanca_arquivo(arquivo, url_arquivo, raise_exception=False, renomeia_arquivo=True, zipa_bloqueado=True):
                            print('Erro no lançamento do arquivo')
                            continue

                        if self.confere_arquivo(arquivo, False, False):
                            print('Arquivo existente')
                            DiarioProcesso.update_batch(self.conn[db], drps, {'drp_upload': 1, })

                    if status_atual[0]['drp_acompanhamento'] is None or not status_atual[0]['drp_acompanhamento']:
                        # SE JÁ POSSUIR LANÇAMENTO CORRESPONDENTE, ATUALIZA NA BASE E PASSA PARA O PRÓXIMO
                        acp = self.tratar_dados(drps, proc['prc_modulo'])
                        if not acp:
                            DiarioProcesso.update_batch(self.conn[db], drps, {'drp_acompanhamento': 0, })
                            continue

                        if self.confere_lancamento(acp, range_data_evento=3):
                            print('ja possui')
                            # ATUALIZAR
                            DiarioProcesso.update_batch(self.conn[db], drps, {'drp_acompanhamento': 1, })
                            continue

                        print('Lançando Ocorrência')
                        if not self.lanca_ocorrencia(acp):
                            # Acompanhamento.update_batch(self.conn[db], acp['acps'], {'acp_ocorrencia': 0})
                            continue

                        if self.confere_lancamento(acp, range_data_evento=3):
                            # ATUALIZAR
                            DiarioProcesso.update_batch(self.conn[db], drps, {'drp_acompanhamento': 1, })

                except MildException:
                    tb = traceback.format_exc()
                    # print(tb)
                    self.logger.warning(tb, extra={'log_prc_id': self.prc_id})
                    continue

                except CriticalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
                    return False

                except FatalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
                    ignorar_id.append(str(proc['prc_id']))
                    continue

        return True

    # CONFERE SE OS DADOS LANÇADOS NOS CAMPOS CONFEREM COM A BASE
    def tratar_dados(self, acps, modulo):
        dados_lanc = []

        return dados_lanc

    # CONFERE QUAL O TIPO DO ACOMPANHAMENTO
    def tipo_acp(self, tipo, esp):
        return 'Despacho', 'Para as partes'