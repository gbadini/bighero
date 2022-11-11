from Controllers.Clientes._cliente import *
from selenium.webdriver.support.ui import Select

# CLASSE PRINCIPAL DO SISTEMA PROCESSUM. HERDA OS METODOS DA CLASSE CLIENTE
class Espaider(Cliente):

    def __init__(self):
        super().__init__()
        self.plataforma = 11
        self.pagina_inicial = "https://espaider.neoenergia.com/login/main2.aspx"
        self.pagina_busca = "https://espaider.neoenergia.com/default.aspx?p0=29"
        self.movs = []
        self.campo_busca = 'prc_numero_processum'
        self.ordem_usuario = 0

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None, base=None):
        '''
               :param str usuario: usuario de acesso
               :param str senha: senha de acesso
               '''
        if not aguarda_presenca_elemento(self.driver, 'userFieldEdt', tipo='ID'):
            return False

        self.driver.find_element_by_id("userFieldEdt").send_keys(usuario)
        self.driver.find_element_by_id("passFieldEdt").send_keys(senha)
        self.driver.find_element_by_id("passFieldEdt").send_keys(Keys.ENTER)

        inicio = time.time()
        while True:
            tempoTotal = time.time() - inicio
            if tempoTotal >= 30:
                return False

            if self.driver.find_element_by_id('q-comp-32'):
                self.driver.find_element_by_id('q-comp-32').click()
                time.sleep(1)
            # try_click(self.driver, '/html/body/div[2]/div/div[2]/div[2]/div/div')

            if self.driver.find_element_by_xpath('//*[@id="modProcessos"]/em/button'):
                if self.driver.find_element_by_xpath('//*[@id="modProcessos"]/em/button').is_displayed():
                    return True

        # if aguarda_presenca_elemento(self.driver, '//*[@id="modProcessos"]/em/button', aguarda_visibilidade=True):
        #     return True

        # return False

    # MÉTODO PARA A BUSCA DO PROCESSO NO CLIENTE
    def busca_processo(self, numero_busca):
        # VERIFICA SE A PAGINA FOI CARREGADA
        aguarda_presenca_elemento(self.driver, 'rightCt', tipo='ID')

        try_click(self.driver, '//*[@id="WARSAW_ALERT"]/div/em/button')

        # ACESSA O IFRAME DA LISTA E BUSCA DE PROCESSOS
        xpath_buscaProcessos = '/html/body/form/div[1]/div[2]/div[2]/iframe'
        aguarda_presenca_elemento(self.driver, '/html/body/form/div[1]/div[2]/div[2]/iframe')

        iframe_buscaProcesso = self.driver.find_element_by_xpath(xpath_buscaProcessos)
        self.driver.switch_to_frame(iframe_buscaProcesso)

        # INSERE PONTOS E TRAÇOS CASO NECESSARIO
        numero_busca_original = numero_busca
        numero_busca = self.insere_pontos_tracos_numero_processo(numero_busca)

        # BUSCA NA BASE COM TODOS OS FORMATOS POSSÍVEIS
        # NUMERO DO JEITO QUE VEIO DA BASE
        self.insere_processo(numero_busca_original)
        if self.valida_busca(numero_busca):
            self.abre_processo()
            return True

        if numero_busca_original != numero_busca:
            # NUMERO FORMATADO
            self.insere_processo(numero_busca)
            if self.valida_busca(numero_busca):
                self.abre_processo()
                return True

        # NUMERO COM A REMOÇÃO DE UM PONTO EM ESPECIFICO
        numero_processo_aux = self.remove_ponto_especifico(numero_busca)
        self.insere_processo(numero_processo_aux)
        if self.valida_busca(numero_busca):
            self.abre_processo()
            return True

        # NUMERO SEM PONTOS E TRAÇOS
        numero_processo_aux = self.remove_ponto_tracos(numero_busca)
        self.insere_processo(numero_processo_aux)
        if self.valida_busca(numero_busca):
            self.abre_processo()
            return True

        return False

    def passa_para_o_frame_por_id(navegador, id, tempo):
        aguarda_presenca_elemento(navegador, id, tempo, tipo='ID')
        iframe = navegador.find_element_by_id(id)

        navegador.switch_to_frame(iframe)

    def wait_load(self, tempo=30, latencia=0.2):
        # time.sleep(1)
        inicio = time.time()
        f = False
        while not f:
            divs = self.driver.find_elements_by_class_name('x-hide-offsets')

            displayed = True
            for div in divs:
                displayed = False
                if div.is_displayed():
                    displayed = True
                    break

            if not displayed:
                break

            f = len(divs) > 1
            time.sleep(latencia)
            tempoTotal = time.time() - inicio
            if tempoTotal >= tempo:
                return False

        return True

    def insere_pontos_tracos_numero_processo(self, numero_processo):
        try:
            # exemplo saída: 0000000-00.0000.0.00.0000
            if "." in numero_processo and "-" in numero_processo:
                return numero_processo

            numero_processo = ajusta_numero(numero_processo)
            numero_final = numero_processo[0:7] + "-" + numero_processo[7:9] + "." + numero_processo[9:13]
            numero_final += "." + numero_processo[13] + "." + numero_processo[14:16] + "." + numero_processo[16:20]
            print("ANTES: ", numero_processo)
            print("FINAL: ", numero_final)
            return numero_final
        except:
            return numero_processo

    def insere_processo(self, numero_busca):
        xpath_campoBusca = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[1]/div/div/div[5]/div/div[2]/input'
        aguarda_presenca_elemento(self.driver, xpath_campoBusca)

        caixa_filtro = self.driver.find_element_by_xpath(xpath_campoBusca)

        caixa_filtro.clear()
        caixa_filtro.send_keys(numero_busca)
        caixa_filtro.send_keys(Keys.RETURN)

    def remove_ponto_especifico(self, numero_busca):
        # 8001770-83.2020.8.05.0127
        return numero_busca[:17] + numero_busca[18:]

    def remove_ponto_tracos(self, numero_processo):
        numero_processo = numero_processo.replace('.', '')
        numero_processo = numero_processo.replace('-', '')
        return numero_processo

    def valida_busca(self, busca_processo):
        if not self.wait_load(60):
            raise MildException("Timeout na busca", self.uf, self.plataforma, self.prc_id)
        # vall = True
        # while vall:
        #     if len(self.driver.find_elements_by_class_name('x-hide-offsets')) == 2:
        #         vall = False
        aguarda_presenca_elemento(self.driver, '//*[@id="q-comp-125"]/table/tbody/tr', tempo=4)

        valida = self.driver.find_elements_by_xpath('//*[@id="q-comp-125"]/table/tbody/tr')
        if len(valida) > 0:
            num_process = self.driver.find_element_by_xpath('//*[@id="q-comp-125"]/table/tbody/tr[2]/td[3]/div').text
            num_process = ajusta_numero(num_process)
            busca_processo = ajusta_numero(busca_processo)
            if busca_processo == num_process:
                return True

        return False

    def abre_processo(self):
        self.driver.switch_to.default_content()
        # ACESSA O IFRAME DA LISTA E BUSCA DE PROCESSOS
        aguarda_presenca_elemento(self.driver, '/html/body/form/div[1]/div[2]/div[2]/iframe')
        iframe_buscaProcesso = self.driver.find_element_by_xpath('/html/body/form/div[1]/div[2]/div[2]/iframe')
        self.driver.switch_to_frame(iframe_buscaProcesso)

        # ABRE O PROCESSO
        xpath_process = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[2]/td[3]/div'
        aguarda_presenca_elemento(self.driver, xpath_process)
        self.driver.find_element_by_xpath(xpath_process).click()

    # CAPTURA O STATUS ATUAL DO PROCESSO
    def captura_status(self):
        situacao = self.driver.find_element_by_xpath('//*[@id="q-comp-125"]/table/tbody/tr[2]/td[8]/div').text
        return situacao

    def detecta_iframe(self):
        inicio = time.time()
        while True:
            tempoTotal = time.time() - inicio
            if tempoTotal >= 30:
                raise MildException("iframe não localizado", self.uf, self.plataforma, self.prc_id)

            iframe_processo = self.driver.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/iframe')
            if iframe_processo:
                return iframe_processo

            iframe_processo = self.driver.find_element_by_xpath('/html/body/div[3]/div/div[2]/div/iframe')
            if iframe_processo:
                return iframe_processo