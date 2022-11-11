import re

class RegexService:
    def __init__(self, rules = []):
        pass
        # self.rules = [
        #     [r'CONHECIDO O RECURSO .+ E NÃO-PROVIDO$', 'CONHECIDO O RECURSO ... E NÃO-PROVIDO', 'PJE-CE25'],
        #     [r'CONHECIDO O RECURSO .+ E PROVIDO$', 'CONHECIDO O RECURSO ... E PROVIDO', 'PJE-CE26'],
        #     [r'CONHECIDO O RECURSO .+ E PROVIDO EM PARTE$', 'CONHECIDO O RECURSO ... E PROVIDO EM PARTE', 'PJE-CE27'],
        #     [r'^DECLARADO IMPEDIMENTO POR ', 'DECLARADO IMPEDIMENTO POR \\"NOME DO MAGISTRADO\\"', 'PJE-RO37'],
        #     [r'^INDEFERIDO O PEDIDO DE ', 'INDEFERIDO O PEDIDO DE {#NOME-PARTE}', 'PJE-RO65'],
        #     [r'Conhecido o recurso de .+ e provido em parte$', 'Conhecido o recurso de #{nome_da_parte} e provido em parte', 'ESAJ-SC32'],
        #     [r'Conhecido o recurso de .+ e provido$', 'Conhecido o recurso de ... e provido', 'PROJUDI-BA60'],
        #     [r'Conhecido o recurso de .+ e provido em parte$', 'Conhecido o recurso de ... e provido em parte', 'PROJUDI-BA61']
        # ]

    def check_reg(self, a_string, b_string):
        a_string = a_string.replace('(', '').replace(')', '').replace('/','')
        b_string = b_string.replace('(', '').replace(')', '').replace('/','')
        result = re.search(r"(\${)([A-Za-z0-9-_?]+)(\})", a_string)
        if result:
            z_split = a_string.split(result.group(0))
            if result.group(0).find('?') > -1:
                reg = "(\s*)([^\s].+|[^\s]+)?(\s*)"
            else:
                reg = "(\s*)([^\s].+|[^\s]+)(\s*)"

            # if result.group(0).find('?') > -1:
            #     reg = "(\s*)([^\s]+)?(\s*)"
            # else:
            #     reg = "(\s*)([^\s]+)(\s*)"

            # if result.group(0).find('?') > -1:
            #     reg = "(\s*)([^\s].+)?(\s*)"
            # else:
            #     reg = "(\s*)([^\s].+)(\s*)"
            r_string = ''
            for index, z in enumerate(z_split):
                if z == '':
                    r_string += reg
                    continue
                if index == 0:
                    r_string += '(\A)'

                r_string += '(' + z.strip() + ")"

                if index < len(z_split) - 1:
                    r_string += reg

                if index == len(z_split) - 1:
                    r_string += '(\Z)'

            r_string = r_string.replace('()', "").strip()
            r_string = r_string.replace(reg + reg, reg).strip()
            r_string += '(?i)'
            result = re.search(r_string, b_string)
            if result:
                return result
        return None

    # def runRegexWithNumber(self, number, string):
    #     return re.findall(self.rules[number][0], string, re.IGNORECASE)

    def execute(self, string):
        for rule in self.rules:
            if re.findall(rule[0], string, re.IGNORECASE):
                return rule[1]
        return False