from Controllers.Tribunais.Projudi._projudi_v2 import *


# CLASSE DA VARREDURA DO PROJUDI DO MA. HERDA OS METODOS DA CLASSE PROJUDIV2
class MA(ProjudiV2):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://projudi.tjma.jus.br/projudi/"
        self.pagina_busca = "https://projudi.tjma.jus.br/projudi/buscas/ProcessosQualquerAdvogado"
        self.pagina_processo = "https://projudi.tjma.jus.br/projudi/listagens/DadosProcesso?numeroProcesso="
        self.xpath_menu = '//*[@id="topo"]/table/tbody/tr[2]/td/ul'
        self.intervalo = 5

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self, ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''

        data_ultima_mov = self.driver.find_element_by_xpath('//*[@id="Arquivos"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td[' + str(self.posicao_elementos['data']) + ']').text
        data_cad = strip_html_tags(data_ultima_mov)
        data_cad = datetime.strptime(data_cad, '%d/%m/%Y %H:%M')

        acp_esp = self.driver.find_element_by_xpath('//*[@id="Arquivos"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td[' + str(self.posicao_elementos['esp']) + ']').text
        acp_esp = strip_html_tags(acp_esp)

        return Acompanhamento.compara_mov(base, prc_id, acp_esp, data_cad, self.plataforma, self.grau, rec_id=self.rec_id)