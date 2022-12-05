from Controllers.varredura import *
from Models.contingenciaModel import Contingencia

# CLASSE PRINCIPAL DA VARREDURA
class PrimeiroGrau(Varredura):
    # METODO CONSTRUTOR
    def __init__(self):
        super().__init__()
        self.arquiva_sentenca = True
        self.captura_movs_download = False
        self.titulo_partes = get_tipo_partes()
        self.ignora_arq_pend = False

    # GERENCIA A CAPTURA DE DADOS, DOWNLOADS E SALVA NA BASE
    def varrer(self, db, login, senha, token=None):

        # CAPTURA CONFIG
        config = ConfigParser()
        config.read('local.ini')
        url_arquivos = config.get('arquivos', 'url_'+db)

        self.chaves_agenda = agenda_base(db)

        if self.area == 3:
            campo_plataforma = 'prc_trf'
            campo_data = 'prc_data_trf'
        else:
            campo_plataforma = 'prc_' + nome_plataforma(self.plataforma)
            campo_data = 'prc_data_' + nome_plataforma(self.plataforma)

        down_pen = self.tipo == 1
        count_error = 0
        self.active_conn = self.conn[db]
        if self.primeiro_ciclo:
            self.driver.get(self.pagina_inicial)
            try:
                if token is None:
                    rl = self.login(login, senha)
                else:
                    rl = self.login(login, senha, token)

                if not rl:
                    print('ERRO NO LOGIN')
                    return False
            except:
                tb = traceback.format_exc()
                print(tb)
                print('Erro no Login')
                time.sleep(60)
                return False

            self.logger.info('Login realizado')
            if not self.reiniciar_navegador:
                self.primeiro_ciclo = False

        # ENQUANTO A QUERY RETORNAR PROCESSOS, A VARREDURA CONTINUA
        procs = [1]
        ignorar_id = []
        casos_com_erro = {}
        while len(procs) > 0:
            query_and = self.query_and

            if len(ignorar_id) > 0:
                ids_txt = ",".join(ignorar_id)
                if self.query_and.strip() != '':
                    query_and = self.query_and + " and"
                query_and = query_and + " prc_id not in ("+ids_txt+") "

            procs = Processo.get_processos_varredura(self.conn[db], self.uf, self.plataforma, self.area, self.dia, query_and=query_and, somente_download_pendente=down_pen, arquivo_morto=self.arquivo_morto, intervalo=self.range, grau=self.grau)
            # print(procs)
            inicio = time.time()
            for proc in procs:
                if Processo.ultimo_update(self.conn[db], proc['prc_id'], self.plataforma, proc[campo_data], area=self.area):
                    print('Processo já varrido - '+str(proc['prc_id']))
                    continue

                if self.varredura_vespertina:
                    print('Varredura vespertina. Aguardando 45s...')
                    time.sleep(45)
                else:
                    if self.intervalo > 0:
                        tempo_total = time.time() - inicio
                        print('sleep ',self.intervalo-tempo_total)
                        if tempo_total < self.intervalo:
                            time.sleep(self.intervalo-tempo_total)
                        inicio = time.time()

                self.prc_id = proc['prc_id']
                self.proc_data = proc
                self.rec_id = None
                self.conn_atual = self.conn[db]
                print('prc_id:', proc['prc_id'], '| prc_numero:', proc['prc_numero'], '| prc_codigo:', proc['prc_codigo'])
                if not self.nao_varrer:
                    self.logger.info('Varrendo Processo', extra={'log_prc_id': self.prc_id})

                try:
                    self.fecha_processo()
                    numero_proc = ajusta_numero(proc['prc_numero'], self.tratar_tamanhos)
                    if self.pagina_processo != '' and self.check_codigo(proc['prc_codigo']):
                        self.driver.get(self.pagina_processo+proc['prc_codigo'])
                    else:
                        if self.pagina_busca != '':
                            self.driver.get(self.pagina_busca)
                        busca = self.busca_processo(numero_proc)

                        if not busca:
                            if (proc[campo_plataforma] is not None and proc[campo_plataforma] > 0) and (self.grau==proc['prc_grau'] or proc['prc_grau'] is None):
                                if self.kill_nao_localizado:
                                    raise FatalException("Processo Localizado Anteriormente", self.uf, self.plataforma, self.prc_id)
                                else:
                                    raise MildException("Processo Localizado Anteriormente", self.uf, self.plataforma, self.prc_id)

                            result_nl = self.trata_dados_nl(proc)
                            Processo.update(self.conn[db], proc['prc_id'], self.plataforma, False, result_nl, area=self.area)
                            self.logger.info('Não Localizado', extra={'log_prc_id': self.prc_id})
                            continue

                    if self.confere_segredo(numero_proc):
                        Processo.update(self.conn[db], proc['prc_id'], self.plataforma, True, {'prc_segredo': True, 'prc_status': 'Segredo de Justiça'}, area=self.area)
                        continue

                    pra_grau = None
                    if self.diferenciar_id_download_2g:
                        pra_grau = 1

                    # CAPTURA OS ARQUIVOS SALVOS NA BASE
                    arquivos_base = ProcessoArquivo.select(self.conn[db], proc['prc_id'], self.plataforma, pra_grau=pra_grau)
                    pendentes = []
                    # VERIFICA QUAIS ARQUIVOS ESTÃO COM O DOWNLOAD PENDENTE
                    if proc['prc_situacao'] in ('Arquivo Morto','Morto','Encerrado'):
                        legado = True
                    else:
                        legado = False
                        for arb in arquivos_base:
                            if arb['pra_erro']:
                                if arb['pra_legado']:
                                    legado = True
                                pendentes.append(arb)

                    full = self.completo or proc[campo_data] is None
                    if not full and self.tipo != 1 and (self.ignora_arq_pend or len(pendentes) == 0 or legado):
                        if self.ultima_movimentacao(proc['cadastro'], proc['prc_id'], self.conn[db]):
                            if not self.confere_arquivos_novos(arquivos_base):
                                Processo.update(self.conn[db], proc['prc_id'], self.plataforma, True, {}, area=self.area)
                                continue

                    if self.nao_varrer:
                        ignorar_id.append(str(proc['prc_id']))
                        print("Pulando Varredura")
                        continue

                    if self.tipo == 2 or self.tipo == 3 or (self.tipo == 1 and self.captura_movs_download):
                        acp_full = full
                        if self.tipo == 1 and self.captura_movs_download:
                            acp_full = True

                        acp = self.acompanhamentos(proc, acp_full, self.conn[db])

                    if self.tipo == 2 or self.tipo == 3:
                        adc, prt, prc, adv = self.ordem_captura(proc)

                        for p in prt['ativo']:
                            if find_string(p['prt_nome'],('TELEFONIA BRASIL','telefônica','telefonica','vivo s.','vivo s/',' vivo ', 'global v', 'global v','CLARO S/A','CLARO S.','coelba','OI S.A','COMPANHIA DE ELETRICIDADE DO ESTADO DA BAHIA')):
                                prt['ativo'], prt['passivo'] = prt['passivo'], prt['ativo']
                                for a in adv:
                                    if a['prr_parte'].upper() == 'POLO ATIVO':
                                        a['prr_parte'] = 'Polo Passivo'
                                        continue
                                    if a['prr_parte'].upper() == 'POLO PASSIVO':
                                        a['prr_parte'] = 'Polo Ativo'
                                break

                        # DEFINE PARTES A PARTIR DOS DADOS CAPTURADOS
                        if 'ativo' in prt and len(prt['ativo']) > 0:
                            if proc['prc_cpf_cnpj'] is None or len(proc['prc_cpf_cnpj']) < 11 or \
                                    proc['prc_cpf_cnpj'] in ('Não Informado', 'Não cadastrado') or proc['prc_cpf_cnpj'].strip('0') == '':
                                    prc['prc_promovente'] = corta_string(prt['ativo'][0]['prt_nome'], 150)
                                    prc['prc_cpf_cnpj'] = prt['ativo'][0]['prt_cpf_cnpj']

                        if 'passivo' in prt and len(prt['passivo']) > 0:
                            if proc['prc_cnpj_promovido'] is None or len(proc['prc_cnpj_promovido']) < 11 or \
                                    proc['prc_cnpj_promovido'] in ('Não Informado', 'Não cadastrado') or proc['prc_cnpj_promovido'].strip('0') == '':
                                prc['prc_promovido'] = corta_string(prt['passivo'][0]['prt_nome'], 150)
                                prc['prc_cnpj_promovido'] = prt['passivo'][0]['prt_cpf_cnpj']


                    target_dir = url_arquivos + '\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\' + str(self.plataforma)
                    target_dir_local = 'C:\\Downloads\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\' + str(self.plataforma)

                    pasta_intermediaria = self.pasta_intermediaria + '\\' + str(proc['prc_id'])
                    # SE FOR PARA FAZER DOWNLOAD, CRIA A PASTA DE DESTINO
                    if self.tipo != 2:
                        create_folder(self.pasta_download, pasta_intermediaria)

                    arq = []
                    if proc['prc_carteira'] in (1, 2) and (self.tipo == 1 or ('prc_migrado' not in prc or not prc['prc_migrado'])):
                        arq = self.download(proc['prc_id'], arquivos_base, pendentes, pasta_intermediaria) if proc['prc_situacao'] is None or proc['prc_situacao'] in ('Ativo','Inativo','Pendente Citação') else []

                    if self.console_log:
                        if self.tipo != 1:
                            # salvar_planilha(proc, prc, adv, self.plataforma)
                            print('acp ',acp)
                            print('adc ',adc)
                            print('prt ',prt)
                            print('adv ',adv)
                            print('prc ',prc)
                        print('arq ', arq)
                    if Processo.ultimo_update(self.conn[db], proc['prc_id'], self.plataforma, proc[campo_data], area=self.area):
                        continue

                    if self.tipo != 1:
                        ProcessoPendencia.insert(self.conn[db], proc['prc_id'], self.plataforma, adc)
                        Acompanhamento.insert(self.conn[db], proc['prc_id'], self.plataforma, 1, acp, chaves_agenda=self.chaves_agenda)
                        ProcessoResponsavel.insert(self.conn[db], proc['prc_id'], adv, self.plataforma, self.apagar_partes_inexistentes)
                        Parte.insert(self.conn[db], proc['prc_id'], prt, self.plataforma, self.apagar_partes_inexistentes)
                        Processo.update(self.conn[db], proc['prc_id'], self.plataforma, True, prc, area=self.area)

                        # CONFERE SE PRECISA ATUALIZAR A CONTINGENCIA DO PROCESSO
                        if 'prc_valor_causa' in prc and prc['prc_valor_causa'].strip() != '':
                            prc_id = proc['prc_id'] if proc['prc_pai'] is None else proc['prc_pai']
                            nao_lancados = Contingencia.select_nao_lancados(self.conn[db], prc_id)
                            if len(nao_lancados) > 0:
                                if nao_lancados[0]['ctg_valor_possivel'] == 0:
                                    ctg_valor_possivel = valor_br(prc['prc_valor_causa'])
                                    Contingencia.update(self.conn[db], nao_lancados[0]['ctg_id'], {'ctg_prc_id': prc_id, 'ctg_valor_possivel': ctg_valor_possivel})

                    print(arq)
                    len_arq = len(arq)
                    arq = self.confere_arquivos_baixados(pendentes, arq)
                    print(arq)
                    ProcessoArquivo.insert(self.conn[db], arq)

                    if len_arq > 0 and self.tipo != 2:
                        try:
                            if not os.path.isdir(target_dir):
                                os.makedirs(target_dir)

                            move_arquivos(pasta_intermediaria, target_dir)
                        except:
                            if not os.path.isdir(target_dir_local):
                                os.makedirs(target_dir_local)

                            move_arquivos(pasta_intermediaria, target_dir_local)

                    if self.tipo == 1:
                        ignorar_id.append(str(proc['prc_id']))
                    # time.sleep(9999)

                except MildException:
                    tb = traceback.format_exc()
                    # print(tb)

                    if self.prc_id in casos_com_erro:
                        casos_com_erro[self.prc_id] += 1
                        if casos_com_erro[self.prc_id] >= 5:
                            ignorar_id.append(str(proc['prc_id']))
                            continue
                    else:
                        casos_com_erro[self.prc_id] = 1

                    self.logger.warning(tb, extra={'log_prc_id': self.prc_id})
                    if tb.find('CNJ') > -1 or tb.find('Unhandled Exception') > -1:
                        count_error += 1
                    else:
                        count_error = 0

                    if count_error == 5:
                        return False

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

    # CONFERE SE O CÓDIGO É VALIDO
    def check_codigo(self, codigo):
        '''
        :param str codigo: codigo _GET de acesso
        '''
        if codigo is None:
            return False

        if codigo.strip() == '':
            return False

        return True

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        prt = self.partes()
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        prc = self.dados(status_atual)
        adv = self.responsaveis()

        return adc, prt, prc, adv

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None, token=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
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

    # ALTERNA ENTRE AS JANELAS ABERTAS
    def alterna_janela(self, indice_janela=1, quantidade_atual=1, tempo=30, aguarda_janela=True, guid=None, not_in_guid=[]):
        wh = self.driver.window_handles
        inicio = time.time()
        if aguarda_janela:
            while len(wh) == quantidade_atual:
                tempoTotal = time.time() - inicio
                if tempoTotal >= tempo:
                    # print("Timeout abrindo processo")
                    # time.sleep(9999)
                    raise MildException("Timeout abrindo janela", self.uf, self.plataforma, self.prc_id)
                try:
                    self.driver.switch_to.alert.accept()
                except NoAlertPresentException:
                    pass

                wh = self.driver.window_handles

        if len(not_in_guid) > 0:
            all_guid = self.driver.window_handles
            for guid in all_guid:
                if guid not in not_in_guid:
                    self.driver.switch_to.window(guid)
                    return

        elif guid is not None:
            self.driver.switch_to.window(guid)
        else:
            self.driver.switch_to.window(wh[indice_janela])

    def confere_arquivos_baixados(self, pendentes, arq):
        for pend in pendentes:
            if pend['pra_grau'] == self.grau:
                achei = False
                for a in arq[:]:
                    if 'pra_id' not in arq:
                        continue

                    if a['pra_id'] == pend['pra_id']:
                        achei = True

                if not achei:
                    p = pend.copy()
                    if p['pra_tentativas'] is None:
                        p['pra_tentativas'] = 0
                    p['pra_tentativas'] = p['pra_tentativas'] + 1

                    if len(arq) > 0:
                        for ind_p in pend:
                            if ind_p not in arq[0]:
                                del p[ind_p]

                    arq.append(p)

        return arq

    def trata_dados_nl(self, dados):
        if self.area == 3:
            return {'prc_trf': dados['prc_trf'], }

        return {}