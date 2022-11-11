from Controllers.Clientes.atas import *
from Controllers.Clientes.Processum._processum import *
from dateutil.relativedelta import relativedelta

# CLASSE DO LANÇAMENTO DE ATAS. HERDA OS METODOS DA CLASSE PROCESSUM
class Atas(AtasCliente, Processum):

    def __init__(self):
        super().__init__()
        self.ordem_usuario = 0

    # CONFERE SE OS DADOS LANÇADOS NOS CAMPOS CONFEREM COM A BASE
    def tratar_dados(self, base, dados):
        tipo = ''
        esp = ''
        if dados['adc_status'] == 'Ausência da Parte Autora':
            tipo = 'Ausência da Parte Autora'
            esp = 'Conciliação'

        if dados['adc_status'] == 'Autos Conclusos':
            tipo = 'Autos Conclusos'
            esp = 'Sentença'

        if dados['adc_status'] == 'Desistência da Ação':
            tipo = 'Desistência'
            esp = 'Da Ação'

        acp_evento = dados['adc_data'].strftime('%d/%m/%Y')
        dia_da_semana = dados['adc_data'].isoweekday()
        if dia_da_semana in (6, 7):
            delta = 8 - dia_da_semana
            acp_evento = dados['adc_data'] + relativedelta(days=+delta)
            acp_evento = acp_evento.strftime('%d/%m/%Y')

        acp_prazo = dados['adc_data'] + relativedelta(days=+7)
        dia_da_semana = acp_prazo.isoweekday()
        if dia_da_semana in (6, 7):
            delta = dia_da_semana - 5
            acp_prazo = dados['adc_data'] + relativedelta(days=+(7-delta))

        acp_prazo = acp_prazo.strftime('%d/%m/%Y')

        acp = {}
        acp['principais'] = {
                'tipo': {'dado': tipo, 'campo':'fCadastrar:tipoOcorrencia', 'by':'ID'},
                'esp': {'dado': esp, 'campo': 'fCadastrar:espTipoOcorrencia', 'by':'ID'},
            }


        acp['input'] = {
                'data_evento': {'dado': acp_evento, 'campo': 'fCadastrar:dataEvento', 'by': 'ID'},
                'obs': {'dado': dados['adc_status'], 'campo': 'fCadastrar:observacao', 'by': 'ID'},
                'data_prazo': {'dado': acp_prazo, 'campo': 'fCadastrar:dataPrazo', 'by': 'ID'},
            }

        acp['arquivo'] = ['Ata de Audiência',]
        acp['arq'] = [{'arq_id': dados['arq_id'], 'arq_url': dados['arq_url']},]
        acp['tipo_arquivo'] = 'Ata de Audiência'
        acp['data_arquivo'] = acp_evento

        escritorio = get_escritorio_nome(base)
        obs_arquivo = escritorio + ' - '
        obs_arquivo += dados['adc_obs'] if dados['adc_status'] == 'Audiência Inexistente' and dados['adc_obs'] != '' else dados['adc_status']
        acp['obs_arquivo'] = obs_arquivo

        return acp

    def check_modulo(self):
        modulo = self.driver.find_element_by_id('fDetalhar:moduloAtualDesc')
        if not modulo:
            modulo = self.driver.find_element_by_id('fImagem:moduloAtualDesc')

        if modulo.text.strip() == 'ADMINISTRATIVO' or modulo.text.strip() == 'INQUÉRITO CIVIL':
            return False

        return True
