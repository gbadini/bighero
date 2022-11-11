from Config.helpers import *
from Controllers.Tribunais.primeiro_grau import *
from selenium.webdriver.common.keys import *
from Models.processoModel import *
import sys, time, shutil
import urllib.parse as urlparse
from urllib.parse import parse_qs

# CLASSE DA VARREDURA DO PROJUDI. HERDA OS METODOS DA CLASSE PLATAFORMA
class Projudi(PrimeiroGrau):

    def __init__(self):
        super().__init__()
        self.plataforma = 3
        self.movs = []
        self.tabela_movs = '//*[@id="tabprefix3"]/div/div/table/tbody/tr'
        self.posicao_elementos = {'tipo': 2, 'esp': 4, 'data': 3, 'usr': 5}
        self.formato_data = '%d/%m/%Y %H:%M:%S'
        self.remover_primeira_tr = False
        self.capturar_todas_movs = False

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        self.driver.find_element_by_id("login").send_keys(usuario)
        self.driver.find_element_by_id("senha").send_keys(senha)
        self.driver.find_element_by_id("senha").send_keys(Keys.ENTER)

        if not aguarda_presenca_elemento(self.driver, 'BarraMenu', tipo='ID'):
            return False

        return True

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        adc = self.audiencias()
        prt = self.partes()
        adv = self.responsaveis()
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        prc = self.dados(status_atual)

        return adc, prt, prc, adv

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''

        # self.driver.find_element_by_xpath('//*[@id="buscaProcessosQualquerInstanciaForm"]/fieldset/table/tbody/tr[2]/td[2]/input[2]').click()
        if self.grau != 2:
            try_click(self.driver, '//*[@id="buscaProcessosQualquerInstanciaForm"]/fieldset/table/tbody/tr[2]/td[2]/input[2]')
        else:
            try_click(self.driver, '//*[@id="buscaProcessosQualquerInstanciaForm"]/fieldset/table/tbody/tr[1]/td[2]/input[2]')

        id_campo_busca = 'numeroRecurso' if self.grau == 2 else 'numeroProcesso'
        aguarda_presenca_elemento(self.driver, id_campo_busca, tipo='ID')
        try:
            self.driver.find_element_by_id(id_campo_busca).clear()
        except:
            raise CriticalException("Campo de busca não localizado", self.uf, self.plataforma, self.prc_id, False)

        self.driver.find_element_by_id(id_campo_busca).send_keys(numero_busca)
        self.driver.find_element_by_id(id_campo_busca).send_keys(Keys.ENTER)
        time.sleep(0.2)
        inicio = time.time()
        while True:
            if time.time() - inicio > 15:
                raise MildException("Erro ao let campo", self.uf, self.plataforma, self.prc_id)

            if not self.driver.find_element_by_id(id_campo_busca):
                break

            readonly = ''
            try:
                readonly = self.driver.find_element_by_id(id_campo_busca).get_attribute('readonly')
            except:
                break
            if readonly is None:
                break

        msg_erro = self.driver.find_element_by_id('errorMessages')
        if msg_erro:
            if find_string(msg_erro.text, ('Alguns erros',)):
                return False

        if self.grau == 2:
            msg_registros = self.driver.find_element_by_xpath('//*[@id="navigator"]/div[2]')
            if msg_registros and msg_registros.text == '0 registro(s) encontrado(s)':
                return False

        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        cnj = self.driver.find_element_by_xpath('//*[@id="buscaProcessosQualquerInstanciaForm"]/table[2]/tbody/tr/td[2]/a')
        cnj_limpo = ajusta_numero(cnj.text)
        if cnj_limpo != numero_busca:
            raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        el = self.driver.find_element_by_xpath('//*[@id="buscaProcessosQualquerInstanciaForm"]/table[2]/tbody/tr/td[3]')
        if el:
            if el.text.find('Segredo de Justiça') > -1:
                return True

        self.confere_cnj(numero_busca)

        a = self.driver.find_element_by_xpath('//*[@id="buscaProcessosQualquerInstanciaForm"]/table[2]/tbody/tr/td[2]/a')
        if a:
            url = a.get_attribute('href')
            self.driver.execute_script("window.open('" + url + "', '_self')")

        return False

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''

        # try_click(self.driver, '//*[@id="buscaProcessosQualquerInstanciaForm"]/table[2]/tbody/tr/td[2]/a')

        citacao = self.driver.find_element_by_xpath('//*[@id="citacaoAdvogadoForm"]/h3')
        if citacao:
            if citacao.text == 'Citações':
                return True

        citacao = self.driver.find_element_by_xpath('//*[@id="intimacaoAdvogadoForm"]/h3')
        if citacao:
            if citacao.text == 'Intimações':
                return True

        if self.grau == 2:
            self.driver.execute_script("setTab('/projudi#', 'tabMovimentacoesRecurso', 'prefix', 2, false);")

        data_ultima_mov = self.driver.find_element_by_xpath(self.tabela_movs+'[1]/td['+str(self.posicao_elementos['data'])+']').text
        data_ultima_mov = strip_html_tags(data_ultima_mov)

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
        if self.grau == 2:
            self.driver.execute_script("setTab('/projudi#', 'tabMovimentacoesRecurso', 'prefix', 2, false);")

        ultima_mov = proc_data['cadastro']
        prc_id = proc_data['prc_id']
        # try_click(self.driver, '//*[@id="buscaProcessosQualquerInstanciaForm"]/table[2]/tbody/tr/td[2]/a')
        if try_click(self.driver, 'botaoTotalMov', tipo='ID'):
            time.sleep(0.3)
            aguarda_presenca_elemento(self.driver, self.tabela_movs)

        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(EC.presence_of_all_elements_located((By.XPATH, self.tabela_movs)))
        except TimeoutException:
            raise MildException("Erro ao carregar tabela de movs.", self.uf, self.plataforma, self.prc_id)

        movs = []
        self.movs = []

        movimentos = self.driver.find_elements_by_xpath(self.tabela_movs)
        capturar = True
        i = 0
        if len(movimentos) == 0:
            raise MildException("Erro ao capturar tabela de movs.", self.uf, self.plataforma, self.prc_id)

        if len(movimentos)>500:
            if self.grau == 1:
                if self.driver.find_element_by_xpath("//select[@name='movimentacoesPageSizeOptions']/option[@value='1000']"):
                    self.driver.find_element_by_xpath("//select[@name='movimentacoesPageSizeOptions']/option[@value='1000']").click()
            else:
                if self.driver.find_element_by_xpath("//select[@name='movimentacoesRecursoPageSizeOptions']/option[@value='1000']"):
                    self.driver.find_element_by_xpath("//select[@name='movimentacoesRecursoPageSizeOptions']/option[@value='1000']").click()

            movimentos = self.driver.find_elements_by_xpath(self.tabela_movs)
            if len(movimentos) == 0:
                raise MildException("Erro ao capturar tabela de movs.", self.uf, self.plataforma, self.prc_id)

        if self.remover_primeira_tr:
            movimentos.pop(0)

        for mov in movimentos:
            acps_cadastro = mov.find_elements_by_xpath('td['+str(self.posicao_elementos['data'])+']')
            if len(acps_cadastro) == 0:
                continue
            acp_cadastro = acps_cadastro[0].text.strip()
            if acp_cadastro == '':
                continue
            acp_cadastro = datetime.strptime(acp_cadastro, self.formato_data)

            i += 1
            if acp_cadastro == ultima_mov:
                capturar = False
                if not completo and i >= 10 and not self.capturar_todas_movs:
                    break

            acp_tipo = mov.find_element_by_xpath('td['+str(self.posicao_elementos['tipo'])+']').text
            acp_esp = mov.find_element_by_xpath('td['+str(self.posicao_elementos['esp'])+']').text
            acp_usuario = mov.find_element_by_xpath('td[' + str(self.posicao_elementos['usr']) + ']').text
            acp_tipo = strip_html_tags(acp_tipo)
            acp_esp = strip_html_tags(acp_esp)
            acp_usuario = strip_html_tags(acp_usuario)

            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp.strip(), 'acp_tipo': acp_tipo.strip(), 'acp_usuario': acp_usuario.strip()}
            if capturar:
                movs.append(acp)

            self.movs.append({**acp, 'novo': capturar})

        return movs

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []
        movs = self.movs[:]
        movs.reverse()
        for mov in movs:
            if not self.completo and not mov['novo']:
                break

            esp = mov['acp_esp'].upper().strip()

            if esp.find('AUDIÊNCIA') != 0 or esp == 'AUDIÊNCIA':
                continue

            r = re.search("(\\d+)(\\s+)(de)(\\s+)([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÍÏÓÔÕÖÚÇÑ]+)(\\s+)(de)(\\s+)(\\d+)(\\s+)(às)(\\s+)(\\d+)(\\:)(\\d+)", esp, re.IGNORECASE | re.DOTALL)
            if r is None:
                continue

            reg_data = r.group(0)
            data_padrao = localiza_data(esp, True)
            esp = esp.replace(reg_data, data_padrao)
            aud = localiza_audiencia(esp, formato_data='%Y-%m-%d %H:%M', formato_re='(\\d+)(\\-)(\\d+)(\\-)(\\d+)(\\s+)(\\d+)(\\:)(\\d+)')
            if not aud:
                continue

            erro = ''
            if 'prp_status' not in aud:
                erro = 'Status'
            if 'prp_tipo' not in aud:
                erro = 'Tipo'

            if erro != '':
                raise MildException("Audiência - "+erro+" não localizado: "+esp, self.uf, self.plataforma, self.prc_id)

            serventia = None
            p = esp.find('(AGENDADA PARA')
            if p > -1:
                esp_spl = esp.split(',')
                if len(esp_spl) > 1:
                    serventia = esp_spl[1][3:-1].strip()
            aud['prp_serventia'] = serventia
            aud['data_mov'] = mov['acp_cadastro']
            adcs.append(aud)

        return adcs

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': [], 'terceiro': []}
        nomes = []
        self.driver.execute_script("setTab('/projudi/visualizacaoProcesso.do?actionType=visualizar', 'tabPartes', 'prefix', 2, true);")
        # self.driver.find_element_by_xpath('//*[@id="tabItemprefix2"]/div[2]/a').click()

        tabela = self.driver.find_elements_by_xpath('//*[@id="includeContent"]/table')
        self.driver.execute_script("window.scrollTo( 0, 0 );")
        i = 0
        for tb in tabela:
            i += 1
            tipo_parte_txt = self.driver.find_element_by_xpath('//*[@id="includeContent"]/h4['+str(i)+']')
            if not tipo_parte_txt:
                continue
            tipo_parte_txt = tipo_parte_txt.text
            achei = False
            for polo in self.titulo_partes:
                if find_string(tipo_parte_txt, self.titulo_partes[polo]):
                    achei = True
                    if polo == 'ignorar':
                        break

                    lista = tb.find_elements_by_xpath('tbody/tr')
                    # polo = 'ativo' if i == 0 else 'passivo'

                    for l in lista:
                        td4 = l.find_elements_by_xpath('td[4]')
                        if len(td4) == 0:
                            continue

                        prt_nome = l.find_element_by_xpath('td[2]').text
                        prt_nome = prt_nome.replace('(em Recuperação Judicial)', '')

                        p = prt_nome.find('(citação')
                        if p > -1:
                            prt_nome = prt_nome[:p-1]

                        p = prt_nome.find('representad')
                        if p > -1:
                            prt_nome = prt_nome[:p-1]

                        if prt_nome in nomes:
                            continue
                        nomes.append(prt_nome)

                        prt_cpf_cnpj = td4[0].text
                        if prt_cpf_cnpj == 'Não Cadastrado':
                            prt_cpf_cnpj = 'Não Informado'

                        partes[polo].append({'prt_nome': prt_nome.strip(), 'prt_cpf_cnpj': prt_cpf_cnpj})

                    break

            if not achei:
                raise MildException("polo vazio " + tipo_parte_txt, self.uf, self.plataforma, self.prc_id)

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        tabela = self.driver.find_elements_by_xpath('//*[@id="includeContent"]/table')
        self.driver.execute_script("window.scrollTo( 0, 0 );")
        i = 0
        for tb in tabela:
            i += 1
            lista = tb.find_elements_by_xpath('tbody/tr')
            # polo = 'Polo Ativo' if i==0 else 'Polo Passivo'
            tipo_parte_txt = self.driver.find_element_by_xpath('//*[@id="includeContent"]/h4['+str(i)+']')
            if not tipo_parte_txt:
                continue
            tipo_parte_txt = tipo_parte_txt.text

            for polo in self.titulo_partes:
                if find_string(tipo_parte_txt, self.titulo_partes[polo]):
                    if polo == 'ignorar':
                        break

                    for l in lista:
                        td4 = l.find_elements_by_xpath('td[4]')
                        if len(td4) == 0:
                            continue

                        advs = l.find_elements_by_xpath('td[6]/ul/li[1]')
                        for adv in advs:
                            prr_nome = adv.text
                            if find_string(prr_nome,('Parte sem advogado','Advogado não cadastrado')):
                                continue

                            if polo == 'ativo':
                                polo_adv = 'Polo Ativo'
                            if polo == 'passivo':
                                polo_adv = 'Polo Passivo'

                            p1 = prr_nome.find(' - ')
                            p2 = prr_nome.find('OAB')
                            prr_oab = prr_nome[p2 + 3:p1 - 1].strip()
                            prr_nome = prr_nome[p1+3:].strip()
                            r = prr_nome.find('**')
                            if r > -1:
                                prr_nome = prr_nome[:r].strip()
                            resps.append({'prr_nome': prr_nome, 'prr_oab': prr_oab, 'prr_cargo': 'Advogado', 'prr_parte': polo_adv})


        # CAPTURA NOME DO JUIZ
        # self.driver.find_element_by_partial_link_text('Informações Gerais').click()
        tab_script = "setTab('/projudi/visualizacaoProcesso.do?actionType=visualizar', 'tabDadosProcesso', 'prefix', 0, true);" if self.grau != 2 else "setTab('/projudi#', 'tabDadosRecurso', 'prefix', 0, false);"
        try:
            self.driver.execute_script(tab_script)
        except:
            try:
                self.driver.refresh()
                self.driver.execute_script(tab_script)
            except:
                raise MildException("Erro ao abrir aba de dados", self.uf, self.plataforma, self.prc_id)

        if self.grau == 1:
            trs = self.driver.find_elements_by_xpath('//*[@id="includeContent"]/fieldset/table/tbody/tr')
        else:
            trs = self.driver.find_elements_by_xpath('//*[@id="tabprefix0"]/fieldset/table/tbody/tr')

        if len(trs) == 0:
            self.driver.refresh()
            if self.grau != 2:
                self.driver.find_element_by_partial_link_text('Informações Gerais').click()
            else:
                self.driver.find_element_by_partial_link_text('Dados do Recurso').click()
            if self.grau == 1:
                trs = self.driver.find_elements_by_xpath('//*[@id="includeContent"]/fieldset/table/tbody/tr')
            else:
                trs = self.driver.find_elements_by_xpath('//*[@id="tabprefix0"]/fieldset/table/tbody/tr')
            if len(trs) == 0:
                raise MildException("Erro na captura de dados", self.uf, self.plataforma, self.prc_id)

        if self.grau == 1:
            i = 0
            juiz = ''
            for tr in trs:
                i += 1
                if juiz != '':
                    break

                tds = tr.find_elements_by_tag_name('td')
                j = 1
                for td in tds:
                    j += 1
                    label = td.find_elements_by_tag_name('label')
                    if len(label) == 0:
                        continue
                    if td.text.upper().find('JUIZ:') > -1:
                        juiz = self.driver.find_element_by_xpath('//*[@id="includeContent"]/fieldset/table/tbody/tr['+str(i)+']/td['+str(j)+']').text
                        break

            if juiz != '':
                resps.append({'prr_nome': juiz.strip(), 'prr_oab': '', 'prr_cargo': 'Juiz', 'prr_parte': ''})

        return resps

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}
        self.confere_sub_processos()

        # LOCALIZA STATUS DO PROCESSO
        prc['prc_status'] = get_status(self.movs, status_atual)

        campos = {'Valor da Causa': 'prc_valor_causa', 'Juízo': 'prc_juizo', 'Comarca': 'prc_comarca2', 'Distribuição': 'prc_distribuicao', 'Data do Trânsito em Julgado': 'prc_data_transito' }

        trs = self.driver.find_elements_by_xpath('//*[@id="includeContent"]/fieldset/table/tbody/tr')
        i = 0
        for tr in trs:
            i += 1
            tds = tr.find_elements_by_tag_name('td')
            j = 1
            for td in tds:
                j += 1
                label = td.find_elements_by_tag_name('label')
                if len(label) == 0:
                    continue
                titulo = td.text

                for c in campos:
                    if titulo.upper().find(c.upper()) > -1:
                        prc[campos[c]] = self.driver.find_element_by_xpath('//*[@id="includeContent"]/fieldset/table/tbody/tr['+str(i)+']/td['+str(j)+']').text
                        break

        if 'prc_juizo' not in prc:
            raise MildException("Juízo não localizado: ", self.uf, self.plataforma, self.prc_id)

        prc['prc_serventia'] = prc['prc_juizo']
        if 'prc_data_transito' in prc:
            r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)', prc['prc_data_transito'])
            if r:
                prc_data_transito = r.group(0)
                prc['prc_data_transito'] = datetime.strptime(prc_data_transito, '%d/%m/%Y')
            else:
                del prc['prc_data_transito']

        if 'prc_distribuicao' in prc:
            r = re.search('(\\d+)(\\/)(\\d+)(\\/)(\\d+)', prc['prc_distribuicao'])
            prc_distribuicao = r.group(0)
            prc['prc_distribuicao'] = datetime.strptime(prc_distribuicao, '%d/%m/%Y')


        campos = {'Classe Processual': 'prc_classe', 'Assunto Principal': 'prc_assunto', 'Nível de Sigilo': 'prc_segredo'}
        trs = self.driver.find_elements_by_xpath('//*[@id="informacoesProcessuais"]/tbody/tr')
        for tr in trs:
            tds = tr.find_elements_by_xpath('td[1]')
            if len(tds) == 0:
                continue

            titulo = tds[0].text
            for c in campos:
                if titulo.upper().find(c.upper()) > -1:
                    prc[campos[c]] = tr.find_element_by_xpath('td[2]').text

        if 'prc_segredo' in prc:
            prc['prc_segredo'] = False if prc['prc_segredo'].find('Público') > -1 else True

        prc_numero2 = self.driver.find_element_by_id('barraTituloStatusProcessual').text
        prc_numero2 = localiza_cnj(prc_numero2)
        prc['prc_numero2'] = prc_numero2


        return prc

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, target_dir):
        arquivos = []
        total_arquivos = 0
        if self.grau == 1:
            self.driver.execute_script("setTab('/projudi/visualizacaoProcesso.do?actionType=visualizar', 'tabMovimentacoesProcesso', 'prefix', 3, true);")
        else:
            self.driver.execute_script("setTab('/projudi#', 'tabMovimentacoesRecurso', 'prefix', 2, false);")
        # self.driver.find_element_by_xpath('//*[@id="tabItemprefix3"]/div[2]/a').click()
        aguarda_presenca_elemento(self.driver, self.tabela_movs)
        try:
            if self.driver.find_element_by_id('habilitacaoProvisoriaButton'):
                onclick = self.driver.find_element_by_id('habilitacaoProvisoriaButton').get_attribute('onclick')
                self.driver.execute_script(onclick)

                # if not self.driver.find_element_by_id('termoAceito'):
                #     self.driver.find_element_by_id('habilitacaoProvisoriaButton').click()

                if not self.driver.find_element_by_id('termoAceito'):
                    self.driver.refresh()

                self.driver.execute_script('document.getElementById("termoAceito").checked = true;')
                # self.driver.find_element_by_id('termoAceito').click()
                onclick = self.driver.find_element_by_id('saveButton').get_attribute('onclick')
                self.driver.execute_script(onclick)
                # self.driver.find_element_by_id('saveButton').click()
        except:
            # tb = traceback.format_exc()
            raise MildException("Erro ao habilitar processo", self.uf, self.plataforma, self.prc_id)

        # if self.grau == 1:
        #     self.driver.execute_script("displayRow('mov1Grau', 'movimentacoes', 'SEMARQUIVO', this.checked)")
        # else:
        #     self.driver.execute_script("displayRow('mov2Grau','movimentacoesRecurso','SEMARQUIVO',this.checked)")

        # if not self.driver.find_element_by_id('gruposOcultarFiltroSEMARQUIVO'):
        #     self.driver.refresh()
        #     time.sleep(1)
        #
        # try:
        #
        #     self.driver.find_element_by_id('gruposOcultarFiltroSEMARQUIVO').click()
        # except:
        #     raise MildException("Erro ao ocultar movimentações ", self.uf, self.plataforma, self.prc_id)

        time.sleep(0.5)

        movimentos = self.driver.find_elements_by_xpath(self.tabela_movs)
        if len(movimentos) > 500:
            if self.grau == 1:
                if self.driver.find_element_by_xpath("//select[@name='movimentacoesPageSizeOptions']/option[@value='1000']"):
                    self.driver.find_element_by_xpath("//select[@name='movimentacoesPageSizeOptions']/option[@value='1000']").click()
            else:
                if self.driver.find_element_by_xpath("//select[@name='movimentacoesRecursoPageSizeOptions']/option[@value='1000']"):
                    self.driver.find_element_by_xpath("//select[@name='movimentacoesRecursoPageSizeOptions']/option[@value='1000']").click()

            movimentos = self.driver.find_elements_by_xpath(self.tabela_movs)

        i = 1
        existe = False
        baixar = True
        for mov in movimentos:
            if existe and len(pendentes) == 0:
                break

            i += 1
            a = mov.find_elements_by_xpath('td[1]/a')
            if len(a) > 0:
                pra_data = mov.find_element_by_xpath('td[3]').text
                pra_data = datetime.strptime(pra_data, self.formato_data)
                a[0].location_once_scrolled_into_view
                a[0].click()
                time.sleep(0.2)

                if self.grau == 1:
                    lista = mov.find_elements_by_xpath('//*[@id="includeContent"]/table/tbody/tr['+str(i)+']/td/div/table/tbody/tr')
                else:
                    lista = mov.find_elements_by_xpath('//*[@id="includeContent"]/table/tbody/tr[' + str(i) + ']/td/div/table/tbody/tr')

                for ls in lista:
                    existe = False
                    arq = {}
                    td1 = ls.find_element_by_xpath('td[1]')
                    td1.location_once_scrolled_into_view
                    pra_descricao = td1.text
                    f = pra_descricao.find('Arquivo')
                    arq['pra_id_tj'] = pra_descricao[:f-1].strip()
                    arq['pra_prc_id'] = prc_id
                    arq['pra_grau'] = self.grau
                    arq['pra_data'] = pra_data
                    arq['pra_plt_id'] = self.plataforma
                    arq['pra_descricao'] = pra_descricao
                    arq['pra_erro'] = True
                    arq['pra_tentativas'] = None

                    if len(pendentes) > 0:
                        for pen in pendentes[:]:
                            if pen['pra_id_tj'] == arq['pra_id_tj'] and pen['pra_grau'] == self.grau and pen['pra_data'] == arq['pra_data']:
                                arq['pra_id'] = pen['pra_id']
                                arq['pra_tentativas'] = pen['pra_tentativas']
                                pendentes.remove(pen)
                                break

                    if 'pra_id' not in arq:
                        for arb in arquivos_base:
                            # print(arb['pra_id_tj'], arq['pra_id_tj'], arb['pra_data'], arq['pra_data'])
                            if arq['pra_id_tj'] == arb['pra_id_tj'] and arb['pra_data'] == arq['pra_data'] and arb['pra_grau'] == self.grau:
                                existe = True
                                break

                        if existe:
                            if len(pendentes) == 0:
                                break
                            continue

                    if self.tipo != 2:
                        limpar_pasta(self.pasta_download)
                        arq['pra_sigilo'] = False
                        td5 = ls.find_elements_by_xpath('td[5]')
                        if td5 is None or len(td5) == 0:
                            raise MildException('td5 não localizado ' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                        if td5[0].text.find('Restrição na Visualização') > -1:
                            arq['pra_sigilo'] = True
                        else:
                            elements = td5[0].find_elements_by_tag_name('a')
                            if elements is None or len(elements) == 0:
                                raise MildException('link não localizado ' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                            if elements[0].get_attribute('title').find('Não é permitido') > -1:
                                arq['pra_sigilo'] = True

                        if arq['pra_sigilo']:
                            arq['pra_erro'] = False
                            arq['pra_original'] = None
                            arq['pra_arquivo'] = None
                            baixar = False
                        else:
                            # exts = ('.webm','.wmv','.mp4','.wav','.ogg','.mp3')
                            # for ext in exts:
                            #     if elements[0].text.endswith(ext):
                            #         self.driver.execute_script("arguments[0].setAttribute('download', 'True')", elements[0])
                            #         break
                            play = td5[0].find_elements_by_class_name('play')
                            if len(play) > 0:
                                self.driver.execute_script("arguments[0].setAttribute('download', 'True')", elements[0])

                            baixar = True
                            ls.find_element_by_xpath('td[5]/a').click()
                            if len(self.driver.window_handles) > 1:
                                try:
                                    self.driver.switch_to.window(self.driver.window_handles[1])
                                except:
                                    pass
                                try:
                                    msg = self.driver.find_element_by_xpath('//*[@id="errorMessages"]/div[3]/div').text
                                    if msg:
                                        if msg.find('erros foram encontrados') > -1:
                                            arq['pra_erro'] = True
                                            arq['pra_original'] = None
                                            arq['pra_arquivo'] = None
                                            baixar = False
                                    else:
                                        # time.sleep(9999)
                                        raise CriticalException('Janela download aberta ' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)
                                    self.driver.close()
                                except:
                                    pass
                                self.driver.switch_to.window(self.driver.window_handles[0])

                            if baixar:
                                arq['pra_erro'] = False if aguarda_download(self.pasta_download, 1) else True

                        pra_usuario = ls.find_element_by_xpath('td[3]').text
                        arq['pra_usuario'] = pra_usuario[5:]

                        if not arq['pra_erro'] and not arq['pra_sigilo']:
                            total_arquivos += 1
                            file_names = os.listdir(self.pasta_download)
                            arq['pra_original'] = file_names[0]
                            pra_arquivo = trata_arquivo(file_names[0], self.pasta_download, target_dir)
                            arq['pra_arquivo'] = pra_arquivo
                        elif arq['pra_erro'] and self.tipo != 2:
                            arq['pra_original'] = None
                            arq['pra_arquivo'] = None
                            arq['pra_tentativas'] = 1 if arq['pra_tentativas'] is None else arq['pra_tentativas'] + 1
                            print('erro download')
                            # time.sleep(9999)
                            # raise MildException('erro download ' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)


                    arq['pra_data_insert'] = datetime.now()
                    arquivos.append(arq)

        arquivos.reverse()
        return arquivos

    def confere_sub_processos(self):
        pesquisa_recurso = True
        pl = False
        if self.grau == 1:
            lista = self.driver.find_elements_by_xpath('//*[@id="trApensamento"]/td[2]/div/div/a')
            for l in lista:
                txt = l.text
                if find_string(txt, ('Invalidado',)):
                    continue
                if find_string(txt, ('Processo:',)):
                    prc_numero = localiza_cnj(txt)
                    print(prc_numero)
                    self.insere_novo_processo(prc_numero)

            pl = self.driver.find_element_by_partial_link_text('Clique aqui para visualizar os recursos')
            if not pl:
                pesquisa_recurso = False
            else:
                href = pl.get_attribute('href')
                self.driver.execute_script("window.open('" + href + "', '_blank')")
                self.alterna_janela(1, 1)

        if pesquisa_recurso:
            lista = self.driver.find_elements_by_xpath('//*[@id="recursoForm"]/fieldset/table[1]/tbody/tr/td[2]/div/div/a')
            if len(lista) <= 3 and self.grau == 2:
                return

            for l in lista:
                txt = l.text
                if find_string(txt, ('Invalidado',)):
                    continue
                if find_string(txt, ('Recurso',)):
                    inicio = txt.find(':')
                    fim = txt.rfind('-')
                    rec_codigo = txt[inicio + 1:fim].strip()
                    rec_codigo = rec_codigo.replace('- Recurso Inominado Cível', '').strip()
                    rec_codigo = rec_codigo.replace('- Apelação Cível','').strip()
                    rec_codigo = rec_codigo.replace('- Agravo de Instrumento', '').strip()
                    rec_codigo = rec_codigo.replace('- Mandado de Segurança', '').strip()
                    rec_codigo = rec_codigo.replace(' - Incidente de Uniformização de Interpretação de Lei', '').strip()
                    rec_numero = localiza_cnj(rec_codigo)
                    print(rec_codigo)
                    result = Recurso.select(self.conn_atual, self.prc_id, rec_codigo)
                    if len(result) == 0:
                        Recurso.insert(self.conn_atual,
                                       {'rec_prc_id': self.prc_id, 'rec_codigo': rec_codigo, 'rec_numero': rec_numero,
                                        'rec_plt_id': self.plataforma})

        if self.grau == 1 and pl:
            self.driver.close()
            wh = self.driver.window_handles
            self.driver.switch_to.window(wh[0])
