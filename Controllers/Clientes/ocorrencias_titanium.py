from Controllers.Clientes._cliente import *
import json

# CLASSE DE LANÇAMENTO DE OCORRÊNCIA NOS SISTEMAS CLIENTES
class OcorrenciasTitaniumCliente(Cliente):

    def __init__(self):
        super().__init__()
        self.movs = []
        self.ordem_usuario = 2


    # GERENCIA A CAPTURA DE DADOS, DOWNLOADS E SALVA NA BASE
    def varrer(self, db, login, senha):
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

        self.logger.info('Login realizado')

        # ENQUANTO A QUERY RETORNAR PROCESSOS, A VARREDURA CONTINUA
        procs = [1]
        ignorar_id = []
        while len(procs) > 0:
            procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=self.query_and, intervalo=self.range, tipo='OcorrenciasTitanium')
            inicio = time.time()

            for proc in procs:
                print('proc', proc)
                # if Processo.ultimo_update(self.conn[db], proc['prc_id'], self.plataforma, proc[campo_data], cliente=True):
                #     print('Processo já varrido')
                #     continue

                if self.intervalo > 0:
                    tempo_total = time.time() - inicio
                    if tempo_total < self.intervalo:
                        time.sleep(self.intervalo - tempo_total)
                    inicio = time.time()

                self.prc_id = proc['prc_id']
                print('prc_id ', proc['prc_id'])
                print(self.campo_busca, proc[self.campo_busca])
                self.logger.info('Iniciando Lançamento de Ocorrência', extra={'log_prc_id': self.prc_id})

                try:
                    numero_busca = proc[self.campo_busca]
                    if self.pagina_busca != '':
                        self.driver.get(self.pagina_busca)
                    busca = self.busca_processo(numero_busca)

                    if not busca:
                        # Processo.update(self.conn[c], proc['prc_id'], self.plataforma, False, {'prc_situacao': 'Removido da Base'}, cliente=True)
                        print('Removido da Base')
                        continue

                    dados_lanc = self.tratar_dados(proc, True)

                    # SE JÁ POSSUIR LANÇAMENTO CORRESPONDENTE, ATUALIZA NA BASE E PASSA PARA O PRÓXIMO
                    if self.confere_lancamento(dados_lanc):
                        Acompanhamento.update(self.conn[db], [{'acp_id':proc['acp_id'], 'acp_ocorrencia': True},])
                        continue

                    self.lanca_ocorrencia(dados_lanc)

                    if self.confere_lancamento(dados_lanc):
                        Acompanhamento.update(self.conn[db], [{'acp_id':proc['acp_id'], 'acp_ocorrencia': True},])

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
    def tratar_dados(self, acps):
        dados_lanc = []

        return dados_lanc