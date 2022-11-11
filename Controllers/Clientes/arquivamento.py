from Controllers.Clientes._cliente import *
from Models.arquivamentoModel import *
from Models.arquivoModel import *

# CLASSE DO LANÇAMENTO DE ARQUIVAMENTO
class ArquivamentoCliente(Cliente):

    def __init__(self):
        super().__init__()
        self.realiza_reavaliacao = False

    # GERENCIA O LANÇAMENTO DAS ATAS
    def varrer(self, db, login, senha):
        url_remoto, url_arquivos = self.format_paths(db)
        print('url_arquivos', url_arquivos)

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

        # ENQUANTO A QUERY RETORNAR PROCESSOS, A VARREDURA CONTINUA
        procs = [1]
        ignorar_id = []
        last_id = 0
        while len(procs) > 0:
            query_and = self.query_and
            if len(ignorar_id) > 0:
                ids_txt = ",".join(ignorar_id)
                query_and = ''
                if self.query_and.strip() != '':
                    query_and = self.query_and + " and"
                query_and = query_and + " aqm_id not in (" + ids_txt + ") "

            procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=query_and, intervalo=self.range, tipo='Arquivamento')
            for proc in procs:
                try:
                    print('proc', proc)

                    if self.pagina_busca != '':
                        self.driver.get(self.pagina_busca)

                    numero_busca = proc[self.campo_busca]
                    busca = self.busca_processo(numero_busca)

                    if not busca:
                        raise FatalException('Removido da Base', self.uf, self.plataforma, self.prc_id)

                    self.confere_restricao()

                    dados_lanc = self.tratar_dados(self.conn[db], proc)

                    for arq in dados_lanc['arq']:
                        if not self.confere_existencia_arquivo(url_arquivos, url_remoto, arq['arq_url']):
                            arq_nome = arq['arq_descricao'] if arq['arq_descricao'] is not None and arq['arq_descricao'].strip() != '' else arq['arq_url']
                            raise FatalException('Arquivo não localizado: '+arq_nome, self.uf, self.plataforma, self.prc_id)

                    # CONFERE SE O PROCESSO ESTÁ ATIVO
                    status = self.captura_status()
                    if status not in ('Pendente Citação',):
                        if not self.confere_valor_provavel():
                            raise FatalException('Valor provável lançado', self.uf, self.plataforma, self.prc_id)

                    # SE JÁ POSSUIR LANÇAMENTO CORRESPONDENTE, ATUALIZA NA BASE E PASSA PARA O PRÓXIMO
                    if not self.confere_lancamento(dados_lanc, range_data_evento=15):
                        print('lançando')
                        if not self.lanca_ocorrencia(dados_lanc, gera_exception=True):
                            continue

                        if not self.confere_lancamento(dados_lanc, range_data_evento=15):
                            continue

                    # CONFERE SE JÁ POSSUI ARQUIVOS LANÇADOS
                    if self.confere_arquivo(dados_lanc, range_data=15):
                        self.update_arquivos(self.conn[db], dados_lanc['arq'])
                        self.reavaliar_e_atualizar(self.conn[db], proc)
                    else:
                        self.lanca_arquivo(dados_lanc, url_arquivos)

                        if self.confere_arquivo(dados_lanc, range_data=15):
                            self.update_arquivos(self.conn[db], dados_lanc['arq'])
                            self.reavaliar_e_atualizar(self.conn[db], proc)

                    print('finalizado')
                except MildException:
                    tb = traceback.format_exc()
                    self.logger.warning(tb, extra={'log_prc_id': self.prc_id})
                    continue

                except CriticalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
                    return False

                except FatalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
                    ignorar_id.append(str(proc['aqm_id']))

                    f = tb.find('FatalException:')
                    erro = tb[f + 15:].strip()
                    erro = erro.replace('Não é possível Inativar/Arquivar este processo.','').strip()
                    erro = erro.replace('ï¿½ï¿½','çã')
                    Arquivamento.update(self.conn[db], proc['aqm_id'], {'aqm_lancado': False, 'aqm_erro': erro})
                    continue

        return True

    def update_arquivos(self, db, arquivos):
        arqs = []
        for arq in arquivos:
            arqs.append({'arq_id': arq['arq_id'], 'arq_status': 'OK', 'arq_data_upload': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

        Arquivo.update(db, arqs)

    def reavaliar_e_atualizar(self, db, proc):
        dados = {'aqm_lancado': True, 'aqm_erro': None}
        if self.realiza_reavaliacao:
            if not self.reavaliar(proc):
                dados['aqm_erro'] = 'Possui valores prévios na reversão'

        Arquivamento.update(db, proc['aqm_id'], dados)

    def confere_valor_provavel(self):
        return True
