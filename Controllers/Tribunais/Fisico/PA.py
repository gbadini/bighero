from Controllers.Tribunais.Fisico._fisico import *
from pysimplesoap.client import SoapClient

# CLASSE DA VARREDURA DO FÍSCO DO PA. HERDA OS METODOS DA CLASSE PROJUDIV2
class PA(Fisico):

    def __init__(self):
        super().__init__()
        self.pagina_inicial = "chrome://version/"
        self.result = {}

    # MÉTODO PARA A BUSCA DO PROCESSO NO TRIBUNAL
    def busca_processo(self, numero_busca):
        self.result = []
        WSDL_URL = 'https://consultas.tjpa.jus.br/WSConsultaProcessualTJ/ConsultaProcessualService?wsdl'
        client = SoapClient(wsdl=WSDL_URL, ns="web", trace=False)
        response = client.dadosProcessoCNJ({'numeroProcessoCNJ': numero_busca, 'tipoConsulta': 2})
        r = response['return']
        print(r)
        print(r['status']['mensagem'])

        if 'Index: 0' in r['status']['mensagem'] or 'não pertence à instância' in r['status']['mensagem']:
            return False

        if 'sucesso' not in r['status']['mensagem'] and 'segredo' not in r['status']['mensagem']:
            raise MildException("Erro na busca", self.uf, self.plataforma, self.prc_id)

        self.result = r
        return True

    # MÉTODO PARA CONFERIR SE O NÚMERO CNJ LOCALIZADO É IGUAL AO PESQUISADO
    def confere_cnj(self, numero_busca):
        '''
        :param str numero_busca: processo a ser comparado
        '''
        numero_site = self.result['numeroCNJ'] if 'numeroCNJ' in self.result else self.result['documentoLista'][-1]['cdProcesso']
        numero_site = ajusta_numero(numero_site)
        if numero_busca == numero_site:
            return True

        raise MildException("Número CNJ Diferente - "+numero_site+" "+numero_busca, self.uf, self.plataforma, self.prc_id)

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        if 'segredo' in self.result['status']['mensagem']:
            return True

        self.confere_cnj(numero_busca)

        return False

    # CONFERE SE A ÚLTIMA MOVIMENTAÇÃO DA PLATAFORMA É SUPERIOR A ULTIMA MOVIMENTAÇÃO DA BASE
    def ultima_movimentacao(self,ultima_data, prc_id, base):
        '''
        :param str ultima_data: data da ultimo movimentação da base
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''

        if 'movimentos' not in self.result:
            return True

        data_tj = self.result['movimentos'][0]['dataMovimento'].replace(tzinfo=None)
        if ultima_data == data_tj:
            return True

        return False

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''
        ultima_mov = proc_data['cadastro']
        self.movs = []
        movs = []

        capturar = True
        i = 0

        if 'movimentos' not in self.result:
            return []

        for mov in self.result['movimentos']:
            i += 1
            acp_cadastro = mov['dataMovimento'].replace(tzinfo=None)
            if acp_cadastro == ultima_mov:
                capturar = False
                if not completo and i >= 10:
                    break

            acp_tipo = str(mov['cdtpmovimento'])
            acp_esp = mov['detpmovimento']
            acp = {'acp_cadastro': acp_cadastro, 'acp_esp': acp_esp, 'acp_tipo': acp_tipo}
            if capturar:
                movs.append(acp)

            self.movs.append({**acp, 'novo': capturar})

        return movs

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        prc = {}

        if 'numeroCNJ' not in self.result:
            for p in self.result['documentoLista']:
                if p['instancia'] == 'PRIMEIRO_GRAU':
                    prc['prc_numero2'] = p['cdProcesso']
                    prc['prc_status'] = 'Ativo'
                    if 'ARQUIVADO' in p['situacao'].upper():
                        prc['prc_status'] = 'Arquivado'

                    break

        else:
            prc['prc_numero2'] = self.result['numeroCNJ']
            prc['prc_classe'] = self.result['classe']
            prc['prc_comarca2'] = self.result['comarca']
            prc['prc_juizo'] = self.result['vara']
            prc['prc_assunto'] = ''
            for assunto in self.result['assuntos']:
                if 'deassunto' in assunto:
                    prc['prc_assunto'] += assunto['deassunto'] + ' '
            prc['prc_assunto'] = prc['prc_assunto'].strip()
            prc['prc_classe'] = self.result['classe']
            prc['prc_distribuicao'] = datetime.strptime(self.result['dataDistribuicao'], '%d/%m/%Y')
            prc['prc_valor_causa'] = self.result['valorCausa']
            prc['prc_status'] = 'Ativo'
            if 'ARQUIVADO' in self.result['situacao'].upper():
                prc['prc_status'] = 'Arquivado'

        return prc

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo': [], 'passivo': [], 'terceiro': []}

        if 'partes' not in self.result:
            return partes

        for prt in self.result['partes']:
            tipo = prt['tpparticipacao']['detpparticipacao']
            if find_string(tipo,self.titulo_partes['ignorar']):
                continue

            polo = ''
            if find_string(tipo,self.titulo_partes['ativo']):
                polo = 'ativo'
            if find_string(tipo,self.titulo_partes['passivo']):
                polo = 'passivo'
            if find_string(tipo,self.titulo_partes['terceiro']):
                polo = 'terceiro'

            if polo == '':
                raise MildException("polo vazio "+tipo, self.uf, self.plataforma, self.prc_id)

            prt_nome = prt['nome']
            partes[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': 'Não Informado'})

        return partes

    # CAPTURA RESPONSÁVEIS DO PROCESSO
    def responsaveis(self):
        resps = []

        if 'partes' not in self.result:
            return resps

        juiz = self.result['nomeMagistrado']
        resps.append({'prr_nome': juiz.strip(), 'prr_oab': '', 'prr_cargo': 'Juiz', 'prr_parte': ''})

        for prt in self.result['partes']:
            tipo = prt['tpparticipacao']['detpparticipacao']
            if find_string(tipo,self.titulo_partes['ignorar']):
                continue
            if find_string(tipo,self.titulo_partes['terceiro']):
                continue

            polo = ''
            if find_string(tipo,self.titulo_partes['ativo']):
                polo = 'ativo'
            if find_string(tipo,self.titulo_partes['passivo']):
                polo = 'passivo'

            if 'representantes' in prt:
                for rep in prt['representantes']:
                    prr_nome = rep['nome']
                    resps.append({'prr_nome': prr_nome, 'prr_oab': None, 'prr_cargo': 'Advogado', 'prr_parte': polo})

        return resps

