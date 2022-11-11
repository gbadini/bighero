from Controllers.Clientes.Processum._processum import *
from Controllers.Clientes.ocorrencias_tj import *
# from Config.tipos_ocorrencia.services.CompareOccurrenceByDescriptionService import ComparaOcorrencias
import json

# CLASSE DE LANÇAMENTO DE OCORRÊNCIA NO PROCESSUM
class OcorrenciasTJ(OcorrenciasTJCliente, Processum):

    def __init__(self):
        super().__init__()
        self.movs = []
        self.ordem_usuario = 0


    # CONFERE SE OS DADOS LANÇADOS NOS CAMPOS CONFEREM COM A BASE
    def tratar_dados(self, base, acps, lanca_imagem, area=1):
        dados_lanc = []
        prev_mes = mes_anterior()
        # prev_mes = datetime.strptime('16/12/2021 00:00:00', '%d/%m/%Y %H:%M:%S')
        to_update = []
        for acp in acps:
            if acp['acp_cadastro'] < prev_mes:
                # print('.', end='')
                if acp['acp_ocorrencia'] is None:
                    to_update.append(acp['acp_id'])
                    # Acompanhamento.update(base, [{'acp_id': acp['acp_id'], 'acp_ocorrencia': 0}, ])
                # ProcessoArquivo.update_by_date(base, acp['acp_processo'],  acp['acp_cadastro'], acp['acp_plataforma'],{'pra_ocorrencia': 0})
                continue

            tipo = self.tipo_acp(acp, area)
            if not tipo or tipo['ocorrencia'][0] == '' or tipo['ocorrencia'][0] == '-':
                if not tipo or tipo['arquivo'][0] == '' or tipo['arquivo'][0] == '-':
                    print('-', end='')
                    if acp['acp_ocorrencia'] is None:
                        to_update.append(acp['acp_id'])
                        # Acompanhamento.update(base, [{'acp_id': acp['acp_id'], 'acp_ocorrencia': 0},])
                    # if lanca_imagem:
                        # ProcessoArquivo.update_by_date(base, acp['acp_processo'], acp['acp_cadastro'],acp['acp_plataforma'], {'pra_ocorrencia': 0})
                    continue

                acp['date_range']: 3
                acp['arquivo'] = tipo['arquivo']
                acp['data_arquivo'] = acp['acp_cadastro'].strftime('%d/%m/%Y')
                acp['obs_arquivo'] = tipo['descricao_arquivo']

                dados_lanc.append(acp)
                continue

            r = self.format_item(acp, tipo)
            # acp_evento = acp['acp_cadastro'].strftime('%d/%m/%Y')
            # acp['acp_cadastro'].isoweekday()
            # dia_da_semana = acp['acp_cadastro'].isoweekday()
            # if dia_da_semana in (6, 7):
            #     delta = 8 - dia_da_semana
            #     acp_evento = acp['acp_cadastro'] + relativedelta(days=+delta)
            #     acp_evento = acp_evento.strftime('%d/%m/%Y')
            #
            # acp_prazo = datetime.today() + relativedelta(days=+7)
            # dia_da_semana = acp_prazo.isoweekday()
            # if dia_da_semana in (6, 7):
            #     delta = 8 - dia_da_semana
            #     acp_prazo = datetime.today() + relativedelta(days=+delta)
            #
            # acp_prazo = acp_prazo.strftime('%d/%m/%Y')
            # esp = strip_html_tags(tipo['descricao'])
            # esp = esp.replace(r'\r','').replace(r'\n','')
            # esp = corta_string(esp, 200, sufixo='...')
            # acp = {
            #     'acp_id': acp['acp_id'],
            #     'acp_cadastro': acp['acp_cadastro'],
            #     'acp_tipo': acp['acp_tipo'],
            #     'acp_esp': acp['acp_esp'],
            #     'acp_ocorrencia': acp['acp_ocorrencia'],
            #     'acp_plataforma': acp['acp_plataforma'],
            #     'principais':{
            #         'tipo': {'dado': tipo['ocorrencia'][0], 'campo':'fCadastrar:tipoOcorrencia', 'by':'ID'},
            #         'esp': {'dado': tipo['ocorrencia'][1], 'campo': 'fCadastrar:espTipoOcorrencia', 'by':'ID'},
            #     },
            #     'input': {
            #         'data_evento': {'dado': acp_evento, 'campo': 'fCadastrar:dataEvento', 'by': 'ID'},
            #         'obs': {'dado': 'Lançamento de Ocorrência: '+esp, 'campo': 'fCadastrar:observacao', 'by': 'ID'},
            #         'data_prazo': {'dado': acp_prazo, 'campo': 'fCadastrar:dataPrazo', 'by': 'ID'},
            #     },
            #     'select': {},
            #     'alternativo': {}
            # }
            #
            # if tipo['alternativo'][0] != '' and tipo['alternativo'][0] != '-':
            #     acp['alternativo']['tipo'] = tipo['alternativo'][0]
            #
            # if tipo['alternativo'][1] != '' and tipo['alternativo'][1] != '-':
            #     acp['alternativo']['esp'] = tipo['alternativo'][1]
            #
            # acp['arquivo'] = tipo['arquivo']
            # acp['data_arquivo'] = acp['acp_cadastro'].strftime('%d/%m/%Y')
            # acp['obs_arquivo'] = tipo['descricao_arquivo']
            # print('*', end='')
            # dados_lanc.append(acp)
            dados_lanc.append(r)

        # if len(dados_lanc) == 0:
        #     acps = Acompanhamento.lista_movs(base, acps[0]['acp_processo'], None, ignora_cliente=True, order_by=True)
        #     data_menos_90 = datetime.now() - timedelta(90)
        #     for acp in acps:
        #         if acp['acp_ocorrencia'] and acp['acp_cadastro'] > data_menos_90:
        #             Acompanhamento.update_batch(base, to_update, [{'acp_ocorrencia': 0, }, ])
        #             return dados_lanc
        #
        #     acps.reverse()
        #     retroativo = False
        #     if acps[0]['acp_cadastro'] < data_menos_90:
        #         for acp in acps:
        #             if acp['acp_ocorrencia']:
        #                 Acompanhamento.update_batch(base, to_update, [{'acp_ocorrencia': 0, }, ])
        #                 return dados_lanc
        #         retroativo = True
        #
        #     for acp in acps:
        #         if acp['acp_ocorrencia']:
        #             continue
        #
        #         chaves_not = ('DECORRIDO PRAZO', 'REVELIA')
        #         if find_string(acp['acp_esp'], chaves_not):
        #             continue
        #
        #         if retroativo:
        #             tipo = self.tipo_acp(acp, area)
        #             if tipo:
        #                 r = self.format_item(acp, tipo, date_range=60)
        #                 r['acp_ocorrencia'] = None
        #                 dados_lanc.append(r)
        #                 break
        #         else:
        #             tipo = acp['acp_tipo'] if acp['acp_tipo'] is not None else ''
        #             if find_string(tipo, chaves_not):
        #                 continue
        #
        #             esp = self.trata_esp(acp)
        #             acp['acp_ocorrencia'] = None
        #             description = esp if tipo == '' else tipo+' - '+esp
        #             tipo = {'ocorrencia': ['Despacho', 'Para as partes'],
        #                              'arquivo': ['-', '-'],
        #                              'alternativo': ['Publicação', '-'],
        #                              'original': description,
        #                              'descricao': description,
        #                              'descricao_arquivo': description
        #                              }
        #
        #             r = self.format_item(acp, tipo, date_range=60)
        #             dados_lanc.append(r)
        #             break

        if len(to_update) > 0:
            Acompanhamento.update_batch(base, to_update, {'acp_ocorrencia': 0,})

        print(' ')
        print(dados_lanc)
        return dados_lanc

    # FORMATA DICT COM OS ELEMENTOS QUE SERÃO LANÇADOS NO SISTEMA
    def format_item(self, acp, tipo, date_range=3):
        acp_evento = acp['acp_cadastro'].strftime('%d/%m/%Y')
        acp['acp_cadastro'].isoweekday()
        dia_da_semana = acp['acp_cadastro'].isoweekday()
        if dia_da_semana in (6, 7):
            delta = 8 - dia_da_semana
            acp_evento = acp['acp_cadastro'] + relativedelta(days=+delta)
            acp_evento = acp_evento.strftime('%d/%m/%Y')

        acp_prazo = datetime.today() + relativedelta(days=+7)
        dia_da_semana = acp_prazo.isoweekday()
        if dia_da_semana in (6, 7):
            delta = 8 - dia_da_semana
            acp_prazo = datetime.today() + relativedelta(days=+delta)

        acp_prazo = acp_prazo.strftime('%d/%m/%Y')
        esp = strip_html_tags(tipo['descricao'])
        esp = esp.replace(r'\r', '').replace(r'\n', '')
        esp = corta_string(esp, 200, sufixo='...')
        item = {
            'acp_id': acp['acp_id'],
            'acp_cadastro': acp['acp_cadastro'],
            'acp_tipo': acp['acp_tipo'],
            'acp_esp': acp['acp_esp'],
            'acp_ocorrencia': acp['acp_ocorrencia'],
            'acp_plataforma': acp['acp_plataforma'],
            'principais': {
                'tipo': {'dado': tipo['ocorrencia'][0], 'campo': 'fCadastrar:tipoOcorrencia', 'by': 'ID'},
                'esp': {'dado': tipo['ocorrencia'][1], 'campo': 'fCadastrar:espTipoOcorrencia', 'by': 'ID'},
            },
            'input': {
                'data_evento': {'dado': acp_evento, 'campo': 'fCadastrar:dataEvento', 'by': 'ID'},
                'obs': {'dado': 'Lançamento de Ocorrência: ' + esp, 'campo': 'fCadastrar:observacao', 'by': 'ID'},
                'data_prazo': {'dado': acp_prazo, 'campo': 'fCadastrar:dataPrazo', 'by': 'ID'},
            },
            'select': {},
            'alternativo': {},
            'date_range': date_range
        }

        if tipo['alternativo'][0] != '' and tipo['alternativo'][0] != '-':
            item['alternativo']['tipo'] = tipo['alternativo'][0]

        if tipo['alternativo'][1] != '' and tipo['alternativo'][1] != '-':
            item['alternativo']['esp'] = tipo['alternativo'][1]

        item['arquivo'] = tipo['arquivo']
        item['data_arquivo'] = acp['acp_cadastro'].strftime('%d/%m/%Y')
        item['obs_arquivo'] = tipo['descricao_arquivo']
        print('*', end='')
        return item

    # CONFERE QUAL O TIPO DO ACOMPANHAMENTO
    def tipo_acp(self, acp, area=1):
        # a = ComparaOcorrencias()
        # se a frase existir na planilha ele retorna a Coluna 'J' da planinha correspondente a frase inserida.
        # se a frase não existir a função retorna 'False'
        esp = self.trata_esp(acp)

        arq_tipo = acp['acp_tipo']
        descricao = acp['acp_esp']

        if acp['acp_tipo'] is not None and acp['acp_tipo'].strip() != '':
            descricao = acp['acp_tipo'] + ' - ' + acp['acp_esp']
            result = re.search(r"(\d+)", acp['acp_tipo'])
            if result:
                if result.group(0) == acp['acp_tipo']:
                    if acp['acp_plataforma'] == 2 and len(result.group(0)) > 5 and area == 1:
                        return False
                    descricao = acp['acp_esp']
        else:
            arq_tipo = 'Arquivo Ocorrência'

        r = self.servico_ocorrencias.execute(esp, acp['acp_tipo'])
        if r:
            r['descricao'] = descricao

            esp = strip_html_tags(acp['acp_esp'])
            esp = esp.replace(r'\r', '').replace(r'\n', '')
            arq_tipo2 = corta_string(arq_tipo, 40, sufixo='')
            descricao_arquivo = arq_tipo2.strip() + ' - ' + acp['acp_cadastro'].strftime('%d/%m/%Y') + ' - ' + esp.strip()
            descricao_arquivo = corta_string(descricao_arquivo, 200, sufixo='...')
            r['descricao_arquivo'] = descricao_arquivo.strip()

        return r

    def trata_esp(self, acp):
        esp = acp['acp_esp']
        if acp['acp_plataforma'] not in (4, 5, 6):
            if acp['acp_tipo'] is not None:
                result = re.search(r"(\d+)", acp['acp_tipo'])
                if result:
                    if result.group(0) == acp['acp_tipo']:
                        if acp['acp_esp'].find(acp['acp_tipo'] + ' - ') == 0:
                            esp = acp['acp_esp'][len(acp['acp_tipo']) + 3:].strip()

        return esp
