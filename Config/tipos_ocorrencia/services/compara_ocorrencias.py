from Config.database import *
from Config.helpers import *
from Config.tipos_ocorrencia.services.Regex import RegexService
from Models.ocorrenciaModel import Ocorrencia
from Models.acompanhamentoModel import Acompanhamento
import json

class ComparaOcorrencias:

    def __init__(self, plataforma=1):
        sqlite_ocorrencia_conn = connect_sqlite('Config\\tipos_ocorrencia\\ocorrencias.db')
        ocrs = Ocorrencia.select_sqlite(sqlite_ocorrencia_conn)
        # print(ocrs)
        self.lista_ocorrencias = {}
        for ocr in ocrs:
            if ocr[0] is not None and ocr[0] != '':
                ocr_tipo = ocr[0]
                ocr_esp = ocr[1]
            else:
                ocr_tipo = ''
                ocr_esp = ocr[4]

            if ocr_tipo not in self.lista_ocorrencias:
                self.lista_ocorrencias[ocr_tipo] = {}

            if ocr_esp not in self.lista_ocorrencias[ocr_tipo]:
                self.lista_ocorrencias[ocr_tipo][ocr_esp] = {}

            if 'Chaves' not in self.lista_ocorrencias[ocr_tipo][ocr_esp]:
                self.lista_ocorrencias[ocr_tipo][ocr_esp]['Chaves'] = []

            self.lista_ocorrencias[ocr_tipo][ocr_esp]['Chaves'].append({'Inicio': '' if ocr[6] is None else remove_acentos(ocr[6].upper()),
                                                                        'Exata': '' if ocr[7] is None else remove_acentos(ocr[7].upper()),
                                                                        'Qualquer': self.convert_to_tuple(ocr[8]),
                                                                        'Not': self.convert_to_tuple(ocr[9])})

            self.lista_ocorrencias[ocr_tipo][ocr_esp]['Documento'] = ocr[4]
            self.lista_ocorrencias[ocr_tipo][ocr_esp]['Documento Alternativo'] = ocr[5]
            tipo_alt = ocr[2] if ocr[2] is not None and ocr[2] != '' and ocr[2] != '-' else False
            esp_alt = ocr[3] if ocr[3] is not None and ocr[3] != '' and ocr[3] != '-' else False
            self.lista_ocorrencias[ocr_tipo][ocr_esp]['Alternativa'] = (tipo_alt,esp_alt)


        self.reorder_dict()

        # for l in self.lista_ocorrencias:
        #     print(l, self.lista_ocorrencias[l])

        db = connect_db('bec')
        # print(self.execute())
        # movs = Acompanhamento.lista_movs_teste_acp(db())
        # for acp in movs:
        #     esp =  acp['acp_esp']
        #     if acp['acp_plataforma'] not in (4, 5, 6):
        #         if acp['acp_tipo'] is not None:
        #             result = re.search(r"(\d+)", acp['acp_tipo'])
        #             if result:
        #                 if result.group(0) == acp['acp_tipo']:
        #                     if acp['acp_esp'].find(acp['acp_tipo'] + ' - ') == 0:
        #                         esp = acp['acp_esp'][len(acp['acp_tipo']) + 3:].strip()
        #
        #     r = self.execute(acp['acp_tipo'], esp)
        #     # if r and r['tipo'] == '':
        #     print(r, acp['acp_tipo'], esp)

    def execute(self, txt_tipo, txt_esp):
        regex = RegexService()
        for texto in (txt_tipo, txt_esp):
            if texto is None:
                continue

            if texto == '':
                continue
            # teste = 'Julgamento -> Com Resolução do Mérito -> Provimento parcialmente'
            text_string = remove_acentos(texto.upper().replace('   ',' ').replace('  ',' '))
            # print(text_string)
            for tipo in self.lista_ocorrencias:
                for esp in self.lista_ocorrencias[tipo]:
                    for ch in self.lista_ocorrencias[tipo][esp]['Chaves']:
                        exata = ch['Exata']
                        if exata is not None and exata != '':
                            if exata.find('${') > -1:
                                if regex.check_reg(exata, text_string) is not None:
                                    return self.format_return(tipo, esp)
                            else:
                                if exata == text_string:
                                    return self.format_return(tipo, esp)

                        inicio = ch['Inicio']
                        f = text_string.find(inicio) if inicio is not None and inicio != '' else 0
                        if f == 0:
                            qualquer = ch['Qualquer']
                            lista_not = ch['Not']
                            if len(qualquer) == 0 and len(lista_not) == 0 and inicio != '':
                                return self.format_return(tipo, esp)

                            achei_sub = False
                            for q in qualquer:
                                achei_sub = False
                                for sq in q:
                                    fs =  text_string.find(sq)
                                    if fs > 0:
                                        achei_sub = True
                                        break

                                if not achei_sub:
                                    break

                            if inicio is not None and inicio != '':
                                if achei_sub or len(qualquer) == 0:
                                    achei_not = False
                                    for ln in lista_not:
                                        for lnt in ln:
                                            if text_string.find(lnt):
                                                achei_not = True

                                    if not achei_not:
                                        return self.format_return(tipo, esp)

        return False

    def convert_to_tuple(self, txt_json):
        if txt_json is None or txt_json.strip() == '':
            return ()
        lst = json.loads(txt_json)
        lst = [[remove_acentos(each_string.upper()) for each_string in ch] for ch in lst]
        tp = [tuple(x) for x in lst]

        return tuple(tp)

    def format_return(self, tipo, esp):
        ret_tipo = tipo
        ret_esp = esp
        if tipo == '':
            ret_tipo = ''
            ret_esp = ''

        result = {'tipo': ret_tipo, 'esp': ret_esp,
                  'alternativo': self.lista_ocorrencias[tipo][esp]['Alternativa'],
                  'arquivo': self.lista_ocorrencias[tipo][esp]['Documento'],
                  'arquivo alternativo': self.lista_ocorrencias[tipo][esp]['Documento Alternativo']
                  }

        return result

    def reorder_dict(self):
        temp = self.lista_ocorrencias['Despacho']
        del self.lista_ocorrencias['Despacho']
        self.lista_ocorrencias['Despacho'] = temp

        temp = self.lista_ocorrencias['']
        del self.lista_ocorrencias['']
        self.lista_ocorrencias[''] = temp