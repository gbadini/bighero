from Controllers.Clientes.pagamentos import *
from Controllers.Clientes.Processum._processum import *
from dateutil.relativedelta import relativedelta

# CLASSE DO LANÇAMENTO DE PAGAMENTOS. HERDA OS METODOS DA CLASSE PROCESSUM
class Pagamentos(PagamentosCliente, Processum):

    def __init__(self):
        super().__init__()
        self.ordem_usuario = 2

    # TRATA OS DADOS PARA O FORMATO DA PLATAFORMA
    def tratar_dados(self, base, dados):
        acp = {}

        esp_pgto = 'Obrigação de Pagar - Tributo/IR' if dados['pag_tipo'] == 'Imposto de Renda' else 'Obrigação de Pagar'
        acp['principais'] = {
                'tipo': {'dado': dados['pag_tipo'], 'campo':'fCadastrar:tipoOcorrencia', 'by':'ID'},
                'esp': {'dado': esp_pgto, 'campo': 'fCadastrar:espTipoOcorrencia', 'by':'ID' , 'aguardar': 'fCadastrar:valEconomicoEnvolvidoFin', 'aguardar_tipo': 'ID'},
            }

        if len(dados['pag_cpf_favorecido']) > 14:
            acp['radio'] = {
                'pag_cpf_cnpj': {'dado': None, 'campo': 'statCpfCnpj', 'by': 'NAME', 'aguardar': 'inputPesquisaCnpj', 'aguardar_tipo': 'ID'},
            }
        acp['input'] = {}
        acp['input']['data_evento'] = {'dado': dados['pag_prazo'].strftime('%d/%m/%Y'), 'campo': 'fCadastrar:dataEvento', 'by': 'ID', 'check': 'fOcorrencia:dataPrazoLegal'}

        acp['select'] = {}
        if dados['pag_tipo_multa'] is not None and dados['pag_tipo_multa'] != '':
            acp['select']['pag_tipo_multa'] = {'dado': dados['pag_tipo_multa'], 'campo': 'fCadastrar:tipoMulta', 'by': 'ID', 'select_by': 'value',}

        if dados['pag_valor_multa'] is not None and dados['pag_valor_multa'] != '':
            pag_valor_multa = dados['pag_valor_multa']
            pag_valor_multa = format_number_br(pag_valor_multa)
            acp['input']['pag_valor_multa'] = {'dado': pag_valor_multa, 'campo': 'fCadastrar:valorMulta', 'by': 'ID'}

        acp['select']['pag_tipo_pagamento'] = {'dado': dados['pag_tipo_pagamento'], 'campo': 'fCadastrar:codTipoPagamentoOcorrencia', 'by': 'ID', 'select_by': 'value'}
        if dados['pag_banco'] is not None and dados['pag_banco'] != '':
            acp['select']['pag_banco'] = {'dado': dados['pag_banco'], 'campo': 'fCadastrar:codBanco', 'by': 'ID', 'select_by': 'value'}
        if dados['pag_agencia'] is not None and dados['pag_agencia'] != '':
            acp['input']['pag_agencia'] = {'dado': dados['pag_agencia'].replace('-','').strip(), 'campo': 'fCadastrar:numAgencia', 'by': 'ID'}

        if dados['pag_agencia_digito'] is not None and dados['pag_agencia_digito'] != '':
            acp['input']['pag_agencia_digito'] = {'dado': dados['pag_agencia_digito'], 'campo': 'fCadastrar:digitoAgencia', 'by': 'ID'}

        if dados['pag_conta'] is not None and dados['pag_conta'] != '':
            if len(dados['pag_conta']) > 16:
                raise FatalException('Conta com mais de 16 dígitos', self.uf, self.plataforma, self.prc_id)

            acp['input']['pag_conta'] = {'dado': dados['pag_conta'].strip(), 'campo': 'fCadastrar:contaCorrente', 'by': 'ID', 'check': 'fOcorrencia:contaCorrente', 'limpar_string': True}

        if dados['pag_conta_digito'] is not None and dados['pag_conta_digito'] != '':
            acp['input']['pag_conta_digito'] = {'dado': dados['pag_conta_digito'].strip(), 'campo': 'fCadastrar:digitoContaCorrente', 'by': 'ID'}

        pag_valor = format_number_br(dados['pag_valor'])

        if dados['pag_tipo'] == 'Acordo':
            acp['input']['pag_valor'] = {'dado': pag_valor, 'campo': 'fCadastrar:valEconomicoEnvolvido', 'by': 'ID', 'check': 'fOcorrencia:valEconomicoEnvolvido'}
        else:
            pag_valor_op = format_number_br(dados['pag_valor_op']) if dados['pag_valor_op'] is not None else '0,00'
            acp['input']['pag_valor_op'] = {'dado': pag_valor_op, 'campo': 'fCadastrar:valEconomicoEnvolvidoOp', 'by': 'ID', 'wait': 1}

            pag_valor_fin = format_number_br(dados['pag_valor_fin']) if dados['pag_valor_fin'] is not None else '0,00'
            acp['input']['pag_valor_fin'] = {'dado': pag_valor_fin, 'campo': 'fCadastrar:valEconomicoEnvolvidoFin', 'by': 'ID', 'wait': 1}

            acp['input']['pag_valor'] = {'dado': pag_valor, 'campo': 'fCadastrar:valEconomicoEnvolvido', 'by': 'ID', 'readonly': True, 'check': 'fOcorrencia:valEconomicoEnvolvido'}

        campocpf = 'inputPesquisaCnpj' if len(dados['pag_cpf_favorecido']) > 14 else 'inputPesquisaCpf'
        campocpf = campocpf.replace('-','').replace('.','').replace('/','')
        acp['input']['pag_cpf_favorecido'] = {'dado': dados['pag_cpf_favorecido'], 'campo': campocpf, 'by': 'ID', 'check': 'panelCpfCnpj'}

        if dados['pag_n_id'] is not None and dados['pag_n_id'] != '':
            acp['input']['pag_n_id'] = {'dado': dados['pag_n_id'].strip(), 'campo': 'fCadastrar:idPagamento', 'by': 'ID', 'limpar_string': True}
        favorecido = ' '.join(dados['pag_favorecido'].split())
        acp['input']['pag_favorecido'] = {'dado': favorecido[:70].replace("'", ''), 'campo': 'fCadastrar:favorecido', 'by': 'ID', 'check': 'fOcorrencia:favorecido'}
        acp['select']['pag_centro_de_custo'] = {'dado': 1,'campo': 'fCadastrar:CentroCusto', 'by': 'ID', 'select_by': 'index', 'ignora_erro': True}
        if dados['pag_descricao'] is not None and dados['pag_descricao'] != '':
            acp['input']['pag_descricao'] = {'dado': dados['pag_descricao'], 'campo': 'fCadastrar:observacao', 'by': 'ID', 'limpar_string': True}
        acp['select']['pag_conta_contabil'] = {'dado': dados['pag_conta_contabil'], 'campo': 'fCadastrar:ContaContabil', 'by': 'ID', 'erro': 'Conferir Conta Contábil'}

        acp['arquivos_ocorrencia'] = Arquivo.select_by_pagamento(base, dados['pag_id'])
        if len(acp['arquivos_ocorrencia']) == 0:
            raise FatalException('Pagamento sem arquivos vinculados', self.uf, self.plataforma, self.prc_id)

        acp['obs_arquivo'] = "Segue anexos"

        print(acp)
        return acp


    # TRATA OS DADOS PARA O FORMATO DA PLATAFORMA
    def tratar_dados_peticao(self, base, dados):
        acp = {}
        acp['principais'] = {
                'tipo': {'dado': 'Petição', 'campo':'fCadastrar:tipoOcorrencia', 'by':'ID'},
                'esp': {'dado': 'Informar Cumprimento Acordo/Sentença', 'campo': 'fCadastrar:espTipoOcorrencia', 'by':'ID' },
            }

        data_evento = dados['pag_prazo'] + relativedelta(days=+2)
        dia_da_semana = data_evento.isoweekday()
        if dia_da_semana in (6, 7):
            delta = 8 - dia_da_semana
            data_evento = data_evento + relativedelta(days=+(delta))

        data_evento = data_evento.strftime('%d/%m/%Y')

        acp['input'] = {}
        acp['input']['data_evento'] = {'dado': data_evento, 'campo': 'fCadastrar:dataEvento', 'by': 'ID' }
        acp['input']['data_prazo'] = {'dado': data_evento, 'campo': 'fCadastrar:dataPrazo', 'by': 'ID'}

        return acp

    def check_restricao_peticao(self):
        modulo = self.driver.find_element_by_id('fAcompanhamento:moduloAtualDesc')
        if not modulo:
            return False

        if modulo.text.strip() == 'ADMINISTRATIVO':
            return True

        return False