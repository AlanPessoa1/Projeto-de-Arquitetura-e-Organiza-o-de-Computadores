import json


# ---------------------------------------------------------
# Tabelas de identificação das instruções
# ---------------------------------------------------------

# Instruções do tipo R com formato:
# nome $rd, $rs, $rt
funcoes_r = {
    32: "add",
    33: "addu",
    34: "sub",
    35: "subu",
    36: "and",
    37: "or",
    38: "xor",
    39: "nor",
    42: "slt"
}

# Instruções de deslocamento com valor imediato:
# nome $rd, $rt, shamt
funcoes_shift = {
    0: "sll",
    2: "srl",
    3: "sra"
}

# Instruções de deslocamento cujo valor vem de outro registrador:
# nome $rd, $rt, $rs
funcoes_shift_variavel = {
    4: "sllv",
    6: "srlv",
    7: "srav"
}

# Multiplicação e divisão:
# nome $rs, $rt
funcoes_mult_div = {
    24: "mult",
    25: "multu",
    26: "div",
    27: "divu"
}

# Instruções que movem HI ou LO para um registrador:
# nome $rd
funcoes_mf = {
    16: "mfhi",
    18: "mflo"
}

# Instruções do tipo I com operando imediato
instrucoes_i = {
    8: "addi",
    9: "addiu",
    10: "slti",
    12: "andi",
    13: "ori",
    14: "xori"
}

# Instruções de acesso à memória:
# nome $rt, offset($rs)
instrucoes_memoria = {
    32: "lb",
    35: "lw",
    36: "lbu",
    40: "sb",
    43: "sw"
}

# Branches que utilizam dois registradores
instrucoes_branch_dois_regs = {
    4: "beq",
    5: "bne"
}

# Branches que utilizam apenas um registrador
instrucoes_branch_um_reg = {
    6: "blez",
    7: "bgtz"
}


# ---------------------------------------------------------
# Função responsável pela decodificação de uma instrução
# ---------------------------------------------------------

