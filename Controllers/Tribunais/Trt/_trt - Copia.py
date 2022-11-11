from re import split
from Config.helpers import *
from Controllers.Tribunais.primeiro_grau import *
from selenium.webdriver.common.keys import *
from Models.processoModel import *
import sys, time, shutil
import datetime
import urllib.parse as urlparse
from urllib.parse import parse_qs
import win32gui
import win32con
import win32api
import win32com.client

# CLASSE DA VARREDURA DO ESAJ. HERDA OS METODOS DA CLASSE PLATAFORMA
class Trt(PrimeiroGrau):

    def __init__(self):
        super().__init__()
        self.plataforma = 2
        self.div = None
        self.movs = []

        # ASSETS TRT
        self._consultas = False

        # self.num_pag_atual = 0
        self.cont_existe_base = 0

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        prt = self.partes()
        adv = self.responsaveis()
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        prc = self.dados(status_atual)

        return adc, prt, prc, adv

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        self.driver.get(self.pagina_inicial)

        if usuario == None:
            self.muda_para_certificado()
            # self.mudar_para_login_PjeOficce()
            # time.sleep(2)
            self.faz_login_com_certificado()
            # time.sleep(10)
        else:
            # print("LOGIN COM USUARIO E SENHA...")
            self.faz_login_usuario_e_senha(usuario, senha)

        if not aguarda_presenca_elemento(self.driver, 'pje-cabecalho-perfil', tempo=60, tipo='TAG_NAME'):
            return False

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        # ESTÁ ATUALIZANDO A PAGINA PARA CADA BUSCA, PARA EVITAR ERROS
        # self.driver.refresh()
        # print('BUSCA')
        time.sleep(1)
        self.clica_para_liberar_campo_processo()

        try:
            self.insere_numero_processo(numero_busca)
        except:
            raise MildException("Erro ao imputar numero", self.uf, self.plataforma, self.prc_id, False)

        # CLICA NO BOTÃO DE CONSULTA
        aguarda_presenca_elemento(self.driver, 'consultaProcessoAdvogadoForm:searchButon', tipo='ID')
        self.driver.find_element_by_id('consultaProcessoAdvogadoForm:searchButon').click()
        self.espera_barrinha_azul()

        quantidade_de_resultados = self.verifica_quantidade_resultados()

        # ENCONTROU UM OU MAIS PROCESSOS
        if quantidade_de_resultados > 0:
            # ENCONTROU VARIOS OU O NUMERO DO PROCESSO É '0'
            if quantidade_de_resultados > 1:
                if numero_busca == '0':
                    # print("ACHOU O NUMERO DE PROCESSO QUE É IGUAL A 0!")
                    return False

                # print("MAIS DE UM RESULTADO ENCONTRADO!")
                # print("O NUMERO DE PROCESSO QUE OCASIONOU ISSO FOI: {}".format(numero_busca))
                return False
            # print("BUSCA FINALIZADA!")
            return True

        # print("PROCESSO NÃO ENCONTRADO!")
        return False

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        # print('CNJ')
        xpath = '/html/body/div[5]/div/div/div[2]/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/div/div[2]/div/div[2]/div[2]/table/tbody/tr/td[2]/div/div/a/span'
        aguarda_presenca_elemento(self.driver, xpath)
        element = self.driver.find_element_by_xpath(xpath)

        if element:
            el = element.text.split(' ')[1]
            numero_site = ajusta_numero(el)
            if numero_busca == numero_site:
                self.clica_no_resultado()
                return True

        raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)

    def clica_no_resultado(self):
        element = self.driver.find_element_by_xpath('/html/body/div[5]/div/div/div[2]/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/div/div[2]/div/div[2]/div[2]/table/tbody/tr/td[2]/div/div/a/span')
        element.click()
        self.alterna_janela()
        self.driver.execute_script("window.scrollTo(0,0)")

        self.espera_barrinha_azul()
        header = self.driver.find_element_by_xpath('/html/body/div[5]/div/form/div[1]/span[1]')
        if header:
            if 'Unhandled or Wrapper Exception' in header.text:
                raise MildException("Erro ao abrir processo", self.uf, self.plataforma, self.prc_id)

        # CLICA NA ABA DE MOVIMENTAÇÕES
        aguarda_presenca_elemento(self.driver, 'MovimentacoesId_lbl', tipo='ID')
        self.driver.find_element_by_id('MovimentacoesId_lbl').click()

        self.espera_barrinha_azul()

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        self.confere_cnj(numero_busca)

        return False

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self, ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        xpath_element = '//*[@id="movimentacaoList:tb"]/tr[1]/td[3]'

        if not aguarda_presenca_elemento(self.driver, xpath_element, tempo=10):
            raise MildException("Erro ao capturar a data", self.uf, self.plataforma, self.prc_id)

        td3 = self.driver.find_element_by_xpath(xpath_element)
        mov_text = td3.text.split(' - ')
        data_tj = datetime.datetime.strptime(mov_text[0], '%d/%m/%Y %H:%M:%S')

        if ultima_data == data_tj:
            return True

        return False

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        # print('COLETA DE MOVIMENTAÇÕES INICIADA!')
        ultima_mov = proc_data['cadastro']
        self.movs = []
        movs = []

        # APAGAR APOS PRIMEIRA VARREDURA
        # prc_id = proc_data['prc_id']
        # Acompanhamento.delete_acp(base, prc_id=prc_id, acp_plataforma=2)
        # ultima_mov = None

        break_while = False
        total_pags = self.driver.find_element_by_class_name('rich-inslider-right-num')
        total_pags = int(total_pags.text) if total_pags else 1
        pag = 0
        capturar = True
        p_mov = ''
        pmov_novo = ''
        i = 0
        while pag < total_pags:
            self.espera_barrinha_azul()
            inicio = time.time()
            inslider = False
            while p_mov == pmov_novo:
                if (time.time() - inicio) >= 40:
                    raise MildException('Erro ao carregar página de movs.', self.uf, self.plataforma, self.prc_id)
                if not inslider and (time.time() - inicio) >= 20:
                    inslider = True
                    # PASSA PARA A PROXIMA PAGINA E CONTINUA VERIFICANDO
                    self.driver.find_element_by_class_name('rich-inslider-dec-horizontal').click()
                    time.sleep(3)
                    self.driver.find_element_by_class_name('rich-inslider-inc-horizontal').click()


                header = self.driver.find_element_by_xpath('/html/body/div[5]/div/form/div[1]/span[1]')
                if header:
                    if 'Unhandled or Wrapper Exception' in header.text and pag == 0:
                        raise MildException("Erro ao abrir processo", self.uf, self.plataforma, self.prc_id)
                    else:
                        break_while = True
                        self.fecha_processo()
                        self.clica_no_resultado()
                        break
                try:
                    pmov_novo = self.driver.find_element_by_xpath('//*[@id="movimentacaoList:tb"]/tr/td[3]').text
                except:
                    pass

            if break_while:
                break
            p_mov = pmov_novo

            # COLETA AS MOVIMENTAÇÕES DA PAGINA ATUAL
            movimentos = self.driver.find_elements_by_xpath('//*[@id="movimentacaoList:tb"]/tr')

            if len(movimentos) == 0:
                raise MildException("Erro ao capturar movimentações", self.uf, self.plataforma, self.prc_id, False)

            # VERIFICA SE AS MOVIMENTAÇÕES DESSA PAGINA JÁ FORAM CAPTURADAS
            for mov in movimentos:
                # if not mov:
                #     break
                i += 1
                mov_aux = mov

                mov_text = mov_aux.find_element_by_xpath('td[3]').text.split(' - ')
                acp_cadastro = datetime.datetime.strptime(mov_text[0], '%d/%m/%Y %H:%M:%S')
                acp_tipo = mov.find_element_by_xpath('td[2]').text
                acp_esp = mov_text[1]
                acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': acp_tipo}

                if acp_cadastro == ultima_mov:
                    capturar = False

                if not capturar and not completo and i >= 10:
                    break_while = True
                    break

                if capturar:
                    movs.append(acp)

                self.movs.append({**acp, 'novo': capturar})

            if break_while:
                break

            pag += 1
            try:
                # PASSA PARA A PROXIMA PAGINA E CONTINUA VERIFICANDO

                # fld = self.driver.find_element_by_class_name('rich-inslider-field')

                btn = self.driver.find_element_by_class_name('rich-inslider-inc-horizontal')
                btn.click()

            except:
                pass
        # print('COLETA DE MOVIMENTAÇÕES FINALIZADA!')
        return movs

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        lista_audiencias = []
        # print("SUBINDO A JANELA PARA CLICAR NA ABA DE AUDIENCIAS")
        self.driver.execute_script("window.scrollTo(0,0)")

        # CLICA NA ABA DE AUDIENCIAS, PARA COLETAR AUDIENCIAS
        # print("CLICA NA ABA DE COLETA DE AUDIENCIAS!")
        self.driver.find_element_by_id('tabProcessoAudiencia_lbl').click()
        aguarda_presenca_elemento(self.driver, 'processoConsultaAudienciaGridList', tipo='ID',aguarda_visibilidade=True)


        quantidade_paginas = self.coleta_quantidade_paginas_aba_audiencias()
        # PERCORRE TODAS AS PAGINAS
        for i in range(quantidade_paginas):
            # COLETA LINHAS COM AS AUDIENCIAS DA PAGINA ATUAL
            xpath = '/html/body/div[3]/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td/div/div/div[2]/span/div/div/table/tbody/tr'
            webelements_audiencias = self.driver.find_elements_by_xpath(xpath)

            # PERCORRE TODAS AUDIENCIAS, E SEPARA AS INFORMAÇÕES
            for webelement_linha in webelements_audiencias:
                # SEPARA AS INFORMAÇÕES EM UMA LISTA
                date_full = webelement_linha.find_element_by_xpath('td[1]').text

                prp_data = datetime.datetime.strptime(date_full, '%d/%m/%Y %H:%M')

                prp_status = webelement_linha.find_element_by_xpath('td[5]').text

                prp_tipo = webelement_linha.find_element_by_xpath('td[2]').text

                data_mov = prp_data.time()

                # ARMAZENA TODAS AUDIENCIAS ENCONTRADAS PARA ESSE PROCESSO NESSA LISTA
                lista_audiencias.append( {'prp_data': prp_data, 'prp_status': prp_status, 'prp_tipo': prp_tipo, 'data_mov': data_mov } )

            if quantidade_paginas > 1:
                self.passa_pagina_audiencia()
                self.espera_barrinha_azul()

        return lista_audiencias

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        # partes = {'ativo': [], 'passivo': [], 'terceiro':[]}
        # print('COLETANDO AS PARTES')

        # CLICA NA ABA DE AUDIENCIAS, PARA COLETAR AUDIENCIAS
        self.driver.find_element_by_id('informativoProcessoTrf_lbl').click()

        aguarda_presenca_elemento(self.driver, 'toggleDocumentos_header_label', tipo='ID')

        # PEGA OS DADOS DA TABELA POLO ATIVO
        tabela_parte_ativa = self.driver.find_element_by_id('listaPoloAtivo')
        tabela_parte_ativa = tabela_parte_ativa.text.split("\n")
        # print("SEPARANDO OS DADOS RELEVANTES DA PARTE ATIVA")

        prts_ativo = self.separa_partes_importantes(tabela_parte_ativa)

        # PEGA OS DADOS DA TABELA POLO PASSIVO
        tabela_parte_passiva = self.driver.find_element_by_id('listaPoloPassivo')
        tabela_parte_passiva = tabela_parte_passiva.text.split("\n")

        prts_passiva = self.separa_partes_importantes(tabela_parte_passiva)

        terceiros = []
        tabela_terceiros = self.driver.find_element_by_id('listaPoloOutros')
        if tabela_terceiros:
            tabela_terceiros = tabela_terceiros.text.split("\n")

            terceiros = self.separa_partes_importantes(tabela_terceiros)

        prts = {'ativo': prts_ativo, 'passivo': prts_passiva, 'terceiro': terceiros}

        return prts

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        # print('COLETANDO OS ADVOGADOS')
        advs = []
        # exemplo
        # adv
        # = {
        #     'prr_nome': '',
        #     'prr_oab': '',
        #     'prr_cargo': 'Advogado',
        #     'prr_parte': '',
        # }

        # PEGA OS DADOS DA TABELA POLO ATIVO
        # aguarda_presenca_elemento(self.driver, 'listaPoloAtivo', tipo='ID')
        tabela_parte_ativa = self.driver.find_element_by_id('listaPoloAtivo')

        tabela_parte_ativa = tabela_parte_ativa.text.split("\n")

        advs_ativos = self.separa_advogados_importantes(tabela_parte_ativa, 'Polo Ativo')

        # PEGA OS DADOS DA TABELA POLO PASSIVO
        # aguarda_presenca_elemento(self.driver, 'listaPoloPassivo', tipo='ID')
        tabela_parte_passiva = self.driver.find_element_by_id('listaPoloPassivo')
        # tabela_parte_passiva.location_once_scrolled_into_view
        tabela_parte_passiva = tabela_parte_passiva.text.split("\n")

        advs_passivos = self.separa_advogados_importantes(tabela_parte_passiva, 'Polo Passivo')

        # print('COLETA DOS ADVOGADOS FINALIZADA!')

        return advs_ativos + advs_passivos

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        # print('COLETANDO OS DADOS')
        prc = {}

        if status_atual == 'Segredo de Justiça':
            status_atual = 'Ativo'

        prc['prc_status'] = get_status(self.movs, status_atual)

        data_distribuicao = self.driver.find_element_by_id('dataDistribuicaoDecoration:dataDistribuicao')
        if data_distribuicao:
            data_distribuicao = data_distribuicao.text.strip()
            if data_distribuicao != '':
                prc['prc_distribuicao'] = datetime.datetime.strptime(data_distribuicao, '%d/%m/%Y')


        # COLETA VALOR DA CAUSA
        # aguarda_presenca_elemento(self.driver, 'valorCausaDecoration:valorCausa', tipo='ID')
        valor_causa = self.driver.find_element_by_id('valorCausaDecoration:valorCausa')
        # valor_causa.location_once_scrolled_into_view
        prc['prc_valor_causa'] = valor_causa.text.strip()

        # COLETA ORGÃO JULGADOR
        # aguarda_presenca_elemento(self.driver, 'orgaoJulgDecoration:orgaoJulg', tipo='ID')
        orgao_julgador = self.driver.find_element_by_id('orgaoJulgDecoration:orgaoJulg')
        # orgao_julgador.location_once_scrolled_into_view
        prc['prc_serventia'] = orgao_julgador.text.strip()
        prc['prc_comarca2'] = localiza_comarca(prc['prc_serventia'], 'RJ')

        # COLETA SEGUNDO NUMERO DO PROCESSO
        # aguarda_presenca_elemento(self.driver, 'processoIdentificadorDiv', tipo='ID')
        segundo_numero_processo = self.driver.find_element_by_id('processoIdentificadorDiv')
        # segundo_numero_processo.location_once_scrolled_into_view
        prc['prc_numero2'] = localiza_cnj(segundo_numero_processo.text)

        # prc['prc_prioridade'] = ''
        prc['prc_assunto'] = self.coleta_prc_assunto()

        # xpath_prc_segredo = '/html/body/div[3]/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/div[1]/div/div/div/form/div/div[3]/table/tbody/tr/td[1]/span/div/span/div/div[2]'
        prc_segredo = self.driver.find_element_by_xpath('//*[@id="caracteristicaProcessoViewViewView"]/div/div[3]/table/tbody/tr/td[1]/span/div/span/div/div[2]')
        if not prc_segredo:
            prc_segredo = self.driver.find_element_by_id('segredoJusticaCletDecoration:divfieldsegredoJusticaClet')

        prc['prc_segredo'] = True if prc_segredo.text == 'SIM' else False

        # print('COLETA DE DADOS FINALIZADA!')
        return prc

    def pagina_anterior(self, num_pag_atual, navegador):
        num_pag_atual -= 1
        navegador.switch_to_window(navegador.window_handles[num_pag_atual])
        return num_pag_atual

    def coleta_quantidade_paginas_aba_audiencias(self):
        ''' Coleta a quantidade de paginas que possui na aba audiencia'''

        try:
            xpath_pg = '/html/body/div[3]/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td/div/div/div[2]/span/div/div[2]/form/table/tbody/tr[1]/td[3]'
            return int(self.driver.find_element_by_xpath(xpath_pg).text)
        except:
            return 1

    def passa_pagina_audiencia(self):
        xpath = '/html/body/div[3]/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td/div/div/div[2]/span/div/div[2]/form/table/tbody/tr[1]/td[4]/div/div[2]'
        aguarda_presenca_elemento(self.driver, xpath)
        self.driver.find_element_by_xpath(xpath).click()

    # CLICA EM PESQUISAR PARA ABRIR A CAIXA E MOSTRAR O CAMPO DE INSERÇÃO DO PROCESSO
    def clica_para_liberar_campo_processo(self):
        time.sleep(1)

        try:
            self.driver.execute_script("SimpleTogglePanelManager.toggleOnClient(event,'leftAdvPnl');")
        except MildException:
            tb = traceback.format_exc()
            # print(tb)
            self.logger.warning(tb, extra={'log_prc_id': self.prc_id})
            return False

    # INSERE O NUMERO DE PROCESSO NO CAMPO DE NUMERO
    def insere_numero_processo(self, numero):
        # INSERE O NUEMRO DO PROCESSO PARA BUSCA
        id = 'consultaProcessoAdvogadoForm:numeroProcessoDecoration:numeroProcesso'
        aguarda_presenca_elemento(self.driver, id, tipo='ID')
        inserir_numero = self.driver.find_element_by_id(id)
        inserir_numero.clear()  # LIMPA A CAIXA DE INSERÇÃO DO NUMERO
        inserir_numero.send_keys(Keys.HOME)  # VAI APRA O COMEÇO DA CAIXA

        if len(numero) > 18:
            parte_um = numero[:13]
            parte_dois = numero[16:]
            inserir_numero.send_keys(parte_um)  # INSERE O NUMERO DO PROCESSO
            inserir_numero.send_keys(parte_dois)  # INSERE O NUMERO DO PROCESSO
        else:
            inserir_numero.send_keys(numero)  # INSERE O NUMERO DO PROCESSO

    # VERIFICA A QUANTIDADE DE RESULTADOS PARA A BUSCA DO PROCESSO
    def verifica_quantidade_resultados(self):
        xpath = '/html/body/div[5]/div/div/div[2]/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/div/div[2]/div/div[2]/div[2]/span'
        aguarda_presenca_elemento(self.driver, xpath)
        quantidade = self.driver.find_element_by_xpath(xpath)
        if not quantidade:
            raise MildException("Erro ao capturar quantidade", self.uf, self.plataforma, self.prc_id, False)
        quantidade = quantidade.text.split(" ")

        return int(quantidade[2])

    # FAZ UM WAIT DIFERENTE, QUE ESPERA A BARRA DE CARREGAMENTO DO PJE
    def espera_barrinha_azul(self, id='_viewRoot:status.start', tempo=60):
        # AUTALIZAÇÃO DO DIA 15/05/2020, COMO ASLGUNS TRT'S ESTÃO MUITO LENTOS, EU SUBI O TEMPO DE ESPERA DE 40 PARA 180,
        if self.driver.find_element_by_id(id):
            wait = WebDriverWait(self.driver, tempo)
            try:
                wait.until(EC.invisibility_of_element((By.ID, id)))
            except TimeoutException:
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)


    def separa_partes_importantes(self, lista_dados, texto='ADV'):
        aux = []
        for elemento in lista_dados:
            if not 'Parte' in elemento:
                if not texto in elemento:
                    # print(elemento)
                    if elemento.find('- CNPJ') > -1:
                        auxiliar = elemento.split('- CNPJ')
                    else:
                        auxiliar = elemento.split('- CPF')
                    nome = auxiliar[0].strip()
                    nome = nome.replace("    ", "")
                    cpf = 'Não Informado'
                    if len(auxiliar) > 1:
                        cpf = auxiliar[1].split(" ")[1].strip()

                    aux.append({'prt_nome': nome, 'prt_cpf_cnpj': cpf})

                    # REINALDO CRUZ E ALBUQUERQUE - CPF: 081.121.547-40
                    # CECILIA TEODORA SILVA - OAB: RJ183856 - CPF: 085.830.517-80
        return aux

    def separa_advogados_importantes(self, lista_dados, parte):
        aux = []
        for elemento in lista_dados:
            if 'ADV' in elemento:
                auxiliar = elemento.split("-")
                nome = auxiliar[0].replace("    ", "")
                if 'OAB' in elemento:
                    OAB = auxiliar[1].replace("OAB:", "")
                    OAB = OAB.replace(" ", "")
                else:
                    OAB = None

                # aux.append(nome)
                # aux.append(OAB)
                # aux.append('Advogado')
                # aux.append(parte)

                # DADOS FORMATADOS
                aux.append({'prr_nome': nome, 'prr_oab': OAB, 'prr_cargo': 'Advogado', 'prr_parte': parte})
        return aux

    # DEFINE A PLATAFORMA UTILIZADA
    def muda_para_certificado(self):

        # VERIOFICA SE O SHODO JÁ TA SELECIONADO
        aguarda_presenca_elemento(self.driver,'/html/body/div[6]/div[2]/div[2]/div/div[1]/a', tipo='XPATH', tempo=4)

        certificado_option = self.driver.find_element_by_xpath('/html/body/div[6]/div[2]/div[2]/div/div[1]/a').text

        if 'Shodô' in certificado_option:
            return

        # ABRE A CAIXA DE OPÇÃO DOS CERTIFICADOS
        self.driver.execute_script("Richfaces.showModalPanel('mpModoOperacao')")

        # SELECIONA A OPÇÃO DO PJE OFFICE CASO NÃO TENHA SELECIONA O SHODO
        try: # SHODO
            aguarda_presenca_elemento(self.driver,'/html/body/div[8]/div[2]/div/div[2]/table/tbody/tr/td/table/tbody/tr[1]/td[2]/form/input[2]', tipo='XPATH', tempo=4)
            self.driver.find_element_by_xpath('/html/body/div[8]/div[2]/div/div[2]/table/tbody/tr/td/table/tbody/tr[1]/td[2]/form/input[2]').click()
        except: # PJEOFFICE
            aguarda_presenca_elemento(self.driver, '/html/body/div[8]/div[2]/div/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/form/input[2]', tipo='XPATH', tempo=4)
            self.driver.find_element_by_xpath('/html/body/div[8]/div[2]/div/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/form/input[2]').click()
            pass

        # FECHA A CAIXA DE SELEÇÃO
        self.driver.execute_script("Richfaces.hideModalPanel('mpModoOperacao');")

        aguarda_presenca_elemento(self.driver,'divLogin')
        # A PAGINA É ATUALIZADA PARA QUE A MUDANÇA SEJA APLICADA
        self.driver.refresh()

    # CLICA NO BOTÃO DE LOGIN COM O CERTIFICADO
    def faz_login_com_certificado(self):
        # try:
            aguarda_presenca_elemento(self.driver, 'loginAplicacaoButton', tipo='ID')
            self.driver.find_element_by_id('loginAplicacaoButton').click()

            while not self.confirma_pje_office():
                time.sleep(1)
                if self.driver.find_element_by_id('/html/body/nav'):
                    break

                try:
                    btn = self.driver.find_element_by_id('loginAplicacaoButton')
                    if btn:
                        btn.click()
                except StaleElementReferenceException:
                    self.driver.refresh()
                    self.driver.find_element_by_id('loginAplicacaoButton').click()
                    continue
                except:
                    continue
        # except:
        #     return False

    # CONFIRMA A BOX DE LOGIN DO CERTIFICADO
    def confirma_pje_office(self):
        time.sleep(1)
        inicio = time.time()
        while True:
            time.sleep(1)
            print('Procurando Janela de Confirmação do PJE')

            if len(self.driver.find_elements_by_xpath('/html/body/pje-root/pje-main/mat-sidenav-container/mat-sidenav-content/div/pje-cabecalho/div/mat-toolbar')):
                return True

            window_name = 'Assinador Digital'
            def callback(h, extra):
                if window_name in win32gui.GetWindowText(h):
                    extra.append(h)
                return True

            extra = []
            win32gui.EnumWindows(callback, extra)
            if len(extra) > 0:
                for hwnd in extra:
                    try:
                        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                    except:
                        pass

            # AUTORIZAÇÃO DO CERTIFICADO
            try:
                hwndMain = win32gui.FindWindow(None, "Autorização")
                if hwndMain > 0:
                    win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                    time.sleep(1)
                    return True
            except Exception as e:
                # print(e)
                pass

            # MODAL DE SENHA
            try:

                hwndMain = win32gui.FindWindow(None, "Insira o PIN:")
                if hwndMain > 0:
                    win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                    time.sleep(1)
                    return True
            except Exception as e:
                # print(e)
                pass

            # CONFIRMAÇÃO DO CERTIFICADO
            hwndMain = win32gui.FindWindow(None, "Autorização de Servidor")
            if hwndMain > 0:
                print("Modal autorização Localizado")

                l,t,_,_ = win32gui.GetWindowRect(hwndMain)
                lParam = win32api.MAKELONG(l+36, t+152)

                # self.bring_to_front(hwndMain)
                win32gui.PostMessage(hwndMain, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                win32gui.PostMessage(hwndMain, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, lParam)


            # ERRO NA LEITURA DO CERTIFICADO
            try:
                hwndMain = win32gui.FindWindow(None, "Erro ao executar tarefa")
                if hwndMain > 0:
                    win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                    return False
            except Exception as e:
                pass

            # ERRO NA LEITURA DO CERTIFICADO
            try:
                hwndMain = win32gui.FindWindow(None, "Erro ao executar a tarefa")
                if hwndMain > 0:
                    win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                    return False
            except Exception as e:
                pass

            if (time.time() - inicio) >= 40:
                raise Exception('PJE Office não localizado')

    def faz_login_usuario_e_senha(self, usuario, senha):

        # COLOCA O USUARIO
        aguarda_presenca_elemento(self.driver, 'username', tipo='ID')
        self.driver.find_element_by_id('username').send_keys(usuario)

        # COLOCA A SENHA
        aguarda_presenca_elemento(self.driver, 'password', tipo='ID')
        self.driver.find_element_by_id('password').send_keys(senha)

        # CLICA NO BOTÃO DE ENTRAR
        aguarda_presenca_elemento(self.driver, 'btnEntrar', tipo='ID')
        self.driver.find_element_by_id('btnEntrar').click()


    def coleta_prc_assunto(self):
        # CLICA NA ABA CARACTERISTICAS DO PROCESSO, PARA COLETAR O PRC ASSUNTO
        self.driver.execute_script("window.scrollTo(0,0)")

        aguarda_presenca_elemento(self.driver, 'caracteristicaProcesso_lbl', tipo='ID')
        self.driver.find_element_by_id('caracteristicaProcesso_lbl').click()

        self.espera_barrinha_azul()

        # CLICA NO BOTÃO ASSUNTO, PARA LISTAS AS LINHAS DA TABELA ASSUNTO
        aguarda_presenca_elemento(self.driver, 'toggleAssuntosProc:_form', tipo='ID')
        self.driver.find_element_by_id('toggleAssuntosProc:_form').click()

        aguarda_presenca_elemento(self.driver, 'processoAssuntoListAbaProcesso:tb', tipo='ID')
        texto_tabela_prc_assunto = self.driver.find_element_by_id('processoAssuntoListAbaProcesso:tb').text

        lista_assuntos = texto_tabela_prc_assunto.split("\n")
        tam_lista_assuntos = len(lista_assuntos)

        i = 1
        prc_assunto_final = ''
        while i < tam_lista_assuntos and len(prc_assunto_final) < 500:
            assunto = lista_assuntos[i].replace("DIREITO DO TRABALHO (864) / ", "")
            prc_assunto_final += assunto
            i += 2

        # print("RESULTADO FINAL PRC_ASSUNTO: ", prc_assunto_final[:500])
        return prc_assunto_final[:500]

    # FECHA A JANELA DO PROCESSO ABERTO ATUALMENTE
    def fecha_processo(self):
        wh = self.driver.window_handles
        while len(wh) > 1:
            try:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.close()
            except:
                pass
            wh = self.driver.window_handles
        self.driver.switch_to.window(self.driver.window_handles[0])


# [SQL: UPDATE processo SET
# prc_numero2=?,        '0100474-45.2019.5.01.0006'
# prc_promovente=?,     'ALEXANDER PEREIRA CARNEIRO'
# prc_promovido=?,      'TELEFONICA BRASIL S.A.'
# prc_cnpj_promovido=?, '02.558.157/0001-62'
# prc_cpf_cnpj=?,       '057.859.937-67'
# prc_comarca2=?,       'NFKD'
# prc_serventia=?,      '6ª Vara do Trabalho do Rio de Janeiro'
# prc_status=?,         'Ativo'
# prc_assunto=?,        'Rescisão do Contrato de Trabalho (2620) / Verbas Rescisórias (2546) / Aviso Prévio'
# prc_distribuicao=?,   '14/05/2019'
# prc_segredo=?,        0
# prc_data_pje=?,       '2021-09-15 13:24:12'
# prc_pje=?,            1
# prc_projudi=?,        0
# prc_eproc=?,          0
# prc_fisico=?,         0
# prc_esaj=?,           0
# prc_ppe=?,            0
# prc_tucujuris=?,      '2021-09-15 13:24:12'
# prc_data_update=?     190570
# WHERE prc_id = ?]
# [parameters: (, , , , , , , , , , , , , , , , , , , , )]