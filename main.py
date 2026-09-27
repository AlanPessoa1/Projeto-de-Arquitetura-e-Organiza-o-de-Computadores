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

    # Campos que a etapa de execução (Entrega 2) precisa para
    # calcular o efeito da instrução sobre os registradores.
    campos = {
        "rs": rs,
        "rt": rt,
        "rd": rd,
        "shamt": shamt,
        "imediato": imediato,
        "imediato_com_sinal": imediato_com_sinal
    }

    return nome, assembly, campos


# ---------------------------------------------------------
# Estado da CPU: banco de 32 registradores e os registradores
# especiais PC, HI e LO
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

    def ler(self, indice):
        return self.registradores[indice]

    def escrever(self, indice, valor):
        # $0 é fixo em zero: qualquer escrita nele é ignorada
        if indice != 0:
            self.registradores[indice] = valor & MASCARA_32_BITS

    def aplicar_config(self, config):
        # Depois da inicialização padrão do MARS, os valores do campo
        # "config" do arquivo de entrada são aplicados, podendo
        # sobrescrever $gp, $sp, $pc, hi e lo.
        for chave, valor in config.items():
            valor_uint32 = valor_para_uint32(valor)

            if chave == "pc":
                self.pc = valor_uint32
            elif chave == "hi":
                self.hi = valor_uint32
            elif chave == "lo":
                self.lo = valor_uint32
            else:
                indice = int(chave.lstrip("$"))
                self.escrever(indice, valor_uint32)


# ---------------------------------------------------------
# Execução das instruções lógicas e aritméticas (Entrega 2)
# ---------------------------------------------------------

def executar(nome, campos, estado):
    rs = estado.ler(campos["rs"])
    rt = estado.ler(campos["rt"])
    rd = campos["rd"]
    destino_i = campos["rt"]
    shamt = campos["shamt"]
    imediato = campos["imediato"]
    imediato_com_sinal = campos["imediato_com_sinal"]

    # add/addu e sub/subu resultam no mesmo padrão de bits: a única
    # diferença entre as versões com e sem sinal é o tratamento de
    # overflow, que não é exigido nesta etapa.
    if nome in ("add", "addu"):
        estado.escrever(rd, rs + rt)

    elif nome in ("sub", "subu"):
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

    elif nome in ("addi", "addiu"):
        estado.escrever(destino_i, rs + imediato_com_sinal)

    elif nome == "slti":
        estado.escrever(destino_i, 1 if para_signed32(rs) < imediato_com_sinal else 0)

    elif nome == "andi":
        estado.escrever(destino_i, rs & imediato)

    elif nome == "ori":
        estado.escrever(destino_i, rs | imediato)

    elif nome == "xori":
        estado.escrever(destino_i, rs ^ imediato)

    # As demais instruções (acesso à memória, desvios e saltos)
    # ainda não são executadas nesta etapa, apenas decodificadas.


# ---------------------------------------------------------
# Montagem do dicionário "regs" com apenas os registradores
# diferentes de zero, conforme exigido na Entrega 2
# ---------------------------------------------------------

def montar_regs(estado):
    regs = {}

    for indice in range(32):
        valor = estado.registradores[indice]
        if valor != 0:
            regs[f"${indice}"] = para_signed32(valor)

    if estado.hi != 0:
        regs["hi"] = para_signed32(estado.hi)

    if estado.lo != 0:
        regs["lo"] = para_signed32(estado.lo)

    if estado.pc != 0:
        regs["pc"] = estado.pc

    return regs


# ---------------------------------------------------------
# Leitura do arquivo de entrada
# ---------------------------------------------------------

with open("entrada.json", "r", encoding="utf-8") as arquivo:
    dados = json.load(arquivo)


# ---------------------------------------------------------
# Decodificação e execução de todas as instruções presentes
# em "text", na mesma ordem em que aparecem
# ---------------------------------------------------------

saida = []
estado = EstadoCPU()
estado.aplicar_config(dados.get("config", {}))

for instrucao_hex in dados["text"]:
    nome, assembly, campos = decodificar(instrucao_hex)

    executar(nome, campos, estado)
    estado.pc += 4

    # O campo mem e o stdout ainda ficam vazios: instruções de
    # memória e syscalls serão implementadas em etapas posteriores.
    resultado = {
        "hex": instrucao_hex,
        "text": assembly,
        "regs": montar_regs(estado),
        "mem": {},
        "stdout": ""
    }

    saida.append(resultado)


# ---------------------------------------------------------
# Exibição da saída no terminal
# ---------------------------------------------------------

print(json.dumps(saida, indent=4, ensure_ascii=False))


# ---------------------------------------------------------
# Criação do arquivo saida.json
# ---------------------------------------------------------

with open("saida.json", "w", encoding="utf-8") as arquivo:
    json.dump(saida, arquivo, indent=4, ensure_ascii=False)
