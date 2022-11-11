from Controllers.Tribunais.Trt._trt import *

# CLASSE DA VARREDURA DO TRT SEGUNDA VERSAO. HERDA OS METODOS DA CLASSE TRT
class TrtV2(Trt):

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
        aguarda_presenca_elemento(self.driver, 'timeline', tipo='ID')
        self.driver.find_element_by_id('timeline').click()

        self.wait(60)

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        self.wait(10)

        if not aguarda_presenca_elemento(self.driver, '//*[@id="timeline"]/ul/li[1]'):
            return True

        el_dia = self.driver.find_element_by_xpath('//*[@id="timeline"]/ul/li[1]')
        if not el_dia:
            raise MildException("Erro ao capturar última movimentação", self.uf, self.plataforma, self.prc_id)

        movs = self.captura_movimentos(base, prc_id, False, limite=8, rec_id=self.rec_id)

        return len(movs) == 0

    def captura_movimentos(self, base, prc_id, completo, limite=None, rec_id=None):
        btn = self.driver.find_element_by_xpath('//*[@id="timeline"]/pje-timeline-busca/mat-card/section/button[2]')
        label = btn.get_attribute('aria-label')
        if label == 'Exibir movimentos.':
            btn.click()

        self.wait(20)
        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)

        movimentos = self.driver.find_elements_by_xpath('//*[@id="timeline"]/ul/li')
        while len(movimentos) == 0:
            movimentos = self.driver.find_elements_by_xpath('//*[@id="timeline"]/ul/li')

        total_limite = 0
        dia = ''
        movs = []
        self.movs = []
        for mov in movimentos:
            div_tl = mov.find_elements_by_class_name('tl-data')
            if len(div_tl) > 0:
                txt = div_tl[0].text
                dia = localiza_data(txt)
                if not dia:
                    raise MildException("Erro ao capturar data da movimentação", self.uf, self.plataforma, self.prc_id)

            cards = mov.find_elements_by_xpath('div/mat-card')
            for c in cards:
                doc = c.find_elements_by_class_name('tl-documento')
                if len(doc) > 0:
                    continue

                if dia == '':
                    raise MildException("Erro ao capturar data inicial", self.uf, self.plataforma, self.prc_id)

                total_limite += 1
                hora = c.find_element_by_tag_name('header').text
                acp_cadastro = datetime.datetime.strptime(dia + ' ' + hora, '%Y-%m-%d %H:%M')
                acp_esp = c.find_element_by_xpath('div').text.replace('Descrição do movimento:\n','')
                acp_tipo = c.get_attribute('id')
                acp_tipo = acp_tipo.replace('mov_','')

                capturar = True
                for l in lista:
                    acp_cadastro_db = l['acp_cadastro'].strftime('%Y-%m-%d %H:%M')
                    acp_cadastro_db = datetime.datetime.strptime(acp_cadastro_db, '%Y-%m-%d %H:%M')
                    if acp_cadastro == acp_cadastro_db:
                        if acp_tipo == l['acp_tipo']:
                            capturar = False
                            break

                self.movs.append({'dia': acp_cadastro, 'esp': acp_esp, 'novo': capturar})
                if capturar:
                    movs.append({'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': acp_tipo})
                else:
                    if not completo:
                        if limite is None and total_limite >= 10:
                            return movs

                        if limite is not None and total_limite >= limite:
                            return movs

        return movs

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        prc_id = proc_data['prc_id']
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None
        movs = self.captura_movimentos(base, prc_id, completo, rec_id=rec_id)

        return movs

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []
        for mov in self.movs:
            if not self.completo and not mov['novo']:
                break

            esp = mov['esp'].upper().strip()
            if esp.find('970 - ') != 0:
                if esp == '' or esp == 'AUDIÊNCIA' or esp == 'AUDIÊNCIA PRELIMINAR/CONCILIAÇÃO' or (esp.find('AUDIÊNCIA') != 0 and esp.find('INCLUÍDO EM PAUTA') == -1):
                    continue

            aud = localiza_audiencia(esp)
            if not aud:
                continue

            if 'prp_tipo' not in aud or 'prp_status' not in aud:
                if esp.find('SEMANA NACIONAL DE CONCILIAÇÃO') > -1:
                    aud['prp_tipo'] = 'Conciliação'
                    aud['prp_status'] = 'Designada'
                elif 'prp_tipo' in aud and aud['prp_tipo'] == 'Audiência' and 'prp_status' not in aud:
                    aud['prp_tipo'] = 'Audiência'
                    aud['prp_status'] = 'Designada'
                elif 'prp_tipo' not in aud and esp.find('INCLUÍDO EM PAUTA O PROCESSO') > -1:
                    aud['prp_tipo'] = 'Audiência'
                    aud['prp_status'] = 'Designada'
                else:
                    erro = ''
                    if 'prp_status' not in aud:
                        erro = 'Status '
                    if 'prp_tipo' not in aud:
                        erro = 'Tipo '
                    raise MildException("Audiência - "+erro+" não localizado: "+esp, self.uf, self.plataforma, self.prc_id)

            serventia = None
            hora = aud['prp_data'].strftime('%H:%M')
            if aud['prp_status'] == 'Designada' or esp.find('REDESIGNADA PARA') > -1:
                aud['prp_status'] = 'Designada'
                p = esp.find(hora)
                serventia = esp[p+5:].replace('()','').strip()

            aud['prp_serventia'] = serventia
            aud['data_mov'] = mov['dia']
            adcs.append(aud)

        return adcs

    # AGUARDA ATÉ QUE A ANIMAÇÃO DE LOADING ESTEJA OCULTA
    def wait(self, tempo=30, id='mat-progress-bar'):
        inicio = time.time()
        while True:
            if time.time() - inicio > tempo:
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id)

            try:
                if not self.driver.find_element_by_class_name('mat-progress-bar'):
                    break
                else:
                    if not self.driver.find_element_by_class_name('mat-progress-bar').is_displayed():
                        break
            except:
                pass

            time.sleep(0.2)

        inicio = time.time()
        while True:
            if time.time() - inicio > tempo:
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id)

            try:
                if not self.driver.find_element_by_id('mat-dialog-0'):
                    return True
                else:
                    if not self.driver.find_element_by_id('mat-dialog-0').is_displayed():
                        return True
            except:
                pass

            time.sleep(0.2)

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        self.driver.find_element_by_xpath('/html/body/pje-root/mat-sidenav-container/mat-sidenav-content/pje-cabecalho/div/mat-toolbar/pje-cabecalho-processo/section/div/section[1]/span[1]/button').click()
        self.wait_complete()
        partes = {'ativo':[], 'passivo':[], 'terceiro':[]}
        aguarda_presenca_elemento(self.driver, '//*[@id="partes-processo-autuacao"]/ul/li/pje-nome-parte/div/span', aguarda_visibilidade=True, tempo=15)

        polos = {'Polo Ativo': 'ativo', 'Polo Passivo': 'passivo', 'Outros Interessados': 'terceiro'}
        quadros = self.driver.find_elements_by_class_name('is-item-pilha-parte')
        for quadro in quadros:

            polo_txt = quadro.find_element_by_xpath('div/span/span').text
            polo = polos[polo_txt]

            qd_partes = quadro.find_elements_by_xpath('pje-parte-processo/section/ul')
            for qd in qd_partes:
                prt_nome = qd.find_element_by_tag_name('pje-nome-parte').text.replace('()','').strip()
                prt_cpf_cnpj = qd.find_element_by_xpath('li/span[2]').text
                f = prt_cpf_cnpj.find('CNPJ:')
                if f == -1:
                    f = prt_cpf_cnpj.find('CPF:')
                if f == -1:
                    prt_cpf_cnpj = ''
                else:
                    f = prt_cpf_cnpj.find(':')
                    prt_cpf_cnpj = prt_cpf_cnpj[f+1:].strip()
                partes[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': prt_cpf_cnpj})

        if len(partes['ativo']) == 0:
            raise MildException("Parte Ativa Vazia", self.uf, self.plataforma, self.prc_id)

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        aguarda_presenca_elemento(self.driver, 'processo', tipo='ID', aguarda_visibilidade=True, tempo=15)

        polos = {'Polo Ativo': 'ativo', 'Polo Passivo': 'passivo', 'Outros Interessados': 'terceiro'}
        quadros = self.driver.find_elements_by_class_name('is-item-pilha-parte')
        for quadro in quadros:

            polo_txt = quadro.find_element_by_xpath('div/span/span').text
            polo = polos[polo_txt]

            if polo == 'terceiro':
                continue

            qd_advs = quadro.find_elements_by_class_name('partes-hierarquia')
            for qd_adv in qd_advs:
                advs = qd_adv.find_elements_by_tag_name('li')
                for adv in advs:
                    prr_nome = adv.find_element_by_xpath('small/span[1]').text
                    try:
                        prr_oab = adv.find_element_by_xpath('small/span[2]/span[2]').text
                    except:
                        prr_oab = ''

                    prr_cargo = 'Advogado'
                    p = prr_nome.find('(')
                    if prr_nome.upper().find('REPRESENTANTE') == -1 and prr_nome.upper().find('ADVOGAD') == -1:
                        prr_cargo = prr_nome[p:]
                        prr_cargo = prr_cargo.replace('(', '').replace(')', '').strip()

                    prr_nome = prr_nome[:p].strip()
                    p = prr_oab.find('OAB:')
                    prr_oab = prr_oab[p+4:].replace('(','').replace(')','').strip()
                    resps.append({'prr_nome': prr_nome, 'prr_oab': prr_oab, 'prr_cargo': prr_cargo, 'prr_parte': 'Polo ' + polo})

        return resps

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}

        campos = {'julgador': 'prc_serventia', 'Assunto': 'prc_assunto', 'Valor': 'prc_valor_causa', 'Distribuído': 'prc_distribuicao', 'Número do Processo': 'prc_numero2'}
        dts = self.driver.find_elements_by_xpath('//*[@id="processo"]/div/div[1]/dl/*')
        i = 0
        conteudo = ''
        campo = ''
        for dt in dts:
            i += 1
            if dt.tag_name == 'dt':
                if campo != '':
                    prc[campo] = conteudo.strip().strip(',')
                conteudo = ''
                titulo = dt.text

                campo = ''
                for c in campos:
                    if titulo.upper().find(c.upper()) > -1:
                        campo = campos[c]
                        break

                if campo == '':
                    continue
            elif dt.tag_name == 'dd':
                conteudo += dt.text + ', '

            if i == len(dts):
                prc[campo] = conteudo.strip().strip(',')

        if len(prc) == 0:
            raise MildException("Erro ao abrir processo", self.uf, self.plataforma, self.prc_id, False)

        if 'prc_serventia' in prc:
            prc['prc_comarca2'] = localiza_comarca(prc['prc_serventia'], self.uf)

        if 'prc_distribuicao' in prc:
            data_dist = localiza_data(prc['prc_distribuicao'])
            if not data_dist:
                del prc['prc_distribuicao']
            else:
                prc['prc_distribuicao'] = data_dist

        if status_atual == 'Segredo de Justiça':
            status_atual = 'Ativo'

        prc['prc_status'] = get_status(self.movs, status_atual)

        if 'prc_numero2' in prc:
            r = re.search("((\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+))", prc['prc_numero2'], re.IGNORECASE | re.DOTALL)
            if r is not None:
                prc['prc_numero2'] = r.group(0)

        self.driver.find_element_by_xpath('//*[@id="autuacao-dialogo"]/a/i').click()
        return prc

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, pasta_intermediaria):
        arquivos = []

        btn = self.driver.find_element_by_xpath('//*[@id="timeline"]/pje-timeline-busca/mat-card/section/button[2]')
        label = btn.get_attribute('aria-label')
        if label == 'Ocultar movimentos.':
            btn.click()

        self.wait(20)
        movimentos = self.driver.find_elements_by_xpath('//*[@id="timeline"]/ul/li')
        while len(movimentos) == 0:
            movimentos = self.driver.find_elements_by_xpath('//*[@id="timeline"]/ul/li')

        dia = ''
        for mov in movimentos:
            div_tl = mov.find_elements_by_class_name('tl-data')
            if len(div_tl) > 0:
                txt = div_tl[0].text
                dia = localiza_data(txt)
                if not dia:
                    raise MildException("Erro ao capturar data da movimentação", self.uf, self.plataforma, self.prc_id)

            cards = mov.find_elements_by_xpath('div/mat-card')
            for c in cards:
                doc = c.find_elements_by_class_name('tl-documento')
                if len(doc) == 0:
                    continue

                if dia == '':
                    continue
                    raise MildException("Erro ao capturar data inicial", self.uf, self.plataforma, self.prc_id)

                hora = c.find_element_by_tag_name('header').text
                pra_data = datetime.datetime.strptime(dia + ' ' + hora, '%Y-%m-%d %H:%M')

                btn_modal = self.driver.find_element_by_xpath(
                    '/html/body/div[3]/div[2]/div/mat-dialog-container/ng-component/div/div[3]/button')
                if btn_modal:
                    btn_modal.click()

                aria = c.find_elements_by_xpath('pje-timeline-anexos/div/div')
                if len(aria) > 0:
                    if aria[0].get_attribute('aria-pressed') == 'false':
                        try:
                            aria[0].click()
                        except:
                            raise
                        time.sleep(0.2)

                elements = len(c.find_elements_by_xpath('div/a[1]'))
                elements += len(c.find_elements_by_xpath('pje-timeline-anexos/div/div[2]/div/a[1]'))

                for i_el in range(0, elements):
                    arq = {'pra_prc_id': prc_id, 'pra_plt_id': self.plataforma, 'pra_erro': False, 'pra_arquivo': None,
                           'pra_sigilo': False, 'pra_original': None, 'pra_tentativas': None, 'pra_excluido': False,
                           'pra_grau': self.grau}

                    aria = c.find_elements_by_xpath('pje-timeline-anexos/div/div')
                    if len(aria) > 0:
                        if aria[0].get_attribute('aria-pressed') == 'false':
                            aria[0].click()
                            time.sleep(0.2)

                    if i_el == 0:
                        el = c.find_element_by_xpath('div/a[1]')
                    else:
                        el = c.find_element_by_xpath('pje-timeline-anexos/div/div[2]/div['+str(i_el)+']/a[1]')

                    txt = el.text
                    f = txt.rfind('-')
                    arq['pra_id_tj'] = txt[f+1:].strip()
                    if len(arq['pra_id_tj']) > 15:
                        continue

                    arq['pra_descricao'] = txt[:f].strip()
                    arq['pra_data'] = pra_data

                    achei = False
                    for a_b in arquivos_base:
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


                    btn_modal = self.driver.find_element_by_xpath('/html/body/div[3]/div[2]/div/mat-dialog-container/ng-component/div/div[3]/button')
                    if btn_modal:
                        btn_modal.click()

                    el.location_once_scrolled_into_view
                    div_scroll = self.driver.find_element_by_xpath('//*[@id="timeline"]/ul')
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop-40", div_scroll)
                    try:
                        el.click()
                    except:
                        pass
                    self.wait(40)

                    aguarda_presenca_elemento(self.driver, 'snack-bar-container', tipo='TAG_NAME', tempo=0.5)
                    snack = self.driver.find_element_by_tag_name('snack-bar-container')
                    if snack:
                        if self.driver.find_element_by_tag_name('snack-bar-container').text.find('Usuário não tem visibilidade') > -1:
                            arq['pra_sigilo'] = True
                            self.driver.find_element_by_tag_name('snack-bar-container').find_element_by_xpath(
                                'div/div/simple-snack-bar/div/button').click()

                    if not arq['pra_sigilo']:
                        click = False
                        while not click:
                            click = self.click_download()

                        # header.find_element_by_xpath('div[2]/div[4]/a[2]/button').click()
                        aguarda_presenca_elemento(self.driver, 'snack-bar-container', tipo='TAG_NAME', tempo=0.5)
                        snack = self.driver.find_element_by_tag_name('snack-bar-container')
                        if snack:
                            if self.driver.find_element_by_tag_name('snack-bar-container').text.find('não encontrado') > -1:
                                arq['pra_erro'] = True
                                self.driver.find_element_by_tag_name('snack-bar-container').find_element_by_xpath('div/div/simple-snack-bar/div/button').click()

                        if not arq['pra_erro']:
                            arq['pra_erro'] = False if aguarda_download(self.pasta_download, 1) else True

                    if not arq['pra_erro'] and not arq['pra_excluido'] and not arq['pra_sigilo']:
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

        arquivos.reverse()
        return arquivos

    def click_download(self):
        header_div = self.driver.find_element_by_xpath('//*[@id="timeline"]/pje-historico-scroll/pje-historico-scroll-titulo/div/mat-card/mat-card-header/div[2]')
        self.driver.execute_script("arguments[0].style.width = '600px';", header_div)

        header = self.driver.find_element_by_tag_name('mat-card-header')
        btns = header.find_elements_by_xpath('div/div/a/button')
        inicio = time.time()
        while len(btns) < 2:
            if (time.time() - inicio) >= 25 and (time.time() - inicio) <= 49:
                header.find_element_by_xpath('button/span[1]/i').click()
            elif (time.time() - inicio) >= 50:
                raise MildException("Erro ao carregar arquivo", self.uf, self.plataforma, self.prc_id, False)

            btns = header.find_elements_by_xpath('div/div/a/button')
        for btn in btns:
            mattooltip = btn.get_attribute('mattooltip')
            if mattooltip.find('Baixar documento sem capa') > -1:
                try:
                    btn.click()
                except:
                    header.find_element_by_xpath('div[2]/div[3]/mat-card-content/button').click()
                    return False

        return True

    def wait_complete(self):
        page_state = ''
        inicio = time.time()
        while page_state != 'complete':
            time.sleep(0.5)
            if time.time() - inicio > 40:
                self.driver.execute_script("window.stop();")
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)
            try:
                page_state = self.driver.execute_script('return document.readyState;')
            except:
                pass