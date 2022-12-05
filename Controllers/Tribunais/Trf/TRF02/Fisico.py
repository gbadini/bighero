from Controllers.Tribunais.Fisico._fisico import *

# CLASSE DA VARREDURA DO PJE DO CE. HERDA OS METODOS DA CLASSE PJE
class Fisico_TRF02(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://balcaojus.trf2.jus.br/balcaojus/#/consultar"
        self.pagina_busca = "https://balcaojus.trf2.jus.br/balcaojus/#/consultar"

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        self.driver.find_element_by_id('numero').clear()
        self.driver.find_element_by_id('numero').send_keys(numero_busca)
        self.driver.find_element_by_id('numero').send_keys(Keys.ENTER)

        msg_erro = self.driver.find_element_by_xpath('//*[@id="app"]/div[5]/div[2]/form/div[1]/div')
        if msg_erro.text.find('não encontrado') > -1:
            return False

        if msg_erro.text.find('Nenhum processo encontrado') > -1:
            return False
        # if msg_erro:
        #     if msg_erro.text.find('O processo é inexistente') > -1:
        #         return False

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def confere_arquivos_novos(self, arquivos_base):
        return False