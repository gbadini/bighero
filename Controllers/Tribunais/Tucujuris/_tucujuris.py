from Config.helpers import *
from Controllers.Tribunais.primeiro_grau import *
from selenium.webdriver.common.keys import *
from Models.processoModel import *
import sys, time, shutil
import urllib.parse as urlparse
from urllib.parse import parse_qs

# CLASSE DA VARREDURA DO PROJUDI. HERDA OS METODOS DA CLASSE PLATAFORMA
class Tucujuris(PrimeiroGrau):

    def __init__(self):
        super().__init__()
        self.plataforma = 6
        self.movs = []
        self.formato_data = '%d/%m/%Y %H:%M'

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''

        # self.wait()

        if not aguarda_presenca_elemento(self.driver, 'usuario', tipo='ID'):
            return False
        time.sleep(3)
        self.driver.find_element_by_id("usuario").send_keys(usuario)
        self.driver.find_element_by_id("senha").send_keys(senha)
        self.driver.find_element_by_id("senha").send_keys(Keys.ENTER)
        self.wait()
        if not aguarda_presenca_elemento(self.driver, 'dropdownMenuPerfilUsuario', tipo='ID'):
            return False

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        self.wait()

        # Carrega nro do processo
        self.driver.find_element_by_xpath('//*[@id="form-consulta"]/div/form/div[1]/div/div/div/input').clear()
        self.driver.find_element_by_xpath('//*[@id="form-consulta"]/div/form/div[1]/div/div/div/input').send_keys(numero_busca)

        # Clica em 'todos'
        self.driver.find_element_by_xpath('//*[@id="form-consulta"]/div/form/div[5]/div/label[4]/input').click()

        # AGUARDA O CAMPO SER PREENCHIDO
        inicio = time.time()
        valor_campo = self.driver.find_element_by_xpath('//*[@id="form-consulta"]/div/form/div[1]/div/div/div/input').get_attribute('value')
        while len(valor_campo) < 25:
            if time.time() - inicio > 30:
                raise MildException("Erro ao preencher campo de busca", self.uf, self.plataforma, self.prc_id)

            valor_campo = self.driver.find_element_by_xpath('//*[@id="form-consulta"]/div/form/div[1]/div/div/div/input').get_attribute('value')
            time.sleep(1)

        # Clica em consultar
        self.driver.find_element_by_id('btnConsultar').click()

        self.wait()
        aguarda_presenca_elemento(self.driver, 'titulo-secao-pagina', tipo='CLASS_NAME')
        # CONFERE SE LOCALIZOU
        msg_erro = self.driver.find_element_by_xpath('//*[@id="resultado-consulta"]/div/div/h4')
        if msg_erro:
            if msg_erro.text.upper().find('NENHUM RESULTADO') > -1:
                return False

        btn = self.driver.find_element_by_xpath('//*[@id="resultado-consulta"]/div/div[2]/div/div/a/cabecalhoprocesso/div/div/div[1]/h3/small[2]/a')
        if not btn:
            raise MildException("Erro ao buscar processo", self.uf, self.plataforma, self.prc_id)

        btn.click()
        self.alterna_janela()

        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        self.wait()
        if not aguarda_presenca_elemento(self.driver, 'numcnj', tipo='CLASS_NAME'):
            raise MildException("Erro ao abrir página", self.uf, self.plataforma, self.prc_id)

        cnj = self.driver.find_element_by_class_name('numcnj')
        cnj_limpo = ajusta_numero(cnj.text)
        while cnj_limpo.strip('0') == '':
            cnj = self.driver.find_element_by_class_name('numcnj')
            cnj_limpo = ajusta_numero(cnj.text)
            time.sleep(1)


        if cnj_limpo != numero_busca:
            raise MildException("Número CNJ Diferente - "+cnj_limpo+" - "+numero_busca, self.uf, self.plataforma, self.prc_id)

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        self.erro_sessao()
        self.wait()
        body = self.driver.find_element_by_id('main-content').text
        if body.find('Segredo de justiça -') > -1:
            return True

        self.confere_cnj(numero_busca)

        return False

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''

        data_ultima_mov = self.driver.find_element_by_xpath('//*[@id="main-content"]/div/div[2]/detalhesprocesso/partial/div/div/div[3]/historicoprocesso/div/div[1]/div[1]/div[1]/span[2]/span')

        if not data_ultima_mov:
            data_ultima_mov = self.driver.find_element_by_xpath('//*[@id="lista-tramitacoes"]/historicoprocesso/div/div[1]/div[1]/div[1]/span[2]/span')

        data_ultima_mov = strip_html_tags(data_ultima_mov.text)
        data_ultima_mov = data_ultima_mov.replace('h','')
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
        prc_id = proc_data['prc_id']
        movs = []
        self.movs = []
        i = 0
        capturar = True
        movimentos = self.driver.find_elements_by_css_selector('div.tj-historicos > div')
        for mov in movimentos:
            acp_cadastro = mov.find_element_by_xpath('div[1]/span[2]/span').text
            acp_cadastro = acp_cadastro.replace('h', '')
            acp_cadastro = datetime.strptime(acp_cadastro, self.formato_data)

            i += 1
            if acp_cadastro == ultima_mov:
                capturar = False
                if not completo and i >= 10:
                    break

            acp_tipo = mov.find_element_by_xpath('div[2]/span[1]').text
            acp_esp = mov.find_element_by_xpath('div[2]/p[1]').text
            acp_tipo = strip_html_tags(acp_tipo)
            acp_esp = strip_html_tags(acp_esp)

            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp.strip(), 'acp_tipo': acp_tipo.strip(),}
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
            if tipo.find('AUDIÊNCIA') != 0:
                continue

            aud = localiza_audiencia(tipo.replace(' ÀS ',' '))
            if not aud:
                continue

            erro = ''
            if 'prp_status' not in aud:
                erro = 'Status '
            if 'prp_tipo' not in aud:
                erro = 'Tipo '

            if erro != '':
                raise MildException("Audiência - "+erro+" não localizado: "+tipo, self.uf, self.plataforma, self.prc_id)

            serventia = self.driver.find_element_by_xpath('//*[@id="main-content"]/div/div[2]/detalhesprocesso/partial/div/div/div[1]/div[1]/cabecalhoprocesso/div/div/p/span[1]').text

            aud['prp_serventia'] = serventia
            aud['data_mov'] = mov['acp_cadastro']
            adcs.append(aud)

        return adcs

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': []}
        nomes = []

        tabela = self.driver.find_elements_by_xpath('//*[@id="main-content"]/div/div[2]/detalhesprocesso/partial/div/div/div[2]/div')
        i = 0
        for tb in tabela:
            polo = ''
            div_polo = tb.find_element_by_xpath('div[1]/div/div[1]').text.upper()
            if find_string(div_polo, ('AUTOR','RECORRENTE','REQUERENTE','APELANTE')):
                polo = 'ativo'

            if find_string(div_polo, ('RÉ','RECORRIDO','REQUERIDO','APELADO')):
                polo = 'passivo'

            if polo == '':
                raise MildException("Polo não localizado", self.uf, self.plataforma, self.prc_id)

            prt_nome = tb.find_element_by_xpath('div[1]/div/div[2]').text
            prt_cpf_cnpj = 'Não Informado'
            if prt_nome == '':
                continue
            partes[polo].append({'prt_nome': prt_nome.strip(), 'prt_cpf_cnpj': prt_cpf_cnpj})

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []
        tabela = self.driver.find_elements_by_xpath('//*[@id="main-content"]/div/div[2]/detalhesprocesso/partial/div/div/div[2]/div')
        i = 0
        for tb in tabela:
            polo = ''
            div_polo = tb.find_element_by_xpath('div[1]/div/div[1]').text.upper()
            if find_string(div_polo, ('AUTOR','RECORRENTE','REQUERENTE',)):
                polo = 'Polo Ativo'

            if find_string(div_polo, ('RÉ','RECORRIDO','REQUERIDO',)):
                polo = 'Polo Passivo'

            prr_nome = tb.find_element_by_xpath('div[2]/div/div[2]').text.strip()
            if prr_nome == '':
                continue
            resps.append({'prr_nome': prr_nome, 'prr_oab': '', 'prr_cargo': 'Advogado', 'prr_parte': polo})

        return resps

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}
        prc['prc_status'] = get_status(self.movs, status_atual)
        prc['prc_numero2'] = self.driver.find_element_by_class_name('numcnj').text

        url = self.driver.execute_script('return window.location')
        parsed = urlparse.urlparse(url['href'])
        parse_qs(parsed.query)
        url_params = parse_qs(parsed.query)
        prc['prc_codigo'] = url_params['id'][0]

        prc['prc_assunto'] = self.driver.find_element_by_xpath('//*[@id="main-content"]/div/div[2]/detalhesprocesso/partial/div/div/div[1]/div[1]/cabecalhoprocesso/div/div/p/span[3]').text
        prc['prc_serventia'] = self.driver.find_element_by_xpath('//*[@id="main-content"]/div/div[2]/detalhesprocesso/partial/div/div/div[1]/div[1]/cabecalhoprocesso/div/div/p/span[1]').text
        prc_comarca2 = self.driver.find_element_by_xpath('//*[@id="main-content"]/div/div[2]/detalhesprocesso/partial/div/div/div[1]/div[1]/cabecalhoprocesso/div/div/p/span[2]').text
        prc['prc_comarca2'] = localiza_comarca(prc_comarca2, self.uf)

        self.movs.reverse()
        prc['prc_distribuicao'] = None
        for m in self.movs:
            if m['acp_tipo'].find('Distribuído') > -1:
                prc['prc_distribuicao'] = m['acp_cadastro']
                break


        return prc

    # AGUARDA ATÉ QUE A ANIMAÇÃO DE LOADING ESTEJA OCULTA
    def wait(self, tempo=30):

        # if id == 'dapageloader':
        ok = 0
        inicio = time.time()
        while True:
            if time.time() - inicio > tempo:
                raise MildException("Erro ao carregar página", self.uf, self.plataforma, self.prc_id)

            if ok == 2:
                break
            ok = 0

            if not self.driver.find_element_by_id('dapageloader'):
                ok += 1
            else:
                classe = self.driver.find_element_by_id('dapageloader').get_attribute('class')
                if classe.find('active') == -1:
                    ok += 1
                else:
                    time.sleep(0.2)
                    continue

            els = self.driver.find_elements_by_id('indicador-carregamento')
            if len(els) == 0:
                ok += 1
            else:
                time.sleep(0.2)
                continue

        return True

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, pasta_intermediaria):
        arquivos = []
        movimentos = self.driver.find_elements_by_css_selector('div.tj-historicos > div')
        existe = False
        for mov in movimentos:
            if existe and len(pendentes) == 0:
                break

            links = mov.find_elements_by_class_name('tj-historicoprocesso-texto-anexos')
            if len(links) == 0:
                continue

            if not links[0].is_displayed():
                continue

            acp_cadastro = mov.find_element_by_xpath('div[1]/span[2]/span').text
            acp_cadastro = acp_cadastro.replace('h', '').strip()
            if acp_cadastro == '':
                continue
            acp_cadastro = datetime.strptime(acp_cadastro, self.formato_data)
            acp_tipo = mov.find_element_by_xpath('div[2]/span[1]').text
            acp_tipo = strip_html_tags(acp_tipo)

            links[0].click()
            aguarda_presenca_elemento(self.driver, 'modal-fullscreen', tipo='CLASS_NAME', aguarda_visibilidade=True)
            modal = self.driver.find_element_by_class_name('modal-fullscreen')
            imgs = modal.find_elements_by_xpath('div/div[2]/div[1]/div/div/a')

            i = 0
            for img in imgs:
                i += 1
                arq = {}
                # modal = self.driver.find_element_by_class_name('modal-fullscreen')
                # img = modal.find_element_by_xpath('div/div[2]/div/div/div['+str(i)+']/a')
                btns = img.find_elements_by_class_name('tj-icon-midia-fora-tucujuris')
                download_direto = False
                if len(btns) > 0:
                    btn = img
                    src = btn.get_attribute('href')
                    parsed = urlparse.urlparse(src)
                    parse_qs(parsed.query)
                    url_params = parse_qs(parsed.query)
                    pra_id_tj = url_params['cv'][0]
                    download_direto = True
                else:
                    btns = img.find_elements_by_xpath('previewarquivo/span/img')
                    if len(btns) == 0:
                        if len(btns) == 0:
                            raise MildException('link do arquivo não localizado', self.uf, self.plataforma, self.prc_id)

                    btn = btns[0]
                    src = btn.get_attribute('src')
                    parsed = urlparse.urlparse(src)
                    parse_qs(parsed.query)
                    url_params = parse_qs(parsed.query)
                    pra_id_tj = url_params['id'][0]

                try:
                    btn.click()
                except:
                    time.sleep(3)
                    try:
                        btn.click()
                    except:
                        raise MildException('erro ao clicar no arquivo', self.uf, self.plataforma, self.prc_id)

                pra_descricao = img.find_element_by_xpath('div').text
                pra_descricao += ' - '+acp_tipo
                arq['pra_id_tj'] = pra_id_tj
                arq['pra_tentativas'] = None
                arq['pra_prc_id'] = prc_id
                arq['pra_grau'] = self.grau
                arq['pra_plt_id'] = self.plataforma
                arq['pra_descricao'] = pra_descricao
                arq['pra_data'] = acp_cadastro
                arq['pra_erro'] = True
                arq['pra_excluido'] = False

                limpar_pasta(self.pasta_download)

                if len(pendentes) > 0:
                    for pen in pendentes[:]:
                        if pen['pra_id_tj'] == arq['pra_id_tj']:
                            arq['pra_id'] = pen['pra_id']
                            arq['pra_tentativas'] = pen['pra_tentativas']
                            pendentes.remove(pen)

                if 'pra_id' not in arq:
                    for arb in arquivos_base:
                        if arq['pra_id_tj'] == arb['pra_id_tj']:
                            existe = True
                            break

                    if existe:
                        if len(pendentes) == 0:
                            break
                        continue

                if not download_direto:
                    if self.driver.find_element_by_tag_name('iframe'):
                        self.driver.switch_to.frame(self.driver.find_element_by_tag_name('iframe'))
                        if not aguarda_presenca_elemento(self.driver, 'page', tipo='CLASS_NAME', aguarda_visibilidade=True, tempo=45):
                            erro = self.driver.find_element_by_id('errorMessage')
                            if erro:
                                if erro.text.upper().find('CORROMPIDO') > -1 or erro.text.upper().find('ERRO AO CARREGAR') > -1:
                                    arq['pra_erro'] = False
                                    arq['pra_excluido'] = True
                                    arq['pra_original'] = None
                                    arq['pra_arquivo'] = None

                            if not arq['pra_excluido']:
                                raise MildException('erro ao abrir arquivo ' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                        self.driver.switch_to.default_content()

                    if not arq['pra_excluido']:
                        modal.find_element_by_xpath('div/div[1]/a').click()

                if not arq['pra_excluido']:
                    arq['pra_erro'] = not aguarda_download(self.pasta_download, 1, tempo_nao_iniciado=60)

                    if not arq['pra_erro']:
                        file_names = os.listdir(self.pasta_download)
                        arq['pra_original'] = file_names[0]
                        pra_arquivo = trata_arquivo(file_names[0], self.pasta_download, pasta_intermediaria)
                        arq['pra_arquivo'] = pra_arquivo
                    elif self.tipo != 2:
                        arq['pra_original'] = None
                        arq['pra_arquivo'] = None
                        arq['pra_tentativas'] = 1 if arq['pra_tentativas'] is None else arq['pra_tentativas'] + 1
                        limpar_pasta(self.pasta_download)
                        raise MildException('erro download ' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                arq['pra_data_insert'] = datetime.now()
                arquivos.append(arq)

            modal.find_element_by_xpath('div/div[1]/button').click()
            wait = WebDriverWait(self.driver, 2)
            try:
                wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'modal-fullscreen')))
            except TimeoutException:
                pass

        arquivos.reverse()
        return arquivos

    # CONFERE SE A SESSÃO DO USUÁRIO EXPIROU
    def erro_sessao(self):
        if aguarda_alerta(self.driver, tempo=0.2):
            raise CriticalException("Sessão Encerrada", self.uf, self.plataforma, self.prc_id)

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
