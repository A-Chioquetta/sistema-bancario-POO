from abc import ABC, abstractmethod
from colorama import Fore, Style, init
from datetime import datetime
import textwrap
from pathlib import Path
init(autoreset=True) # Initialize colorama

ROOT_PATH = Path(__file__).parent   

class ContasIterador:
    def __init__(self, contas):
        self.contas = contas
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        try:
            conta = self.contas[self._index]
            return f"""\
            Agência:\t{conta.agencia}
            Número:\t\t{conta.numero}
            Titular:\t{conta.cliente.nome}
            Saldo:\t\tR$ {conta.saldo:.2f}
        """
        except IndexError:
            raise StopIteration
        finally:
            self._index += 1

class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []
        self.indice_conta = 0
    
    def realizar_transacao(self, conta, transacao):
        transacao.registrar(conta)
    
    def adicionar_conta(self, conta):
        self.contas.append(conta)
        
class PessoaFisica(Cliente):
    def __init__(self, nome, data_nascimento, cpf, endereco):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: ('{self.nome}', '{self.cpf}')>"
                  
class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @classmethod
    def nova_conta(cls, cliente, numero):
        return cls(numero,cliente)
    
    @property
    def saldo(self):
        return self._saldo
    
    @property
    def numero(self):
        return self._numero
    
    @property
    def agencia(self):
        return self._agencia
    
    @property
    def cliente(self):
        return self._cliente
    
    @property
    def historico(self):
        return self._historico
        

    def sacar(self, valor):
        saldo = self.saldo
        excedeu_saldo = valor > saldo

        if excedeu_saldo:
            print("\n --- A operação falhou! Você não tem saldo suficiente. --- \n")
        
        elif valor > 0:
            self._saldo -= valor
            print("\n --- Saque realizado com sucesso! --- \n")    
            return True
        
        else:
            print("\n Operação falhou! O valor informado é inválido. --- \n")
        return False
        

    def depositar(self, valor):
        if valor > 0:
            self._saldo += valor
            print("\n --- Depósito realizado com sucesso! --- \n")
        else:
            print("\n --- Operação falhou! O valor informado é invalido. --- \n")
            return False
        return True

class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite = 500, limite_saques = 3):
        super().__init__(numero, cliente)
        self._limite = limite
        self._limite_saques = limite_saques

    @classmethod
    def nova_conta(cls, cliente, numero, limite, limite_saques):
        return cls(numero, cliente, limite, limite_saques)
    
    def sacar(self, valor):
        numero_saques = len(
            [transacao for transacao in self.historico.transacoes
             if transacao["tipo"] == Saque.__name__ ]
             )

        excedeu_limite = valor > self._limite
        excedeu_saques = numero_saques >= self._limite_saques

        if excedeu_limite:
            print("\n --- Operação falhou! O valor excede o limite. --- \n")

        elif excedeu_saques:
            print("\n --- Operação falhou! Número de saques excedido. --- \n")
        
        else:
            return super().sacar(valor)
        
        return False
    def __repr__(self):
        return f"<{self.__class__.__name__}: ('{self.agencia}', '{self.numero}', '{self.cliente.nome}')>"

    def __str__(self):
        return f""" \
                Agência: \t{self.agencia}
                C\c:\t{self.numero}
                Titular:\t{self.cliente.nome}
                """

class Historico:
    def __init__(self):
        self._transacoes = []
    
    @property
    def transacoes(self):
        return self._transacoes
    
    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )
    
    def gerar_relatorio(self, tipo_transacao=None):
        for transacao in self._transacoes:
            if tipo_transacao is None or transacao["tipo"].lower()== tipo_transacao.lower():
                yield transacao
                                                   
class Transacao(ABC):
    @property
    @abstractmethod
    def valor(self):
        pass

    @abstractmethod
    def registrar(self, conta):
        pass

class Saque(Transacao):
    def __init__(self,valor):
        self._valor = valor
    
    @property
    def valor(self):
        return self._valor
    
    def registrar(self, conta):
        sucesso_transacao = conta.sacar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)

class Deposito(Transacao):
    def __init__(self,valor):
        self._valor = valor
    
    @property
    def valor(self):
        return self._valor
    
    def registrar(self, conta):
        sucesso_transacao = conta.depositar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)

def log_transacao(func):
    def envelope(*args, **kwargs):
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        resultado = func(*args, **kwargs)
        with open(ROOT_PATH / "log.txt", "a", encoding="utf-8") as arquivo:
            arquivo.write(f"[{data_hora}] Função '{func.__name__}' executada com argumentos {args} e {kwargs}."
            f"Retornou {resultado}\n")
        return resultado

    return envelope

def menu():
    menu = """
    ======== MENU ========

    [D]\tDepositar
    [S]\tSacar
    [E]\tExtrato
    [NU]\tNovo usuário
    [NC]\tNova conta
    [LC]\tListar contas
    [Q]\tSair

    """
    return input(textwrap.dedent(menu)).upper()

