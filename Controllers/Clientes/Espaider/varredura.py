import time

from Controllers.Clientes.Espaider._espaider import *

# CLASSE DA VARREDURA DO PROCESSUM. HERDA OS METODOS DA CLASSE PROCESSUM
class Varredura(Espaider):

    def __init__(self):
        super().__init__()
        self.movs = []
        self.ordem_usuario = 0
        self.titulo_partes = get_tipo_partes()
        self.reiniciar_varredura = False

    # CAPTURA DADOS DO PROCESSO
    def dados(self, dados, base):
        '''
        :param dict dados: Dados do processo salvos atualmente na base
        '''
        prc = {}

        self.driver.switch_to.default_content()

        # ACESSA O IFRAME DA LISTA E BUSCA DE PROCESSOS
        # aguarda_presenca_elemento(self.driver, '/html/body/div[2]/div/div[2]/div/iframe')
        iframe_processo = self.detecta_iframe()
        self.driver.switch_to_frame(iframe_processo)

        aguarda_presenca_elemento(self.driver, '//*[@id="tab_NVQCGERAL"]/div/div/div/div[2]/div/div/div[1]/div')

        # REMOVE O readonly QUE IMPEDE A COLETA DO TEXTO
        lista_WebElementos = self.driver.find_elements_by_tag_name('input')
        for WebElemento in lista_WebElementos:
            self.driver.execute_script("arguments[0].removeAttribute('readonly','readonly')", WebElemento)

        divs = self.driver.find_elements_by_xpath('//*[@id="tab_NVQCGERAL"]/div/div/div/div/div/div/div/div')
        campos = {'Número contrato': 'prc_sequencial', 'Cadastrado em': 'prc_data', 'Natureza': 'prc_modulo', 'Situação': 'prc_situacao', 'Objeto': 'prc_objeto1', 'Objeto causa': 'prc_objeto2', 'Empresa': 'prc_empresa', 'Adverso': 'prc_promovente', 'Data de citação': 'prc_data_citacao', 'CPF\CNPJ':  'prc_cpf_cnpj' }
        i = 1
        for div in divs:
            i += 1
            label = div.find_element_by_xpath('div[1]').text
            for c in campos:
                if label.upper() == c.upper():
                    txt = div.find_element_by_xpath('div[2]/input').get_attribute("value")
                    prc[campos[c]] = txt
                    break

        # data_distribuicao = self.driver.find_element_by_xpath('/html/body/form/div/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[9]/div/div/div/div[9]/div[2]/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[2]/input').get_attribute("value")
        # prc['prc_distribuicao'] = datetime.strptime(data_distribuicao, '%d/%m/%Y')
        # prc['prc_sequencial']
        if prc['prc_sequencial'].strip() == '' or find_string(prc['prc_sequencial'],('SEM CONTA CONTRATO','SEM CONTRATO','NÃO FOI INFORMAD','NÃO FOI CITAD','NAO FOI CITAD')):
            prc['prc_sequencial'] = 'SEM CONTRATO'
        else:
            f = find_string(prc['prc_sequencial'],('/',';',',',' E ','    '))
            if f:
                prc['prc_sequencial'] = prc['prc_sequencial'][:f[1]].strip()

            if len(prc['prc_sequencial']) > 25:
                prc['prc_sequencial'] = corta_string(prc['prc_sequencial'], 25)

        # prc['prc_serventia'] = self.driver.find_element_by_xpath('/html/body/form/div/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[9]/div/div/div/div[9]/div[2]/div/div[1]/div[1]/div/div/div/div/div[3]/div/div[2]/input[1]').get_attribute("value")
        # prc['prc_comarca'] = self.driver.find_element_by_xpath('/html/body/form/div/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[9]/div/div/div/div[9]/div[2]/div/div[1]/div[1]/div/div/div/div/div[5]/div/div[2]/input[1]').get_attribute("value")

        # VERIFICA SE O NUMERO MUDOU. CASO SEJA DIFERENTE, SE FOR UM PROCESSO LOCALIZADO ANTERIOMENTE, ACRESCENTA UM NOVO, SE NÃO FOI LOCALIZADO, ALTERA O NUMERO
        # prc_numero_processum = self.driver.find_element_by_xpath('/html/body/form/div/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[9]/div/div/div/div[9]/div[2]/div/div[1]/div[1]/div/div/div/div/div[7]/div/div[2]/input').get_attribute("value")
        prc['prc_numero_processum'] = self.driver.find_element_by_id('ABA_DESD_txtNumeroEdt').get_attribute("value").strip()
        prc['prc_juizo'] = self.driver.find_element_by_id('ABA_DESD_JuizoIDEdt').get_attribute("value").strip()
        prc['prc_comarca'] = self.driver.find_element_by_id('ABA_DESD_BuscaComarcaIDEdt').get_attribute("value").strip()

        prc['prc_numero_processum'] = prc['prc_numero_processum'][:35]

        if dados['prc_numero_processum'] is None or prc['prc_numero_processum'] != dados['prc_numero_processum']:
            acps = Acompanhamento.lista_movs(base, dados['prc_id'], None)
            if len(acps) == 0:
                prc['prc_numero'] = prc['prc_numero_processum']
                prc['prc_projudi'] = None
                prc['prc_esaj'] = None
                prc['prc_pje'] = None
            else:
                prcs = Processo.get_processo_by_numero(base, prc['prc_numero_processum'])
                if len(prcs) == 0:
                    Processo.insert(base, {'prc_numero': prc['prc_numero_processum'], 'prc_estado': dados['prc_estado'], 'prc_autor': dados['prc_autor'], 'prc_pai': dados['prc_id'], 'prc_area': dados['prc_area'], 'prc_carteira': dados['prc_carteira']})
                    prc['prc_numero_antigo'] = prc['prc_numero_processum']

        if dados['prc_numero'] == '0':
            prc['prc_numero'] = prc['prc_numero_processum']

        if 'prc_data_citacao' in prc:
            if prc['prc_data_citacao'].strip() == '':
                del prc['prc_data_citacao']
            else:
                prc['prc_data_citacao'] = datetime.strptime(prc['prc_data_citacao'], '%d/%m/%Y')
                if prc['prc_data_citacao'].year < 1900:
                    prc['prc_data_citacao'] = None

        if 'prc_data' in prc:
            if prc['prc_data'].strip() == '':
                del prc['prc_data']
            else:
                prc['prc_data'] = datetime.strptime(prc['prc_data'], '%d/%m/%Y %H:%M')
                if prc['prc_data'].year < 1900:
                    prc['prc_data'] = None
                else:
                    prc['prc_data_cadastro'] = prc['prc_data']

        if dados['prc_promovido'] is None or len(dados['prc_autor']) < 5:
            if 'prc_promovente' in prc:
                prc['prc_autor'] = prc['prc_promovente'].strip()
            if 'prc_empresa' in prc:
                prc['prc_promovido'] = prc['prc_empresa'].strip()
        else:
            if 'prc_promovente' in prc:
                del prc['prc_promovente']
            if 'prc_cpf_cnpj' in prc:
                del prc['prc_cpf_cnpj']

        if 'prc_modulo' in prc:
            prc['prc_modulo'] = corta_string(prc['prc_modulo'], 50)

        # prc['prc_situacao'] = self.driver.find_element_by_xpath('/html/body/form/div/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[9]/div/div/div/div[2]/div[2]/div/div[4]/div/div[2]/input[1]').get_attribute('value')
        # CLICA EM VALORES/RISCO
        self.driver.find_element_by_xpath('/html/body/form/div/div/div[2]/div[2]/div[2]/div[1]/div/div[1]/div[4]/div/div[4]/em/button').click()
        aguarda_presenca_elemento(self.driver, '//*[@id="tab_PQCVALORES"]/div/div/div/div[1]/div/div[2]/input')
        divs = self.driver.find_elements_by_xpath('//*[@id="tab_PQCVALORES"]/div/div/div/div/div/div/div/div')
        campos = {'Pedido Autor': 'prc_valor_provavel', 'Pedido': 'prc_valor_provavel2'}
        i = 1
        for div in divs:
            i += 1
            label = div.find_element_by_xpath('div[1]').text
            for c in campos:
                if label.upper() == c.upper():
                    txt = div.find_element_by_xpath('div[2]/input').get_attribute("value")
                    prc[campos[c]] = txt
                    break

        if 'prc_valor_provavel' in prc:
            if prc['prc_valor_provavel'] == '':
                prc['prc_valor_provavel'] = prc['prc_valor_provavel2']
            prc['prc_valor_provavel'] = prc['prc_valor_provavel'].replace('.', '').replace(',', '.')
            prc['prc_valor_provavel'] = float(prc['prc_valor_provavel'])

        if 'prc_valor_provavel2' in prc:
            del prc['prc_valor_provavel2']

        # CLICA EM GARANTIAS/PENHORAS
        self.driver.find_element_by_id('colGarantias').click()
        iframe_garantia = self.driver.find_element_by_xpath('//*[@id="panelcategory28"]/iframe')
        self.driver.switch_to_frame(iframe_garantia)
        aguarda_presenca_elemento(self.driver, '//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/div[2]')
        txt_tabela_penhora = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/div[2]')
        # if txt_tabela_penhora and txt_tabela_penhora.text != 'Nenhum registro.':
        #     print('cheguei')

        self.driver.switch_to.default_content()
        iframe_processo = self.detecta_iframe()
        self.driver.switch_to_frame(iframe_processo)

        return prc

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        # partes = {'ativo': [], 'passivo': [], 'terceiro': []}
        nomes = []
        # VAI PARA AS TELA DE DADOS
        self.driver.find_element_by_id('Geral').click()

        # COLETA DADOS PARTE ATIVA
        aguarda_presenca_elemento(self.driver,'/html/body/form/div/div/div[2]/div[2]/div[2]/div[1]/div/div[2]/div[9]/div/div/div/div[7]/div[2]/div/div[1]/div/div[2]/input[1]')

        nome = self.driver.find_element_by_name('Adverso').get_attribute('value')
        cpf_cnpj_ativo = self.driver.find_element_by_name('CLI_CPFCNPJAdverso').get_attribute('value')
        nomes.append(nome)
        if cpf_cnpj_ativo == '':
            cpf_cnpj_ativo = 'Não Informado'

        aux = []
        aux.append({'prt_nome': nome, 'prt_cpf_cnpj': cpf_cnpj_ativo})
        prt_ativo = aux

        # COLETA DADOS PARTE PASSIVA
        aux = []
        # REMOVE O readonly QUE IMPEDE A COLETA DO TEXTO
        lista_WebElementos = self.driver.find_elements_by_tag_name('input')
        for WebElemento in lista_WebElementos:
            self.driver.execute_script("arguments[0].removeAttribute('readonly','readonly')", WebElemento)

        nome_passivo = self.driver.find_element_by_name('Cliente').get_attribute('value')
        nomes.append(nome_passivo)
        cpf_cnpj_passivo = 'Não informado'
        aux.append({'prt_nome': nome_passivo, 'prt_cpf_cnpj': cpf_cnpj_passivo})
        prt_passivo = aux

        partes = {'ativo': prt_ativo, 'passivo': prt_passivo, 'terceiro': []}
        classes = {'Empresa':'ativo', 'Adverso':'passivo', 'Terceiro':'terceiro', }
        # VAI PARA AS TELA DE PARTICIPANTES
        self.driver.find_element_by_id('colParticipantes').click()
        # self.driver.switch_to.default_content()
        iframe_partes = self.driver.find_element_by_xpath('//*[@id="panelcategory8"]/iframe')
        self.driver.switch_to_frame(iframe_partes)
        self.wait_load()

        txt_tabela_partes = self.driver.find_elements_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/div[2]')
        if txt_tabela_partes:
            for txt in txt_tabela_partes:
                if txt.is_displayed() and txt.text == 'Nenhum registro.':
                    self.driver.switch_to.default_content()
                    return partes

        aguarda_presenca_elemento(self.driver, '//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[3]', aguarda_visibilidade=True)
        prts = self.driver.find_elements_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr')
        for prt in prts:
            len_td = prt.find_elements_by_xpath('td/div')
            if len(len_td) > 6:
                continue

            prt_nome = prt.find_elements_by_xpath('td[2]/div')
            if len(prt_nome) == 0:
                continue
            prt_nome = prt_nome[0].text.strip()
            td4 = prt.find_element_by_xpath('td[4]/div').text
            td3 = prt.find_element_by_xpath('td[3]/div').text
            polo = ''

            if td3 in classes:
                polo = classes[td3]

            else:
                if find_string(td4, self.titulo_partes['ignorar']):
                    continue

                if find_string(td4, self.titulo_partes['ativo']):
                    polo = 'ativo'
                if find_string(td4, self.titulo_partes['passivo']):
                    polo = 'passivo'
                if find_string(td4, self.titulo_partes['terceiro']):
                    polo = 'terceiro'

            if polo == '':
                raise MildException("polo vazio " + td4, self.uf, self.plataforma, self.prc_id)

            if prt_nome in nomes:
                continue
            nomes.append(prt_nome)
            partes[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': 'Não Informado'})

        self.driver.switch_to.default_content()
        return partes

    # CAPTURA MOVIMENTAÇÕES DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base, pasta_intermediaria):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        iframe_processo = self.detecta_iframe()
        self.driver.switch_to_frame(iframe_processo)
        # iframe_menu = self.driver.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/iframe')
        # self.driver.switch_to_frame(iframe_menu)

        # CLICA EM ANDAMENTOS
        self.driver.find_element_by_xpath('/html/body/form/div/div/div[2]/div[2]/div[1]/div[2]/div/div/div[2]/div/div[3]/ul/li[5]/a').click()
        self.wait_load()

        # ACESSA O IFRAME DOS ANDAMENTOS
        aguarda_presenca_elemento(self.driver, '/html/body/form/div/div/div[2]/div[2]/div[2]/div[5]/iframe')
        iframe_andamento = self.driver.find_element_by_xpath('/html/body/form/div/div/div[2]/div[2]/div[2]/div[5]/iframe')
        self.driver.switch_to_frame(iframe_andamento)

        self.wait_load()
        txt_tabela_acp = self.driver.find_elements_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/div[2]')
        if txt_tabela_acp:
            for txt in txt_tabela_acp:
                if txt.is_displayed() and txt.text == 'Nenhum registro.':
                    return [], []

        # ultima_mov = proc_data['cadastro']
        # countTenMovi = 0


        try:
            self.driver.maximize_window()
        except:
            pass
        colunas = {}
        inicio = time.time()
        div_scroll = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]')

        while 'Data' not in colunas or colunas['Data'] < 4:
            tempoTotal = time.time() - inicio
            if tempoTotal >= 30:
                raise MildException("Timeout capturando colunas", self.uf, self.plataforma, self.prc_id)
            colunas = {}
            i = 0
            titulos = self.driver.find_elements_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[1]/div/div/div/div')
            for tt in titulos:
                i += 1
                if i == 1:
                    self.driver.execute_script("arguments[0].scrollLeft -= 1000;", div_scroll)
                if i > 5:
                    self.driver.execute_script("arguments[0].scrollLeft += 1000;", div_scroll)
                nome = remove_acentos(tt.text).strip()
                if nome == '':
                    continue

                colunas[nome] = i

        aux = 'de 0'
        i = 0
        while aux == 'de 0' or aux == '':
            i += 1
            if i > 200:
                raise MildException("Erro ao coletar os Andamentos do processo.", self.uf, self.plataforma, self.prc_id)
            aux = self.driver.find_element_by_xpath('/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[3]/div/div/div[6]').text
        quantidade_paginas = int(aux.replace('de ', ''))
        pagina_atual = 0
        # break_while = False
        movs = []
        self.movs = []
        capturar = True
        lista = Acompanhamento.lista_movs(base, proc_data['prc_id'], self.plataforma)
        while pagina_atual < quantidade_paginas:
            self.wait_load()
            pagina_atual += 1
            aguarda_presenca_elemento(self.driver,'//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[2]/td[6]', aguarda_visibilidade=True)
            andamentos = self.driver.find_elements_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr')
            countMovs = 0
            for mov in andamentos:
                countMovs += 1

                while True:
                    try:
                        acp_cadastro = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[' + str(countMovs) + ']/td[2]').text.strip()
                        acp_tipo = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[' + str(countMovs) + ']/td['+str(colunas['Andamento'])+']').text
                        acp_esp = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[' + str(countMovs) + ']/td['+str(colunas['Complementos'])+']').text
                        acp_usuario = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr['+str(countMovs)+']/td['+str(colunas['Responsavel'])+']').text
                        break
                    except:
                        tb = traceback.format_exc()
                        print(tb)
                        pass

                if acp_cadastro == '':
                    continue

                acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y')
                if acp_cadastro > datetime.strptime('01/01/2500', '%d/%m/%Y'):
                    acp_cadastro = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[' + str(countMovs) + ']/td['+str(colunas['Data'])+']').text[:10].strip()
                    acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y')

                if acp_usuario == '':
                    acp_usuario = None

                esp_site = self.trata_string_acp(acp_esp)
                tipo_site = self.trata_string_acp(acp_tipo)
                # VERIFICA SE A MOV É NOVA PRO BANCO
                capturar = True

                for l in lista:
                    esp_base = self.trata_string_acp(l['acp_esp'])
                    tipo_base = self.trata_string_acp(l['acp_tipo'])

                    if acp_cadastro.date() == l['acp_cadastro'].date() and esp_site.upper() == esp_base.upper():
                        if tipo_base == tipo_site:
                            capturar = False
                            break

                if capturar:
                    movs.append({'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': acp_tipo, 'acp_usuario': acp_usuario})

                self.movs.append({'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': acp_tipo, 'acp_usuario': acp_usuario})

            # if break_while or len(lista) > 0:
            # if len(lista) > 0:
            #     break
            # PASSA PARA A PROXIMA PAGINA DE ANDAMENTOS
            if quantidade_paginas > 1:
                self.driver.find_element_by_xpath('/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[3]/div/div/div[8]/em/button').click()

        arquivos = []
        return movs, arquivos

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        self.driver.switch_to.default_content()
        # ACESSA O IFRAME DAS AUDIENCIAS
        iframe_processo = self.detecta_iframe()
        self.driver.switch_to_frame(iframe_processo)

        # aguarda_presenca_elemento(self.driver, '/html/body/div[2]/div/div[2]/div/iframe')
        # iframe_audiencia = self.driver.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/iframe')
        # self.driver.switch_to_frame(iframe_audiencia)

        self.wait_load()
        # CLICA EM Providências
        self.driver.find_element_by_xpath('/html/body/form/div/div/div[2]/div[2]/div[1]/div[2]/div/div/div[2]/div/div[3]/ul/li[6]/a').click()
        self.wait_load()
        adcs = []

        # ACESSA O IFRAME DA TABELA
        aguarda_presenca_elemento(self.driver, '/html/body/form/div/div/div[2]/div[2]/div[2]/div[6]/iframe')
        iframe_audiencia = self.driver.find_element_by_xpath('/html/body/form/div/div/div[2]/div[2]/div[2]/div[6]/iframe')
        self.driver.switch_to_frame(iframe_audiencia)

        nr = False
        self.wait_load()
        txt_tabela_providencias = self.driver.find_element_by_xpath('//*[@id="tabCt_0"]/div/div/div/div/div[1]/div/div[2]/div/div[2]/div[2]')
        if txt_tabela_providencias:
            if txt_tabela_providencias.text == 'Nenhum registro.':
                self.driver.switch_to.default_content()
                self.driver.find_element_by_xpath('/html/body/div/div/div[1]/div/div[2]/div/div').click()
                nr = True
                # return []

        if not nr:
            aguarda_presenca_elemento(self.driver, '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr')
            audiencias = self.driver.find_elements_by_xpath('/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr')
            for mov in audiencias:
                date_full = mov.find_element_by_xpath('td[4]').text

                if date_full == '':
                    continue

                prp_data = datetime.strptime(date_full, '%d/%m/%Y %H:%M')

                prp_status = mov.find_element_by_xpath('td[5]').text

                prp_tipo = mov.find_element_by_xpath('td[2]').text

                adcs.append({'adc_data': prp_data, 'adc_status': prp_status, 'adc_tipo': prp_tipo, 'adc_data_cadastro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

            self.driver.switch_to.default_content()
            # aguarda_presenca_elemento(self.driver,'/html/body/div[2]/div/div[1]/div/div[2]/div/div')
            self.driver.find_element_by_xpath('/html/body/div/div/div[1]/div/div[2]/div/div').click()

        for m in self.movs:
            esp = m['acp_esp'].upper()
            if esp.find('AGENDADA PARA') > -1 and esp.find('AUDIÊNCIA') == 0:
                dia = localiza_data(esp, True)
                if not dia:
                    continue

                try:
                    adc_data = datetime.strptime(dia, '%Y-%m-%d %H:%M')
                except:
                    continue

                adc_tipo = 'Audiência'
                for tipo in dados_audiencia['tipo']:
                    b = esp.find(tipo.upper())
                    if b > -1:
                        adc_tipo = tipo
                        break

                adc = {'adc_data': adc_data, 'adc_status': 'Designada', 'adc_tipo': adc_tipo,
                             'adc_data_cadastro': m['acp_cadastro']}

                achei = False
                for a in adcs:
                    if a['adc_data'] == adc_data:
                        achei = True
                        break

                if achei:
                    continue

                adcs.append(adc)

        return adcs

    def trata_string_acp(self, texto):
        if texto is None:
            return ''

        texto = strip_html_tags(texto)
        texto = texto.replace('"', '').replace("'", '')
        texto = " ".join(texto.split())
        return corta_string(texto, 200).upper()
