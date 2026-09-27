# Projeto-de-Arquitetura-e-Organiza-o-de-Computadores
O programa começa lendo o arquivo JSON de entrada e acessando as instruções armazenadas no campo text. Cada instrução hexadecimal é convertida para uma representação binária de 32 bits. Em seguida, os bits são separados de acordo com os campos utilizados pelo formato MIPS, como opcode, rs, rt, rd, shamt, funct e imediato.

O opcode é utilizado para determinar o tipo da instrução. Quando o opcode é zero, a instrução pertence ao tipo R e o campo funct é usado para identificar a operação específica. Nos demais casos, o próprio opcode permite identificar instruções do tipo I ou J.

Como diferentes instruções possuem formatos diferentes de operandos, elas foram organizadas em grupos. Por exemplo, operações aritméticas do tipo R utilizam rd, rs e rt, enquanto instruções de memória utilizam o formato rt, offset(rs) e instruções de deslocamento utilizam também o campo shamt.

Para valores imediatos de 16 bits, também foi necessário considerar a representação com sinal em complemento de dois. Após a identificação da instrução, o programa monta sua representação em Assembly MIPS.

Na segunda entrega, o programa passou a executar as instruções lógicas e aritméticas dos tipos R e I (add, sub, slt, and, or, xor, nor, mfhi, mflo, addu, subu, mult, multu, div, divu, sll, srl, sra, sllv, srlv, srav, addi, slti, andi, ori, xori e addiu). Para isso foi criado um banco de 32 registradores de 32 bits, além dos registradores especiais PC, HI e LO. O resultado de mult e multu, que é um valor de 64 bits, é dividido entre HI (32 bits mais significativos) e LO (32 bits menos significativos); o mesmo par é usado por div e divu para armazenar quociente (LO) e resto (HI).

Os registradores são inicializados com os mesmos valores padrão do MARS: todos zerados, exceto $gp (0x10008000), $sp (0x7fffeffc) e o PC (0x00400000). Em seguida, os valores definidos no campo config do arquivo de entrada são aplicados, podendo sobrescrever qualquer registrador, incluindo $gp, $sp, PC, HI e LO. O registrador $0 é fixo em zero e nunca é alterado.

As instruções são processadas na mesma ordem em que aparecem no campo text, e cada execução pode alterar o estado usado pelas instruções seguintes. Após cada instrução, o JSON de saída traz no campo regs apenas os registradores com valor diferente de zero, já refletindo o estado atualizado. As instruções de acesso à memória, desvio e salto ainda são apenas decodificadas, não executadas; por isso os campos mem e stdout permanecem vazios, ficando para as etapas posteriores.