def decodificar(instrucao_hex):
    # Converte a instrução hexadecimal para inteiro
    instrucao = int(instrucao_hex, 16)

    # Representa a instrução usando exatamente 32 bits
    instrucao_bin = format(instrucao, "032b")

    # -----------------------------------------------------
    # Separação dos campos da instrução MIPS
    # -----------------------------------------------------

    opcode_bin = instrucao_bin[0:6]
    rs_bin = instrucao_bin[6:11]
    rt_bin = instrucao_bin[11:16]
    rd_bin = instrucao_bin[16:21]
    shamt_bin = instrucao_bin[21:26]
    funct_bin = instrucao_bin[26:32]

    # Nas instruções do tipo I, os últimos 16 bits
    # representam o valor imediato
    imediato_bin = instrucao_bin[16:32]

    # -----------------------------------------------------
    # Conversão dos campos binários para decimal
    # -----------------------------------------------------

    opcode = int(opcode_bin, 2)
    rs = int(rs_bin, 2)
    rt = int(rt_bin, 2)
    rd = int(rd_bin, 2)
    shamt = int(shamt_bin, 2)
    funct = int(funct_bin, 2)
    imediato = int(imediato_bin, 2)

    # Algumas instruções utilizam um imediato de 16 bits
    # com sinal. Caso o bit mais significativo seja 1,
    # o valor é negativo em complemento de dois.
    imediato_com_sinal = imediato

    if imediato >= 32768:
        imediato_com_sinal = imediato - 65536

    # -----------------------------------------------------
    # Decodificação das instruções do tipo R
    # -----------------------------------------------------

    if opcode == 0:
        if funct in funcoes_r:
            nome = funcoes_r[funct]
            assembly = f"{nome} ${rd}, ${rs}, ${rt}"

        elif funct in funcoes_shift:
            nome = funcoes_shift[funct]
            assembly = f"{nome} ${rd}, ${rt}, {shamt}"

        elif funct in funcoes_shift_variavel:
            nome = funcoes_shift_variavel[funct]
            assembly = f"{nome} ${rd}, ${rt}, ${rs}"

        elif funct in funcoes_mult_div:
            nome = funcoes_mult_div[funct]
            assembly = f"{nome} ${rs}, ${rt}"

        elif funct in funcoes_mf:
            nome = funcoes_mf[funct]
            assembly = f"{nome} ${rd}"

        elif funct == 8:
            nome = "jr"
            assembly = f"jr ${rs}"

        elif funct == 12:
            nome = "syscall"
            assembly = "syscall"

        else:
            nome = None
            assembly = "instrução R desconhecida"

    # -----------------------------------------------------
    # Decodificação das instruções do tipo I
    # -----------------------------------------------------

    elif opcode in instrucoes_i:
        nome = instrucoes_i[opcode]

        # andi, ori e xori utilizam imediato sem sinal
        if nome in ["andi", "ori", "xori"]:
            assembly = f"{nome} ${rt}, ${rs}, {imediato}"

        else:
            assembly = f"{nome} ${rt}, ${rs}, {imediato_com_sinal}"

    # lui utiliza apenas rt e imediato
    elif opcode == 15:
        nome = "lui"
        assembly = f"lui ${rt}, {imediato}"

    # Instruções de acesso à memória
    elif opcode in instrucoes_memoria:
        nome = instrucoes_memoria[opcode]
        assembly = f"{nome} ${rt}, {imediato_com_sinal}(${rs})"

    # Branches com dois registradores
    elif opcode in instrucoes_branch_dois_regs:
        nome = instrucoes_branch_dois_regs[opcode]
        assembly = f"{nome} ${rs}, ${rt}, {imediato_com_sinal}"

    # Branches com apenas um registrador
    elif opcode in instrucoes_branch_um_reg:
        nome = instrucoes_branch_um_reg[opcode]
        assembly = f"{nome} ${rs}, {imediato_com_sinal}"

    # bltz possui opcode próprio dentro das instruções exigidas
    elif opcode == 1:
        nome = "bltz"
        assembly = f"bltz ${rs}, {imediato_com_sinal}"

    # -----------------------------------------------------
    # Decodificação das instruções do tipo J
    # -----------------------------------------------------

    elif opcode == 2:
        nome = "j"
        alvo = int(instrucao_bin[6:32], 2)
        assembly = f"j {alvo}"

    elif opcode == 3:
        nome = "jal"
        alvo = int(instrucao_bin[6:32], 2)
        assembly = f"jal {alvo}"

    else:
        nome = None
        assembly = "instrução desconhecida"

    # Campos que a etapa de execução precisa para calcular o efeito
    # da instrução sobre os registradores, a memória e o PC.
    campos = {
        "rs": rs,
        "rt": rt,
        "rd": rd,
        "shamt": shamt,
        "imediato": imediato,
        "imediato_com_sinal": imediato_com_sinal,
        # Endereço de 26 bits dos saltos j e jal
        "alvo": instrucao & 0x03FFFFFF
    }

    return nome, assembly, campos


# ---------------------------------------------------------
# Constantes e funções auxiliares para valores de 32 bits
# ---------------------------------------------------------

MASCARA_32_BITS = 0xFFFFFFFF

def para_signed32(valor):
    # Reinterpreta um valor de 32 bits sem sinal como um inteiro
    # em complemento de dois (necessário para add/sub com números
    # negativos, comparações com slt/slti, shifts aritméticos etc.)
    valor &= MASCARA_32_BITS
    if valor >= 0x80000000:
        valor -= 0x100000000
    return valor


def valor_para_uint32(valor):
    # O campo "config" pode trazer números decimais (inclusive
    # negativos) ou strings hexadecimais como "0x10008000".
    if isinstance(valor, str):
        valor = int(valor, 16) if valor.lower().startswith("0x") else int(valor)
    return valor & MASCARA_32_BITS


# ---------------------------------------------------------
# Memória (Entrega 3)
#
# A memória é endereçada a byte: cada posição guarda um dado de
# 8 bits. Ela é armazenada de forma esparsa (dicionário
# endereço -> byte), então só ocupa espaço o que foi escrito, e
# endereços nunca escritos valem zero.
#
# Assim como no MARS, as words são armazenadas em little-endian:
# o byte menos significativo fica no menor endereço.
# ---------------------------------------------------------

# Segmentos de memória com os endereços base usados pelo MARS.
# Cada um suporta bem mais que as 1024 entradas mínimas exigidas.
SEGMENTOS = [
    # nome,   primeiro endereço, último endereço
    ("text",  0x00400000,        0x0FFFFFFF),  # código (.text)
    ("data",  0x10000000,        0x1007FFFF),  # .extern, $gp, .data (0x10010000) e heap
    ("stack", 0x7FFF0000,        0x7FFFFFFF),  # pilha ($sp = 0x7fffeffc)
]


