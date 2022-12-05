from Controllers.Clientes.Processum._processum import *
from Controllers.Clientes.ocorrencias_dj import *
import json

# CLASSE DE LANÇAMENTO DE OCORRÊNCIA NO PROCESSUM
class OcorrenciasDJ(OcorrenciasDJCliente, Processum):

    def __init__(self):
        super().__init__()
        self.movs = []
        self.ordem_usuario = 0

    # TRATA DADOS DA BASE NO FORMATO DO SISTEMA DO CLIENTE
    def tratar_dados(self, acps, modulo):

        if modulo == 'ADMINISTRATIVO':
            return False

        obss = []
        for a in acps:
            obs = ''
            if a['drp_subtitulo'] != '':
                subtitulo = a['drp_subtitulo'].replace('__','').replace('  ',' ') + ' - '
                subtitulo = corta_string(subtitulo, 45)
                obs += subtitulo + ' - '

            if a['drp_subtitulo'].lower().find('pauta') > -1:
                obs += a['drp_enunciado'].replace('__','') + ' - '
            else:
                if a['drp_extrato'] != '':
                    drp_extrato = a['drp_extrato'].replace('\n','').replace('\r','').replace('[**]','').replace('[*]','').replace('__','').replace('  ',' ')
                    obs += drp_extrato
                else:
                    drp_conteudo = a['drp_conteudo'].replace('\n','').replace('\r','').replace('__','').replace('  ',' ')
                    drp_conteudo = strip_html_tags(drp_conteudo)
                    obs += drp_conteudo

            if obs not in obss:
                obss.append(obs)

        len_total = 500
        while len_total > 215:
            len_total = 0
            for l in obss:
                len_total += len(l)

            if len_total > 215:
                maior = max(obss, key=len)
                i_maior = obss.index(maior)
                obss[i_maior] = corta_string(maior, len(maior) - 1, sufixo='...')

        obs_final = 'Publicação DJ: ' + " | ".join(obss)

        acp_evento = acps[0]['dro_dia'].strftime('%d/%m/%Y')
        acp = {
            'principais':{
                'tipo': {'dado': 'Despacho', 'campo':'fCadastrar:tipoOcorrencia', 'by':'ID'},
                'esp': {'dado': 'Para as partes', 'campo': 'fCadastrar:espTipoOcorrencia', 'by':'ID'},
            },
            'input': {
                # 'data_prazo': {'dado': acp_evento, 'campo': 'fCadastrar:dataPrazo', 'by': 'ID'},
                'data_evento': {'dado': acp_evento, 'campo': 'fCadastrar:dataEvento', 'by': 'ID'},
                'obs': {'dado': obs_final, 'campo': 'fCadastrar:observacao', 'by': 'ID'},
            },
            'select': {},
            'alternativo': {'tipo': 'Publicação', },
        }
        # dados_lanc.append(acp)
        # print(acp)
        return acp
