from Controllers.Clientes.pagamentos import *
from Controllers.Clientes.Espaider._espaider import *
from dateutil.relativedelta import relativedelta
from selenium.webdriver import ActionChains

# CLASSE DO LANÇAMENTO DE PAGAMENTOS. HERDA OS METODOS DA CLASSE PROCESSUM
class Pagamentos(PagamentosCliente, Espaider):

    def __init__(self):
        super().__init__()
        self.ordem_usuario = 0

    # TRATA OS DADOS PARA O FORMATO DA PLATAFORMA
    def tratar_dados(self, base, dados):
        acp = dict(input={}, select={})

        acp['input']['pag_tipo'] = {'dado': dados['pag_tipo'], 'campo': '//*[@id="CLI_TipoPagamento"]/div/div[2]/input[1]', 'by': 'XPATH', 'check_tb': 'lkpPopupCLI_TipoPagamento_grdv'}
        acp['input']['pag_favorecido'] = {'dado': dados['pag_favorecido'], 'campo': '//*[@id="CLI_Fornecedor"]/div/div[2]/input[1]', 'by': 'XPATH', 'check_tb': 'lkpPopupCLI_Fornecedor_grdv'}
        acp['input']['pag_tipo_pagamento'] = {'dado': dados['pag_tipo_pagamento'], 'campo': '//*[@id="CLI_FormaPagamento"]/div/div[2]/input[1]', 'by': 'XPATH', 'check_tb': 'lkpPopupCLI_FormaPagamento_grdv'}
        acp['input']['pag_conta_contabil'] = {'dado': dados['pag_conta_contabil'], 'campo': '//*[@id="CLI_CentroCusto"]/div/div[2]/input[1]', 'by': 'XPATH', 'check_tb': 'lkpPopupCLI_CentroCusto_grdv'}
        acp['input']['pag_ordem'] = {'dado': dados['pag_ordem'], 'campo': '//*[@id="CLI_CentroCustoOrdem"]/div/div[2]/input[1]', 'by': 'XPATH', 'check_tb': 'lkpPopupCLI_CentroCustoOrdem_grdv'}


        acp['input']['pag_data_limite'] = {'dado': dados['pag_data_limite'].strftime('%d/%m/%Y'), 'campo': '//*[@id="CLI_DataVencimento"]/div/div[2]/input', 'by': 'XPATH'}
        acp['input']['pag_valor'] = {'dado': format_number_br(dados['pag_valor']), 'campo': '//*[@id="CLI_Valor"]/div/div[2]/input', 'by': 'XPATH'}

        if dados['pag_cpf_favorecido'] is not None and dados['pag_cpf_favorecido'] != '' and dados['pag_cpf_favorecido'] != 'NSA':
            acp['input']['pag_cpf_favorecido'] = {'dado': dados['pag_cpf_favorecido'], 'campo': '//*[@id="CLI_CPFCNPJFornec"]/div/div[2]/input', 'by': 'XPATH'}

        acp['input']['pag_codigo_barra'] = {'dado': dados['pag_codigo_barra'], 'campo': '//*[@id="CLI_CodigoBarras"]/div/div[2]/input', 'by': 'XPATH'}
        acp['input']['pag_descricao'] = {'dado': dados['pag_descricao'], 'campo': '//*[@id="PagtoObservacoes"]/div/div/textarea', 'by': 'XPATH'}


        acp['arquivos_ocorrencia'] = Arquivo.select_by_pagamento(base, dados['pag_id'])
        if len(acp['arquivos_ocorrencia']) == 0:
            raise FatalException('Pagamento sem arquivos vinculados', self.uf, self.plataforma, self.prc_id)

        acp['obs_arquivo'] = "Segue anexos"

        print(acp)
        return acp

    # CONFERE SE A OCORRENCIA FOI LANÇADA
    def confere_lancamento(self, dados_lanc, range_data_cadastro=2, range_data_evento=0, confere_conteudo=False, quantidade=1, ignora_cancelado=False):
        # return False
        self.driver.switch_to.default_content()
        self.wait_load()
        aguarda_presenca_elemento(self.driver, '/html/body/div/div/div[2]/div/iframe')
        iframe_audiencia = self.driver.find_element_by_xpath('/html/body/div/div/div[2]/div/iframe')
        self.driver.switch_to_frame(iframe_audiencia)
        aguarda_presenca_elemento(self.driver,'//*[@id="colCLI_HistoricoContingenciador"]/a')
        self.driver.find_element_by_xpath('//*[@id="colCLI_HistoricoContingenciador"]/a').click()
        # self.driver.find_element_by_xpath('/html/body/form/div/div/div[2]/div[2]/div[1]/div[2]/div/div/div[2]/div/div[3]/ul/li[24]/a').click()
        self.wait_load()

        # ACESSA O IFRAME DA TABELA
        aguarda_presenca_elemento(self.driver, '//*[@id="rightContainer"]/div/iframe')
        iframe_audiencia = self.driver.find_element_by_xpath('//*[@id="rightContainer"]/div/iframe')
        self.driver.switch_to_frame(iframe_audiencia)
        self.wait_load()

        tabela_pagamentos = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr')
        if tabela_pagamentos:
            if tabela_pagamentos.text == 'Nenhum registro.':
                return False

            colunas = self.detecta_colunas()
            # today = datetime.today()
            tabela_pagamentos = self.driver.find_elements_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr')
            for txt in tabela_pagamentos:
                if txt.is_displayed() and txt.text == 'Nenhum registro.':
                    return False

                print(txt.find_element_by_xpath('td['+str(colunas['Codigo de barras'])+']').text[:47])
                print(dados_lanc['input']['pag_codigo_barra']['dado'][:47])
                if txt.find_element_by_xpath('td['+str(colunas['Codigo de barras'])+']').text[:47] == dados_lanc['input']['pag_codigo_barra']['dado'][:47]:
                    # data_transf = txt.find_element_by_xpath('td[]').text
                    # data_transf = datetime.strptime(data_transf, '%d/%m/%Y').date()
                    # if data_transf == today:
                    return True

                    # if txt.find_element_by_xpath('td[5]').text == today.strftime('%d/%m/%Y'):
                    #     return True

        return False

    # GERENCIA O LANÇAMENTO DE OCORRENCIAS NO PROCESSUM
    def lanca_ocorrencia(self, acp, url_arquivos='', gera_exception=False, lanca_arquivos=True):
        print('Lançando Ocorrência')
        self.driver.switch_to.default_content()
        iframe_processo = self.detecta_iframe()
        self.driver.switch_to_frame(iframe_processo)
        self.driver.find_element_by_xpath('//*[@id="cmdCLI_PagtoDespesas_Processos"]/em/button').click()
        self.wait_load()

        self.aguarda_iframe('https://espaider.neoenergia.com//pgs/AbrirSolicitacaoQualquerInterface.aspx?ID=')

        aguarda_presenca_elemento(self.driver, '//*[@id="TabPanel_SlSolicitacoes"]/div[1]/div[4]/div/div[24]/em/button', aguarda_visibilidade=True)
        self.driver.find_element_by_xpath('//*[@id="TabPanel_SlSolicitacoes"]/div[1]/div[4]/div/div[24]/em/button').click()
        aguarda_presenca_elemento(self.driver, '//*[@id="CLI_TipoPagamento"]/div/div[2]/input[1]', aguarda_visibilidade=True)

        inputs = acp['input']
        entrei = True
        while entrei:
            entrei = False
            for d in inputs:
                if 'readonly' in inputs[d] and inputs[d]['readonly']:
                    continue

                if inputs[d]['dado'] is None:
                    continue

                # limpar_string = inputs[d]['limpar_string'] if 'limpar_string' in inputs[d] else False
                by = getattr(By, inputs[d]['by'])
                campo = self.driver.find_element(by, inputs[d]['campo'])
                texto_cli = campo.get_attribute('value')
                texto_cli = self.clear_special_chars(texto_cli)
                texto_original = self.clear_special_chars(inputs[d]['dado'])

                if texto_cli.upper() != texto_original.upper():
                    entrei = True
                    check_tb = inputs[d]['check_tb'] if 'check_tb' in inputs[d] else False
                    self.preenche_campo(inputs[d]['dado'], inputs[d]['campo'], inputs[d]['by'], check_tb=check_tb)

        self.driver.find_element_by_xpath('//*[@id="CLI_GuiaPagamento"]/div/div[2]/input[1]').click()
        # aguarda_presenca_elemento(self.driver, 'q-comp-2733_proxy', tipo='ID')
        self.aguarda_iframe('https://espaider.neoenergia.com//upl/default.aspx')

        aguarda_presenca_elemento(self.driver, 'fakeInputFileEdt', tipo='ID', aguarda_visibilidade=True)

        file_upload = self.driver.find_element_by_id('TheFile')
        try:
            file_upload.send_keys(url_arquivos + acp['arquivos_ocorrencia'][0]['arq_url'])
        except:
            raise FatalException("Confererir integridade de arquivo: " + acp['arquivos_ocorrencia'][0]['arq_nome'], self.uf, self.plataforma, self.prc_id)

        self.driver.find_element_by_xpath('//*[@id="Yes"]/em/button').click()

        self.driver.switch_to.default_content()
        iframe_processo = self.driver.find_element_by_xpath('/html/body/div[5]/div/div[2]/div/iframe')
        self.driver.switch_to_frame(iframe_processo)

        self.driver.find_element_by_xpath('//*[@id="Save_SlSolicitacoes"]/em/button').click()
        self.driver.find_element_by_xpath('//*[@id="cmdFAPD_EnviarParaAprovacao_SlSolicitacoes"]/em/button').click()

        self.driver.switch_to.default_content()
        iframe_processo = self.driver.find_element_by_xpath('/html/body/div[6]/div/div[2]/div/iframe')
        self.driver.switch_to_frame(iframe_processo)

        self.driver.find_element_by_xpath('//*[@id="nextButton"]/em/button').click()
        self.driver.find_element_by_xpath('//*[@id="toolbar"]/div/div/em/button').click()

        # self.driver.find_element_by_xpath('//*[@id="SaveAndClose_SlSolicitacoes"]/em/button').click()

        self.driver.switch_to.default_content()
        iframe_processo = self.driver.find_element_by_xpath('/html/body/div[5]/div/div[2]/div/iframe')
        self.driver.switch_to_frame(iframe_processo)

        return True

    # PREENCHE O CAMPO DESEJADO
    def preenche_campo(self, texto, elemento, tipo='XPATH', check_tb=False):
        by = getattr(By, tipo)
        texto_original = self.clear_special_chars(texto)
        print(texto, elemento)
        texto_cli = ''
        inicio = time.time()
        action = ActionChains(self.driver)

        while texto_original.upper() != texto_cli.upper():
            if time.time() - inicio > 20:
                raise MildException("Erro ao imputar texto no campo "+elemento+" | "+texto_original+" | "+texto_cli, self.uf, self.plataforma, self.prc_id)

            # campo = self.driver.find_element(by, elemento)
            try:
                # self.driver.switch_to.default_content()
                self.driver.find_element(by, elemento).clear()
                self.driver.find_element(by, elemento).click()
                self.driver.find_element(by, elemento).send_keys(Keys.HOME)
                campo = self.driver.find_element(by, elemento)
                for t in texto:
                    tentativas = 0
                    while True:
                        try:
                            campo.send_keys(t)
                            break
                        except:
                            tentativas += 1
                            if tentativas > 3:
                                raise

                            tb = traceback.format_exc(limit=1)
                            # print(tb)
                            if tb.find('stale element') > -1:
                                time.sleep(0.5)
                            else:
                                raise

                if check_tb:
                    self.driver.switch_to.default_content()
                    # id_tb = self.driver.find_elements_by_xpath('//*[@id="'+check_tb+'"]/div/div/div[2]/div/div[2]/table/tbody/tr')
                    inicio_w = time.time()
                    while True:

                        achei = False
                        total_linhas = 0
                        id_tb = self.driver.find_elements_by_xpath('//*[@id="' + check_tb + '"]/div/div/div[2]/div/div[2]/table/tbody/tr')
                        for linha in id_tb:

                            try:
                                if linha.is_displayed():
                                    total_linhas += 1

                                    td1 = linha.find_element_by_xpath('td[1]').text
                                    td2 = linha.find_element_by_xpath('td[2]').text

                                    if td1.upper() == texto_original.upper() or td2.upper() == texto_original.upper():
                                        time.sleep(1)
                                        achei = True
                                        linha.click()
                                        campo.send_keys(Keys.TAB)
                                        # action.double_click(linha)
                                        # time.sleep(1)
                                        break
                            except:
                                total_linhas = 0
                                break

                        if achei:
                            break

                        if total_linhas < 1:
                            if time.time() - inicio_w > 8:
                                break

                        if total_linhas >= 1 and total_linhas < 7:
                            break

                    self.aguarda_iframe('https://espaider.neoenergia.com//pgs/AbrirSolicitacaoQualquerInterface.aspx?ID=')

                campo.send_keys(Keys.TAB)
                campo = self.driver.find_element(by, elemento)
                texto_cli = campo.get_attribute('value')
                texto_cli = self.clear_special_chars(texto_cli)
                ini_texto = time.time()

                # AGUARDA O PREENCHIMENTO DO CAMPO
                while len(texto_cli) != len(texto_original):
                    time.sleep(0.5)
                    if time.time() - ini_texto > 3:
                        break
                    try:
                        texto_cli = campo.get_attribute('value')
                        texto_cli = self.clear_special_chars(texto_cli)

                    except:
                        tb = traceback.format_exc(limit=1)
                        if tb.find('stale element') > -1:
                            time.sleep(1)
                        else:
                            raise
            except:
                tb = traceback.format_exc(limit=1)
                if tb.find('stale element') > -1:
                    time.sleep(1)

                if tb.find('stale element') == -1 and tb.find('invalid element state') == -1:
                    print(tb)

                self.driver.switch_to.default_content()
                self.aguarda_iframe('https://espaider.neoenergia.com//pgs/AbrirSolicitacaoQualquerInterface.aspx?ID=')

                print(tb)
                pass

        time.sleep(0.5)

    def clear_special_chars(self, texto):
        return texto.replace('/', '').replace('\\', '').replace('.', '').replace('-', '').replace('\r', '').replace('\n', '')

    def aguarda_iframe(self, src):
        self.driver.switch_to.default_content()
        while True:
            iframes = self.driver.find_elements_by_tag_name('iframe')
            for ifrm in iframes:
                if ifrm.get_attribute('src').find(src) > -1:
                    self.driver.switch_to_frame(ifrm)
                    self.wait_load()
                    return

    def detecta_colunas(self):
        colunas = {}
        try:
            self.driver.maximize_window()
        except:
            pass

        while 'Codigo de barras' not in colunas:
            titulos = self.driver.find_elements_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[1]/div/div/div/div/div[1]')
            i = 0
            colunas = {}
            for tt in titulos:
                nome = remove_acentos(tt.text)
                if nome == '':
                    continue

                i += 1
                colunas[nome] = i

        print(colunas)
        return colunas