from Controllers.Tribunais.Projudi._projudi import *
from Config.helpers import *
import urllib.request


# CLASSE DA VARREDURA DO PROJUDI DE GO. HERDA OS METODOS DA CLASSE PROJUDI
class GO(Projudi):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://projudi.tjgo.jus.br"
        self.pagina_busca = "https://projudi.tjgo.jus.br/BuscaProcessoUsuarioExterno?PaginaAtual=2&Proprios=0"
        self.pagina_processo = "https://projudi.tjgo.jus.br/BuscaProcessoUsuarioExterno?PaginaAtual=-1&PassoBusca=2&Id_Processo="
        self.tabela_movs = '//*[@id="tabListaProcesso"]/tr'
        self.captura_movs_download = True
        self.posicao_elementos = {'tipo': 1, 'esp': 2, 'data': 3, 'usr': 4}
        self.formato_data = '%d/%m/%Y %H:%M:%S'
        self.capturar_todas_movs = True

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        if usuario is None:
            self.driver.find_element_by_xpath('//*[@id="formLoginCertificado"]/div/input').click()
        else:
            self.driver.find_element_by_id("login").send_keys(usuario)
            self.driver.find_element_by_id("senha").send_keys(senha)
            self.driver.find_element_by_id("senha").send_keys(Keys.ENTER)

        try_click(self.driver, '//*[@id="divCorpo"]/fieldset[1]/label/a')

        if not aguarda_presenca_elemento(self.driver, 'Cabecalho', tipo='ID'):
            return False

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        ano = numero_busca[-11:-7]
        seq = numero_busca[0:-13]
        verif = numero_busca[-13:-11]

        if len(seq.strip('0')) < 2 and (int(ano) < 1900 or int(ano) > 2100):
            return False

        prc_numero = seq+'.'+verif

        try:
            self.driver.find_element_by_id('ProcessoNumero').clear()
        except:
            raise CriticalException("Campo de busca não localizado", self.uf, self.plataforma, self.prc_id, False)

        self.driver.find_element_by_id('ProcessoNumero').send_keys(prc_numero)
        self.driver.find_element_by_xpath('//*[@id="divEditar"]/fieldset/fieldset/label[1]/input[4]').click()
        self.driver.find_element_by_xpath('//*[@id="divBotoesCentralizados"]/input[1]').click()

        if self.driver.find_element_by_xpath('//*[@id="divEditar"]/div/span[1]'):
            return True

        if try_click(self.driver, '/html/body/div[2]/div[3]/div/button'):
            return False

        els = self.driver.find_elements_by_xpath('//*[@id="tabListaProcesso"]/tr')
        if len(els) == 1:
            if not try_click(self.driver, '//*[@id="tabListaProcesso"]/tr/td[7]/input'):
                self.driver.find_element_by_xpath('//*[@id="tabListaProcesso"]/tr/td[6]/input').click()

            # self.driver.find_element_by_xpath('//*[@id="tabListaProcesso"]/tr/td[7]/input').click()
            return True
        else:
            for el in els:
                td5 = el.find_elements_by_xpath('td[5]')
                if len(td5) == 0:
                    continue

                td5 = td5[0].text

                td6 = el.find_element_by_xpath('td[6]').text
                ano_td5 = td5[6:].strip()
                ano_td6 = td6[6:].strip()
                if ano_td5 == ano or ano_td6 == ano:
                    try:
                        el.find_element_by_xpath('td[7]/input').click()
                    except:
                        el.find_element_by_xpath('td[6]/input').click()

                    return True

        return False

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        el = self.driver.find_element_by_xpath('//*[@id="divCorpo"]/div/h2')
        if el:
            if el.text.find('Segredo de Justiça') > -1:
                return True

        self.confere_cnj(numero_busca)

        return False

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        el = self.driver.find_element_by_xpath('//*[@id="divCorpo"]/div/h2')
        cnj = ''
        if el:
            if el.text.find('Segredo de Justiça') > -1:
                cnj = self.driver.find_element_by_xpath('//*[@id="divEditar"]/div/span[1]').text

        if cnj == '':
            span_proc_numero = self.driver.find_element_by_id('span_proc_numero')
            if not span_proc_numero:
                raise MildException("Erro ao capturar CNJ", self.uf, self.plataforma, self.prc_id)
            cnj = span_proc_numero.text

        cnj_limpo = ajusta_numero(cnj)
        if cnj_limpo != numero_busca:
            raise MildException("Número CNJ Diferente "+cnj_limpo+" "+numero_busca, self.uf, self.plataforma, self.prc_id)

    # CONFERE SE A SESSÃO DO USUÁRIO EXPIROU
    def erro_sessao(self):
        el = self.driver.find_element_by_xpath('/html/body/div/div[2]')
        if el:

            if find_string(el.text,('Usuário inválido','sessão foi invalidada',)):
                raise CriticalException("Sessão Encerrada", self.uf, self.plataforma, self.prc_id)

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []
        self.driver.get('https://projudi.tjgo.jus.br/BuscaProcessoUsuarioExterno?PaginaAtual=1')
        self.erro_sessao()
        lgs = self.driver.find_elements_by_xpath('//*[@id="Formulario"]/fieldset/fieldset/legend')
        i = 0
        for lg in lgs:
            i += 1
            if lg.text.upper().find('AUDIÊNCIAS') > -1:
                break

        audiencias = self.driver.find_elements_by_xpath('//*[@id="Formulario"]/fieldset/fieldset['+str(i)+']/table/tbody/tr')
        for adc in audiencias:
            td5 = adc.find_elements_by_xpath('td[5]')
            if len(td5) == 0:
                continue
            dia = adc.find_element_by_xpath('td[3]').text
            tipo = adc.find_element_by_xpath('td[1]').text
            if len(tipo) > 100:
                prp_tipo = ''
                for d in dados_audiencia['tipo']:
                    if tipo.upper().find(d.upper()) > -1:
                        prp_tipo = d
            else:
                prp_tipo = tipo

            if prp_tipo == '':
                # prp_tipo = 'Audiência'
                raise MildException("Audiência - tipo não localizado: "+tipo, self.uf, self.plataforma, self.prc_id)

            status = adc.find_element_by_xpath('td[5]').text
            serventia = adc.find_element_by_xpath('td[4]').text
            data_tj = datetime.strptime(dia, self.formato_data)

            adcs.append({'data_mov': data_tj, 'prp_data': data_tj, 'prp_status':status, 'prp_tipo':prp_tipo, 'prp_serventia': serventia})

        self.driver.find_element_by_xpath('//*[@id="VisualizaDados"]/span/a').click()

        return adcs

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': []}
        nomes = []
        els = self.driver.find_elements_by_xpath('/html/body/div/form/div[1]/fieldset/fieldset/fieldset')

        for el in els:
            leg = el.find_elements_by_tag_name('legend')
            if len(leg) == 0:
                continue

            legend = leg[0].text
            polo = ''
            if legend.find('ATIVO') > -1:
                polo = 'ativo'
            if legend.find('PASSIVO') > -1:
                polo = 'passivo'

            if polo == '':
                continue
            fieldset = el.find_elements_by_tag_name('fieldset')

            for fs in fieldset:
                nomes = fs.find_elements_by_xpath('span[1]')
                if len(nomes) == 0:
                    continue

                prt_nome = nomes[0].text
                prt_cpf_cnpj = 'Não Informado'
                spans = fs.find_elements_by_tag_name('span')
                for s in spans:
                    cpf = s.text
                    cl = s.get_attribute('class')
                    if cl.find('span2') > -1 and cpf.find('-') > -1 and cpf.find('.') > -1:
                        prt_cpf_cnpj = cpf
                        break

                partes[polo].append({'prt_nome': prt_nome.strip(), 'prt_cpf_cnpj': prt_cpf_cnpj})

        if len(partes['ativo']) == 0 or len(partes['passivo']) == 0:
            raise MildException("Parte não localizada", self.uf, self.plataforma, self.prc_id)
        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []
        self.driver.get('https://projudi.tjgo.jus.br/BuscaProcessoUsuarioExterno?PaginaAtual=-4')
        self.erro_sessao()

        # CAPTURA DADOS DO JUIZ
        els = self.driver.find_elements_by_xpath('//*[@id="Responsaveis"]/tbody/tr')
        for el in els:
            cargo = el.find_elements_by_xpath('td[2]')
            if len(cargo) == 0:
                continue
            cargo = cargo[0].text
            if cargo == 'Juiz' or cargo == 'Relator':
                nome = el.find_element_by_xpath('td[3]').text.strip()
                if nome != '':
                    resps.append({'prr_nome': nome.strip(), 'prr_oab': '', 'prr_cargo': 'Juiz', 'prr_parte': ''})
                break

        # CAPTURA DADOS DOS ADVOGADOS
        els = self.driver.find_elements_by_xpath('//*[@id="tabListaAdvogadoParte"]/tr')
        for el in els:
            nome = el.find_elements_by_xpath('td')
            if len(nome) == 0:
                continue
            prr_nome = nome[0].text
            prr_oab = nome[1].text
            # prr_oab = el.find_element_by_xpath('td[2]').text
            polo = nome[-1].text
            # polo = el.find_element_by_xpath('td[7]').text
            prr_parte = ''
            if find_string(polo,self.titulo_partes['ignorar']):
                continue

            if find_string(polo,self.titulo_partes['terceiro']):
                continue

            if find_string(polo,('credor',)):
                continue

            if polo.upper().find('ATIVO') > -1:
                prr_parte = 'Polo Ativo'
            if polo.upper().find('PASSIVO') > -1 or polo.upper().find('JURÍDICO TELEFÔNICA') > -1 or polo.upper().find('ITAPEVA') > -1:
                prr_parte = 'Polo Passivo'
            if prr_parte == '':
                raise MildException("Parte Adv não localizada - "+polo, self.uf, self.plataforma, self.prc_id)

            resps.append({'prr_nome': prr_nome, 'prr_oab': prr_oab, 'prr_cargo': 'Advogado', 'prr_parte': prr_parte})

        return resps

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}
        self.driver.find_element_by_xpath('//*[@id="VisualizaDados"]/span/a').click()

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)

        # LOCALIZA NÚMERO DO PROCESSO
        el = self.driver.find_element_by_xpath('//*[@id="divCorpo"]/div/h2')
        cnj = ''
        if el:
            if el.text.find('Segredo de Justiça') > -1:
                cnj = self.driver.find_element_by_xpath('//*[@id="divEditar"]/div/span[1]').text

        if cnj == '':
            cnj = self.driver.find_element_by_id('span_proc_numero').text

        prc['prc_numero2'] = cnj

        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        prc['prc_codigo'] = url_params['Id_Processo'][0]

        fieldset = self.driver.find_elements_by_tag_name('fieldset')
        achei = False
        for fs in fieldset:
            leg = fs.find_elements_by_xpath('legend')
            if len(leg) == 0:
                continue
            legend = leg[0].text
            if legend.upper().find('OUTRAS INFORMA') > -1:
                divs = fs.find_elements_by_xpath('div')
                i = 0
                for div in divs:
                    i += 1
                    titulo = div.text.strip()
                    if titulo == 'Classe':
                        cls = fs.find_element_by_xpath('span[' + str(i) + ']').text
                        if cls.upper().find('RECURSO') == -1:
                            achei = True
                            break

                    if titulo == 'Processo Originário':
                        a = fs.find_element_by_xpath('span[' + str(i) + ']/a')
                        if a.text.strip() != '':
                            a.click()
                        achei = True
                        break

            if achei:
                break

        campos = {'Serventia': 'prc_serventia', 'Classe': 'prc_classe', 'Valor da Causa': 'prc_valor_causa', 'Valor Condenação': 'prc_valor_condenacao', 'Processo Originário': 'prc_proc_origem',
                  'Fase Processual': 'prc_fase', 'Segredo de Justiça': 'prc_segredo', 'Penhora no Rosto': 'prc_penhora_rosto', 'Efeito Suspensivo': 'prc_suspensivo','Custa': 'prc_custa',
                  'Prioridade': 'prc_prioridade', 'Assunto': 'prc_assunto', 'Dt. Distribuição': 'prc_distribuicao', 'Dt. Trânsito em Julgado': 'prc_data_transito'}

        fieldset = self.driver.find_elements_by_tag_name('fieldset')
        for fs in fieldset:
            leg = fs.find_elements_by_xpath('legend')
            if len(leg) == 0:
                continue
            legend = leg[0].text
            if legend.upper().find('OUTRAS INFORMA') > -1:
                divs = fs.find_elements_by_xpath('div')
                i = 0
                for div in divs:
                    i += 1
                    titulo = div.text.strip()
                    if titulo == '':
                        continue
                    for c in campos:
                        if titulo.upper().find(c.upper()) > -1:
                            if campos[c] == 'prc_assunto':
                                prc['prc_assunto'] = ''
                                tds = fs.find_elements_by_xpath('span['+str(i)+']/table/tbody/tr/td')
                                for td in tds:
                                    prc['prc_assunto'] += td.text
                            else:
                                prc[campos[c]] = fs.find_element_by_xpath('span['+str(i)+']').text
                            break

        # p = prc['prc_serventia'].find(' - ') > -1
        # comarca = prc['prc_serventia'][p+3:] if p == -1 else prc['prc_serventia']
        prc['prc_comarca2'] = localiza_comarca(prc['prc_serventia'], self.uf)

        if 'prc_segredo' in prc:
            prc['prc_segredo'] = True if prc['prc_segredo'].find('Sim') > -1 else False

        if 'prc_penhora_rosto' in prc:
            prc['prc_penhora_rosto'] = True if prc['prc_penhora_rosto'].find('Sim') > -1 else False

        if 'prc_suspensivo' in prc:
            prc['prc_suspensivo'] = True if prc['prc_suspensivo'].find('Sim') > -1 else False

        if 'prc_prioridade' in prc:
            prc['prc_prioridade'] = False if prc['prc_prioridade'].find('Normal') > -1 else True

        if 'prc_data_transito' in prc:
            r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)', prc['prc_data_transito'])
            if r:
                prc_data_transito = r.group(0)
                prc['prc_data_transito'] = datetime.strptime(prc_data_transito, '%d/%m/%Y')
            else:
                del prc['prc_data_transito']

        if 'prc_distribuicao' in prc:
            r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)', prc['prc_distribuicao'])
            prc_distribuicao = r.group(0)
            prc['prc_distribuicao'] = datetime.strptime(prc_distribuicao, '%d/%m/%Y')

        return prc

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, target_dir):
        arquivos = []
        self.driver.get('https://projudi.tjgo.jus.br/DescartarPendenciaProcesso?PaginaAtual=8')
        aguarda_presenca_elemento(self.driver, '/html/body/div[5]/div[3]/div/button', aguarda_visibilidade=True, tempo=2)
        try_click(self.driver, '/html/body/div[5]/div[3]/div/button')
        err = self.driver.find_element_by_xpath('/html/body/div/div[2]')
        if err:
            if err.text.upper().find('SEGREDO DE JUSTIÇA') > -1:
                return arquivos

        err = self.driver.find_element_by_class_name('texto_erro')
        if err:
            if err.text.upper().find('USUÁRIO TEM QUE ESPERAR') > -1:
                self.driver.execute_script("window.history.go(-1)")

        self.erro_sessao()
        aguarda_presenca_elemento(self.driver, 'ui-id-2', tipo='ID', aguarda_visibilidade=True)
        # self.driver.find_element_by_xpath('//*[@id="ui-id-2"]/span').click()
        self.driver.execute_script('document.getElementById("ui-id-2").click();')

        if not aguarda_presenca_elemento(self.driver, '//*[@id="dadosIndice"]/ul/ul', aguarda_visibilidade=True):

            id4 = self.driver.find_element_by_id('ui-id-4')
            if id4:
                if id4.text.upper().find('PROJUDI - ERRO') > -1:
                    return []
            raise MildException("Erro ao abrir índice", self.uf, self.plataforma, self.prc_id, False)

        movimentos = self.driver.find_elements_by_xpath('//*[@id="dadosIndice"]/ul/ul')
        movimentos.reverse()

        if len(movimentos) == 0:
            raise MildException("Erro ao carregar lista de documentos", self.uf, self.plataforma, self.prc_id, False)
        existe = False
        i = 0
        for mov in movimentos:
            i += 1
            if existe and len(pendentes) == 0:
                break

            pra_id_tj = mov.find_element_by_xpath('li/b').text
            pra_descricao = ''
            for m in self.movs:
                if m['acp_tipo'] == pra_id_tj:
                    pra_data = m['acp_cadastro']
                    pra_descricao = m['acp_esp']
                    break

            if pra_descricao == '':
                continue
                # raise MildException("Erro ao vincular tabelas - "+pra_id_tj, self.uf, self.plataforma, self.prc_id)

            uls = mov.find_elements_by_xpath('li/ul/li/a')
            for ul in uls:
                arq = {}
                arq['pra_id_tj'] = pra_id_tj
                arq['pra_prc_id'] = prc_id
                arq['pra_grau'] = self.grau
                arq['pra_plt_id'] = self.plataforma
                arq['pra_descricao'] = pra_descricao
                arq['pra_data'] = pra_data
                arq['pra_erro'] = True
                arq['pra_excluido'] = False
                arq['pra_tentativas'] = None
                arq['pra_original'] = self.cut_backwards(ul.text.strip(),99)

                limpar_pasta(self.pasta_download)

                if len(pendentes) > 0:
                    for pen in pendentes[:]:
                        pen_original = self.cut_backwards(pen['pra_original'],99)
                        if pen['pra_id_tj'] == arq['pra_id_tj'] and pen_original == arq['pra_original']:
                            arq['pra_id'] = pen['pra_id']
                            arq['pra_tentativas'] = pen['pra_tentativas']
                            pendentes.remove(pen)

                if 'pra_id' not in arq:
                    for arb in arquivos_base:
                        if arq['pra_id_tj'] == arb['pra_id_tj'] and arq['pra_original'] == arb['pra_original']:
                            existe = True
                            break

                    if existe:
                        if len(pendentes) == 0:
                            break
                        continue

                if self.tipo != 2:
                    if find_string(arq['pra_original'], ('.mp4','.mp3','.m4a')):
                        ul.click()
                        self.alterna_janela(1, 1)
                        video = self.driver.find_element_by_xpath('/html/body/video/source')
                        video_url = video.get_property('src')
                        urllib.request.urlretrieve(video_url, self.pasta_download + '\\' + arq['pra_original'])
                    else:
                        if find_string(arq['pra_original'],('.webm', '.wmv', '.wav', '.ogg', '.mp3','.m4a')):
                            self.driver.execute_script("arguments[0].setAttribute('download', 'True')", ul)

                        ul.click()
                        if arq['pra_original'].upper().endswith('.HTML') or arq['pra_original'].upper().endswith('.HTML.P7Z'):
                            self.alterna_janela(1, 1)
                            self.driver.execute_script('setTimeout(function() { window.print(); }, 0);')

                    arq['pra_erro'] = False if aguarda_download(self.pasta_download, 1) else True
                    if len(self.driver.window_handles) > 1:
                        if arq['pra_erro']:
                            self.alterna_janela(1, 1)
                            err = self.driver.find_element_by_xpath('/html/body/div/div[2]')
                            if err:
                                if err.text.upper().find('ARQUIVO CORROMPIDO') > -1:
                                    arq['pra_erro'] = False
                                    arq['pra_excluido'] = True
                                    arq['pra_arquivo'] = None

                            err = self.driver.find_element_by_xpath('/html/body/h1')
                            if err:
                                if err.text.upper().find('NOT FOUND') > -1:
                                    arq['pra_erro'] = False
                                    arq['pra_excluido'] = True
                                    arq['pra_arquivo'] = None

                            err = self.driver.find_element_by_class_name('texto_erro')
                            if err:
                                if err.text.upper().find('MALFORMED') > -1:
                                    arq['pra_erro'] = False
                                    arq['pra_excluido'] = True
                                    arq['pra_arquivo'] = None



                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        self.driver.close()
                        self.alterna_janela(0, 2)

                    if not arq['pra_excluido']:
                        if not arq['pra_erro']:
                            file_names = os.listdir(self.pasta_download)
                            # arq['pra_original'] = file_names[0]
                            pra_arquivo = trata_arquivo(file_names[0], self.pasta_download, target_dir)
                            arq['pra_arquivo'] = pra_arquivo
                        elif arq['pra_erro'] and self.tipo != 2:
                            # arq['pra_original'] = None
                            arq['pra_tentativas'] = 1 if arq['pra_tentativas'] is None else arq['pra_tentativas']+1
                            arq['pra_arquivo'] = None
                            print('erro download ' + arq['pra_id_tj'])
                            # time.sleep(9999)
                            # raise MildException('erro download ' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                arq['pra_data_insert'] = datetime.now()
                arquivos.append(arq)

        arquivos.reverse()
        return arquivos

    def cut_backwards(self, texto, tamanho):
        texto = texto.replace('-', '').replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace(',', '')
        texto = texto.replace('  ', ' ').replace(' ', '_')
        texto = texto[::-1]
        texto = texto[:tamanho]
        return texto[::-1].lower()
