###############################################################################
#  PROJETO SNAKE - Jogo da cobrinha em Assembly MIPS (MARS)
#
#  CONFIGURACAO DO MARS (obrigatoria antes de executar):
#
#  Tools > Bitmap Display
#     Unit Width in Pixels .......... 16
#     Unit Height in Pixels ......... 16
#     Display Width in Pixels ....... 512
#     Display Height in Pixels ...... 512
#     Base address for display ...... 0x10010000 (static data)
#     -> clicar em "Connect to MIPS"
#
#  Tools > Keyboard and Display MMIO Simulator
#     -> clicar em "Connect to MIPS"
#     -> digitar as teclas W A S D na caixa de texto inferior (KEYBOARD)
#
#  Depois: Assemble (F3) e Run (F5).
#
#  REGRAS:
#   - A regiao do jogo e uma grade de 32 x 32 celulas (512/16 = 32).
#   - A cobra comeca com tamanho 1 na celula (0,0) (canto superior esquerdo).
#   - A comida aparece numa celula (I,J) aleatoria e livre.
#   - A cada 0,5 s a cobra anda uma celula na ultima direcao escolhida.
#   - Pontuacao: +1 a cada 0,5 s de movimento e +5 a cada comida coletada.
#   - Fim de jogo: cabeca bate na parede ou em qualquer parte do corpo.
#
#  O jogo fica parado ate o jogador apertar a primeira tecla de direcao.
###############################################################################

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
.eqv GRADE        32            # celulas por linha/coluna (512 / 16)
.eqv TOTAL_CEL    1024          # 32 * 32 celulas
.eqv MASCARA_BUF  1023          # mascara do buffer circular (TOTAL_CEL - 1)
.eqv TICK_MS      500           # intervalo entre movimentos (0,5 s)
.eqv POLL_MS      10            # intervalo de leitura do teclado

.eqv KBD_CTRL     0xffff0000    # registrador de controle do teclado (bit 0 = tecla pronta)
.eqv KBD_DADO     0xffff0004    # registrador com o codigo ASCII da tecla

.eqv COR_FUNDO    0x00101010    # fundo (quase preto)
.eqv COR_CORPO    0x000066CC    # corpo da cobra (azul)
.eqv COR_CABECA   0x0000DDFF    # cabeca da cobra (azul claro)
.eqv COR_COMIDA   0x0066BB33    # comida (verde)

.eqv PONTOS_TICK   1            # pontos a cada 0,5 s
.eqv PONTOS_COMIDA 5            # pontos por comida

###############################################################################
#  SEGMENTO DE DADOS
#  ATENCAO: "tela" deve ser o PRIMEIRO item do .data, pois ela fica
#  exatamente no endereco 0x10010000, que e o endereco base do Bitmap Display.
#  Cada celula 16x16 do display corresponde a 1 palavra (4 bytes) da tela.
###############################################################################
.data
tela:        .space 4096        # 1024 celulas * 4 bytes (memoria de video)

# Buffer circular com o indice (0..1023) de cada celula do corpo da cobra.
# corpo[pos_cabeca] = cabeca ; corpo[pos_cauda] = cauda
corpo:       .space 4096

pos_cauda:   .word 0            # posicao da cauda dentro do buffer circular
ult_dx:      .word 0            # ultima direcao efetivamente usada (eixo x)
ult_dy:      .word 0            # ultima direcao efetivamente usada (eixo y)
t_inicio:    .word 0            # instante (ms) de inicio do tick atual

msg_inicio:  .asciiz "=== SNAKE ===\nUse W (cima), A (esquerda), S (baixo), D (direita)\nno Keyboard and Display MMIO Simulator.\nAperte uma direcao para comecar!\n\n"
msg_comeu:   .asciiz "Comeu! Pontuacao: "
msg_fim:     .asciiz "\n*** GAME OVER ***\nPontuacao final: "
msg_venceu:  .asciiz "\n*** VOCE VENCEU! A cobra ocupou toda a tela! ***\nPontuacao final: "
msg_dialogo: .asciiz "GAME OVER!\nSua pontuacao foi: "
msg_denovo:  .asciiz "Deseja jogar novamente?"
nova_linha:  .asciiz "\n"

###############################################################################
#  USO DOS REGISTRADORES SALVOS (validos durante todo o jogo)
#   $s0 = coluna (x) da cabeca          $s1 = linha (y) da cabeca
#   $s2 = direcao atual dx (-1, 0, 1)   $s3 = direcao atual dy (-1, 0, 1)
#   $s4 = tamanho da cobra              $s5 = pontuacao
#   $s6 = indice da celula da comida    $s7 = posicao da cabeca no buffer
###############################################################################
.text
.globl main

