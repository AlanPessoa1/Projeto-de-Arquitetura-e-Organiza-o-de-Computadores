# Projeto SNAKE — Assembly MIPS (MARS)

Jogo da cobrinha feito em Assembly MIPS para rodar no simulador MARS.
O código-fonte está em [snake.asm](snake.asm).

## Como executar

1. Abra o `snake.asm` no MARS.
2. **Tools > Bitmap Display**, configure assim e clique em **Connect to MIPS**:
   | Opção | Valor |
   |---|---|
   | Unit Width in Pixels | 16 |
   | Unit Height in Pixels | 16 |
   | Display Width in Pixels | 512 |
   | Display Height in Pixels | 512 |
   | Base address for display | 0x10010000 (static data) |
3. **Tools > Keyboard and Display MMIO Simulator** → clique em **Connect to MIPS**.
4. Assemble (F3) e Run (F5).
5. Clique na caixa de texto inferior do Keyboard MMIO e use **W A S D**.
   A cobra só começa a andar depois da primeira tecla.

## Regras

- Área de 512×512 pixels com células de 16×16 → grade de 32×32 células.
- A cobra começa com tamanho 1 na célula (0,0); a comida aparece numa célula livre aleatória.
- A cada 0,5 s a cobra anda uma célula, repetindo o último comando.
- Ao comer, a cobra cresce 1 célula e a comida é reposicionada.
- Pontuação: +1 a cada 0,5 s e +5 por comida.
- Game over ao bater na parede ou no próprio corpo; a pontuação é mostrada no console
  e numa janela, com opção de jogar novamente.

## Organização do código

| Rotina | Função |
|---|---|
| `main` / `novo_jogo` | Inicializa tela, cobra, pontuação e comida |
| `laco_jogo` | Laço principal: lê o teclado a cada 10 ms e move a cobra a cada 500 ms |
| `mover_cobra` | Calcula a nova cabeça, trata paredes, comida, crescimento e colisão |
| `ler_teclado` | Lê o Keyboard MMIO (0xFFFF0000/0xFFFF0004) e atualiza a direção |
| `gerar_comida` | Sorteia (syscall 42) uma célula livre para a comida |
| `pintar_celula` / `ler_celula` | Escreve/lê a cor de uma célula no Bitmap Display |
| `limpar_tela` | Pinta todo o display com a cor de fundo |

O corpo da cobra é guardado num buffer circular de 1024 posições (`corpo`), com
ponteiros para a cabeça (`$s7`) e a cauda (`pos_cauda`), então cada movimento custa O(1).
