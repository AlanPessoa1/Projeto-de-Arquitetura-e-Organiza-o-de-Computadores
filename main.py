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
            assembly = f"jr ${rs}"

        elif funct == 12:
            assembly = "syscall"

        else:
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
        assembly = f"bltz ${rs}, {imediato_com_sinal}"

    # -----------------------------------------------------
    # Decodificação das instruções do tipo J
    # -----------------------------------------------------

    elif opcode == 2:
        alvo = int(instrucao_bin[6:32], 2)
        assembly = f"j {alvo}"

    elif opcode == 3:
        alvo = int(instrucao_bin[6:32], 2)
        assembly = f"jal {alvo}"

    else:
        assembly = "instrução desconhecida"

    return assembly


# ---------------------------------------------------------
# Leitura do arquivo de entrada
# ---------------------------------------------------------

with open("entrada.json", "r", encoding="utf-8") as arquivo:
    dados = json.load(arquivo)


# ---------------------------------------------------------
# Decodificação de todas as instruções presentes em "text"
# ---------------------------------------------------------

saida = []

for instrucao_hex in dados["text"]:
    assembly = decodificar(instrucao_hex)

    # Nesta primeira etapa, regs, mem e stdout permanecem
    # vazios, pois ainda não ocorre execução das instruções.
    resultado = {
        "hex": instrucao_hex,
        "text": assembly,
        "regs": {},
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