class Memoria:
    def __init__(self):
        self.bytes = {}

    def segmento(self, endereco):
        for nome, inicio, fim in SEGMENTOS:
            if inicio <= endereco <= fim:
                return nome
        return None

    def _gravar_byte(self, endereco, valor):
        valor &= 0xFF
        if valor == 0:
            self.bytes.pop(endereco, None)
        else:
            self.bytes[endereco] = valor

    def _juntar_word(self, endereco):
        valor = 0
        for i in range(4):
            valor |= self.bytes.get(endereco + i, 0) << (8 * i)
        return valor

    # ----- acesso a byte (lb, lbu, sb) -----

    def ler_byte(self, endereco):
        return self.bytes.get(endereco & MASCARA_32_BITS, 0)

    def escrever_byte(self, endereco, valor):
        self._gravar_byte(endereco & MASCARA_32_BITS, valor)

    # ----- acesso a word de 4 bytes (lw, sw, busca de instrução) -----

    def ler_word(self, endereco):
        return self._juntar_word(endereco & MASCARA_32_BITS)

    def escrever_word(self, endereco, valor):
        endereco &= MASCARA_32_BITS
        valor &= MASCARA_32_BITS
        for i in range(4):
            self._gravar_byte(endereco + i, valor >> (8 * i))

    # ----- instantâneo para o arquivo de saída -----

    def montar_mem(self):
        # Apresenta a memória de dados (segmentos data e stack) agrupada
        # em words, em decimal, em ordem crescente de endereço e apenas
        # com as words diferentes de zero. O segmento text guarda as
        # próprias instruções do programa e por isso não é listado.
        enderecos_words = sorted({endereco & ~3 for endereco in self.bytes
                                  if self.segmento(endereco) != "text"})
        mem = {}
        for endereco in enderecos_words:
            valor = self._juntar_word(endereco)
            if valor != 0:
                mem[str(endereco)] = para_signed32(valor)
        return mem


# ---------------------------------------------------------
# Estado da CPU: banco de 32 registradores, os registradores
# especiais PC, HI e LO, a memória e a saída padrão (stdout)
# ---------------------------------------------------------

class EstadoCPU:
    def __init__(self):
        self.registradores = [0] * 32

        # Valores de inicialização do MARS: todos os registradores
        # começam zerados, exceto $gp, $sp e o PC.
        self.registradores[28] = 0x10008000  # $gp
        self.registradores[29] = 0x7fffeffc  # $sp

        self.hi = 0
        self.lo = 0
        self.pc = 0x00400000

        self.memoria = Memoria()

        # Texto acumulado da saída do programa (ex.: "overflow"),
        # assim como o console do MARS.
        self.stdout = []

    def ler(self, indice):
        return self.registradores[indice]

    def escrever(self, indice, valor):
        # $0 é fixo em zero: qualquer escrita nele é ignorada
        if indice != 0:
            self.registradores[indice] = valor & MASCARA_32_BITS

    def aplicar_regs(self, regs):
        # Depois da inicialização padrão do MARS, os valores de
        # config.regs são aplicados, podendo sobrescrever $gp, $sp,
        # pc, hi e lo.
        for chave, valor in regs.items():
            valor_uint32 = valor_para_uint32(valor)
            nome = chave.lstrip("$").lower()

            if nome == "pc":
                self.pc = valor_uint32
            elif nome == "hi":
                self.hi = valor_uint32
            elif nome == "lo":
                self.lo = valor_uint32
            else:
                self.escrever(int(nome), valor_uint32)

    def aplicar_config(self, config):
        # config.regs: registradores pré-carregados
        # config.mem: words pré-carregadas na memória
        self.aplicar_regs(config.get("regs") or {})
        self.carregar_words(config.get("mem") or {})

    def carregar_words(self, words):
        # Carrega pares "endereço": valor (config.mem e .data) na
        # memória antes da execução.
        for endereco, valor in words.items():
            self.memoria.escrever_word(valor_para_uint32(endereco), valor_para_uint32(valor))


# ---------------------------------------------------------
# Execução das instruções
#   Entrega 2: lógicas e aritméticas
#   Entrega 3: load, store e desvio
#
# Quando executar() é chamada, estado.pc já aponta para a
# instrução seguinte (PC + 4), que é a base dos desvios.
# ---------------------------------------------------------

