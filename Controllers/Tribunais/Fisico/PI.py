from Controllers.Tribunais.Fisico._fisico import *
import urllib.parse as urlparse
from urllib.parse import parse_qs

# CLASSE DA VARREDURA DO FISICO DE PE. HERDA OS METODOS DA CLASSE FISICO
class PI(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.pagina_busca = "http://www.tjpi.jus.br/themisconsulta/"
        self.formato_data = '%d/%m/%Y %H:%M:%S'

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        aguarda_presenca_elemento(self.driver, '//*[@id="container"]/div[2]/div[2]', aguarda_visibilidade=True)

        # Remove os dígitos fixos 8.18
        numero_busca = numero_busca[:13] + numero_busca[-4:]

        try:
            # Carrega o nro do processo
            self.driver.find_element_by_id('input-numero-unico').click()
            self.driver.find_element_by_id('input-numero-unico').send_keys(numero_busca)
            self.driver.find_element_by_id('input-numero-unico').send_keys(Keys.ENTER)

        except:
            raise MildException("Erro ao localizar campo de busca", self.uf, self.plataforma, self.prc_id)


        msg = self.driver.find_element_by_id('messages')

        # Sai do sistema quando não existe o processo
        if msg and msg.text.find('Nenhum processo foi encontrado') > -1:
            return False

        msg = self.driver.find_element_by_id('error-numero-unico')

        # Sai do sistema quando não existe o processo
        if msg and msg.is_displayed() and msg.text.find('Número único inválido') > -1:
            return False


        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        numero_site = ''
        ''
        el = self.driver.find_element_by_xpath('//*[@id="container"]/div[2]/div[1]')
        if el:
            cnj = localiza_cnj(el.text)
            numero_site = ajusta_numero(cnj)
            if numero_busca == numero_site:
                return True

        raise MildException("Número CNJ Diferente - "+numero_site+" "+numero_busca, self.uf, self.plataforma, self.prc_id)

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        data_ultima_mov = self.driver.find_element_by_xpath('//*[@id="tab-movimentacoes"]/tr[1]/th').text.strip()
        # data_ultima_mov = movs[0].text.strip()
        data_tj = datetime.strptime(data_ultima_mov, self.formato_data)
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
        movs = []
        self.movs = []
        i = 0
        capturar = True

        # Movimentos antes clicar 'Exibir todas'
        movimentos = self.driver.find_elements_by_xpath('//*[@id="tab-movimentacoes"]/tr')
        len_mov = 0

        btn_more = self.driver.find_element_by_id('btn-more')
        while btn_more:
            btn_more.click()

            self.wait()
            # time.sleep(2)
            # len_mov = len(movimentos)
            btn_more = self.driver.find_element_by_id('btn-more')

        movimentos = self.driver.find_elements_by_xpath('//*[@id="tab-movimentacoes"]/tr')
        for mov in movimentos:
            acp_cadastro = mov.find_elements_by_tag_name('th')
            if len(acp_cadastro) == 0:
                continue

            acp_cadastro = acp_cadastro[0].text.strip()
            acp_cadastro = datetime.strptime(acp_cadastro, self.formato_data)

            i += 1
            if acp_cadastro <= ultima_mov:
                capturar = False
                if not completo and i >= 10:
                    break

            texto = mov.find_element_by_xpath('td/div[1]').get_attribute('innerHTML').split('<br>')

            acp_tipo = texto[0].replace('<strong>', ' ').replace('</strong>', ' ').strip()
            acp_usuario = texto[-1].strip()

            if len(texto) > 2:
                acp_esp = ''
                for t in texto[1:-1]:
                    acp_esp += ' ' + t.strip()
            else:
                acp_esp = acp_tipo

            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp.strip(), 'acp_tipo': acp_tipo}
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
            if esp.find('AUDIÊNCIA') != 0:
                continue

            aud = localiza_audiencia(esp, formato_data='%d-%m-%Y %H:%M', formato_re='(\\d+)(\\-)(\\d+)(\\-)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
            if not aud:
                continue

            erro = ''
            if 'prp_status' not in aud:
                aud['prp_status'] = 'Agendada'
            if 'prp_tipo' not in aud:
                erro = 'Tipo '

            if erro != '':
                raise MildException("Audiência - "+erro+" não localizado: "+esp, self.uf, self.plataforma, self.prc_id)

            aud['data_mov'] = mov['acp_cadastro']
            adcs.append(aud)

        return adcs

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)

        campos = {'Valor da ação': 'prc_valor_causa', 'Comarca': 'prc_comarca2', 'Assuntos': 'prc_assunto', 'Classe Processual': 'prc_classe', 'Data de Abertura': 'prc_distribuicao' }

        trs = self.driver.find_elements_by_xpath('//*[@id="container"]/div[2]/div[2]/table/tbody/tr')
        i = 0
        for tr in trs:
            th = tr.find_element_by_tag_name('th').text
            for c in campos:
                if th.upper().find(c.upper()) > -1:
                    prc[campos[c]] = tr.find_element_by_tag_name('td').text
                    break

        prc['prc_serventia'] = prc['prc_comarca2']
        if 'prc_distribuicao' in prc:
            r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+(\\d+)(\\:)(\\d)(\\:)(\\d))', prc['prc_distribuicao'])
            if r:
                prc_data_transito = r.group(0)
                prc['prc_distribuicao'] = datetime.strptime(prc_data_transito, '%d/%m/%Y')
            else:
                del prc['prc_distribuicao']

        if 'prc_distribuicao' in prc:
            r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)', prc['prc_distribuicao'])
            prc_distribuicao = r.group(0)
            prc['prc_distribuicao'] = datetime.strptime(prc_distribuicao, '%d/%m/%Y')

        prc_numero2 = self.driver.find_element_by_xpath('//*[@id="container"]/div[2]/div[1]').text
        prc_numero2 = localiza_cnj(prc_numero2)
        prc['prc_numero2'] = prc_numero2

        return prc

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': []}
        nomes = []

        tabela = self.driver.find_elements_by_xpath('//*[@id="container"]/div[2]/div[6]/table/tbody/tr')
        for tb in tabela:
            polo = ''
            th = tb.find_element_by_tag_name('th').text

            if find_string(th,self.titulo_partes['ignorar']):
                continue

            if find_string(th,self.titulo_partes['ativo']):
                polo = 'ativo'

            if find_string(th,self.titulo_partes['passivo']):
                polo = 'passivo'

            if polo == '':
                continue

            prt_nome = tb.find_element_by_tag_name('td').text
            prt_cpf_cnpj = 'Não Informado'

            if prt_nome == '':
                continue

            if prt_nome in nomes:
                continue
            nomes.append(prt_nome)

            partes[polo].append({'prt_nome': prt_nome.strip(), 'prt_cpf_cnpj': prt_cpf_cnpj})

        if len(partes['ativo']) == 0 or len(partes['passivo']) == 0:
            print(partes)
            raise MildException("Polo não localizado ", self.uf, self.plataforma, self.prc_id)

        return partes

    # AGUARDA ATÉ QUE A ANIMAÇÃO DE LOADING ESTEJA OCULTA
    def wait(self, tempo=50):
        inicio = time.time()
        while True:
            if time.time() - inicio > tempo:
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id)
            time.sleep(0.5)
            spinner = self.driver.find_element_by_class_name('progress')
            if not spinner:
                break

        return True