main:
    # Mostra as instrucoes no console (Run I/O)
    li   $v0, 4
    la   $a0, msg_inicio
    syscall

# ---------------------------------------------------------------------------
# Inicializacao (tambem usada quando o jogador decide jogar novamente)
# ---------------------------------------------------------------------------
novo_jogo:
    jal  limpar_tela            # pinta todas as celulas com a cor de fundo

    li   $s0, 0                 # cabeca na coluna 0
    li   $s1, 0                 # cabeca na linha 0
    li   $s2, 0                 # sem direcao: cobra parada ate a 1a tecla
    li   $s3, 0
    li   $s4, 1                 # tamanho inicial = 1 (so a cabeca)
    li   $s5, 0                 # pontuacao zerada
    li   $s7, 0                 # cabeca na posicao 0 do buffer

    sw   $zero, pos_cauda       # cauda tambem na posicao 0 (tamanho 1)
    sw   $zero, ult_dx
    sw   $zero, ult_dy

    la   $t0, corpo
    sw   $zero, 0($t0)          # corpo[0] = celula 0 = (0,0)

    li   $a0, 0                 # desenha a cabeca na celula (0,0)
    li   $a1, COR_CABECA
    jal  pintar_celula

    jal  gerar_comida           # coloca a primeira comida

    # Descarta alguma tecla que tenha ficado no buffer do teclado
    li   $t0, KBD_CTRL
    lw   $t1, 0($t0)
    andi $t1, $t1, 1
    beqz $t1, laco_jogo
    li   $t0, KBD_DADO
    lw   $t1, 0($t0)            # leitura apenas para limpar o bit "pronto"

# ---------------------------------------------------------------------------
# Laco principal: cada iteracao corresponde a um "tick" de 0,5 s.
# Durante o tick o teclado e lido varias vezes (a cada 10 ms), assim
# o jogo responde rapidamente ao jogador sem alterar a velocidade.
# ---------------------------------------------------------------------------
laco_jogo:
    li   $v0, 30                # syscall 30: tempo do sistema em ms ($a0 = 32 bits baixos)
    syscall
    sw   $a0, t_inicio

espera_tick:
    jal  ler_teclado            # atualiza $s2/$s3 se alguma tecla foi pressionada

    li   $v0, 30
    syscall
    lw   $t0, t_inicio
    subu $t0, $a0, $t0          # tempo decorrido desde o inicio do tick
    li   $t1, TICK_MS
    bgeu $t0, $t1, fim_tick     # ja passou 0,5 s? entao executa o movimento

    li   $v0, 32                # syscall 32: dorme POLL_MS milissegundos
    li   $a0, POLL_MS
    syscall
    j    espera_tick

fim_tick:
    # Se ainda nao ha direcao (jogo nao comecou), nao move nem pontua
    or   $t0, $s2, $s3
    beqz $t0, laco_jogo

    jal  mover_cobra            # $v0 = 0 continua | 1 game over | 2 vitoria
    bnez $v0, fim_de_jogo

    addi $s5, $s5, PONTOS_TICK  # +1 ponto a cada 0,5 s
    j    laco_jogo

# ---------------------------------------------------------------------------
# Fim de jogo: mostra a pontuacao no console e numa janela de dialogo,
# e pergunta se o jogador quer jogar novamente.
# ---------------------------------------------------------------------------
fim_de_jogo:
    li   $t0, 2
    la   $a0, msg_fim
    bne  $v0, $t0, imprime_fim
    la   $a0, msg_venceu
imprime_fim:
    li   $v0, 4                 # imprime mensagem de fim
    syscall
    li   $v0, 1                 # imprime a pontuacao
    move $a0, $s5
    syscall
    li   $v0, 4
    la   $a0, nova_linha
    syscall

    li   $v0, 56                # syscall 56: MessageDialogInt (janela com a pontuacao)
    la   $a0, msg_dialogo
    move $a1, $s5
    syscall

    li   $v0, 50                # syscall 50: ConfirmDialog (0 = Sim, 1 = Nao, 2 = Cancelar)
    la   $a0, msg_denovo
    syscall
    beqz $a0, novo_jogo         # "Sim" -> recomeca

    li   $v0, 10                # encerra o programa
    syscall

