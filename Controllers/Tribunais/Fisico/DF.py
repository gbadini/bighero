from Controllers.Tribunais.Fisico._fisico import *
import urllib.parse as urlparse
from urllib.parse import parse_qs

# CLASSE DA VARREDURA DO FISICO DO DF. HERDA OS METODOS DA CLASSE FISICO
class DF(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.pagina_busca = "https://www.tjdft.jus.br/consultas/processuais/1a-instancia"
        self.pagina_processo = "https://cache-internet.tjdft.jus.br/cgi-bin/tjcgi1?NXTPGM=tjhtml105&SELECAO=1&ORIGEM=INTER&CIRCUN="
        self.formato_data = '%d/%m/%Y - %H:%M:%S'
        self.tratar_tamanhos = True

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        prc = self.dados(status_atual)
        prt = self.partes()
        adv = self.responsaveis()

        return adc, prt, prc, adv

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        self.driver.find_element_by_id('chave').clear()
        self.driver.find_element_by_id('chave').send_keys(numero_busca)
        self.driver.find_element_by_id('chave').send_keys(Keys.ENTER)

        self.alterna_janela()
        msg_erro = self.driver.find_element_by_xpath('/html/body/font[1]')
        if msg_erro:
            if msg_erro.text.find('0 processo(s) localizado(s)') > -1:
                return False

        procs = self.driver.find_elements_by_xpath('/html/body/font[2]/ul/table/tbody/tr/td[1]/li/a')
        if len(procs) > 0:
            achei = False
            for prc in procs:
                numero_site = prc.text.replace('.','').replace('-','')
                if numero_site == numero_busca:
                    prc.click()
                    achei = True
                    break

            if not achei:
                return False

        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''

        aguarda_presenca_elemento(self.driver, 'i_numeroProcesso20', tipo='ID')
        el = self.driver.find_element_by_id('i_numeroProcesso20')
        el2 = self.driver.find_element_by_id('i_numeroProcesso14')
        numero_site = ''
        numero_site2 = ''
        if el:
            cnj = localiza_cnj(el.text)
            numero_site = ajusta_numero(cnj)
            nro_antigo = el2.text
            numero_site2 = nro_antigo.replace('.','').replace('-','')

            if numero_busca == numero_site or numero_busca == numero_site2:
                return True

        raise MildException("Número CNJ Diferente - "+numero_site+" "+numero_busca, self.uf, self.plataforma, self.prc_id)

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self, ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        dia = self.driver.find_element_by_xpath('//*[@id="i_competencia"]/table/tbody/tr[4]/td[1]/font/b/span').text

        data_tj = datetime.strptime(dia.strip(), self.formato_data)
        if ultima_data == data_tj:
            return True

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

        movimentos = self.driver.find_elements_by_xpath('//*[@id="i_competencia"]/table/tbody/tr')

        if len(movimentos) == 0:
            raise MildException("Erro ao capturar movimentações", self.uf, self.plataforma, self.prc_id, False)

        capturar = True
        i = 0
        for mov in movimentos:
            i += 1

            tds = mov.find_elements_by_tag_name('td')

            acp_cadastro = tds[0].text.strip()
            if acp_cadastro == '' or acp_cadastro == 'Data':
                continue

            try:
                acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y - %H:%M:%S')
            except:
                acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y')

            if acp_cadastro == ultima_mov:
                capturar = False
                if not completo and i >= 10:
                    break

            acp_tipo = tds[1].text
            acp_esp = ''
            if len(tds) > 2:
                acp_esp = tds[2].text
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

            tipo = mov['acp_tipo'].upper().strip()
            tipo = tipo.replace('Ê','E')

            f = tipo.find('AUDIENCIA')
            f2 = tipo.find('248 - ')

            if f2 == -1 and f != 0:
                continue

            if f2 > -1:
                tipo = tipo[f2:].strip()

            aud_txt = mov['acp_tipo'].upper().strip()+" "+mov['acp_esp'].upper().strip()

            aud = localiza_audiencia(aud_txt, formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
            if not aud:
                continue

            if 'prp_status' not in aud:
                aud['prp_status'] = 'Designada'

            if 'prp_tipo' not in aud:
                # print("Audiência - Tipo não localizado: "+tipo)
                # time.sleep(9999)
                raise MildException("Audiência - Tipo não localizado: "+tipo, self.uf, self.plataforma, self.prc_id)

            aud['data_mov'] = mov['acp_cadastro']
            adcs.append(aud)

        return adcs

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        '''
        :param str status_atual: Status atual
        '''
        prc = {}

        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        prc['prc_codigo'] = '&CIRCUN='+url_params['CIRCUN'][0]+'&CDNUPROC='+url_params['CDNUPROC'][0]

        prc['prc_numero2'] = self.driver.find_element_by_id('i_numeroProcesso20').text

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)

        circunscricao = self.driver.find_element_by_id('i_nomeCircunscricao').text
        f = circunscricao.find('-')
        if f > -1:
            circunscricao = circunscricao[f:]
        prc['prc_serventia'] = circunscricao
        prc['prc_comarca2'] = localiza_comarca(prc['prc_serventia'], self.uf)

        # prc['prc_vara'] = self.driver.find_element_by_id('i_descricaoVara').text

        prc_distribuicao = self.driver.find_element_by_id('i_dataDistribuicao').text
        prc['prc_distribuicao'] = datetime.strptime(prc_distribuicao, '%d/%m/%Y')

        prc['prc_assunto'] = self.driver.find_element_by_id('i_assuntoProcessual').text
        prc['prc_valor_causa'] = self.driver.find_element_by_id('i_valorCausa').text

        return prc

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': []}

        self.driver.find_element_by_partial_link_text('Consulta Advogados das Partes').click()
        # self.driver.find_element_by_xpath('//*[@id="i_competencia"]/p[1]/b[4]/a').click()
        # self.alterna_janela()

        html = self.driver.find_element_by_xpath('/html/body').get_attribute('innerHTML').strip().split('<br>')
        html = html[3:-1]
        for p in html:
            if p.lower().find('advogado') > -1:
                continue

            txt = strip_html_tags(p)

            if txt == '':
                continue

            pontos = txt.find(':')
            if pontos == -1:
                continue
            tipo = txt[:pontos]
            polo = ''
            if find_string(tipo,self.titulo_partes['ignorar']):
                continue

            if find_string(tipo,self.titulo_partes['ativo']):
                polo = 'ativo'
            if find_string(tipo,self.titulo_partes['passivo']):
                polo = 'passivo'

            if polo == '':
                # print("polo vazio "+tipo)
                # time.sleep(999)
                raise MildException("polo vazio "+tipo, self.uf, self.plataforma, self.prc_id)

            prt_nome = txt[pontos+1:]
            partes[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': 'Não Informado'})

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        ultimo_polo = ''
        html = self.driver.find_element_by_xpath('/html/body').get_attribute('innerHTML').strip().split('<br>')
        html = html[3:-1]

        for p in html:

            txt = p.replace('<b>', '').replace('</b>', '')

            pontos = txt.find(':')
            tipo = txt[:pontos]
            if find_string(tipo, self.titulo_partes['ativo']):
                ultimo_polo = 'Polo Ativo'
            if find_string(tipo, self.titulo_partes['passivo']):
                ultimo_polo = 'Polo Passivo'

            if p.upper().find('ADVOGADO') == -1 or p.upper().find('NAO CONSTA') > -1:
                continue

            prr_nome = txt[pontos+1:]
            resps.append({'prr_nome': prr_nome.strip(), 'prr_cargo': 'Advogado', 'prr_parte': ultimo_polo})


        return resps

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