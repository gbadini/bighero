from Controllers.Tribunais.Ppe._ppe import *
from selenium.webdriver.support.ui import Select

# CLASSE DA VARREDURA DO EPROC DO RS. HERDA OS METODOS DA CLASSE EPROC
class SE(Ppe):
    def __init__(self):
        super().__init__()
        self.movs = []
        self.apagar_partes_inexistentes = True
        self.tratar_tamanhos = False
        self.pagina_inicial = "https://www.tjse.jus.br/portaldoadvogado/"
        self.reiniciar_navegador = False

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        prc = self.dados(status_atual)
        prt = self.partes()
        adv = self.responsaveis()

        return adc, prt, prc, adv

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        if not aguarda_presenca_elemento(self.driver, 'tmp_oab', tipo='ID'):
            return False

        num, digito = usuario.split()

        select_letter = Select(self.driver.find_element_by_name('tmp_letra'))
        select_letter.select_by_value(digito.upper())

        num_field = self.driver.find_element_by_id('tmp_oab')
        num_field.send_keys(num)

        password = self.driver.find_element_by_id('tmp_senha_formulario')
        password.send_keys(senha)

        captcha = self.driver.find_element_by_id('tmp_captcha_formulario')
        captcha.click()
        while True:
            if len(captcha.get_attribute('value')) == 6:
                self.driver.find_element_by_id('botaoLogin').click()
                time.sleep(1)
                try:
                    alert = self.driver.switch_to_alert()
                    alert.accept()
                    captcha.clear()
                    time.sleep(1)
                    continue
                except:
                    break

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''

        self.driver.execute_script('window.open("https://www.tjse.jus.br/tjnet/portaladv/consultas/numProcessoUnico.wsp", "mainFrame");')

        aguarda_presenca_elemento(self.driver, 'downFrame', tipo='NAME')
        self.driver.switch_to.frame('downFrame')
        self.driver.switch_to.frame('mainFrame')

        aguarda_presenca_elemento(self.driver, 'tmp.sequencial', tipo='ID')

        field = self.driver.find_element_by_id('tmp.sequencial')
        field.clear()
        field.send_keys(numero_busca[:7])

        field = self.driver.find_element_by_id('tmp.digito')
        field.clear()
        field.send_keys(numero_busca[7:9])

        field = self.driver.find_element_by_id('tmp.ano')
        field.clear()
        field.send_keys(numero_busca[9:13])

        field = self.driver.find_element_by_id('tmp.origem')
        field.clear()
        field.send_keys(numero_busca[-4:])

        self.driver.find_element_by_xpath('//button[text()="Enviar"]').click()

        # time.sleep(1)
        text = self.driver.find_element_by_name('formulario').text

        if 'Nenhum Processo foi encontrado' in text:
            return False

        self.driver.find_element_by_xpath('/html/body/div[2]/form/center/table/tbody/tr[2]/td[1]/a').click()
        self.alterna_janela()
        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''

        tables = self.driver.find_elements_by_xpath('/html/body/form/table')
        for table in tables:
            loc = table.find_elements_by_xpath('thead/tr/th')
            if loc:
                if loc[0].text == 'Dados do Processo:':
                    td = table.find_element_by_xpath('tbody/tr/td[1]').text
                    break

        n1 = localiza_cnj(td)
        n1 = ajusta_numero(n1)
        if n1 != numero_busca:
            raise MildException("CNJ diferente na busca", self.uf, self.plataforma, self.prc_id, False)

        return True

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        self.confere_cnj(numero_busca)

        return False

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        dia = self.driver.find_element_by_xpath('//*[@id="movimentos-processo"]/tbody/tr[2]/td[1]').text

        data_tj = datetime.strptime(dia.strip(), '%d/%m/%Y %H:%M:%S')
        return ultima_data == data_tj

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        movs = []
        ultima_mov = proc_data['cadastro']
        movimentos = self.driver.find_elements_by_xpath('//*[@id="movimentos-processo"]/tbody/tr')
        movimentos.pop(0)

        capturar = True
        i = 0
        for mov in movimentos:
            i += 1
            acp_cadastro = mov.find_element_by_xpath('td[1]').text
            acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y %H:%M:%S')
            if acp_cadastro == ultima_mov:
                capturar = False
                if not completo and i >= 10:
                    break

            acp_tipo = mov.find_element_by_xpath('td[2]').text
            acp_esp = strip_html_tags(mov.find_element_by_xpath('td[3]').text)
            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': acp_tipo}
            if capturar:
                movs.append(acp)

            self.movs.append({**acp, 'novo': capturar})

        return movs

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []
        for mov in self.movs:
            if not self.completo and not mov['novo']:
                break

            esp = mov['acp_esp'].upper().strip()
            tipo = mov['acp_tipo'].upper().strip()

            if esp.find('PARA QUE SEJA REALIZADA AUDIÊNCIA') == -1:
                if tipo.find('AUDIÊNCIA') != 0:
                    continue

            esp = esp.replace('H:',':')
            aud = localiza_audiencia(esp, formato_data='%d/%m/%Y %H:%M', formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(ÀS)(\\s+)(\\d+)(\\:)(\\d+)', reverse=True)
            if not aud:
                continue

            erro = ''
            if 'prp_status' not in aud:
                erro = 'Status '
            if 'prp_tipo' not in aud:
                erro = 'Tipo '

            if erro != '':
                raise MildException("Audiência - "+erro+" não localizado: "+esp, self.uf, self.plataforma, self.prc_id)

            aud['data_mov'] = mov['acp_cadastro']
            adcs.append(aud)

        return adcs

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        prts = {'ativo':[], 'passivo':[], 'terceiro':[]}

        tables = self.driver.find_elements_by_xpath('/html/body/form/table')
        for table in tables:
            loc = table.find_elements_by_xpath('thead/tr/th')
            if loc:
                if loc[0].text == 'Partes do Processo:':
                    partes = table.find_elements_by_xpath('tbody/tr')
                    partes.pop(0)
                    break

        for parte in partes:
            tipo = parte.find_element_by_xpath('td[1]').text
            if find_string(tipo,self.titulo_partes['ignorar']):
                continue

            polo = ''
            if find_string(tipo,self.titulo_partes['ativo']):
                polo = 'ativo'
            if find_string(tipo,self.titulo_partes['passivo']):
                polo = 'passivo'
            if find_string(tipo,self.titulo_partes['terceiro']):
                polo = 'terceiro'

            if polo == '':
                raise MildException("polo vazio "+tipo, self.uf, self.plataforma, self.prc_id)

            prr_nome = parte.find_element_by_xpath('td[2]').text
            prts[polo].append({'prt_nome': prr_nome, 'prt_cpf_cnpj': 'Não Informado'})


        return prts


    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        tables = self.driver.find_elements_by_xpath('/html/body/form/table')
        for table in tables:
            loc = table.find_elements_by_xpath('thead/tr/th')
            if loc:
                if loc[0].text == 'Partes do Processo:':
                    partes = table.find_elements_by_xpath('tbody/tr')
                    partes.pop(0)
                    break

        for parte in partes:
            tipo = parte.find_element_by_xpath('td[1]').text
            if find_string(tipo,self.titulo_partes['ignorar']):
                continue
            if find_string(tipo,self.titulo_partes['terceiro']):
                continue

            polo = ''
            if find_string(tipo,self.titulo_partes['ativo']):
                polo = 'Polo Ativo'
            if find_string(tipo,self.titulo_partes['passivo']):
                polo = 'Polo Passivo'

            if polo == '':
                raise MildException("polo vazio "+tipo, self.uf, self.plataforma, self.prc_id)

            td3 = parte.find_elements_by_xpath('td[3]')
            if len(td3) == 0:
                continue

            advogados = td3[0].text
            advogados = advogados.split('\n')
            advogados = [advogado.split(':') for advogado in advogados]
            advogados = [dado for dado in advogados if dado != 'Advogado']
            for advogado in advogados:
                if advogado[0] == '':
                    continue

                prr_nome = advogado[1][:advogado[1].find('-')].strip()
                prr_oab = advogado[1][advogado[1].find('-') + 1:].strip()
                resps.append({'prr_nome': prr_nome, 'prr_oab': prr_oab, 'prr_cargo': 'Advogado', 'prr_parte': polo})


        return resps

     # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        '''
        :param str status_atual: Status atual
        '''
        prc = {}

        campos = {'Competência': 'prc_juizo', 'Classe': 'prc_classe', 'Segredo de Justiça': 'prc_segredo', 'Fase': 'prc_fase', 'Distribuido': 'prc_distribuicao', 'Valor da Causa': 'prc_valor_causa', 'Número Único': 'prc_numero2'}

        tables = self.driver.find_elements_by_xpath('/html/body/form/table')
        for table in tables:
            loc = table.find_elements_by_xpath('thead/tr/th')
            if loc:
                if loc[0].text == 'Dados do Processo:':
                    table = table.find_elements_by_xpath('tbody/tr')
                    break

        for tr in table:
            tds = tr.find_elements_by_tag_name('td')

            for td in tds:
                coluna = td.text
                coluna = coluna.split('\n')
                titulo = ''
                for k, cln in enumerate(coluna):
                    if k % 2 == 0:
                        titulo = cln
                        continue

                    for cmp in campos:
                        if titulo.upper().find(cmp.upper()) > -1:
                            prc[campos[cmp]] = cln.strip()
                            break
        if 'prc_juizo' in prc:
            prc['prc_serventia'] = prc['prc_juizo']
            prc['prc_status'] = get_status(self.movs, status_atual, self.arquiva_sentenca)
            prc['prc_comarca2'] = localiza_comarca(prc['prc_juizo'], self.uf)

        if 'prc_distribuicao' in prc:
            prc['prc_distribuicao'] = datetime.strptime(prc['prc_distribuicao'].strip(), '%d/%m/%Y')

        if 'prc_segredo' in prc:
            prc['prc_segredo'] = False if prc['prc_segredo'].find('NÃO') > -1 else True

        ths = self.driver.find_elements_by_xpath('/html/body/form/table/thead/tr/th')
        i = 0
        for th in ths:
            i += 1
            if th.text.strip() == 'Assuntos:':
                break

        tables = self.driver.find_elements_by_xpath('/html/body/form/table')
        for table in tables:
            loc = table.find_elements_by_xpath('tbody/tr[1]/th')
            if loc:
                if loc[0].text == 'Assuntos:':
                    table = table.find_elements_by_xpath('tbody/tr')
                    table.pop(0)
                    break

        assuntos = []
        for tr in table:
            assuntos.append(tr.text)

        if len(assuntos) > 0:
            prc['prc_assunto'] = ' | '.join(assuntos)

        return prc

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
    def download(self, prc_id, arquivos_base, pendentes, target_dir):
        return []

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def confere_arquivos_novos(self):
        return False