def menu_extrato():
    menu = """
    ======== MENU EXTRATO ========

    [T]\tTodos
    [D]\tDepósitos
    [S]\tSaques
    [Q]\tVoltar ao menu principal

    """
    return input(textwrap.dedent(menu)).upper()

def filtrar_cliente(cpf, clientes):
    clientes_filtrados = [cliente for cliente in clientes if cliente.cpf == cpf]
    return clientes_filtrados[0] if clientes_filtrados else None


def recuperar_conta_cliente(cliente):
    if not cliente.contas:
        print("\n --- Cliente não possui conta! --- \n")
        return
    
    # FIXME: não permite cliente escolher a conta
    return cliente.contas[0]

@log_transacao
def depositar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n --- Cliente não encontrado! --- ")
        return
    
    valor = float(input("Informe o valor do depósito: R$"))
    transacao = Deposito(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, transacao)

@log_transacao
def sacar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n --- Cliente não encontrado! --- ")
        return
    
    valor = float(input("Informe o valor do saque: R$"))
    transacao = Saque(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, transacao)

@log_transacao
def exibir_extrato(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n --- Cliente não encontrado! --- \n")
        return
    
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return
    tipo_extrato = menu_extrato()
    if tipo_extrato == 'Q':
        return menu()
    
    print("\n ========== EXTRATO ========== \n")
    extrato = ""
    tem_transacoes = False
    if tipo_extrato == 'S':
        tipo_transacao = 'saque'
        for transacao in conta.historico.gerar_relatorio(tipo_transacao=tipo_transacao):
            tem_transacoes = True
            extrato += Fore.RED + f"\n{transacao['tipo']}:\t\t R$:{transacao['valor']:.2f}\t\t{transacao['data']}"
    elif tipo_extrato == 'D':
        tipo_transacao = 'deposito'
        for transacao in conta.historico.gerar_relatorio(tipo_transacao=tipo_transacao):
            tem_transacoes = True
            extrato +=Fore.BLUE + f"\n{transacao['tipo']}:\t R$:{transacao['valor']:.2f}\t\t{transacao['data']}"
    elif tipo_extrato == 'T':
        for transacao in conta.historico.gerar_relatorio(tipo_transacao=None):
            tem_transacoes = True
            if transacao['tipo'].lower() == 'saque':
                extrato += Fore.RED + f"\n{transacao['tipo']}:\t\t R$:{transacao['valor']:.2f}\t\t{transacao['data']}"
            else:
                extrato +=Fore.BLUE + f"\n{transacao['tipo']}:\t R$:{transacao['valor']:.2f}\t\t{transacao['data']}"
    else:
        print("\n --- Opção inválida, por favor selecione novamente a operação desejada. --- \n")
        return menu_extrato()
    
    if not tem_transacoes:
        extrato = "Não foram realizadas movimentações"

    print(extrato)
    print(f"\nSaldo:\t\tR$ {conta.saldo:.2f}")
    print("=============================")

@log_transacao
def criar_cliente(clientes):
    cpf = input("Informe o CPF (somente números): ")
    cliente = filtrar_cliente(cpf, clientes)

    if cliente:
        print("\n --- Já existe cliente com esse CPF! --- ")
        return
    
    nome = input("Informe o nome completo: ")
    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
    endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): ")

    cliente = PessoaFisica(nome=nome, data_nascimento=data_nascimento, cpf=cpf, endereco=endereco)
    clientes.append(cliente)

    print("\n ==== Cliente criado com sucesso! ==== \n")

@log_transacao
def criar_conta(numero_conta, clientes, contas):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n --- Cliente não encontrado. Fluxo de criação de conta encerrado! ---")
        return

    conta = ContaCorrente.nova_conta(cliente=cliente, numero=numero_conta, limite=500, limite_saques=3)
    contas.append(conta)
    cliente.contas.append(conta)

    print("\n === Conta criada com sucesso! === \n")

def listar_contas(contas):
    for conta in contas:
        print(textwrap.dedent(str(conta)))

def main():
    clientes = []
    contas = []

    while True:
        opcao = menu()

        if opcao == "D":
            print("==== Depósito ====")
            depositar(clientes)

        elif opcao == "S":
            print("==== Saque ====")
            sacar(clientes)
            
        elif opcao == "E":
            print("==== Extrato ====")
            exibir_extrato(clientes)
            
        elif opcao == "NU":
            print("=== Criar novo usuário ===")
            criar_cliente(clientes)
              
        elif opcao == "NC":
            print("=== Criar nova conta ===")
            numero_conta = len(contas) + 1
            criar_conta(numero_conta,clientes,contas)
            
        elif opcao == "LC":
            print("=== Lista de contas === \n")
            listar_contas(contas)
           
        elif opcao == "Q":
            break

        else:
            print("Opção inválida, por favor selecione novamente a operação desejada.")


main()