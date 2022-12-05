from Controllers.Tribunais.Fisico._fisico import *

# CLASSE DA VARREDURA DO FISICO DO DF. HERDA OS METODOS DA CLASSE FISICO
class Fisico_TRF05(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.pagina_busca = "http://portal.trf5.jus.br/cp/"

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
        self.driver.find_element_by_id('filtro').clear()
        self.driver.find_element_by_id('filtro').send_keys(numero_busca)
        self.driver.find_element_by_id('filtro').send_keys(Keys.ENTER)

        self.alterna_janela()
        msg_erro = self.driver.find_element_by_xpath('//*[@id="wrapper"]/table/tbody/tr/td/table[2]/tbody/tr[1]')
        if msg_erro.text.find('O processo é inexistente') > -1:
            return False

        # if msg_erro:
        #     if msg_erro.text.find('O processo é inexistente') > -1:
        #         return False

        return True

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

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def confere_arquivos_novos(self, arquivos_base):
        return False