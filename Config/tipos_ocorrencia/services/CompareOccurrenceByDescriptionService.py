from Config.tipos_ocorrencia.services.Regex import RegexService
from pathlib import Path
import pandas as pd

class ComparaOcorrencias:
    def __init__(self, sentences = [], planilha = []):
        self.sentences = sentences
        # self.sqlite_ocorrencia_conn = connect_sqlite('Config\\tipos_ocorrencia\\ocorrencias_processum.db')

    def execute(self, tipo, esp):
        for description in (esp, tipo):
            if description is None or description.strip() == '':
                continue
            processedSentence = self.processSentence(description)
            processedSentence = processedSentence.replace('{','').replace('}','')
            # Checar se encaixa em alguma expressão regular
            regex = RegexService()

            # regexSentence = regex.execute(description)
            # # Caso a description se encaixe na regex então procuramos a regex na planilha e retornamos os dados
            # if regexSentence:
            #     processedSentence = regexSentence

            # Loop para andar entre os SISTEMAS
            for platform in range(7):
                # Preenche a planilha com o sistema correto
                self.collectSentences(platform)

                # Loop para percorrer todas as frases da planilha e comparar com a frase recebida
                listPosition = 0
                found = False
                for item in self.sentences:
                    count = 0
                    dados = []
                    # Garante o padrão para comparação das descrições
                    item = self.processSentence(item)
                    # print('item',item)
                    if item.find('${') > -1:
                        if regex.check_reg(item, processedSentence) is not None:
                            found = True

                    else:
                        # tamanho diferente já elimina a frase
                        if len(item) == len(processedSentence):
                            # varre caractere por caractere para validar a igualdade
                            for iterator in processedSentence:
                                if iterator != item[count]: break
                                count = count + 1
                            # count == len(frase) significa que a frase foi encontrada
                            if count == len(processedSentence):
                                found = True

                    if found:
                        dados = {'ocorrencia': [self.planilha['TIPO DE OCORRêNCIA'][listPosition].strip(), self.planilha['ESP. TIPO DE OCORRÊNCIA'][listPosition].strip()],
                                 'arquivo': [self.planilha['DOCUMENTO - ESPECIFICAÇÃO DO TIPO'][listPosition].strip(), self.planilha['OBSERVÇÃO'][listPosition].strip()],
                                 'alternativo': [self.planilha['TIPO ALTERNATIVO'][listPosition].strip(), self.planilha['ESP ALTERNATIVO'][listPosition].strip()],
                                 'original': description
                                 }
                        result = False
                        if dados['ocorrencia'][0] != '' and dados['ocorrencia'][0] != '-':
                            result = dados

                        return result

                    listPosition = listPosition + 1
        # Retorna 'False' caso não tenha encontrado a frase na planilha
        return False

    # Coleta os dados da planilha
    def collectSentences(self, platform): # Colocar o caminho da pasta abaixo...
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.planilha = pd.read_excel(str(BASE_DIR)+r"\public\LISTA_GERAL_-_ANDAMENTOS_-_OCORRENCIAS.xlsx", sheet_name=platform)
        # self.planilha = pd.read_excel(r"E:\ESTAGIO\PYTHON\Tools\utils\public\LISTA_GERAL_-_ANDAMENTOS_-_OCORRENCIAS.xlsx", sheet_name=platform)
        self.sentences = self.planilha['Descrição']

    # Deixa a frase apenas com caracteres maiusculos e sem espaços nas laterais     
    def processSentence(self, sentence):
        if sentence[-1] == '.':
            sentence = sentence[:-1]
        return sentence.upper().strip().replace('  ',' ')