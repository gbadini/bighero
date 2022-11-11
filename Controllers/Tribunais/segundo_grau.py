from Controllers.Tribunais.primeiro_grau import *

# CLASSE PRINCIPAL DA VARREDURA
class SegundoGrau(PrimeiroGrau):

    # METODO CONSTRUTOR
    def __init__(self):
        super().__init__()
        self.primeiro_ciclo = True
        self.arquiva_sentenca = True
        self.captura_movs_download = False
        self.apagar_partes_inexistentes = False
        self.diferenciar_id_download_2g = False

    # GERENCIA A CAPTURA DE DADOS, DOWNLOADS E SALVA NA BASE
    def varrer(self, db, login, senha, token=None):

        # CAPTURA CONFIG
        config = ConfigParser()
        config.read('local.ini')
        url_arquivos = config.get('arquivos', 'url_'+db)

        self.chaves_agenda = agenda_base(db)
        self.titulo_partes = get_tipo_partes(grau=2)
        # print(self.titulo_partes)
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

            if not self.reiniciar_navegador:
                self.primeiro_ciclo = False

        # ENQUANTO A QUERY RETORNAR PROCESSOS, A VARREDURA CONTINUA
        procs = [1]
        ignorar_id = []
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
            self.numero_original = False
            for proc in procs:
                if Processo.ultimo_update(self.conn[db], proc['rec_id'], self.plataforma, proc['rec_data_update'], 2):
                    print('Processo já varrido')
                    continue

                if self.intervalo > 0:
                    tempo_total = time.time() - inicio
                    print('sleep',self.intervalo-tempo_total)
                    if tempo_total < self.intervalo:
                        time.sleep(self.intervalo-tempo_total)
                    inicio = time.time()

                self.prc_id = proc['prc_id']
                self.proc_data = proc
                self.rec_id = proc['rec_id']
                self.conn_atual = self.conn[db]
                print('prc_id:', proc['prc_id'], '| rec_id:', proc['rec_id'])
                print('prc_numero:', proc['prc_numero'], '| rec_numero:', proc['rec_numero'], '| rec_codigo:', proc['rec_codigo'])
                self.buscar_origem = False
                self.numero_original = False
                try:
                    self.fecha_processo()
                    self.numero_original = proc['rec_codigo'] if proc['rec_codigo'] is not None else 3

                    if self.check_confere_origem(proc):
                        prc_numero = proc['prc_numero']
                        self.buscar_origem = True
                    else:
                        if proc['rec_numero'] is not None and proc['rec_numero'].strip() != '':
                            prc_numero = proc['rec_numero']
                        else:
                            self.numero_original = False
                            prc_numero = proc['prc_numero']
                            if proc['prc_numero_2g'] is not None and proc['prc_numero_2g'].strip() != '' and proc['prc_numero_2g'].strip() != '0':
                                prc_numero = proc['prc_numero_2g']

                    numero_proc = ajusta_numero(prc_numero, self.tratar_tamanhos)
                    print("numero_proc",numero_proc)
                    print("rec_numero", proc['rec_numero'])
                    if self.pagina_processo != '' and self.check_codigo(proc['rec_codigo']) and self.check_confere_origem(proc):
                        self.driver.get(self.pagina_processo+proc['rec_codigo'])
                    else:
                        if self.pagina_busca != '':
                            self.driver.get(self.pagina_busca)
                        busca = self.busca_processo(numero_proc)

                        if not busca:
                            if proc['rec_id'] is not None:
                                if not self.buscar_origem:
                                    if self.kill_nao_localizado:
                                        raise FatalException("Processo Localizado Anteriormente", self.uf, self.plataforma, self.prc_id)
                                    else:
                                        raise MildException("Processo Localizado Anteriormente", self.uf, self.plataforma, self.prc_id)

                            print('não localizado')
                            if proc['rec_id'] is None:
                                Processo.update(self.conn[db], proc['prc_id'], self.plataforma, False, {'prc_grau':1}, grau=2)
                            else:
                                Processo.update(self.conn[db], proc['prc_id'], self.plataforma, False, {}, grau=2)

                            continue

                    if not self.confere_recursos(self.conn[db], proc):
                        if self.buscar_origem:
                            Processo.update(self.conn[db], proc['prc_id'], self.plataforma, True, {}, grau=2)
                        continue

                    if self.buscar_origem:
                        Processo.update(self.conn[db], proc['prc_id'], self.plataforma, True, {}, grau=2)
                        continue

                    if self.confere_segredo(numero_proc, proc['rec_codigo']):
                        Recurso.update(self.conn[db], proc['prc_id'], proc['rec_id'], self.plataforma, {'rec_status':'Segredo de Justiça','rec_segredo': True,})
                        Processo.update(self.conn[db], proc['prc_id'], self.plataforma, True, {}, grau=2)
                        continue

                    # CAPTURA OS ARQUIVOS SALVOS NA BASE
                    grau_down = None
                    pra_rec_id = None
                    if self.diferenciar_id_download_2g:
                        grau_down = self.grau
                        pra_rec_id = self.rec_id

                    arquivos_base = ProcessoArquivo.select(self.conn[db], proc['prc_id'], self.plataforma, pra_grau=grau_down, pra_rec_id=pra_rec_id)
                    pendentes = []
                    # VERIFICA QUAIS ARQUIVOS ESTÃO COM O DOWNLOAD PENDENTE
                    legado = False
                    for arb in arquivos_base:
                        if arb['pra_erro']:
                            if arb['pra_legado']:
                                legado = True
                            pendentes.append(arb)

                    full = self.completo or proc['rec_data_update'] is None
                    if not full and self.tipo != 1 and (len(pendentes) == 0 or legado):
                        if self.ultima_movimentacao(proc['cadastro'], proc['prc_id'], self.conn[db]):
                            Recurso.update(self.conn[db], proc['prc_id'], proc['rec_id'], self.plataforma, {})
                            Processo.update(self.conn[db], proc['prc_id'], self.plataforma, True, {}, grau=2)
                            continue

                    if self.nao_varrer:
                        if proc['rec_id'] is not None:
                            if legado or len(pendentes) > 0 or self.confere_arquivos_novos(arquivos_base):
                                ignorar_id.append(str(proc['rec_id']))

                        if self.confere_arquivos_novos():
                            print("Pulando Varredura")
                            continue

                    # time.sleep(9999)
                    if self.tipo == 2 or self.tipo == 3:
                        # full = self.completo or proc[campo_data] is None
                        acp = self.acompanhamentos(proc, full, self.conn[db])
                        adc, prt, rec, adv = self.ordem_captura(proc)

                        ambos = False
                        if len(prt['ativo']) > 0 and prt['ativo'][0]['prt_nome'] == 'AMBOS':
                            ambos = True
                            prt = {'ativo': [], 'passivo': []}
                            adv = []

                        # DEFINE PARTES A PARTIR DOS DADOS CAPTURADOS
                        if ambos:
                            rec['rec_recorrente'] = 'AMBOS'
                            rec['rec_recorrido'] = 'AMBOS'

                        else:
                            if 'ativo' in prt and len(prt['ativo']) > 0:
                                rec['rec_recorrente'] = corta_string(prt['ativo'][0]['prt_nome'], 100)

                            if 'passivo' in prt and len(prt['passivo']) > 0:
                                rec['rec_recorrido'] = corta_string(prt['passivo'][0]['prt_nome'], 100)

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

                        for a in adv:
                            if a['prr_cargo'] == 'Juiz':
                                rec['rec_relator'] = a['prr_nome']
                                break

                    target_dir = url_arquivos + '\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\' + str(self.plataforma)
                    target_dir_local = 'C:\\Downloads\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\' + str(self.plataforma)

                    pasta_intermediaria = self.pasta_intermediaria + '\\' + str(proc['prc_id'])
                    # SE FOR PARA FAZER DOWNLOAD, CRIA A PASTA DE DESTINO
                    if self.tipo != 2:
                        create_folder(self.pasta_download, pasta_intermediaria)

                    arq = []
                    if proc['prc_carteira'] in (1, 2):
                        arq = self.download(proc['prc_id'], arquivos_base, pendentes, pasta_intermediaria) if proc['prc_situacao'] is None or proc['prc_situacao'] in ('Ativo','Inativo','Pendente Citação') else []
                    # arq = self.download(proc['prc_id'], arquivos_base, pendentes, pasta_intermediaria)

                    if self.tipo != 1:
                        print('acp ',acp)
                        print('adc ',adc)
                        print('prt ',prt)
                        print('adv ',adv)
                        print('rec ',rec)
                    print('arq ', arq)

                    # time.sleep(9999)
                    # continue
                    if Processo.ultimo_update(self.conn[db], proc['rec_id'], self.plataforma, proc['rec_data_update'], 2):
                        continue
                    # time.sleep(9999)
                    rec_id = proc['rec_id']
                    dados_prc = {}
                    dados_prc['prc_grau'] = 1
                    if self.tipo != 1:
                        if rec['rec_status'] == 'Ativo':
                            dados_prc['prc_status'] = 'Ativo'
                            dados_prc['prc_grau'] = 2
                            if proc['prc_numero2'] is None:
                                dados_prc['prc_numero2'] = rec['rec_numero']



                            if proc['rec_id'] is None:
                                result = Recurso.select(self.conn[db], proc['prc_id'], rec_codigo=proc['rec_codigo'], rec_numero=proc['rec_numero'], rec_plt_id=self.plataforma)
                                if len(result) > 0:
                                    continue

                        rec_id = Recurso.update(self.conn[db], proc['prc_id'], proc['rec_id'], self.plataforma, rec)
                        ProcessoPendencia.insert(self.conn[db], proc['prc_id'], self.plataforma, adc)
                        Acompanhamento.insert(self.conn[db], proc['prc_id'], self.plataforma, 2, acp, rec_id, chaves_agenda=self.chaves_agenda)
                        ProcessoResponsavel.insert(self.conn[db], proc['prc_id'], adv, self.plataforma, self.apagar_partes_inexistentes)
                        Parte.insert(self.conn[db], proc['prc_id'], prt, self.plataforma, self.apagar_partes_inexistentes)
                        Processo.update(self.conn[db], proc['prc_id'], self.plataforma, True, dados_prc, grau=2)

                    if self.diferenciar_id_download_2g:
                        for ar in arq:
                            ar['pra_rec_id'] = rec_id

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
                    print(tb)
                    if tb.find('CNJ') > -1:
                        count_error += 1
                    else:
                        count_error = 0

                    if count_error == 5:
                        return False
                    # time.sleep(9999)
                    continue

                except CriticalException:
                    tb = traceback.format_exc()
                    print(tb)
                    # time.sleep(9999)
                    return False

                except FatalException:
                    tb = traceback.format_exc()
                    self.logger.critical(tb, extra={'log_prc_id': self.prc_id})
                    ignorar_id.append(str(proc['prc_id']))
                    continue

        self.logger.info('Ciclo encerrado')
        return True

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        prt = self.partes()
        status_atual = 'Ativo' if self.completo else proc['rec_status']
        prc = self.dados(status_atual)
        adv = self.responsaveis()

        return adc, prt, prc, adv

    # CONFERE SE OS RECURSOS ESTÃO NA BASE
    def confere_recursos(self, base, proc):
        return True

    def check_confere_origem(self, proc):
        if proc['prc_data_2g'] is None:
            return True

        if proc['prc_data_2g'] is not None and proc['cadastro2'] is not None and proc['cadastro2'] >= proc['prc_data_2g']:
            return True

        return False