from Controllers.Tribunais.Fisico.PE import *
from Controllers.Tribunais.segundo_grau import *

# CLASSE DA VARREDURA DO FISICO DE PE DE SEGUNDO GRAU. HERDA OS METODOS DA CLASSE ESAJ2g
class PE2g(SegundoGrau, PE):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.pagina_busca = "https://srv01.tjpe.jus.br/consultaprocessualunificada/processo/"
        # self.pagina_processo = "https://srv01.tjpe.jus.br/consultaprocessualunificada/processo/"
        self.formato_data = '%d/%m/%Y %H:%M'
        # self.reiniciar_navegador = False
        self.titulo_partes['ativo'] += ('PROCURADORIA DE JUSTIÇA',)
        self.titulo_partes['passivo'] += ('REPRESENTANTE',)

    # CONFERE SE OS RECURSOS ESTÃO NA BASE CASO EXISTA MAIS DE UM
    def confere_recursos(self, base, proc):
        uls = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")

        if len(uls) == 1:
            return True

        achei = True
        if len(uls) > 1:
            achei1g = False
            for ul in uls:
                if ul.find_element_by_class_name('panel-heading').text.upper().find('1º GRAU - FÍSICO') > -1:
                    achei1g = True
                    break

            if achei1g:
                recs = 0
                for ul in uls:
                    cnj = ul.find_element_by_xpath('uib-accordion/div/div/div[2]/div/h4').text
                    cnj = localiza_cnj(cnj)
                    if ul.find_element_by_class_name('panel-heading').text.upper().find('2º GRAU - FÍSICO') > -1:
                        result = Recurso.select(base, proc['prc_id'], rec_numero=cnj, rec_plt_id=4, rec_codigo=str(recs))
                        if len(result) == 0:
                            achei = False
                            time.sleep(1)
                            Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_numero': cnj, 'rec_plt_id':4, 'rec_codigo': recs})

                        recs += 1

                    if ul.find_element_by_class_name('panel-heading').text.upper().find('2º GRAU - ELETRÔNICO') > -1:
                        result = Recurso.select(base, rec_numero=cnj, rec_plt_id=2)
                        if len(result) == 0:
                            time.sleep(1)
                            Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_numero': cnj, 'rec_plt_id': 2})

        return achei

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        '''
        :param str numero_busca: processo a ser localizado
        '''
        self.wait()
        aguarda_presenca_elemento(self.driver, '/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div/div/div/form/div[1]/div/div[1]/div/div[2]/div[2]/div/input', aguarda_visibilidade=True)

        try:
            self.driver.find_element_by_xpath(
                '/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div/div/div/form/div[1]/div/div[1]/div/div[2]/div[2]/div/input').send_keys(numero_busca)
        except:
            raise MildException("Erro na Busca", self.uf, self.plataforma, self.prc_id)

        # Verifica se tem captcha
        # Se tiver captcha aguarda até digitação do captcha
        # Senão clica direto no botão Consultar

        captcha = self.driver.find_element_by_id('captcha')
        if not captcha:
            self.process_main_child = foca_janela(self.process_main_child)
            try:
                self.driver.find_element_by_class_name('button-consultar').click()
            except:
                time.sleep(2)
                self.driver.find_element_by_class_name('button-consultar').click()

            self.wait()
        else:
            self.captcha(numero_busca)

        self.wait()
        #CONFERIR SE O CAMPO DE BUSCA ESTÁ VAZIO E NÃO POSSUI MENSAGEM DE ERRO, DAR UM RAISE
        campo = self.driver.find_element_by_xpath('/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div/div/div/form/div[1]/div/div[1]/div/div[2]/div[2]/div/input')
        if campo.get_attribute('value') == '':
            raise MildException("Erro na Busca", self.uf, self.plataforma, self.prc_id)

        msg = self.driver.find_element_by_xpath('/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div[1]')
        if msg:
            if msg.text.find('Não foram encontradas informações') > -1:
                return False

        erro = self.driver.find_element_by_xpath('/html/body/div/div[2]/ui-view/section[2]/ng-include/div/div[1]/div/span/li')
        if erro:
            if erro.text.find('Valor indicado para a imagem') > -1:
                raise MildException("Erro na busca (captcha)", self.uf, self.plataforma, self.prc_id)

        uls = []
        while len(uls) == 0:
            uls = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")

        for ul in uls:
            if ul.find_element_by_class_name('panel-heading').text.upper().find('2º GRAU - FÍSICO') > -1:
                return True

        return False


    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        captcha = self.driver.find_element_by_id('captcha')
        if captcha:
            self.captcha(numero_busca)

        numero_site = ''
        uls = []
        while len(uls) == 0:
            uls = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")

        self.uli = -1
        i = 0
        recs = 0
        for ul in uls:
            if ul.find_element_by_class_name('panel-heading').text.upper().find('2º GRAU - FÍSICO') > -1:
                if int(self.numero_original) == recs:
                    self.uli = i
                    break
                recs += 1

            i += 1

        # aguarda_presenca_elemento(self.driver, "//ul[contains(@class, 'resultado-detalhe-item')]", aguarda_visibilidade=True)
        aguarda_presenca_elemento(self.driver, '/html/body/div/div[2]/ui-view/section[2]/ui-view/div/ul/uib-accordion/div/div/div[2]/div/h4', aguarda_visibilidade=True)

        el = self.driver.find_element_by_xpath('/html/body/div/div[2]/ui-view/section[2]/ui-view/div/ul/uib-accordion/div/div/div[2]/div/h4')
        if el:
            cnj = localiza_cnj(el.text)
            numero_site = ajusta_numero(cnj)
            if numero_busca == numero_site:
                return True

            el = self.driver.find_element_by_xpath('/html/body/div/div[2]/ui-view/section[2]/ui-view/div/ul[1]/uib-accordion/div/div/div[2]/div/div[1]/div')
            if el:
                cnj = localiza_cnj(el.text)
                if cnj:
                    numero_site = ajusta_numero(cnj)
                    if numero_busca == numero_site:
                        return True

        # print("Número CNJ Diferente - "+numero_site+" "+numero_busca)
        # time.sleep(999)
        raise MildException("Número CNJ Diferente - " + numero_site + " " + numero_busca, self.uf, self.plataforma, self.prc_id)

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        rec = {}

        # LOCALIZA STATUS DO PROCESSO
        rec['rec_status'] = get_status(self.movs, status_atual, grau=2)

        ul = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")[self.uli]

        rec_numero = ul.find_element_by_xpath('uib-accordion/div/div/div[2]/div/h4').text
        rec['rec_numero'] = localiza_cnj(rec_numero)

        detalhes = ul.find_elements_by_class_name('result-group')
        for d in detalhes:
            titulo = d.find_element_by_tag_name('label').text
            if titulo == 'Orgão Julgador':
                rec['rec_orgao'] = d.find_element_by_tag_name('div').text

            if titulo == 'Classe CNJ':
                prc_classe = d.find_element_by_tag_name('div').text
                rec['rec_classe'] = prc_classe

            if titulo == 'Assunto(s) CNJ':
                rec['rec_assunto'] = d.find_element_by_tag_name('div').text

            if titulo == 'Relator':
                rec['rec_relator'] = d.find_element_by_tag_name('div').text

        return rec

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': []}
        nomes = []

        ul = self.driver.find_elements_by_xpath("//ul[contains(@class, 'resultado-detalhe-item')]")[self.uli]
        tabela = ul.find_elements_by_class_name('result-group')
        tipos = {'ativo': 'X', 'passivo': 'Y', 'terceiro': 'Z'}
        for tb in tabela:
            polo = ''
            div_polo = tb.find_element_by_tag_name('label').text.strip().upper()

            # if find_string(div_polo,self.titulo_partes['ignorar']):
            #     continue

            if div_polo.upper() == 'REQUERENTE':
                polo = 'ativo' if len(partes['ativo']) == 0 else 'passivo'
            else:
                if find_string(div_polo,self.titulo_partes['ativo']):
                    polo = 'ativo'
                if find_string(div_polo,self.titulo_partes['passivo']):
                    polo = 'passivo'

            if polo == '':
                continue

            tipos[polo] = div_polo
            prt_nome = tb.find_element_by_tag_name('div').text
            prt_cpf_cnpj = 'Não Informado'

            if prt_nome == '':
                continue

            if prt_nome in nomes:
                continue
            nomes.append(prt_nome)

            partes[polo].append({'prt_nome': prt_nome.strip(), 'prt_cpf_cnpj': prt_cpf_cnpj})

        if tipos['ativo'] == tipos['passivo']:
            return {'ativo': [{'prt_nome': 'AMBOS',}, ],}

        return partes