###############################################################################
#  mover_cobra
#  Move a cobra uma celula na direcao ($s2, $s3).
#  Retorno: $v0 = 0 (ok), 1 (colisao -> game over), 2 (vitoria: tela cheia)
###############################################################################
mover_cobra:
    addi $sp, $sp, -12
    sw   $ra, 0($sp)
    sw   $s0, 4($sp)            # guardados apenas para manter a convencao
    sw   $s1, 8($sp)

    # Guarda a direcao usada neste movimento (para impedir meia-volta)
    sw   $s2, ult_dx
    sw   $s3, ult_dy

    # Nova posicao da cabeca: (nx, ny) = (x + dx, y + dy)
    add  $t0, $s0, $s2          # $t0 = nx
    add  $t1, $s1, $s3          # $t1 = ny

    # --- Colisao com as paredes: nx e ny devem estar em [0, 31] ---
    # (comparacao sem sinal: -1 vira 0xFFFFFFFF, que e >= 32)
    li   $t2, GRADE
    bgeu $t0, $t2, mover_colidiu
    bgeu $t1, $t2, mover_colidiu

    # Indice da nova celula: ny * 32 + nx
    sll  $t3, $t1, 5
    add  $t3, $t3, $t0          # $t3 = indice da nova cabeca

    # Salva nx, ny e indice na pilha temporariamente (as funcoes chamadas usam $t)
    addi $sp, $sp, -12
    sw   $t0, 0($sp)
    sw   $t1, 4($sp)
    sw   $t3, 8($sp)

    # 1) A cabeca antiga passa a ser corpo
    sll  $a0, $s1, 5
    add  $a0, $a0, $s0
    li   $a1, COR_CORPO
    jal  pintar_celula

    # 2) Se a nova celula NAO e a comida, a cauda anda (apaga a ultima celula)
    lw   $t3, 8($sp)
    beq  $t3, $s6, mover_verifica

    lw   $t4, pos_cauda
    la   $t5, corpo
    sll  $t6, $t4, 2
    add  $t6, $t6, $t5
    lw   $a0, 0($t6)            # indice da celula da cauda
    li   $a1, COR_FUNDO
    jal  pintar_celula          # apaga a cauda da tela

    lw   $t4, pos_cauda         # avanca a cauda no buffer circular
    addi $t4, $t4, 1
    andi $t4, $t4, MASCARA_BUF
    sw   $t4, pos_cauda
    addi $s4, $s4, -1           # tamanho diminui 1 (sera somado 1 abaixo)

mover_verifica:
    # 3) Colisao com o proprio corpo: a nova celula ja esta pintada de cobra?
    #    (a cauda ja foi apagada, entao andar para onde a cauda estava e permitido)
    lw   $a0, 8($sp)
    jal  ler_celula
    li   $t0, COR_CORPO
    beq  $v0, $t0, mover_colidiu_pilha
    li   $t0, COR_CABECA
    beq  $v0, $t0, mover_colidiu_pilha

    # 4) Insere a nova cabeca no buffer circular
    addi $s7, $s7, 1
    andi $s7, $s7, MASCARA_BUF
    la   $t5, corpo
    sll  $t6, $s7, 2
    add  $t6, $t6, $t5
    lw   $t3, 8($sp)
    sw   $t3, 0($t6)            # corpo[pos_cabeca] = indice da nova cabeca
    addi $s4, $s4, 1            # tamanho + 1

    # 5) Desenha a nova cabeca
    move $a0, $t3
    li   $a1, COR_CABECA
    jal  pintar_celula

    # Recupera nx, ny (novas coordenadas da cabeca)
    lw   $t0, 0($sp)
    lw   $t1, 4($sp)
    lw   $t3, 8($sp)
    addi $sp, $sp, 12

    # 6) Comeu a comida?
    bne  $t3, $s6, mover_ok_coord

    addi $s5, $s5, PONTOS_COMIDA    # +5 pontos

    li   $v0, 4                 # informa no console
    la   $a0, msg_comeu
    syscall
    li   $v0, 1
    move $a0, $s5
    syscall
    li   $v0, 4
    la   $a0, nova_linha
    syscall

    li   $t2, TOTAL_CEL         # cobra ocupou a tela inteira -> vitoria
    beq  $s4, $t2, mover_venceu

    # Atualiza a cabeca antes de gerar comida (o retorno restaura $s0/$s1 da pilha,
    # entao gravamos as novas coordenadas diretamente na pilha)
    sw   $t0, 4($sp)
    sw   $t1, 8($sp)
    jal  gerar_comida
    j    mover_ok

mover_ok_coord:
    sw   $t0, 4($sp)            # novas coordenadas da cabeca serao restauradas
    sw   $t1, 8($sp)            # em $s0 e $s1 no epilogo
mover_ok:
    li   $v0, 0
    j    mover_sai

mover_venceu:
    li   $v0, 2
    j    mover_sai

mover_colidiu_pilha:
    addi $sp, $sp, 12           # descarta nx, ny e indice salvos
mover_colidiu:
    li   $v0, 1

