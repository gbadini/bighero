from Controllers.Tribunais.Fisico._fisico import *

# CLASSE DA VARREDURA DO PJE DO CE. HERDA OS METODOS DA CLASSE PJE
class Fisico_TRF01(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://processual.trf1.jus.br/consultaProcessual/numeroProcesso.php?secao=TRF1"
        self.pagina_busca = "https://processual.trf1.jus.br/consultaProcessual/numeroProcesso.php?secao=TRF1"

    # DEFINE A ORDEM QUE OS DADOS SÃO CAPTURADOS
    def ordem_captura(self, proc):
        status_atual = 'Ativo' if self.completo else proc['prc_status']
        adc = self.audiencias()
        prc = self.dados(status_atual)
        prt = self.partes()
        adv = self.responsaveis()

        return adc, prt, prc, adv

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        self.driver.find_element_by_id('proc').clear()
        self.driver.find_element_by_id('proc').send_keys(numero_busca)
        self.driver.find_element_by_id('proc').send_keys(Keys.ENTER)

        msg_erro = self.driver.find_element_by_xpath('//*[@id="content"]/div[3]/div[1]')
        if msg_erro.text.find('Processo não foi encontrado') > -1:
            return False

        # if msg_erro:
        #     if msg_erro.text.find('O processo é inexistente') > -1:
        #         return False

        return True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def confere_arquivos_novos(self, arquivos_base):
        return False