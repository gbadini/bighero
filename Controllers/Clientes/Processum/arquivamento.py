import time
from Controllers.Clientes.arquivamento import *
from Controllers.Clientes.Processum._processum import *
from dateutil.relativedelta import relativedelta
from Models.sentencaModel import *

# CLASSE DO LANÇAMENTO DE ARQUIVAMENTO. HERDA OS METODOS DA CLASSE PROCESSUM
class Arquivamento(ArquivamentoCliente, Processum):

    def __init__(self):
        super().__init__()
        self.ordem_usuario = 0
        self.realiza_reavaliacao = True

    # CONFERE SE OS DADOS LANÇADOS NOS CAMPOS CONFEREM COM A BASE
    def tratar_dados(self, base, dados):
        sentencas = Sentenca.select_by_prc_id(base, dados['prc_id'])
        if len(sentencas) == 0:
            raise FatalException('Sentença não cadastrada', self.uf, self.plataforma, self.prc_id)

        resultados = {'Acordo':'Acordo', 'Acordo Pós Sentença': 'Acordo pós Sentença', 'Improcedente':'Sentença improcedente',
                     'Parcialmente procedente':'Sentença parcialmente procedente', 'Extinto':'Sentença sem julgamento do mérito',
                      'Procedente': 'Sentença totalmente procedente'}

        obs = sentencas[0]['resultado_principal']
        resultado = resultados[sentencas[0]['resultado_principal']] if sentencas[0]['resultado_principal'] in resultados else sentencas[0]['resultado_principal']
        motivo_principal = sentencas[0]['motivo_principal'] if sentencas[0]['motivo_principal'] is not None else ''
        motivo_julgamento = sentencas[0]['motivo_julgamento'] if sentencas[0]['motivo_julgamento'] is not None else ''
        motivo_arquivamento = sentencas[0]['motivo_arquivamento']

        if motivo_principal == 'Acordo Pós Sentença' or motivo_julgamento == 'Acordo Pós Sentença':
            resultado = 'Acordo pós Sentença'

        if motivo_arquivamento is not None and motivo_arquivamento != '':
            resultado = motivo_arquivamento

        acp = {}
        acp['principais'] = {
                'tipo': {'dado': 'Arquivamento', 'campo':'fCadastrar:tipoOcorrencia', 'by':'ID'},
                'esp': {'dado': resultado, 'campo': 'fCadastrar:espTipoOcorrencia', 'by':'ID' },
            }

        # acp['select'] = {}
        # acp['select']['comarca'] = {'dado': 1, 'campo': 'fCadastrar:comarca', 'by': 'ID', 'select_by': 'index',}

        data_evento = datetime.today()
        dia_da_semana = data_evento.isoweekday()
        if dia_da_semana in (6, 7):
            delta = dia_da_semana-5
            data_evento = datetime.today() + relativedelta(days=-delta)

        data_prazo = data_evento + relativedelta(days=+7)

        data_evento = data_evento.strftime('%d/%m/%Y')
        data_prazo = data_prazo.strftime('%d/%m/%Y')

        acp['input'] = {}
        acp['input']['data_evento'] = {'dado': data_evento, 'campo': 'fCadastrar:dataEvento', 'by': 'ID'}
        acp['input']['obs'] = {'dado': obs, 'campo': 'fCadastrar:observacao', 'by': 'ID'}
        acp['input']['data_prazo'] = {'dado': data_prazo, 'campo': 'fCadastrar:dataPrazo', 'by': 'ID'}

        acp['arq'] = Arquivo.select_by_processo(base, dados['prc_id'])
        if len(acp['arq']) == 0:
            raise FatalException('Arquivamento sem arquivos vinculados', self.uf, self.plataforma, self.prc_id)

        acp['arquivo'] = ['Arquivamento',]
        acp['tipo_arquivo'] = 'Arquivamento'
        acp['data_arquivo'] = data_evento
        acp['obs_arquivo'] = 'Encerramento de processo judicial'

        return acp

    def confere_restricao(self):
        self.confere_filtro()

    def confere_valor_provavel(self):
        self.abre_modal_contingencia()

        val = self.driver.find_element_by_id('fContingencia:valorProvavel7').get_attribute('value')
        self.fecha_modal()

        if val != '0,00' and val != '':
            return False

        return True





