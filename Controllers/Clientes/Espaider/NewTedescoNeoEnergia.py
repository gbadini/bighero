import re
from Config.helpers import *


class NeoEnergia:
    def __init__(self, base_dados='ede'):
        self.user = 'RVEIGA'
        self.password = 'Coelba@113'
        self.site = 'https://espaider.neoenergia.com/login/main2.aspx'
        info_banco = [get_ip_base_de_dados(base_dados), 'sa', 'BEC@db521', base_dados]
        self.conexao = inicia_conexao_com_banco(info_banco)
        self.navegador = cria_driver()
        self.navegador.get(self.site)
        # 0077632-02.2014.8.05.0001
        self.expressao_valida_numero_processo = re.compile('[0-9]+-[0-9]+\.[0-9]+\.[0-9]\.[0-9]+\.[0-9]+')

    def faz_login(self):
        espera_um_elmento_por_id(self.navegador, 'userFieldEdt', 5).send_keys(self.user)
        espera_um_elmento_por_id(self.navegador, 'passFieldEdt', 5).send_keys(self.password)
        espera_um_elmento_por_id(self.navegador, 'q-comp-19', 5).click()

    def monta_datas(self):
        data_atual = str(datetime.strftime(date.today(), '%d-%m-%Y'))
        data_atual = data_atual.replace('-', '')

        dia_inicial = str(datetime.strftime((datetime.now() - timedelta(15)), '%d-%m-%Y'))
        dia_inicial = dia_inicial.replace('-', '')

        print("dia inicial: ", dia_inicial, " dia atual: ", data_atual)
        # return '12092020',data_atual
        return dia_inicial, data_atual

    def preenche_datas(self, tipo_data):
        # POR ENQUANTO COM GUAMBIARRA PARA CONTORNAR OS BUGS DO SITE

        id_inicio = 'q-comp-208'
        id_fim = 'q-comp-210'  # 'q-comp-206'
        if tipo_data != 'criado':
            id_inicio = 'q-comp-216'  # 'q-comp-212' # 'q-comp-161'
            id_fim = 'q-comp-218'  # 'q-comp-214' # 'q-comp-163'

        datas = self.monta_datas()
        # PREENCHE DATA DE INICIO
        sleep(2)
        return
        webelement_data_inicial = None
        cont = 0
        while cont < 5:
            try:
                webelement_data_inicial = espera_um_elmento_por_id(self.navegador, id_inicio, 20)
                webelement_data_inicial.send_keys(datas[0])
                break
            except:
                print("ERRO NA INSERÇÃO DA DATA DE INICIO! FAZENDO UMA TENTATIVA NOVA")
                self.navegador.refresh()
                sleep(1)
            cont += 1

        cont = 0
        verifica_data_final = False
        while cont < 5:
            try:
                # PREENCHE DATA FINAL, QUE É A DATA ATUAL
                data_final = espera_um_elmento_por_id(self.navegador, id_fim, 20)
                data_final.send_keys(datas[1])
                data_final.send_keys(Keys.RETURN)
                verifica_data_final = True
                break
            except:
                print("ERRO NA INSERÇÃO DA DATA DE FIM! FAZENDO UMA TENTATIVA NOVA")
                self.navegador.refresh()
                sleep(1)
            cont += 1

        if not verifica_data_final and webelement_data_inicial is not None:
            print(
                "ERRO NA INSERÇÃO DA DATA FINAL! PORÉM A INICIAL FOI INSERIDA, ENTÃO SERÁ INSERIDO UM ENTER NA PRIMEIRA DATA!")
            webelement_data_inicial.send_keys(Keys.RETURN)

    def coleta_quantidade_paginas(self):
        print("!!! COLETANDO QUANTIDADE DE PAGINAS !!!")# q-comp-83
        return int(espera_um_elmento_por_id(self.navegador, 'q-comp-47', 5).text.replace("de ", ""))

    def volta_para_o_html_principal(self):
        self.navegador.switch_to.default_content()

    def coleta_numero_processo(self, texto_linha):
        # SEPARA O TEXTO DA LINHA POR QUEBRA DE LINHA, PARA PODER COLETAR AS INFORMAÇÕES
        lista_auxiliar = texto_linha.split("\n")
        for aux in lista_auxiliar:
            # VERIFICA SE É O NÚMERO DO PROCESSO, SE SIM RETORNA O NUMERO DO PROCESSO
            if self.expressao_valida_numero_processo.match(aux[:25]) is not None:
                print("ENCONTROU O NUMERO DO PROCESSO: ", aux[:25])
                return aux[:25]

        return ''

    # CLICA EM CIMA DA LINHA DO PROCESSO, PARA VER TODAS INFORMAÇÕES REFERENTES A ESSE PROCESSO
    def busca_web_element_linha(self, pos):
        # MONTA O XPATH PARA CLICAR EM CADA PROCESSO
        # xpath='/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[2]/td[3]/div'
        xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[' + str(
            pos + 1) + ']/td[3]/div'
        # ABRE TELA COM AS INFORMAÇÕES DO PROCESSO
        return espera_um_elemento_por_xpath(self.navegador, xpath, 5)

    def passa_para_o_frame_da_janela_informacoes(self):
        # PASSA PARA O FRAME DA JANELA QUE ABRIU
        xpath = '/html/body/div[2]/div/div[2]/div/iframe'
        passa_para_o_frame_por_xpath(self.navegador, xpath, 5)
        print("PASSOU PARA O FRAME DA CAIXA DE INFORMAÇÕES!!")

    def coleta_texto_todas_linhas(self, lista_elmentes):
        lista_texto_linhas = []
        for elemento in lista_elmentes:
            lista_texto_linhas.append(elemento.text)

        return lista_texto_linhas

    def passa_para_proxima_pagina(self):  # q-comp-155 q-comp-157 q-comp-121
        # clica = input('proxima pagina?')
        espera_um_elmento_por_id(self.navegador, 'q-comp-121', 5).click()

    def espera_pagina_carregar(self):
        xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[4]/div[1]'
        wait = WebDriverWait(self.navegador, 60)
        wait.until(EC.invisibility_of_element((By.XPATH, xpath)))

    def coleta_informacoes_processos(self):
        # COLETA JUIZO
        juizo = espera_um_elmento_por_id(self.navegador, 'ABA_DESD_JuizoIDEdt', 5).get_attribute('value').replace("'",
                                                                                                                  " ")
        # COLETA COMARCA
        comarca = espera_um_elmento_por_id(self.navegador, 'ABA_DESD_BuscaComarcaIDEdt', 5).get_attribute(
            'value').replace("'", " ")
        # REMOVE O readonly QUE IMPEDE A COLETA DO TEXTO
        lista_WebElementos = self.navegador.find_elements_by_tag_name('input')
        for WebElemento in lista_WebElementos:
            self.navegador.execute_script("arguments[0].removeAttribute('readonly','readonly')", WebElemento)

        # self.navegador.execute_script('document.getElementByTagName("value").removeAttribute("readonly")')
        situacao = espera_um_elmento_por_nome(self.navegador, 'SituacaoProcesso', 5).get_attribute('value').replace("'",
                                                                                                                    " ")
        autor = espera_um_elmento_por_nome(self.navegador, 'Adverso', 5).get_attribute('value').replace("'", " ")
        objeto1 = espera_um_elmento_por_nome(self.navegador, 'CLI_Objeto', 5).get_attribute('value').replace("'", " ")

        # TRATA O CONTEUDO QUE FOI COLETADO DE AUTOR, PARA EVITAR QUE PASSE O NUMERO DE CARACTERES
        autor = corta_string(texto=autor,chars=80)

        return [autor, comarca, objeto1, situacao, juizo]

    def fecha_janela_informacoes_processo(self):
        # FECHA JANELA NOVA QUE ABRIU
        xpath = '/html/body/div[2]/div/div[1]/div/div[2]/div/div/em/button'
        espera_um_elemento_por_xpath(self.navegador, xpath, 5).click()
        print("FECHA JANELA QUE ABRIU!")

    def coleta_todos_os_processos(self):
        quant_processos_inseridos = 0
        sleep(3)
        quant_paginas = self.coleta_quantidade_paginas()
        # FOR QUE PERCORRE POR TODAS AS PAGINAS
        print("QUANTIDADE DE PAGINAS: ", quant_paginas)

        # GARANTE QUE O BOT NÃO COLETOU A QUANTIDADE DE PAGINAS ERRADA
        while quant_paginas > 110:
            quant_paginas = self.coleta_quantidade_paginas()

        for j in range(quant_paginas):
            # COLETA OS ELEMENTS DE TODAS AS LINHAS
            #         '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr'
            # analuiza = input('CONFERE XPATH')
            xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr'
            lista_elements = self.navegador.find_elements_by_xpath(xpath)
            quant_linhas = len(lista_elements)
            print("Quantidade de linhas: ", quant_linhas)
            # FOR QUE PERCORRE POR TODAS AS LINHAS
            # OBS: COMEÇA NA POSIÇÃO 1, PQ A 0 É UMA LINHA VAZIA QUE POSSUI NA TABELA
            lista_texto_linhas = self.coleta_texto_todas_linhas(lista_elements)
            for i in range(1, quant_linhas):
                # print("---------------------------------------------------------------")
                # print("INFORMAÇÕES DE CADA POSIÇÃO DA LISTA: ", lista_texto_linhas[i])
                # print("---------------------------------------------------------------")
                # sleep(6000)
                numero_processo = self.coleta_numero_processo(lista_texto_linhas[i])
                # VERIFICA SE ESSE PROCESSO JÁ EXISTE NA BASE DE DADOS, CASO JÁ EXISTA JÁ PASSA PARA O PROXIMO

                if numero_processo != '' and len(self.conexao.consulta_processo_neo_energia(numero_processo)) == 0:
                    # EXECUTA A COLETA DE INFORMAÇÕES
                    # ESPERA ATÉ QUE O LOADING DA PAGINA FINALIZE
                    print("UM NOVO PROCESSO FOI ENCONTRADO -> {}".format(numero_processo))
                    print("ESPERANDO FUNÇÃO LOADING FINALIZAR!")

                    self.espera_pagina_carregar()
                    # CLICA NA LINHA DO PROCESSO, PARA ACESSAR INFORMAÇÕES DO PROCESSO
                    elemento_linha = self.busca_web_element_linha(i)
                    elemento_linha.click()
                    print("VOLTA PARA O HTML PRINCIPAL!!!")
                    self.volta_para_o_html_principal()
                    # PASSA PARA O FRAME DA ABA QUE ABRIU COM AS INFORMAÇÕES DO PROCESSO
                    self.passa_para_o_frame_da_janela_informacoes()
                    sleep(1)
                    '''INFORMAÇÕES QUE SERAM COLETADAS NESSA ETAPA:
                            -> Comarca
                            -> Juizo
                            -> Autor
                            -> Objeto
                        Seguindo a seguinte ordem na lista:
                        0        1         2       3        4        5        6
                    [numero, sequencial, autor, comarca, objeto1, situacao, juizo]'''
                    lista_informacoes_processo_coletadas = [numero_processo,
                                                            'SEM CONTRATO'] + self.coleta_informacoes_processos()
                    print("INFORMAÇÕES DO PROCESSO: ", lista_informacoes_processo_coletadas)
                    print("VOLTA PARA O HMTL PRINCIPAL NOVAMENTE!")
                    self.volta_para_o_html_principal()
                    self.fecha_janela_informacoes_processo()
                    # VOLTA PARA O FRAME QUE POSSUI TODOS OS PROCESSOS q-comp-30
                    print("VOLTA PARA O FRAME QUE TEM TODOS OS PROCESSOS!")
                    passa_para_o_frame_por_id(self.navegador, 'q-comp-27', 10)
                    print(lista_informacoes_processo_coletadas)
                    # sleep(20)
                    self.conexao.insere_processo_neo_energia(lista_informacoes_processo_coletadas)
                    print("================================================")
                    self.espera_pagina_carregar()
                    quant_processos_inseridos += 1
                else:
                    print("PROCESSO: {} JÁ EXISTE NA BASE DE DADOS!".format(numero_processo))
                    print("ATUALIZA O CAMPO prc_data_update1 DESSE PROCESSO")
                    self.conexao.seta_prc_data_update1_como_null(numero_processo)
                    print("================================================")

            print("Valor de i: ", j, " quant_paginas - 1: ", quant_paginas - 1)
            if j < quant_paginas - 1:
                sleep(1)
                print("PASSANDO PARA A PROXIMA PAGINA!")
                self.passa_para_proxima_pagina()
                self.espera_pagina_carregar()

        print("!!!!! QUANTIDADE DE PROCESSOS QUE FORAM INSERIDOS [{}] !!!!!".format(quant_processos_inseridos))

    def nova_tentativa_login(self):
        self.navegador.close()
        self.navegador = cria_driver()
        self.navegador.get(self.site)
        self.faz_login()
        passa_para_o_frame_por_id(self.navegador, 'q-comp-27', 10)

    def clica_em_contensioso(self):
        xpath = '/html/body/form/div[1]/div[1]/div/div[1]/div[1]/div/div[2]/em/button'
        espera_um_elemento_por_xpath(self.navegador, xpath, 5).click()
        # espera_um_elmento_por_id(self.navegador, 'q-comp-11', 5).click()

    def execute(self, tipo_data):
        self.faz_login()
        # recusa_alerta(self.navegador)
        sleep(15)
        print("LOGIN FEITO COM SUCESSO!")
        print("INDO PARA CONTENSIOSO!")
        self.clica_em_contensioso()
        self.espera_pagina_carregar()

        # MUDA DE FRAME PARA PREENCHER AS DATAS
        try:  # antes era q-comp-29 e 30
            passa_para_o_frame_por_id(self.navegador, 'q-comp-27', 10)
            print("PASSOU PARA O IFRAME")
        except:
            print("ERRO NO LOGIN, FAZENDO UMA SEGUNDA TENTATIVA!")
            sleep(5)
            self.nova_tentativa_login()

        # self.navegador.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # PASSA PARA O FRAME DA BARRA DE ROLAGEM POR XPATH
        self.volta_para_o_html_principal()
        sleep(5)
        xpath = '/html/body/form/div[1]/div[2]/div[2]/iframe'
        passa_para_o_frame_por_xpath(self.navegador, xpath, 5)
        # print("TENTANDO ROLAR A TELA PARA O LADO")
        # self.navegador.execute_script("window.scrollTo(0, 200)")
        # self.navegador.execute_script("window.scrollTo(-1000, 0)")
        # sleep(600)
        print("PASSOU PARA O PROXIMO FRAME!")
        self.preenche_datas(tipo_data)
        x = input("DATAS PREENCHIDAS?")
        sleep(5)  # ESSE SLEEP É NECESSARIO, PARA QUE DE TEMPO DA PAGINA ATUALIZAR
        print("INICIANDO COLETA DE TODOS OS PROCESSOS!")
        self.espera_pagina_carregar()
        self.coleta_todos_os_processos()
        self.navegador.close()
        print("!!!!! VARREDURA FINALIZADA !!!!!")


