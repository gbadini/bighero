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

# CLASSE DA VARREDURA DO TRT. HERDA OS METODOS DA CLASSE PLATAFORMA
class Trt(PrimeiroGrau):

    def __init__(self):
        super().__init__()
        self.plataforma = 2
        self.div = None
        self.movs = []
        self.kill_nao_localizado = True
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
        if usuario == None:
            # self.muda_para_certificado('Shodô')
            if not self.faz_login_com_certificado():
                self.muda_para_certificado('PJeOffice')
                if not self.faz_login_com_certificado():
                    return False
        else:
            self.faz_login_usuario_e_senha(usuario, senha)

        if not aguarda_presenca_elemento(self.driver, 'pje-cabecalho-perfil', tempo=60, tipo='TAG_NAME'):
            return False
        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        time.sleep(1)
        self.clica_para_liberar_campo_processo()

        try:
            self.insere_numero_processo(numero_busca)
        except:
            raise MildException("Erro ao imputar numero", self.uf, self.plataforma, self.prc_id, False)

        # CLICA NO BOTÃO DE CONSULTA
        aguarda_presenca_elemento(self.driver, 'consultaProcessoAdvogadoForm:searchButon', tipo='ID')
        self.driver.find_element_by_id('consultaProcessoAdvogadoForm:searchButon').click()
        self.aguarda_barra_azul()

        quantidade_de_resultados = self.verifica_quantidade_resultados()

        # ENCONTROU UM OU MAIS PROCESSOS
        if quantidade_de_resultados > 0:
            # ENCONTROU VARIOS OU O NUMERO DO PROCESSO É '0'
            if quantidade_de_resultados > 1:
                if numero_busca == '0':
                    return False

                # print("MAIS DE UM RESULTADO ENCONTRADO!")
                # print("O NUMERO DE PROCESSO QUE OCASIONOU ISSO FOI: {}".format(numero_busca))
                raise MildException('Mais de um processo localizado', self.uf, self.plataforma, self.prc_id)
                return False

            return True

        return False

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        self.confere_cnj(numero_busca, codigo)

        return False

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca, codigo=None):
        '''
        :param str numero_busca: processo a ser comparado
        '''
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

        self.aguarda_barra_azul()
        header = self.driver.find_element_by_xpath('/html/body/div[5]/div/form/div[1]/span[1]')
        if header:
            if 'Unhandled or Wrapper Exception' in header.text:
                raise MildException("Erro ao abrir processo", self.uf, self.plataforma, self.prc_id)

        # CLICA NA ABA DE MOVIMENTAÇÕES
        aguarda_presenca_elemento(self.driver, 'MovimentacoesId_lbl', tipo='ID')
        self.driver.find_element_by_id('MovimentacoesId_lbl').click()

        self.aguarda_barra_azul()

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self, ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        total_colunas = self.driver.find_elements_by_xpath('//*[@id="movimentacaoList"]/thead/tr/th')
        total_colunas = len(total_colunas)
        xpath_element = '//*[@id="movimentacaoList:tb"]/tr[1]/td['+str(total_colunas - 1)+']'

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
        total_colunas = self.driver.find_elements_by_xpath('//*[@id="movimentacaoList"]/thead/tr/th')
        total_colunas = len(total_colunas)
        i = 0
        while pag < total_pags:
            self.aguarda_barra_azul()
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

                mov_text = mov_aux.find_element_by_xpath('td['+str(total_colunas-1)+']').text.split(' - ')
                acp_cadastro = datetime.datetime.strptime(mov_text[0], '%d/%m/%Y %H:%M:%S')
                acp_tipo = mov.find_element_by_xpath('td['+str(total_colunas-2)+']').text
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

        return movs

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        lista_audiencias = []
        # print("SUBINDO A JANELA PARA CLICAR NA ABA DE AUDIENCIAS")
        self.driver.execute_script("window.scrollTo(0,0)")

        # CLICA NA ABA DE AUDIENCIAS, PARA COLETAR AUDIENCIAS
        self.driver.find_element_by_id('tabProcessoAudiencia_lbl').click()
        aguarda_presenca_elemento(self.driver, 'processoConsultaAudienciaGridList', tipo='ID',aguarda_visibilidade=True)

        # quantidade_paginas = self.coleta_quantidade_paginas_aba_audiencias()
        # PERCORRE TODAS AS PAGINAS
        # for i in range(quantidade_paginas):
            # COLETA LINHAS COM AS AUDIENCIAS DA PAGINA ATUAL
        # xpath = '/html/body/div[3]/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td/div/div/div[2]/span/div/div/table/tbody/tr'
        xpath = '//*[@id="processoConsultaAudienciaGridList:tb"]/tr'
        webelements_audiencias = self.driver.find_elements_by_xpath(xpath)

        # PERCORRE TODAS AUDIENCIAS DE PRIMEIRO GRAU, E SEPARA AS INFORMAÇÕES
        for webelement_linha in webelements_audiencias:
            # SEPARA AS INFORMAÇÕES EM UMA LISTA
            date_full = webelement_linha.find_element_by_xpath('td[1]').text
            prp_data = datetime.datetime.strptime(date_full, '%d/%m/%Y %H:%M')

            prp_status = webelement_linha.find_element_by_xpath('td[5]').text
            prp_serventia = webelement_linha.find_element_by_xpath('td[3]').text
            prp_tipo = webelement_linha.find_element_by_xpath('td[2]').text

            data_mov = prp_data.time()

            # ARMAZENA TODAS AUDIENCIAS ENCONTRADAS PARA ESSE PROCESSO NESSA LISTA
            lista_audiencias.append({'prp_data': prp_data, 'prp_status': prp_status, 'prp_tipo': prp_tipo, 'prp_serventia': prp_serventia, 'data_mov': data_mov})

        xpath = '//*[@id="visualizarConsultaSessaoJulgamentoGridList:tb"]/tr'
        webelements_audiencias = self.driver.find_elements_by_xpath(xpath)

        # PERCORRE TODAS AUDIENCIAS DE SEGUNDO GRAU, E SEPARA AS INFORMAÇÕES
        for webelement_linha in webelements_audiencias:
            # SEPARA AS INFORMAÇÕES EM UMA LISTA
            date_full = webelement_linha.find_element_by_xpath('td[1]').text
            prp_data = datetime.datetime.strptime(date_full, '%d/%m/%Y %H:%M')

            prp_status = webelement_linha.find_element_by_xpath('td[4]').text
            prp_serventia = webelement_linha.find_element_by_xpath('td[2]').text
            prp_serventia += ' - '+webelement_linha.find_element_by_xpath('td[3]').text
            if prp_serventia.upper().find('EXECUÇÃO')>-1:
                prp_tipo = 'Execução'
            elif prp_serventia.upper().find('DISSÍDIOS INDIVIDUAIS') > -1:
                prp_tipo = 'Díssidio Individual'
            else:
                prp_tipo = 'Recurso'

            data_mov = prp_data.time()

            # ARMAZENA TODAS AUDIENCIAS ENCONTRADAS PARA ESSE PROCESSO NESSA LISTA
            lista_audiencias.append(
                {'prp_data': prp_data, 'prp_status': prp_status, 'prp_tipo': prp_tipo, 'prp_serventia': prp_serventia, 'data_mov': data_mov})

            # if quantidade_paginas > 1:
            #     self.passa_pagina_audiencia()
            #     self.aguarda_barra_azul()

        return lista_audiencias

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        # partes = {'ativo': [], 'passivo': [], 'terceiro':[]}

        # CLICA NA ABA DE AUDIENCIAS, PARA COLETAR AUDIENCIAS
        self.driver.find_element_by_id('informativoProcessoTrf_lbl').click()

        aguarda_presenca_elemento(self.driver, 'toggleDocumentos_header_label', tipo='ID')

        # PEGA OS DADOS DA TABELA POLO ATIVO
        tabela_parte_ativa = self.driver.find_element_by_id('listaPoloAtivo')
        tabela_parte_ativa = tabela_parte_ativa.text.split("\n")

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
        # exemplo
        # adv
        # = {
        #     'prr_nome': '',
        #     'prr_oab': '',
        #     'prr_cargo': 'Advogado',
        #     'prr_parte': '',
        # }

        # PEGA OS DADOS DA TABELA POLO ATIVO
        tabela_parte_ativa = self.driver.find_element_by_id('listaPoloAtivo')
        tabela_parte_ativa = tabela_parte_ativa.text.split("\n")

        advs_ativos = self.separa_advogados_importantes(tabela_parte_ativa, 'Polo Ativo')

        # PEGA OS DADOS DA TABELA POLO PASSIVO
        tabela_parte_passiva = self.driver.find_element_by_id('listaPoloPassivo')
        tabela_parte_passiva = tabela_parte_passiva.text.split("\n")

        advs_passivos = self.separa_advogados_importantes(tabela_parte_passiva, 'Polo Passivo')

        # print('COLETA DOS ADVOGADOS FINALIZADA!')
        # JUIZ
        # if self.grau == 1:
        #     {'prr_nome': '', 'prr_oab': '', 'prr_cargo': 'Advogado','prr_parte': '',}

        return advs_ativos + advs_passivos

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
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
        valor_causa = self.driver.find_element_by_id('valorCausaDecoration:valorCausa')
        prc['prc_valor_causa'] = valor_causa.text.strip()

        # COLETA ORGÃO JULGADOR
        orgao_julgador = self.driver.find_element_by_id('orgaoJulgDecoration:orgaoJulg')
        prc['prc_serventia'] = orgao_julgador.text.strip()
        prc['prc_comarca2'] = localiza_comarca(prc['prc_serventia'], 'RJ')

        # COLETA SEGUNDO NUMERO DO PROCESSO
        segundo_numero_processo = self.driver.find_element_by_id('processoIdentificadorDiv')
        prc['prc_numero2'] = localiza_cnj(segundo_numero_processo.text)

        prc['prc_assunto'] = self.coleta_prc_assunto()

        prc_segredo = self.driver.find_element_by_xpath('//*[@id="caracteristicaProcessoViewViewView"]/div/div[3]/table/tbody/tr/td[1]/span/div/span/div/div[2]')
        if not prc_segredo:
            prc_segredo = self.driver.find_element_by_id('segredoJusticaCletDecoration:divfieldsegredoJusticaClet')

        prc['prc_segredo'] = True if prc_segredo.text == 'SIM' else False

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
    def aguarda_barra_azul(self, id='_viewRoot:status.start', tempo=60):
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
                    if elemento.find('- CNPJ') > -1:
                        auxiliar = elemento.split('- CNPJ')
                    else:
                        auxiliar = elemento.split('- CPF')
                    nome = auxiliar[0].strip()
                    nome = nome.replace("    ", "")
                    cpf = 'Não Informado'
                    if len(auxiliar) > 1:
                        auxiliar[1] = auxiliar[1].replace(':', '').strip()
                        cpf = auxiliar[1].split(" ")[0].strip()

                    aux.append({'prt_nome': nome, 'prt_cpf_cnpj': cpf})

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

                aux.append({'prr_nome': nome, 'prr_oab': OAB, 'prr_cargo': 'Advogado', 'prr_parte': parte})
        return aux

    # DEFINE A PLATAFORMA UTILIZADA
    def muda_para_certificado(self, option):
        print('TENTANDO LOGAR COM O {}'.format(option))
        # VERIFICA SE A OPÇÃO JÁ TA SELECIONADA
        aguarda_presenca_elemento(self.driver,'/html/body/div[6]/div[2]/div[2]/div/div[1]/a', tipo='XPATH', tempo=4)
        certificado_option = self.driver.find_element_by_xpath('/html/body/div[6]/div[2]/div[2]/div/div[1]/a').text

        if option in certificado_option:
            return

        # ABRE A CAIXA DE OPÇÃO DOS CERTIFICADOS
        self.driver.execute_script("Richfaces.showModalPanel('mpModoOperacao')")

        # SELECIONA O CERTIFICADO
        if 'Shodô' in option:
            aguarda_presenca_elemento(self.driver,'/html/body/div[8]/div[2]/div/div[2]/table/tbody/tr/td/table/tbody/tr[1]/td[2]/form/input[2]', tipo='XPATH', tempo=4)
            self.driver.find_element_by_xpath('/html/body/div[8]/div[2]/div/div[2]/table/tbody/tr/td/table/tbody/tr[1]/td[2]/form/input[2]').click()
        else:
            try:
                aguarda_presenca_elemento(self.driver, '/html/body/div[8]/div[2]/div/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/form/input[2]', tipo='XPATH', tempo=4)
                self.driver.execute_script("selecionarPJeOffice();")
                # self.driver.find_element_by_xpath('/html/body/div[8]/div[2]/div/div[2]/table/tbody/tr/td/table/tbody/tr[2]/td[2]/form/input[2]').click()
            except:
                raise Exception('PJeOffice não localizado')

        # FECHA A CAIXA DE SELEÇÃO
        self.driver.execute_script("Richfaces.hideModalPanel('mpModoOperacao');")

        aguarda_presenca_elemento(self.driver,'divLogin', tempo=4)
        # A PAGINA É ATUALIZADA PARA QUE A MUDANÇA SEJA APLICADA
        self.driver.refresh()

    # CLICA NO BOTÃO DE LOGIN COM O CERTIFICADO
    def faz_login_com_certificado(self):
        aguarda_presenca_elemento(self.driver, 'loginAplicacaoButton', tipo='ID')
        self.driver.find_element_by_id('loginAplicacaoButton').click()
        return self.confirma_pje_office()

    # CONFIRMA A BOX DE LOGIN DO CERTIFICADO
    def confirma_pje_office(self):
        time.sleep(1)
        inicio = time.time()
        try:
            while True:
                time.sleep(1)
                if self.driver.find_element_by_xpath('/html/body/pje-root/pje-main/mat-sidenav-container/mat-sidenav-content/div/pje-cabecalho/div/mat-toolbar'):
                    return True

                if self.driver.find_element_by_tag_name('pje-cabecalho-perfil'):
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
                # try:
                hwndMain = win32gui.FindWindow(None, "Autorização de Servidor")
                if hwndMain > 0:
                    # l, t, _, _ = win32gui.GetWindowRect(hwndMain)
                    # lParam = win32api.MAKELONG(l + 149, t + 188)
                    l, t, r, b = win32gui.GetWindowRect(hwndMain)
                    lParam = win32api.MAKELONG(math.ceil(r*0.6683), math.ceil(b*0.958))
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

                if (time.time() - inicio) >= 40:
                    raise Exception('PJE Office não localizado')
        except:
            print('ERRO LOGIN')
            return False

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

        self.aguarda_barra_azul()

        # CLICA NO BOTÃO ASSUNTO, PARA LISTAS AS LINHAS DA TABELA ASSUNTO
        aguarda_presenca_elemento(self.driver, 'toggleAssuntosProc:_form', tipo='ID')
        self.driver.find_element_by_id('toggleAssuntosProc:_form').click()

        aguarda_presenca_elemento(self.driver, 'processoAssuntoListAbaProcesso:tb', tipo='ID')
        texto_tabela_prc_assunto = self.driver.find_element_by_id('processoAssuntoListAbaProcesso:tb').text

        lista_assuntos = texto_tabela_prc_assunto.split("\n")
        tam_lista_assuntos = len(lista_assuntos)

        i = 1
        prc_assunto_final = ''
        while i < tam_lista_assuntos:
            assunto = lista_assuntos[i].replace("DIREITO DO TRABALHO (864) / ", "")
            prc_assunto_final += assunto
            i += 2

        return prc_assunto_final

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

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, pasta_intermediaria):
        arquivos = []
        total_arquivos = 0
        total_pags = 1

        # Clica na aba "Processo"
        aguarda_presenca_elemento(self.driver, 'informativoProcessoTrf_lbl', tipo='ID')
        self.driver.find_element_by_id('informativoProcessoTrf_lbl').click()
        aguarda_presenca_elemento(self.driver, '//*[@id="processoDocumentoGridTabList:tb"]/tr')

        # Quando só tem 1 página, não existe a div com o xpath do total de páginas.
        # Se tiver mais de uma página, retorna a quantidade total de páginas
        qtd_divs = self.driver.find_elements_by_xpath(
            '/html/body/div[3]/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td/div/div[2]/div[2]/div/div/div[2]/div/div/div[2]/span/div/div')

        qtd_pag = 1
        # Retorna a quantidade de páginas, caso seja mais que 1
        if len(qtd_divs) > 1:
            qtd_pag = int(self.driver.find_element_by_xpath(
                '//*[@id="processoDocumentoGridTab"]/div/div[2]/form/table/tbody/tr[1]/td[3]').text)

        # Verifica o grau do processo, 2º grau tem uma coluna a mais
        # td_coluna = ['4', '5', '6', '7', '8', '9']
        # if self.grau == 1:
        #     td_coluna.insert(0, '3')

        # # Verifica o grau do processo pela quantidade de colunas (1º grau = 8 colunas, 2º grau 9 = colunas)
        colunas = self.driver.find_elements_by_xpath('//*[@id="processoDocumentoGridTabList:tb"]/tr[1]/td')
        td_coluna = ['4', '5', '6', '7', '8', '9']
        if len(colunas) == 8:
            td_coluna.insert(0, '3')

        # Iteração global em todas as páginas
        for bloco in range(0, qtd_pag):
            procs = self.driver.find_elements_by_xpath('//*[@id="processoDocumentoGridTabList:tb"]/tr')

            # Captura o primeiro ID para fazer a comparação se trocou de página
            prim_td = procs[0].find_elements_by_xpath('td')
            prim_id_proc = prim_td[0].text

            # Iteração de cada página, blocos de 10 processos
            for en, proc in enumerate(procs):
                # Inicializa as variáveis
                arq = {'pra_prc_id': prc_id, 'pra_plt_id': self.plataforma, 'pra_erro': False, 'pra_arquivo': None,
                       'pra_sigilo': False, 'pra_original': None, 'pra_tentativas': None, 'pra_excluido': False}

                limpar_pasta(self.pasta_download)

                # Recebe o Xpath parcial das tds
                td = '//*[@id="processoDocumentoGridTabList:tb"]/tr[' + str(en + 1) + ']/td['

                # Recebe o ID TJ
                arq['pra_id_tj'] = self.driver.find_element_by_xpath(td + '1]').text

                # Recebe o grau
                grau = self.driver.find_element_by_xpath(td + '2]').text
                if grau == '3º Grau':
                    arq['pra_grau'] = 3
                elif grau == '2º Grau':
                    arq['pra_grau'] = 2
                else:
                    arq['pra_grau'] = 1

                # Recebe a data
                pra_data = self.driver.find_element_by_xpath(td + td_coluna[0] + ']').text
                if pra_data == '':
                    # Se a data estiver em branco
                    arq['pra_data'] = None
                else:
                    # Se o campo estiver preenchido com a data
                    arq['pra_data'] = datetime.datetime.strptime(pra_data, '%d/%m/%Y %H:%M')

                # Verifica se o documento é sigiloso
                if self.driver.find_element_by_xpath(td + td_coluna[1] + ']').text == 'Documento Sigiloso':
                    arq['pra_sigilo'] = True

                # Recebe Documento + Tipo de Documento
                # Se forem iguais recebe somente Documento
                if self.driver.find_element_by_xpath(td + td_coluna[1] + ']').text == self.driver.find_element_by_xpath(
                        td + td_coluna[2] + ']').text:
                    arq['pra_descricao'] = self.driver.find_element_by_xpath(td + td_coluna[1] + ']').text
                else:
                    arq['pra_descricao'] = self.driver.find_element_by_xpath(
                        td + td_coluna[1] + ']').text + ' - ' + self.driver.find_element_by_xpath(td + td_coluna[2] + ']').text

                # Verifica se o documento foi excluído
                if self.driver.find_element_by_xpath(td + td_coluna[5] + ']').text == 'Excluido':
                    arq['pra_excluido'] = True

                print(arq)
                # Se o arquivo não constar na base realiza o download
                achei = False
                for a_b in arquivos_base:
                    # print(a_b['pra_id_tj'], arq['pra_id_tj'])
                    # Verifica se o ID TJ já existe na base
                    if a_b['pra_id_tj'] == arq['pra_id_tj']:
                        achei = True

                        # Se o arquivo existe na base, verifica se existe pendências
                        if len(pendentes) == 0:
                            return arquivos

                        # Se o arquivo existir na lista de pendências recebe o valor salvo na base
                        # Realiza o download e remove da lista de pendentes
                        for p, pend in enumerate(pendentes[:]):
                            if pend['pra_id_tj'] == arq['pra_id_tj']:
                                achei = False
                                arq['pra_tentativas'] = pend['pra_tentativas']
                                arq['pra_id'] = pend['pra_id']

                                # Apaga o item atual da lista das pendências
                                del pendentes[p]
                                break
                        break
                # Se o arquivo constar na base e não constar na lista de pendências
                if achei:
                    continue

                # Verifica a quantidade de SPANS antes de clicar para baixar, geralmente tem 2 ou 3 SPANS
                spans = self.driver.find_elements_by_xpath(td + td_coluna[3] + ']/span/div/span')
                str_spans = str(len(spans))

                if arq['pra_data'] == None:
                    # Quando a data é Nula, tem 4 SPANS tem que subtrair um span da contagem
                    str_spans = str(len(spans) - 1)

                # Verifica a existencia do gif do visualizador de processo
                visualizador = self.driver.find_elements_by_xpath(
                    td + td_coluna[3] + ']/span/div/span[' + str_spans + ']/form[2]/a/img')

                if not arq['pra_excluido'] and not arq['pra_sigilo']:
                    # Verifica se é só visualizador ou tem PDF pra baixar
                    if len(visualizador) > 0:
                        self.driver.find_element_by_xpath(
                            td + td_coluna[3] + ']/span/div/span[' + str_spans + ']/form[2]/a/img').click()
                        # Alterna para a janela do visualizador
                        self.driver.switch_to.window(self.driver.window_handles[-1])

                        # Aguarda a presença do botão de imprimir
                        aguarda_presenca_elemento(self.driver, 'btnimprimir', tipo='ID')

                        # Salva a visualização em PDF
                        self.driver.execute_script('setTimeout(function() { window.print(); }, 0);')
                        arq['pra_erro'] = False if aguarda_download(self.pasta_download, 1) else True

                        # Fecha a janela do visualizador
                        self.driver.close()
                        # Retorna para a janela principal
                        self.driver.switch_to.window(self.driver.window_handles[1])

                    # Se tiver PDF para baixar
                    else:
                        # Verifica a existencia do elemento a
                        elem_a = self.driver.find_elements_by_xpath(td + td_coluna[3] + ']/span/div/span[' + str_spans + ']/a')
                        if not elem_a:
                            arq['pra_erro'] = True
                        else:
                            self.driver.find_element_by_xpath(td + td_coluna[3] + ']/span/div/span[' + str_spans + ']/a/img').click()
                            arq['pra_erro'] = False if aguarda_download(self.pasta_download, 1) else True

                if not arq['pra_erro'] and not arq['pra_excluido'] and not arq['pra_sigilo']:
                    total_arquivos += 1
                    file_names = os.listdir(self.pasta_download)
                    arq['pra_original'] = file_names[0]
                    pra_arquivo = trata_arquivo(file_names[0], self.pasta_download, pasta_intermediaria)
                    arq['pra_arquivo'] = pra_arquivo

                elif self.tipo != 2 and arq['pra_erro']:
                    arq['pra_original'] = None
                    arq['pra_arquivo'] = None
                    arq['pra_tentativas'] = 1 if arq['pra_tentativas'] is None else arq['pra_tentativas'] + 1
                    limpar_pasta(self.pasta_download)
                    print('Erro download ', arq)

                arquivos.append(arq)

            # Se tiver somente uma página, não existe seta de avançar página.
            if qtd_pag > bloco + 1:
                # Seta avançar página
                self.driver.find_element_by_xpath(
                    '//*[@id="processoDocumentoGridTab"]/div/div[2]/form/table/tbody/tr[1]/td[4]/div/div[2]').click()

                # Aguarda o carregamento da nova página
                self.aguarda_barra_azul()

                # Verifica se o conteúdo alterou comparando o primeiro ID de cada página
                # Clica e permanece no loop até trocar de página
                while True:
                    # Captura novamente o primeiro ID do bloco
                    novo_procs = self.driver.find_elements_by_xpath('//*[@id="processoDocumentoGridTabList:tb"]/tr')
                    novo_first_td = novo_procs[0].find_elements_by_xpath('td')
                    novo_prim_id_proc = novo_first_td[0].text

                    # Quebra o loop quando os dois IDs forem diferentes
                    if prim_id_proc != novo_prim_id_proc:
                        break

        arquivos.reverse()
        return arquivos
