from Controllers.Tribunais.segundo_grau import *
import win32gui
import win32con
import win32api
import win32com.client

# CLASSE DA VARREDURA DO JPE DE MG DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PPE2g
class MG2g(SegundoGrau):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://pe.tjmg.jus.br/rupe/portaljus/intranet/principal.rupe"
        self.pagina_busca = 'https://pe.tjmg.jus.br/rupe/portaljus/intranet/processo/processos.rupe?acao=2&localizacaoAtual=681'

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        if not aguarda_presenca_elemento(self.driver, 'login', tipo='ID'):
            return False

        self.driver.execute_script("exibirDadosLoginCertDigital();")
        aguarda_presenca_elemento(self.driver, 'entrarCertificadoLocal', tipo='ID', aguarda_visibilidade=True)
        self.driver.find_element_by_id("entrarCertificadoLocal").click()

        ttv = 0
        while not self.confirma_pje_office():
            ttv += 1
            if ttv > 5:
                raise Exception('Erro ao realizar login')

            time.sleep(1)
            if self.driver.find_element_by_id('/html/body/nav'):
                break

            try:
                btn = self.driver.find_element_by_id('entrarCertificadoLocal')
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

        if not aguarda_presenca_elemento(self.driver, 'barraMenu', tipo='ID'):
            return False

        try_click(self.driver, 'imgFecharPopuppopupMensagemPlantao', tipo='ID')

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''

        id = 'formFiltrosfiltrosProcessos:origem' if self.buscar_origem else 'formFiltrosfiltrosProcessos:processo'

        self.driver.find_element_by_id(id).clear()
        self.driver.find_element_by_id(id).send_keys(numero_busca)
        self.driver.find_element_by_id(id).send_keys(Keys.ENTER)
        self.wait()

        trs = self.driver.find_element_by_xpath('//*[@id="formTabelaProcessos:dataTabletabelaProcessos:tb"]/tr')
        if len(trs) == 0:
            return False

        return True

    # CONFERE SE OS RECURSOS ESTÃO NA BASE CASO EXISTA MAIS DE UM
    def confere_recursos(self, base, proc):
        recs = self.driver.find_element_by_xpath('//*[@id="formTabelaProcessos:dataTabletabelaProcessos:tb"]/tr')

        if len(recs) == 1 and proc['rec_codigo'] is not None:
            return True

        if proc['rec_id'] is not None and proc['rec_codigo'] is None:
            td2 = recs[0].find_element_by_xpath('td[2]')
            id = td2.get_attribute('id')
            f_id = id.split(':')
            Recurso.update_simples(base, proc['rec_id'], {'rec_codigo': f_id[2],})
            return False

        if len(recs) == 1 and proc['rec_codigo'] is not None:
            return True

        if len(recs) > 1:
            recs.pop(0)

        achei = True
        for rec in recs:
            td2 = rec.find_element_by_xpath('td[2]')
            id = td2.get_attribute('id')
            f_id = id.split(':')
            result = Recurso.select(base, proc['prc_id'], f_id[2])
            if len(result) == 0:
                achei = False
                Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_codigo': f_id[2], 'rec_numero': td2.text.strip(),'rec_plt_id':self.plataforma})

        return achei


    # AGUARDA ATÉ QUE A ANIMAÇÃO DE LOADING ESTEJA OCULTA
    def wait(self, tempo=30, id='panelStatusContainer'):
        # time.sleep(0.2)
        if self.driver.find_element_by_id(id):
            wait = WebDriverWait(self.driver, tempo)
            try:
                wait.until(EC.invisibility_of_element((By.ID, id)))
            except TimeoutException:
                raise MildException("Loading Timeout", self.uf, self.plataforma, self.prc_id, False)

        return True

    # CONFIRMA DIALOG DO PJEOFFICE
    def confirma_pje_office(self):
        time.sleep(1)
        inicio = time.time()
        while True:
            time.sleep(1)
            print('Procurando Janela de Confirmação do PJE')

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

                    lParam = win32api.MAKELONG(math.ceil(r*0.6683), math.ceil(b*0.958))

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

            if (time.time() - inicio) >= 40:
                raise Exception('PJE Office não localizado')