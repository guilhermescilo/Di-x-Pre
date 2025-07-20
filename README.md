Estrutura dos Arquivos e Raciocínio
O projeto foi estruturado em três scripts principais para modularizar as funcionalidades e facilitar a manutenção:

1. load_and_filter.py
O que faz?
Este script é responsável por carregar os dados da planilha case.xlsx.
Ele utiliza a biblioteca pandas para ler o arquivo Excel e convertê-lo em um DataFrame, que é uma estrutura de dados tabular fácil de manipular.
A principal função deste script é filtrar o DataFrame para manter apenas as linhas que correspondem ao produto "Futuro de DI", conforme solicitado no desafio.
Raciocínio:
A ideia de separar essa funcionalidade em um script próprio foi para isolar a lógica de acesso e preparação dos dados. Se a fonte de dados mudasse no futuro (por exemplo, de um Excel para um banco de dados), apenas este arquivo precisaria ser modificado, sem impactar o resto do código.
Como usar:
Este script não é destinado a ser executado diretamente, mas sim a ser importado por outros scripts. A sua função load_and_filter_data() é chamada pelo main.py para obter os dados iniciais.
2. b3_scraper.py
O que faz?
Este é o coração do web scraping. Ele acessa a página de taxas referenciais da B3 para uma data específica e extrai as taxas de DI.
Ele utiliza a biblioteca undetected-chromedriver, uma versão especializada do selenium, para automatizar um navegador Chrome em modo "headless" (sem interface gráfica).
A biblioteca BeautifulSoup é usada para analisar o HTML da página e extrair os dados da tabela de taxas.
Raciocínio:
A abordagem de web scraping foi necessária porque não havia uma API pública disponível para obter os dados.
Inicialmente, tentei usar a biblioteca requests, mas o site da B3 apresentou bloqueios. O uso do undetected-chromedriver foi a solução para simular um acesso de navegador mais "humano", contornando esses bloqueios e problemas de compatibilidade de versão do driver.
Assim como o load_and_filter.py, este script foi projetado para ser modular.
Como usar:
A sua função get_b3_rates_uc() é chamada pelo main.py para cada data de referência necessária, retornando um DataFrame com as taxas da B3.
3. main.py
O que faz?
Este é o script principal que orquestra todo o fluxo de trabalho.
Ele começa chamando load_and_filter_data() para obter os dados filtrados.
Em seguida, ele itera sobre as datas necessárias e chama get_b3_rates_uc() para coletar todas as taxas da B3.
A lógica principal de validação reside aqui. Ele compara os preços da planilha com os preços da B3, usando a coluna n_dias_corridos para uma correspondência precisa.
Ele implementa a fórmula de cálculo de MtM fornecida para recalcular o resultado_correto para cada operação.
Ele adiciona colunas de validação (preco_b3_referencia, preco_b3_anterior, validacao_b3, status_validacao) para enriquecer a análise.
Por fim, ele gera o relatório final validacao_mtm_final.xlsx, contendo todas as operações de Futuro de DI e os resultados da validação.
Raciocínio:
O main.py serve como o ponto de entrada e o "cérebro" da aplicação. Ele conecta os módulos de dados e de scraping para realizar a tarefa final.
A lógica de cálculo e de comparação foi centralizada aqui para manter a clareza do processo.
Como usar:
Este é o único script que você precisa executar para rodar o projeto. Basta executar o comando python main.py no seu terminal.
Como Executar o Projeto
Pré-requisitos: Certifique-se de ter o Python 3 instalado.
Instalar as dependências: Execute o seguinte comando no seu terminal para instalar todas as bibliotecas necessárias:
pip install pandas openpyxl undetected-chromedriver beautifulsoup4 numpy
Executar a validação: Coloque o arquivo case.xlsx no mesmo diretório dos scripts e execute o main.py:
python main.py
Verificar o resultado: Após a execução, um novo arquivo chamado validacao_mtm_final.xlsx será criado no mesmo diretório. Este arquivo contém a análise completa.