mover_sai:
    lw   $ra, 0($sp)
    lw   $s0, 4($sp)            # $s0 = coluna da cabeca (nova, se moveu)
    lw   $s1, 8($sp)            # $s1 = linha da cabeca (nova, se moveu)
    addi $sp, $sp, 12
    jr   $ra

###############################################################################
#  ler_teclado
#  Le uma tecla do Keyboard MMIO (se houver) e atualiza a direcao ($s2, $s3).
#  Teclas validas: W/w (cima), A/a (esquerda), S/s (baixo), D/d (direita).
#  A cobra nao pode dar meia-volta (inverter a direcao) se tiver tamanho > 1.
###############################################################################
ler_teclado:
    li   $t0, KBD_CTRL
    lw   $t1, 0($t0)
    andi $t1, $t1, 1            # bit 0 = 1 -> existe tecla disponivel
    beqz $t1, teclado_sai

    li   $t0, KBD_DADO
    lw   $t1, 0($t0)            # codigo ASCII da tecla (leitura limpa o bit "pronto")

    # Converte minuscula para maiuscula ('a'..'z' -> 'A'..'Z')
    li   $t2, 'a'
    blt  $t1, $t2, teclado_decodifica
    li   $t2, 'z'
    bgt  $t1, $t2, teclado_decodifica
    addi $t1, $t1, -32

teclado_decodifica:
    li   $t2, 'W'
    beq  $t1, $t2, tecla_cima
    li   $t2, 'S'
    beq  $t1, $t2, tecla_baixo
    li   $t2, 'A'
    beq  $t1, $t2, tecla_esquerda
    li   $t2, 'D'
    beq  $t1, $t2, tecla_direita
    jr   $ra                    # tecla invalida: ignora

tecla_cima:
    li   $t3, 0
    li   $t4, -1
    j    teclado_aplica
tecla_baixo:
    li   $t3, 0
    li   $t4, 1
    j    teclado_aplica
tecla_esquerda:
    li   $t3, -1
    li   $t4, 0
    j    teclado_aplica
tecla_direita:
    li   $t3, 1
    li   $t4, 0

teclado_aplica:
    # Bloqueia meia-volta: se tamanho > 1 e (dx,dy) == -(ultima direcao), ignora
    li   $t2, 1
    ble  $s4, $t2, teclado_aceita
    lw   $t5, ult_dx
    lw   $t6, ult_dy
    add  $t5, $t5, $t3          # soma = 0 nos dois eixos -> direcao oposta
    add  $t6, $t6, $t4
    or   $t5, $t5, $t6
    beqz $t5, teclado_sai

teclado_aceita:
    move $s2, $t3
    move $s3, $t4

teclado_sai:
    jr   $ra

###############################################################################
#  gerar_comida
#  Sorteia uma celula livre (cor de fundo) e desenha a comida nela.
#  Resultado em $s6 (indice da celula da comida).
###############################################################################
gerar_comida:
    addi $sp, $sp, -4
    sw   $ra, 0($sp)

comida_sorteia:
    li   $v0, 42                # syscall 42: inteiro aleatorio em [0, $a1)
    li   $a0, 0                 # id do gerador
    li   $a1, TOTAL_CEL
    syscall                     # $a0 = indice sorteado (0..1023)

    move $t7, $a0
    jal  ler_celula             # celula esta livre?
    li   $t0, COR_FUNDO
    bne  $v0, $t0, comida_sorteia   # ocupada pela cobra: sorteia de novo

    move $s6, $t7               # guarda a posicao da comida
    move $a0, $t7
    li   $a1, COR_COMIDA
    jal  pintar_celula

    lw   $ra, 0($sp)
    addi $sp, $sp, 4
    jr   $ra

###############################################################################
#  pintar_celula
#  $a0 = indice da celula (0..1023)   $a1 = cor (0x00RRGGBB)
#  Endereco = tela + indice * 4
###############################################################################
pintar_celula:
    la   $t8, tela
    sll  $t9, $a0, 2
    add  $t9, $t9, $t8
    sw   $a1, 0($t9)
    jr   $ra

###############################################################################
#  ler_celula
#  $a0 = indice da celula (0..1023)   ->   $v0 = cor atual da celula
###############################################################################
ler_celula:
    la   $t8, tela
    sll  $t9, $a0, 2
    add  $t9, $t9, $t8
    lw   $v0, 0($t9)
    jr   $ra

###############################################################################
#  limpar_tela
#  Pinta todas as 1024 celulas com a cor de fundo.
###############################################################################
limpar_tela:
    la   $t0, tela
    li   $t1, TOTAL_CEL
    li   $t2, COR_FUNDO
limpar_laco:
    sw   $t2, 0($t0)
    addi $t0, $t0, 4
    addi $t1, $t1, -1
    bnez $t1, limpar_laco
    jr   $ra
