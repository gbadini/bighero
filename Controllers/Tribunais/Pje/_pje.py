from Config.helpers import *
from Controllers.Tribunais.primeiro_grau import *
# from Config.database import connect_db
from selenium.webdriver.common.keys import *
from Models.processoModel import *
import win32gui
import win32con
import win32api
import win32com.client
import pyautogui
import win32process
from pywinauto.application import Application

from pywinauto.keyboard import send_keys
from pywinauto.findwindows import *
import sys, time, shutil

# CLASSE DA VARREDURA DO PJE. HERDA OS METODOS DA CLASSE PLATAFORMA
class Pje(PrimeiroGrau):

    def __init__(self):
        super().__init__()
        self.plataforma = 2
        self.div = None
        self.movs = []
        self.tempo_nao_iniciado_download = 45

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        inicio = time.time()
        sso_frame = False
        while True:
            if time.time() - inicio > 40:
                return False

            if self.driver.find_element_by_id('loginAplicacaoButton'):
                break

            if self.driver.find_element_by_id('ssoFrame'):
                sso_frame = True
                break

        self.remove_erro_pje()

        id_btn = 'loginAplicacaoButton'
        if sso_frame:
            id_btn = 'kc-pje-office'
            self.driver.switch_to.frame(self.driver.find_element_by_id('ssoFrame'))
            if not aguarda_presenca_elemento(self.driver, 'kc-pje-office', tipo='ID'):
                return False

        if aguarda_presenca_elemento(self.driver, 'btnUtilizarApplet', tipo='ID', tempo=5):
            try_click(self.driver, 'btnUtilizarApplet', tipo='ID')

        if not aguarda_presenca_elemento(self.driver, id_btn, tipo='ID'):
            try_click(self.driver, 'btnUtilizarApplet', tipo='ID')

        try:
            self.driver.find_element_by_id(id_btn).click()
        except ElementClickInterceptedException:
            try_click(self.driver, 'btnUtilizarApplet', tipo='ID')
            time.sleep(2)
            if not try_click(self.driver, id_btn, tipo='ID'):
                return False

        ttv = 0
        while not self.confirma_pje_office():
            ttv += 1
            if ttv > 5:
                # raise Exception('Erro ao realizar login')
                return False

            time.sleep(1)
            if aguarda_alerta(self.driver):
                return False

            if self.driver.find_element_by_id('/html/body/nav'):
                break

            try:
                btn = self.driver.find_element_by_id(id_btn)
                print('clicando')
                if btn:
                    btn.click()
                else:
                    continue
            except:
            # except StaleElementReferenceException:
                # self.driver.refresh()
                # self.driver.find_element_by_id('loginAplicacaoButton').click()
                continue


        if not aguarda_presenca_elemento(self.driver, '/html/body/nav'):
            return False

        return True

    # CONFIRMA DIALOG DO PJEOFFICE RO
    def remove_erro_pje(self):
        try:
            hwndMain = win32gui.FindWindow(None, "Erro ao executar tarefa")
            if hwndMain > 0:
                if win32gui.IsWindowVisible(hwndMain):
                    print("Modal Erro Localizado")
                    # self.bring_to_front(hwndMain)
                    win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)

        except Exception as e:
            pass

        try:
            hwndMain = win32gui.FindWindow(None, "Erro ao executar a tarefa")
            if hwndMain > 0:
                if win32gui.IsWindowVisible(hwndMain):
                    print("Modal Erro Localizado")
                    # self.bring_to_front(hwndMain)
                    win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)

        except Exception as e:
            pass

    # CONFIRMA DIALOG DO PJEOFFICE
    def confirma_pje_office(self):
        time.sleep(1)
        inicio = time.time()
        while True:
            if (time.time() - inicio) >= 40:
                raise Exception('PJE Office não localizado')

            time.sleep(1)
            print('Procurando Janela de Confirmação do PJE')
            # load_cert = self.driver.find_element_by_id('mp_formValidarContentTable')
            # if not load_cert:
            #     self.driver.find_element_by_id('loginAplicacaoButton').click()

            try:
                if self.driver.find_element_by_xpath('/html/body/nav'):
                    return True
            except:
                return False

            # AUTORIZAÇÃO DO CERTIFICADO
            try:
                hwndMain = win32gui.FindWindow(None, "Autorização")
                if hwndMain > 0:
                    print("Modal Localizado")
                    # self.bring_to_front(hwndMain)
                    win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                    time.sleep(1)
                # return True
            except Exception as e:
                # print(e)
                pass

            # MODAL DE SENHA
            try:
                hwndMain = win32gui.FindWindow(None, "Insira o PIN:")
                if hwndMain > 0:
                    print("Modal Senha Localizado")
                    # chars = (0x73,0x65,0x72,0x61,0x73,0x61,0x31,0x32)
                    #
                    # for c in chars:
                    #    win32api.PostMessage(hwndMain, win32con.WM_CHAR, c, 0)
                    # self.bring_to_front(hwndMain)
                    # remote_thread, _ = win32process.GetWindowThreadProcessId(hwndMain)
                    # win32process.AttachThreadInput(win32api.GetCurrentThreadId(), remote_thread, True)
                    # win32gui.SetForegroundWindow(hwndMain)
                    # win32api.keybd_event(win32con.WM_KEYDOWN, 0, )  # Alt

                    # win32gui.SendMessage(hwnd, win32con.WM_SETCURSOR, hwnd, win32api.MAKELONG(win32con.HTCLIENT, win32con.WM_MOUSEMOVE))
                    # win32gui.SendMessage(hwnd, win32con.WM_MOUSEACTIVATE, hwnd, win32api.MAKELONG(win32con.HTCLIENT, win32con.WM_LBUTTONDOWN))
                    try:
                        self.bring_to_front(hwndMain)
                    except:
                        pass
                    win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                    time.sleep(1)
                # return True
            except Exception as e:
                print(e)
                pass

            window_name = 'Autorização de Servidor'
            def callback(h, extra):
                # print(win32gui.GetWindowText(h))
                if window_name in win32gui.GetWindowText(h):
                    extra.append(h)
                return True

            extra = []
            win32gui.EnumWindows(callback, extra)
            if len(extra) > 0:
                for hwndMain in extra:
                    print("Modal autorização Localizado")
                    if not win32gui.IsWindowVisible(hwndMain):
                        continue

                    # l, t, _, _ = win32gui.GetWindowRect(hwndMain)
                    l, t, r, b = win32gui.GetWindowRect(hwndMain)
                    # print(l,t,r,b)

                    lParam = win32api.MAKELONG(math.ceil(r*0.693), math.ceil(b*0.958))

                    # if r - l > 400:
                    #     lParam = win32api.MAKELONG(l + 62, t + 192)
                    # else:
                    #     lParam = win32api.MAKELONG(l + 68, t + 173)

                    try:
                        self.bring_to_front(hwndMain)
                    except:
                        pass
                    try:
                        win32gui.PostMessage(hwndMain, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                        win32gui.PostMessage(hwndMain, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, lParam)
                    except:
                        tb = traceback.format_exc()
                        print(tb)
                        time.sleep(1)

            # continue

            # CONFIRMAÇÃO DO CERTIFICADO
            # hwndMain = win32gui.FindWindow(None, "Autorização de Servidor")
            # if hwndMain > 0:
            #     print("Modal autorização Localizado")
            #     print(pyautogui.position())
            #
            #     l, t, _, _ = win32gui.GetWindowRect(hwndMain)
            #     print(l + 30, t + 152)
            #     # lParam = win32api.MAKELONG(l+30, t+152)
            #     lParam = win32api.MAKELONG(l + 62, t + 192)
            #     lParam2 = win32api.MAKELONG(l+68, t+173)
            #
            #     try:
            #         self.bring_to_front(hwndMain)
            #     except:
            #         pass
            #     try:
            #         win32gui.PostMessage(hwndMain, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam2)
            #         win32gui.PostMessage(hwndMain, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, lParam2)
            #
            #         win32gui.PostMessage(hwndMain, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            #         win32gui.PostMessage(hwndMain, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, lParam)
            #     except:
            #         tb = traceback.format_exc()
            #         print(tb)
            #         time.sleep(1)

            def callback(h, extra):
                # print(win32gui.GetWindowText(h))
                if 'Erro ao executar tarefa' in win32gui.GetWindowText(h):
                    extra.append(h)

                if 'Erro ao executar a tarefa' in win32gui.GetWindowText(h):
                    extra.append(h)

                return True

            extra = []
            win32gui.EnumWindows(callback, extra)
            if len(extra) > 0:
                for hwndMain in extra:
                    if win32gui.IsWindowVisible(hwndMain):
                        try:
                            self.bring_to_front(hwndMain)
                        except:
                            pass
                        win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                        print("Modal erro Localizado")
                        return False
            #
            # # ERRO NA LEITURA DO CERTIFICADO
            # try:
            #     hwndMain = win32gui.FindWindow(None, "Erro ao executar tarefa")
            #     if hwndMain > 0:
            #         if win32gui.IsIconic(hwndMain):
            #             try:
            #                 self.bring_to_front(hwndMain)
            #             except:
            #                 pass
            #             win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
            #             print("Modal erro Localizado")
            #             return False
            # except Exception as e:
            #     # print(e)
            #     pass
            #
            # # ERRO NA LEITURA DO CERTIFICADO
            # try:
            #     hwndMain = win32gui.FindWindow(None, "Erro ao executar a tarefa")
            #     if hwndMain > 0:
            #         if win32gui.IsIconic(hwndMain):
            #             try:
            #                 self.bring_to_front(hwndMain)
            #             except:
            #                 pass
            #             win32api.PostMessage(hwndMain, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
            #             print("Modal erro Localizado")
            #             return False
            # except Exception as e:
            #     # print(e)
            #     pass



    def bring_to_front(self, hwndMain):
        win32gui.ShowWindow(hwndMain, 5)
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%')
        win32gui.SetForegroundWindow(hwndMain)

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        ordem = numero_busca[0:7]
        digito1 = numero_busca[7:9]
        ano = numero_busca[9:13]
        justica = numero_busca[13:14]
        tribunal = numero_busca[14:16]
        digito2 = numero_busca[16:]

        aguarda_alerta(self.driver, tempo=0, aceitar=False)

        if not self.driver.find_element_by_xpath('//*[@id="fPP:consultaPeticaoSearchForm"]/div/div/div[2]/input[1]'):
            raise CriticalException("Erro ao buscar processo (Unhandled Exception)", self.uf, self.plataforma, self.prc_id)

        if not self.driver.find_element_by_xpath('//*[@id="fPP:consultaPeticaoSearchForm"]/div/div/div[2]/input[1]').is_displayed():
            raise MildException("Erro ao buscar processo (Campo Oculto)", self.uf, self.plataforma, self.prc_id, False)

        for i in range(1, 6):
            try:
                self.driver.find_element_by_xpath('//*[@id="fPP:consultaPeticaoSearchForm"]/div/div/div[2]/input['+str(i)+']').clear()
            except InvalidElementStateException:
                pass

        self.driver.find_element_by_xpath('//*[@id="fPP:consultaPeticaoSearchForm"]/div/div/div[2]/input[1]').send_keys(ordem)
        self.driver.find_element_by_xpath('//*[@id="fPP:consultaPeticaoSearchForm"]/div/div/div[2]/input[2]').send_keys(digito1)
        self.driver.find_element_by_xpath('//*[@id="fPP:consultaPeticaoSearchForm"]/div/div/div[2]/input[3]').send_keys(ano)
        try:
            self.driver.find_element_by_xpath('//*[@id="fPP:consultaPeticaoSearchForm"]/div/div/div[2]/input[4]').send_keys(justica)
        except InvalidElementStateException:
            pass
        self.driver.find_element_by_xpath('//*[@id="fPP:consultaPeticaoSearchForm"]/div/div/div[2]/input[5]').send_keys(tribunal)
        self.driver.find_element_by_xpath('//*[@id="fPP:consultaPeticaoSearchForm"]/div/div/div[2]/input[6]').send_keys(digito2)

        self.driver.find_element_by_xpath('//*[@id="fPP:consultaPeticaoSearchForm"]/div/div/div[2]/input[6]').send_keys(Keys.ENTER)
        self.wait()
        self.wait(30, 'modalStatusContainer')

        try_click(self.driver, '//*[@id="popupAlertaCertificadoProximoDeExpirarContentDiv"]/div/form')
        if not aguarda_presenca_elemento(self.driver, 'fPP:processosTable:tb', tipo='ID'):
            raise MildException("Erro ao buscar processo (tabela não localizada)", self.uf, self.plataforma, self.prc_id, False)

        # CONFERE SE JA CARREGOU A LISTAGEM
        trs = self.driver.find_elements_by_xpath('//*[@id="fPP:processosTable:tb"]/tr')
        if len(trs) == 0 and not check_text(self.driver, '//*[@id="fPP:processosPeticaoGridPanel_body"]/dl', 'NÃO FOI ENCONTRADO'):
            time.sleep(1)

        if check_text(self.driver, '//*[@id="fPP:processosPeticaoGridPanel_body"]/dl', 'NÃO FOI ENCONTRADO'):
            return False

        footer = self.driver.find_element_by_xpath('//*[@id="fPP:processosTable"]/tfoot/tr/td/div/div[2]/span')
        if footer.text == '0 resultados encontrados':
            return False

        trs = self.driver.find_elements_by_xpath('//*[@id="fPP:processosTable:tb"]/tr')
        if len(trs) == 0:
            raise MildException("Erro ao buscar processo", self.uf, self.plataforma, self.prc_id, False)

        return True

    # AGUARDA ATÉ QUE A ANIMAÇÃO DE LOADING ESTEJA OCULTA
    def wait(self, tempo=30, id='_viewRoot:status.start'):
        # time.sleep(0.2)
        if self.driver.find_element_by_id(id):
            # wait = WebDriverWait(self.driver, 0.2)
            # try:
            #     wait.until(EC.visibility_of_element_located((By.ID, id)))
            # except TimeoutException:
            #     pass


            wait = WebDriverWait(self.driver, tempo)
            try:
                wait.until(EC.invisibility_of_element((By.ID, id)))
            except TimeoutException:
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)

        # f = self.driver.find_element_by_id(id)
        # inicio = time.time()
        # while f:
        #     time.sleep(0.2)
        #     f = self.driver.find_element_by_id(id).is_displayed()
        #     if time.time() - inicio > tempo:
        #         raise MildException("Loading Timeout")

        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        aguarda_presenca_elemento(self.driver,'//*[@id="fPP:processosTable:tb"]/tr/td[2]')
        el = self.driver.find_element_by_xpath('//*[@id="fPP:processosTable:tb"]/tr/td[2]')
        numero_site = ''
        if el:
            numero_site = ajusta_numero(el.text)
            if numero_busca == numero_site:
                return True

        raise MildException("Número CNJ Diferente " + numero_site + ' | ' + numero_busca, self.uf, self.plataforma, self.prc_id)

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        self.confere_cnj(numero_busca)

        achei = False
        if check_text(self.driver, '//*[@id="fPP:processosPeticaoGridPanel_body"]/dl', 'sigilo'):
            achei = True

        exc = self.driver.find_element_by_class_name('fa-exclamation-circle')
        if exc:
            achei = True

        if achei:
            if not self.driver.find_element_by_xpath('//*[@id="fPP:processosTable:tb"]/tr/td[1]/a[2]'):
                return True

        self.abre_processo()

        return False

    def abre_processo(self):
        self.abre_aba_processo()
        self.wait(10)

        if check_text(self.driver, '//*[@id="pageBody"]/div/div[2]/pre/dl', 'Sem permissão para acessar a página'):
            self.fecha_processo()
            self.abre_aba_processo()
            self.wait(10)
            if check_text(self.driver, '//*[@id="pageBody"]/div/div[2]/pre/dl', 'Sem permissão para acessar a página'):
                raise MildException("Erro de permissão", self.uf, self.plataforma, self.prc_id)

        erro = self.driver.find_element_by_class_name('alert-danger')
        if erro:
            if erro.text.upper().find('Erro inesperado') > -1:
                raise CriticalException("Erro ao abrir processo (Unhandled Exception)", self.uf, self.plataforma,
                                        self.prc_id)

    def abre_aba_processo(self, index=1):
        if not try_click(self.driver, '//*[@id="fPP:processosTable:tb"]/tr['+str(index)+']/td[1]/a[1]'):
            raise MildException("Botão de abrir não localizado", self.uf, self.plataforma, self.prc_id, False)

        aguarda_alerta(self.driver)

        self.alterna_janela()

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        self.wait(10)
        aviso = self.driver.find_element_by_xpath('//*[@id="detalheDocumento:quadroDocumento"]/h3')
        if aviso:
            if aviso.text.find('não possui permissão') > -1:
                return True

        self.get_div()
        el_dia = self.driver.find_element_by_xpath('//*[@id="divTimeLine:' + self.div + '"]/div[2]')
        if not el_dia:
            raise MildException("Erro ao capturar última movimentação", self.uf, self.plataforma, self.prc_id)

        movimentos = self.driver.find_elements_by_xpath('//*[@id="divTimeLine:' + self.div + '"]/div')
        movs = self.captura_movimentos(movimentos, ultima_data, base, prc_id, False, limite=8, rec_id=self.rec_id)

        return len(movs) == 0

        # dia = el_dia.text
        # hora = self.driver.find_element_by_xpath('//*[@id="divTimeLine:' + self.div + '"]/div[3]')
        #
        # small = hora.find_elements_by_tag_name('small')
        # if len(small) == 0 or small[-1] is None:
        #     raise MildException("Erro ao capturar data", self.uf, self.plataforma, self.prc_id)
        #
        # hora = small[-1].text.strip()
        # dia_tj = localiza_data(dia)
        # if not dia_tj or hora == '':
        #     raise MildException("Erro ao capturar data", self.uf, self.plataforma, self.prc_id)
        #
        # data_tj = datetime.strptime(dia_tj+' '+hora, '%Y-%m-%d %H:%M')
        # # d_base = datetime.strptime(ultima_data, '%Y-%m-%d %H:%M:%S')
        # if ultima_data == data_tj:
        #     return True
        #
        # return False

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
        rec_id = proc_data['rec_id'] if 'rec_id' in proc_data else None
        self.get_div()
        self.movs = []
        movs = []
        self.wait(50)
        total_paginas = 1
        pagina_atual = 1
        if completo:
            if not self.driver.find_element_by_id('totalPaginas'):
                raise MildException("Erro ao carregar tela processo", self.uf, self.plataforma, self.prc_id)

            total_paginas = self.driver.find_element_by_id('totalPaginas').get_attribute('value')
            total_paginas = int(total_paginas)

        movimentos = self.driver.find_elements_by_xpath('//*[@id="divTimeLine:' + self.div + '"]/div')
        if len(movimentos) == 0:
            raise MildException("Erro ao capturar movimentações (tabela vazia)", self.uf, self.plataforma, self.prc_id)

        top = 0
        inicio = time.time()
        tentativas = 0
        while pagina_atual < total_paginas:
            if time.time() - inicio > 120:
                raise MildException("Erro ao capturar movimentações (não carregou na íntegra)", self.uf, self.plataforma, self.prc_id)

            top += 15000
            self.driver.execute_script("document.getElementById('divTimeLine:divEventosTimeLine').scrollTop = "+str(top))
            # movimentos[-1].location_once_scrolled_into_view
            time.sleep(0.5)
            if not self.wait(60):
                raise MildException("Erro ao aguardar movimentações", self.uf, self.plataforma, self.prc_id)

            movimentos = self.driver.find_elements_by_xpath('//*[@id="divTimeLine:' + self.div + '"]/div')
            paginaAtual = self.driver.find_element_by_id('paginaAtual')
            if not paginaAtual:
                raise MildException("Erro ao capturar campo de página atual", self.uf, self.plataforma, self.prc_id)
            nova_pagina = paginaAtual.get_attribute('value')
            nova_pagina = int(nova_pagina)

            if pagina_atual == nova_pagina and nova_pagina != total_paginas:
                tentativas += 1
                if time.time() - inicio > 20:
                    self.driver.refresh()
                foca_janela(self.process_children)
                if total_paginas == 2 and nova_pagina== 1 and tentativas > 3:
                    movimentos = self.driver.find_elements_by_xpath('//*[@id="divTimeLine:' + self.div + '"]/div')
                    if find_string(movimentos[-1].text+movimentos[-2].text,('PETIÇÃO INICIAL','DISTRIBU')):
                        break

                continue

            tentativas = 0
            inicio = time.time()
            pagina_atual = nova_pagina
            if pagina_atual == total_paginas:
                break

        if len(movimentos) == 0:
            raise MildException("Erro ao capturar movimentações (tabela vazia)", self.uf, self.plataforma, self.prc_id)

        movs = self.captura_movimentos(movimentos, ultima_mov, base, prc_id, completo, rec_id=rec_id)
        return movs

    def captura_movimentos(self, movimentos, ultima_mov, base, prc_id, completo, limite=None, rec_id=None):
        del movimentos[0]
        lista = Acompanhamento.lista_movs(base, prc_id, self.plataforma, acp_grau=self.grau, rec_id=rec_id)
        capturar = True
        total_limite = 0
        i = 0
        movs = []
        for mov in movimentos:
            i += 1
            try:
                cls = mov.get_attribute('class')
                txt = mov.text

                if cls == 'media data':
                    dia = localiza_data(txt)
                    if not dia:
                        raise MildException("Erro ao capturar data da movimentação", self.uf, self.plataforma, self.prc_id)

                    continue

                # texto_mov = localiza_elementos(mov, ('texto-movimento','anexos','texto-movimento-inativo'), tipo='CLASS_NAME', retorna_multiplos=True)
                texto_mov = mov.find_elements_by_xpath('div[2]/div')
                textos = []
                txt_total = ''
                hora = ''
                for tt in texto_mov:
                    # if not tt:
                    #     continue

                    hora_mov = tt.find_elements_by_tag_name('small')
                    hora = ''
                    if hora_mov:
                        hora = hora_mov[0].text
                        break

                    texto = tt.text.strip()
                    if texto != '':
                        txt_total += ' ' + texto

                    tmi = tt.find_elements_by_class_name('texto-movimento-inativo')
                    agn = None
                    if len(tmi) > 0 and texto != '':
                        agn = False
                        texto = '<strike>' + texto + '</strike>'

                    anexo = False
                    cls = tt.get_attribute('class')
                    if cls.find('anexos') > -1:
                        if texto == '':
                            continue
                        agn = False
                        anexo = True

                    textos.append({'texto': texto, 'agenda': agn, 'anexo': anexo})

                if len(textos) == 0:
                    continue

                if hora == '':
                    print(textos)
                    raise MildException("Erro ao capturar data na movimentação", self.uf, self.plataforma, self.prc_id)

                # COMPARA SE O TAMANHO DO TEXTO DA DIV É IGUAL AO TEXTO CAPTURADO, CASO CONTRARIO, HOUVE ERRO NA CAPTURA DO TEXTO
                mov_completo = mov.text[:-5].replace('\r', ' ').replace('\n', ' ').strip()
                mov_textos = txt_total.replace('\r', ' ').replace('\n', ' ').strip()
                if len(mov_textos) != len(mov_completo):
                    # print(len(mov_completo), mov_completo)
                    # print(len(mov_textos), mov_textos)
                    raise MildException("Erro no tamanho dos textos", self.uf, self.plataforma, self.prc_id)

                data_tj = datetime.strptime(dia+' '+hora, '%Y-%m-%d %H:%M')
                # data_tj = ''
            except StaleElementReferenceException:
                raise MildException("Erro ao capturar data da movimentação", self.uf, self.plataforma, self.prc_id)

            # CONFERE SE ALGUM DOS TEXTOS ESTÁ VAZIO E ELIMINA, CASO NÃO SEJA O ÚNICO ELEMENTO
            if len(textos) > 1:
                it = 0
                for t in textos[:]:
                    if t['texto'] == '' and len(textos) > 1:
                        del textos[it]
                        continue
                    it += 1

            fim = False
            for txt_dict in textos:
                total_limite += 1
                # print("txt_dict",txt_dict)
                texto = txt_dict['texto']
                agn = txt_dict['agenda'] if len(textos) > 1 else None
                anx = txt_dict['anexo']

                # print('tj', data_tj, txt_dict)
                capturar = True
                if anx and ultima_mov is not None and data_tj <= ultima_mov and len(textos) > 1 and textos[0]['texto'] != '':
                    capturar = False
                elif anx and ultima_mov is not None and data_tj <= ultima_mov and texto.upper().find('- PETIÇÃO INICIAL') > -1:
                    capturar = False
                else:
                    esp_site = self.trata_esp(texto)
                    for l in lista:
                        esp_base = self.trata_esp(l['acp_esp'])

                        if data_tj == l['acp_cadastro']:
                            # print('db',l)
                            if esp_site == esp_base:
                                capturar = False
                                break

                # if not capturar and not completo and i >= 10:
                #     break

                self.movs.append({'dia': data_tj, 'esp': texto, 'novo': capturar})

                if capturar:
                    tipo = get_tipo_pje(texto)
                    # print({'acp_cadastro': data_tj, 'acp_esp': texto, 'acp_tipo': tipo})
                    movs.append({'acp_cadastro': data_tj, 'acp_esp': texto, 'acp_tipo': tipo, 'acp_agenda': agn, 'acp_ocorrencia': agn})

                if self.grau == 2 and texto.upper().find('DISTRIBUÍDO POR SORTEIO') > -1 and texto.upper().find('REDISTRIBUÍDO') == -1:
                    fim = True

                if limite is not None and limite <= total_limite:
                    fim = True

            if fim:
                break

        # if limite is None and not completo and len(movs) == 0 and ultima_mov is not None:
        #     raise MildException("Movimentação Suspeita", self.uf, self.plataforma, self.prc_id)

        return movs

    def trata_esp(self, texto):
        texto = texto.replace('<strike>','')
        texto = texto.replace('</strike>', '')
        if texto == '':
            return texto

        src = re.search(r"(\d+)", texto[0])
        if src:
            ft = texto.find('-')
            if ft > -1:
                texto = texto[ft + 1:].strip()
        texto = corta_string(texto)

        return texto

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []
        for mov in self.movs:
            if not self.completo and not mov['novo']:
                break

            esp = mov['esp'].upper().strip()
            if esp.find('970 - ') != 0:
                if esp == '' or esp == 'AUDIÊNCIA' or esp == 'AUDIÊNCIA PRELIMINAR/CONCILIAÇÃO' or (esp.find('AUDIÊNCIA') != 0):
                    continue

            aud = localiza_audiencia(esp)
            if not aud:
                continue

            if 'prp_tipo' not in aud or 'prp_status' not in aud:
                if esp.find('SEMANA NACIONAL DE CONCILIAÇÃO') > -1:
                    aud['prp_tipo'] = 'Conciliação'
                    aud['prp_status'] = 'Designada'
                elif aud['prp_tipo'] == 'Audiência' and 'prp_status' not in aud:
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
            hora =  aud['prp_data'].strftime('%H:%M')
            if aud['prp_status'] == 'Designada' or esp.find('REDESIGNADA PARA') > -1:
                aud['prp_status'] = 'Designada'
                p = esp.find(hora)
                serventia = esp[p+5:].strip()

            aud['prp_serventia'] = serventia
            aud['data_mov'] = mov['dia']
            adcs.append(aud)

        return adcs

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        element = self.driver.find_element_by_class_name("mais-detalhes")
        self.driver.execute_script("arguments[0].className += ' open'", element)

        partes = {'ativo':[], 'passivo':[]}
        aguarda_presenca_elemento(self.driver, '//*[@id="poloAtivo"]/table/tbody/tr[1]', aguarda_visibilidade=True, tempo=15)
        inicio = time.time()
        while True:
            tempoTotal = time.time() - inicio
            if tempoTotal >= 30:
                raise MildException("Erro ao exibir partes", self.uf, self.plataforma, self.prc_id)
            atv = self.driver.find_element_by_xpath('//*[@id="poloAtivo"]/table/tbody/tr[1]').text.strip()
            if atv != '':
                break

        if not self.driver.find_element_by_xpath('//*[@id="navbar"]/ul/li/a[1]').is_displayed():
            raise MildException("Erro ao abrir processo (partes não carregadas)", self.uf, self.plataforma, self.prc_id, False)

        polos = {'ativo': 'poloAtivo', 'passivo': 'poloPassivo'}
        for polo in polos:
            i = 0
            prts = self.driver.find_elements_by_xpath('//*[@id="'+polos[polo]+'"]/table/tbody/tr')
            for prt in prts:
                c = localiza_elementos(prt, ('td[1]/span[1]', 'td[1]/a[1]'))
                txt = c.text
                cpf = 'Não Informado'

                p1 = txt.find(':')
                if p1 > -1:
                    cpf_temp = txt[p1+1:]
                    p2 = 0
                    while p2 > -1:
                        p2 = cpf_temp.rfind('(')
                        if p2 > -1:
                            cpf_temp = cpf_temp[:p2].strip()

                    if cpf_temp.find('.') > -1 and cpf_temp.find('-') > -1:
                        cpf = cpf_temp

                p1 = txt.find(' - ')
                if p1 > -1:
                    nome = txt[:p1]
                else:
                    p1 = 0
                    nome = txt
                    while p1 >-1:
                        p1 = nome.rfind('(')
                        if p1 > -1:
                            nome = nome[:p1].strip()

                if nome.strip() == '':
                    continue

                partes[polo].append({'prt_nome': nome, 'prt_cpf_cnpj': cpf})
                i += 1

        # if len(partes['ativo']) == 0:
        #     raise MildException("Parte Ativa Vazia", self.uf, self.plataforma, self.prc_id)

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        polos = {'ativo': 'poloAtivo', 'passivo': 'poloPassivo'}
        for polo in polos:
            i = 0
            prts = self.driver.find_elements_by_xpath('//*[@id="'+polos[polo]+'"]/table/tbody/tr')

            for prt in prts:
                advs = prt.find_elements_by_xpath('td/ul/li')

                for adv in advs:
                    tipo = adv.find_element_by_tag_name('i').get_attribute('title')
                    prr_tipo = 'Advogado'
                    if tipo != '' and tipo.upper().find('REPRESENTANTE') == -1 and tipo.upper().find('ADVOGAD') == -1:
                        prr_tipo = tipo

                    prr_nome = adv.text.strip()
                    if prr_nome == '':
                        continue
                    prr_oab = None
                    p = prr_nome.upper().find('- OAB')
                    if p > -1:
                        prr_oab = prr_nome[p+5:]
                        prr_nome = prr_nome[:p-1]

                    p = prr_nome.upper().find('REGISTRADO(A)')
                    if p > -1:
                        prr_nome = prr_nome[:p-1]

                    p = prr_nome.upper().find('- CPF')
                    if p > -1:
                        prr_nome = prr_nome[:p-1]

                    if prr_oab is not None:
                        p = prr_oab.upper().find('- CPF')
                        if p > -1:
                            prr_oab = prr_oab[:p-1]
                            prr_oab = prr_oab.replace('(ADVOGADO)', '')

                    prr_nome = prr_nome.replace('(ADVOGADO)', '')

                    resps.append({'prr_nome': prr_nome, 'prr_oab': prr_oab, 'prr_cargo': prr_tipo, 'prr_parte': 'Polo '+polo})

        self.driver.execute_script("A4J.AJAX.Submit('navbar',event,{'similarityGroupingId':'navbar:linkAbaDocumentos','parameters':{'navbar:linkAbaDocumentos':'navbar:linkAbaDocumentos'} } );")
        self.wait(60)

        if self.driver.find_element_by_id('toggleDocumentos_switch_off'):
            if self.driver.find_element_by_id('toggleDocumentos_switch_off').is_displayed():
                # self.driver.execute_script("SimpleTogglePanelManager.toggleOnAjax(event,'toggleDocumentos');A4J.AJAX.Submit(null,event,{'similarityGroupingId':'toggleDocumentos','actionUrl':'/pje\x2Dweb/Processo/ConsultaProcesso/Detalhe/listProcessoCompletoAdvogado.seam','parameters':{'toggleDocumentos':'toggleDocumentos','ajaxSingle':'toggleDocumentos'} } )")
                self.driver.find_element_by_id('toggleDocumentos_switch_off').click()
                self.wait()

        aguarda_presenca_elemento(self.driver, '//*[@id="processoDocumentoGridList:tb"]/tr[1]')

        trs = self.driver.find_elements_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr')
        l = 0
        for tr in trs:
            l += 1
            linha_atual = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr[' + str(l) + ']')
            usuario = linha_atual.find_element_by_xpath('td[6]').text
            doc = linha_atual.find_element_by_xpath('td[7]').text

            f = usuario.upper().find('MAGISTRAD')
            f2 = doc.upper().find('MAGISTRAD')
            f3 = doc.upper().find('VOTO DO MAGISTRADO')
            if f > -1:
                nome = usuario[:f - 3].strip()
            elif(f3 > -1):
                nome = doc[19:].strip()
            else:
                nome = usuario

            # nome = usuario[:f-3].strip() if f > -1 else usuario

            if f > -1 or f2 > -1:
                resps.append({'prr_nome': nome, 'prr_oab': '', 'prr_cargo': 'Juiz', 'prr_parte': ''})
                break

        return resps

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}
        xpaths = ('//*[@id="maisDetalhes"]/dl/dt','//*[@id="maisDetalhes"]/div[1]/dl/dt',)
        campos = {'Julgador': 'prc_serventia', 'Jurisdição': 'prc_comarca2', 'Classe': 'prc_classe', 'Assunto': 'prc_assunto', 'Valor': 'prc_valor_causa', 'Segredo': 'prc_segredo', 'Prioridade': 'prc_prioridade', 'distribuição': 'prc_distribuicao'}
        for xp in xpaths:
            dts = self.driver.find_elements_by_xpath(xp)
            i = 0
            for dt in dts:
                i += 1
                titulo = dt.text
                campo = ''
                for c in campos:
                    if titulo.upper().find(c.upper()) > -1:
                        campo = campos[c]
                        break

                if campo == '':
                    continue

                conteudo = self.driver.find_element_by_xpath(xp[:-2]+'dd['+str(i)+']').text
                prc[campo] = conteudo

        if len(prc) == 0:
            raise MildException("Erro ao abrir processo", self.uf, self.plataforma, self.prc_id, False)

        if 'prc_serventia' not in prc:
            prc['prc_serventia'] = prc['prc_comarca2']

        if 'prc_comarca2' in prc:
            prc['prc_comarca2'] = localiza_comarca(prc['prc_comarca2'], self.uf)

        if 'prc_segredo' in prc:
            prc['prc_segredo'] = True if prc['prc_segredo'] == 'SIM' else False

        if 'prc_prioridade' in prc:
            prc['prc_prioridade'] = True if prc['prc_prioridade'] == 'SIM' else False

        if 'prc_distribuicao' in prc:
            data_dist = localiza_data(prc['prc_distribuicao'])
            if not data_dist:
                del prc['prc_distribuicao']
            else:
                prc['prc_distribuicao'] = data_dist

        if status_atual == 'Segredo de Justiça':
            status_atual = 'Ativo'

        prc['prc_status'] = get_status(self.movs, status_atual)

        numero2 = self.driver.find_element_by_xpath('//*[@id="navbar"]/ul/li/a[1]').text
        r = re.search("((\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+))", numero2, re.IGNORECASE | re.DOTALL)
        if r is not None:
            prc['prc_numero2'] = r.group(0)

        return prc

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, pasta_intermediaria):
        # print(arquivos_base)
        # print('pen', pendentes)
        arquivos = []
        total_arquivos = 0
        total_pags = 1
        # SE FOR SOMENTE DOWNLOAD, ABRE O LINK DOS DOWNLOADS
        if self.tipo == 1:
            self.driver.execute_script("A4J.AJAX.Submit('navbar',event,{'similarityGroupingId':'navbar:linkAbaDocumentos','parameters':{'navbar:linkAbaDocumentos':'navbar:linkAbaDocumentos'} } );")
            self.wait(60)
            aguarda_presenca_elemento(self.driver, '//*[@id="processoDocumentoGridList:tb"]/tr[1]')
            if self.driver.find_element_by_id('toggleDocumentos_switch_off'):
                if self.driver.find_element_by_id('toggleDocumentos_switch_off').is_displayed():
                    # self.driver.execute_script("SimpleTogglePanelManager.toggleOnAjax(event,'toggleDocumentos');A4J.AJAX.Submit(null,event,{'similarityGroupingId':'toggleDocumentos','actionUrl':'/pje\x2Dweb/Processo/ConsultaProcesso/Detalhe/listProcessoCompletoAdvogado.seam','parameters':{'toggleDocumentos':'toggleDocumentos','ajaxSingle':'toggleDocumentos'} } )")
                    self.driver.find_element_by_id('toggleDocumentos_switch_off').click()
                    self.wait()

        erro = self.driver.find_element_by_xpath('//*[@id="pageBody"]/div/form/div[1]')
        if erro:
            if erro.text.find('Unhandled or Wrapper Exception') > -1:
                return []

        # CONFERE A QUANTIDADE DE PAGINAS DE DOWNLOAD
        if self.tipo != 2:
            total_pags = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGrid"]/div/div/form/table/tbody/tr[1]/td[3]')
            if not total_pags:
                txt_pags = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGrid"]/div/span')
                if txt_pags and txt_pags.text == '0 resultados encontrados':
                    return []

            total_pags = int(total_pags.text) if total_pags else 1

        i = 1
        while i <= total_pags:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            trs = self.driver.find_elements_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr')
            l = 0
            if not aguarda_presenca_elemento(self.driver, '//*[@id="processoDocumentoGridList:tb"]/tr['+str(l+1)+']/td[1]'):
                # return arquivos
                raise MildException('erro ao abrir página de listagem de arquivos', self.uf, self.plataforma, self.prc_id, False)

            for tr in trs:
                l += 1
                self.driver.execute_script("document.getElementsByClassName('navbar')[0].style.display = 'none';")
                existe = False
                arq = {}
                try:
                    arq['pra_id_tj'] = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr['+str(l)+']/td[1]').text[:29]
                    pra_id_tj = arq['pra_id_tj']
                    pra_id_tj_origem = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr['+str(l)+']/td[2]').text.strip()[:29]
                    if pra_id_tj_origem != '':
                        arq['pra_id_tj'] = pra_id_tj_origem
                except:
                    raise CriticalException("Sessão Encerrada", self.uf, self.plataforma, self.prc_id, False)

                arq['pra_tentativas'] = None

                # print(arq['pra_id_tj'])
                if len(pendentes) > 0:
                    for pen in pendentes[:]:
                        if pen['pra_id_tj'] == pra_id_tj or pen['pra_id_tj'] == pra_id_tj_origem:
                            arq['pra_id'] = pen['pra_id']
                            arq['pra_tentativas'] = pen['pra_tentativas']
                            pendentes.remove(pen)

                if 'pra_id' not in arq:
                    for arb in arquivos_base:
                        if arq['pra_id_tj'] == arb['pra_id_tj'] or pra_id_tj_origem == arb['pra_id_tj']:
                            existe = True
                            break

                    if existe:
                        if len(pendentes) == 0 and len(arquivos_base) > 16:
                            i = total_pags + 1
                            break
                        continue

                arq['pra_prc_id'] = prc_id
                origem = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr[' + str(l) + ']/td[4]').text
                arq['pra_grau'] = 2 if origem.find('2') > -1 else 1
                arq['pra_plt_id'] = self.plataforma

                if self.tipo != 2:
                    limpar_pasta(self.pasta_download)

                pra_data = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr[' + str(l) + ']/td[5]').text
                if pra_data.strip() == '':
                    arq['pra_data'] = None
                    arq['pra_erro'] = True
                    arq['pra_usuario'] = None
                    arq['pra_descricao'] = None
                else:
                    arq['pra_data'] = datetime.strptime(pra_data, '%d/%m/%y %H:%M')
                    arq['pra_usuario'] = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr[' + str(l) + ']/td[6]').text
                    arq['pra_descricao'] = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr[' + str(l) + ']/td[7]').text.strip()
                    td8 = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr[' + str(l) + ']/td[8]').text
                    arq['pra_descricao'] += ' - '+td8 if arq['pra_descricao'] != '' else td8

                linha_atual = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr[' + str(l) + ']')
                dng = linha_atual.find_elements_by_class_name('btn-danger')
                exl = linha_atual.find_elements_by_class_name('fa-external-link')
                src = linha_atual.find_elements_by_class_name('fa-search')
                # print(dng)
                # print(exl)
                # print(src)
                # CONFERE SE O ARQUIVO FOI EXCLUIDO NO PJE
                if len(dng) > 0:
                    # SE FOI EXCLUÍDO, PREENCHE AS RESPECTIVAS VARIÁVEIS
                    arq['pra_excluido'] = True
                    arq['pra_erro'] = False
                    arq['pra_original'] = None
                    arq['pra_arquivo'] = None
                # elif len(exl) > 0 or len(src) > 0:
                elif len(src) > 0:
                    arq['pra_excluido'] = False
                    arq['pra_erro'] = True
                    arq['pra_original'] = None
                    arq['pra_arquivo'] = None
                elif 'pra_erro' in arq:
                    # SE FOI DETECTADO ERRO PREVIAMENTE SOMENTE MARCA COMO NÃO EXCLUÍDO
                    arq['pra_excluido'] = False
                else:
                    arq['pra_excluido'] = False
                    # SE NÃO FOR PARA FAZER DOWNLOAD, SALVA SOMENTE NA BASE, E MARCA COMO ERRO, PARA REALIZAR O DOWNLOAD POSTERIORMENTE
                    if self.tipo == 2:
                        arq['pra_erro'] = True
                    else:
                        # SE NÃO FOI DETECTADO ERRO, BAIXA OS ARQUIVOS
                        href = linha_atual.find_elements_by_xpath('td[9]/span/div/a[1]')
                        if len(href) == 0:
                            href = linha_atual.find_elements_by_xpath('td[11]/span/div/a[1]')

                        href = href[0].get_attribute('href')
                        self.driver.execute_script("window.open('"+href+"', '_blank')")

                        if href.find('visualizarExpediente') > -1:
                            self.alterna_janela(2, 2)
                            erro = self.driver.find_element_by_class_name('alert-danger')
                            if erro:
                                if erro.text.upper().find('Erro inesperado') > -1:
                                    limpar_pasta(self.pasta_download)
                                    limpar_pasta(pasta_intermediaria)
                                    wh = self.driver.window_handles
                                    if len(wh) > 1:
                                        self.driver.close()
                                        self.driver.switch_to.window(wh[1])
                                    raise CriticalException('erro download(Unhandled Exception)' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                            self.driver.switch_to.window(self.driver.current_window_handle)
                            baixar = True
                            if not aguarda_presenca_elemento(self.driver, 'detalhesDocumento:download', tipo='ID'):
                                self.driver.refresh()
                                if not aguarda_presenca_elemento(self.driver, 'detalhesDocumento:download', tipo='ID'):
                                    limpar_pasta(self.pasta_download)
                                    print('erro download (Botão não localizado)')
                                    arq['pra_erro'] = True
                                    baixar = False
                                # raise CriticalException('erro download (Botão não localizado) ' + arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                            if baixar:
                                # self.driver.find_element_by_id('detalhesDocumento:download').click()
                                dwn = self.driver.find_element_by_id('detalhesDocumento:download').get_attribute('onclick')
                                f1 = dwn.find('jsfcljs(')
                                f2 = dwn.rfind('return false')
                                cmd = dwn[f1:f2-2]
                                self.driver.execute_script(cmd)
                                # aguarda_alerta(self.driver)

                                arq['pra_erro'] = False if aguarda_download(self.pasta_download, 1, tempo_nao_iniciado=self.tempo_nao_iniciado_download) else True

                        else:
                            arq['pra_erro'] = False if aguarda_download(self.pasta_download, 1) else True

                        if self.tipo != 2 and arq['pra_erro']:
                            webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

                        wh = self.driver.window_handles
                        if len(wh) > 2:
                            self.driver.switch_to.window(wh[-1])
                            self.driver.close()
                            self.driver.switch_to.window(wh[1])

                # print(arq)
                if not arq['pra_erro'] and not arq['pra_excluido']:
                    total_arquivos += 1
                    file_names = os.listdir(self.pasta_download)
                    arq['pra_original'] = file_names[0]
                    pra_arquivo = trata_arquivo(file_names[0], self.pasta_download, pasta_intermediaria)
                    arq['pra_arquivo'] = pra_arquivo
                elif self.tipo != 2 and arq['pra_erro']:
                    arq['pra_original'] = None
                    arq['pra_arquivo'] = None
                    arq['pra_tentativas'] = 1 if arq['pra_tentativas'] is None else arq['pra_tentativas'] + 1
                    if arq['pra_data'] is not None:
                        limpar_pasta(self.pasta_download)
                        # COMENTAR LINHAS ABAIXO
                        # shutil.rmtree(pasta_intermediaria)
                        print('erro download ', arq)
                        # time.sleep(9999)
                        # raise MildException('erro download '+arq['pra_id_tj'], self.uf, self.plataforma, self.prc_id)

                arq['pra_data_insert'] = datetime.now()
                arquivos.append(arq)

            i += 1
            if i <= total_pags:
                try:
                    self.driver.find_element_by_xpath('//*[@id="processoDocumentoGrid"]/div/div/form/table/tbody/tr[1]/td[5]/input').clear()
                    self.driver.find_element_by_xpath('//*[@id="processoDocumentoGrid"]/div/div/form/table/tbody/tr[1]/td[5]/input').send_keys(str(i))
                except:
                    time.sleep(3)
                    try:
                        self.driver.find_element_by_xpath('//*[@id="processoDocumentoGrid"]/div/div/form/table/tbody/tr[1]/td[5]/input').clear()
                        self.driver.find_element_by_xpath('//*[@id="processoDocumentoGrid"]/div/div/form/table/tbody/tr[1]/td[5]/input').send_keys(str(i))
                    except:
                        raise CriticalException('Erro ao alternar página de listagem de arquivos', self.uf, self.plataforma, self.prc_id, False)
                time.sleep(0.2)
                # self.driver.find_element_by_xpath('//*[@id="processoDocumentoGrid"]/div/div/form/table/tbody/tr[1]/td[4]').click()
                self.wait(60)
                aguarda_presenca_elemento(self.driver, '//*[@id="processoDocumentoGridList:tb"]/tr[1]')

        # print(arquivos)
        arquivos.reverse()
        return arquivos

    # IDENTIFICA O ID DA DIV DAS MOVIMENTAÇÕES
    def get_div(self):
        if self.div is not None:
            return
        if self.driver.find_element_by_class_name('alert-danger'):
            if self.driver.find_element_by_xpath('//*[@id="pageBody"]/div').text.find('Unhandled') > -1:
                raise CriticalException("Erro ao buscar processo (Unhandled Exception)", self.uf, self.plataforma, self.prc_id)

        if self.driver.find_element_by_xpath('//*[@id="divTimeLine:divEventosTimeLine"]/div[3]'):
            self.div = 'divEventosTimeLine'
        elif self.driver.find_element_by_xpath('//*[@id="divTimeLine:eventosTimeLineElement"]/div[2]'):
            self.div = 'eventosTimeLineElement'
        else:
            raise MildException("Erro ao abrir processo (detecção da div)", self.uf, self.plataforma, self.prc_id)

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

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def confere_arquivos_novos(self, arquivos_base):
        self.driver.execute_script("A4J.AJAX.Submit('navbar',event,{'similarityGroupingId':'navbar:linkAbaDocumentos','parameters':{'navbar:linkAbaDocumentos':'navbar:linkAbaDocumentos'} } );")
        self.wait(60)
        aguarda_presenca_elemento(self.driver, '//*[@id="processoDocumentoGridList:tb"]/tr[1]')
        if self.driver.find_element_by_id('toggleDocumentos_switch_off'):
            if self.driver.find_element_by_id('toggleDocumentos_switch_off').is_displayed():
                # self.driver.execute_script("SimpleTogglePanelManager.toggleOnAjax(event,'toggleDocumentos');A4J.AJAX.Submit(null,event,{'similarityGroupingId':'toggleDocumentos','actionUrl':'/pje\x2Dweb/Processo/ConsultaProcesso/Detalhe/listProcessoCompletoAdvogado.seam','parameters':{'toggleDocumentos':'toggleDocumentos','ajaxSingle':'toggleDocumentos'} } )")
                self.driver.find_element_by_id('toggleDocumentos_switch_off').click()
                self.wait()

        erro = self.driver.find_element_by_xpath('//*[@id="pageBody"]/div/form/div[1]')
        if erro:
            if erro.text.find('Unhandled or Wrapper Exception') > -1:
                return True

        # CONFERE A QUANTIDADE DE PAGINAS DE DOWNLOAD
        if self.tipo != 2:
            total_pags = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGrid"]/div/div/form/table/tbody/tr[1]/td[3]')
            if not total_pags:
                txt_pags = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGrid"]/div/span')
                if txt_pags and txt_pags.text == '0 resultados encontrados':
                    return False

            total_pags = int(total_pags.text) if total_pags else 1

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        trs = self.driver.find_elements_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr')
        if not aguarda_presenca_elemento(self.driver, '//*[@id="processoDocumentoGridList:tb"]/tr[1]/td[1]'):
            return True

        self.driver.execute_script("document.getElementsByClassName('navbar')[0].style.display = 'none';")

        try:
            pra_id_tj = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr[1]/td[1]').text
            pra_id_tj_origem = self.driver.find_element_by_xpath('//*[@id="processoDocumentoGridList:tb"]/tr[1]/td[2]').text.strip()
        except:
            return True

        for arb in arquivos_base:
            if pra_id_tj == arb['pra_id_tj'] or pra_id_tj_origem == arb['pra_id_tj']:
                self.driver.execute_script("A4J.AJAX.Submit('navbar',event,{'similarityGroupingId':'navbar:linkAbaAutosHome','parameters':{'navbar:linkAbaAutosHome':'navbar:linkAbaAutosHome'} } );")
                self.wait(60)
                return False

        return True