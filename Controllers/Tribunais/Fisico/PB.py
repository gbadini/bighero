from Controllers.Tribunais.Fisico._fisico import *
import urllib.parse as urlparse
from urllib.parse import parse_qs

# CLASSE DA VARREDURA DO FISICO DE PE. HERDA OS METODOS DA CLASSE FISICO
class PB(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.pagina_busca = "https://app.tjpb.jus.br/consulta-processual/"
        self.pagina_processo = "https://app.tjpb.jus.br/consulta-processual/sistemas/"
        self.formato_data = '%d/%m/%Y %H:%M'
        self.tratar_tamanhos = True
        self.titulo_partes['ativo'] += ('PROCURADORIA DE JUSTIÇA',)
        self.titulo_partes['passivo'] += ('REPRESENTANTE',)

        # self.pagina_processo = "https://www4.tjmg.jus.br/juridico/sf/proc_resultado.jsp?tipoPesquisa=1&nomePessoa=&tipoPessoa=X&naturezaProcesso=0&situacaoParte=X&codigoOAB=&tipoOAB=N&ufOAB=MG&numero=1&select=1&tipoConsulta=1&natureza=0&ativoBaixado=X&https://www4.tjmg.jus.br/juridico/sf/proc_resultado.jsp?tipoPesquisa=1&nomePessoa=&tipoPessoa=X&naturezaProcesso=0&situacaoParte=X&codigoOAB=&tipoOAB=N&ufOAB=MG&numero=1&select=1&tipoConsulta=1&natureza=0&ativoBaixado=X&https://www4.tjmg.jus.br/juridico/sf/proc_resultado.jsp?tipoPesquisa=1&nomePessoa=&tipoPessoa=X&naturezaProcesso=0&situacaoParte=X&codigoOAB=&tipoOAB=N&ufOAB=MG&numero=1&select=1&tipoConsulta=1&natureza=0&ativoBaixado=X&listaProcessos="

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        if not aguarda_presenca_elemento(self.driver, 'numeroProcessoUnificado', tipo='NAME', aguarda_visibilidade=True):
            raise MildException("Erro ao carregar página de busca", self.uf, self.plataforma, self.prc_id)

        self.driver.find_element_by_name('numeroProcessoUnificado').send_keys(numero_busca)
        self.driver.find_element_by_name('numeroProcessoUnificado').send_keys(Keys.ENTER)

        self.wait()

        warning = self.driver.find_element_by_class_name('alert')
        if warning:
            if warning.text.find('Ocorreu uma falha durante a consulta') > -1 or warning.text.find('recurso solicitado não foi encontrado') > -1:
                raise CriticalException("Erro na Busca", self.uf, self.plataforma, self.prc_id)

        check1 = self.driver.find_element_by_xpath('//*[@id="consultaPorNumeroProcessoForm"]/div[2]/div/div')
        check2 = self.driver.find_element_by_xpath('//*[@id="content"]/app-consulta-basica/app-resultados-encontrados/div/div[4]/div/div/p')
        if check1 or check2:
            return False

        procs = self.driver.find_elements_by_xpath('//*[@id="content"]/app-consulta-basica/app-resultados-encontrados/div/div[3]/div/table/tbody/tr')
        procs.pop(0)
        for proc in procs:
            tipo = proc.find_element_by_xpath('td[3]').text
            link = proc.find_element_by_xpath('td[1]/p/a').get_attribute('href')

            if not find_string(link, (r'/5/', r'/6/', r'/1/', r'/2/', )):
                continue

            if not find_string(tipo, ('Apelação', 'Recurso')):
                continue

        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''

        if try_click(self.driver,'//*[@id="tjpb-lista-notificacoes"]/li/span'):
            time.sleep(2)

        cnj1 = self.driver.find_element_by_xpath('//*[@id="informacoes-gerais"]/app-detalhar-processo-informacoes-gerais/div[1]/div[1]/p')
        if cnj1:
            try:
                numero_site = cnj1.text
            except:
                raise MildException("Erro ao capturar CNJ", self.uf, self.plataforma, self.prc_id, False)
            inicio = time.time()
            while len(numero_site) < 5:
                if time.time() - inicio > 60:
                    raise MildException("Erro ao ler CNJ", self.uf, self.plataforma, self.prc_id)
                try:
                    cnj1 = self.driver.find_element_by_xpath('//*[@id="informacoes-gerais"]/app-detalhar-processo-informacoes-gerais/div[1]/div[1]/p')
                    numero_site = cnj1.text
                except:
                    pass

            f = numero_site.find('(')
            if f > -1:
                numero_site = numero_site[:f - 1]

            numero_site = numero_site.replace(' ','').replace('-','').replace('.','').replace('\t','').replace('\t','').replace('\r','').replace('/','')
            if numero_busca == numero_site:
                self.driver.find_element_by_xpath('//*[@id="content"]/app-detalhar-processo/ul/li[3]/a').click()
                return True

        else:
            procs = self.driver.find_elements_by_xpath('//*[@id="content"]/app-consulta-basica/app-resultados-encontrados/div/div[3]/div/table/tbody/tr')
            procs.pop(0)
            numero_site = ''
            for proc in procs:
                cnj = proc.find_element_by_xpath('td[1]').text
                numero_site = cnj.replace(' ','').replace('-','').replace('.','').replace('\t','').replace('\t','').replace('\r','').replace('/','')
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
        procs = self.driver.find_elements_by_xpath('//*[@id="content"]/app-consulta-basica/app-resultados-encontrados/div/div[3]/div/table/tbody/tr')
        if len(procs) > 0:
            procs = self.driver.find_elements_by_xpath('//*[@id="content"]/app-consulta-basica/app-resultados-encontrados/div/div[3]/div/table/tbody/tr')
            procs.pop(0)
            for proc in procs:
                if "Apelação" in proc.find_element_by_xpath('td[3]').text:
                    continue

                if "Recurso" in proc.find_element_by_xpath('td[3]').text:
                    continue

                mov_txt = proc.find_element_by_xpath('td[5]').text
                mov_link = proc.find_element_by_xpath('td[1]/p/a').text
                break

            pos = mov_txt.find('-')
            cad = mov_txt[:pos].strip()
            acp_esp = mov_txt[pos+1:].strip()

            data_cad = datetime.strptime(cad, '%d/%m/%Y')
            result = Acompanhamento.compara_mov(base, prc_id, acp_esp, data_cad, self.plataforma, self.grau, rec_id=self.rec_id)
            if not result:
                mov_link.click()
                self.alterna_janela()
                self.driver.find_element_by_xpath('//*[@id="content"]/app-detalhar-processo/ul/li[3]/a').click()

        if not aguarda_presenca_elemento(self.driver, '//*[@id="movimentacoes"]/app-detalhar-processo-movimentacoes/div[1]/div/table/tbody/tr', aguarda_visibilidade=True, tempo=40):
            raise CriticalException("Erro ao abrir acompanhamentos", self.uf, self.plataforma, self.prc_id)

        if len(procs) == 0:
            cad = self.driver.find_element_by_xpath('//*[@id="movimentacoes"]/app-detalhar-processo-movimentacoes/div[1]/div/table/tbody/tr[2]/td[1]').text
            print(cad[:10])
            data_cad = datetime.strptime(cad[:10].strip(), '%d/%m/%Y')
            acp_esp = self.driver.find_element_by_xpath('//*[@id="movimentacoes"]/app-detalhar-processo-movimentacoes/div[1]/div/table/tbody/tr[2]/td[2]').text
            result = Acompanhamento.compara_mov(base, prc_id, acp_esp, data_cad, self.plataforma, self.grau)

        return result


    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        self.movs = []
        movs = []
        prc_id = proc_data['prc_id']
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None

        # BUSCA MOVIMENTAÇÕES DO PROCESSO NA BASE
        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)

        wh = self.driver.window_handles
        if len(wh) == 1:
            try:
                self.driver.find_element_by_xpath('//*[@id="content"]/app-consulta-basica/app-resultados-encontrados/div/div[3]/div/table/tbody/tr/td[1]/p/a').click()
                self.alterna_janela()
                self.driver.find_element_by_xpath('//*[@id="content"]/app-detalhar-processo/ul/li[3]/a').click()
            except:
                pass

        movimentos_antes = self.driver.find_elements_by_xpath('//*[@id="movimentacoes"]/app-detalhar-processo-movimentacoes/div[1]/div/table/tbody/tr')

        aguarda_presenca_elemento(self.driver, '//*[@id="movimentacoes"]/app-detalhar-processo-movimentacoes/div[2]/div[2]/button')
        self.driver.find_element_by_xpath('//*[@id="movimentacoes"]/app-detalhar-processo-movimentacoes/div[2]/div[2]/button').click()

        movimentos = self.driver.find_elements_by_xpath('//*[@id="movimentacoes"]/app-detalhar-processo-movimentacoes/div[1]/div/table/tbody/tr')
        while movimentos_antes == movimentos:
            movimentos = self.driver.find_elements_by_xpath('//*[@id="movimentacoes"]/app-detalhar-processo-movimentacoes/div[1]/div/table/tbody/tr')

        movimentos.pop(0)

        capturar = True
        i = 0
        for mov in movimentos:
            i += 1
            acp_cadastro = mov.find_element_by_xpath('td[1]').text[:10].strip()
            acp_cadastro = datetime.strptime(acp_cadastro + ' 00:00:00', '%d/%m/%Y %H:%M:%S')

            acp_esp = mov.find_element_by_xpath('td[2]').text

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

            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': ''}
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
            esp = esp.replace('AUDIÊNCIA', 'AUDIENCIA')
            if esp.find('AUDIENCIA') == -1:
                continue

            if esp.find('AUDIENCIA') > 0 and esp.find('SALA DE AUDIENCIA') == -1:
                continue

            aud = localiza_audiencia(esp, formato_data='%d/%m/%Y %H:%M', formato_re='(\\d+)(\\/)(\\d+)(\\/)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
            if not aud:
                aud = localiza_audiencia(esp, formato_data='%d%m%Y %H%M', formato_re='(\\d+)(\\s+)(\\d+)')
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
        '''
        :param str status_atual: Status atual
        '''
        prc = {}

        campos = {'Órgão Julgador': 'prc_juizo', 'Classe': 'prc_classe', 'Segredo de justiça': 'prc_segredo', 'Assunto principal': 'prc_assunto', 'Data da distribuição': 'prc_distribuicao', 'Valor da ação': 'prc_valor_causa', 'Número do Processo': 'prc_numero2'}

        self.driver.find_element_by_xpath('//*[@id="content"]/app-detalhar-processo/ul/li[1]/a').click()

        campo_dados = self.driver.find_elements_by_xpath(' //*[@id="informacoes-gerais"]/app-detalhar-processo-informacoes-gerais/div[1]/div')

        for campo in campo_dados:
            aux = campo.text.split('\n')
            if len(aux) == 1:
                continue

            if aux[1].strip() == '--':
                continue

            titulo = aux[0]

            for cmp in campos:
                if titulo.upper().find(cmp.upper()) > -1:
                    prc[campos[cmp]] = aux[1].strip()
                    break

        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        path = parsed.path
        f = path.find(r'sistemas/')
        prc['prc_codigo'] = path[f+9:]

        prc['prc_serventia'] = prc['prc_juizo']
        prc['prc_status'] = get_status(self.movs, status_atual, self.arquiva_sentenca)
        prc['prc_comarca2'] = localiza_comarca(prc['prc_juizo'], self.uf)

        f = prc['prc_numero2'].find('(')
        if f > -1:
            prc['prc_numero2'] = prc['prc_numero2'][:f-1]

        if 'prc_distribuicao' in prc:
            prc['prc_distribuicao'] = datetime.strptime(prc['prc_distribuicao'].strip(), '%d/%m/%Y')

        if 'prc_segredo' in prc:
            prc['prc_segredo'] = False if prc['prc_segredo'].find('Não') > -1 else True

        return prc

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': [], 'terceiro':[]}
        nomes = []

        self.driver.find_element_by_xpath('//*[@id="content"]/app-detalhar-processo/ul/li[2]/a').click()
        aguarda_presenca_elemento(self.driver, '//*[@id="partes"]/app-detalhar-processo-partes', aguarda_visibilidade=True)

        inicio = time.time()
        while True:
            if time.time() - inicio > 30:
                raise CriticalException("Partes não localizadas", self.uf, self.plataforma, self.prc_id, False)

            div = self.driver.find_element_by_xpath('//*[@id="partes"]/app-detalhar-processo-partes/div')
            if div:
                try:
                    if div.text.strip() == 'Nenhuma parte para este processo.':
                        return partes
                except:
                    pass

            if self.driver.find_element_by_xpath('//*[@id="partes"]/app-detalhar-processo-partes/div/div/table/tbody/tr'):
                break

        test = self.driver.find_element_by_xpath('//*[@id="partes"]/app-detalhar-processo-partes/div')
        if test and test.text == 'Nenhuma parte para este processo.':
            return partes

        table = self.driver.find_elements_by_xpath('//*[@id="partes"]/app-detalhar-processo-partes/div/div/table/tbody/tr')
        table.pop(0)

        for pt in table:
            polo = ''
            td1 = pt.find_element_by_xpath('td[1]').text

            if find_string(td1,self.titulo_partes['ignorar']):
                continue

            if find_string(td1,self.titulo_partes['ativo']):
                polo = 'ativo'
            if find_string(td1,self.titulo_partes['passivo']):
                polo = 'passivo'
            if find_string(td1,self.titulo_partes['terceiro']):
                polo = 'terceiro'

            if polo == '':
                raise MildException("polo vazio "+td1, self.uf, self.plataforma, self.prc_id)

            prt_nome = pt.find_element_by_xpath('td[3]').text

            partes[polo].append({'prt_nome': prt_nome.strip(), 'prt_cpf_cnpj': 'Não Informado'})

        if len(partes['ativo']) == 0 or len(partes['passivo']) == 0:
            print(partes)
            raise MildException("Polo não localizado ", self.uf, self.plataforma, self.prc_id)

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []
        nomes = []

        test = self.driver.find_element_by_xpath('//*[@id="partes"]/app-detalhar-processo-partes/div')
        if test and test.text == 'Nenhuma parte para este processo.':
            return []

        table = self.driver.find_elements_by_xpath('//*[@id="partes"]/app-detalhar-processo-partes/div/div/table/tbody/tr')
        table.pop(0)

        for pt in table:
            polo = ''
            td1 = pt.find_element_by_xpath('td[1]').text

            if find_string(td1, self.titulo_partes['ignorar']):
                continue

            if find_string(td1, self.titulo_partes['terceiro']):
                continue

            if find_string(td1, self.titulo_partes['ativo']):
                polo = 'Polo Ativo'
            if find_string(td1, self.titulo_partes['passivo']):
                polo = 'Polo Passivo'

            prr_nome = pt.find_element_by_xpath('td[4]').text
            if prr_nome in nomes:
                continue
            nomes.append(prr_nome)

            resps.append({'prr_nome': prr_nome, 'prr_cargo': 'Advogado', 'prr_parte': polo})

        return resps

    # AGUARDA ATÉ QUE A ANIMAÇÃO DE LOADING ESTEJA OCULTA
    def wait(self, tempo=50):
        inicio = time.time()
        while True:
            if time.time() - inicio > tempo:
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id)
            time.sleep(0.5)
            spinner = self.driver.find_element_by_class_name('loader')
            if not spinner:
                break

        return True

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