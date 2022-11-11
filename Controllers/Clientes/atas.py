from Controllers.Clientes._cliente import *
from Models.arquivoModel import *

# CLASSE DO LANÇAMENTO DE ATAS
class AtasCliente(Cliente):

    def __init__(self):
        super().__init__()
        self.tipos_com_ocorrencia = ('Ausência da Parte Autora', 'Autos Conclusos', 'Desistência da Ação',)

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
                query_and = query_and + " prc_id not in (" + ids_txt + ") "

            if last_id > 0:
                if query_and != '':
                    query_and += ' and '
                query_and += ' prc_id > ' + str(last_id)

            procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=query_and, intervalo=self.range, tipo='Atas')
            for proc in procs:
                try:
                    print('proc', proc)

                    if self.pagina_busca != '':
                        self.driver.get(self.pagina_busca)

                    numero_busca = proc[self.campo_busca]
                    busca = self.busca_processo(numero_busca)

                    if not busca:
                        raise FatalException('Removido da Base', self.uf, self.plataforma, self.prc_id)
                        # Processo.update(self.conn[c], proc['prc_id'], self.plataforma, False, {'prc_situacao': 'Removido da Base'}, cliente=True)

                    imagem_lancada = False
                    dados_lanc = self.tratar_dados(db, proc)
                    if proc['arq_acp'] is None or proc['arq_acp'] == 0:
                        if self.confere_arquivo(dados_lanc, range_data=3):
                            imagem_lancada = True
                            if not self.update_and_continue(self.conn[db], dados_lanc, proc['adc_status'] in self.tipos_com_ocorrencia):
                                continue
                        else:
                            for arq in dados_lanc['arq']:
                                if not self.confere_existencia_arquivo(url_arquivos, url_remoto, arq['arq_url']):
                                    raise FatalException('Arquivo não localizado', self.uf, self.plataforma, self.prc_id)

                            self.lanca_arquivo(dados_lanc, url_arquivos)

                            if self.confere_arquivo(dados_lanc, range_data=3):
                                imagem_lancada = True
                                if not self.update_and_continue(self.conn[db], dados_lanc,proc['adc_status'] in self.tipos_com_ocorrencia):
                                    continue
                    else:
                        imagem_lancada = True

                    if not proc['adc_status'] in self.tipos_com_ocorrencia:
                        continue

                    if not self.check_modulo():
                        self.update_and_continue(self.conn[db], dados_lanc, False)
                    elif imagem_lancada:
                        # SE JÁ POSSUIR LANÇAMENTO CORRESPONDENTE, ATUALIZA NA BASE E PASSA PARA O PRÓXIMO
                        if self.confere_lancamento(dados_lanc, range_data_evento=3):
                            self.update_and_continue(self.conn[db], dados_lanc, False)
                            continue

                        if not self.lanca_ocorrencia(dados_lanc):
                            continue

                        if self.confere_lancamento(dados_lanc, range_data_evento=3):
                            self.update_and_continue(self.conn[db], dados_lanc, False)
                            continue

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
                    ignorar_id.append(str(proc['prc_id']))
                    continue

        return True

    def update_and_continue(self, db, dados_lanc, possui_acp):
        print('Arquivo existente')
        arqs = []
        if possui_acp:
            for arq in dados_lanc['arq']:
                arqs.append({'arq_id': arq['arq_id'], 'arq_acp': 1})
        else:
            for arq in dados_lanc['arq']:
                arqs.append({'arq_id': arq['arq_id'], 'arq_status': 'OK',
                             'arq_data_upload': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

        Arquivo.update(db, arqs)
        return possui_acp