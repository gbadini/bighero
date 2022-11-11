import os
import sys
from time import sleep
from threading import *
from argparse import ArgumentParser
import time
sys.path.append('C:\\Users\\bighero\\Desktop\\PH_Bots\\Bots\\Bots_Tedesco_TRT_TST_CPFS')
sys.path.append('C:\\Users\\bighero\\Desktop\\PH_Bots\\Bots\\Bots_Tedesco_TRT_TST_CPFS\\Controllers')
#sys.path.append('C:\\Users\\paulo\\Desktop\\PH_Bots\\Bots\\Bots_Tedesco_TRT_TST_CPFS')
#sys.path.append('C:\\Users\\paulo\\Desktop\\PH_Bots\\Bots\\Bots_Tedesco_TRT_TST_CPFS\\Controllers')
from Controllers.NewTedescoNeoEnergia import NeoEnergia
from Controllers.NewTedescoNeoEnergia import NeoEnergiaAndamentos


def retira_varridos_lista(lista):
    caminhooo = 'C:\\Users\\bighero\\Desktop\\SucessoVarredura\\'
    lista_arquivos = os.listdir(caminhooo)
    print("Quant arquivos: ", len(lista_arquivos))
    print(lista_arquivos)

    cont = 0
    for prc_id_arquivo in lista_arquivos:
        prc_id_arquivo_sem_txt = prc_id_arquivo.replace(".txt", "")
        # print("PRC_ID BUSCADO NO MOMENTO: ", prc_id_arquivo_sem_txt)
        i = 0
        tam_lista = len(lista)
        print("POSIÇÃO: ", cont, " TAM DA LISTA, QUE FOI BUSCADO NA BASE: ", tam_lista)
        while i < tam_lista:
            if str(prc_id_arquivo_sem_txt) == str(lista[i][1]):
                print("!!!!!!!!!!!!! ACHOU O PRC_ID CORRESPONDENTE, DELETANDO DA LISTA!!!!!!!!!!!!!!!")
                del (lista[i])
                break
            i += 1
        cont += 1

    return lista


def cria_lista_threads(bool_chama_funcao_coleta_processos, quant_bots):
    quantidade_bots = quant_bots
    if bool_chama_funcao_coleta_processos: # GUAMBIARRA, ATÉ ORGANIZAR COMO VIA FICA DEFINIDO ESSA VARREDURA
        quantidade_bots = 1

    lista_threads = []
    obj_aux = NeoEnergiaAndamentos(bool_chama_funcao_coleta_processos=bool_chama_funcao_coleta_processos)
    lista_com_dados_processos = obj_aux.conexao.busca_dados_nova_varredura_neo_energia()
    print("QUANTIDADE LISTA PROCESSOS ANTES: ", len(lista_com_dados_processos))
    obj_aux.navegador.close()
    # Gambiarra temporaria
    # lista_com_dados_processos = retira_varridos_lista(lista_com_dados_processos)
    print("QUANTIDADE LISTA PROCESSOS DEPOIS: ", len(lista_com_dados_processos))
    sleep(20)
    tamanho_lista_processos = len(lista_com_dados_processos)

    quant_por_bot = int(tamanho_lista_processos / quantidade_bots)
    resto = tamanho_lista_processos % quantidade_bots

    ini = 0
    fim = quant_por_bot

    print("QUANT: ", quant_por_bot, " RESTO:", resto)

    for i in range(quantidade_bots):
        # print("ini: ", ini, " fim: ", fim)
        obj = NeoEnergiaAndamentos(inicio=ini, fim=fim, lista_processos=lista_com_dados_processos, bool_chama_funcao_coleta_processos=bool_chama_funcao_coleta_processos)
        T = Thread(target=obj.execute_busca_andamentos)
        lista_threads.append(T)
        ini += quant_por_bot
        fim += quant_por_bot

    if resto != 0:
        print("inicio resto: ", tamanho_lista_processos - resto, "FIM RESTO: ", tamanho_lista_processos)
        obj = NeoEnergiaAndamentos(inicio=tamanho_lista_processos - resto, fim=tamanho_lista_processos,
                                   lista_processos=lista_com_dados_processos, bool_chama_funcao_coleta_processos=bool_chama_funcao_coleta_processos)
        T = Thread(target=obj.execute_busca_andamentos)
        lista_threads.append(T)

    return lista_threads


def  inicia_threads(lista_threads):
    for tre in lista_threads:
        tre.start()
        sleep(0.5)

    for tre in lista_threads:
        tre.join()


parser = ArgumentParser(
    prog="Bot Neo Energia",
    description="Executa a varredura para o site Neo Energia."
)

parser.add_argument('-CA', action="store_true", help="Troca para o tipo de data cadastrado")
parser.add_argument('-AND', action="store_false", help="Troca para a varredura dos acompanhamentos")
args = parser.parse_args()

tipo_data = 'criado'
if args.CA:
    tipo_data = 'cadastrado'

# tipo_data = 'cadastrado'
#

# SELECIONA SE VAI FAZER A COLETA DE ENTRANTES, OU ANDAMENTOS
entrantes = args.AND
''' Se true habilita a coleta de entrantes, dos processos que que tiveram movimentação recente, se false executa apenas
a coleta dos andamentos, dos processos que tiveram movimentação recente.'''
bool_chama_funcao_coleta_processos = True


if entrantes:
    print("======================================")
    print("     !INICIANDO VARREDURA!")
    print("     TIPO DE DATA: ", tipo_data)
    print("======================================")
    obj = NeoEnergia()
    obj.execute(tipo_data)

else:
    if bool_chama_funcao_coleta_processos:
        print("============================================================================")
        print("    INICIANDO COLETA DE ENTRANTES, PROCESSOS MOVIMENTAÇÃO RECENTE")
        print("============================================================================")
        inicioT = time.time()
        numero_bots = 10
        aux = cria_lista_threads(bool_chama_funcao_coleta_processos, numero_bots)
        inicia_threads(aux)
        print("AAAAAAAA: ", inicioT)
        print("FINALLLL: ", time.time())
        print("AAAAAAAAAA final: ", time.time() - inicioT)

    print("-----------------------------------------------------------------------")
    bool_chama_funcao_coleta_processos = False
    print("======================================")
    print("    INICIANDO COLETA DE ANDAMENTOS")
    print("======================================")
    inicioT = time.time()
    numero_bots = 17
    aux = cria_lista_threads(bool_chama_funcao_coleta_processos, numero_bots)
    inicia_threads(aux)
    print("AAAAAAAA: ", inicioT)
    print("FINALLLL: ", time.time())
    print("AAAAAAAAAA final: ", time.time() - inicioT)