from Controllers.Tribunais.Projudi._projudi_v2 import *


# CLASSE DA VARREDURA DO PROJUDI DO PA. HERDA OS METODOS DA CLASSE PROJUDIV2
class PA(ProjudiV2):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "https://projudi.tjpa.jus.br/projudi/PaginaPrincipal.jsp"
        self.pagina_busca = "https://projudi.tjpa.jus.br/projudi/buscas/ProcessosQualquerAdvogado"
        self.pagina_processo = "https://projudi.tjpa.jus.br/projudi/listagens/DadosProcesso?numeroProcesso="
        self.posicao_elementos = {'tipo': 2, 'esp': 3, 'data': 4, 'usr': 5}
        self.limpar_com_backspace = True

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        if not aguarda_presenca_elemento(self.driver, 'numeroProcesso', tipo='ID'):
            raise CriticalException("Campo de busca não localizado", self.uf, self.plataforma, self.prc_id, False)

        inicio = time.time()
        captchaimg = self.driver.find_element_by_id('captchaimg')
        if captchaimg:
            v = self.driver.find_element_by_xpath('//*[@id="corpo"]/form/table/tbody/tr[2]/td[2]/input').get_attribute('value').strip()
            while len(v) < 5:
                if time.time() - inicio > 60:
                    raise CriticalException("Captcha Detectado", self.uf, self.plataforma, self.prc_id, False)
                v = self.driver.find_element_by_xpath('//*[@id="corpo"]/form/table/tbody/tr[2]/td[2]/input').get_attribute('value').strip()
                time.sleep(1)

        self.driver.find_element_by_id('numeroProcesso').clear()
        if self.limpar_com_backspace:
            for r in range(0,20):
                self.driver.find_element_by_id("numeroProcesso").send_keys(Keys.BACKSPACE)

        self.driver.find_element_by_id('numeroProcesso').send_keys(numero_busca)

        id_nome_parte_input = self.driver.find_element_by_id('id_nome_parte')
        if id_nome_parte_input:
            id_nome_parte_input.click()
            id_nome_parte = self.driver.find_element_by_id('id_nome_parte').get_attribute('value')

            if id_nome_parte.strip() != '':
                return False

        self.driver.find_element_by_id("numeroProcesso").send_keys(Keys.ENTER)
        listagem = localiza_elementos(self.driver, ('/html/body/div[1]/form[2]/table/tbody/tr[4]/td[2]/a', '/html/body/div[3]/div/div[1]/form[2]/table/tbody/tr[4]/td[2]/a', '/html/body/div[1]/form[2]/table/tbody/tr[2]/td[1]/a','//*[@id="corpo"]/div[1]/form[2]/table/tbody/tr[4]/td[2]/a'))
        if listagem:
            numero_site = localiza_cnj(listagem.text, regex="(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\-)(\\d+)")
            numero_site = ajusta_numero(numero_site)
            if numero_busca != numero_site:
                return False
            listagem.click()
            aguarda_alerta(self.driver, 0.1)
            return True

        numero_busca = numero_busca.strip('0')
        if len(numero_busca) < 15:
            self.driver.get(self.pagina_busca)
            for r in range(0,20):
                self.driver.find_element_by_id("numeroProcesso").send_keys(Keys.BACKSPACE)
            self.driver.execute_script("mostrarEsconderBuscaNumeracaoCNJ('divRecuperarNumeracaoCNJ','numeroProcessoAntigo')")
            time.sleep(1)
            for n in numero_busca:
                self.driver.find_element_by_id('divRecuperarNumeracaoCNJ').send_keys(n)
            self.driver.find_element_by_id('divRecuperarNumeracaoCNJ').send_keys(numero_busca)
            self.driver.find_element_by_id('divRecuperarNumeracaoCNJ').send_keys(Keys.TAB)
            self.driver.execute_script("recuperarNumeracaoCNJ('numeroProcessoAntigo', 'numeroProcesso', 'divRecuperarNumeracaoCNJ')")
            if aguarda_alerta(self.driver):
                return False

            self.driver.find_element_by_id("numeroProcesso").send_keys(Keys.ENTER)
            listagem = localiza_elementos(self.driver, ('/html/body/div[1]/form[2]/table/tbody/tr[4]/td[2]/a', '/html/body/div[3]/div/div[1]/form[2]/table/tbody/tr[4]/td[2]/a', '/html/body/div[1]/form[2]/table/tbody/tr[2]/td[1]/a', '//*[@id="corpo"]/div[1]/form[2]/table/tbody/tr[4]/td[2]/a'))
            if listagem:
                cnj = self.driver.find_element_by_xpath('/html/body/div[1]/form[2]/table/tbody/tr[4]/td[3]').text
                cnj_limpo = ajusta_numero(cnj).strip('0')
                if cnj_limpo != numero_busca:
                    return False
                listagem.click()
                aguarda_alerta(self.driver, 0.1)
                return True

        return False

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        cnjs = self.driver.find_elements_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td')
        for cnj_txt in cnjs:
            cnj = cnj_txt.text

            cnj = localiza_cnj(cnj, "(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)|(\\d+)(.)([0-9]{4})(\\.)(\\d+)(\\.)(\\d+)(\\-)(\\d+)")
            if not cnj:
                continue
            cnj_limpo = ajusta_numero(cnj)
            if cnj_limpo == numero_busca:
                return True

            cnj = self.driver.find_element_by_xpath('//*[@id="Partes"]/table/tbody/tr[1]/td/font')
            if cnj:
                cnj = cnj.text
                f = cnj.find(':')
                cnj = cnj[f+1:]
                cnj_limpo = ajusta_numero(cnj)
                if cnj_limpo == numero_busca:
                    return True

        # print("Número CNJ Diferente")
        # time.sleep(9999)
        raise MildException("Número CNJ Diferente", self.uf, self.plataforma, self.prc_id)