def soma_com_overflow(a, b, estado, destino):
    # Soma com sinal usada por add, sub e addi. Se o resultado não
    # couber em 32 bits com sinal, ocorre overflow: assim como no
    # MIPS, o registrador destino não é alterado, e a ocorrência é
    # registrada no stdout.
    resultado = para_signed32(a) + b
    if resultado < -0x80000000 or resultado > 0x7FFFFFFF:
        estado.stdout.append("overflow")
    else:
        estado.escrever(destino, resultado)


def desviar(estado, condicao, deslocamento):
    # Desvio condicional: o deslocamento é contado em instruções
    # (words) a partir de PC + 4.
    if condicao:
        estado.pc = (estado.pc + (deslocamento << 2)) & MASCARA_32_BITS


def saltar(estado, alvo):
    # j/jal: os 4 bits mais significativos vêm de PC + 4 e os 26 bits
    # do campo alvo são deslocados 2 posições (endereço de word).
    estado.pc = (estado.pc & 0xF0000000) | (alvo << 2)


def executar(nome, campos, estado):
    rs = estado.ler(campos["rs"])
    rt = estado.ler(campos["rt"])
    rd = campos["rd"]
    destino_i = campos["rt"]
    shamt = campos["shamt"]
    imediato = campos["imediato"]
    imediato_com_sinal = campos["imediato_com_sinal"]
    memoria = estado.memoria

    # Endereço efetivo das instruções de memória: base + offset
    endereco = (rs + imediato_com_sinal) & MASCARA_32_BITS

    # ----- Entrega 2: lógicas e aritméticas -----

    # add, sub e addi geram exceção de overflow; addu, subu e addiu não.
    if nome == "add":
        soma_com_overflow(rs, para_signed32(rt), estado, rd)

    elif nome == "addu":
        estado.escrever(rd, rs + rt)

    elif nome == "sub":
        soma_com_overflow(rs, -para_signed32(rt), estado, rd)

    elif nome == "subu":
        estado.escrever(rd, rs - rt)

    elif nome == "and":
        estado.escrever(rd, rs & rt)

    elif nome == "or":
        estado.escrever(rd, rs | rt)

    elif nome == "xor":
        estado.escrever(rd, rs ^ rt)

    elif nome == "nor":
        estado.escrever(rd, ~(rs | rt))

    elif nome == "slt":
        estado.escrever(rd, 1 if para_signed32(rs) < para_signed32(rt) else 0)

    elif nome == "sll":
        estado.escrever(rd, rt << shamt)

    elif nome == "srl":
        estado.escrever(rd, rt >> shamt)

    elif nome == "sra":
        estado.escrever(rd, para_signed32(rt) >> shamt)

    elif nome == "sllv":
        estado.escrever(rd, rt << (rs & 0x1F))

    elif nome == "srlv":
        estado.escrever(rd, rt >> (rs & 0x1F))

    elif nome == "srav":
        estado.escrever(rd, para_signed32(rt) >> (rs & 0x1F))

    elif nome == "mult":
        produto = (para_signed32(rs) * para_signed32(rt)) & ((1 << 64) - 1)
        estado.hi = (produto >> 32) & MASCARA_32_BITS
        estado.lo = produto & MASCARA_32_BITS

    elif nome == "multu":
        produto = rs * rt
        estado.hi = (produto >> 32) & MASCARA_32_BITS
        estado.lo = produto & MASCARA_32_BITS

    elif nome == "div":
        dividendo = para_signed32(rs)
        divisor = para_signed32(rt)
        # Divisão por zero é comportamento indefinido no MIPS real;
        # aqui optamos por simplesmente não alterar HI/LO.
        if divisor != 0:
            quociente = abs(dividendo) // abs(divisor)
            if (dividendo < 0) != (divisor < 0):
                quociente = -quociente
            resto = dividendo - quociente * divisor
            estado.lo = quociente & MASCARA_32_BITS
            estado.hi = resto & MASCARA_32_BITS

    elif nome == "divu":
        if rt != 0:
            estado.lo = (rs // rt) & MASCARA_32_BITS
            estado.hi = (rs % rt) & MASCARA_32_BITS

    elif nome == "mfhi":
        estado.escrever(rd, estado.hi)

    elif nome == "mflo":
        estado.escrever(rd, estado.lo)

    elif nome == "addi":
        soma_com_overflow(rs, imediato_com_sinal, estado, destino_i)

    elif nome == "addiu":
        estado.escrever(destino_i, rs + imediato_com_sinal)

    elif nome == "slti":
        estado.escrever(destino_i, 1 if para_signed32(rs) < imediato_com_sinal else 0)

    elif nome == "andi":
        estado.escrever(destino_i, rs & imediato)

    elif nome == "ori":
        estado.escrever(destino_i, rs | imediato)

    elif nome == "xori":
        estado.escrever(destino_i, rs ^ imediato)

    # ----- Entrega 3: load e store -----

    elif nome == "lui":
        estado.escrever(destino_i, imediato << 16)

    elif nome == "lw":
        estado.escrever(destino_i, memoria.ler_word(endereco))

    elif nome == "sw":
        memoria.escrever_word(endereco, rt)

    elif nome == "lb":
        # Byte com extensão de sinal
        byte = memoria.ler_byte(endereco)
        estado.escrever(destino_i, byte - 256 if byte >= 128 else byte)

    elif nome == "lbu":
        # Byte com extensão de zeros
        estado.escrever(destino_i, memoria.ler_byte(endereco))

    elif nome == "sb":
        # Grava apenas os 8 bits menos significativos de rt
        memoria.escrever_byte(endereco, rt)

    # ----- Entrega 3: desvios condicionais -----

    elif nome == "beq":
        desviar(estado, rs == rt, imediato_com_sinal)

    elif nome == "bne":
        desviar(estado, rs != rt, imediato_com_sinal)

    elif nome == "bltz":
        desviar(estado, para_signed32(rs) < 0, imediato_com_sinal)

    # ----- Entrega 3: saltos -----

    elif nome == "j":
        saltar(estado, campos["alvo"])

    elif nome == "jal":
        # Guarda o endereço de retorno (PC + 4) em $ra ($31)
        estado.escrever(31, estado.pc)
        saltar(estado, campos["alvo"])

    elif nome == "jr":
        estado.pc = rs

    # As demais instruções são apenas decodificadas, sem alterar o estado.


# ---------------------------------------------------------
# Montagem do dicionário "regs" com apenas os registradores
# diferentes de zero, na ordem $0..$31, pc, hi, lo
# ---------------------------------------------------------

def montar_regs(estado):
    regs = {}

    for indice in range(32):
        valor = estado.registradores[indice]
        if valor != 0:
            regs[f"${indice}"] = para_signed32(valor)

    if estado.pc != 0:
        regs["pc"] = estado.pc

    if estado.hi != 0:
        regs["hi"] = para_signed32(estado.hi)

    if estado.lo != 0:
        regs["lo"] = para_signed32(estado.lo)

    return regs


# ---------------------------------------------------------
# Simulação completa
# ---------------------------------------------------------

def simular(dados):
    estado = EstadoCPU()

    # 1) Configuração inicial: registradores, memória e .data
    estado.aplicar_config(dados.get("config") or {})
    estado.carregar_words(dados.get("data") or {})

    # 2) Carga do código no segmento de texto, a partir do PC inicial
    # (0x00400000, como no MARS, a menos que config.regs defina outro)
    inicio = estado.pc
    instrucoes = dados.get("text") or []
    for i, instrucao_hex in enumerate(instrucoes):
        estado.memoria.escrever_word(inicio + 4 * i, int(instrucao_hex, 16))
    fim = inicio + 4 * len(instrucoes)

    # 3) Ciclo de busca, decodificação e execução. A próxima instrução
    # é a apontada pelo PC, então desvios e saltos alteram a ordem de
    # execução. A simulação termina quando o PC sai do programa (como
    # no MARS, ao "cair" após a última instrução).
    saida = []

    while inicio <= estado.pc < fim:
        palavra = estado.memoria.ler_word(estado.pc)
        instrucao_hex = f"0x{palavra:08x}"
        nome, assembly, campos = decodificar(instrucao_hex)

        estado.pc = (estado.pc + 4) & MASCARA_32_BITS
        executar(nome, campos, estado)

        saida.append({
            "hex": instrucao_hex,
            "text": assembly,
            "regs": montar_regs(estado),
            "mem": estado.memoria.montar_mem(),
            "stdout": "\n".join(estado.stdout)
        })

    return saida


# ---------------------------------------------------------
# Programa principal
# ---------------------------------------------------------

if __name__ == "__main__":
    with open("entrada.json", "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    saida = simular(dados)

    # Exibição da saída no terminal
    print(json.dumps(saida, indent=4, ensure_ascii=False))

    # Criação do arquivo de saída
    with open("saida.json", "w", encoding="utf-8") as arquivo:
        json.dump(saida, arquivo, indent=4, ensure_ascii=False)