class NeoEnergiaAndamentos(NeoEnergia):

    def __init__(self, base_dados='ede', inicio=0, fim=0, lista_processos=None,bool_chama_funcao_coleta_processos=True):
        super().__init__(base_dados=base_dados)
        self.lista_processos = []
        if lista_processos is not None:
            self.lista_processos = lista_processos

        self.inicio = inicio
        self.fim = fim
        self.bool_chama_funcao_coleta_processos = bool_chama_funcao_coleta_processos
        # self.fim = len(self.lista_processos)
        print("Inicio: {} Fim: {}".format(self.inicio, self.fim))

    def insere_pontos_tracos_numero_processo(self, numero_processo):
        try:
            # exemplo saída: 0000000-00.0000.0.00.0000
            if "." in numero_processo and "-" in numero_processo:
                return numero_processo

            numero_final = numero_processo[0:7] + "-" + numero_processo[7:9] + "." + numero_processo[9:13]
            numero_final += "." + numero_processo[13] + "." + numero_processo[14:16] + "." + numero_processo[16:20]
            print("ANTES: ", numero_processo)
            print("FINAL: ", numero_final)
            return numero_final
        except:
            return numero_processo

    def insere_processo(self, numero_processo):
        # caixa_filtro = espera_um_elmento_por_id(self.navegador, 'filterTBX_gridpanel_XIDG1493FDD7Edt', 5)
        xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[1]/div/div/div[5]/div/div[2]/input'
        caixa_filtro = espera_um_elemento_por_xpath(self.navegador, xpath, 5)
        caixa_filtro.clear()
        caixa_filtro.send_keys(numero_processo)
        caixa_filtro.send_keys(Keys.RETURN)

    def coleta_todas_linhas_tabela(self):
        sleep(1)
        xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr'
        return self.navegador.find_elements_by_xpath(xpath)

    def clica_em_andamentos(self):
        espera_um_elmento_por_id(self.navegador, 'colEventosNova', 10).click()

    def coleta_linhas_andamentos(self):
        sleep(0.5)
        xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr'
        return self.navegador.find_elements_by_xpath(xpath)

    def coleta_texto_linha(self, posicao):
        xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[{}]'.format(
            posicao)
        return espera_um_elemento_por_xpath(self.navegador, xpath, 5).text

    def trata_data_andamento_banco(self, data):
        auxiliar = []
        if "datetime" in data:
            data = data.replace("datetime.datetime", "")
            data = data.replace("(", "")
            data = data.replace(")", "")
            data = data.replace(" ", "")
            auxiliar = data.split(",")
            data = auxiliar[:3]
            data.reverse()
            auxiliar = data + auxiliar[3:5]

        else:
            aux = data.split(" ")
            data = aux[0].split("-")
            data.reverse()
            hora = aux[1].split(":")
            auxiliar = data + hora

        # print("LISTA AUXILIAR DATA ANTES: ", auxiliar)
        auxiliar = ["0" + aux if len(aux) == 1 else aux for aux in auxiliar]
        # print("LISTA AUXILIAR DATA DEPOIS DE SER TRATADA", auxiliar)

        return "/".join(auxiliar[:3])

    def apaga_movimentacoes_erradas(self, lista_ids_existe_base, lista_movimentacoes_base):
        listal_final = []

        if len(lista_ids_existe_base) == len(lista_movimentacoes_base):
            return

        print("TAMANHO LISTA IDS EXISTEM NA BASE: ", len(lista_ids_existe_base))
        print("TAMANHO LISTA MOVIMENTAÇÕES EXISTEM NA BASE: ", len(lista_movimentacoes_base))
        print("-----------------------------------------------")
        print(lista_ids_existe_base)
        print("-----------------------------------------------")
        print(lista_movimentacoes_base)
        print("-----------------------------------------------")

        lista_pos = []
        for i in range(len(lista_ids_existe_base)):
            for j in range(len(lista_movimentacoes_base)):
                if lista_ids_existe_base[i] == lista_movimentacoes_base[j][3]:
                    lista_pos.append(j)

        print("POSIÇÕES DOS ITEMS QUE SERÃO DELETADOS: ", lista_pos)
        for i in range(len(lista_movimentacoes_base)):
            if not i in lista_pos:
                print("ESSA POSIÇÃO NÃO EXISTE NA LISTA: ", i)
                listal_final.append(lista_movimentacoes_base[i][3])

        print("-----------------------------------------------")
        print("TAMANHO LISTA MOVIMENTAÇÕES EXISTEM NA BASE: ", len(listal_final))
        for posicao in listal_final:
            print("-> ", posicao)
        print("-----------------------------------------------")
        print("CHEGOU NO SLEEP")
        self.conexao.deleta_acompanhamento_base(listal_final)

    def separa_e_insere_andamentos_na_base(self, prc_id, lista_acompanhamentos_coletados):
        lista_ids_existe_base = []

        lista_andamentos_que_esxistem_na_base = self.conexao.busca_andamentos_neo_energia(prc_id)
        tam_lista_andamentos_da_base = len(lista_andamentos_que_esxistem_na_base)
        print("Tamanho da lista de andamentos:: ", tam_lista_andamentos_da_base)
        quant_andamentos_inseridos = 0
        quant_andamentos_que_sofreram_update = 0

        # print(",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,")
        # print(lista_andamentos_que_esxistem_na_base)
        # print(lista_acompanhamentos_coletados)
        # print(".........................................................")
        # for ll in lista_acompanhamentos_coletados:
        #     print(ll)
        # print(",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,")

        if tam_lista_andamentos_da_base == 0:
            print("Esse processo não tem andamentos na base, insere todos coletados!")
            for acompanhamento_coletado in lista_acompanhamentos_coletados:
                self.conexao.insere_acompanhamento_neo_energia(prc_id, acompanhamento_coletado)
                quant_andamentos_inseridos += 1
        else:
            for acompanhamento_coletado in lista_acompanhamentos_coletados:
                id_acompanhamento_existe_na_base = ''
                acompanhamento_existe_na_base = False
                print("INICIANDO VERIFICAÇÃO DO PRIMEIRO ANDAMENTO")
                for acompanhamento_base in lista_andamentos_que_esxistem_na_base:
                    # print("DATA QUE ESTÁ NA BASE, ANTES DE SER TRATADA: ", acompanhamento_base[0])
                    data_andamento_tratada = self.trata_data_andamento_banco(str(acompanhamento_base[0]))
                    # print("Tenta arrumar data que veio da base: ", data_andamento_tratada)
                    acp_tipo_base = trata_string_para_comparacao(str(acompanhamento_base[1]))
                    acp_tipo_coletado_site = trata_string_para_comparacao(str(acompanhamento_coletado[1]))

                    acp_esp_base = trata_string_para_comparacao(acompanhamento_base[2])
                    acp_esp_coletado = trata_string_para_comparacao(acompanhamento_coletado[2])

                    # if "DESPACHO" in acompanhamento_base[1]:
                    # print("--------------------------------------\nCOMPARAÇÃO DOS DADOS:")
                    # print(acompanhamento_coletado[0])
                    # print(data_andamento_tratada)
                    # print("---------------")
                    # print(acp_tipo_coletado_site)
                    # print(acp_tipo_base)
                    # print("--------------")
                    # print(acp_esp_coletado)
                    # print(acp_esp_base)
                    # print("--------------------------------------")
                    # print("-> ", acompanhamento_coletado[2])
                    # print("-> ", acompanhamento_base[2])
                    # print("--------------------------------------")
                    # print("Antes da comparação")
                    # print(acompanhamento_base)

                    # print(acp_esp_coletado," # ",acp_esp_base)
                    if acompanhamento_coletado[0] == data_andamento_tratada and acp_tipo_base == acp_tipo_coletado_site \
                            and (acp_esp_coletado == acp_esp_base):
                        print("--------------------------------------")
                        print("***> ", acompanhamento_coletado[1])
                        print("***> ", acompanhamento_base[1])
                        print("--------------------------------------")
                        print("--------------------------------------")
                        print("===> ", acompanhamento_coletado[2])
                        print("===> ", acompanhamento_base[2])
                        print("--------------------------------------")
                        print("ESSE ACOMPANHAMENTO JÁ EXISTE NA BASE!")
                        acompanhamento_existe_na_base = True
                        id_acompanhamento_existe_na_base = acompanhamento_base[3]
                        lista_ids_existe_base.append(id_acompanhamento_existe_na_base)
                        break

                print("SAI DO FOR! VERIFICA VARIAVEL BOOLEANA!")
                if not acompanhamento_existe_na_base:
                    print("ESSE ACOMPANHAMENTO NÃO EXISTE NA BASE, ENTÃO SERÁ INSERIDO")
                    self.conexao.insere_acompanhamento_neo_energia(prc_id, acompanhamento_coletado)
                    quant_andamentos_inseridos += 1
                else:
                    print("ESSE ANDAMENTO JÁ EXISTE NA BASE! APENAS O ACP USUARIO SERÁ ATUALIZADO")
                    # Esse acompanhamento já existe na base, então apenas atualiza o acp_usuario dele
                    self.conexao.atualiza_acp_usuario_processo(id_acompanhamento_existe_na_base,
                                                               acompanhamento_coletado[3])
                    quant_andamentos_que_sofreram_update += 1
        self.apaga_movimentacoes_erradas(lista_ids_existe_base, lista_andamentos_que_esxistem_na_base)
        print("----- QUANTIDADE DE ANDAMENTOS QUE PASSARAM POR UPDATE: {} -----".format(
            quant_andamentos_que_sofreram_update))
        print("------------ QUANTIDADE DE ANDAMENTOS INSERIDOS: {} ------------".format(quant_andamentos_inseridos))

    def valida_busca(self, elemento_linha, numero_processo):
        ''' Verifica se o resultado da busca, é valido, se não for, tenta buscar o processo novamente, se o erro se repetir
        a busca é reiniciada desde, partindo a partir do ponto em que o erro ocorreu'''
        texto_linha_numero = elemento_linha.text
        texto_linha_numero_aux = texto_linha_numero
        # print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        # print("texto_numero linha, antes de ser enviado para função: ", texto_linha_numero)
        texto_linha_numero = texto_linha_numero.replace(".", "")
        texto_linha_numero = texto_linha_numero.replace("-", "")
        # print("DEPOIS DE TRATAR A VARIAVEL: ", texto_linha_numero)
        # print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")

        texto_linha_numero = self.insere_pontos_tracos_numero_processo(texto_linha_numero)
        if texto_linha_numero_aux == numero_processo:
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            print("COM OS PONTOS E TRAÇOS, O NUMERO ESTA CORRETO COM O ENCONTRADO NO SITE")
            print("NUMERO QUE CAIU NESSE IF: ", texto_linha_numero_aux, numero_processo)
            print("[{}] == [{}]".format(texto_linha_numero, numero_processo))
            print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            return True

        # VERIFICA SE O PROCESSO QUE SAI COMO RESULTADO DA BUSCA, É O MESMO QUE ESTÁ SENDO BUSCADO
        print("[{}] == [{}]".format(texto_linha_numero, numero_processo))
        if not texto_linha_numero == numero_processo:
            print("O NÚMERO QUE ESTÁ COMO RESULTADO, ESTÁ DIFERENTE, DO NÚMERO QUE ESTÁ SENDO BUSCADO")
            print("----- A BUSCA ESTÁ SENDO REINICIADA, PARTIDA DO PONTO EM QUE OCORREU ESSE ERRO -----")
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("ANTES DE REINICIAR A BUSCA, TENTA BUSCAR O PROCESSO NO SITE NOVAMENTE")
            sleep(5)
            return False

        return True

    def coleta_andamentos_processo(self, numero_processo):
        lista_acompanhamentos_coletados = []
        print("COLETA A LISTA DE WEBELEMENTS DE TODAS AS LINHAS")
        lista_web_elments_linhas = self.coleta_todas_linhas_tabela()
        quantidade_linhas = len(lista_web_elments_linhas)
        print("Quantidade de linhas da tabela: ", quantidade_linhas)
        if quantidade_linhas == 0:
            return []

        for i in range(1, quantidade_linhas):
            print("BUSCA O WEB ELEMENT DA LINHA")
            elemento_linha = self.busca_web_element_linha(i)

            if not self.valida_busca(elemento_linha, numero_processo):
                # TENTA EXECUTAR UM ENTER NA BUSCA DO PROCESSO NOVAMENTE
                xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[1]/div/div/div[5]/div/div[2]/input'
                espera_um_elemento_por_xpath(self.navegador, xpath, 5).send_keys(Keys.RETURN)
                self.espera_pagina_carregar()

                elemento_linha = self.busca_web_element_linha(i)

                if not self.valida_busca(elemento_linha, numero_processo):
                    '''Após a segunda tentativa de busca, o erro persistiu, então a busca deve ser reiniciada'''
                    if quantidade_linhas > 1:
                        print("ERRO PROCESSOS DIFERENTES, POREM POSSUI MAIS DE UMA LINHA")
                        continue

                    return None

            print("CLICA NA LINHA DO PROCESSO")
            elemento_linha.click()
            sleep(2)
            self.volta_para_o_html_principal()
            self.passa_para_o_frame_da_janela_informacoes()
            print("CLICA EM ANDAMENTOS!")
            self.clica_em_andamentos()
            # PASSA PARA O FRAME QUE TEM OS ANDAMENTOS
            xpath_frame = '/html/body/form/div/div/div[2]/div[2]/div[2]/div[5]/iframe'
            passa_para_o_frame_por_xpath(self.navegador, xpath_frame, 5)
            linhas_andamentos = self.coleta_linhas_andamentos()
            tam_linhas_andamentos = len(linhas_andamentos)
            print("Quantidade de linhas andamentos: ", len(linhas_andamentos))
            if tam_linhas_andamentos == 0:
                print(
                    "NÃO EXISTE NENHUM ANDAMENTO PARA ESSE PROCESSO, FECHANDO JANELA DOS ANDAMENTOS E PASSANDO PARA O PROXIMO")
                self.volta_para_o_html_principal()
                self.fecha_janela()
                self.espera_pagina_carregar()
                passa_para_o_frame_por_id(self.navegador, 'q-comp-27', 5) #'q-comp-30'

                return []

            xpathh = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[3]/td[2]/div'

            # COLETA O TEXTO DAS LINHAS DOS ANDAMENTOS
            for i in range(2, tam_linhas_andamentos + 1):
                xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[{}]/td[2]/div'.format(
                    i)
                data_acompanhamento = espera_um_elemento_por_xpath(self.navegador, xpath, 5).text

                xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[{}]/td[3]/div'.format(
                    i)
                andamento = espera_um_elemento_por_xpath(self.navegador, xpath, 5).text

                xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[{}]/td[4]/div'.format(
                    i)
                publicacao = espera_um_elemento_por_xpath(self.navegador, xpath, 5).text

                xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[{}]/td[5]/div'.format(
                    i)
                complemento = espera_um_elemento_por_xpath(self.navegador, xpath, 5).text

                xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[{}]/td[6]/div'.format(
                    i)
                responsavel = espera_um_elemento_por_xpath(self.navegador, xpath, 5).text

                # print("--------------------------------------------------------------")
                # print(data_acompanhamento)
                # print(andamento)
                # print(publicacao)
                # print(complemento)
                # print(responsavel)
                # print("--------------------------------------------------------------")

                lista_acompanhamentos_coletados.append([data_acompanhamento, andamento, complemento, responsavel])

        return lista_acompanhamentos_coletados

    def fecha_janela(self):
        xpath_botao = '/html/body/div[2]/div/div[1]/div/div[2]/div/div/em/button'
        espera_um_elemento_por_xpath(self.navegador, xpath_botao, 5).click()

    def remove_ponto_tracos(self, numero_processo):
        numero_processo = numero_processo.replace('.', '')
        numero_processo = numero_processo.replace('-', '')
        return numero_processo

    def remove_ponto_especifico(self, numero_processo):
        # 8001770-83.2020.8.05.0127
        return numero_processo[:17] + numero_processo[18:]

    def busca_todos_processos(self):
        print("INICIANDO A BUSCA DE TODOS OS PROCESSOS")
        print("INTERVALO DE BUSCA: ", self.inicio, " - ", self.fim)
        for i in range(self.inicio, self.fim):
            prc_id = self.lista_processos[i][1]
            print("######################### {} / {} #########################".format(i, self.fim))
            numero_processo = self.lista_processos[i][0]

            # numero_processo = '0000167-72.2010.805.0221'
            if numero_processo is None:
                numero_processo = self.lista_processos[i][7]
            if numero_processo is None:
                numero_processo = self.lista_processos[i][8]

            # if '0000855-79.2016.8.05.0138' != numero_processo:
            #     continue

            if numero_processo is None:
                print("ENCONTROU O NUMERO DE PROCESSO QUE É NONE")
                continue

            prc_id = self.lista_processos[i][1]
            print("---------------------------------------------------------")
            print("NUMERO PROCESSO: ", numero_processo)
            print("PRC ID: ", prc_id)
            print("---------------------------------------------------------")
            print("TRATA O NÚMERO DO PROCESSO")

            # HERE 2

            numero_processo = self.insere_pontos_tracos_numero_processo(numero_processo)
            # INSERE O PROCESSO NO CAMPO FILTRO, E PRESSIONA ENTER PARA BUSCAR O MESMO
            print("INSERE O NÚMERO DO PROCESSO NO SITE")

            self.navegador.refresh()
            passa_para_o_frame_por_id(self.navegador, 'q-comp-27', 5) # 'q-comp-30'
            self.espera_pagina_carregar()
            lista_andamentos_coletados = []
            for i in range(3):
                numero_processo_aux = numero_processo
                if i == 0:
                    self.insere_processo(numero_processo)
                    # print('-> NORMAL')
                    # sleep(2)d
                elif i == 1:
                    numero_processo_aux = self.remove_ponto_especifico(numero_processo)
                    self.insere_processo(numero_processo_aux)
                    # print('-> PONTO ESPECIFICO')
                    # sleep(10)
                else:
                    numero_processo_aux = self.remove_ponto_tracos(numero_processo)
                    self.insere_processo(numero_processo_aux)
                    # print('-> SEM PONTOS E TRACOS')
                    # sleep(2)

                self.espera_pagina_carregar()
                lista_andamentos_coletados = self.coleta_andamentos_processo(numero_processo_aux)
                if len(lista_andamentos_coletados) != 0:
                    # if i != 0:
                    #     print('---> CAIU NO SLEEEEEEEEEEEEEEEEEEEEEP')
                    #     sleep(600)
                    break


            ''' Se chegou aqui como None, quer dizer que o numero resultado do site, não bate com o numero que está 
            sendo buscado no site, então a busca deve ser reiniciada.'''
            if lista_andamentos_coletados is None:
                # SE ESSE ERRO OCORREU, RETORNA A POSIÇÃO EM QUE PAROU, PARA RECOMEÇAR
                return i

            if len(lista_andamentos_coletados) == 0:
                print("NÃO ENCONTROU O PROCESSO NO SITE!")
                print("NÃO ENCONTROU NENHUM PROCESSO, PARA ESSA BUSCA, PASSANDO PARA A PROXIMA BUSCA!")
                continue

            self.separa_e_insere_andamentos_na_base(prc_id, lista_andamentos_coletados)
            print(1)
            self.volta_para_o_html_principal()
            self.fecha_janela()
            self.espera_pagina_carregar()
            passa_para_o_frame_por_id(self.navegador, 'q-comp-27', 5) # 'q-comp-30'
            self.conexao.seta_prc_data_update1_com_a_data_atual(numero_processo)

        return -1

    def seta_filtro_andamentos_recentes(self):
        # CASO TENHA VOLTADO PARA O HTML PRINCIPAL, VAI ATÉ O FRAME EM QUE O BOTÃO DE FILTRO ESTÁ
        xpath = '/html/body/form/div[1]/div[2]/div[2]/iframe'

        # XPATH DO BOTÃO DE FILTRO AVANÇADO
        xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[1]/div/div/div[7]/em/button'
        passa_para_o_frame_por_id(self.navegador, 'q-comp-27', 5)
        # CLICA NO BOTÃO DE FILTRO AVANÇADO
        # espera_um_elmento_por_id(self.navegador, 'q-comp-145', 5).click()
        print("CLICA NO BOTÃO DE FILTRO AVANÇADO")
        espera_um_elemento_por_xpath(self.navegador, xpath, 5).click()
        sleep(2)

        print("VOLTA PARA O HTML PRINCIPAL")
        self.volta_para_o_html_principal()
        # PASSA PARA O FRAME DA CAIXA QUE ABRIU  q-comp-331_proxy
        print("PASSA PARA O IFRAME DAS OPÇÕES DO FILTRO")
        passa_para_o_frame_por_id(self.navegador, 'q-comp-295_proxy', 5)

        print("CLICA NA LISTA DE FILTROS")
        espera_um_elmento_por_id(self.navegador, 'cbModeloFiltroEdt', 5).click()

        self.volta_para_o_html_principal()
        # SELECIONA O FILTRO CORRETO
        print("FILTRO CORRETO")
        xpath = '/html/body/div[3]/div/div/div/div[13]'
        espera_um_elemento_por_xpath(self.navegador, xpath, 5).click()

    def clica_em_ok_filtro(self):
        # CLICA EM OK, PARA APLICAR O FILTRO
        xpath = '/html/body/form/div[1]/div/div[2]/div[2]/div/div/div[1]/em/button'
        espera_um_elemento_por_xpath(self.navegador, xpath, 5).click()

    def preenche_datas_intervalo_andamentos(self):
        passa_para_o_frame_por_id(self.navegador, 'q-comp-295_proxy', 5)
        datas = self.monta_datas()
        # DATA DE INICIO
        id = 'ProcessoEventos_DataEvento_startDateEdt'
        xpath = '/html/body/form/div[1]/div/div[2]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/table[1]/tbody/tr/td[2]/div/div/div/input'
        espera_um_elemento_por_xpath(self.navegador, xpath, 5).send_keys(datas[0])

        # DATA DE FIM
        id = 'ProcessoEventos_DataEvento_endDateEdt'
        xpath = '/html/body/form/div[1]/div/div[2]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/table[1]/tbody/tr/td[4]/div/div/div/input'
        espera_um_elemento_por_xpath(self.navegador, xpath, 5).send_keys(datas[1])

    def coleta_andamentos_processo_intervalo_data(self):
        lista_acompanhamentos_coletados = []
        print("COLETA A LISTA DE WEBELEMENTS DE TODAS AS LINHAS")
        lista_web_elments_linhas = self.coleta_todas_linhas_tabela()
        quantidade_linhas = len(lista_web_elments_linhas)
        print("Quantidade de linhas da tabela: ", quantidade_linhas)
        if quantidade_linhas == 0:
            return []

        for i in range(1, quantidade_linhas):
            print("BUSCA O WEB ELEMENT DA LINHA")
            elemento_linha = self.busca_web_element_linha(i)
            print("CLICA NA LINHA DO PROCESSO")
            elemento_linha.click()
            sleep(2)
            self.volta_para_o_html_principal()
            self.passa_para_o_frame_da_janela_informacoes()
            print("CLICA EM ANDAMENTOS!")
            self.clica_em_andamentos()
            # PASSA PARA O FRAME QUE TEM OS ANDAMENTOS
            xpath_frame = '/html/body/form/div/div/div[2]/div[2]/div[2]/div[5]/iframe'
            passa_para_o_frame_por_xpath(self.navegador, xpath_frame, 5)
            linhas_andamentos = self.coleta_linhas_andamentos()
            tam_linhas_andamentos = len(linhas_andamentos)
            print("Quantidade de linhas andamentos: ", len(linhas_andamentos))
            if tam_linhas_andamentos == 0:
                print(
                    "NÃO EXISTE NENHUM ANDAMENTO PARA ESSE PROCESSO, FECHANDO JANELA DOS ANDAMENTOS E PASSANDO PARA O PROXIMO")
                self.volta_para_o_html_principal()
                self.fecha_janela()
                self.espera_pagina_carregar()
                passa_para_o_frame_por_id(self.navegador, 'q-comp-27', 5) #'q-comp-30'

                return []

            xpathh = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[3]/td[2]/div'

            # COLETA O TEXTO DAS LINHAS DOS ANDAMENTOS
            print("COLETA O TEXTO DA LINHA DOS ANDAMENTOS")
            for i in range(2, tam_linhas_andamentos + 1):
                xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[{}]/td[2]/div'.format(
                    i)
                data_acompanhamento = espera_um_elemento_por_xpath(self.navegador, xpath, 5).text

                xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[{}]/td[3]/div'.format(
                    i)
                andamento = espera_um_elemento_por_xpath(self.navegador, xpath, 5).text

                xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[{}]/td[4]/div'.format(
                    i)
                publicacao = espera_um_elemento_por_xpath(self.navegador, xpath, 5).text

                xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[{}]/td[5]/div'.format(
                    i)
                complemento = espera_um_elemento_por_xpath(self.navegador, xpath, 5).text

                xpath = '/html/body/form/div/div[2]/div/div/div/div/div/div[1]/div/div[2]/div/div[2]/table/tbody/tr[{}]/td[6]/div'.format(
                    i)
                responsavel = espera_um_elemento_por_xpath(self.navegador, xpath, 5).text

                # print("--------------------------------------------------------------")
                # print(data_acompanhamento)
                # print(andamento)
                # print(publicacao)
                # print(complemento)
                # print(responsavel)
                # print("--------------------------------------------------------------")

                lista_acompanhamentos_coletados.append([data_acompanhamento, andamento, complemento, responsavel])

            # FECHA CAIXA DOS ANDAMETOS
            self.volta_para_o_html_principal()
            print("FECHA JANELA DA CAIXA DE INFORMAÇÕES")
            self.volta_para_o_html_principal()
            self.fecha_janela()
            self.espera_pagina_carregar()
            passa_para_o_frame_por_id(self.navegador, 'q-comp-27', 5)
            sleep(1)

        return lista_acompanhamentos_coletados

    # ----------------------------------------------------------------------------------------------------------------------
    # HERE

    def execute_busca_andamentos_(self):
        try:
            print("FAZ-ENDO LOGIN")
            self.faz_login()
            sleep(10)
            print("CLICA EM CONTENCIOSO")
            self.clica_em_contensioso()
            print("espera_pagina_carregar")
            self.espera_pagina_carregar()
            # sleep(6000)
            # MARCA O FILTRO SÓ QUANDO VAI FAZER A COLETA DOS PROCESSOS QUE NÃO EXISTE
            if self.bool_chama_funcao_coleta_processos:
                self.seta_filtro_andamentos_recentes()
                self.preenche_datas_intervalo_andamentos()
                self.clica_em_ok_filtro()

            print("DEPOIS DE CLICAR O OK")
            self.volta_para_o_html_principal()
            print("VOLTOU PARA O HTML PRINCIPAL")
            # # Passa para o frame em que está a caixa do filtro
            # alk = input('kaio')
            # id_ = 'q-comp-27'  # 'q-comp-30' 'q-comp-609'
            xpath = '/html/body/form/div[1]/div[2]/div[2]/iframe'
            # passa_para_o_frame_por_id(self.navegador, id_, 10)
            print("passa_para_o_frame")
            passa_para_o_frame_por_xpath(self.navegador, xpath, 10)

            print("PASSOU PARA DENTRO DO FRAME")
            '''Chama a função da classe que coleta os entrantes, para assim coletar os processos que não aparecem na 
            coleta de entrates por data de cadastro'''
            if self.bool_chama_funcao_coleta_processos:
                self.coleta_todos_os_processos()
                return -1

            print("SLEEP PARA TESTE DA COLETA DOS PROCESSOS")
            aux___ = self.busca_todos_processos()
            return aux___
        except Exception as ERRO:
            print("ERRO: ", ERRO)
            print("ERRO NA COLETA DE ANDAMENTOS!")
            return self.inicio

    def execute_busca_andamentos(self):
        cont = 0
        while cont < 10:

            aux = self.execute_busca_andamentos_()
            if aux == -1:
                break

            try:
                self.navegador.close()
            except:
                pass

            self.navegador = cria_driver()
            self.navegador.get(self.site)
            print("-====================================+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("POSIÇÃO QUE PAROU ANTES DO ERRO: ", aux)
            self.inicio = aux
            print("REINICIANDO A VARREDURA, AGR COM O LIMITE: ", self.inicio, self.fim)
            cont += 1

        try:
            self.navegador.close()
        except:
            pass

