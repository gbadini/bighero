from Controllers.Tribunais.Pje._pje import *
from Controllers.Tribunais.segundo_grau import *
# from Models.recursoModel import *
import time


# CLASSE DA VARREDURA DO PJE DE SEGUNDO GRAU. HERDA OS METODOS DAS CLASSES PLATAFORMA e PJE
class Pje2g(SegundoGrau, Pje):

    # CONFERE SE OS RECURSOS ESTÃO NA BASE CASO EXISTA MAIS DE UM
    def confere_recursos(self, base, proc):
        recs = self.driver.find_elements_by_xpath('//*[@id="fPP:processosTable:tb"]/tr')

        if proc['rec_id'] is not None and proc['rec_codigo'] is None:
            td2 = recs[0].find_element_by_xpath('td[2]')
            id = td2.get_attribute('id')
            f_id = id.split(':')
            Recurso.update_simples(base, proc['rec_id'], {'rec_codigo': f_id[2],})
            return False

        if len(recs) == 1 and proc['rec_codigo'] is not None:
            return True

        if len(recs) > 1:
            recs.pop(0)

        achei = True
        for rec in recs:
            td2 = rec.find_element_by_xpath('td[2]')
            id = td2.get_attribute('id')
            f_id = id.split(':')
            result = Recurso.select(base, proc['prc_id'], f_id[2])
            if len(result) == 0:
                achei = False
                Recurso.insert(base, {'rec_prc_id': proc['prc_id'], 'rec_codigo': f_id[2], 'rec_numero': td2.text.strip(),'rec_plt_id':self.plataforma})

        return achei

    # CONFERE SE PROCESSO CORRE EM SEGREDO DE JUSTIÇA
    def confere_segredo(self, numero_busca, codigo=None):
        self.confere_cnj(numero_busca)

        achei = False
        if check_text(self.driver, '//*[@id="fPP:processosPeticaoGridPanel_body"]/dl', 'sigilo'):
            achei = True

        trs = self.driver.find_elements_by_xpath('//*[@id="fPP:processosTable:tb"]/tr')

        if len(trs) == 1 and achei:
            return True

        i = 1
        for tr in trs:
            td2 = tr.find_element_by_xpath('td[1]/a[1]')
            f_id = td2.get_attribute('onclick')
            # f_id = id.split(':')
            if f_id.find(codigo) > -1:
                exc = tr.find_elements_by_class_name('fa-exclamation-circle')
                if exc:
                    achei = True

                if achei:
                    if len(tr.find_elements_by_xpath('td[1]/a[2]')) == 0:
                        return True

                self.abre_aba_processo(index=i)
                self.wait(10)
                break

            i += 1

        if check_text(self.driver, '//*[@id="pageBody"]/div/div[2]/pre/dl', 'Sem permissão para acessar a página'):
            self.fecha_processo()
            self.abre_aba_processo(index=i)
            self.wait(10)
            if check_text(self.driver, '//*[@id="pageBody"]/div/div[2]/pre/dl', 'Sem permissão para acessar a página'):
                raise MildException("Erro de permissão", self.uf, self.plataforma, self.prc_id)

        erro = self.driver.find_element_by_class_name('alert-danger')
        if erro:
            if erro.text.upper().find('Erro inesperado') > -1:
                raise CriticalException("Erro ao abrir processo (Unhandled Exception)", self.uf, self.plataforma, self.prc_id)

        return False

    # CAPTURA DADOS DO PROCESSO
    def dados(self, status_atual):
        rec = {}
        xpaths = ('//*[@id="maisDetalhes"]/dl/dt','//*[@id="maisDetalhes"]/div[1]/dl/dt',)
        campos = {'Julgador': 'rec_orgao', 'Assunto': 'rec_assunto', 'Classe': 'rec_classe', 'Valor': 'rec_valor', 'Segredo': 'rec_segredo',  'Relator': 'rec_relator', 'distribuição': 'rec_distribuicao',}
        for xp in xpaths:
            dts = self.driver.find_elements_by_xpath(xp)
            i = 0
            for dt in dts:
                i += 1
                titulo = dt.text
                campo = ''
                for c in campos:
                    if titulo.upper().find(c.upper()) > -1:
                        campo = campos[c]
                        break

                if campo == '':
                    continue

                conteudo = self.driver.find_element_by_xpath(xp[:-2]+'dd['+str(i)+']').text
                rec[campo] = conteudo

        if len(rec) == 0:
            raise MildException("Erro ao abrir processo", self.uf, self.plataforma, self.prc_id, False)

        if 'rec_segredo' in rec:
            rec['rec_segredo'] = True if rec['rec_segredo'] == 'SIM' else False

        if 'rec_distribuicao' in rec:
            data_dist = localiza_data(rec['rec_distribuicao'])
            if not data_dist:
                del rec['rec_distribuicao']
            else:
                rec['rec_distribuicao'] = data_dist

        rec['rec_status'] = get_status(self.movs, status_atual, grau=2)

        numero2 = self.driver.find_element_by_xpath('//*[@id="navbar"]/ul/li/a[1]').text
        r = re.search("((\\d+)(-)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+)(\\.)(\\d+))", numero2, re.IGNORECASE | re.DOTALL)
        if r is not None:
            rec['rec_numero'] = r.group(0)

        return rec

    # CAPTURA PARTES DO PROCESSO
    def partes(self):
        element = self.driver.find_element_by_class_name("mais-detalhes")
        self.driver.execute_script("arguments[0].className += ' open'", element)

        # self.driver.find_element_by_xpath('//*[@id="navbar"]/ul/li/a[1]').click()

        partes = {'ativo':[], 'passivo':[]}
        aguarda_presenca_elemento(self.driver, '//*[@id="poloAtivo"]/table/tbody/tr')

        inicio = time.time()
        while True:
            try:
                wait = WebDriverWait(self.driver, 2)
                wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="poloAtivo"]/table/tbody/tr[1]')))
                break
            except TimeoutException:
                self.wait()
                if time.time() - inicio > 15:
                    foca_janela(self.process_children)
                    break
                # self.driver.find_element_by_xpath('//*[@id="navbar"]/ul/li/a[1]').click()


        if not self.driver.find_element_by_xpath('//*[@id="navbar"]/ul/li/a[1]').is_displayed():
            raise MildException("Erro ao abrir processo (partes não carregadas)", self.uf, self.plataforma, self.prc_id, False)

        polos = {'ativo': 'poloAtivo', 'passivo': 'poloPassivo'}
        tipos = {'ativo': 'X', 'passivo': 'Y'}
        for polo in polos:
            i = 0
            prts = self.driver.find_elements_by_xpath('//*[@id="'+polos[polo]+'"]/table/tbody/tr')
            for prt in prts:
                c = localiza_elementos(prt, ('td[1]/span[1]', 'td[1]/a[1]'))
                txt = c.text
                p1 = txt.find(':')
                if p1 == -1:
                    cpf = 'Não Informado'
                else:
                    cpf = txt[p1+1:]
                    p2 = 0
                    while p2 > -1:
                        p2 = cpf.rfind('(')
                        if p2 > -1:
                            tipos[polo] = cpf[p2:]
                            cpf = cpf[:p2].strip()


                p1 = txt.find(' - ')
                if p1 > -1:
                    nome = txt[:p1]
                else:
                    p1 = 0
                    nome = txt
                    while p1 >-1:
                        p1 = nome.rfind('(')
                        if p1 > -1:
                            nome = nome[:p1].strip()

                if nome.strip() == '':
                    continue

                partes[polo].append({'prt_nome': nome, 'prt_cpf_cnpj': cpf})
                i += 1

        if len(partes['ativo']) == 0:
            raise MildException("Parte Ativa Vazia", self.uf, self.plataforma, self.prc_id)

        if tipos['ativo'] == tipos['passivo']:
            return {'ativo': [{'prt_nome': 'AMBOS',}, ],}

        return partes