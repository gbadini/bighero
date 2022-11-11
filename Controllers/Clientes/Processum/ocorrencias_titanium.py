from Controllers.Clientes.Processum._processum import *
from Controllers.Clientes.ocorrencias_titanium import *
import json

# CLASSE DE LANÇAMENTO DE OCORRÊNCIA NO PROCESSUM
class OcorrenciasTitanium(OcorrenciasTitaniumCliente, Processum):

    def __init__(self):
        super().__init__()
        self.movs = []
        self.ordem_usuario = 0

    # CONFERE SE OS DADOS LANÇADOS NOS CAMPOS CONFEREM COM A BASE
    def tratar_dados(self, acp, current_date=False, delta=5):
        if current_date:
            acp_evento = datetime.now()
            dia_da_semana = acp_evento.isoweekday()
            if dia_da_semana in (6, 7):
                delta_evento = 8 - dia_da_semana
                acp_evento = acp_evento + relativedelta(days=+delta_evento)
        else:
            acp_evento = acp['acp_data_evento']

        acp_prazo = acp_evento + relativedelta(days=+delta)
        acp_prazo = acp_prazo.strftime('%d/%m/%Y')

        acp_evento = acp_evento.strftime('%d/%m/%Y')
        acp = {
            'principais':{
                'tipo': {'dado': acp['acp_tipo'], 'campo':'fCadastrar:tipoOcorrencia', 'by':'ID'},
                'esp': {'dado': acp['acp_esp'], 'campo': 'fCadastrar:espTipoOcorrencia', 'by':'ID'},
            },
            'input': {
                'data_prazo': {'dado': acp_prazo, 'campo': 'fCadastrar:dataPrazo', 'by': 'ID'},
                'data_evento': {'dado': acp_evento, 'campo': 'fCadastrar:dataEvento', 'by': 'ID'},
                'obs': {'dado': '', 'campo': 'fCadastrar:observacao', 'by': 'ID'},
            },
            'select': {}
        }

        return acp