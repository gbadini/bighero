import time
from Controllers.Clientes._cliente import *
from selenium.webdriver.support.ui import Select

# CLASSE PRINCIPAL DO SISTEMA PROCESSUM. HERDA OS METODOS DA CLASSE CLIENTE
class Processum(Cliente):

    def __init__(self):
        super().__init__()
        self.plataforma = 1
        # self.pagina_inicial = "https://ww3.vivo-base.com.br/processumweb/modulo/processo/filtro.jsf"
        self.pagina_inicial = "https://ww3.vivo-base.com.br/processumweb"
        self.pagina_busca = "https://ww3.vivo-base.com.br/processumweb/modulo/processo/filtro.jsf"
        self.movs = []
        self.campo_busca = 'prc_sequencial'
        self.pra_bloqueado = []
        self.drp_bloqueado = []

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None, base=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        if not aguarda_presenca_elemento(self.driver, 'username', tipo='ID'):
            return False

        self.driver.find_element_by_id("username").send_keys(usuario)
        self.driver.find_element_by_id("password").send_keys(senha)
        self.driver.find_element_by_id("password").send_keys(Keys.ENTER)

        erro = self.driver.find_element_by_xpath('//*[@id="form"]/fieldset/p')
        if erro:
            if erro.text.find('Acesso inválido') > -1:
                self.driver.find_element_by_id("username").send_keys(usuario)
                self.driver.find_element_by_id("password").send_keys(senha)
                inicio = time.time()
                f = False
                while not f:
                    time.sleep(1)
                    tempoTotal = time.time() - inicio
                    if tempoTotal >= 60:
                        return False
                    f = self.driver.find_element_by_id('formMenu')


        inicio = time.time()
        f = False
        while not f:
            time.sleep(1)
            tempoTotal = time.time() - inicio
            if tempoTotal >= 45:
                return False

            self.detecta_erro()

            newpassword = self.driver.find_element_by_id("newpassword")
            if newpassword:
                self.altera_senha(usuario, senha, base)

            f = self.driver.find_element_by_id('formMenu')
            # username = self.driver.find_element_by_id("username")
            # if username:
            #     usuario = username.get_attribute('value').strip()
            #     if usuario == '':
            #         self.logger.exception('Usuário/Senha inválidos')
            #         return False


        # check_reset = Plataforma.check_data_user(self.conn[base], 1, self.ordem_usuario+1)
        # print('check_reset',check_reset)
        # if len(check_reset) > 0:
        #     self.driver.find_element_by_xpath('//*[@id="formMenu"]/table/tbody/tr/td/div/table/tbody/tr/td[4]').click()
        #     aguarda_presenca_elemento(self.driver, '//*[@id="cmSubMenuID8"]/table/tbody/tr/td[2]', aguarda_visibilidade=True)
        #     self.driver.find_element_by_xpath('//*[@id="cmSubMenuID8"]/table/tbody/tr/td[2]').click()
        #     aguarda_presenca_elemento(self.driver, 'formAlterarSenha:senhaAtual', tipo='ID', aguarda_visibilidade=True)
        #     self.altera_senha_menu(usuario, senha, base)

        return True

    # ALTERA A SENHA DO PROCESSUM NA BASE
    def altera_senha(self, usuario=None, senha=None, base=None):
        new_password = create_password()
        print(new_password)
        if self.driver.find_element_by_id("username"):
            self.driver.find_element_by_id("username").send_keys(usuario)
            self.driver.find_element_by_id("oldpassword").send_keys(senha)
            self.driver.find_element_by_id("newpassword").send_keys(new_password)
            self.driver.find_element_by_id("newpasswordconfirm").send_keys(new_password)
            self.driver.find_element_by_id("newpasswordconfirm").send_keys(Keys.ENTER)

        time.sleep(2)

        if self.driver.find_element_by_id("login"):
            self.driver.find_element_by_id("login").send_keys(usuario)
            self.driver.find_element_by_id("oldpassword").send_keys(senha)
            self.driver.find_element_by_id("newpassword").send_keys(new_password)
            self.driver.find_element_by_id("newpasswordconfirm").send_keys(new_password)
            self.driver.find_element_by_id("newpasswordconfirm").send_keys(Keys.ENTER)

        campos = ['plt_senha','plt_senha2','plt_senha3']
        Plataforma.update_password(self.conn[base], 1, '*', campos[self.ordem_usuario], new_password)
        raise CriticalException("Senha alterada - "+usuario+" | "+new_password, self.uf, self.plataforma, self.prc_id, False)

        # ALTERA A SENHA DO PROCESSUM NA BASE

    def altera_senha_menu(self, usuario=None, senha=None, base=None):
        new_password = create_password()
        print('senha',senha)
        print('new_password', new_password)
        self.driver.find_element_by_id("formAlterarSenha:senhaAtual").send_keys(senha)
        self.driver.find_element_by_id("formAlterarSenha:senhaNova").send_keys(new_password)
        self.driver.find_element_by_id("formAlterarSenha:confirmacaoSenhaNova").send_keys(new_password)
        self.driver.find_element_by_id("formAlterarSenha:confirmacaoSenhaNova").send_keys(Keys.ENTER)

        campos = ['plt_senha', 'plt_senha2', 'plt_senha3']
        Plataforma.update_password(self.conn[base], 1, '*', campos[self.ordem_usuario], new_password)

    # CONFERE SE OCORREU ERRO NO PROCESSUM
    def detecta_erro(self, raise_critical=True):
        msg_erro = self.driver.find_element_by_xpath('/html/body/form/table/tbody/tr/td[2]/table/tbody/tr[1]/td/font')
        if msg_erro:
            if msg_erro.text.upper().find('ERRO DETECTADO') > -1:
                if raise_critical:
                    raise CriticalException("Erro Detectado", self.uf, self.plataforma, self.prc_id, False)
                else:
                    raise MildException("Erro Detectado", self.uf, self.plataforma, self.prc_id, False)

    # MÉTODO PARA A BUSCA DO PROCESSO NO CLIENTE
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        try:
            self.driver.find_element_by_id('fPesquisa:sequencial').clear()
        except:
            raise CriticalException("Campo de busca não localizado", self.uf, self.plataforma, self.prc_id, False)

        self.driver.find_element_by_id('fPesquisa:sequencial').send_keys(numero_busca)
        aguarda_alerta(self.driver, tempo=0.5)
        self.driver.find_element_by_id("fPesquisa:lblBtnFiltrar").click()

        if not self.driver.find_element_by_xpath('//*[@id="fPesquisa:dtbProcesso:0:actionDetalhar"]'):
            erros = self.driver.find_element_by_id("subviewMessages:formHeader:msgErro")
            if not erros:
                raise MildException("Erro ao buscar processo", self.uf, self.plataforma, self.prc_id, False)

            msg = erros.text.upper()
            if msg.find('NENHUM PROCESSO') > -1:
                return False

            if msg.find('NÃO FOI ENCONTRADO UM MÓDULO') > -1:
                raise MildException("Não foi encontrado um módulo", self.uf, self.plataforma, self.prc_id, False)

        self.detecta_erro()

        link = self.driver.find_element_by_id('fPesquisa:dtbProcesso:0:actionDetalhar')
        if link.text != numero_busca:
            raise MildException("Erro na busca do processo", self.uf, self.plataforma, self.prc_id, False)

        onclick = link.get_attribute('onclick')
        self.driver.execute_script(onclick)
        self.detecta_erro()

        return True

    # ABRE E FECHA ABAS DA ÁREA DE INFORMAÇÃO DO PROCESSO
    def abre_fecha_aba(self, nome):
        tts = self.driver.find_elements_by_xpath('//*[@id="fDetalhar:pnlGeral2"]/tbody/tr/td/div/div[1]')
        for ts in tts:
            if ts.text.upper().find(nome.upper()) > -1:
                ts.click()
                return True

        return False

    # ABRE O MODAL PARA INSERIR OCORRÊNCIA
    def abre_modal_ocorrencia(self):
        btn = self.driver.find_element_by_id('fAcompanhamento:dtbOcorrencia:popupManipulaOcorrencia')
        if not btn:
            raise MildException("Botão de Inserir Indisponível", self.uf, self.plataforma, self.prc_id, False)

        btn.click()
        self.abre_e_aguarda_modal()

    # ABRE O MODAL PARA INSERIR IMAGEM
    def abre_modal_imagem(self):
        btn = self.driver.find_element_by_xpath('//*[@id="fImagem"]/table[6]/tbody/tr/td[2]/a')
        if not btn:
            btn = self.driver.find_element_by_xpath('//*[@id="fImagem"]/table[7]/tbody/tr/td[2]/a')
        if not btn:
            raise MildException("Botão de Inserir Imagem Indisponível", self.uf, self.plataforma, self.prc_id, False)

        btn.click()
        self.abre_e_aguarda_modal()

    # ABRE O MODAL PARA LANÇAR CONTINGENCIA
    def abre_modal_contingencia(self):
        btn = self.driver.find_element_by_id('fDetalhar:popupEditarProvisionamento')
        if not btn:
            btn = self.driver.find_element_by_xpath('//*[@id="fDetalhar:pnlContig"]/thead/tr/th/span/a')

        if not btn:
            raise MildException("Link de contingência indisponível", self.uf, self.plataforma, self.prc_id, False)

        if not btn.is_displayed():
            self.abre_fecha_aba('CONTINGÊNCIA')

        btn.click()
        self.abre_e_aguarda_modal()

    def abre_e_aguarda_modal(self):
        aguarda_presenca_elemento(self.driver, '__jeniaPopupFrameTarget', tipo='ID', aguarda_visibilidade=True)
        self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))

        self.detecta_erro_modal()

    # VERIFICA SE OCORREU ALGUM ERRO NA HORA DE ABRIR O MODAL
    def detecta_erro_modal(self, xpath='/html/body/form/table/tbody/tr/td[2]/table/tbody/tr[1]/td/font'):
        err = self.driver.find_element_by_xpath(xpath)
        if err:
            if err.text.find('Erro detectado') > -1 or('Web server is down'):
                raise MildException("Erro ao abrir modal", self.uf, self.plataforma, self.prc_id)

            err = self.driver.find_element_by_xpath('/html/body/h1')
            if err:
                if err.text.find('Erro de Operação') > -1:
                    raise MildException("Erro ao abrir modal", self.uf, self.plataforma, self.prc_id)

            err = self.driver.find_element_by_xpath('//*[@id="cf-error-details"]/header/h1')
            if err:
                if err.text.find('Error 1020') > -1:
                    raise MildException("Erro ao abrir modal", self.uf, self.plataforma, self.prc_id)

        err = self.driver.find_element_by_xpath('//*[@id="cf-error-details"]/header/h2')
        if err:
            raise MildException("Erro ao abrir modal", self.uf, self.plataforma, self.prc_id)

    # SALVA A OCORRÊNCIA E FECHA O MODAL DE INSERIR OCORRÊNCIA
    def fecha_modal(self, salvar=False):
        if salvar:
            # CLICA EM ADICIONAR
            btn = self.driver.find_element_by_xpath('//*[@id="fCadastrar"]/table[5]/tbody/tr/td[1]/input[1]')
            if not btn:
                btn = self.driver.find_element_by_xpath('//*[@id="fCadastrar"]/table[8]/tbody/tr/td[1]/input')
            btn.click()
            try:
                trs = self.driver.find_elements_by_xpath('//*[@id="fCadastrar:dtbOcorrencia"]/tbody/tr/td[1]')
            except:
                raise MildException("Erro ao confirmar salvamento de ocorrencia", self.uf, self.plataforma, self.prc_id)
            # AGUARDA A INCLUSÃO DA LINHA ANTES DE GRAVAR
            inicio = time.time()
            while len(trs) == 0:
                # CONFERE SE DEU ERRO NA INSERÇÃO
                erro = self.driver.find_element_by_id('subviewMessages:formHeader:msgErro')
                if erro and erro.text.strip() != '':
                    return erro.text.strip()

                time.sleep(0.5)
                if time.time() - inicio > 30:
                    raise MildException("Erro ao carregar lista de esps", self.uf, self.plataforma, self.prc_id)
                trs = self.driver.find_elements_by_xpath('//*[@id="fCadastrar:dtbOcorrencia"]/tbody/tr/td[1]')

            # CLICA EM GRAVAR
            btn = self.driver.find_element_by_xpath('//*[@id="fCadastrar"]/table[8]/tbody/tr/td[1]/input')
            if not btn:
                btn = self.driver.find_element_by_xpath('//*[@id="fCadastrar"]/table[9]/tbody/tr/td[1]/input')
            btn.click()

            aguarda_alerta(self.driver, 5, False)

            inicio = time.time()
            linhas = []
            msgok = []
            while len(linhas) == 0 or len(msgok) == 0:
                tempo_total = time.time() - inicio
                if tempo_total > 40:
                    raise MildException("Erro ao salvar ocorrencia", self.uf, self.plataforma, self.prc_id)

                self.driver.switch_to.default_content()
                linhas = self.driver.find_elements_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr')
                msgok = self.driver.find_elements_by_id('subviewMessages:formHeader:msgOk')

                # CONFERE SE DEU ERRO NA INSERÇÃO
                try:
                    self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))
                    erro = self.driver.find_element_by_id('subviewMessages:formHeader:msgErro')
                    if erro:
                        return erro.text
                except:
                    pass


                try:
                    self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))
                    erro = self.driver.find_element_by_xpath('//*[@id="subviewMessages"]/tbody/tr/td/table/tbody/tr/td/span')
                    if erro:
                        classe_erro = erro.get_attribute('class')
                        if classe_erro and classe_erro.find('msgErro') > -1 and erro.text.strip() != '':
                            return erro.text
                except:
                    pass

                try:
                    # CONFERE SE O MODAL APRESENTOU ALGUM ERRO
                    self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))
                    self.detecta_erro_modal()
                except:
                    pass

            self.driver.switch_to.default_content()
            while True:
                msgok = self.driver.find_element_by_id('subviewMessages:formHeader:msgOk')
                if msgok.text.find('Ocorrência cadastrada') > -1:
                    break

        self.driver.switch_to.default_content()
        self.driver.execute_script("hidePopupFrame();")
        return False

    # ABRE A ABA DE ACOMPANHAMENTOS E AGUARDA A PRESENÇA DA TABELA
    def abre_aba_acompanhamento(self):
        if not self.driver.find_element_by_id('fAcompanhamento:dtbOcorrencia'):
            btn = localiza_elementos(self.driver, ('//*[@id="fDetalhar"]/table[6]/tbody/tr/td[2]/input', '//*[@id="fDetalhar"]/table[5]/tbody/tr/td[2]/input','//*[@id="fAcompanhamento"]/table[6]/tbody/tr/td[2]/input', '//*[@id="fAcompanhamento"]/table[5]/tbody/tr/td[2]/input','//*[@id="fImagem"]/table[5]/tbody/tr/td[2]/input','//*[@id="fImagem"]/table[6]/tbody/tr/td[2]/input'))
            if not btn:
                raise MildException("Aba não localizada", self.uf, self.plataforma, self.prc_id)

            btn.click()

            if not self.driver.find_element_by_id('fAcompanhamento:dtbOcorrencia'):
                raise MildException("Tabela não localizada", self.uf, self.plataforma, self.prc_id)

        self.wait_complete()

        footer = self.driver.find_element_by_id('fAcompanhamento:dtbOcorrencia:lstTamanhoOcorrencias')
        inicio = time.time()
        while not footer:
            footer = self.driver.find_element_by_id('fAcompanhamento:dtbOcorrencia:lstTamanhoOcorrencias')
            tempoTotal = time.time() - inicio
            if tempoTotal >= 30:
                raise MildException("Timeout carregando acompanhamentos", self.uf, self.plataforma, self.prc_id)

        total_orig = 0
        total = 0
        footer = self.driver.find_element_by_id('fAcompanhamento:dtbOcorrencia:lstTamanhoOcorrencias').text
        r = re.search("(\\d+)", footer, re.IGNORECASE | re.DOTALL)
        if r is not None:
            total = int(r.group(0))
            total_orig = total
            if total > 10:
                total = 10

        quoc = total // 10
        resto = total_orig % 10
        linhas = self.driver.find_elements_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr')
        inicio = time.time()
        while len(linhas) < total:
            cls = self.driver.find_element_by_class_name('tScrColActive').text
            linhas = self.driver.find_elements_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr')
            if int(cls) == (quoc+1) and resto == len(linhas):
                break

            tempoTotal = time.time() - inicio
            if tempoTotal >= 30:
                raise MildException("Timeout carregando acompanhamentos", self.uf, self.plataforma, self.prc_id)

    # ABRE A ABA DE IMAGENS E AGUARDA A PRESENÇA DA TABELA
    def abre_aba_imagem(self):
        if not self.driver.find_element_by_id('fImagem:dtbImagem'):
            btn = localiza_elementos(self.driver, ('//*[@id="fDetalhar"]/table[6]/tbody/tr/td[3]/input', '//*[@id="fDetalhar"]/table[5]/tbody/tr/td[3]/input','//*[@id="fAcompanhamento"]/table[6]/tbody/tr/td[3]/input', '//*[@id="fAcompanhamento"]/table[5]/tbody/tr/td[3]/input',))
            if not btn:
                raise MildException("Aba não localizada", self.uf, self.plataforma, self.prc_id)

            btn.click()

            if not self.driver.find_element_by_id('fImagem:dtbImagem'):
                raise MildException("Tabela não localizada", self.uf, self.plataforma, self.prc_id)

    # ABRE A ABA DE DADOS PRINCIPAIS E AGUARDA A PRESENÇA DA TABELA
    def abre_aba_principal(self):
        if not self.driver.find_element_by_id('fDetalhar:pnlGeral2'):
            btn = localiza_elementos(self.driver, ('//*[@id="fAcompanhamento:panelBotoes"]/tbody/tr/td[1]/input','//*[@id="fAcompanhamento"]/table[5]/tbody/tr/td[2]/input','//*[@id="fAcompanhamento"]/table[6]/tbody/tr/td[2]/input','//*[@id="fImagem"]/table[5]/tbody/tr/td[1]/input','//*[@id="fImagem"]/table[6]/tbody/tr/td[1]/input',))
            if not btn:
                raise MildException("Aba não localizada", self.uf, self.plataforma, self.prc_id)

            btn.click()

            if not self.driver.find_element_by_id('fDetalhar:pnlGeral2'):
                raise MildException("Tabela não localizada", self.uf, self.plataforma, self.prc_id)

    # SELECIONA O TIPO DE ACOMPANHAMENTO PELO TEXTO PASSADO E AGUARDA O CARREGAMENTO DOS TIPOS
    def select_tipo(self, texto, aguarda_esp=True, possui_alternativa=False, sem_esp=False):
        select = Select(self.driver.find_element_by_id('fCadastrar:tipoOcorrencia'))
        try:
            select.select_by_visible_text(texto)
        except:
            if possui_alternativa:
                return False
            print("Tipo não localizado: "+texto)
            return None
            # raise MildException("Tipo não localizado: "+texto, self.uf, self.plataforma, self.prc_id)

        if aguarda_esp:
            tipos = self.driver.find_elements_by_xpath('//*[@id="fCadastrar:espTipoOcorrencia"]/option')
            inicio = time.time()
            if not sem_esp:
                while len(tipos) == 1:
                    tipos = self.driver.find_elements_by_xpath('//*[@id="fCadastrar:espTipoOcorrencia"]/option')
                    time.sleep(0.5)
                    if time.time() - inicio > 30:
                        if possui_alternativa:
                            return False
                        raise MildException("Erro ao carregar lista de esps", self.uf, self.plataforma, self.prc_id)
        else:
            time.sleep(1)

        return True

    # SELECIONA A ESPECIFICAÇÃO DO ACOMPANHAMENTO PELO TEXTO PASSADO E AGUARDA O CARREGAMENTO, CASO SEJA ESPECIFICADO
    def select_esp(self, texto, aguardar=False, tipo_aguardar='XPATH', possui_alternativa=False):
        select = Select(self.driver.find_element_by_id('fCadastrar:espTipoOcorrencia'))
        try:
            select.select_by_visible_text(texto)
        except:
            if possui_alternativa:
                return False
            raise MildException("Esp não localizada "+texto, self.uf, self.plataforma, self.prc_id)

        if aguardar:
            if not aguarda_presenca_elemento(self.driver, aguardar, tipo=tipo_aguardar):
                raise MildException("Erro ao carregar campos modal", self.uf, self.plataforma, self.prc_id)

        return True

    # SELECIONA VALOR EM UM SELECT PELO TEXTO
    def seleciona_option(self, texto, elemento, tipo='XPATH', select_by='text', erro='Opção não localizada', ignora_erro=False):
        by = getattr(By, tipo)
        select = Select(self.driver.find_element(by, elemento))
        if erro == 'Opção não localizada':
            erro = erro + ': ' + str(texto)
        try:
            if select_by == 'text':
                select.select_by_visible_text(texto)
            if select_by == 'value':
                select.select_by_value(texto)
            if select_by == 'index':
                select.select_by_index(texto)
        except:
            if not ignora_erro:
                raise FatalException(erro, self.uf, self.plataforma, self.prc_id)

    # PREENCHE O CAMPO DESEJADO
    def preenche_campo(self, texto, elemento, tipo='XPATH', limpar_string=False, wait=0):
        by = getattr(By, tipo)
        texto_original = texto
        # CONFERE SE É UMA DATA
        if len(texto) < 12:
            m = re.search(r'(\d+)(/)(\d+)(/)(\d+)', texto, re.I)
            if m is not None:
                texto = texto.replace('/','')

        # if limpar_string:
        #     texto_original = self.clear_special_chars(texto)
        texto_original = self.clear_special_chars(texto)

        texto_cli = ''
        inicio = time.time()
        while texto_original != texto_cli:
            if time.time() - inicio > 15:
                raise MildException("Erro ao imputar texto no campo "+elemento+" | "+texto_original+" | "+texto_cli, self.uf, self.plataforma, self.prc_id)

            # campo = self.driver.find_element(by, elemento)
            try:
                self.driver.find_element(by, elemento).clear()
                self.driver.find_element(by, elemento).click()
                self.driver.find_element(by, elemento).send_keys(Keys.HOME)
                campo = self.driver.find_element(by, elemento)
                for t in texto:
                    tentativas = 0
                    while True:
                        try:
                            campo.send_keys(t)
                            break
                        except:
                            tentativas += 1
                            if tentativas > 3:
                                raise

                            tb = traceback.format_exc(limit=1)
                            # print(tb)
                            if tb.find('stale element') > -1:
                                time.sleep(0.5)
                            else:
                                raise

                campo.send_keys(Keys.TAB)
                if wait > 0:
                    time.sleep(wait)
                campo = self.driver.find_element(by, elemento)
                texto_cli = campo.get_attribute('value')
                texto_cli = self.clear_special_chars(texto_cli)
                ini_texto = time.time()

                # AGUARDA O PREENCHIMENTO DO CAMPO
                while len(texto_cli) != len(texto_original):
                    time.sleep(0.5)
                    if time.time() - ini_texto > 3:
                        break
                    try:
                        texto_cli = campo.get_attribute('value')
                        texto_cli = self.clear_special_chars(texto_cli)
                        # print('texto_cli', texto_original, texto_cli)
                        # if limpar_string:
                        #     texto_cli = self.clear_special_chars(texto)
                    except:
                        tb = traceback.format_exc(limit=1)
                        if tb.find('stale element') > -1:
                            time.sleep(1)
                        else:
                            raise
            except:
                tb = traceback.format_exc(limit=1)
                if tb.find('stale element') > -1:
                    time.sleep(1)

                if tb.find('stale element') == -1 and tb.find('invalid element state') == -1:
                    print(tb)
                pass

        time.sleep(0.5)

    # PREENCHE O CAMPO DESEJADO
    def clica_radio(self, elemento, tipo='XPATH', aguardar=False, tipo_aguardar='XPATH'):
        by = getattr(By, tipo)
        self.driver.find_element(by, elemento).click()

        if aguardar:
            if not aguarda_presenca_elemento(self.driver, aguardar, tipo=tipo_aguardar):
                raise MildException("Erro ao clicar no radio " + elemento, self.uf, self.plataforma, self.prc_id)


    # CONFERE SE OS DADOS LANÇADOS NOS CAMPOS CONFEREM COM A BASE
    def confere_dados(self, dados_lanc):
        print('conferindo dados')
        erro = False
        # NO PRIMEIRO CICLO CONFERE E TENTA CORRIGIR
        inputs = dados_lanc['input']

        for d in inputs:
            by = getattr(By, inputs[d]['by'])
            campo = self.driver.find_element(by, inputs[d]['campo'])
            texto = campo.get_attribute('value')
            dado = inputs[d]['dado']
            limpar_string = True if 'limpar_string' in inputs[d] and inputs[d]['limpar_string'] else False
            # if limpar_string:
            texto = self.clear_special_chars(texto)
            dado = self.clear_special_chars(dado)

            if texto != dado:
                erro = True

                if 'readonly' not in inputs[d] or not inputs[d]['readonly']:
                    print('preenchendo novamente', inputs[d]['campo'])
                    self.preenche_campo(inputs[d]['dado'], inputs[d]['campo'], inputs[d]['by'])
                else:
                    raise MildException("Erro na integridade de dados em campo readonly. Campo: "+inputs[d]['campo']+texto+"|"+dado, self.uf, self.plataforma, self.prc_id)


        # NO SEGUNDO CICLO, CASO TENHA DETECTADO ERRO NO PRIMEIRO, CONFERE E RETORNA EXCEÇÃO SE CONTINUAR ERRADO
        if erro:
            time.sleep(3)
            for d in inputs:
                by = getattr(By, inputs[d]['by'])
                campo = self.driver.find_element(by, inputs[d]['campo'])
                texto = campo.get_attribute('value')
                texto = self.clear_special_chars(texto)
                dado = self.clear_special_chars(inputs[d]['dado'])
                if texto != dado:
                    raise MildException("Erro na integridade dos dados. Campo: "+inputs[d]['campo']+texto+"|"+dado, self.uf, self.plataforma, self.prc_id)

        if 'arquivos_ocorrencia' in dados_lanc:
            trs_arq = len(self.driver.find_elements_by_xpath('//*[@id="fCadastrar:dtbAnexo:tbody_element"]/tr'))
            if len(dados_lanc['arquivos_ocorrencia']) != trs_arq:
                raise MildException("Erro na quantidade de arquivos", self.uf, self.plataforma, self.prc_id)

    # GERENCIA O LANÇAMENTO DE OCORRENCIAS NO PROCESSUM
    def lanca_ocorrencia(self, acp, url_arquivos='', gera_exception=False, lanca_arquivos=True):
        print('Lançando Ocorrência')
        self.abre_modal_ocorrencia()
        alternativo = False

        com_esp = acp['principais']['esp']['dado'] != '-' and acp['principais']['esp']['dado'] != ''
        sem_esp = acp['principais']['esp']['dado'] == '-' or acp['principais']['esp']['dado'] == '' or acp['principais']['esp']['dado'] is None
        rt = self.select_tipo(acp['principais']['tipo']['dado'], com_esp, 'alternativo' in acp and 'tipo' in acp['alternativo'], sem_esp=sem_esp)
        if rt is None:
            self.fecha_modal(False)
            return False

        if 'alternativo' in acp and rt is not None and not rt:
            alternativo = True
            sem_esp = 'esp' not in acp['alternativo']
            rt = self.select_tipo(acp['alternativo']['tipo'], com_esp, sem_esp=sem_esp)
            if rt is None:
                self.fecha_modal(False)
                return False

        aguardar = acp['principais']['esp']['aguardar'] if 'aguardar' in acp['principais']['esp'] else 'fCadastrar:dataEvento'
        aguarda_tipo = acp['principais']['esp']['aguardar_tipo'] if 'aguardar_tipo' in acp['principais']['esp'] else 'ID'

        if com_esp or alternativo:
            if alternativo:
                if 'esp' in acp['alternativo']:
                    self.select_esp(acp['alternativo']['esp'], aguardar, aguarda_tipo)
            else:
                if not self.select_esp(acp['principais']['esp']['dado'], aguardar, aguarda_tipo, True):
                    print('não achei esp')
                    if 'alternativo' in acp and 'tipo' in acp['alternativo']:
                        print('imputando tipo alternativo')
                        rt = self.select_tipo(acp['alternativo']['tipo'], 'esp' in acp['alternativo'])
                        if rt is None:
                            self.fecha_modal(False)
                            return False
                        if 'esp' in acp['alternativo']:
                            print('imputando esp alternativo')
                            self.select_esp(acp['alternativo']['esp'], aguardar, aguarda_tipo)
                    else:
                        if 'alternativo' in acp and 'esp' in acp['alternativo']:
                            self.select_esp(acp['alternativo']['esp'], aguardar, aguarda_tipo)
                        else:
                            self.select_esp(acp['principais']['esp']['dado'], aguardar, aguarda_tipo)

        # self.select_tipo(acp['principais']['tipo']['dado'], com_esp)
        # if com_esp:
        #     self.select_esp(acp['principais']['esp']['dado'], 'fCadastrar:dataEvento', 'ID')

        radios = acp['radio'] if 'radio' in acp else []
        for d in radios:
            aguardar =  radios[d]['aguardar'] if 'aguardar' in radios[d] else False
            tipo_aguardar = radios[d]['aguardar_tipo'] if 'aguardar_tipo' in radios[d] else 'XPATH'
            self.clica_radio(radios[d]['campo'], radios[d]['by'], aguardar, tipo_aguardar)
            # self.driver.find_element(radios[d]['by'], radios[d]['campo']).click()

        inputs = acp['input']
        for d in inputs:
            if 'readonly' in inputs[d] and inputs[d]['readonly']:
                continue
            limpar_string = inputs[d]['limpar_string'] if 'limpar_string' in inputs[d] else False
            wait_after = inputs[d]['wait'] if 'wait' in inputs[d] else 0
            self.preenche_campo(inputs[d]['dado'], inputs[d]['campo'], inputs[d]['by'], limpar_string=limpar_string, wait=wait_after)

        selects = acp['select'] if 'select' in acp else []
        for d in selects:
            select_by = selects[d]['select_by'] if 'select_by' in selects[d] else 'text'
            erro = selects[d]['erro'] if 'erro' in selects[d] else 'Opção não localizada'
            ignora_erro = selects[d]['ignora_erro'] if 'ignora_erro' in selects[d] else False
            self.seleciona_option(selects[d]['dado'], selects[d]['campo'], selects[d]['by'], select_by=select_by, erro=erro, ignora_erro=ignora_erro)

        if lanca_arquivos and 'arquivos_ocorrencia' in acp and len(acp['arquivos_ocorrencia']) > 0:
            prev_trs_arq = 0
            trs_arq = 0
            for arq in acp['arquivos_ocorrencia']:
                file_upload = self.driver.find_element_by_id('fCadastrar:anexo')
                try:
                    file_upload.send_keys(url_arquivos + arq['arq_url'])
                    self.driver.find_element_by_xpath('//*[@id="fCadastrar:pnlAnexo"]/tbody/tr/td[2]/a').click()
                except:
                    raise FatalException("Confererir integridade de arquivo: "+arq['arq_nome'], self.uf, self.plataforma, self.prc_id)

                inicio = time.time()
                while prev_trs_arq == trs_arq:
                    tempoTotal = time.time() - inicio
                    if tempoTotal >= 60:
                        raise MildException("Timeout ao carregar arquivos", self.uf, self.plataforma, self.prc_id)
                    trs_arq = len(self.driver.find_elements_by_xpath('//*[@id="fCadastrar:dtbAnexo:tbody_element"]/tr'))

                prev_trs_arq = trs_arq

        self.confere_dados(acp)
        erro_lancamento = self.fecha_modal(True)
        if erro_lancamento:
            print(erro_lancamento)
            if gera_exception:
                raise FatalException(erro_lancamento, self.uf, self.plataforma, self.prc_id)

        return True

    # TRATA O CAMPORTAMENTO EM CASO DE ERRO NO MODAL DE ARQUIVOS
    def exception_modal_arquivo(self, raise_exception, mensagem):
        if raise_exception:
            raise FatalException(mensagem, self.uf, self.plataforma, self.prc_id)
        else:
            self.fecha_modal()
            return False

    # GERENCIA O LANÇAMENTO DE OCORRENCIAS NO PROCESSUM
    def lanca_arquivo(self, acp, url, raise_exception=True, renomeia_arquivo=False, zipa_bloqueado=False):
        print('lançando arquivo', url)

        total_arquivos_lancados = 0
        footer = self.driver.find_element_by_xpath('//*[@id="fImagem:dtbImagem"]/tfoot/tr/td').text
        r = re.search("(\\d+)", footer, re.IGNORECASE | re.DOTALL)
        if r is not None:
            total_arquivos_lancados = int(r.group(0))

        empresa = self.driver.find_element_by_id('fImagem:empresa').text
        self.abre_modal_imagem()
        self.driver.find_element_by_xpath('//*[@id="tipoUpload"]/tbody/tr/td[2]/label/input').click()
        aguarda_presenca_elemento(self.driver, 'formProtocolo:anexo', tipo='ID', aguarda_visibilidade=True)
        select = Select(self.driver.find_element_by_id('codEmpresa'))
        select.select_by_visible_text(empresa)

        # TENTA PREENCHER O TIPO DE DOCUMENTO
        try:
            select = Select(self.driver.find_element_by_id('codigoEspecTpDoc'))
            select.select_by_visible_text(acp['arquivo'][0])
        except:
            return self.exception_modal_arquivo(raise_exception, "Tipo não localizado: "+acp['arquivo'][0])

        self.preenche_campo(acp['data_arquivo'], 'dataRecebEmpresa', 'ID')
        self.preenche_campo(acp['data_arquivo'], 'dataRecebAJU', 'ID')
        self.preenche_campo(acp['obs_arquivo'], 'observacao', 'ID')

        prev_trs_arq = 0
        trs_arq = 0
        if 'pra' in acp and len(acp['pra']) > 0:
            temp_folder = self.pasta_download
            if renomeia_arquivo :
                temp_folder = self.pasta_download + '\\rename\\' + str(acp['pra'][0]['pra_prc_id']) + '\\'
                create_folder(temp_folder, None, False)

            for pra in acp['pra']:
                file_upload = self.driver.find_element_by_id('formProtocolo:anexo')
                dest = url + pra['pra_arquivo']
                zip = False
                if zipa_bloqueado:
                    if pra['pra_id'] in self.pra_bloqueado:
                        ponto = pra['pra_arquivo'].rfind('.')
                        novo_nome = pra['pra_arquivo'][:ponto] if ponto > -1 else pra['pra_arquivo']
                        novo_nome = temp_folder+novo_nome+'.rar'
                        os.system('rar a -ep "'+novo_nome+'" "'+url + pra['pra_arquivo']+'"')
                        pra['pra_arquivo'] = novo_nome
                        zip = True

                if renomeia_arquivo:
                    pra_data = pra['pra_data'].strftime('%Y-%m-%d')
                    pra_descricao = corta_string(pra['pra_descricao'], 30, corta_se_branco=True)
                    pra_descricao = ''.join(e for e in pra_descricao if e.isalnum() or e in ('-', ',', ' '))
                    dest = temp_folder + pra_data + ' - ' + pra['pra_id_tj'] + ' - ' + pra_descricao + ' - ' + pra['pra_arquivo'][-12:].lower()
                    try:
                        if zip:
                            ponto = dest.rfind('.')
                            dest = dest[:ponto]+'.zip'
                            shutil.copyfile(pra['pra_arquivo'], dest)
                        else:
                            shutil.copyfile(url + pra['pra_arquivo'], dest)
                    except:
                        return self.exception_modal_arquivo(raise_exception,"Arquivo não localizado " + url + pra['pra_arquivo'])

                try:
                    file_upload.send_keys(dest)
                    self.driver.find_element_by_xpath('//*[@id="formProtocolo"]/table[5]/tbody/tr[2]/td/table/tbody/tr/td[2]/a').click()
                except:
                    return self.exception_modal_arquivo(raise_exception,"Arquivo não localizado " + url + pra['pra_arquivo'])

                block_error = self.driver.find_element_by_xpath('//*[@id="cf-error-details"]/div[1]/h1')
                if block_error:
                    if block_error.text.find('Sorry, you have been blocked') > -1:
                        self.pra_bloqueado.append(pra['pra_id'])
                        raise MildException("Arquivo Bloqueado "+str(pra['pra_id']), self.uf, self.plataforma, self.prc_id)

                inicio = time.time()
                while prev_trs_arq == trs_arq:
                    tempoTotal = time.time() - inicio
                    if tempoTotal >= 60:
                        raise MildException("Timeout ao carregar arquivos", self.uf, self.plataforma, self.prc_id)
                    trs_arq = len(self.driver.find_elements_by_xpath('//*[@id="formProtocolo:dtbAnexos:tbody_element"]/tr'))

                prev_trs_arq = trs_arq

            if renomeia_arquivo:
                shutil.rmtree(temp_folder)

        if 'arq' in acp:
            for arq in acp['arq']:
                file_upload = self.driver.find_element_by_id('formProtocolo:anexo')
                file_path = trata_path(url + arq['arq_url'])
                try:
                    file_upload.send_keys(file_path)
                    self.driver.find_element_by_xpath('//*[@id="formProtocolo"]/table[5]/tbody/tr[2]/td/table/tbody/tr/td[2]/a').click()
                except:
                    return self.exception_modal_arquivo(raise_exception, "Problema ao lançar arquivo "+arq['arq_descricao'])

                inicio = time.time()
                while prev_trs_arq == trs_arq:
                    tempoTotal = time.time() - inicio
                    if tempoTotal >= 60:
                        raise MildException("Timeout ao carregar arquivos", self.uf, self.plataforma, self.prc_id)
                    trs_arq = len(self.driver.find_elements_by_xpath('//*[@id="formProtocolo:dtbAnexos:tbody_element"]/tr'))

                prev_trs_arq = trs_arq

        if 'drp' in acp and len(acp['drp']) > 0:
            temp_folder = self.pasta_download + '\\rename\\' + str(acp['drp'][0]['drp_prc_id']) + '\\'
            create_folder(temp_folder, None, False)
            for drp in acp['drp']:
                conteudo = cria_html_diario(drp)
                conteudo = conteudo.replace('@',' @ ')
                dro_dia = drp['dro_dia'].strftime('%Y-%m-%d')
                uid1 = str(uuid.uuid1())[:8]
                subtitulo = drp['drp_subtitulo'] if drp['drp_subtitulo'] is not None and drp['drp_subtitulo'].strip() != '' else 'Publicação'
                subtitulo = subtitulo.replace('/','').replace('\\','').replace('__','')
                subtitulo = remove_acentos(subtitulo)
                subtitulo = corta_string(subtitulo, 45)
                pdf_url = temp_folder+'DJ-'+dro_dia+'-'+subtitulo+'-'+uid1+'.pdf'
                html_to_pdf(conteudo, pdf_url)

                if drp['drp_id'] in self.drp_bloqueado:
                    pdf_to_img(pdf_url, temp_folder)

                file_upload = self.driver.find_element_by_id('formProtocolo:anexo')
                file_path = trata_path(pdf_url)
                try:
                    file_upload.send_keys(file_path)
                    self.driver.find_element_by_xpath('//*[@id="formProtocolo"]/table[5]/tbody/tr[2]/td/table/tbody/tr/td[2]/a').click()
                except:
                    return self.exception_modal_arquivo(raise_exception, "Problema ao lançar arquivo "+pdf_url)

                block_error = self.driver.find_element_by_xpath('//*[@id="cf-error-details"]/div[1]/h1')
                if block_error:
                    if block_error.text.find('Sorry, you have been blocked') > -1:
                        self.drp_bloqueado.append(drp['drp_id'])
                        raise MildException("Arquivo Bloqueado "+str(drp['drp_id']), self.uf, self.plataforma, self.prc_id)

                inicio = time.time()
                while prev_trs_arq == trs_arq:
                    tempoTotal = time.time() - inicio
                    if tempoTotal >= 60:
                        raise MildException("Timeout ao carregar arquivos", self.uf, self.plataforma, self.prc_id)
                    trs_arq = len(self.driver.find_elements_by_xpath('//*[@id="formProtocolo:dtbAnexos:tbody_element"]/tr'))

                prev_trs_arq = trs_arq

        len_arqs = 0
        if 'arq' in acp and len(acp['arq']) > 0:
            len_arqs = len(acp['arq'])
        elif 'pra' in acp and len(acp['pra']) > 0:
            len_arqs = len(acp['pra'])

        if len_arqs > 0:
            trs_arq =  len(self.driver.find_elements_by_xpath('//*[@id="formProtocolo:dtbAnexos:tbody_element"]/tr'))
            if len_arqs != trs_arq:
                raise MildException("Erro ao lançar arquivos", self.uf, self.plataforma, self.prc_id, False)

        block_error = self.driver.find_element_by_xpath('//*[@id="cf-error-details"]/div[1]/h1')
        if block_error:
            if block_error.text.find('Sorry, you have been blocked') > -1:
                return self.exception_modal_arquivo(raise_exception, "Arquivo Bloqueado ")

        self.driver.find_element_by_xpath('//*[@id="actions"]/tbody/tr/td[1]/input').click()
        self.fecha_modal()

        inicio = time.time()
        novo_total_arquivos_lancados = total_arquivos_lancados
        while total_arquivos_lancados == novo_total_arquivos_lancados:
            if time.time() - inicio > 20:
                raise MildException("Timeout ao salvar arquivo", self.uf, self.plataforma, self.prc_id, False)

            footer = self.driver.find_element_by_xpath('//*[@id="fImagem:dtbImagem"]/tfoot/tr/td').text
            r = re.search("(\\d+)", footer, re.IGNORECASE | re.DOTALL)
            if r is not None:
                novo_total_arquivos_lancados = int(r.group(0))

        return True

    # GERENCIA O LANÇAMENTO DE OCORRENCIAS NO PROCESSUM
    def lanca_arquivo_comentario(self, acp, url, i_tr):
        self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr['+i_tr+']/td[16]/a/img').click()

        aguarda_presenca_elemento(self.driver, '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr['+i_tr+']/td[16]/div/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[5]/td/a/span', aguarda_visibilidade=True)
        self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr['+i_tr+']/td[16]/div/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[5]/td/a/span').click()

        aguarda_presenca_elemento(self.driver, '__jeniaPopupFrameTarget', tipo='ID', aguarda_visibilidade=True)
        self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))

        self.preenche_campo(acp['obs_arquivo'], 'fComentar:descricao', 'ID')

        if 'pra' in acp:
            for pra in acp['pra']:
                file_upload = self.driver.find_element_by_id('fComentar:anexo')
                file_upload.send_keys(url+pra['pra_arquivo'])
                self.driver.find_element_by_xpath('//*[@id="fComentar:pnlAnexo"]/tbody/tr/td[2]/a').click()

        if 'arq' in acp:
            for arq in acp['arq']:
                file_upload = self.driver.find_element_by_id('fComentar:anexo')
                file_upload.send_keys(url+arq['pra_arquivo'])
                self.driver.find_element_by_xpath('//*[@id="fComentar:pnlAnexo"]/tbody/tr/td[2]/a').click()

        self.driver.find_element_by_xpath('//*[@id="fComentar:botoesGravar"]/tbody/tr/td[1]/input').click()
        self.fecha_modal()

        return True

    # CONFERE SE A OCORRENCIA FOI LANÇADA
    def confere_lancamento(self, dados_lanc, range_data_cadastro=2, range_data_evento=0, confere_conteudo=False, quantidade=1, ignora_cancelado=False):
        self.abre_aba_acompanhamento()
        self.driver.execute_script("oamSubmitForm('fAcompanhamento','fAcompanhamento:scrollResultadosidx1',null,[['fAcompanhamento:scrollResultados','idx1']]);")
        # for i in range(0, paginas):
        today = datetime.today().date()
        pdata = today + relativedelta(days=-range_data_cadastro)
        data_evento_base = datetime.strptime(dados_lanc['input']['data_evento']['dado'], '%d/%m/%Y')
        data_evento_prev = data_evento_base
        data_evento_post = data_evento_base
        if range_data_evento > 0:
            data_evento_prev = datetime.strptime(dados_lanc['input']['data_evento']['dado'], '%d/%m/%Y') + relativedelta(days=-range_data_evento)
            data_evento_post = datetime.strptime(dados_lanc['input']['data_evento']['dado'], '%d/%m/%Y') + relativedelta(days=range_data_evento)

        data_evento_base = datetime.strptime(dados_lanc['input']['data_evento']['dado'], '%d/%m/%Y')
        tipo_base = dados_lanc['principais']['tipo']['dado'].strip().upper()
        tipo_alternativo = dados_lanc['alternativo']['tipo'].strip().upper() if 'alternativo' in dados_lanc and 'tipo' in dados_lanc['alternativo'] else ''

        esp_base = dados_lanc['principais']['esp']['dado'].strip().upper() if dados_lanc['principais']['esp']['dado'] != '-' and dados_lanc['principais']['esp']['dado'] != '' else ''
        esp_alternativo = dados_lanc['alternativo']['esp'].strip().upper() if 'alternativo' in dados_lanc and  'esp' in dados_lanc['alternativo'] else ''

        checks = 0
        i = 1
        while True:
            i += 1
            linhas = self.driver.find_elements_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr')
            for indice, tr in enumerate(linhas):
                i_tr = str(indice + 1)

                acp_tipo = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[9]/span').text.strip()
                acp_esp = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[10]/span').text.strip()
                if ignora_cancelado:
                    cancelado = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[5]').text.strip()
                    if cancelado.find('Cancelado') > -1:
                        continue

                acp_cadastro = get_text(self.driver, '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[13]/span')
                # acp_cadastro_sem_hora = datetime.strptime(acp_cadastro, '%d/%m/%Y %H:%M').date() if acp_cadastro else None
                acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y %H:%M').date() if acp_cadastro else None


                acp_data_evento = get_text(self.driver, '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[6]/a/span[1]')
                acp_data_evento = datetime.strptime(acp_data_evento, '%d/%m/%Y') if acp_data_evento else None

                if acp_tipo == 'Sentença' and acp_esp.upper() == 'SEM JULGAMENTO DO MÉRITO':
                    acp_esp = 'Extinção sem Julgamento do Mérito'

                # print(dados_lanc['principais']['tipo']['dado'],acp_tipo)
                # print(tipo_alternativo, esp_alternativo)
                # print(dados_lanc['principais']['esp']['dado'],acp_esp)
                # print(acp_cadastro, today, acp_cadastro, pdata)
                # print(data_evento_base,acp_data_evento)
                # print(data_evento_post, data_evento_prev)
                # print(today, pdata)
                # print('-----------------')

                achei_esp = False
                if tipo_alternativo == '' and esp_alternativo != '':
                    if tipo_base == acp_tipo.upper() and esp_alternativo == acp_esp.upper():
                        achei_esp = True

                if tipo_alternativo != '':
                    if tipo_alternativo == acp_tipo.upper() and esp_alternativo == acp_esp.upper():
                        achei_esp = True

                if tipo_base == acp_tipo.upper() and esp_base == acp_esp.upper():
                    achei_esp = True

                if achei_esp and acp_data_evento is not None:
                    if data_evento_prev != data_evento_base:
                        if acp_data_evento <= data_evento_post and acp_data_evento >= data_evento_prev:
                            checks += 1
                            if confere_conteudo:
                                cc = self.confere_conteudo(dados_lanc, i_tr)
                                if cc:
                                    return True

                                if not cc and quantidade == checks:
                                    raise FatalException('Diferença nos dados lançados', self.uf, self.plataforma,  self.prc_id)

                            if not confere_conteudo:
                                return True

                    if data_evento_base == acp_data_evento:
                        if acp_cadastro <= today and acp_cadastro >= pdata:
                            checks += 1
                            if confere_conteudo:
                                cc = self.confere_conteudo(dados_lanc, i_tr)
                                if cc:
                                    return True

                                if not cc and quantidade == checks:
                                    raise FatalException('Diferença nos dados lançados', self.uf, self.plataforma, self.prc_id)

                            if not confere_conteudo:
                                return True

            # DETECTA SE EXISTE BOTÃO PARA IR PARA A PRÓXIMA PÁGINA E CLICA NELE
            ultimo_evento = get_text(self.driver, '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr['+str(len(linhas))+']/td[6]/a/span[1]')
            if ultimo_evento:
                ultima_data_evento = datetime.strptime(ultimo_evento, '%d/%m/%Y')
                if data_evento_base > ultima_data_evento:
                    break

            proximo = self.driver.find_element_by_id('fAcompanhamento:scrollResultadosidx'+str(i))
            if not proximo:
                break

            proximo.click()

        return False

    # CONFERE SE O CONTEÚDO DA OCORRÊNCIA ESTÁ CORRETO
    def confere_conteudo(self, dados_lanc, linha):
        self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + linha + ']/td[6]/a').click()
        aguarda_presenca_elemento(self.driver, '__jeniaPopupFrameTarget', tipo='ID', aguarda_visibilidade=True)
        self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))
        inputs = {}
        inputs.update(dados_lanc['input'])
        inputs.update(dados_lanc['select'])

        for d in inputs:
            if 'check' not in inputs[d]:
                continue
            texto = self.driver.find_element_by_id(inputs[d]['check']).text
            dado = inputs[d]['dado']
            limpar_string = True if 'limpar_string' in inputs[d] and inputs[d]['limpar_string'] else False
            if limpar_string:
                texto = self.clear_special_chars(texto)
                dado = self.clear_special_chars(dado)

            # by = getattr(By, inputs[d]['by'])

            if texto != dado:
                print('Diferença nos Dados!',texto, inputs[d]['dado'])
                # raise FatalException('Diferença nos dados lançados', self.uf, self.plataforma, self.prc_id)
                self.fecha_modal()
                return False

        if 'arquivos_ocorrencia' in dados_lanc:
            trs_arq = len(self.driver.find_elements_by_xpath('//*[@id="fOcorrencia:dtbAnexos:tbody_element"]/tr'))
            if len(dados_lanc['arquivos_ocorrencia']) != trs_arq:
                print("Erro na quantidade de arquivos")
                self.fecha_modal()
                return False
                # raise FatalException("Erro na quantidade de arquivos", self.uf, self.plataforma, self.prc_id)

        self.fecha_modal()
        return True

    # CONFERE SE A OCORRENCIA POSSUI COMENTÁRIO
    def confere_arquivo_comentario(self, dados_lanc, range_data_cadastro=2, range_data_evento=0):
        self.abre_aba_acompanhamento()
        # for i in range(0, paginas):
        today = datetime.today()
        pdata = today + relativedelta(days=-range_data_cadastro)
        data_evento_base = datetime.strptime(dados_lanc['input']['data_evento']['dado'], '%d/%m/%Y')
        data_evento_prev = data_evento_base
        data_evento_post = data_evento_base
        if range_data_evento > 0:
            data_evento_prev = datetime.strptime(dados_lanc['input']['data_evento']['dado'],
                                                 '%d/%m/%Y') + relativedelta(days=-range_data_evento)
            data_evento_post = datetime.strptime(dados_lanc['input']['data_evento']['dado'],
                                                 '%d/%m/%Y') + relativedelta(days=range_data_evento)

        data_evento_base = datetime.strptime(dados_lanc['input']['data_evento']['dado'], '%d/%m/%Y')
        tipo_base = dados_lanc['principais']['tipo']['dado'].upper()
        tipo_alternativo = dados_lanc['alternativo']['tipo'].upper() if 'tipo' in dados_lanc['alternativo'] else ''

        esp_base = dados_lanc['principais']['esp']['dado'].upper() if dados_lanc['principais']['esp']['dado'] != '-' and dados_lanc['principais']['esp']['dado'] != '' else ''
        esp_alternativo = dados_lanc['alternativo']['esp'].upper() if 'esp' in dados_lanc['alternativo'] else ''

        i = 1
        while True:
            i += 1
            linhas = self.driver.find_elements_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr')
            for indice, tr in enumerate(linhas):
                i_tr = str(indice + 1)

                acp_tipo = self.driver.find_element_by_xpath(
                    '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[9]/span').text
                acp_esp = self.driver.find_element_by_xpath(
                    '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[10]/span').text

                acp_cadastro = get_text(self.driver,
                                        '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[13]/span')
                acp_cadastro = datetime.strptime(acp_cadastro, '%d/%m/%Y %H:%M') if acp_cadastro else None

                acp_data_evento = get_text(self.driver,
                                           '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[6]/a/span[1]')
                acp_data_evento = datetime.strptime(acp_data_evento, '%d/%m/%Y') if acp_data_evento else None

                if acp_tipo == 'Sentença' and acp_esp.upper() == 'SEM JULGAMENTO DO MÉRITO':
                    acp_esp = 'Extinção sem Julgamento do Mérito'

                # print(dados_lanc['principais']['tipo']['dado'],acp_tipo)
                # print(dados_lanc['principais']['esp']['dado'],acp_esp)
                # print(data_evento_base,acp_data_evento)
                # print(data_evento_post, data_evento_prev)
                # print(today, pdata)
                # print('-----------------')

                achei_esp = False
                if tipo_alternativo == '' and esp_alternativo != '':
                    if tipo_base == acp_tipo.upper() and esp_alternativo == acp_esp.upper():
                        achei_esp = True

                if tipo_alternativo != '':
                    if tipo_alternativo == acp_tipo.upper() and esp_alternativo == acp_esp.upper():
                        achei_esp = True

                if tipo_base == acp_tipo.upper() and esp_base == acp_esp.upper():
                    achei_esp = True

                if achei_esp and acp_data_evento is not None:
                    if data_evento_prev != data_evento_base:
                        if acp_data_evento <= data_evento_post and acp_data_evento >= data_evento_prev:
                            coment = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[1]/table/tbody/tr/td/label/input')
                            if coment:
                                return True
                            else:
                                return i_tr

                    if data_evento_base == acp_data_evento:
                        if acp_cadastro <= today and acp_cadastro >= pdata:
                            coment = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[1]/table/tbody/tr/td/label/input')
                            if coment:
                                return True
                            else:
                                return i_tr

            # DETECTA SE EXISTE BOTÃO PARA IR PARA A PRÓXIMA PÁGINA E CLICA NELE
            ultimo_evento = get_text(self.driver, '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + str(
                len(linhas)) + ']/td[6]/a/span[1]')
            if ultimo_evento:
                ultima_data_evento = datetime.strptime(ultimo_evento, '%d/%m/%Y')
                if data_evento_base > ultima_data_evento:
                    break

            proximo = self.driver.find_element_by_id('fAcompanhamento:scrollResultadosidx' + str(i))
            if not proximo:
                break

            proximo.click()

        return False

    # CONFERE SE O ARQUIVO FOI LANÇADO
    def confere_arquivo(self, dados_lanc, confere_data=True, confere_tipo=True, range_data=3, utilizar_data_atual=True, retorna_linha=False):
        self.abre_aba_imagem()
        data_atual = datetime.now().date()
        data_evento = datetime.strptime(dados_lanc['data_arquivo'], '%d/%m/%Y').date()
        data_evento_prev = data_atual if utilizar_data_atual else data_evento
        data_evento_post = data_atual if utilizar_data_atual else data_evento
        if confere_data:
            data_evento_prev = data_evento_prev + relativedelta(days=-range_data)
            data_evento_post = data_evento_post + relativedelta(days=range_data)

        pags = 1
        footer = self.driver.find_element_by_xpath('//*[@id="fImagem:dtbImagem"]/tfoot/tr/td').text
        r = re.search("(\\d+)", footer, re.IGNORECASE | re.DOTALL)
        if r is not None:
            total = int(r.group(0))
            if total > 10:
                pags = total/10
                pags = math.ceil(pags)
                self.driver.find_element_by_id('fImagem:scrollResultadoslast').click()

        while pags > 0:
            pags = pags - 1
            linhas = self.driver.find_elements_by_xpath('//*[@id="fImagem:dtbImagem"]/tbody/tr')
            ultima_data_evento = self.driver.find_element_by_xpath('//*[@id="fImagem:dtbImagem"]/tbody/tr[1]/td[4]')
            if not ultima_data_evento:
                return False
            ultima_data_evento = ultima_data_evento.text
            ultima_data_evento = datetime.strptime(ultima_data_evento, '%d/%m/%Y').date()
            for indice, tr in enumerate(linhas):
                i_tr = len(linhas) - indice
                img_data = self.driver.find_element_by_xpath('//*[@id="fImagem:dtbImagem"]/tbody/tr[' + str(i_tr) + ']/td[4]').text
                img_obs = self.driver.find_element_by_xpath('//*[@id="fImagem:dtbImagem"]/tbody/tr[' + str(i_tr) + ']/td[3]').text
                img_obs = " ".join(img_obs.split())
                img_obs = img_obs.replace('¿','').replace('´','').replace('§','')
                img_tipo = self.driver.find_element_by_xpath('//*[@id="fImagem:dtbImagem"]/tbody/tr[' + str(i_tr) + ']/td[2]').text

                obs_arquivo = corta_string(dados_lanc['obs_arquivo'],190)
                obs_arquivo = obs_arquivo.replace('¿','').replace('´','').replace('§','')
                if confere_tipo:
                    if img_tipo != dados_lanc['tipo_arquivo']:
                        continue

                if confere_data:
                    data_arquivo = datetime.strptime(img_data, '%d/%m/%Y').date()
                    if range_data == 0:
                        if data_arquivo != data_evento_prev:
                            continue
                    elif not (data_arquivo >= data_evento_prev and data_arquivo <= data_evento_post):
                        continue

                if obs_arquivo in img_obs:
                    if retorna_linha:
                        return i_tr
                    else:
                        return True

                # REMOVER NO FUTURO
                if obs_arquivo.replace(' - Evento ',' - ') in img_obs:
                    if retorna_linha:
                        return i_tr
                    else:
                        return True

            if data_evento >= ultima_data_evento:
                break

            if pags > 0:
                self.driver.find_element_by_id('fImagem:scrollResultadosidx'+str(pags)).click()

        return False

    def abrir_modal_anexo(self, indice):
        if not try_click(self.driver, '//*[@id="fAcompanhamento:dtbComentario:tbody_element"]/tr[' + indice + ']/td[7]/a', tentativas=2):
            raise MildException("Erro ao clicar no link do comentário ", self.uf, self.plataforma, self.prc_id)

        if not aguarda_presenca_elemento(self.driver, '__jeniaPopupFrameTarget', tipo='ID'):
            raise MildException("Erro ao carregar modal de comentário ", self.uf, self.plataforma, self.prc_id)

        self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))

        if not aguarda_presenca_elemento(self.driver, '//*[@id="fAnexo:dtbAnexos:tbody_element"]/tr[1]/td[1]/a'):
            raise MildException("Erro ao carregar lista no modal de comentário ", self.uf, self.plataforma, self.prc_id)

    def abrir_modal_comentario(self, indice):
        if not try_click(self.driver, '//*[@id="fAcompanhamento:dtbComentario:tbody_element"]/tr['+indice+']/td[5]/a', tentativas=2):
            raise MildException("Erro ao clicar no link do comentário ", self.uf, self.plataforma, self.prc_id)

        if not aguarda_presenca_elemento(self.driver, '__jeniaPopupFrameTarget', tipo='ID'):
            raise MildException("Erro ao carregar modal de comentário ", self.uf, self.plataforma, self.prc_id)

        self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))

        if not aguarda_presenca_elemento(self.driver, '//*[@id="fPopUp"]/textarea'):
            raise MildException("Erro ao carregar lista no modal de comentário ", self.uf, self.plataforma, self.prc_id)

    # CAPTURA O STATUS ATUAL DO PROCESSO
    def captura_status(self):
        return self.driver.find_element_by_id('fDetalhar:situacao1').text.strip()

    def clear_special_chars(self, texto):
        return texto.replace('/', '').replace('\\', '').replace('.', '').replace('-', '').replace('\r', '').replace('\n', '')

    # REALIZA O POCESSO DE REAVALIAÇÃO
    def reavaliar(self, proc, abrir_aba=True, raise_error=False):
        if abrir_aba:
            self.abre_aba_principal()
            status = self.captura_status()
            if status == 'Pendente Citação':
                return True

        if proc['prc_area'] == 2:
            return self.reavaliar_trabalhista()
        else:
            return self.reavaliar_civel(abrir_aba, raise_error)

    # REALIZA O PROCESSO DE REAVALIAÇÃO CÍVEL
    def reavaliar_civel(self, abrir_aba=True, raise_error=False):
        if abrir_aba:
            self.abre_modal_contingencia()

        disabled = self.driver.find_element_by_id('fContingencia:rwgr').get_attribute('disabled')
        if disabled is not None:
            if raise_error:
                raise MildException("Contingencia Indisponível", self.uf, self.plataforma, self.prc_id)

            return False

        val = self.driver.find_element_by_id('fContingencia:valorProvavel410').get_attribute('value')
        if val != '0,00':
            self.seleciona_option('2', 'fContingencia:tr1', tipo='ID', select_by='value')
            self.preenche_campo(val, 'fContingencia:efwe', tipo='ID')
            self.seleciona_option('1', 'fContingencia:tr2', tipo='ID', select_by='value')
            self.preenche_campo(val, 'fContingencia:rwgr', tipo='ID')
            self.driver.find_element_by_xpath('//*[@id="fContingencia"]/table[5]/tbody/tr[4]/td[3]/input').click()
            erros = self.driver.find_element_by_id("subviewMessages:formHeader:msgErro")
            if erros:
                if erros.text.find('não pode ser') > -1:
                    if raise_error:
                        raise MildException("Erro na Reversão", self.uf, self.plataforma, self.prc_id)
                    return False
            self.fecha_modal()
            self.abre_modal_contingencia()

        val1 = self.driver.find_element_by_id('fContingencia:valorProvavel10').get_attribute('value')
        val2 = self.driver.find_element_by_id('fContingencia:rwgr').get_attribute('value')
        if val1 == val2 or val1 == '0,00':
            return True

        return False

    # REALIZA O PROCESSO DE REAVALIAÇÃO TRABALHISTA
    def reavaliar_trabalhista(self):
        self.abre_fecha_aba('PEDIDO(S)')
        while True:
            fim = True
            trs = self.driver.find_elements_by_xpath('//*[@id="fDetalhar:dtbPedido"]/tbody/tr')
            # for tr in trs:
            for idx, tr in enumerate(trs):
                btn = self.driver.find_element_by_xpath('//*[@id="fDetalhar:dtbPedido"]/tbody/tr[' + str(idx + 1) + ']/td[10]/a')
                if not btn:
                    continue
                tipo = self.driver.find_element_by_xpath('//*[@id="fDetalhar:dtbPedido"]/tbody/tr['+str(idx+1)+']/td[1]').text.strip()
                possivel = self.driver.find_element_by_xpath('//*[@id="fDetalhar:dtbPedido"]/tbody/tr[' + str(idx + 1) + ']/td[7]').text.strip()
                # possivel = tr.find_element_by_xpath('td[7]').text.strip()

                if possivel == '0,00' or possivel == '':
                    continue

                fim = False
                remoto = self.driver.find_element_by_xpath('//*[@id="fDetalhar:dtbPedido"]/tbody/tr['+str(idx+1)+']/td[8]').text.strip()
                btn.click()
                self.abre_e_aguarda_modal()

                print(tipo, possivel, remoto)
                if remoto != '0,00':
                    self.seleciona_option('2', 'fPedido:tr1', tipo='ID', select_by='value')
                    self.preenche_campo(possivel, 'fPedido:efwe', tipo='ID')
                    # self.driver.find_element_by_id('fPedido:rwgr').click()
                    btn = self.driver.find_element_by_id('fPedido:_idJsp47')
                    if btn:
                        self.driver.find_element_by_id('fPedido:_idJsp47').click()
                else:
                    self.seleciona_option('1', 'fPedido:tr2', tipo='ID', select_by='value')
                    self.preenche_campo(possivel, 'fPedido:rwgr', tipo='ID')
                    # self.driver.find_element_by_id('fPedido:rwgr').click()
                    btn = self.driver.find_element_by_id('fPedido:_idJsp53')
                    if btn:
                        self.driver.find_element_by_id('fPedido:_idJsp53').click()

            if fim:
                self.fecha_modal()
                break

        return True

    def confere_filtro(self):
        if self.driver.find_element_by_id('fAcompanhamento:pnlAlertaContaFiltro'):
            raise FatalException('Processo com Filtro', self.uf, self.plataforma, self.prc_id)

        if self.driver.find_element_by_id('fDetalhar:pnlAlertaContaFiltro'):
            raise FatalException('Processo com Filtro', self.uf, self.plataforma, self.prc_id)

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