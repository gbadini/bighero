from Controllers.Tribunais.Fisico._fisico import *
import urllib.parse as urlparse
from urllib.parse import parse_qs
from selenium.webdriver.common.action_chains import ActionChains

# CLASSE DA VARREDURA DO FISICO DA BA. HERDA OS METODOS DA CLASSE FISICO
class BA(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.pagina_busca = "http://www2.tjba.jus.br/consultaprocessual/consulta.wsp"
        self.pagina_processo = "http://www2.tjba.jus.br/consultaprocessual/primeirograu/numero.wsp?parametro="
        self.url = {}

    # FAZ O LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        return True

    # REALIZA A BUSCA DO PROCESSO. RETORNA TRUE SE LOCALIZAR, FALSE SE NÃO
    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        # if self._consultas:
        #     self.driver.find_element_by_xpath('/html/body/form[1]/table/tbody/tr/td[2]/a[1]/img').click()
        aguarda_presenca_elemento(self.driver, 'tmp.p1', tipo='ID')
        self.driver.find_element_by_id('tmp.p1').send_keys(numero_busca)

        captcha = self.driver.find_element_by_xpath('/html/body/form/table[3]/tbody/tr/td/input')
        captcha.click()
        while True:
            if len(captcha.get_attribute('value')) == 4:
                self.driver.find_element_by_id('consultar').click()
                if aguarda_alerta(self.driver):
                    captcha = self.driver.find_element_by_xpath('/html/body/form/table[3]/tbody/tr/td/input')
                    captcha.clear()
                    captcha.click()
                    continue
                else:
                    break

        while True:
            existencia = self.driver.find_elements_by_xpath('/html/body/form/table[1]/tbody/tr/td')
            if existencia and 'Inexistente' in existencia[0].text:
                return False

            existencia = self.driver.find_elements_by_xpath('/html/body/table[2]/tbody/tr/td[2]')
            if existencia:
                break

        # self._consultas = True
        return True

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        acp_esp = self.driver.find_element_by_xpath('/html/body/center/table/tbody/tr[2]/td[4]').text
        acp_esp = strip_html_tags(acp_esp).strip()
        acp_cad = self.driver.find_element_by_xpath('/html/body/center/table/tbody/tr[2]/td[1]').text
        acp_tipo = strip_html_tags(self.driver.find_element_by_xpath('/html/body/center/table/tbody/tr[2]/td[2]').text).strip()
        if acp_esp == '':
            acp_esp = acp_tipo

        acp_cadastro = datetime.strptime(acp_cad + ' 00:00:00', '%d/%m/%Y %H:%M:%S')
        return Acompanhamento.compara_mov(base, prc_id, acp_esp, acp_cadastro, self.plataforma, self.grau, rec_id=self.rec_id)

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        aguarda_presenca_elemento(self.driver,'/html/body/table[2]/tbody/tr/td[2]')
        el = self.driver.find_element_by_xpath('/html/body/table[2]/tbody/tr/td[2]')
        if el:
            numero_site = ajusta_numero(el.text)
            if numero_busca == numero_site:
                return True

        raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)

    # CAPTURAR MOVIMENTAÇÕES DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        prc_id = proc_data['prc_id']
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None
        movs = []
        self.movs = []
        self.url = self.driver.execute_script('return window.location')
        # BUSCA MOVIMENTAÇÕES DO PROCESSO NA BASE
        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)
        capturar = True
        fim = False
        i = 0
        while True:
            linhas = self.driver.find_elements_by_xpath('/html/body/center/table/tbody/tr')
            linhas.pop(0)
            for linha in linhas:
                i += 1
                acp_cadastro = linha.find_element_by_xpath('td[1]').text
                acp_cadastro = datetime.strptime(acp_cadastro + ' 00:00:00', '%d/%m/%Y %H:%M:%S')
                acp_esp = strip_html_tags(linha.find_element_by_xpath('td[4]').text).strip()
                acp_tipo = strip_html_tags(linha.find_element_by_xpath('td[2]').text).strip()
                if acp_esp == '':
                    acp_esp = acp_tipo
                mov = {
                    'acp_cadastro': acp_cadastro,
                    'acp_esp': acp_esp,
                    'acp_tipo': acp_tipo,
                }

                if completo:
                    capturar = True

                esp_site = corta_string(mov['acp_esp'])
                for l in lista:
                    esp_base = corta_string(l['acp_esp'])

                    if acp_cadastro == l['acp_cadastro'] and esp_site == esp_base:
                        capturar = False
                        break

                if not capturar and not completo and i >= 10:
                    fim = True
                    break

                if capturar:
                    movs.append(mov)

                self.movs.append({**mov, 'novo': capturar})

            if fim:
                break

            next_page = self.driver.find_element_by_partial_link_text('Próximo')
            if not next_page:
                break

            next_page.click()

        return movs

    # CAPTURAR DADOS ESPECIFICADOS NO DICT
    def dados(self, status_atual):
        prc = {}

        campos = {'Numeração Única:': 'prc_numero2', 'Comarca': 'prc_comarca2', 'Data Entrada': 'prc_distribuicao', 'Órgão Judicial': 'prc_serventia'}

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)

        tables = self.driver.find_elements_by_xpath('/html/body/table')
        for table in tables:
            trs = table.find_elements_by_xpath('tbody/tr')
            for tr in trs:
                tds = tr.find_elements_by_tag_name('td')
                i = 0
                for td in tds:
                    i += 1
                    if i % 2 == 0 or len(tds) < i+1:
                        continue

                    for c in campos:
                        if td.text.upper().find(c.upper()) > -1:
                            prc[campos[c]] = tds[i].text.strip()
                            break

        if 'prc_distribuicao' in prc:
            if prc['prc_distribuicao'] == '':
                del prc['prc_distribuicao']
            else:
                prc['prc_distribuicao'] = datetime.strptime(prc['prc_distribuicao'], '%d/%m/%Y')

        parsed = urlparse.urlparse(self.url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        if 'parametro' in url_params:
            prc['prc_codigo'] = url_params['parametro'][0]

        return prc

    # CAPTURA AS PARTES ENVOLVIDAS (REU, AUTOR, AGRAVANTE, AGRAVADO, RECLAMANTE, RECLAMADA, ETC).
    def partes(self):
        prts = {'ativo': [], 'passivo': [], 'terceiro': []}

        parts = self.driver.find_elements_by_xpath('/html/body/table[6]/tbody/tr')
        parts.pop(0)
        for part in parts:
            nome = part.find_element_by_xpath('td[1]').text
            f = nome.find('\n')
            prt_nome = nome[:f].strip()
            tipo = nome[f:].strip()
            if find_string(tipo,self.titulo_partes['ignorar']):
                continue

            polo = ''
            if find_string(tipo, self.titulo_partes['ativo']):
                polo = 'ativo'
            if find_string(tipo, self.titulo_partes['passivo']):
                polo = 'passivo'
            if find_string(tipo, self.titulo_partes['terceiro']):
                polo = 'terceiro'

            if polo == '':
                raise FatalException("polo vazio " + nome, self.uf, self.plataforma, self.prc_id)

            prts[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': 'Não Informado'})

        return prts

    # CAPTURA OS ADVOGADOS DE AMBAS AS PARTES
    def responsaveis(self):
        advs = []

        parts = self.driver.find_elements_by_xpath('/html/body/table[6]/tbody/tr')
        parts.pop(0)
        for part in parts:
            nome = part.find_element_by_xpath('td[1]').text
            f = nome.find('\n')
            tipo = nome[f:].strip()
            if find_string(tipo, self.titulo_partes['ignorar']) or find_string(tipo, self.titulo_partes['terceiro']):
                continue

            polo = ''
            if find_string(tipo, self.titulo_partes['ativo']):
                polo = 'Polo Ativo'

            if find_string(nome, self.titulo_partes['passivo']):
                polo = 'Polo Passivo'

            advogados = part.find_element_by_xpath('td[2]').text.split('\n')

            for advogado in advogados:
                dados = advogado.split('(')
                if len(dados) == 1:
                    continue

                adv = {
                    'prr_nome': dados[0],
                    'prr_oab': dados[1][:-1],
                    'prr_cargo': 'Advogado',
                    'prr_parte': polo,
                }
                advs.append(adv)

        return advs

