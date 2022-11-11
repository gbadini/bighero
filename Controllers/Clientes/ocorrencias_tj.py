from Controllers.Clientes._cliente import *
from Models.diarioprocessoModel import DiarioProcesso
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
        self.pra_bloqueado = []

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
                            raise FatalException('Processo Inativo', self.uf, self.plataforma, self.prc_id)
                            # print('processo inativo')
                            inativo = True
                        print('sequencial alterado para', pai[0]['prc_sequencial'])
                        numero_busca = pai[0]['prc_sequencial']
                    else:
                        numero_busca = proc[self.campo_busca]

                    print('capturando acps')
                    acps = Acompanhamento.lista_movs_tj(self.conn[db], proc['prc_id'], semente_sem_ocorrencia=True)
                    # acps = Acompanhamento.lista_movs(self.conn[db], proc['prc_id'], None, ignora_cliente=True)
                    if inativo:
                        for acp in acps:
                            Acompanhamento.update(self.conn[db], [{'acp_id': acp['acp_id'], 'acp_ocorrencia': 0}, ])

                        if pai is not None:
                            acps = Acompanhamento.lista_movs_tj(self.conn[db], proc['prc_id'], semente_sem_ocorrencia=True)
                            # acps = Acompanhamento.lista_movs(self.conn[db], proc['prc_pai'], None, ignora_cliente=True, ocorrencia=not lanca_arquivos)
                            for acp in acps:
                                Acompanhamento.update(self.conn[db], [{'acp_id': acp['acp_id'], 'acp_ocorrencia': 0}, ])

                        continue
                    print('tratando dados')
                    dados_lanc = self.tratar_dados(self.conn[db], acps, lanca_arquivos, proc['prc_area'])

                    if not lanca_arquivos or ('pra_id' in proc and proc['pra_id'] is None):
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
                    for acp in dados_lanc:
                        if acp['acp_ocorrencia'] is not None:
                            continue

                        print('iniciando lançamento')

                        # SE JÁ POSSUIR LANÇAMENTO CORRESPONDENTE, ATUALIZA NA BASE E PASSA PARA O PRÓXIMO
                        if self.confere_lancamento(acp, range_data_evento=3):
                            print('ja possui')
                            # ATUALIZAR
                            Acompanhamento.update_batch(self.conn[db], acp['acps'], {'acp_ocorrencia': 1})
                            continue

                        print('lançando')
                        if not self.lanca_ocorrencia(acp):
                            Acompanhamento.update_batch(self.conn[db], acp['acps'], {'acp_ocorrencia': 0})
                            continue

                        if self.confere_lancamento(acp, range_data_evento=3):
                            # ATUALIZAR
                            Acompanhamento.update_batch(self.conn[db], acp['acps'], {'acp_ocorrencia': 1})

                    if lanca_arquivos:
                        nao_lancados = []
                        # VERIFICA SE NENHUM ARQUIVO DO PROCESSO FOI LANÇADO
                        ent = ProcessoArquivo.confere_arquivos_entrantes(self.conn[db], proc['prc_id'])
                        acp = Acompanhamento.lista_movs_tj(self.conn[db], proc['prc_id'])[-1]
                        pra_ent = ProcessoArquivo.select_arquivos_entrantes(self.conn[db], proc['prc_id'])

                        ci = self.confere_copia_integral()
                        if ci:
                            url = url_arquivos + '\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\'
                            r = re.search("(\\d+)(\/)(\\d+)(\/)(\\d+)", ci[0], re.IGNORECASE | re.DOTALL)
                            dia = r.group(0)
                            acp_cadastro = datetime.strptime(dia + ' 23:59:59', '%d/%m/%Y %H:%M:%S')
                            novos_entrantes = []
                            print('acp_cadastro', acp_cadastro)
                            for pre in pra_ent:
                                # print(pre['pra_data'], acp_cadastro)
                                if (pre['pra_data'] is None or pre['pra_data'] <= acp_cadastro) and pre['pra_ocorrencia'] is None:
                                    if self.files_to_ignore(pre, url) or pre['pra_data'] is None:
                                        ProcessoArquivo.update(self.conn[db], [{'pra_ocorrencia': 0, 'pra_id': pre['pra_id']}])
                                        continue
                                    novos_entrantes.append(pre)

                            print(novos_entrantes)
                            if len(novos_entrantes) > 0:
                                if not self.insere_arquivos_entrantes(ci[1], novos_entrantes, url):
                                    raise FatalException("Erro ao lançar arquivos retroativos", self.uf, self.plataforma, self.prc_id, False)

                            ProcessoArquivo.update_arquivos_lancados(self.conn[db], proc['prc_id'], {'pra_ocorrencia': 1}, acp_cadastro)

                            if ent and len(acp) > 3 and len(pra_ent) >= 4:
                                ent = ProcessoArquivo.confere_arquivos_entrantes(self.conn[db], proc['prc_id'])
                                if not ent:
                                    raise MildException("Cópia integral localizada", self.uf, self.plataforma, self.prc_id, False)

                                ent = False

                        # SE NENHUM ARQUIVO FOI LANÇADO E O PROCESSO POSSUI MAIS DE TRÊS OCORRÊNCIAS LANÇADAS  TODOS OS ARQUIVOS SÃO LANÇADOS EM UM PACOTE UNICO
                        if ent and len(acp) > 3 and len(pra_ent) >= 4:
                            if ent == 'não varrer':
                                raise FatalException('Baixar arquivos do processo novamente', self.uf, self.plataforma, self.prc_id)

                            # drp_ent = DiarioProcesso.select_diarios_entrantes(self.conn[db], proc['prc_id'])
                            # CONFERE SE ARQUIVO É MAIOR QUE O PERMITIDO, OU DE EXTENSÃO NÃO PERMITIDA
                            url = url_arquivos + '\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\'
                            for pra in pra_ent[:]:
                                if self.files_to_ignore(pra, url) or pra['pra_data'] is None:
                                    ProcessoArquivo.update(self.conn[db], [{'pra_ocorrencia': 0, 'pra_id': pra['pra_id']}])
                                    pra_ent.remove(pra)

                            dt = acp['acp_cadastro'].strftime('%d/%m/%Y')
                            evento = acp['acp_tipo'] if acp['acp_tipo'] is not None and acp['acp_tipo'] != '' else corta_string(acp['acp_esp'], 180)
                            descricao = 'Cópia integral até o dia ' + dt + ' - Evento ' + evento.upper()
                            nao_lancados = [{'data_arquivo': dt, 'obs_arquivo': descricao, 'pra': pra_ent, 'drp': [], 'arquivo': ['Outros',]},]

                        # SE JA POSSUI ARQUIVOS LANÇADOS, LANÇA OS ARQUIVOS INDIVIDUALMENTE
                        else:
                            # CAPTURA ARQUIVOS VINCULADOS AO PROCESSO
                            # seis_meses = datetime.today() + relativedelta(days=-180)
                            pra_nv = ProcessoArquivo.select_arquivos_vinculados(self.conn[db], proc['prc_id'], proc['prc_estado'])
                            print('pra_nv', pra_nv)
                            for plt in pra_nv:
                                # CAPTURA MOVIMENTAÇÕES VINCULADAS AO PROCESSO E A PLATAFORMA
                                lista = Acompanhamento.lista_movs_tj(self.conn[db], proc['prc_id'], plt)
                                # ITERA SOBRE AS DATAS
                                for dt in pra_nv[plt]:
                                    # ITERA SOBRE AS HORAS
                                    for hr in pra_nv[plt][dt]:
                                        # ITERA SOBRE OS GRAUS
                                        for gr in pra_nv[plt][dt][hr]:
                                            pular = False
                                            for pra in pra_nv[plt][dt][hr][gr][:]:
                                                # CONFERE SE ARQUIVO JA FOI LANÇADO
                                                # if pra['pra_ocorrencia'] is not None and pra['pra_ocorrencia']:
                                                #     pular = True
                                                #     break
                                                # CONFERE SE ARQUIVO JA FOI LANÇADO
                                                if pra['pra_ocorrencia'] is not None:
                                                    pra_nv[plt][dt][hr][gr].remove(pra)
                                                    continue

                                                # CONFERE SE ARQUIVO ESTÁ COM ERRO
                                                if pra['pra_erro'] is not None and pra['pra_erro']:
                                                    pular = True
                                                    break

                                                # CONFERE SE ARQUIVO FOI EXCLUIDO NO TJ
                                                if pra['pra_excluido'] is not None and pra['pra_excluido']:
                                                    ProcessoArquivo.update(self.conn[db], [{'pra_ocorrencia': 0, 'pra_id': pra['pra_id']}])
                                                    pra_nv[plt][dt][hr][gr].remove(pra)
                                                    continue

                                                # CONFERE SE DATA É NULA
                                                if pra['pra_data'] is None:
                                                    ProcessoArquivo.update(self.conn[db], [{'pra_ocorrencia': 0, 'pra_id': pra['pra_id']}])
                                                    pra_nv[plt][dt][hr][gr].remove(pra)
                                                    continue

                                                # CONFERE SE ARQUIVO ESTÁ SOB SEGREDO DE JUSTIÇA
                                                if pra['pra_sigilo'] is not None and pra['pra_sigilo']:
                                                    ProcessoArquivo.update(self.conn[db], [{'pra_ocorrencia': 0, 'pra_id': pra['pra_id']}])
                                                    pra_nv[plt][dt][hr][gr].remove(pra)
                                                    continue

                                                # CONFERE SE ARQUIVO É ANTIGO
                                                # if not ent and pra['pra_data'] < seis_meses:
                                                #     ProcessoArquivo.update(self.conn[db], [{'pra_ocorrencia': 0, 'pra_id':pra['pra_id']}])
                                                #     pular = True
                                                #     break

                                                # CONFERE SE ARQUIVO É MAIOR QUE O PERMITIDO, OU DE EXTENSÃO NÃO PERMITIDA
                                                url = url_arquivos + '\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\'
                                                if self.files_to_ignore(pra, url):
                                                    ProcessoArquivo.update(self.conn[db], [{'pra_ocorrencia': 0, 'pra_id':pra['pra_id']}])
                                                    pra_nv[plt][dt][hr][gr].remove(pra)

                                            # SE JA TEVE ARQUIVO LANÇADO, PULA
                                            if pular:
                                                break

                                            # PULA DATA CASO NÃO TENHA ARQUIVOS DISPONÍVEIS
                                            if len(pra_nv[plt][dt][hr][gr]) == 0:
                                                continue

                                            acps = []
                                            descricoes = []
                                            # VINCULA ARQUIVO COM OCORRENCIA
                                            for l in lista:
                                                acp_cadastro = l['acp_cadastro'].strftime('%d/%m/%Y %H:%M')
                                                pra_data = pra_nv[plt][dt][hr][gr][0]['pra_data'].strftime('%d/%m/%Y %H:%M')
                                                if acp_cadastro == pra_data and pra_nv[plt][dt][hr][gr][0]['pra_grau'] == l['acp_grau']:
                                                    acps.append(l)
                                                    tipo = l['acp_tipo'] if l['acp_tipo'] is not None and l['acp_tipo'] != '' else corta_string(l['acp_esp'],100)
                                                    if tipo not in descricoes:
                                                        if pra_nv[plt][dt][hr][gr][0]['pra_rec_id'] == l['acp_rec_id']:
                                                            descricoes.append(tipo)
                                                    # print(plt, dt, hr, pra, l['acp_tipo'])
                                            if len(descricoes) == 0:
                                                # SE NÃO CONSEGUE VINCULAR COM OCORRÊNCIA, VINCULA COM A DESCRIÇÃO DO ARQUIVO
                                                for pra in pra_nv[plt][dt][hr][gr]:
                                                    pra_descricao = corta_string(pra['pra_descricao'], 50)
                                                    if pra_descricao not in descricoes:
                                                        descricoes.append(pra_descricao)

                                            if len(acps) > 1:
                                                acps = self.check_acps(pra_nv[plt][dt][hr][gr], acps)

                                            descricao = self.monta_descricao(dt, descricoes, acps)
                                            # print(descricao)
                                            # DEFINE O TIPO DO ARQUIVO PARA LANÇAMENTO
                                            tipo_doc = "Outros"
                                            if len(acps) == 1:
                                                teste = ComparaOcorrencias()
                                                r = teste.execute(acps[0]['acp_tipo'],acps[0]['acp_esp'])
                                                if r:
                                                    if r['arquivo'] != '' and r['arquivo'] != '-':
                                                        tipo_doc = r['arquivo']
                                            else:
                                                achei_peticao = False
                                                for pra in pra_nv[plt][dt][hr][gr]:
                                                    achei_peticao = False
                                                    pra_descricao = remove_acentos(pra['pra_descricao'])
                                                    if find_string(pra_descricao, ('peticao',)):
                                                        achei_peticao = True

                                                if achei_peticao:
                                                    tipo_doc = "Petição"

                                            nao_lancados.append({'data_arquivo': dt, 'obs_arquivo': descricao, 'pra': pra_nv[plt][dt][hr][gr], 'drp': [], 'arquivo': [tipo_doc,]})

                        print(nao_lancados)
                        url = url_arquivos + '\\' + db + '\\' + proc['prc_estado'] + '\\' + str(proc['prc_id']) + '\\'
                        # REALIZA O PROCESSO DE CONFERENCIA E LANÇAMENTO DE ARQUIVOS
                        for pr in nao_lancados:
                            i_tr = self.confere_arquivo(pr, False, False, retorna_linha=True)
                            if i_tr:
                                print('Arquivo existente')
                                self.insere_arquivos_entrantes(i_tr, pr['pra'], url)
                                ProcessoArquivo.update_batch(self.conn[db], pr['pra'], {'pra_ocorrencia': 1, })
                                DiarioProcesso.update_batch(self.conn[db], pr['drp'], {'drp_upload': 1, })
                                continue

                            print('lançando imagem')
                            url_arquivo = url + str(pr['pra'][0]['pra_plt_id']) + '\\'
                            if not self.lanca_arquivo(pr, url_arquivo, raise_exception=False, renomeia_arquivo=True, zipa_bloqueado=True):
                                print('Erro no lançamento do arquivo')
                                ignorar_id.append(str(proc['prc_id']))
                                continue

                            if self.confere_arquivo(pr, False, False):
                                print('Arquivo existente')
                                ProcessoArquivo.update_batch(self.conn[db], pr['pra'], {'pra_ocorrencia': 1, })
                                DiarioProcesso.update_batch(self.conn[db], pr['drp'], {'drp_upload': 1, })
                                continue

                    print('finalizado')
                except MildException:
                    tb = traceback.format_exc()
                    if tb.find('Esp não localizada') > -1:
                        ignorar_id.append(str(proc['prc_id']))

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

    def files_to_ignore(self, pra, url):
        pra_arquivo = pra['pra_arquivo'].lower()
        ext = pra_arquivo.split(".")[-1]
        if ext in ('htm','html','mp3','mp4','wmv','wma','ogg','wav','webm','xhtml','asf','mov','mpeg','mpg','jpeg','p7s','p7z','m4a','jfif','3gp','opus','3gpp','m4v','odt','bmp'):
            return True

        try:
            size = os.path.getsize(url + str(pra['pra_plt_id']) + '\\' + pra['pra_arquivo'])
        except:
            raise FatalException('Arquivo nao localizado ' + url + str(pra['pra_plt_id']) + '\\' + pra['pra_arquivo'], self.uf, self.plataforma, self.prc_id)

        size = size / 1024 / 1024
        if size > 60:
           return True

        if size > 20:
            temp_folder = self.pasta_download + '\\rename\\' + str(pra['pra_prc_id']) + '\\'
            create_folder(temp_folder, None, False)
            os.system('rar a -ep "' + temp_folder + pra['pra_arquivo']+'.rar' + '" "' + url + str(pra['pra_plt_id']) + '\\' + pra['pra_arquivo'] + '"')
            size = os.path.getsize(temp_folder + pra['pra_arquivo'] + '.rar')
            if size <= 20:
                self.pra_bloqueado.append(pra['pra_id'])
            else:
                return True

        return False

    # CONFERE SE OS DADOS LANÇADOS NOS CAMPOS CONFEREM COM A BASE
    def tratar_dados(self, base, acps, lanca_imagem, area):
        dados_lanc = []

        return dados_lanc

    # CONFERE QUAL O TIPO DO ACOMPANHAMENTO
    def tipo_acp(self, esp):
        pass

    # MONTA A DESCRIÇÃO DO ARQUIVO
    def monta_descricao(self, dia, descricoes, acps):
        print(acps)
        print(descricoes)
        if len(acps) == 1:
            acp_tipo = acps[0]['acp_tipo'].split(' ', 1)[0] if acps[0]['acp_tipo'] is not None else ''
            acp_esp = acps[0]['acp_esp'].split(' ', 1)[0] if acps[0]['acp_esp'] is not None else ''
            for pp in (acp_tipo, acp_esp):
                pp = remove_acentos(pp)
                if find_string(pp, ('Peticao Inicial',)):
                    return dia + " - Petição Inicial e Documentos"

                if find_string(pp, ('distribuido', 'distribuicao',)):
                    return dia + " - Distribuição e Documentos"

        if len(acps) == 1:
            acp_tipo = acps[0]['acp_tipo'] + " - " if acps[0]['acp_tipo'] is not None else ''
            descricao = acp_tipo + dia + " - " + acps[0]['acp_esp']
            return self.limpa_descricao(descricao)

        try:
            descricoes = [int(i) for i in descricoes]
            descricoes.sort()
            descricao = dia + " - Evento " + str(descricoes[0])
            if len(descricoes) > 1:
                descricao += " a " + str(descricoes[-1])
        except:
            descricao = dia + " - " + " - ".join(descricoes)
            if len(descricao) > 150:
                descricao = dia + ' - ' + descricoes[0]
                if len(descricoes) > 1:
                    descricao += ' - ' + descricoes[-1]

        return self.limpa_descricao(descricao)

    def limpa_descricao(self, descricao):
        descricao = descricao.replace(r'\r', '').replace(r'\n', '')
        descricao = " ".join(descricao.split())
        return corta_string(descricao, 250)

    def check_acps(self, pras, acps):
        pra = pras[0]
        for p in pras:
            if p['pra_id_tj'] != pra['pra_id_tj'] and p['pra_descricao'] != pra['pra_descricao']:
                return acps
            pra = p

        pra_descricao = pra['pra_descricao']
        for acp in acps:
            if acp['acp_rec_id'] != pra['pra_rec_id']:
                continue

            acp_tipo = acp['acp_tipo'] if acp['acp_tipo'] is not None else ''

            if acp_tipo != '' and acp_tipo == pra_descricao:
                return [acp]

            if acp['acp_esp'] == pra_descricao:
                return [acp]

            if acp_tipo == pra['pra_id_tj']:
                return [acp]

        return acps

    # CONFERE SE A CÓPIA INTEGRAL FOI LANÇADA
    def confere_copia_integral(self):
        self.abre_aba_imagem()

        pags = 1
        footer = self.driver.find_element_by_xpath('//*[@id="fImagem:dtbImagem"]/tfoot/tr/td').text
        r = re.search("(\\d+)", footer, re.IGNORECASE | re.DOTALL)
        if r is not None:
            total = int(r.group(0))
            if total > 10:
                pags = total / 10
                pags = math.ceil(pags)
                self.driver.find_element_by_id('fImagem:scrollResultadoslast').click()

        # x = 0
        while pags > 0:
            # x += 1
            pags = pags - 1
            linhas = self.driver.find_elements_by_xpath('//*[@id="fImagem:dtbImagem"]/tbody/tr')

            for indice, tr in enumerate(linhas):
                i_tr = len(linhas) - indice
                img_obs = self.driver.find_element_by_xpath(
                    '//*[@id="fImagem:dtbImagem"]/tbody/tr[' + str(i_tr) + ']/td[3]').text

                if 'Cópia integral até o dia' in img_obs:
                    return [img_obs, str(i_tr)]

            if pags > 0:
                self.driver.find_element_by_id('fImagem:scrollResultadosidx' + str(pags)).click()

            # if x >= 3:
            #     return False

        return False


    # CONFERE SE A CÓPIA INTEGRAL FOI LANÇADA
    def insere_arquivos_entrantes(self, i_tr, pras, url):
        print('//*[@id="fImagem:dtbImagem"]/tbody/tr[' + str(i_tr) + ']/td[1]/input')
        aguarda_presenca_elemento(self.driver, '//*[@id="fImagem:dtbImagem"]/tbody/tr[' + str(i_tr) + ']/td[1]/input')
        self.driver.find_element_by_xpath('//*[@id="fImagem:dtbImagem"]/tbody/tr[' + str(i_tr) + ']/td[1]/input').click()
        trs_arquivos = self.driver.find_elements_by_xpath('//*[@id="fDetalhar:body:dtTable:tbody_element"]/tr/td[1]/a')
        len_tr_arquivos = len(trs_arquivos)
        nomes = []
        for tr in trs_arquivos:
            nomes.append(tr.text.upper().replace('  ',' '))

        temp_folder = self.pasta_download + '\\rename\\' + str(pras[0]['pra_prc_id']) + '\\'
        btn_inserir = self.driver.find_element_by_id('fDetalhar:body:lblInserir')
        if not btn_inserir:
            quant = 0
            for pra in pras:
                pra_data = pra['pra_data'].strftime('%Y-%m-%d')
                pra_descricao = corta_string(pra['pra_descricao'], 30, corta_se_branco=True)
                pra_descricao = ''.join(e for e in pra_descricao if e.isalnum() or e in ('-', ',', ' '))
                novo_nome_arquivo = pra_data + ' - ' + pra['pra_id_tj'] + ' - ' + pra_descricao + ' - ' + pra['pra_arquivo'][-12:].lower()
                if novo_nome_arquivo.upper().replace('  ', ' ') in nomes:
                    continue

                ponto = novo_nome_arquivo.rfind('.')
                novo_nome_arquivo = novo_nome_arquivo[:ponto] + '.ZIP'
                if novo_nome_arquivo.upper().replace('  ', ' ') in nomes:
                    continue

                quant += 1
                break

            if quant == 0:
                return True
            else:
                return False

        btn_inserir.click()
        self.abre_e_aguarda_modal()
        self.driver.find_element_by_xpath('//*[@id="tipoUpload"]/tbody/tr/td[2]/label/input').click()
        aguarda_presenca_elemento(self.driver, 'formProtocolo:anexo', tipo='ID', aguarda_visibilidade=True)

        prev_trs_arq = 0
        trs_arq = 0
        create_folder(temp_folder, None, False)

        quant = 0
        for pra in pras:
            file_upload = self.driver.find_element_by_id('formProtocolo:anexo')
            pra_data = pra['pra_data'].strftime('%Y-%m-%d')
            pra_descricao = corta_string(pra['pra_descricao'],30, corta_se_branco=True)
            pra_descricao = ''.join(e for e in pra_descricao if e.isalnum() or e in ('-', ',', ' '))
            novo_nome_arquivo = pra_data + ' - ' + pra['pra_id_tj'] + ' - ' + pra_descricao + ' - ' + pra['pra_arquivo'][-12:].lower()
            dest = temp_folder + novo_nome_arquivo
            if novo_nome_arquivo.upper().replace('  ',' ') in nomes:
                continue

            ponto = novo_nome_arquivo.rfind('.')
            novo_nome_arquivo = novo_nome_arquivo[:ponto] + '.ZIP'
            if novo_nome_arquivo.upper().replace('  ', ' ') in nomes:
                continue

            zip = False
            if pra['pra_id'] in self.pra_bloqueado:
                ponto = pra['pra_arquivo'].rfind('.')
                novo_nome = pra['pra_arquivo'][:ponto] if ponto > -1 else pra['pra_arquivo']
                novo_nome = temp_folder + novo_nome + '.rar'
                os.system('rar a -ep "' + novo_nome + '" "' + url + str(pra['pra_plt_id']) + '\\' + pra['pra_arquivo'] + '"')
                pra['pra_arquivo'] = novo_nome
                zip = True

            quant += 1
            try:
                if zip:
                    ponto = dest.rfind('.')
                    dest = dest[:ponto] + '.zip'
                    shutil.copyfile(pra['pra_arquivo'], dest)
                else:
                    shutil.copyfile(url + str(pra['pra_plt_id']) + '\\' + pra['pra_arquivo'], dest)
            except:
                self.fecha_modal(salvar=False)
                return False

            try:
                file_upload.send_keys(dest)
                self.driver.find_element_by_xpath('//*[@id="formProtocolo"]/table[1]/tbody/tr[2]/td/table/tbody/tr/td[2]/a').click()
            except:
                self.fecha_modal(salvar=False)
                return False

            block_error = self.driver.find_element_by_xpath('//*[@id="cf-error-details"]/div[1]/h1')
            if block_error:
                if block_error.text.find('Sorry, you have been blocked') > -1:
                    self.pra_bloqueado.append(pra['pra_id'])
                    raise MildException("Arquivo Bloqueado " + str(pra['pra_id']), self.uf, self.plataforma, self.prc_id)

            inicio = time.time()
            while prev_trs_arq == trs_arq:
                tempoTotal = time.time() - inicio
                if tempoTotal >= 60:
                    raise MildException("Timeout ao carregar arquivos", self.uf, self.plataforma, self.prc_id)
                trs_arq = len(self.driver.find_elements_by_xpath('//*[@id="formProtocolo:dtbAnexos:tbody_element"]/tr'))

            prev_trs_arq = trs_arq

        shutil.rmtree(temp_folder)

        if quant == 0:
            self.driver.find_element_by_id('formProtocolo:fechar').click()
        else:
            self.driver.find_element_by_xpath('//*[@id="actions"]/tbody/tr/td[1]/input').click()
            novo_len_tr_arquivos = len_tr_arquivos
            while len_tr_arquivos == novo_len_tr_arquivos:
                novo_len_tr_arquivos = len(self.driver.find_elements_by_xpath('//*[@id="fDetalhar:body:dtTable:tbody_element"]/tr/td[1]/a'))

        return True
