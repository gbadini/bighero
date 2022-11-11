from Controllers.Tribunais.Fisico._fisico import *
import urllib.parse as urlparse
from urllib.parse import parse_qs

# CLASSE DA VARREDURA DO FISICO DO ES. HERDA OS METODOS DA CLASSE FISICO
class ES(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.pagina_busca = "http://aplicativos.tjes.jus.br/sistemaspublicos/consulta_12_instancias/consulta_proces.cfm"
        self.pagina_processo = ""
        # self.pagina_processo = "https://cache-internet.tjdft.jus.br/cgi-bin/tjcgi1?NXTPGM=tjhtml105&SELECAO=1&ORIGEM=INTER&CIRCUN="
        self.formato_data = '%d/%m/%Y'
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
        self.driver.find_element_by_id('edNumProcesso').clear()
        self.driver.find_element_by_id('edNumProcesso').send_keys(numero_busca)
        # self.driver.find_element_by_id('edNumProcesso').send_keys(Keys.ENTER)
        captcha = self.driver.find_element_by_xpath('/html/body/table/tbody/tr[2]/td/form/table/tbody/tr[7]/td/div/div/div/iframe')
        if not captcha:
            self.driver.find_element_by_id('edNumProcesso').send_keys(Keys.ENTER)

        wh = self.driver.window_handles
        while len(wh) == 1:
            wh = self.driver.window_handles

        self.alterna_janela()
        msg_erro = self.driver.find_element_by_xpath('//*[@id="conteudo"]/table/tbody/tr[2]/td')
        if msg_erro:
            if msg_erro.text.find('Nenhum PROCESSO encontrado') > -1:
                return False

        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        aguarda_presenca_elemento(self.driver, '//*[@id="conteudo"]/table/tbody/tr[4]/td[1]/strong')
        el = self.driver.find_element_by_xpath('//*[@id="conteudo"]/table/tbody/tr[4]/td[1]/strong')
        numero_site = ''
        if el:
            cnj = localiza_cnj(el.text)
            numero_site = ajusta_numero(cnj)
            if numero_busca == numero_site:
                return True

        raise MildException("Número CNJ Diferente - "+numero_site+" "+numero_busca, self.uf, self.plataforma, self.prc_id)

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self, ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        movs = self.driver.find_elements_by_class_name('andamentos')
        spans = movs[0].find_elements_by_xpath('td[1]/span')
        acp_cadastro = spans[0].text.strip()
        acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y')

        acp_tipo = spans[1].text.strip()

        acp_esp = ''
        if len(spans) > 2:
            for s in spans[2:]:
                acp_esp = s.text.strip() + ' '

            acp_esp = acp_esp.strip()

        if acp_esp == '':
            acp_esp = acp_tipo

        return Acompanhamento.compara_mov(base, prc_id, acp_esp, acp_cadastro, self.plataforma, self.grau, rec_id=self.rec_id)

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        prc_id = proc_data['prc_id']
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None
        self.movs = []
        movs = []

        # BUSCA MOVIMENTAÇÕES DO PROCESSO NA BASE
        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)

        movimentos = self.driver.find_elements_by_class_name('andamentos')

        if len(movimentos) == 0:
            raise MildException("Erro ao capturar movimentações", self.uf, self.plataforma, self.prc_id, False)

        capturar = True
        i = 0
        for mov in movimentos:
            i += 1

            spans = mov.find_elements_by_xpath('td[1]/span')
            acp_cadastro = spans[0].text.strip()
            acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y')

            acp_tipo = spans[1].text.strip()

            acp_esp = ''
            if len(spans) > 2:
                for s in spans[2:]:
                    acp_esp = s.text.strip() + ' '

                acp_esp = acp_esp.strip()

            if acp_esp == '':
                acp_esp = acp_tipo


            if completo:
                capturar = True

            esp_site = corta_string(acp_esp)
            for l in lista:
                esp_base = corta_string(l['acp_esp'])

                if acp_cadastro == l['acp_cadastro'] and esp_site == esp_base:
                    capturar = False
                    break

            if not capturar and not completo and i >= 10:
                break

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

            if f != 0:
                continue

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

        trs = self.driver.find_elements_by_xpath('//*[@id="conteudo"]/table/tbody/tr')
        campos = {'Valor :': 'prc_valor_causa', 'Ação :': 'prc_classe', 'Vara :': 'prc_serventia', 'Data :': 'prc_distribuicao', 'Processo :': 'prc_numero2' }

        i = 1
        fim = False
        for tr in trs:
            tds = tr.find_elements_by_tag_name('td')
            for td in tds:
                if td.text.find('Partes do Processo') > -1:
                    fim = True
                    break

                for c in campos:
                    if td.text.upper().find(c.upper()) > -1:
                        txt = td.find_element_by_tag_name('strong').text

                        if campos[c] in prc:
                            prc[campos[c]] += ' ' + txt
                        else:
                            prc[campos[c]] = txt
                        break

            if fim:
                break

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)
        prc['prc_comarca2'] = localiza_comarca(prc['prc_serventia'], self.uf)

        if 'prc_distribuicao' in prc:
            prc['prc_distribuicao'] = datetime.strptime(prc['prc_distribuicao'], '%d/%m/%Y %H:%M')

        return prc

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': [], 'terceiro': []}

        html = ''
        trs = self.driver.find_elements_by_xpath('//*[@id="conteudo"]/table/tbody/tr')
        for i, tr in enumerate(trs):
            if tr.text.find('Partes do Processo') > -1:
                html = trs[i+1].get_attribute('innerHTML').strip().split('<b>')
                break

        nomes = []
        for b in html:
            if len(b) < 50:
                continue
            f = b.find('</b>')
            tipo = b[:f]

            if find_string(tipo,('Recorrente','Recorrido',)):
                continue

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
                # print("polo vazio "+tipo)
                # time.sleep(9999)
                raise MildException("polo vazio "+tipo, self.uf, self.plataforma, self.prc_id)

            brs = b[f:].split('<br>')
            for br in brs:
                if br.count('&nbsp') > 3:
                    continue

                txt = strip_html_tags(br)
                prt_nome = txt.strip()
                if prt_nome == '':
                    continue

                if prt_nome in nomes:
                    continue
                nomes.append(prt_nome)

                partes[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': 'Não Informado'})

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        html = ''
        trs = self.driver.find_elements_by_xpath('//*[@id="conteudo"]/table/tbody/tr')
        for i, tr in enumerate(trs):
            if tr.text.find('Partes do Processo') > -1:
                html = trs[i+1].get_attribute('innerHTML').strip().split('<b>')
                break

        nomes = []
        for b in html:
            if len(b) < 50:
                continue

            f = b.find('</b>')
            tipo = b[:f]

            if find_string(tipo,('Recorrente','Recorrido',)):
                continue

            if find_string(tipo,self.titulo_partes['ignorar']):
                continue
            if find_string(tipo,self.titulo_partes['terceiro']):
                continue

            polo = ''
            if find_string(tipo,self.titulo_partes['ativo']):
                polo = 'Polo Ativo'
            if find_string(tipo,self.titulo_partes['passivo']):
                polo = 'Polo Passivo'

            brs = b[f:].split('<br>')
            for br in brs:
                if br.count('&nbsp') < 4:
                    continue

                txt = strip_html_tags(br)
                f = txt.find('-')
                prr_nome = txt[f+2:].strip()

                if prr_nome == '' or prr_nome == 'INEXISTENTE':
                    continue

                if prr_nome in nomes:
                    continue
                nomes.append(prr_nome)

                prr_oab = txt[:f]

                resps.append({'prr_nome': prr_nome, 'prr_oab': prr_oab.strip(), 'prr_cargo': 'Advogado', 'prr_parte': polo})

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