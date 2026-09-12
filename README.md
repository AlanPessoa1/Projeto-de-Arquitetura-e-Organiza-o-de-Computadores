# Projeto-de-Arquitetura-e-Organiza-o-de-Computadores
O programa começa lendo o arquivo JSON de entrada e acessando as instruções armazenadas no campo text. Cada instrução hexadecimal é convertida para uma representação binária de 32 bits. Em seguida, os bits são separados de acordo com os campos utilizados pelo formato MIPS, como opcode, rs, rt, rd, shamt, funct e imediato.

O opcode é utilizado para determinar o tipo da instrução. Quando o opcode é zero, a instrução pertence ao tipo R e o campo funct é usado para identificar a operação específica. Nos demais casos, o próprio opcode permite identificar instruções do tipo I ou J.

Como diferentes instruções possuem formatos diferentes de operandos, elas foram organizadas em grupos. Por exemplo, operações aritméticas do tipo R utilizam rd, rs e rt, enquanto instruções de memória utilizam o formato rt, offset(rs) e instruções de deslocamento utilizam também o campo shamt.

Para valores imediatos de 16 bits, também foi necessário considerar a representação com sinal em complemento de dois. Após a identificação da instrução, o programa monta sua representação em Assembly MIPS.

Por fim, todas as instruções do campo text são processadas na mesma ordem da entrada e adicionadas ao JSON de saída. Nesta primeira entrega, os campos regs, mem e stdout permanecem vazios, pois a execução efetiva das instruções será implementada nas etapas posteriores.
