from Controllers.Tribunais.Fisico._fisico import *

# CLASSE DA VARREDURA DO PJE DO CE. HERDA OS METODOS DA CLASSE PJE
class Fisico_TRF03(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "http://web.trf3.jus.br/consultas/Internet/ConsultaProcessual"
        self.pagina_busca = "http://web.trf3.jus.br/consultas/Internet/ConsultaProcessual"

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        self.driver.find_element_by_id('NumeroProcesso').clear()
        self.driver.find_element_by_id('NumeroProcesso').send_keys(numero_busca)
        self.driver.find_element_by_id('NumeroProcesso').send_keys(Keys.ENTER)

        msg_erro = self.driver.find_element_by_id('mensagemErro')
        if msg_erro and msg_erro.text.find('Não foi possível encontrar') > -1:
            return False

        msg_erro = self.driver.find_element_by_xpath('/html/body/span/h2/i')
        if msg_erro and msg_erro.text.find('não é um número de processo válido') > -1:
            return False

        # if msg_erro:
        #     if msg_erro.text.find('O processo é inexistente') > -1:
        #         return False

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def confere_arquivos_novos(self, arquivos_base):
        return False