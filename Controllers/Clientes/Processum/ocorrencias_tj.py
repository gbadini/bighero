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

    # TRATA DADOS DA BASE NO FORMATO DO SISTEMA DO CLIENTE
    def tratar_dados(self, base, acps, lanca_imagem, area=1):
        dados_lanc = []
        prev_mes = mes_anterior()
        to_update = []
        for acp in acps:
            if acp['acp_cadastro'] < prev_mes:
                if acp['acp_ocorrencia'] is None:
                    to_update.append(acp['acp_id'])
                continue

            # if acp['acp_ocorrencia'] is not None:
            #     continue

            tipo = self.tipo_acp(acp, area)
            if not tipo or tipo['tipo'] == '' or tipo['tipo'] == '-':
                if acp['acp_ocorrencia'] is None:
                    to_update.append(acp['acp_id'])
                continue

            r = self.format_item(acp, tipo)
            achei = False
            for i, dl in enumerate(dados_lanc):
                if dl['input']['data_evento'] == r['input']['data_evento']:
                    if dl['principais']['tipo'] == r['principais']['tipo'] and dl['principais']['esp'] == r['principais']['esp']:
                        achei = True
                        dados_lanc[i]['acps'].append(acp['acp_id'])
                        if dl['input']['obs']['dado'] == r['input']['obs']['dado']:
                            break

                        obs = r['input']['obs']['dado'].replace('Lançamento de Ocorrência:','').strip()
                        dados_lanc[i]['input']['obs']['esp'].append(obs)

                        obs = dados_lanc[i]['input']['obs']['dado'] + " | " + obs
                        dados_lanc[i]['input']['obs']['dado'] = corta_string(obs,250)

                        break

            if not achei:
               dados_lanc.append(r)

        if len(to_update) > 0:
            Acompanhamento.update_batch(base, to_update, {'acp_ocorrencia': 0,})

        for dl in dados_lanc:
            esps = []
            for e1 in dl['input']['obs']['esp']:
                ins = True
                for e2 in esps:
                    if e2.upper().find(e1[:20].upper()) == 0:
                        ins = False
                if ins:
                    esps.append(e1)

            len_total = 500
            while len_total > 210:
                len_total = 0
                for l in esps:
                    len_total += len(l)

                if len_total > 210:
                    maior = max(esps, key=len)
                    i_maior = esps.index(maior)
                    esps[i_maior] = corta_string(maior, len(maior) - 1)

                esps = list(dict.fromkeys(esps))

            obs_final = 'Lançamento de Ocorrência: ' + " | ".join(esps)
            dl['input']['obs']['dado'] = obs_final

        return dados_lanc

    # FORMATA DICT COM OS ELEMENTOS QUE SERÃO LANÇADOS NO SISTEMA
    def format_item(self, acp, tipo):
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
        # esp = corta_string(esp, 200, sufixo='...')
        item = {
            'acps': [acp['acp_id']],
            'acp_id': acp['acp_id'],
            'acp_cadastro': acp['acp_cadastro'],
            'acp_tipo': acp['acp_tipo'],
            'acp_esp': acp['acp_esp'],
            'acp_ocorrencia': acp['acp_ocorrencia'],
            'acp_plataforma': acp['acp_plataforma'],
            'principais': {
                'tipo': {'dado': tipo['tipo'], 'campo': 'fCadastrar:tipoOcorrencia', 'by': 'ID'},
                'esp': {'dado': tipo['esp'], 'campo': 'fCadastrar:espTipoOcorrencia', 'by': 'ID'},
            },
            'input': {
                'data_evento': {'dado': acp_evento, 'campo': 'fCadastrar:dataEvento', 'by': 'ID'},
                'obs': {'esp': [esp],  'dado': 'Lançamento de Ocorrência: ' + esp, 'campo': 'fCadastrar:observacao', 'by': 'ID'},
                # 'data_prazo': {'dado': acp_prazo, 'campo': 'fCadastrar:dataPrazo', 'by': 'ID'},
            },
            'select': {},
            'alternativo': {},
        }

        if tipo['tipo'] in ('Recurso', 'Sentença','Contestação',):
            item['input']['data_prazo'] = {'dado': acp_prazo, 'campo': 'fCadastrar:dataPrazo', 'by': 'ID'}

        if tipo['alternativo'][0]:
            item['alternativo']['tipo'] = tipo['alternativo'][0]

        if tipo['alternativo'][1]:
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
