from Controllers.Tribunais.Fisico._fisico import *
import urllib.parse as urlparse
from urllib.parse import parse_qs
from selenium.webdriver.support.ui import Select

# CLASSE DA VARREDURA DO FISICO DO MA. HERDA OS METODOS DA CLASSE FISICO
class MA(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.pagina_busca = "https://jurisconsult.tjma.jus.br/#/pg-public-search-form"
        self.pagina_processo = ""

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        adc = self.audiencias()
        prt = self.partes()
        adv = self.responsaveis()
        prc = self.dados(status_atual)

        return adc, prt, prc, adv

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        if not aguarda_presenca_elemento(self.driver, '/html/body/ion-app/ng-component/ion-split-pane/ion-nav/page-pg-public-search-form/ion-content/div[2]/form/ion-list/ion-item[1]/div[1]/ion-toggle/button', tipo='XPATH', aguarda_visibilidade=True):
            raise MildException("Erro ao carregar página de busca", self.uf, self.plataforma, self.prc_id)

        self.format_busca(numero_busca)
        # time.sleep(60)

        achei = False
        while True:
            time.sleep(1)

            # Se o captcha foi digitado errado e aparecer a mensagem de erro, continua no loop
            txt_falha = self.driver.find_element_by_class_name('alert-sub-title')
            if txt_falha:
                if txt_falha.text.find('segredo de justiça') > -1:
                    return True

                if txt_falha.text.find('Captcha incorreto') > -1 or txt_falha.text.find('expirou') > -1 or txt_falha.text.find('formato inválido') > -1:
                    print('captcha errado')
                    btns = self.driver.find_elements_by_class_name('alert-button')
                    btns.reverse()
                    for b in btns:
                        try:
                            b.click()
                            break
                        except:
                            continue

                    self.format_busca(numero_busca)
                    continue

            resultado_busca = self.driver.find_element_by_class_name('alert-title')
            if resultado_busca and resultado_busca.is_displayed():
                print('não localizado')
                if resultado_busca.text.find('Nenhum registro encontrado') > -1:
                    return False

            campo_captcha = self.driver.find_element_by_xpath('/html/body/ion-app/ng-component/ion-split-pane/ion-nav/page-pg-public-search-form/ion-content/div[2]/form/ion-grid/ion-row/ion-col[2]/div[1]/div/ion-input/input')
            if campo_captcha and campo_captcha.is_displayed():
                print('campo_captcha localizado')
                inputs = self.driver.find_elements_by_class_name('text-input')
                for input in inputs:
                    if input.is_displayed():
                        ph = input.get_attribute('placeholder')
                        if ph == 'xxxxxxxxx':
                            self.format_busca(numero_busca)
                            break


                txt_capcha = campo_captcha.get_attribute('value')

                # Aguarda a digitação dos 5 caracteres
                if len(txt_capcha) != 5:
                    continue

                try:
                    self.driver.find_element_by_xpath('/html/body/ion-app/ng-component/ion-split-pane/ion-nav/page-pg-public-search-form/ion-content/div[2]/form/div/button').click()
                except:
                    continue

            if achei:
                cnj = self.driver.find_element_by_xpath('//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-grid/ion-row[2]/ion-col[2]')
                if cnj:
                    break

                continue

            linhas_busca = self.driver.find_elements_by_class_name('tr-table-result')
            if len(linhas_busca) > 0:
                for tr in linhas_busca:
                    if tr.is_displayed():
                        try:
                            tr.click()
                            achei = True
                            break
                        except:
                            pass



        # while True:
        #     print('procurando')
        #     cnj = self.driver.find_element_by_xpath('//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-grid/ion-row[2]/ion-col[2]')
        #     if cnj:
        #         break

        return True
        # return self.captcha(numero_busca)

    def format_busca(self, numero_busca):
        select = Select(self.driver.find_element_by_xpath('/html/body/ion-app/ng-component/ion-split-pane/ion-nav/page-pg-public-search-form/ion-content/div[2]/form/ion-list/ion-item[3]/div[1]/div/ion-label/select'))
        select.select_by_visible_text('Numeração Única Origem')

        inputs = self.driver.find_elements_by_class_name('text-input')
        el = None
        for input in inputs:
            ph = input.get_attribute('placeholder')
            if ph == 'xxxxxxx-xx.xxxx.x.xx-xxxx':
                el = input
                break
        try:
            el.clear()
        except:
            self.driver.refresh()
            return

        for r in range(0, 30):
            el.send_keys(Keys.BACKSPACE)
        for c in numero_busca:
            el.send_keys(c)

        try:
            self.driver.find_element_by_xpath('/html/body/ion-app/ng-component/ion-split-pane/ion-nav/page-pg-public-search-form/ion-content/div[2]/form/ion-grid/ion-row/ion-col[2]/div[1]/div/ion-input/input').click()
        except:
            pass

    # MÉTODO PARA TESTAR O CAPTCHA
    def captcha(self, numero_busca):
        inicio = time.time()
        i = 0
        while True:
            i += 1
            # if time.time() - inicio > 600:
            #     raise CriticalException("Erro ao ler captcha", self.uf, self.plataforma, self.prc_id)
            # campo_captcha = self.driver.find_element_by_xpath('/html/body/ion-app/ng-component/ion-split-pane/ion-nav/page-pg-public-search-form/ion-content/div[2]/form/ion-grid/ion-row/ion-col[2]/div[1]/div/ion-input/input')
            #
            # resultado_busca = self.driver.find_element_by_class_name('alert-title')
            # if resultado_busca and campo_captcha.is_displayed():
            #     print('não localizado')
            #     if resultado_busca.text.find('Nenhum registro encontrado') > -1:
            #         print('d')
            #         return False
            #
            # # Se o captcha foi digitado errado e aparecer a mensagem de erro, continua no loop
            # txt_falha = self.driver.find_element_by_class_name('alert-sub-title')
            # if txt_falha:
            #     if txt_falha.text.find('Captcha incorreto') > -1 or txt_falha.text.find('expirou') or txt_falha.text.find('formato inválido') > -1:
            #         print('captcha errado')
            #         try:
            #             btns = self.driver.find_elements_by_class_name('alert-button')
            #             btns.reverse()
            #             for b in btns:
            #                 try:
            #                     b.click()
            #                 except:
            #                     continue
            #             self.format_busca(numero_busca)
            #             self.driver.find_element_by_xpath('/html/body/ion-app/ng-component/ion-split-pane/ion-nav/page-pg-public-search-form/ion-content/div[2]/form/ion-grid/ion-row/ion-col[2]/div[1]/div/ion-input/input').clear()
            #             self.driver.find_element_by_xpath('/html/body/ion-app/ng-component/ion-split-pane/ion-nav/page-pg-public-search-form/ion-content/div[2]/form/ion-grid/ion-row/ion-col[2]/div[1]/div/ion-input/input').click()
            #         except Exception as e:
            #             tb = traceback.format_exc()
            #             print(tb)
            #             time.sleep(1)
            #             pass
            #
            #         continue
            #
            # select = Select(self.driver.find_element_by_xpath('/html/body/ion-app/ng-component/ion-split-pane/ion-nav/page-pg-public-search-form/ion-content/div[2]/form/ion-list/ion-item[3]/div[1]/div/ion-label/select'))
            # selected_option = select.first_selected_option
            # if selected_option.text != 'Numeração Única':
            #     try:
            #         self.format_busca(numero_busca)
            #     except Exception as e:
            #         tb = traceback.format_exc()
            #         print(tb)
            #     continue
            #
            # inputs = self.driver.find_elements_by_class_name('text-input')
            # for input in inputs:
            #     ph = input.get_attribute('placeholder')
            #     print('ph', ph)
            #     if ph == 'xxxxxxx-xx.xxxx.x.xx-xxxx':
            #         if input.get_attribute('value').strip() == '':
            #             print('vazio')
            #             self.format_busca(numero_busca)
            #         break
            #
            # if campo_captcha and campo_captcha.is_displayed():
            #     print('campo_captcha localizado')
            #     txt_capcha = campo_captcha.get_attribute('value')
            #     time.sleep(1)
            #
            #     # Aguarda a digitação dos 5 caracteres
            #     if len(txt_capcha) != 5:
            #         continue
            #
            #     try:
            #         self.driver.find_element_by_xpath(
            #             '/html/body/ion-app/ng-component/ion-split-pane/ion-nav/page-pg-public-search-form/ion-content/div[2]/form/div/button').click()
            #     except:
            #         continue

            linhas_busca = self.driver.find_elements_by_class_name('tr-table-result')
            if len(linhas_busca) > 0:
                for tr in linhas_busca:
                    if tr.is_displayed():
                        tr.click()
                        return True

                continue


    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''

        movs = self.driver.find_elements_by_xpath('//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-list')
        dia = movs[0].find_element_by_tag_name('p').text
        dia = localiza_data(dia)
        divs = movs[0].find_elements_by_tag_name('div')

        ps = divs[0].find_elements_by_tag_name('p')
        hora = ps[0].text[3:12].strip()
        data_tj = datetime.strptime(dia + ' ' + hora, '%Y-%m-%d %H:%M:%S')

        if ultima_data == data_tj:
            return True

        return False

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        txt_falha = self.driver.find_element_by_class_name('alert-sub-title')
        if txt_falha:
            if txt_falha.text.find('segredo de justiça') > -1:
                return True

        self.confere_cnj(numero_busca)

        return False

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        # aguarda_presenca_elemento(self.driver, "//ul[contains(@class, 'resultado-detalhe-item')]", aguarda_visibilidade=True)
        aguarda_presenca_elemento(self.driver, '//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-grid/ion-row[2]/ion-col[2]', tempo=90, aguarda_visibilidade=True)

        numero_site = ''
        el = self.driver.find_element_by_xpath('//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-grid/ion-row[2]/ion-col[2]')
        if el:
            cnj = localiza_cnj(el.text)
            numero_site = ajusta_numero(cnj)
            if numero_busca == numero_site:
                self.driver.find_element_by_xpath('//*[@id="print"]/div[2]/ion-toolbar/div[2]/ion-segment/ion-segment-button[4]').click()
                if not aguarda_presenca_elemento(self.driver, '//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-list[1]/p', tempo=10, aguarda_visibilidade=True):
                    raise MildException("Erro ao abrir movimentações", self.uf, self.plataforma, self.prc_id)

                return True

        raise MildException("Número CNJ Diferente - "+numero_site+" "+numero_busca, self.uf, self.plataforma, self.prc_id)


    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        ultima_mov = proc_data['cadastro']
        prc_id = proc_data['prc_id']
        self.movs = []
        movs = []

        movimentos = self.driver.find_elements_by_xpath('//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-list')
        if len(movimentos) == 0:
            raise MildException("Erro ao capturar movimentações", self.uf, self.plataforma, self.prc_id, False)

        capturar = True
        fim = False
        i = 0
        for mov in movimentos:
            i += 1
            dia = mov.find_element_by_tag_name('p').text
            dia = localiza_data(dia)
            divs = mov.find_elements_by_tag_name('div')
            if fim:
                break

            for div in divs:
                ps = div.find_elements_by_tag_name('p')
                hora = ps[0].text[3:12].strip()
                acp_cadastro = datetime.strptime(dia+' '+hora, '%Y-%m-%d %H:%M:%S')
                if acp_cadastro == ultima_mov:
                    capturar = False
                    if not completo and i >= 10:
                        fim = True
                        break

                acp_tipo = ps[0].text[14:].strip()
                if len(ps) < 3:
                    acp_esp = acp_tipo
                else:
                    acp_esp = ps[1].text
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

            esp = mov['acp_tipo'].upper().strip()
            esp = esp.replace('AUDIÊNCIA', 'AUDIENCIA')

            if esp.find('AUDIENCIA') != 0:
                continue

            aud = localiza_audiencia(esp, formato_data='%d/%m/%Y %H:%M', formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
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

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': [], 'terceiro':[]}

        self.driver.find_element_by_xpath('//*[@id="print"]/div[2]/ion-toolbar/div[2]/ion-segment/ion-segment-button[2]').click()
        aguarda_presenca_elemento(self.driver, '//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-grid[1]', aguarda_visibilidade=True)

        trs = self.driver.find_elements_by_xpath('//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-grid')
        reqs = 0
        if len(trs) == 2:
            for tr in trs:
                td1 = tr.find_element_by_xpath('ion-row[1]/ion-col[1]').text
                if td1.find('requerente') > -1:
                    reqs += 1

        nomes = []
        i = 0
        for tr in trs:
            polo = ''
            td1 = tr.find_element_by_xpath('ion-row[1]/ion-col[1]').text
            if find_string(td1,self.titulo_partes['ignorar']):
                continue

            if reqs == 2:
                polo = 'ativo' if i == 0 else 'passivo'
                i += 1
            else:
                if find_string(td1,self.titulo_partes['ativo']):
                    polo = 'ativo'
                if find_string(td1,self.titulo_partes['passivo']):
                    polo = 'passivo'
                if find_string(td1,self.titulo_partes['terceiro']):
                    polo = 'terceiro'

            if polo == '':
                raise MildException("polo vazio "+td1, self.uf, self.plataforma, self.prc_id)

            prt_nome = tr.find_element_by_xpath('ion-row[1]/ion-col[2]').text
            if prt_nome in nomes:
                continue
            nomes.append(prt_nome)
            partes[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': 'Não Informado'})

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        trs = self.driver.find_elements_by_xpath('//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-grid')

        nomes = []
        for tr in trs:
            polo = ''
            td1 = tr.find_element_by_xpath('ion-row[1]/ion-col[1]').text
            if find_string(td1,self.titulo_partes['ignorar']):
                continue

            if find_string(td1,self.titulo_partes['terceiro']):
                continue

            if find_string(td1,self.titulo_partes['ativo']):
                polo = 'Polo Ativo'
            if find_string(td1,self.titulo_partes['passivo']):
                polo = 'Polo Passivo'

            rows = tr.find_elements_by_tag_name('ion-row')

            for r in rows:
                td1 = r.find_element_by_xpath('ion-col[1]').text
                if td1.upper().find('ADVOGAD') == -1:
                    continue

                td2 = r.find_element_by_xpath('ion-col[2]').text
                f = td2.find('OAB:')
                f2 = td2.find('UF:')
                prr_nome = td2[:f]
                prr_oab = td2[f:f2]
                if prr_nome in nomes:
                   continue
                nomes.append(prr_nome)
                resps.append({'prr_nome': prr_nome.strip(), 'prr_oab': prr_oab.strip(), 'prr_cargo': 'Advogado', 'prr_parte': polo})


        juiz = ''
        # CAPTURA NOME JUIZ
        self.driver.find_element_by_xpath('//*[@id="print"]/div[2]/ion-toolbar/div[2]/ion-segment/ion-segment-button[1]').click()
        aguarda_presenca_elemento(self.driver, '//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-grid/ion-row[1]', aguarda_visibilidade=True)

        rows = self.driver.find_elements_by_xpath('//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-grid/ion-row')

        for row in rows:
            titulo = row.find_element_by_xpath('ion-col[1]').text

            if titulo.find('Juiz') > -1:
                juiz = row.find_element_by_xpath('ion-col[2]').text

                resps.append({'prr_nome': juiz.strip(), 'prr_oab': '', 'prr_cargo': 'Juiz', 'prr_parte': ''})

        return resps

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}

        if status_atual == 'Segredo de Justiça':
            status_atual = 'Ativo'

        prc['prc_status'] = get_status(self.movs, status_atual)

        campos = {'Assunto': 'prc_assunto', 'Classe': 'prc_classe', 'Comarca': 'prc_comarca2', 'Data de Abertura': 'prc_distribuicao', 'Nº Único': 'prc_numero2' }
        i = 1

        rows = self.driver.find_elements_by_xpath('//*[@id="print"]/div[2]/ion-card/ion-card-content/div/ion-item-group/ion-grid/ion-row')
        for row in rows:
            titulo = row.find_element_by_xpath('ion-col[1]').text
            for c in campos:
                if titulo.upper().find(c.upper()) > -1:
                    txt = row.find_element_by_xpath('ion-col[2]').text

                    if campos[c] in prc:
                        prc[campos[c]] += ' '+txt
                    else:
                        prc[campos[c]] = txt
                    break

        if 'prc_distribuicao' in prc:
            prc['prc_distribuicao'] = datetime.strptime(prc['prc_distribuicao'], '%d/%m/%Y %H:%M:%S')

        if 'prc_comarca2' in prc:
            prc['prc_comarca2'] = localiza_comarca(prc['prc_comarca2'], 'MA')

        return prc