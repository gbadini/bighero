from Controllers.Clientes._cliente import *
from selenium.webdriver.support.ui import Select

# CLASSE PRINCIPAL DO SISTEMA PROCESSUM. HERDA OS METODOS DA CLASSE CLIENTE
class Espaider(Cliente):

    def __init__(self):
        super().__init__()
        self.plataforma = 11
        self.pagina_inicial = "https://espaider.neoenergia.com/login/main2.aspx"
        self.pagina_busca = ""
        self.movs = []
        self.campo_busca = 'prc_numero'
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

        if aguarda_presenca_elemento(self.driver, '//*[@id="modProcessos"]/em/button', aguarda_visibilidade=True):
            return True

        return False

    # MÉTODO PARA A BUSCA DO PROCESSO NO CLIENTE
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        return True

    def wait_load(self, tempo=30, latencia=0.2):
        time.sleep(1)
        inicio = time.time()
        f = False
        while not f:
            f = len(self.driver.find_elements_by_class_name('x-hide-offsets')) > 1
            time.sleep(latencia)
            tempoTotal = time.time() - inicio
            if tempoTotal >= tempo:
                return False