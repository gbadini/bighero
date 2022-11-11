from Controllers.Clientes._cliente import *
import json
from Config.tipos_ocorrencia.services.compara_ocorrencias import ComparaOcorrencias

# CLASSE DE LANÇAMENTO DE OCORRÊNCIA NOS SISTEMAS CLIENTES
class OcorrenciasTJCliente(Cliente):

    def __init__(self):
        super().__init__()
        self.movs = []
        self.ordem_usuario = 2
        self.pre_conferido = False
        self.servico_ocorrencias = ComparaOcorrencias()

    # GERENCIA A CAPTURA DE DADOS, DOWNLOADS E SALVA NA BASE
    def varrer(self, db, login, senha):
        campo_data = 'prc_data_update1'

        # CONFERE PREVIAMENTE OS ACOMPANHAMENTOS QUE NÃO SE APLICAM
        procs = [1]
        not_in = []
        # query_and = self.query_and
        # if not self.pre_conferido:
        #     while len(procs) > 0:
        #         procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=query_and, intervalo=self.range, tipo='OcorrenciasTJ')
        #         for proc in procs:
        #             # print('proc',proc['prc_id'], proc)
        #             print('conferindo acompanhamentos do processo '+str(proc['prc_sequencial']))
        #             acps = Acompanhamento.lista_movs(self.conn[db], proc['prc_id'], None, ignora_cliente=True, ocorrencia=True)
        #             dados_lanc = self.tratar_dados(self.conn[db], acps)
        #             if len(dados_lanc) > 0 or proc['prc_sequencial'] is None:
        #                 print('Ocorrencia localizada')
        #                 not_in.append(str(proc['prc_id']))
        #             else:
        #                 print('Pulando Processo')
        #
        #         if len(not_in) > 0:
        #             ids_txt = ",".join(not_in)
        #             query_and = ''
        #             if self.query_and.strip() != '':
        #                 query_and = self.query_and + " and"
        #             query_and = query_and + " prc_id not in (" + ids_txt + ")"

            # print('query_and', query_and)

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

        # CAPTURA CONFIG
        config = ConfigParser()
        config.read('local.ini')
        url_arquivos = config.get('arquivos', 'url_'+db)
        lanca_arquivos = config.getboolean('arquivos', 'lancar')
        print('url_arquivos', url_arquivos)

        # ENQUANTO A QUERY RETORNAR PROCESSOS, A VARREDURA CONTINUA
        procs = [1]
        ignorar_id = []
        # last_id = 0
        while len(procs) > 0:
            query_and = self.query_and
            if len(ignorar_id) > 0:
                ids_txt = ",".join(ignorar_id)
                query_and = ''
                if self.query_and.strip() != '':
                    query_and = self.query_and + " and"
                query_and = query_and + " prc_id not in (" + ids_txt + ") "

            # if last_id > 0:
            #     if query_and != '':
            #         query_and += ' and '
            #     query_and += ' prc_id > ' + str(last_id)

            procs = Processo.get_processos_cliente(self.conn[db], self.plataforma, query_and=query_and, intervalo=self.range, tipo='OcorrenciasTJ')
            inicio = time.time()
            for proc in procs:
                print('proc', proc)

                if self.intervalo > 0:
                    tempo_total = time.time() - inicio
                    if tempo_total < self.intervalo:
                        time.sleep(self.intervalo - tempo_total)
                    inicio = time.time()

                self.prc_id = proc['prc_id']
                # last_id = proc['prc_id']
                print('prc_id ', proc['prc_id'])
                print(self.campo_busca, proc[self.campo_busca])
                self.logger.info('Iniciando Lançamento de Ocorrência', extra={'log_prc_id': self.prc_id})

                try:
                    pai = None
                    inativo = False
                    if proc['prc_pai'] is not None and proc['prc_pai'] > 0:
                        print('procurando processo pai')
                        pai = Processo.get_processo_by_id(self.conn[db], proc['prc_pai'])
                        if pai[0]['prc_situacao'] != 'Ativo':
                            print('processo inativo')
                            inativo = True
                        print('sequencial alterado para', pai[0]['prc_sequencial'])
                        numero_busca = pai[0]['prc_sequencial']
                    else:
                        numero_busca = proc[self.campo_busca]

                    print('capturando acps')
                    # acp_ocorrencia status: 0=não se aplica, 1=ocorrencia lançada, 2=arquivo lançado,
                    acps = Acompanhamento.lista_movs(self.conn[db], proc['prc_id'], None, ignora_cliente=True, ocorrencia=not lanca_arquivos)
                    if inativo:
                        for acp in acps:
                            Acompanhamento.update(self.conn[db], [{'acp_id': acp['acp_id'], 'acp_ocorrencia': 0}, ])

                        if pai is not None:
                            acps = Acompanhamento.lista_movs(self.conn[db], proc['prc_pai'], None, ignora_cliente=True, ocorrencia=not lanca_arquivos)
                            for acp in acps:
                                Acompanhamento.update(self.conn[db], [{'acp_id': acp['acp_id'], 'acp_ocorrencia': 0}, ])

                        continue
                    print('tratando dados')
                    dados_lanc = self.tratar_dados(self.conn[db], acps, lanca_arquivos, proc['prc_area'])
                    if len(dados_lanc) == 0:
                        print('Nenhum acp localizado')
                        continue

                    if self.pagina_busca != '':
                        self.driver.get(self.pagina_busca)
                    busca = self.busca_processo(numero_busca)

                    if not busca:
                        Processo.update(self.conn[db], proc['prc_id'], self.plataforma, False, {'prc_situacao': 'Removido da Base'}, cliente=True)
                        print('Removido da Base')
                        continue

                    # CONFERE SE O PROCESSO ESTÁ ATIVO
                    status = self.captura_status()
                    if status in ('Arquivo Morto', ):
                        raise FatalException('Processo Inativo', self.uf, self.plataforma, self.prc_id)

                    # print('dados_lanc', dados_lanc)
                    # print('acps', acps)
                    pras = {}
                    for acp in dados_lanc:
                        # print('acp', acp)

                        if lanca_arquivos and acp['arquivo'][0] != '' and acp['arquivo'][0] != '-':
                            pra = ProcessoArquivo.select_by_date(self.conn[db], acp['acp_id'], acp['acp_plataforma'], proc['prc_area']!=2)
                            # print('pra', pra)
                            if len(pra) > 0:
                                data_index = acp['acp_cadastro'].strftime('%d/%m/%y %H:%M')
                                # data_index = pra[0]['pra_arquivo']
                                if data_index not in pras:
                                    pras[data_index] = {}
                                    pras[data_index]['pra'] = pra
                                    pras[data_index]['acps'] = []

                                pras[data_index]['acps'].append(acp)
                            # if inativo:
                            #     Acompanhamento.update(self.conn[db], [{'acp_id': acp['acp_id'], 'acp_ocorrencia': 0}, ])
                            #     continue
                        if acp['acp_ocorrencia'] is not None:
                            continue

                        print('iniciando lançamento')

                        # SE JÁ POSSUIR LANÇAMENTO CORRESPONDENTE, ATUALIZA NA BASE E PASSA PARA O PRÓXIMO
                        if self.confere_lancamento(acp, range_data_evento=acp['date_range']):
                            print('ja possui')
                            # ATUALIZAR
                            Acompanhamento.update(self.conn[db], [{'acp_id': acp['acp_id'], 'acp_ocorrencia': 1},])
                            continue

                        print('lançando')
                        if not self.lanca_ocorrencia(acp):
                            Acompanhamento.update(self.conn[db], [{'acp_id': acp['acp_id'], 'acp_ocorrencia': 0}, ])
                            continue

                        if self.confere_lancamento(acp, range_data_evento=acp['date_range']):
                            # ATUALIZAR
                            Acompanhamento.update(self.conn[db], [{'acp_id': acp['acp_id'], 'acp_ocorrencia': 1},])

                    if lanca_arquivos:
                        # print('pras',pras)
                        arquivos = []
                        for pr in pras:
                            temparq = []
                            total_arqs = 0
                            if len(pras[pr]['acps']) == 1:
                                arq = pras[pr]['acps'][0]
                                arq['pra'] = pras[pr]['pra']
                                arquivos.append(arq)
                            else:
                                for acp in pras[pr]['acps']:
                                    arq = acp
                                    arq['pra'] = []
                                    for pra in pras[pr]['pra']:
                                        if pra['pra_descricao'] in acp['acp_esp'] or pra['pra_original'] in acp['acp_esp']:
                                            arq['pra'].append(pra)
                                            total_arqs = total_arqs + 1

                                    if len(arq['pra']) > 0:
                                        temparq.append(arq)

                                if len(pras[pr]['pra']) == total_arqs:
                                    arquivos = arquivos + temparq
                                else:
                                    # arq = pras[pr]['acps'][0]
                                    # arq['pra'] = pras[pr]['pra']
                                    # del pras[pr]['acps'][0]
                                    for acp in pras[pr]['acps']:
                                        # esp = acp['acp_esp'].replace(r'\r', '').replace(r'\n', '')
                                        # esp = corta_string(esp, 100, sufixo='...')
                                        # arq['obs_arquivo'] += ' | ' + esp
                                        arq = acp
                                        arq['pra'] = pras[pr]['pra']
                                        arquivos.append(arq)

                        url = url_arquivos + '\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\'
                        self.confere_lanca_arquivos(arquivos, db, url)

                        arquivos_nao_lancados = ProcessoArquivo.select_arquivos_vinculados(self.conn[db], proc['prc_id'])
                        nao_lancados = []
                        print('arquivos_nao_lancados',arquivos_nao_lancados)
                        for anl in arquivos_nao_lancados:
                            pra_data = anl['pra_data'].strftime('%d/%m/%Y')
                            pra_descricao = anl['pra_descricao']
                            achei = False
                            for inl, nl in enumerate(nao_lancados):
                                if nl['data_arquivo'] == pra_data:
                                    nao_lancados[inl]['pra'].append(anl)
                                    nao_lancados[inl]['obs_arquivo'] += ' | ' + pra_descricao
                                    achei = True
                                    break

                            if not achei:
                                nao_lancados.append({'data_arquivo': pra_data, 'obs_arquivo': pra_descricao, 'pra': [anl], 'arquivo': ['Outros',]})

                        print('nao_lancados', nao_lancados)
                        if len(nao_lancados) > 0:
                            for inl, nl in enumerate(nao_lancados):
                                if len(nl['pra']) == 1:
                                    a = ComparaOcorrencias()
                                    r = a.execute(nl['obs_arquivo'], '')
                                    print(r)
                                    if r:
                                        if r['arquivo'] and r['arquivo'][0] != '' and r['arquivo'][0] != '-':
                                            nao_lancados[inl]['arquivo'] = r['arquivo']

                                nao_lancados[inl]['obs_arquivo'] = nl['data_arquivo'] + ' - Arquivos TJ - ' + nl['obs_arquivo']

                            self.confere_lanca_arquivos(nao_lancados, db, url)

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

        self.logger.info('Ciclo encerrado')
        return True

    # REALIZA O PROCESSO DE CONFERENCIA E LANÇAMENTO DE ARQUIVOS
    def confere_lanca_arquivos(self, arquivos, db, url):
        for pr in arquivos:
            # if pr['arquivo'][0] == 'Comentário':
            #     coment = self.confere_arquivo_comentario(pr, range_data_evento=3)
            #     if not coment.is_integer():
            #         continue
            #
            #     self.lanca_arquivo_comentario(pr, url_arquivos + '\\' + db + '\\' + proc['prc_estado'] + '\\' + str(
            #         proc['prc_id']) + '\\' + str(pr['pra'][0]['pra_plt_id']) + '\\', coment)
            #     coment = self.confere_arquivo_comentario(pr, range_data_evento=3)
            #      if coment.is_integer() or not coment:
            #         continue
            # else:
            if self.confere_arquivo(pr, False, False):
                print('Arquivo existente')
                arqs = []
                for arq in pr['pra']:
                    arqs.append({'pra_id': arq['pra_id'], 'pra_ocorrencia': 1})
                ProcessoArquivo.update(self.conn[db], arqs)
                continue

            print('lançando imagem')
            url_arquivo = url + str(pr['pra'][0]['pra_plt_id']) + '\\'
            self.lanca_arquivo(pr, url_arquivo)
            # if not self.lanca_arquivo(pr, 'C:\\downloads\\rek\\'+proc['prc_estado']+'\\'+str(proc['prc_id'])+'\\'+str(pr['pra'][0]['pra_plt_id'])+'\\'):
            #     Acompanhamento.update(self.conn[db], [{'acp_id': pr['acp_id'], 'acp_ocorrencia': 0}, ])
            #     continue

            if self.confere_arquivo(pr, False, False):
                print('Arquivo existente')
                arqs = []
                for arq in pr['pra']:
                    arqs.append({'pra_id': arq['pra_id'], 'pra_ocorrencia': 1})
                ProcessoArquivo.update(self.conn[db], arqs)
                continue

    # CONFERE SE OS DADOS LANÇADOS NOS CAMPOS CONFEREM COM A BASE
    def tratar_dados(self, base, acps, lanca_imagem, area):
        dados_lanc = []

        return dados_lanc

    # CONFERE QUAL O TIPO DO ACOMPANHAMENTO
    def tipo_acp(self, esp):
        pass