from Controllers.Clientes.Processum._processum import *
import json
from datetime import date
from dateutil.relativedelta import relativedelta

# CLASSE DA VARREDURA DO PROCESSUM. HERDA OS METODOS DA CLASSE PROCESSUM
class Varredura(Processum):

    def __init__(self):
        super().__init__()
        self.movs = []
        self.ordem_usuario = 0

    # CAPTURA DADOS DO PROCESSO
    def dados(self, dados, base):
        '''
        :param dict dados: Dados do processo salvos atualmente na base
        '''
        prc = {}

        prc_filtro = self.driver.find_element_by_id('fDetalhar:pnlAlertaContaFiltro')
        prc['prc_filtro'] = True if prc_filtro else False

        # ABRE ABA DADOS DO PROCESSO
        self.abre_fecha_aba('DADOS DO PROCESSO')

        prc['prc_situacao'] = self.captura_status()
        prc = self.alimentar('prc_modulo', prc, 'fDetalhar:moduloAtualDesc', tipo='ID')
        prc = self.alimentar('prc_divisao', prc, 'fDetalhar:descDivisaoProcesso', tipo='ID')
        prc = self.alimentar('prc_empresa', prc, 'fDetalhar:empresa', tipo='ID')
        prc = self.alimentar('prc_fase', prc, 'fDetalhar:faseProcessual', tipo='ID')

        if 'prc_empresa' in prc:
            prc['prc_empresa'] = corta_string(prc['prc_empresa'],50)

        if 'prc_modulo' in prc:
            # if prc['prc_modulo'] in ('VARA CÍVEL','JEC',):
            #     prc['prc_area'] = 1
            if prc['prc_modulo'] in ('TRABALHISTA',):
                prc['prc_area'] = 2
            else:
                prc['prc_area'] = 1

        prc_favorito = get_text(self.driver, 'fDetalhar:relevante', tipo='ID')
        if prc_favorito and prc_favorito.find('Sim') > -1:
            prc['prc_favorito'] = 1

        prc = self.alimentar('prc_canal', prc, 'fDetalhar:canalHabilitador', tipo='ID')

        if 'prc_canal' in prc:
            prc['prc_canal'] = prc['prc_canal'].replace('( Descredenciado)','').replace('(Descredenciado)','').replace('-Revenda','').strip()

        objetos = get_text(self.driver, 'fDetalhar:objAcao', tipo='ID')
        if objetos:
            objetos_split = objetos.split("-")
            idx = 1
            for obj in objetos_split:
                prc['prc_objeto'+str(idx)] = obj.strip()
                idx += 1
                if idx > 4:
                    break

        prc['prc_localizacao'] = self.driver.find_element_by_id('fDetalhar:localizacao').text.strip()
        if dados['prc_estado'] is None:
            comarca_split = prc['prc_localizacao'].split("-")
            prc['prc_estado'] = tratar_estado(comarca_split[0].strip())

        if dados['prc_comarca'] is None:
            comarca_split = prc['prc_localizacao'].split("-")
            prc['prc_comarca'] = comarca_split[1].strip()

        for in_pa in range(1,5):
            prc_promovente = self.driver.find_element_by_xpath('//*[@id="fDetalhar:dtbPoloAtivo'+str(in_pa)+'"]/tbody/tr/td/span')
            if prc_promovente:
                break

        prc_promovente = prc_promovente.text.strip()
        prc['prc_pessoa'] = 2 if prc_promovente.upper().find('CPNJ:') > -1 else 1

        # IDENTAR POSTERIORMENTE
        if dados['prc_promovido'] is None or dados['prc_cpf_cnpj'] is None or len(dados['prc_cpf_cnpj']) < 11 or \
                dados['prc_cpf_cnpj'] in ('Não cadastrado','Não Informado') or dados['prc_cpf_cnpj'].strip('0') == '':
            # CAPTURA NOME DO AUTOR
            divisor = ', CPNJ:' if prc['prc_pessoa'] == 2 else ', CPF:'
            proms = prc_promovente.split(divisor)
            prc_autor = proms[0]
            f = prc_autor.upper().find('REPRESENTAD')
            if f > -1:
                prc_autor = prc_autor[:f]
            prc['prc_autor'] = prc_autor.strip()
            prc_cpf_cnpj = proms[1].strip()
            if len(prc_cpf_cnpj) > 5:
                prc['prc_cpf_cnpj'] = proms[1].strip()


            # CAPTURA NOME DO RÉU
            for in_pa in range(1, 5):
                prc_promovido = self.driver.find_element_by_xpath('//*[@id="fDetalhar:dtbPoloPassivo'+ str(in_pa) + '"]/tbody/tr/td/span')
                if prc_promovido:
                    break

            if prc_promovido:
                prc_promovido = prc_promovido.text.strip()
                divisor = ', CPNJ:' if prc_promovido.upper().find('CPNJ:') > -1 else ', CPF:'
                proms = prc_promovido.split(divisor)
                prc['prc_promovido'] = proms[0]
                prc_cnpj_promovido = proms[1].replace('CPNJ:','').replace(':','').strip()
                if len(prc_cnpj_promovido) > 5:
                    prc['prc_cnpj_promovido'] = prc_cnpj_promovido

        prc_data_citacao = get_text(self.driver, 'fDetalhar:dataCitacao', tipo='ID')
        if prc_data_citacao:
            prc['prc_data_citacao'] = datetime.strptime(prc_data_citacao, '%d/%m/%Y')
            if prc['prc_data_citacao'].year < 1900:
                prc['prc_data_citacao'] = None

        if dados['prc_data'] is None:
            prc_data_cadastro = get_text(self.driver, 'fDetalhar:dataCadastro', tipo='ID')
            if prc_data_cadastro:
                prc['prc_data_cadastro'] = datetime.strptime(prc_data_cadastro, '%d/%m/%Y')
                if prc['prc_data_cadastro'].year < 1900:
                    prc['prc_data_cadastro'] = None
                prc['prc_data'] = prc['prc_data_cadastro']

        prc_data_envio = get_text(self.driver, 'fDetalhar:dataEnvioEscritorio', tipo='ID')
        if prc_data_envio:
            prc['prc_data_envio'] = datetime.strptime(prc_data_envio, '%d/%m/%Y')
            if prc['prc_data_envio'].year < 1900:
                prc['prc_data_envio'] = None

        prc_data_encerramento = get_text(self.driver, 'fDetalhar:dataEncerramento', tipo='ID')
        if prc_data_encerramento:
            prc['prc_data_encerramento'] = datetime.strptime(prc_data_encerramento, '%d/%m/%Y')
            if prc['prc_data_encerramento'].year < 1900:
                prc['prc_data_encerramento'] = None

        # CAPTURA PRODUTOS
        if dados['prc_produto'] is None:
            link_prod = self.driver.find_element_by_id('fDetalhar:imgVisualizarProdutos')
            if link_prod:
                link_prod.click()
                self.driver.switch_to.frame(self.driver.find_element_by_id('__jeniaPopupFrameTarget'))
                elements = self.driver.find_elements_by_xpath('//*[@id="fProcesso:dtbProdutos"]/tbody/tr')
                produtos = []
                for el in elements:
                    td1 = el.find_element_by_xpath('td[1]').text
                    td2 = el.find_element_by_xpath('td[2]').text
                    achei = False
                    for prd in produtos:
                        if prd['nome'] == td1 and prd['esp'] == td2:
                            achei = True
                            break

                    if not achei:
                        produtos.append({'nome': td1, 'esp': td2})

                self.driver.switch_to.default_content()
                self.driver.execute_script("hidePopupFrame();")
                if len(produtos) > 0:
                    prc['prc_produto'] = json.dumps(produtos)

        # FECHA ABA DADOS DO PROCESSO
        self.abre_fecha_aba('DADOS DO PROCESSO')

        # VERIFICA SE O NUMERO MUDOU. CASO SEJA DIFERENTE, SE FOR UM PROCESSO LOCALIZADO ANTERIOMENTE, ACRESCENTA UM NOVO, SE NÃO FOI LOCALIZADO, ALTERA O NUMERO
        fDetalhar_numero = self.driver.find_element_by_id('fDetalhar:numero')
        if fDetalhar_numero:
            prc_numero_processum = self.driver.find_element_by_id('fDetalhar:numero').text.strip()
            prc['prc_numero_processum'] = prc_numero_processum[:35]

            if prc['prc_numero_processum'] is None or prc['prc_numero_processum'] != dados['prc_numero_processum']:
                acps = Acompanhamento.lista_movs(base, dados['prc_id'], None)
                if len(acps) == 0:
                    prc['prc_numero'] = prc['prc_numero_processum']
                    # prc['prc_data_update'] = None
                    prc['prc_eproc'] = None
                    prc['prc_projudi'] = None
                    prc['prc_esaj'] = None
                    prc['prc_pje'] = None
                else:
                    prcs = Processo.get_processo_by_numero(base, prc['prc_numero_processum'])
                    if len(prcs) == 0:
                        Processo.insert(base, {'prc_numero': prc['prc_numero_processum'], 'prc_estado': dados['prc_estado'], 'prc_autor': dados['prc_autor'], 'prc_pai': dados['prc_id'], 'prc_area': dados['prc_area'], 'prc_carteira': dados['prc_carteira']})
                        prc['prc_numero_antigo'] = prc_numero_processum

            if dados['prc_numero'] == '0':
                prc['prc_numero'] = prc['prc_numero_processum']

        # ABRE ABA CONTINGÊNCIA
        if self.abre_fecha_aba('CONTINGÊNCIA'):
            prc_valor_provavel = self.driver.find_element_by_id('fDetalhar:valorProvavel2').text.strip()
            prc_valor_provavel = prc_valor_provavel.replace('.','').replace(',','.')
            prc['prc_valor_provavel'] = float(prc_valor_provavel)

            prc_valor_possivel = self.driver.find_element_by_id('fDetalhar:valorPossivel').text.strip()
            if prc_valor_possivel != '':
                prc_valor_possivel = prc_valor_possivel.replace('.','').replace(',','.')
                prc['prc_valor_possivel'] = float(prc_valor_possivel)

            # FECHA ABA CONTINGÊNCIA
            self.abre_fecha_aba('CONTINGÊNCIA')

        # ABRE ABA PAGAMENTO/GARANTIA
        self.abre_fecha_aba('PAGAMENTO')
        # CAPTURA SE O PROCESSO POSSUI PENHORA
        prc['prc_penhora'] = False
        elements = self.driver.find_elements_by_xpath('//*[@id="fDetalhar:dtbValoresPorData"]/tbody/tr')
        for el in elements:
            td4 =  el.find_elements_by_xpath('td[4]')
            if len(td4) == 0:
                continue

            img1 = el.find_elements_by_xpath('td[2]/a/img')
            img2 = el.find_elements_by_xpath('td[2]/img')

            if len(img1) > 0 or len(img2) > 0:
                prc['prc_penhora'] = True
                break

        # CAPTURA VALOR DA SENTENÇA
        elements = self.driver.find_elements_by_xpath('//*[@id="fDetalhar:dtbValoresPorData"]/tbody/tr')
        for el in elements:
            td5 =  el.find_elements_by_xpath('td[5]')
            if len(td5) == 0:
                continue

            tipo = td5[0].text.strip()
            if tipo == 'Condenação' or tipo == 'Acordo':
                valor = el.find_element_by_xpath('td[7]').text
                valor = valor.replace('.', '').replace(',', '.')
                prc['prc_valor_sentenca'] = valor

        # FECHA ABA PAGAMENTO/GARANTIA
        self.abre_fecha_aba('PAGAMENTO')


        # CAPTURA NÚMERO DA CONTA E DO TELEFONE
        if dados['prc_conta'] is None:
            # ABRE ABA DADOS DO CLIENTE
            self.abre_fecha_aba('DADOS DO CLIENTE')

            element = self.driver.find_element_by_xpath('//*[@id="fDetalhar:dtbReclamantes"]/tbody/tr/td[2]/table[1]/tbody/tr/td[1]/img')
            if element:
                element.click()
                aguarda_presenca_elemento(self.driver, '//*[@id="fDetalhar:dtbReclamantes"]/tbody/tr/td[2]/table[2]/tbody/tr/td', aguarda_visibilidade=True)
                prc['prc_conta'] = self.driver.find_element_by_xpath('//*[@id="fDetalhar:dtbReclamantes"]/tbody/tr/td[2]/table[1]/tbody/tr/td[2]').text.strip()
                prc['prc_fone'] = self.driver.find_element_by_xpath('//*[@id="fDetalhar:dtbReclamantes"]/tbody/tr/td[2]/table[2]/tbody/tr/td').text.strip()
            else:
                conta = self.driver.find_element_by_xpath('//*[@id="fDetalhar:dtbReclamantes"]/tbody/tr/td[2]/table[1]/tbody/tr/td[2]')
                if conta:
                    prc['prc_conta'] = get_text(self.driver, '//*[@id="fDetalhar:dtbReclamantes"]/tbody/tr/td[2]/table[1]/tbody/tr/td[1]')
            if 'prc_conta' in prc:
                prc['prc_conta'] = prc['prc_conta'].lstrip('0')
                prc['prc_conta'] = prc['prc_conta'][:20].strip()

            # FECHA ABA DADOS DO CLIENTE
            self.abre_fecha_aba('DADOS DO CLIENTE')

        # CAPTURA OS PROCESSOS VINCULADOS
        # ABRE ABA INCIDENTES
        self.abre_fecha_aba('INCIDENTE')

        elements = self.driver.find_elements_by_xpath('//*[@id="fDetalhar:dtbIncidente"]/tbody/tr')

        prc_vinculo_base = [] if dados['prc_vinculo'] is None else json.loads(dados['prc_vinculo'])
        prc_vinculo = []
        if len(elements) != len(prc_vinculo_base):
            for el in elements:
                td1 = el.find_element_by_xpath('td[1]/a').text
                m = re.search(r'[a-z]', td1, re.I)
                if m is not None:
                    a = m.start()
                    td1 = td1[:a-1]

                prcs = Processo.get_processo_by_numero(base, prc_sequencial=td1)
                if len(prcs) == 0:
                    print('processo Novo')

                    el.find_element_by_xpath('td[7]/a').click()
                    situacao = el.find_element_by_xpath('td[6]').text
                    objeto = el.find_element_by_xpath('td[2]').text
                    prc_id = Processo.insert(base, {'prc_sequencial': td1,'prc_numero': '0', 'prc_estado': dados['prc_estado'], 'prc_autor': dados['prc_autor'], 'prc_area': dados['prc_area'], 'prc_carteira': dados['prc_carteira'], 'prc_situacao': situacao, 'prc_numero_antigo': situacao, 'prc_objeto1': objeto})
                else:
                    prc_id = prcs[0]['prc_id']
                prc_vinculo.append(prc_id)

            prc['prc_vinculo'] = json.dumps(prc_vinculo)

        return prc

    # VERIFICA SE DEVE ALIMENTAR O OBJETO COM O VALOR DO ELEMENTO
    def alimentar(self, indice, dados, elemento, tipo='XPATH'):
        valor = get_text(self.driver, elemento, tipo=tipo)
        if valor:
            dados[indice] = valor

        return dados

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        partes = {'ativo':[], 'passivo':[], 'terceiro':[]}

        polos = {'ativo': 'fDetalhar:autor', 'passivo': 'fDetalhar:reu', 'terceiro': 'fDetalhar:terceiro'}
        for polo in polos:
            i = 0
            for in_polo in range(1, 5):
                prts = self.driver.find_elements_by_xpath('//*[@id="' + polos[polo] + str(in_polo) + '"]/tbody/tr[2]/td/div/table/tbody/tr/td')
                if len(prts) > 0:
                    break

            # prts = self.driver.find_elements_by_xpath('//*[@id="'+polos[polo]+'"]/tbody/tr[2]/td/div/table/tbody/tr/td')
            for prt in prts:
                txt = prt.text
                divisor = ', CPNJ:' if txt.upper().find('CPNJ:') > -1 else ', CPF:'

                proms = txt.split(divisor)
                prt_nome = proms[0]
                f = prt_nome.upper().find('REPRESENTAD')
                if f > -1:
                    prt_nome = prt_nome[:f]

                prt_cpf_cnpj = proms[1].strip()

                if prt_nome.strip() == '':
                    continue

                if prt_cpf_cnpj == '':
                    prt_cpf_cnpj = 'Não Informado'

                if prt_nome[-1] == '*':
                    prt_nome = prt_nome[:-1]

                partes[polo].append({'prt_nome': prt_nome, 'prt_cpf_cnpj': prt_cpf_cnpj})
                i += 1

        if len(partes['ativo'])==0:
            raise MildException("Parte Ativa Vazia", self.uf, self.plataforma, self.prc_id)

        return partes

    # CAPTURA ACOMPANHAMENTOS DO PROCESSO
    def acompanhamentos(self, proc_data, completo, base, pasta_intermediaria):
        '''
        :param datetime Última movimentação registrada na base
        :param bool Realiza a captura completa das movimentações
        :param int prc_id: id do processo
        :param Session base: conexão de destino
        '''

        self.abre_aba_acompanhamento()

        situacao = proc_data['prc_situacao'] if proc_data['prc_situacao'] is not None else self.driver.find_element_by_id('fAcompanhamento:situacao1').text.strip()
        prc_id = proc_data['prc_id']
        lista_db = Acompanhamento.lista_movs_docs(base, prc_id, self.plataforma, retornar_valores_unicos=True)
        lista_titanium = Acompanhamento.lista_movs(base, prc_id, 0)
        self.movs = []
        movs = []
        arquivos = []
        i = 2
        while True:
            linhas = self.driver.find_elements_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr')
            for indice, tr in enumerate(linhas):
                i_tr = str(indice+1)
                acp = {}
                if not self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr['+i_tr+']/td[9]/span'):
                    raise MildException("Erro ao capturar movimentação", self.uf, self.plataforma, self.prc_id)

                acp['acp_tipo'] = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr['+i_tr+']/td[9]/span').text
                acp['acp_esp'] = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[10]/span').text

                acp_cadastro = get_text(self.driver, '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[13]/span')
                acp['acp_cadastro'] = datetime.strptime(acp_cadastro, '%d/%m/%Y %H:%M') if acp_cadastro else None

                acp_data_evento = get_text(self.driver, '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[6]/a/span[1]')
                acp['acp_data_evento'] = datetime.strptime(acp_data_evento, '%d/%m/%Y') if acp_data_evento else None

                if acp['acp_cadastro'] is None:
                    acp['acp_cadastro'] = acp['acp_data_evento']

                acp_cumprimento = get_text(self.driver, '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[12]/span')
                acp['acp_cumprimento'] = datetime.strptime(acp_cumprimento, '%d/%m/%Y %H:%M') if acp_cumprimento else None

                acp_audiencia = get_text(self.driver, '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[8]/span[1]')
                acp['acp_audiencia'] = datetime.strptime(acp_audiencia, '%d/%m/%Y %H:%M') if acp_audiencia else None

                varrer, acp_base, lista_db = self.check_acp(lista_db, lista_titanium, acp)
                if not varrer:
                    continue

                acp['acp_id'] = acp_base['acp_id']

                acp_prazo = get_text(self.driver, '//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[11]/span[1]')
                acp['acp_prazo'] = datetime.strptime(acp_prazo, '%d/%m/%Y') if acp_prazo else None

                acp['acp_usuario'] = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr[' + i_tr + ']/td[15]/span').text

                incluir = True
                # CONFERE SE A MOVIMENTAÇÃO POSSUI DOCUMENTOS VINCULADOS
                # and (acp['acp_esp'] == 'Contrato' or acp['acp_esp'] == 'Emissão 2ª Via de fatura' or acp['acp_esp'].upper().find('RESGATE DE GRAVAÇÃO') > -1):
                acp['acp_sem_doc'] = acp_base['acp_sem_doc']
                if (acp['acp_tipo'] == 'Apuração' or acp['acp_esp'] == 'Obrigação de Pagar' or acp['acp_esp'] == 'Obrigação de Fazer') and situacao != 'Arquivo Morto':
                    radio = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbOcorrencia"]/tbody/tr['+i_tr+']/td[1]/table/tbody/tr/td/label/input')
                    if radio:
                        try:
                            radio.click()
                        except:
                            tb = traceback.format_exc(limit=1)
                            print(tb)
                            raise MildException("Erro ao clicar no radioButton "+acp_cadastro+" | "+acp['acp_tipo'], self.uf, self.plataforma, self.prc_id)

                        if acp['acp_tipo'] == 'Apuração' and acp['acp_esp'].find('Contestação') == 0:
                            comment = self.check_comments(acp, lista_titanium)
                            if comment:
                                movs.append(comment)

                        acp['acp_sem_doc'], arqs_acp = self.check_doc(base, prc_id, acp, pasta_intermediaria, acp_base)

                        if acp['acp_id'] is not None:
                            if acp_base['acp_sem_doc'] == acp['acp_sem_doc'] and acp_base['acp_cumprimento'] == acp['acp_cumprimento']:
                                incluir = False

                            # REMOVER APOS CONCILIAR A BASE. ESSE TRECHO SOMENTE ATUALIZA OS CASOS SEM USUARIO
                            if acp_base['acp_usuario'] is None:
                                incluir = True


                        if acp['acp_id'] is None and len(arqs_acp) > 0:
                            acp['acp_id'] = 'tmp-' + str(uuid.uuid1())

                        for pra in arqs_acp:
                            pra['pra_acp_id'] = acp['acp_id']

                        arquivos = arquivos+arqs_acp
                    elif acp['acp_id'] is not None:
                        incluir = False

                if incluir:
                    movs.append(acp)
                self.movs.append(acp)

            # CASO NA LISTA DE MOVIMENTAÇÕES JÁ EXISTENTES NA BASE CONTENHA ALGUMA DO TIPO "APURAÇÃO", FAZ A VARREDURA RETROATIVA PARA CONFERIR SE O ARQUIVO FOI LANÇADO
            if len(lista_db) > 0:
                if situacao == 'Arquivo Morto':
                    fim = True
                else:
                    fim = True
                    for li in lista_db:
                        if li['acp_tipo'] == 'Audiência':
                            semestre = datetime.today() + relativedelta(months=-6)
                            data_aud = li['acp_audiencia'] if li['acp_audiencia'] is not None else li['acp_data_evento']
                            if data_aud is not None:
                                if data_aud > semestre:
                                    fim = False
                                    break
                            
                        if (li['acp_tipo'] == 'Apuração' or li['acp_esp'] == 'Obrigação de Pagar' or li['acp_esp'] == 'Obrigação de Fazer'):
                            if li['acp_sem_doc'] is None or li['acp_sem_doc'] or (not li['acp_sem_doc'] and li['pra_id'] is None) or li['pra_erro']:
                                fim = False
                                break

                            if li['acp_esp'].find('Contestação') == 0:
                                achei = False
                                for lt in lista_titanium:
                                    if lt['acp_tipo'] == li['acp_tipo'] + ' - ' + li['acp_esp']:
                                        if li['acp_cadastro'] == lt['acp_cadastro']:
                                            achei = True
                                            break

                                if not achei:
                                    fim = False
                                    break

                        # REMOVER APOS CONCILIAR A BASE. ESSE TRECHO SOMENTE ATUALIZA OS CASOS SEM USUARIO
                        if li['acp_usuario'] is None:
                            fim = False
                            break

                if fim:
                    break

            # DETECTA SE EXISTE BOTÃO PARA IR PARA A PRÓXIMA PÁGINA E CLICA NELE
            proximo = self.driver.find_element_by_id('fAcompanhamento:scrollResultadosidx'+str(i))
            if not proximo:
                break

            try:
                self.driver.find_element_by_id('fAcompanhamento:scrollResultadosidx'+str(i)).click()
            except:
                raise MildException("Erro ao alternar página", self.uf, self.plataforma, self.prc_id)

            i += 1

        return movs, arquivos

    # CAPTURA AUDIENCIAS DO PROCESSO
    def audiencias(self):
        adcs = []
        for mov in self.movs:
            if mov['acp_audiencia'] is not None and mov['acp_tipo'] == 'Audiência':
                if mov['acp_audiencia'].year > 1000:
                    adcs.append({'adc_data': mov['acp_audiencia'], 'adc_tipo': mov['acp_esp'], 'adc_data_cadastro': mov['acp_cadastro']})

        return adcs

    # CONFERE SE A MOVIMENTAÇÃO PRECISA SER VARRIDA
    def check_acp(self, lista_db, lista_titanium, acp):
        varrer = True
        acp_base = {'acp_id': None, 'pra_erro': None, 'acp_sem_doc': None}
        for li in lista_db[:]:
            if li['acp_cadastro'] == acp['acp_cadastro'] and li['acp_tipo'] == acp['acp_tipo'] and li['acp_esp'] == acp['acp_esp']:
                varrer = True
                acp_base = li
                lista_db.remove(li)

                if acp['acp_tipo'] == 'Audiência':
                    semestre = datetime.today() + relativedelta(months=-6)
                    data_aud = acp['acp_audiencia'] if acp['acp_audiencia'] is not None else acp['acp_data_evento']
                    if data_aud is not None:
                        if data_aud >= semestre or acp['acp_cumprimento'] != li['acp_cumprimento']:
                            varrer = True
                        else:
                            varrer = False

                elif acp['acp_tipo'] != 'Apuração' and acp['acp_esp'] != 'Obrigação de Pagar' and acp['acp_esp'] != 'Obrigação de Fazer':
                    if acp['acp_cumprimento'] == li['acp_cumprimento']:
                        varrer = False

                else:
                    dois_anos = datetime.today() + relativedelta(months=-24)
                    if acp['acp_esp'] == 'Obrigação de Pagar' and (acp['acp_tipo'] == 'Sentença' or acp['acp_tipo'] == 'Acordo') and acp['acp_cadastro'] < dois_anos:
                        varrer = False
                    if acp['acp_tipo'] == 'Apuração' and acp['acp_esp'].find('Contestação') == 0:
                        for lt in lista_titanium:
                            if lt['acp_tipo'] == acp['acp_tipo']+' - '+acp['acp_esp']:
                                if acp['acp_cadastro'] == lt['acp_cadastro']:
                                    varrer = False
                    else:
                        if not li['acp_sem_doc'] and li['pra_id'] is not None:
                            varrer = False

                if li['pra_erro']:
                    varrer = True

                # REMOVER APOS CONCILIAR A BASE. ESSE TRECHO SOMENTE ATUALIZA OS CASOS SEM USUARIO
                if li['acp_usuario'] is None:
                    varrer = True

                break

        return varrer, acp_base, lista_db

    # CONFERE SE A MOVIMENTAÇÃO POSSUI DOCUMENTOS VINCULADOS
    def check_comments(self, acp, lista_titanium):
        lista_coment = self.driver.find_elements_by_xpath('//*[@id="fAcompanhamento:dtbComentario:tbody_element"]/tr')
        movs = []
        for indice, coment in enumerate(lista_coment):
            ind_str = str(indice+1)
            acp_titanium = acp.copy()
            del acp_titanium['acp_id']
            link_comment = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbComentario:tbody_element"]/tr['+ind_str+']/td[5]/a')
            if not link_comment:
                continue

            if link_comment.text.upper().find('AVALIAÇÃO') == -1:
                continue

            achei = False
            for lt in lista_titanium:
                if lt['acp_tipo'] == acp['acp_tipo'] + ' - ' + acp['acp_esp']:
                    if acp['acp_cadastro'] == lt['acp_cadastro']:
                        achei = True

            if achei:
                continue

            self.abrir_modal_comentario(ind_str)
            acp_titanium['acp_tipo'] = acp['acp_tipo'] + ' - ' + acp['acp_esp']
            acp_titanium['acp_esp'] = self.driver.find_element_by_xpath('//*[@id="fPopUp"]/textarea').text
            acp_titanium['acp_plataforma'] = 0

            self.fecha_modal()

            movs.append(acp_titanium)

        if len(movs) > 0:
            return movs[0]

        return False

    # CONFERE SE A MOVIMENTAÇÃO POSSUI DOCUMENTOS VINCULADOS
    def check_doc(self, base, prc_id, acp, pasta_intermediaria, acp_base):
        arquivos = []
        acp_sem_doc = True
        lista_coment = self.driver.find_elements_by_xpath('//*[@id="fAcompanhamento:dtbComentario:tbody_element"]/tr')
        for indice, coment in enumerate(lista_coment):
            ind_str = str(indice+1)

            link_coment = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbComentario:tbody_element"]/tr['+ind_str+']/td[7]/a')
            if not link_coment:
                continue

            pra_usuario = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbComentario:tbody_element"]/tr[' + ind_str + ']/td[3]/span').text
            pra_data = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbComentario:tbody_element"]/tr[' + ind_str + ']/td[1]/span').text
            pra_data = datetime.strptime(pra_data, '%d/%m/%Y %H:%M')
            descricao = self.driver.find_element_by_xpath('//*[@id="fAcompanhamento:dtbComentario:tbody_element"]/tr[' + ind_str + ']/td[5]/a')
            descricao = descricao.text if descricao else acp['acp_esp']

            pra_descricao = acp['acp_esp']
            if (acp['acp_tipo'] == 'Sentença' or acp['acp_tipo'] == 'Acordo') and acp['acp_esp'].upper().find('OBRIGAÇÃO DE PAGAR') > -1:
                if descricao.upper().find('SEGREGA') == -1:
                    pra_descricao += ' Comprovante'
                else:
                    continue

            self.abrir_modal_anexo(ind_str)

            arqs_base = []
            if 'pra_id' in acp_base and acp_base['pra_id'] is not None:
                arqs_base = ProcessoArquivo.select_by_acp(base, acp['acp_id'])

            anexos = self.driver.find_elements_by_xpath('//*[@id="fAnexo:dtbAnexos:tbody_element"]/tr/td[1]/a')
            for ind in range(1, len(anexos)+1):
                limpar_pasta(self.pasta_download)
                anexo = self.driver.find_element_by_xpath('//*[@id="fAnexo:dtbAnexos:tbody_element"]/tr['+str(ind)+']/td[1]/a')
                if not anexo:
                    self.fecha_modal()
                    self.abrir_modal_anexo(ind_str)
                    anexo = self.driver.find_element_by_xpath('//*[@id="fAnexo:dtbAnexos:tbody_element"]/tr[' + str(ind) + ']/td[1]/a')

                titulo_full = anexo.text
                titulo = titulo_full[:95]
                arb = {}
                arq = {'pra_id': None, 'pra_tentativas': 1, 'pra_plt_id': 1, 'pra_prc_id': prc_id}
                achei = False
                for arb in arqs_base:
                    if (arb['pra_data'] == pra_data or arb['pra_data'] == acp['acp_cadastro']) and ((len(arb['pra_original']) > 70 and arb['pra_original'] in titulo) or (arb['pra_original'][:80] == titulo[:80])):
                        arq['pra_id'] = arb['pra_id']
                        arq['pra_tentativas'] = arb['pra_tentativas']
                        achei = True
                        break

                if achei and arb['pra_erro'] is not None and not arb['pra_erro']:
                    continue

                baixar = False
                if acp['acp_tipo'] == 'Apuração':
                    if acp['acp_esp'].upper().find('RESGATE DE GRAVAÇÃO') > -1 or acp['acp_esp'].upper().find('EMISSÃO SPIC') > -1:
                        # acp_sem_doc = False
                        if not find_string(titulo_full, ('.docx', '.png', '.jpg','.msg','.partial')):
                            baixar = True
                        # else:
                            # acp_sem_doc = True
                    else:
                        # acp_sem_doc = True
                        if find_string(titulo_full, ('.pdf', '.zip', '.jpg', '.png', '.rar', '.docx','.doc','.xls','.xlsx',)):
                            # acp_sem_doc = False
                            baixar = True
                else:
                    if not find_string(titulo_full, ('.msg', '.partial',)):
                        baixar = True

                if baixar:
                    acp_sem_doc = False
                    arq['pra_id_tj'] = acp['acp_tipo'][0:29]
                    arq['pra_original'] = titulo
                    arq['pra_data'] = pra_data
                    arq['pra_usuario'] = pra_usuario
                    arq['pra_descricao'] = pra_descricao
                    arq['pra_excluido'] = False
                    arq['pra_erro'] = False
                    anexo.click()
                    result_download = aguarda_download(self.pasta_download, 1, tempo_nao_iniciado=30)
                    if not result_download:
                        limpar_pasta(self.pasta_download)
                        arq['pra_erro'] = True
                        arq['pra_arquivo'] = None
                        arq['pra_tentativas'] = arq['pra_tentativas'] + 1 if arq['pra_tentativas'] is not None else 1
                    else:
                        file_names = os.listdir(self.pasta_download)
                        pra_arquivo = trata_arquivo(file_names[0], self.pasta_download, pasta_intermediaria)
                        arq['pra_arquivo'] = pra_arquivo


                    arquivos.append(arq)

            self.fecha_modal()
            # self.driver.switch_to.default_content()
            # self.driver.find_element_by_xpath('//*[@id="popupFrameContainer"]/tbody/tr[1]/td/table/tbody/tr/td[2]').click()

        return acp_sem_doc, arquivos