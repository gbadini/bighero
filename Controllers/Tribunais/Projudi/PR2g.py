from Controllers.Tribunais.Projudi._projudi2g import *
from pyotp import *

# CLASSE DA VARREDURA DO PJE DE RO DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE PJE
class PR2g(Projudi2g):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://projudi.tjpr.jus.br/projudi/usuario/logon.do?actionType=inicio"
        self.pagina_busca = "https://projudi.tjpr.jus.br/projudi/processo/buscaProcessosQualquerInstancia.do?actionType=iniciar"
        self.diferenciar_id_download_2g = True
        self.kill_nao_localizado = True

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None, token=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        aguarda_presenca_elemento(self.driver, '//*[@id="mainPage"]/div[1]/div[2]/div[1]/div[1]/ul/li[2]')
        self.driver.find_element_by_xpath('//*[@id="mainPage"]/div[1]/div[2]/div[1]/div[1]/ul/li[2]').click()
        aguarda_presenca_elemento(self.driver, 'username', tipo='ID')
        self.driver.find_element_by_id("username").send_keys(usuario)
        self.driver.find_element_by_id("password").send_keys(senha)
        self.driver.find_element_by_id("password").send_keys(Keys.ENTER)

        while self.driver.find_element_by_xpath('//*[@id="mainPage"]/div/div[2]/iframe'):
            time.sleep(5)

        print(token)
        totp = TOTP(token)
        tk = totp.now()
        # print(token)
        self.driver.find_element_by_id('totp').send_keys(tk)
        try:
            self.driver.find_element_by_id('totp').send_keys(Keys.ENTER)
        except:
            pass
        time.sleep(1)

        if not aguarda_presenca_elemento(self.driver, 'BarraMenu', tipo='ID', tempo=900):
            return False

        self.driver.find_element_by_xpath('//*[@id="main-menu"]/li[8]/a').click()
        aguarda_presenca_elemento(self.driver, '//*[@id="main-menu"]/li[8]/ul/li[2]/a')
        self.driver.find_element_by_xpath('//*[@id="main-menu"]/li[8]/ul/li[2]/a').click()
        url = self.driver.find_element_by_partial_link_text('Processos 2º Grau').get_attribute('href')
        self.pagina_busca = url

        return True