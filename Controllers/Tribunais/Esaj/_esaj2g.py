from Controllers.Tribunais.Esaj._esaj import *
from Controllers.Tribunais.segundo_grau import *


# CLASSE DA VARREDURA DO ESAJ DE SEGUNDO GRAU. HERDA OS METODOS DAS CLASSES PLATAFORMA e ESAJ
class Esaj2g(SegundoGrau, Esaj):

    # CONFERE SE OS RECURSOS ESTÃO NA BASE CASO EXISTA MAIS DE UM
    def confere_recursos(self, base, proc):
        recs = self.driver.find_elements_by_xpath('//*[@id="listagemDeProcessos"]/ul/li/div/div[1]/div[1]/a')

        if len(recs) < 2:
            return True

        achei = True
        for rec in recs:
            href = rec.get_attribute('href')
            parsed = urlparse.urlparse(href)
            parse_qs(parsed.query)
            url_params = parse_qs(parsed.query)
            if 'processo_codigo' in url_params:
                processo_codigo = url_params['processo_codigo'][0]
                rec_codigo = url_params['processo_codigo'][0]
                if 'processo_foro' in url_params:
                    rec_codigo += '&processo_foro=' + url_params['processo_foro'][0]

            elif 'processo.codigo' in url_params:
                processo_codigo = url_params['processo.codigo'][0]
                rec_codigo = url_params['processo.codigo'][0]
                if 'processo.foro' in url_params:
                    rec_codigo += '&processo.foro=' + url_params['processo.foro'][0]

            result = Recurso.select(base, proc['prc_id'], processo_codigo, like=True)
            if len(result) == 0:
                achei = False
                Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_codigo': rec_codigo, 'rec_numero': rec.text.strip(), 'rec_plt_id': self.plataforma})

        return achei

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        if self.driver.find_element_by_class_name("g-recaptcha"):
            if self.driver.find_element_by_class_name("g-recaptcha").is_displayed():
                raise CriticalException("Captcha Detectado", self.uf, self.plataforma, self.prc_id)

        xpaths = (
            '//*[@id="containerDadosPrincipaisProcesso"]/div[1]/div/div/span',
            '/html/body/div[1]/div[2]/div/div[1]/div/span[1]',
            '/html/body/table[4]/tbody/tr/td/table[2]/tbody/tr[1]/td[2]/table/tbody/tr/td/span[1]',
            '/html/body/div/table[4]/tbody/tr/td/div[1]/table[2]/tbody/tr[1]/td[2]/table/tbody/tr/td/span[1]',
            '//*[@id="blocoDados"]/ul/li[1]/span'
        )
        numero_site = 'edfwefewfewf'
        for xp in xpaths:
            el = self.driver.find_element_by_xpath(xp)
            if el:
                cnj = localiza_cnj(el.text)
                if cnj:
                    numero_site = ajusta_numero(cnj)
                    if numero_busca == numero_site:
                        return True
                    else:
                        els = self.driver.find_elements_by_xpath('/html/body/div[2]/table[3]/tbody/tr/td[1]')
                        for el in els:
                            cnj = localiza_cnj(el.text)
                            if cnj:
                                numero_site = ajusta_numero(cnj)
                                if numero_busca.lstrip('0') == numero_site.lstrip('0'):
                                    return True

                        els = self.driver.find_elements_by_xpath('/html/body/table[4]/tbody/tr/td/table[2]/tbody/tr/td[2]')
                        for el in els:
                            cnj = localiza_cnj(el.text)
                            if cnj:
                                numero_site = ajusta_numero(cnj)
                                if numero_busca == numero_site:
                                    return True


        raise MildException("Número CNJ Diferente: "+numero_busca + " | " + numero_site, self.uf, self.plataforma, self.prc_id)

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        rec = {}
        # self.driver.execute_script("$('#botaoExpandirDadosSecundarios').click()")
        # self.driver.execute_script("$('#maisDetalhes').addClass('show')")
        self.driver.execute_script("window.scrollTo(0,0);")

        # LOCALIZA STATUS DO PROCESSO
        rec['rec_status'] = get_status(self.movs, status_atual, grau=2)

        # LOCALIZA NRO CNJ
        # if self.versao == 1:
        numero2 = self.driver.find_element_by_id('numeroProcesso')
        if numero2:
            rec['rec_numero'] = numero2.text
        else:
            xpaths = (
                '//*[@id="containerDadosPrincipaisProcesso"]/div[1]/div/div/span',
                '/html/body/div[1]/div[2]/div/div[1]/div/span[1]',
                '/html/body/table[4]/tbody/tr/td/table[2]/tbody/tr[1]/td[2]/table/tbody/tr/td/span[1]',
                '/html/body/div/table[4]/tbody/tr/td/div[1]/table[2]/tbody/tr[1]/td[2]/table/tbody/tr/td/span[1]',
                '/html/body/table[4]/tbody/tr/td/table[2]/tbody/tr[1]/td[2]/table/tbody/tr/td/span[1]'
            )

            for xp in xpaths:
                el = self.driver.find_element_by_xpath(xp)
                if el:
                    cnj = localiza_cnj(el.text)
                    if cnj:
                        rec['rec_numero'] = cnj
                        break

        if self.versao == 1:
            main_div = self.driver.find_element_by_xpath('/html/body/div[1]')
            divs = main_div.find_elements_by_xpath("//div[contains(@class, 'row')]/div")
        else:
            divs = self.driver.find_elements_by_xpath('/html/body/table[4]/tbody/tr/td/table[2]/tbody/tr')

        campos = {'Valor da ação': 'rec_valor', 'Assunto': 'rec_assunto', 'Classe': 'rec_classe',  'Órgão Julgador': 'rec_orgao', 'Relator': 'rec_relator', 'Distribuição': 'rec_distribuicao'}

        i = 1
        for div in divs:
            i += 1
            try:
                if self.versao == 1:
                    label = div.find_element_by_tag_name('span').text
                else:
                    label = div.find_element_by_xpath('td[1]').text
            except:
                continue

            for c in campos:
                if label.upper().find(c.upper()) > -1:
                    if self.versao == 1:
                        txt = div.find_element_by_tag_name('div').text
                    else:
                        txt = div.find_element_by_xpath('td[2]').text

                    if campos[c] in rec:
                        rec[campos[c]] += ' '+txt
                    else:
                        rec[campos[c]] = txt
                    break

        if 'rec_distribuicao' in rec:
            if rec['rec_distribuicao'].strip() == '':
                del rec['rec_distribuicao']
            else:
                r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(às)(\\s+)(\\d+)(:)(\\d+)', rec['rec_distribuicao'])
                if r is not None:
                    rec_distribuicao = r.group(0).replace(' às', '')
                    rec['rec_distribuicao'] = datetime.strptime(rec_distribuicao, '%d/%m/%Y %H:%M')
                else:
                    del rec['rec_distribuicao']

        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        if 'processo_codigo' in url_params:
            processo_codigo = url_params['processo_codigo'][0]
            rec_codigo = url_params['processo_codigo'][0]
            if 'processo_foro' in url_params:
                rec_codigo += '&processo_foro=' + url_params['processo_foro'][0]

        elif 'processo.codigo' in url_params:
            processo_codigo = url_params['processo.codigo'][0]
            rec_codigo = url_params['processo.codigo'][0]
            if 'processo.foro' in url_params:
                rec_codigo += '&processo.foro=' + url_params['processo.foro'][0]
        else:
            htmls = self.driver.find_elements_by_tag_name('script')
            for html in htmls:
                inner = html.get_attribute('innerHTML')
                p = inner.find('cdProcesso')
                if p > -1:
                    codigo = inner[p+11:]
                    p = codigo.find('&')
                    codigo = codigo[:p]

                    p = inner.find('cdForo=')
                    foro = inner[p+7:]
                    p = foro.find('&')
                    foro = foro[:p]
                    rec['rec_codigo'] = codigo+'&processo.foro='+foro
                    break

        return rec

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': [], 'terceiro':[]}

        # IDENTIFICA A VERSÃO DO E-SAJ
        if self.versao is None:
            self.versao = 1 if self.driver.find_element_by_class_name('unj-entity-header') else 2

        self.tabela_partes = 'tablePartesPrincipais'
        if try_click(self.driver, 'linkpartes', 'ID'):
            wait = WebDriverWait(self.driver, 10)
            try:
                wait.until(EC.visibility_of_element_located((By.ID, 'tableTodasPartes')))
            except:
                try_click(self.driver, 'linkpartes', 'ID')
                wait = WebDriverWait(self.driver, 10)
                try:
                    wait.until(EC.visibility_of_element_located((By.ID, 'tableTodasPartes')))
                except:
                    raise MildException('erro ao carregar tabela de partes', self.uf, self.plataforma, self.prc_id)
            self.tabela_partes = 'tableTodasPartes'

        trs = self.driver.find_elements_by_xpath('//*[@id="'+self.tabela_partes+'"]/tbody/tr')

        if len(trs) == 0:
            raise MildException('tr partes vazio', self.uf, self.plataforma, self.prc_id)

        tipos = {'ativo': 'X', 'passivo': 'Y', 'terceiro': 'Z'}
        nomes = []
        for tr in trs:

            td1 = tr.find_element_by_xpath('td[1]').text
            if find_string(td1,self.titulo_partes['ignorar']):
                continue

            polo = ''
            if find_string(td1,self.titulo_partes['ativo']):
                polo = 'ativo'
            elif find_string(td1,self.titulo_partes['passivo']):
                polo = 'passivo'
            elif find_string(td1,self.titulo_partes['terceiro']):
                polo = 'terceiro'

            if polo == '':
                raise MildException("polo vazio "+td1, self.uf, self.plataforma, self.prc_id)

            tipos[polo] = td1
            td2 = tr.find_element_by_xpath('td[2]')
            html = td2.get_attribute('innerHTML')

            prts = html.split('<br>')

            for prt in prts:
                prt_nome = strip_html_tags(prt)

                if not find_string(prt_nome,('ADVOGADO:','ADVOGADA:')):
                    if prt_nome in nomes:
                        continue
                    nomes.append(prt_nome)
                    partes[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': 'Não Informado'})

        if tipos['ativo'] == tipos['passivo']:
            return {'ativo': [{'prt_nome': 'AMBOS',}, ],}
        return partes