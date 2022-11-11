import os
import pandas as pd
from random import *
from time import sleep
from datetime import date
from datetime import datetime, timedelta
from selenium import webdriver
from unicodedata import normalize
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from Database.connDatabase import SQL
from classe_dados_processo import Classe_de_dados_processo


class buscar_processos_processum:
    def __init__(self, site='https://ww3.vivo-base.com.br/processumweb/principalPadrao.jsf', user='', password='',
                 base_dados='', tipo_data_busca=''):
        self.IPs = {
            "bec": '45.178.181.49',
            "rek": '45.178.181.49',
            "ede": '45.178.181.49',
            "titanium_dev": '201.47.170.196'
        }
        # NESSE LISTA SERÃO GUARDADOS OS OBJETOS QUE EME TEORIA SERIA INSERIDOS NA BASE, PARA CASO ACONTEÇA ALGUM ERRO, OS VALORES DOS MESMO SEJAM CONFERIDOS
        self.objs_para_conferir_dps = []
        self.user = user
        self.password = password
        self.base_dados = base_dados
        self.tipo_data_busca = tipo_data_busca
        self.site = site
        self.lista_de_logs = []
        self.chrome_options = webdriver.ChromeOptions()
        self.path_download_prov = os.path.abspath('C:/Users/bighero/Desktop/PH_Bots/Bots/BotVivo/Downloads/' +
                                                  self.tipo_data_busca.replace(" ", "_") + '/' + str(hex(id(self))) + "_" + base_dados)
        os.makedirs(str(self.path_download_prov), 0o777,False)
        print("CAMINHO DA PASTA DOWNLOAD: ", str(self.path_download_prov))
        self.chrome_options.add_experimental_option("prefs",
                                                    {"download.default_directory": r"" + str(self.path_download_prov),
                                                     "download.prompt_for_download": False,
                                                     "download.directory_upgrade": True,
                                                     "safebrowsing.enabled": False,
                                                     "safebrowsing_for_trusted_sources_enabled": False,
                                                     'download.extensions_to_open': 'msg',
                                                     "plugins.always_open_pdf_externally": True})

    def set_lista_log(self, lista):
        self.lista_de_logs = lista

    # FAZ A CONEXÃO COM O BANCO DE DADOS
    def sql_test(self):
        try:
            access = [self.IPs[self.base_dados], 'sa', 'BEC@db521', self.base_dados]
            print("LIISTA DE INFORMAÇÕES PARA CONECTAR COM O BANCO: ", access)
            return SQL(access[0], access[1], access[2], access[3])
        except:
            print("ERRO DE CONEXÃO COM A BASE DE DADOS")

    # RETIRAR QUALQUER FORMA DE ACENTUAÇÃO
    def remove_accents(self, txt):
        return normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')

    # TRATAR ESTADOS
    def tratar_estado(self, estado):
        estado = self.remove_accents(estado)
        estado.upper()
        estado_sigla = {
            'ACRE': 'AC', 'ALAGOAS': 'AL',
            'AMAPA': 'AP', 'AMAZONAS': 'AM',
            'BAHIA': 'BA', 'DISTRITO FEDERAL': 'DF',
            'CEARA': 'CE', 'ESPIRITO SANTO': 'ES',
            'GOIAS': 'GO', 'MARANHAO': 'MA',
            'MATO GROSSO': 'MT', 'MATO GROSSO DO SUL': 'MS',
            'MINAS GERAIS': 'MG', 'PARAIBA': 'PB',
            'PARANA': 'PR', 'PARA': 'PA',
            'PERNAMBUCO': 'PE', 'PIAUI': 'PI',
            'RIO DE JANEIRO': 'RJ', 'RIO GRANDE DO NORTE': 'RN',
            'RIO GRANDE DO SUL': 'RS', 'RONDONIA': 'RO',
            'RORAIMA': 'RR', 'SANTA CATARINA': 'SC',
            'SAO PAULO': 'SP', 'SERGIPE': 'SE', 'TOCANTINS': 'TO', 'BRASILIA': 'DF'
        }
        return estado_sigla[estado]

    # FAZ A ALTERAÇÃO DO NOME DA PLANILHA, PARA UM NOME GENERICO, PARA FACILITAR O ACESSO
    def altera_nome_planilha(self, caminho):
        print("Caminho: ", caminho)
        # ACESSA O DIRETORIO DOWNLOADS, QUE É ONDE A PLANILHA SE ENCONTRA
        diretorio = os.listdir(caminho)
        os.chdir(caminho)
        # PERCORRE A LISTA DE ELEMENTOS CONTIDOS NO DIRETORIO DOWNLOADS PARA ENCONTRAR A PLANILHA
        for dir in diretorio:
            auxiliar = (dir[0] + dir[1] + dir[2] + dir[3] + dir[4])
            if auxiliar == 'temp-':
                remover_espaco_nome_tipo_data = self.tipo_data_busca.replace(" ", "_")
                comando_rename_pronto = 'rename ' + str(dir) + ' planilha' + remover_espaco_nome_tipo_data + '.xls'
                print("comando_rename_pronto: ", comando_rename_pronto)
                # ASSIM QUE ENCONTRAR, RENOMEIA PARA UM NOME GENERICO PARA FACILITAR O USO, E PARA O FOR DE BUSCA
                os.system(comando_rename_pronto)
                return 1
        return 0

    # ------------------------------------- FUNÇÕES NOVAS, MUDANÇA NA CONSULTA ----------------------------------------------------------------------------------

    # FAZ A BUSCA EM UMA LISTA QUE TEM QUE ESTAR PREVIAMENTE ORDENADA, RETORNA SE O VALOR ESTÁ CONTIDO NA LISTA EM UMA COMPLEXIDADE DE LOG N NA BASE 2.
    def busca_binaria(self, lista_numeros, ini, fim, chave):
        meio = int(((ini + fim) / 2))
        if lista_numeros[meio] == chave:
            return True
        if ini >= fim:
            return False
        if chave > lista_numeros[meio]:
            return self.busca_binaria(lista_numeros, meio + 1, fim, chave)
        return self.busca_binaria(lista_numeros, ini, meio, chave)

    # REMOVE OS CARACTERES QUE VEM JUNTO COM OS DADOS BUSCADOS NA BASE
    def remove_caracter(self, numero):
        auxiliar = str(numero)
        auxiliar = auxiliar.replace("(", "")
        auxiliar = auxiliar.replace(")", "")
        auxiliar = auxiliar.replace("'", "")
        auxiliar = auxiliar.replace(",", "")
        return auxiliar

    # RECEBE UMA LISTA DE PROCESSOS QUE FORAM BUSCADOS NA BASE DE DADOS, TRATA A LISTA E RETORNA ELA
    def trata_lista_processos_buscados(self, lista_processos_buscados):
        lista_processos_tratados = []
        for pos in lista_processos_buscados:
            lista_processos_tratados.append(self.remove_caracter(pos))
        return lista_processos_tratados

    # -------------------------------------------------------------------------------------------------------------------------------------------------------------

    # FAZ A CONSULTA AO BANCO DE DADOS PELO NUMERO DE PROCESSO
    def consulta_banco_de_dados(self, lista_de_objetos_com_os_dados_dos_processos):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!CONECTANDO COM O BANCO DE DADOS...!!!!!!!!!!!!!!!!!!!!!!!!!")
        conexao_banco = self.sql_test()
        lista_com_processos_que_serao_inseridos = []
        lista_objetos_processos_ja_existem_na_base = []
        numero_processo_antes_insercao = conexao_banco.quantidade_processo()  # PEGA A QUANTIDADE DE PROCESSOS ANTES DA INSERÇÃO DOS PROCESSOS NOVOS
        lista_sequencias_que_existem_na_base = conexao_banco.busca_que_ja_existem_na_base(
            lista_de_objetos_com_os_dados_dos_processos)  # PEGA A LISTA COM OS PROCESSOS QUE JÁ EXISTEM NA BASE
        lista_sequencias_que_existem_na_base = self.trata_lista_processos_buscados(
            lista_sequencias_que_existem_na_base)  # TRATA A LISTA DE PROCESSOS QUE FOI BUSCADA, REMOVENDOOS CARACTERES INDEJADOS QUE VIERAM JUNTO
        lista_sequencias_que_existem_na_base.sort()  # ORDENA A LISTA, PQ PARA A BUSCA BINARIA, A LISTA TEM QUE ESTAR NECESSARIAMENTE ORDENADA
        tamanho_lista_sequenciais_existem_na_base = len(lista_sequencias_que_existem_na_base)

        tamanho_lista_com_todos_objetos = len(lista_de_objetos_com_os_dados_dos_processos)
        print(
            "!!!!!!!!!!!!!!!!!!!!!!!!!INICIANDO A CONSULTA DOS PROCESSOS NO BANCO DE DADOS...!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!TOTAL DE SEQUENCIAIS A SEREM CONSULTADOS: ", tamanho_lista_com_todos_objetos,
              '!!!!!!!!!!!!!!!!!!!!!!!!!')
        print("!!!!!!!!!!!!!!!!!! DOS ", tamanho_lista_com_todos_objetos, ", ",
              tamanho_lista_sequenciais_existem_na_base, "JÁ EXISTEM NA BASE!!!!!!!!!!!!!!!!!!!!!!!")

        # USA A BUSCA BINARIA PARA SEPARAR OS PROCESSOS QUE NÃO EXISTEM, PARA QUE ELE POSSAM SER INSERIDOS
        for obj in lista_de_objetos_com_os_dados_dos_processos:
            # SE A FUNÇÃO RETORNAR FALSO, É PQ NÃO ACHOU ESSE NUMERO DE SEQUENCIAL NA LISTA DE SEQUENCIAL QUE EXISTEM NA BASE
            if not self.busca_binaria(lista_sequencias_que_existem_na_base, 0,
                                      tamanho_lista_sequenciais_existem_na_base - 1, obj.prc_sequencial):
                lista_com_processos_que_serao_inseridos.append(obj)
                # print('Base: ' + self.base_dados + ' - numero processo -> ', obj.prc_numero)
                # coloca em uma lista, para de algum erro referente ao tamanho, possa ser verificado dps, qual foi a string que ocasionou o erro
                self.objs_para_conferir_dps.append(obj)
            else:
                lista_objetos_processos_ja_existem_na_base.append(obj)
        print(
            "!!!!!!!!!!!!!!!!!!!!!!!!!FIM DA CONSULTA NA BASE DE DADOS!!!!!!!!!!!!!!!!!!!!!!!!!\n!!!!!!!!!!!!!!!!!!!!!!!!!LISTA COM OS OBJETOS DOS PROCESSOS QUE SERÃO INSERIDOS PRONTA!!!!!!!!!!!!!!!!!!!!!!!!!\n!!!!!!!!!!!!!!!!!!!!!!!!!COMEÇANDO A INSERÇÃO DOS PROCESSOS...!!!!!!!!!!!!!!!!!!!!!!!!!")

        # ATUALIZA O CAMPO PRC_SITUACAO DOS PROCESSOS QUE JÁ EXISTEM NA BASE
        conexao_banco.update_prc_situacao(lista_objetos_processos_ja_existem_na_base)

        if self.base_dados == 'titanium_dev':
            conexao_banco.insere_dados_processum_titanium_dev(lista_com_processos_que_serao_inseridos)
        else:
            conexao_banco.insere_dados_processum_Juris_Ede_Rek(lista_com_processos_que_serao_inseridos)

        log_final = ''
        log = '----------------------------------------------------------------------\n'
        log += '--------------------------' + self.tipo_data_busca + '-------------------------\n'
        log += '----------------------------------------------------------------------\n'
        log += "!!!!![USUARIO = " + str(self.user) + " --- BANCO DE DADOS = " + str(self.base_dados) + "]!!!!!\n"
        qunt_process = conexao_banco.quantidade_processo()
        log += "!!!!![Antes da inserção = " + str(numero_processo_antes_insercao) + " Depois da inserção = " + str(
            qunt_process) + "]!!!!!\n"
        log += "QUANTIDADE DE PROCESSOS NOVOS = {" + str(qunt_process - numero_processo_antes_insercao) + "}\n"
        log += "!!!!![Quantidades processos que passaram por update: " + str(
            len(lista_objetos_processos_ja_existem_na_base)) + "]!!!!!\n"
        log += '----------------------------------------------------------------------\n'

        print(log)
        self.lista_de_logs.append(log)

    # VERFICA QUAL É A CARTEIRA, E RETORNA O VALOR ADEQUADO
    def verifica_carteira(self, sequencial):
        A = str(sequencial)
        aux_seq = ''
        tam = len(A)
        tam -= 1
        cont = 0
        while tam > 0 and cont < 2:
            B = A[tam]
            aux_seq = B + aux_seq
            if B == '-':
                cont += 1
            tam -= 1

        if aux_seq == '--148':
            return 2
        return 1

    # FAZ O TRATAMENTO NA PARTE ATIVA, PARA EVITAR NUMEROS GRANDES
    def trata_parte_ativa(self, parte_ativa):
        if parte_ativa is None:
            return parte_ativa
        aux_ativa = ''
        tam = len(parte_ativa)
        for i in range(tam):
            if parte_ativa[i] == ',':
                break
            aux_ativa += parte_ativa[i]
        aux_ativa = aux_ativa.replace("'", " ")
        return aux_ativa

    def trata_numero_processo_cadastrado_errado(self, numero):
        '''
            Caso o numero do processo tenha mais de 20 caracteres, ele deve ter sido cadastrado errado. Quando isso ocorre, o numero completo
        deve ser salvo no campo prc_numero_processum(pois ele é maior que o campo prc_numero), e esse ele possuir algum espaço, ele tem que ser partido no espaço,
        e então a maiar parte pega e salva no campo prc_numero, caso ele não tenha nenhum espaço, ele deve ser apenas partido no meio, e metade salva no campo prc_numero.
        '''
        maior = ''
        if " " in numero:
            auxiliar = numero.split(" ")
            for i in auxiliar:
                if len(maior) < len(i):
                    maior = i
        else:
            maior = numero[0:int(len(numero) / 2)]
        return maior

    # MONTA AS LISTAS COM OS DADOS OBTIDOS DA PLANILHA
    def monta_listas(self, caminho):
        # O DOWNLOAD DA PLANILHA FOI FEITO COM SUCESSO, ENTÃO O NAVAGADOR JÁ PODE SER FECHADO
        self.navegador.close()
        print("Navagador fechado, començando a busca!")
        sleep(2)

        # ABRIR A PLANILHA EXCEL QUE CONTEM OS DADOS
        arruma_espaco_nome_tipo_data = self.tipo_data_busca.replace(" ", "_")
        caminho_abrir_planilha_pronto = caminho + "/planilha" + arruma_espaco_nome_tipo_data + ".xls"
        print("caminho para abrir planilha pronto:\n", caminho_abrir_planilha_pronto)
        planilha = pd.read_excel(caminho_abrir_planilha_pronto)

        # SEPARA OS DADOS PRESENTES DA PLANILHA
        lista_de_estados = list(planilha['ESTADO'])
        lista_de_sequencial = list(planilha['PROCESSO SEQ Nº'])
        lista_de_numeros = list(planilha['PROCESSO 1ª INSTANCIA Nº'])
        lista_parte_ativa = list(planilha['NOME AUTOR'])
        # lista_parte_passiva = list(planilha['NOME REU'])
        lista_de_cadastro = list(planilha['DATA CADASTRO'])
        lista_de_objetos1 = list(planilha['OBJETO ACAO'])
        lista_de_objetos2 = list(planilha['ESP OBJETO ACAO'])
        lista_de_objetos3 = list(planilha['DET ESP OBJETO ACAO'])
        lista_de_carteiras = list(planilha['EMPRESA'])
        lista_de_areas = list(planilha['DIVISAO RESPONSAVEL'])
        lista_comarca = list(planilha['COMARCA'])
        lista_escritorio_contratado = list(planilha['ESCRITORIO CONTRATADO'])
        lista_situacao = list(planilha['SITUAÇÃO'])

        tam = len(lista_de_numeros)
        lista_de_objetos_dados_processo = []
        # MONTA A LISTA DE OBJETOS, COM OS DADOS DO PROCESSO, CASO NÃO TENHA NADA NA CELULA DA PLANILHA, ELA RETORNA NAN, NESSE CASO O TERNARIO TROCA O NAN POR NONE
        for i in range(tam):
            situacao = str(lista_situacao[i]) if str(lista_situacao[i]) != 'nan' else None
            numero_processum = ''
            estado = str(lista_de_estados[i]) if str(lista_de_estados[i]) != 'nan' else None
            sequencial = str(lista_de_sequencial[i]) if str(lista_de_sequencial[i]) != 'nan' else None
            numero = str(lista_de_numeros[i]) if str(lista_de_numeros[i]) != 'nan' else None
            estado = str(lista_de_estados[i]) if str(lista_de_estados[i]) != 'nan' else None
            parte_ativa = str(lista_parte_ativa[i]) if str(lista_parte_ativa[i]) != 'nan' else None
            # parte_passiva = str(lista_parte_passiva[i]) if str(lista_parte_passiva[i]) != 'nan' else None
            cadastro = str(lista_de_cadastro[i]) if str(lista_de_cadastro[i]) != 'nan' else None
            obj1 = str(lista_de_objetos1[i]) if str(lista_de_objetos1[i]) != 'nan' else None
            obj2 = str(lista_de_objetos2[i]) if str(lista_de_objetos2[i]) != 'nan' else None
            obj3 = str(lista_de_objetos3[i]) if str(lista_de_objetos3[i]) != 'nan' else None
            carteira = str(lista_de_carteiras[i]) if str(lista_de_carteiras[i]) != 'nan' else None
            area = str(lista_de_areas[i]) if str(lista_de_areas[i]) != 'nan' else None
            comarca = str(lista_comarca[i]) if str(lista_comarca[i]) != 'nan' else None
            comarca = comarca.replace("'", " ")
            # FAZ O TRATAMENTO NA PARTE ATIVA, PARA EVITAR NUMEROS GRANDES

            parte_ativa = self.trata_parte_ativa(parte_ativa)

            # TRUNCAR A PARTE ATIVA, QUE É EQUIVALENTE AO PRC_AUTOR
            if "REPRESENTADO" in parte_ativa:
                x = parte_ativa.split("REPRESENTADO")
                parte_ativa = x[0]

            numero_processum = numero
            if len(numero) > 20:
                print("UM NUMERO DE PROCESSO COM O MAIS DE 20 NUMEROS!!!!")
                numero = self.trata_numero_processo_cadastrado_errado(numero)

            # VERFICA QUAL É A AREA, E ATRIBUI O VALOR ADEQUADO
            area = 1 if area == 'CONSUMIDOR NACIONAL' else 2
            # VERFICA QUAL É A CARTEIRA, E ATRIBUI O VALOR ADEQUADO
            carteira = self.verifica_carteira(sequencial)
            # TRATA O NOME DO ESTADO, PARA DEIXAR APENAS A SILGA REFENTE AO NOME DAQUELE ESTADO
            estado = self.tratar_estado(estado)
            if self.base_dados == 'ede':
                aux = list(lista_escritorio_contratado[i].split("-"))
                if estado != 'BA':
                    print("ESTADO OU ESCRITORIO ERRADO!! ESTADO: ", estado, " ESCRITORIO: ", aux)
                    continue
                elif aux[0] != 'EDE':
                    print("ESTADO OU ESCRITORIO ERRADO!! ESTADO: ", estado, " ESCRITORIO: ", aux)
                    continue

            cadastro = datetime.strptime(cadastro, '%d/%m/%Y %H:%M')

            if sequencial == '3845/2020--50':
                print("ENCONTROUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUU")

            sequencial = sequencial.strip()
            if self.base_dados == 'titanium_dev':

                objeto_pronto = Classe_de_dados_processo(prc_numero=str(numero), prc_carteira=carteira,
                                                         prc_estado=estado,
                                                         prc_objeto1=obj1, prc_objeto2=obj2, prc_objeto3=obj3,
                                                         prc_data_cadastro=cadastro,
                                                         prc_objeto4='NULL', prc_area=str(area),
                                                         prc_penhora='NULL', prc_responsavel='NULL',
                                                         prc_sequencial=sequencial, prc_empresa=1,
                                                         prc_situacao=situacao)
            else:
                objeto_pronto = Classe_de_dados_processo(prc_numero=str(numero),
                                                         prc_numero_processum=str(numero_processum),
                                                         prc_carteira=carteira
                                                         , prc_estado=estado, prc_autor=parte_ativa,
                                                         prc_objeto1=obj1,
                                                         prc_objeto2=obj2, prc_objeto3=obj3,
                                                         prc_data_cadastro=cadastro,
                                                         prc_objeto4='NULL', prc_area=str(area),
                                                         prc_penhora='NULL', prc_responsavel='NULL',
                                                         prc_sequencial=sequencial, prc_data=cadastro,
                                                         prc_comarca=comarca, prc_situacao=situacao)

            lista_de_objetos_dados_processo.append(objeto_pronto)

        # CHAMA A FUNÇÃO QUE VAI CONSULTAR E INSERIR NO BANCO DE DADOS
        self.consulta_banco_de_dados(lista_de_objetos_dados_processo)


    def login(self, usuario=None, senha=None, base=None):
        # FAZ O LOGIN
        self.driver.find_element_by_id("username").send_keys(usuario)
        self.driver.find_element_by_id("password").send_keys(senha)
        self.driver.find_element_by_id("password").send_keys(Keys.ENTER)
        # kaio = input('kaiooooooooooooo')
        return True

    # VAI SELECIONAR O CAMPO BAHIA, PARA RODAR AAUXILIAR NA INSERÇÃO NA BASE EDE
    def seleciona_campo_estado_bahia(self):
        data_de_final = WebDriverWait(self.navegador, 2)
        data_de_final.until(EC.visibility_of_element_located((By.ID, "fPesquisa:estado")))
        campo_estado = Select(self.navegador.find_element_by_id('fPesquisa:estado'))
        campo_estado.select_by_visible_text('BAHIA')

    # RETORNA A DATA ATUAL, E A DE 7 DIAS ATRÁS NO FORMATO STR
    def datas(self, retroativo):
        data_atual = str(datetime.strftime(date.today() + timedelta(7), '%d%m%Y'))
        dia_inicial = ""
        dia_inicial = str(datetime.strftime(datetime.now() - timedelta(retroativo), '%d%m%Y'))
        return data_atual, dia_inicial

    def preencher_datas(self, retroativo):
        # CHAMA FUNÇÃO DATAS, QUE IRA RETORNAR A DATA DO DIA ANTERIOR E A DATA ATUAL
        intervalo_de_datas = self.datas(retroativo)
        print("\nDataini: ", intervalo_de_datas[1], " DataFim: ", intervalo_de_datas[0], "\n")

        # PREENCHE O CAMPO DE DATA
        cont = 0
        data_de_inicio = WebDriverWait(self.navegador, 5)
        data_de_inicio.until(EC.visibility_of_element_located((By.ID, "fPesquisa:dataInicial")))
        # FAZ 3 TENTATIVAS DE PREENCHIMENTO DO CAMPO DE DATA INICAL
        while cont < 3:
            input_dataInicio = self.navegador.find_element_by_id('fPesquisa:dataInicial')  # intervalo_de_datas[1]
            ActionChains(self.navegador).move_to_element(input_dataInicio).click().send_keys(
                intervalo_de_datas[1]).perform()
            sleep(1)
            cont += 1

        data_de_final = WebDriverWait(self.navegador, 5)
        data_de_final.until(EC.visibility_of_element_located((By.ID, "fPesquisa:dataFinal")))
        input_dataFinal = self.navegador.find_element_by_id("fPesquisa:dataFinal")  # intervalo_de_datas[0]
        ActionChains(self.navegador).move_to_element(input_dataFinal).click().send_keys(intervalo_de_datas[0]).perform()
        # FIM DO PREENCHIMENTO DE DATAS

    # SELECIONA A OPÇÃO FILTRO AVANÇADO E A OPÇÃO CADASTRAMENTO
    def busca_processo(self):
        # kaio = input('kaiooooooooooooo')
        self.navegador.get('https://ww3.vivo-base.com.br/processumweb/modulo/processo/filtro.jsf')
        filtro_avançado = self.navegador.find_element_by_id('fPesquisa:lblBtMudarFiltro')
        filtro_avançado.click()

        # SELECIONA A OPÇÃO CADASTRAMENTO
        opcoes = Select(self.navegador.find_element_by_id('fPesquisa:datas'))
        opcoes.select_by_visible_text(self.tipo_data_busca)

        # CASO ESTEJA INSERINDO NA BASE EDE, CHAMA A FUNÇÃO PARA MARCAR BAHIA
        if self.base_dados == 'ede':
            self.seleciona_campo_estado_bahia()

    def seleciona_ativo(self):
        # SELECIONA A OPÇÃO ATIVO
        situacao = Select(self.navegador.find_element_by_id('fPesquisa:situacao'))
        situacao.select_by_visible_text('Ativo')

    # CLICA EM PESQUISAR, E DPS QUE A PAGINA CARREGA CLICA EM EXPORTAR EXCEL
    def clica_em_pesquisar_e_exportarExcel(self):
        print("CLICA NO BOTÃO DE PESQUISAR!")
        data_de_final = WebDriverWait(self.navegador, 5)
        data_de_final.until(EC.visibility_of_element_located((By.ID, "fPesquisa:_idJsp224")))
        pesquisar = self.navegador.find_element_by_id('fPesquisa:_idJsp224')
        pesquisar.click()
        self.navegador.execute_script("window.scrollTo(0,100)")
        print("CLICA NO BOTÃO DE EXPORTAR EXCEL!")
        xpath = '/html/body[2]/form[2]/table[2]/tbody/tr/td[1]/a'
        WebDriverWait(self.navegador, 10).until(EC.visibility_of_element_located((By.ID, 'fPesquisa:_idJsp245')))
        exportar_exel = self.navegador.find_element_by_id('fPesquisa:_idJsp245')
        exportar_exel.click()

    def finaliza_download_planilha(self):
        # CLICA EM DADOS DO PROCESSO PARA TERMINAR O DOWNLOAD DA PLANILHA
        cont = 0
        while cont < 3:
            try:
                iframe = self.navegador.find_element_by_id("__jeniaPopupFrameTarget")
                self.navegador.switch_to.frame(iframe)
                wait = WebDriverWait(self.navegador, 5 * 60)
                wait.until(EC.visibility_of_element_located(
                    (By.XPATH, '//*[@id="body:fExportar:pPreDefinido:itemPreDefinidoInteger"]/optgroup[9]/option')))
                detalhes_dos_processos = self.navegador.find_element_by_xpath(
                    '//*[@id="body:fExportar:pPreDefinido:itemPreDefinidoInteger"]/optgroup[9]/option')
                print(detalhes_dos_processos.click())
                break
            except:
                wait = WebDriverWait(self.navegador, 5 * 60)
                wait.until(EC.visibility_of_element_located(
                    (By.XPATH, '//*[@id="body:fExportar:pPreDefinido:itemPreDefinidoInteger"]/optgroup[9]/option')))
                detalhes_dos_processos = self.navegador.find_element_by_xpath(
                    '//*[@id="body:fExportar:pPreDefinido:itemPreDefinidoInteger"]/optgroup[9]/option')
                print(detalhes_dos_processos.click())
        # TERMINA A PARTE DE DOWLOAD DA PLANILHA
        print("RODANDO SLEEP, PARA GARATIR DOWNLOD DA PLANILHA")
        sleep(5)
        print("TERMINOU O SLEEP DE ESPERA PARA O DOWNLOAD DA PLANILHA")

    # ACESSA A PLANILHA BAIXADA, E CHAMA A FUNÇÃO QUE MONTA A LISTA DE OBJETO COM OS DADOS DA PLANILHA,
    # E A FUNÇÃO QUE MONTA OS DADOS, APÓS TERMINAR DE MONTAR, CHAMA A FUNÇÃO QUE CONSULTA
    def acessa_planilha_e_monta_lista(self, caminho):
        sleep(10)
        # SE "altera_nome_planilha" retornar 1 é pq conseguiu acessar a planilha
        cont = 0
        while cont < 10:
            resultado_abrir_arquivo = self.altera_nome_planilha(caminho)
            if resultado_abrir_arquivo:
                # CHAMA A FUNÇÃO QUE MONTA AS LISTAS, E A FUNÇÃO MONTA LISTAS CHAMA A FUNÇÃO DE CONSULTA AO BANCO DE DADOS
                self.monta_listas(caminho)
                print("###################################### ACHOU A PLANILHA ###############################")
                break
            else:
                print("NÃO ACHOU A PLANILHA!!!")
                print("SERÁ FEITA MAIS UMA TENTATIVA DE ENCONTRAR A PLANILHA!")
                sleep(10)

            cont += 1

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ATUALIZAÇÃO DO BOT DIA 21-01-2020, BUSCAR POR DATA OCORRENCIA !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    def monta_listas_data_ocorrencia(self, caminho):
        # O DOWNLOAD DA PLANILHA FOI FEITO COM SUCESSO, ENTÃO O NAVAGADOR JÁ PODE SER FECHADO
        print("Navagador fechado, començando a busca!")
        sleep(2)
        # ABRIR A PLANILHA EXCEL QUE CONTEM OS DADOS
        arruma_espaco_nome_tipo_data = self.tipo_data_busca.replace(" ", "_")
        caminho_abrir_planilha_pronto = caminho + "/planilha" + arruma_espaco_nome_tipo_data + ".xls"
        print("caminho para abrir planilha pronto:\n", caminho_abrir_planilha_pronto)
        planilha = pd.read_excel(caminho_abrir_planilha_pronto)

        # SEPARA OS DADOS PRESENTES DA PLANILHA
        lista_de_estados = list(planilha['ESTADO'])
        lista_de_sequencial_aux = list(planilha['PROCESSO SEQ Nº'])
        lista_escritorio_contratado = list(planilha['ESCRITORIO CONTRATADO'])
        # lista_situacao = list(planilha['SITUAÇÃO'])

        tam = len(lista_de_sequencial_aux)
        lista_de_sequencial = []
        # MONTA A LISTA DE OBJETOS, COM OS DADOS DO PROCESSO, CASO NÃO TENHA NADA NA CELULA DA PLANILHA, ELA RETORNA NAN, NESSE CASO O TERNARIO TROCA O NAN POR NONE
        for i in range(tam):
            # if lista_situacao[i] == 'Arquivo Morto':
            #     print("MORTO, PASSANDO PARA O PROXIMO!")
            #     continue

            # TRATA OS DADOS
            # situacao = str(lista_situacao[i]) if str(lista_situacao[i]) != 'nan' else None
            sequencial = str(lista_de_sequencial_aux[i]) if str(lista_de_sequencial_aux[i]) != 'nan' else None
            estado = str(lista_de_estados[i]) if str(lista_de_estados[i]) != 'nan' else None

            if self.base_dados == 'ede':
                aux = list(lista_escritorio_contratado[i].split("-"))
                if estado != 'BAHIA':
                    print("ESTADO OU ESCRITORIO ERRADO!! ESTADO: ", estado, " ESCRITORIO: ", aux)
                    continue
                elif aux[0] != 'EDE':
                    print("ESTADO OU ESCRITORIO ERRADO!! ESTADO: ", estado, " ESCRITORIO: ", aux)
                    continue

            # LISTAS CORRETAS
            sequencial = sequencial.strip()
            lista_de_sequencial.append(sequencial)
        try:
            # FAZ A CONEÇÃO COM O BANCO DE DADOS, E CHAMA A FUNÇÃO DE CONSULTA
            conexao = self.sql_test()
            conexao.update_prc_update1(lista_de_sequencial)
            print("UPDATE FEITO COM SUCESSO!")
            print("FOI FEITO O UPDATE PARA: ", len(lista_de_sequencial), " PROCESSOS!!")
        except:
            print("!!!!!!!!!!!!!!!!!ERRO NO UPDATE!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    # ------------------------------------------------------------
    def coleta_maiores_strings(self):
        maior_prc_numero = ''
        maior_prc_autor = ''
        maior_prc_objeto1 = ''
        maior_prc_objeto2 = ''
        maior_prc_objeto3 = ''
        maior_prc_numero_processum = ''
        maior_prc_comarca = ''

        for obj in self.objs_para_conferir_dps:
            if len(maior_prc_numero) < len(obj.prc_numero):
                maior_prc_numero = obj.prc_numero
            if len(maior_prc_autor) < len(obj.prc_autor):
                maior_prc_autor = obj.prc_autor
            if len(maior_prc_objeto1) < len(obj.prc_objeto1):
                maior_prc_objeto1 = obj.prc_objeto1
            if len(maior_prc_objeto2) < len(obj.prc_objeto2):
                maior_prc_objeto2 = obj.prc_objeto2
            if len(maior_prc_objeto3) < len(obj.prc_objeto3):
                maior_prc_objeto3 = obj.prc_objeto3
            if len(maior_prc_numero_processum) < len(obj.prc_numero_processum):
                maior_prc_numero_processum = obj.prc_numero_processum
            if len(maior_prc_comarca) < len(obj.prc_comarca):
                maior_prc_comarca = obj.prc_comarca

        relatorio_maiores_strings = "----------------------MAIORES STRINGS NOS RESPECTIVOS CAMPOS-----------------------\n"
        relatorio_maiores_strings += "!!! PRC_NUMERO: " + maior_prc_numero + "!!!\n"
        relatorio_maiores_strings += "!!! PRC_AUTOR: " + maior_prc_autor + "!!!\n"
        relatorio_maiores_strings += "!!! PRC_OBJETO1: " + maior_prc_objeto1 + "!!!\n"
        relatorio_maiores_strings += "!!! PRC_OBJETO2: " + maior_prc_objeto2 + "!!!\n"
        relatorio_maiores_strings += "!!! PRC_OBJETO3: " + maior_prc_objeto3 + "!!!\n"
        relatorio_maiores_strings += "!!! PRC_NUMERO_PROCESSUM: " + maior_prc_numero_processum + "!!!\n"
        relatorio_maiores_strings += "!!! PRC_COMARCA: " + maior_prc_comarca + "!!!\n"
        relatorio_maiores_strings += "----------------------------------------------------------------------------------\n"
        return relatorio_maiores_strings
    # -------------------------------------------------------------
    # COMEÇA AQUI
    def executar_varredura_Cadastro_ocorrencia(self):
        try:
            self.iniciar_navegador()
            caminho = self.path_download_prov.replace('\\', '/')
            self.busca_usuario_e_senha_na_base()
            self.login()
            self.busca_processo()
            # kaio = input('kaiooooooooooooo')
            self.preencher_datas(7)
            self.clica_em_pesquisar_e_exportarExcel()
            self.finaliza_download_planilha()
            # kaio = input('kaiooooooooooooo')
            sleep(10)
            self.acessa_planilha_e_monta_lista(caminho)
            sleep(2)
            self.monta_listas_data_ocorrencia(caminho)
        except Exception as ERRO:
            print("ERRO: ", ERRO)
            log_erro = "---------------------------------------------------------------\n"
            log_erro += "!!!!!!!!!!!!!!!!!!!!!!!!!!!!ERRO!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            log_erro += "!!!!!!!!!!!!!! BANCO DE DADOS = " + self.base_dados.upper() + "!!!!!!!!!!!!!!" + "\n"
            log_erro += "!!!!!!!!!!!!!!!!!!!!! CADASTRO OCORRENCIA !!!!!!!!!!!!!!!!!!!!!\n"
            log_erro += "!!!" + str(ERRO) + "!!!\n"
            log_erro += "---------------------------------------------------------------\n"
            self.lista_de_logs.append(log_erro)
