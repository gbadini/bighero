from Controllers.Tribunais.Projudi._projudi_v2 import *
from Config.helpers import *


# CLASSE DA VARREDURA DO PROJUDI DO MT. HERDA OS METODOS DA CLASSE PROJUDI
class MT(ProjudiV2):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://projudi.tjmt.jus.br/"
        self.pagina_busca = "https://projudi.tjmt.jus.br/projudi/buscas/ProcessosQualquerAdvogado"
        self.pagina_processo = "https://projudi.tjmt.jus.br/projudi/listagens/DadosProcesso?numeroProcesso="
        self.tabela_movs = '//*[@id="movimentos"]/table/tbody/tr/td/table/tbody/tr'
        self.intervalo = 8
        self.remover_primeira_tr = False

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''

        data_ultima_mov = self.driver.find_element_by_xpath('//*[@id="conteudiMov"]/table[3]/tbody/tr/td[5]').text
        data_ultima_mov = strip_html_tags(data_ultima_mov)

        data_tj = datetime.strptime(data_ultima_mov, self.formato_data)
        if ultima_data == data_tj:
            return True

        return False

    # REALIZA LOGIN NA PLATAFORMA
    def login(self, usuario=None, senha=None):
        '''
        :param str usuario: usuario de acesso
        :param str senha: senha de acesso
        '''
        if not aguarda_presenca_elemento(self.driver, 'login', tipo='ID'):
            return False

        if usuario is None:
            raise CriticalException("Usuário não consigurado", self.uf, self.plataforma, self.prc_id)
        else:
            self.driver.find_element_by_id("login").send_keys(usuario)
            self.driver.find_element_by_id("senha").send_keys(senha)
            self.driver.find_element_by_id("senha").send_keys(Keys.ENTER)


        if not aguarda_presenca_elemento(self.driver, 'contador-sessao', tipo='ID'):
            return False

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        if not aguarda_presenca_elemento(self.driver, 'numeroProcesso', tipo='ID'):
            raise CriticalException("Campo de busca não localizado", self.uf, self.plataforma, self.prc_id, False)


        numero_tj = 'XXX'
        inicio = time.time()
        while numero_busca != numero_tj:
            if time.time() - inicio > 6:
                    if numero_busca[0] == '8':
                        self.driver.find_element_by_id('numeroProcesso').clear()
                        self.driver.find_element_by_id('numeroProcesso').send_keys(numero_busca[1:])
                        break
                    else:
                        raise MildException("Erro ao imputar CNJ no campo", self.uf, self.plataforma, self.prc_id)

            self.driver.find_element_by_id('numeroProcesso').clear()
            for c in numero_busca:
                self.driver.find_element_by_id('numeroProcesso').send_keys(c)

            numero_tj = self.driver.find_element_by_id('numeroProcesso').get_attribute('value')
            numero_tj = ajusta_numero(numero_tj)

        self.driver.find_element_by_id("numeroProcesso").send_keys(Keys.ENTER)

        inicio = time.time()
        while True:
            if time.time() - inicio > 10:
                # print('Timeout Busca')
                # time.sleep(999)
                raise CriticalException("Timeout Busca", self.uf, self.plataforma, self.prc_id, False)

            erro_busca = self.driver.find_element_by_xpath('//*[@id="corpo"]/view-content/content-body/view/div[2]/form[2]/table/tbody/tr[4]/td')
            if erro_busca:
                if erro_busca.text.find('Nenhum registro') > -1:
                    return False

            if self.driver.find_element_by_xpath('//*[@id="corpo"]/view-content/content-body/view/div[2]/form[2]/table/tbody/tr[4]/td[2]/a'):
                break

            if self.driver.find_element_by_xpath('//*[@id="Partes"]/table[3]/tbody/tr[1]/td'):
                break

            # CONFERE SE FOI SOLICITADO CAPTCHA
            if self.driver.find_element_by_xpath('//*[@id="idAvisos"]/div/ul/li/span'):
                if self.driver.find_element_by_xpath('//*[@id="idAvisos"]/div/ul/li/span').text.find('Captcha incorreto') > -1:
                    v = self.driver.find_element_by_id('numeroProcesso').get_attribute('value')
                    v = v.strip()
                    while v == '':
                        if time.time() - inicio > 120:
                            raise CriticalException("Captcha Detectado", self.uf, self.plataforma, self.prc_id, False)
                        v = self.driver.find_element_by_id('numeroProcesso').get_attribute('value')
                        v = v.strip()
                    inicio = time.time()

                self.driver.find_element_by_id('numeroProcesso').clear()
                self.driver.find_element_by_id('numeroProcesso').send_keys(numero_busca)
                self.driver.find_element_by_id("numeroProcesso").send_keys(Keys.ENTER)



        return True

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        if not try_click(self.driver, '//*[@id="corpo"]/view-content/content-body/view/div[2]/form[2]/table/tbody/tr[4]/td[2]/a'):
            time.sleep(1)
            try_click(self.driver, '//*[@id="corpo"]/view-content/content-body/view/div[2]/form[2]/table/tbody/tr[4]/td[2]/a')

        if not aguarda_presenca_elemento(self.driver, '//*[@id="Partes"]/table[3]/tbody/tr[1]/td'):
            raise MildException("Erro ao carregar processo", self.uf, self.plataforma, self.prc_id, True)

        # IMPLEMENTAR CONFERENCIA DE SEGREDO

        self.confere_cnj(numero_busca)
        return False

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        cnj = self.driver.find_element_by_xpath('//*[@id="Partes"]/table[3]/tbody/tr[1]/td')
        cnj = localiza_cnj(cnj.text)
        cnj_limpo = ajusta_numero(cnj)

        if numero_busca == cnj_limpo or numero_busca == '8'+cnj_limpo[1:]:
            return True

    # MÉTODO PARA REALIZAR O DOWNLOAD DE ARQUIVOS
    def download(self, prc_id, arquivos_base, pendentes, pasta_intermediaria):
        return []