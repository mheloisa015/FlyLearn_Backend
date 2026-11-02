FLYLEARN
========

Sistema para criação, aplicação e correção de avaliações escolares.

O FlyLearn foi desenvolvido para auxiliar professores na organização de
turmas, alunos, matérias e questões, além de permitir a montagem de provas,
geração de versões, impressão de folhas de respostas e correção automática
por meio de leitura óptica (OMR) e QR Code.


1. SOBRE O PROJETO
------------------

O FlyLearn é uma aplicação web educacional voltada para professores.

O sistema reúne em um único ambiente as principais etapas do processo de
avaliação:

- Cadastro de professores;
- Cadastro e organização de matérias;
- Cadastro de turmas e alunos;
- Criação de um banco de questões;
- Montagem de provas;
- Geração de versões diferentes da mesma prova;
- Geração de QR Codes para identificar as versões;
- Impressão das provas e folhas de respostas;
- Aplicação das avaliações;
- Leitura automática das respostas;
- Correção e armazenamento dos resultados;
- Recuperação de senha por e-mail.

O objetivo é reduzir o trabalho manual do professor, organizar os dados
acadêmicos e facilitar a correção de avaliações impressas.


2. PRINCIPAIS FUNCIONALIDADES
-----------------------------

2.1 Cadastro e acesso do professor

O sistema possui funcionalidades para:

- Cadastrar um professor;
- Validar nome, e-mail e senha;
- Armazenar a senha usando hash;
- Realizar login;
- Alterar dados do perfil;
- Alterar a senha;
- Desativar ou controlar o estado da conta;
- Solicitar recuperação de senha;
- Validar o token de recuperação;
- Redefinir a senha.


2.2 Gerenciamento de matérias

O professor pode:

- Cadastrar matérias;
- Informar nome e descrição;
- Consultar matérias;
- Alterar dados;
- Excluir matérias quando não houver dependências que impeçam a operação.


2.3 Gerenciamento de turmas

O sistema permite:

- Criar turmas;
- Informar o ano escolar;
- Informar a disciplina;
- Associar a turma a um professor;
- Consultar turmas;
- Alterar turmas;
- Excluir turmas respeitando os vínculos existentes.


2.4 Gerenciamento de alunos

Para cada turma, o professor pode:

- Cadastrar alunos;
- Informar nome;
- Informar registro acadêmico (RA);
- Informar e-mail;
- Consultar alunos;
- Alterar dados;
- Excluir alunos quando não houver avaliações que impeçam a operação.


2.5 Banco de questões

O banco de questões permite:

- Cadastrar enunciados;
- Associar questões a matérias;
- Cadastrar alternativas;
- Definir a alternativa correta;
- Ativar ou desativar questões;
- Consultar questões por matéria;
- Evitar a exclusão de questões já utilizadas em provas.

Cada questão pode possuir várias alternativas, organizadas por ordem.


2.6 Criação de provas

O professor pode:

- Criar uma prova;
- Definir nome e descrição;
- Associar a prova a uma matéria;
- Selecionar questões do banco;
- Definir a quantidade de questões;
- Gerar versões da prova;
- Embaralhar questões;
- Associar o gabarito às versões;
- Consultar as versões geradas.

O sistema trabalha com modelos de folhas de 10 e 20 questões no fluxo OMR.


2.7 Geração de versões e QR Code

Cada versão de prova possui:

- Identificador próprio;
- UUID;
- Código de versão;
- Questões organizadas;
- Gabarito associado;
- QR Code para identificação.

O QR Code permite relacionar a folha respondida à versão correta da prova.


2.8 Aplicação e avaliação

O sistema permite registrar a aplicação de uma prova para:

- Um aluno específico;
- Uma turma;
- Uma data de aplicação;
- Um status de avaliação.

Os status utilizados incluem avaliações aplicadas e corrigidas.


2.9 Correção automática

A correção pode utilizar o serviço OMR para:

- Receber uma imagem da folha;
- Localizar a folha na imagem;
- Identificar os marcadores dos cantos;
- Detectar se as alternativas foram preenchidas;
- Identificar questões sem resposta;
- Identificar marcações duplas;
- Ler o QR Code;
- Relacionar a imagem à versão da prova;
- Calcular o resultado;
- Retornar linhas detalhadas da correção;
- Gerar uma imagem de diagnóstico opcional.

O serviço aceita folhas com 10 ou 20 questões.


2.10 Geração de folhas em PDF

O serviço OMR também gera folhas de respostas em PDF.

O PDF pode ser produzido a partir do UUID da versão da prova e da
quantidade de questões desejada.

As folhas são preparadas para impressão e possuem área de identificação
por QR Code.


3. TECNOLOGIAS UTILIZADAS
--------------------------

3.1 Backend principal

- Python;
- Django;
- Django ORM;
- SQLite para desenvolvimento;
- PostgreSQL por meio de psycopg em ambientes de produção;
- dj-database-url para configurar o banco por DATABASE_URL;
- Django password hashers para armazenamento seguro de senhas;
- Django signing para tokens assinados;
- Django cache para limitar solicitações de recuperação de senha;
- Django Email Backend para envio de e-mails.


3.2 Serviço de processamento OMR

- Python;
- Flask;
- Flask-CORS;
- OpenCV;
- NumPy;
- Pillow;
- QR Code;
- ReportLab;
- Gunicorn para execução em produção.

O OpenCV é usado para processamento de imagens, localização da folha,
binarização e identificação das marcações.

O NumPy é usado para manipulação dos dados matriciais das imagens.

O ReportLab é usado para geração de arquivos PDF.

Os recursos de QR Code são usados para gerar e ler identificadores das
versões de prova.


3.3 Frontend

- HTML5;
- CSS3;
- JavaScript;
- localStorage para dados locais e prototipação;
- Fetch API para comunicação com o backend;
- Netlify para hospedagem e proxy das chamadas da API;
- Fontes e bibliotecas externas carregadas por CDN.

O frontend é uma aplicação estática, sem um framework JavaScript obrigatório.


3.4 E-mail

O sistema possui suporte a:

- Backend de e-mail do console para desenvolvimento;
- SMTP para execução local;
- API HTTP do Brevo para produção.

O backend do Brevo utiliza a biblioteca padrão do Python e comunicação HTTPS.


4. ARQUITETURA DO PROJETO
--------------------------

O projeto é dividido em três partes principais:

    Frontend
        Interface usada pelo professor.

    Backend Django
        API, regras de negócio, modelos e recuperação de senha.

    Serviço OMR Flask
        Processamento de imagens, leitura de respostas e geração de folhas.

Fluxo simplificado:

    Professor
        |
        v
    Frontend HTML/CSS/JavaScript
        |
        v
    API Django
        |
        +--> Banco de dados
        |
        +--> Geração de provas e QR Codes
        |
        +--> Serviço OMR
                    |
                    +--> Leitura da imagem
                    +--> Identificação da folha
                    +--> Leitura das marcações
                    +--> Leitura do QR Code
                    +--> Resultado da correção


5. ESTRUTURA DE DIRETÓRIOS
---------------------------

    FlyLearn/
    |
    +-- Backend/
    |   +-- config/
    |   |   +-- settings.py
    |   |   +-- urls.py
    |   |   +-- asgi.py
    |   |   +-- wsgi.py
    |   |
    |   +-- core/
    |   |   +-- models.py
    |   |   +-- views.py
    |   |   +-- urls.py
    |   |   +-- middleware.py
    |   |   +-- email_backends.py
    |   |   +-- services/
    |   |       +-- correction.py
    |   |       +-- qr_generator.py
    |   |       +-- recuperacao_senha.py
    |   |
    |   +-- omr/
    |   |   +-- app_web.py
    |   |   +-- corretor.py
    |   |   +-- extrairGabarito.py
    |   |   +-- gerar_folha.py
    |   |   +-- qr_util.py
    |   |   +-- omr_config.py
    |   |
    |   +-- manage.py
    |   +-- requirements.txt
    |   +-- .gitignore
    |
    +-- Frontend/
    |   +-- index.html
    |   +-- login.html
    |   +-- cadastro.html
    |   +-- dashboard.html
    |   +-- materias.html
    |   +-- turmas.html
    |   +-- questoes.html
    |   +-- gerador.html
    |   +-- biblioteca.html
    |   +-- correcao.html
    |   +-- correcao-mobile.html
    |   +-- correcao.js
    |   +-- app.js
    |   +-- styles.css
    |   +-- netlify.toml
    |
    +-- core/
    +-- config/
    +-- omr/
    +-- manage.py
    +-- servidor.py
    +-- requirements.txt
    +-- .gitignore

Observação:

Existe uma implementação Django na raiz e outra dentro de Backend.
Antes do deploy, deve ser definido qual diretório representa a aplicação
oficial, para evitar divergência entre as duas cópias.


6. PRINCIPAIS ARQUIVOS DO BACKEND
----------------------------------

6.1 config/settings.py

Contém as configurações do Django, incluindo:

- Chave secreta;
- Modo de depuração;
- Hosts permitidos;
- Aplicações instaladas;
- Middleware;
- Banco de dados;
- Idioma e fuso horário;
- Configuração de e-mail;
- URL do frontend;
- Configuração de CORS;
- Tempo de validade do token de recuperação.


6.2 config/urls.py

É o arquivo principal de rotas do Django.

Ele registra:

- Painel administrativo;
- Rotas da aplicação core.


6.3 core/models.py

Representa as entidades utilizadas pelo sistema:

- Professor;
- Matéria;
- Turma;
- Aluno;
- Questão;
- Alternativa;
- Prova;
- Versão de prova;
- Questão da prova;
- Gabarito;
- Avaliação;
- Resposta.


6.4 core/views.py

Implementa as operações da API, incluindo cadastro, consulta, atualização,
exclusão, geração de versões, avaliação e recuperação de senha.


6.5 core/services/

Agrupa regras específicas:

- correction.py: rotinas relacionadas à correção;
- qr_generator.py: geração de QR Codes;
- recuperacao_senha.py: tokens e envio de recuperação de senha;
- outros serviços de apoio ao fluxo de provas.


6.6 core/middleware.py

Implementa o middleware de CORS utilizado pelo backend.


7. PRINCIPAIS ARQUIVOS DO FRONTEND
-----------------------------------

    index.html
        Página inicial.

    login.html
        Tela de acesso do professor.

    cadastro.html
        Cadastro de novos professores.

    dashboard.html
        Painel principal do sistema.

    materias.html
        Cadastro e consulta de matérias.

    turmas.html
        Cadastro de turmas e alunos.

    questoes.html
        Banco de questões e alternativas.

    gerador.html
        Seleção de questões e montagem de provas.

    biblioteca.html
        Consulta das provas e versões geradas.

    correcao.html
        Aplicação e correção das avaliações.

    correcao-mobile.html
        Fluxo de correção adaptado para dispositivos móveis.

    app.js
        Funções compartilhadas, navegação, dados locais e comunicação com API.

    correcao.js
        Lógica da tela de aplicação e correção.

    styles.css
        Estilos visuais compartilhados.

    netlify.toml
        Configuração do proxy entre o frontend e a API.


8. PRINCIPAIS ROTAS DA API
---------------------------

Professor:

    POST   /professores/
    GET    /professores/<id>/
    PUT    /professores/<id>/
    PUT    /professores/<id>/senha/
    POST   /login/

Matérias:

    GET/POST       /materias/
    GET/PUT/DELETE /materias/<id>/

Turmas:

    GET/POST       /turmas/
    GET/PUT/DELETE /turmas/<id>/

Alunos:

    GET/POST       /alunos/
    GET/PUT/DELETE /alunos/<id>/

Questões:

    GET/POST       /questoes/
    PATCH/DELETE   /questoes/<id>/

Provas:

    GET/POST       /provas/
    GET/DELETE     /provas/<id>/
    POST           /provas/<id>/versoes/
    POST           /provas/<id>/aplicar/

Versões:

    GET    /versoes/<id>/
    GET    /versoes/<id>/completa/
    GET    /versoes/<id>/qr.png
    GET    /versoes/uuid/<uuid>/

Avaliações:

    GET/DELETE /avaliacoes/<id>/
    POST       /avaliacoes/<id>/resultado/

Recuperação de senha:

    POST /recuperar-senha/
    POST /recuperar-senha/validar/
    POST /redefinir-senha/


9. ROTAS DO SERVIÇO OMR
------------------------

    GET /
        Verifica se o serviço está disponível.

    GET /health
        Endpoint de saúde.

    POST /corrigir
        Recebe a imagem de uma folha e retorna a leitura das respostas.

    GET /folha/<identificador>.pdf
        Gera uma folha de respostas em PDF.

Parâmetros e recursos utilizados:

- foto ou imagem: arquivo enviado para correção;
- gabarito: lista JSON com respostas A, B, C, D ou E;
- debug: habilita imagem de diagnóstico;
- n=10 ou n=20: define a quantidade de questões da folha.


10. PROCESSO DE CORREÇÃO OMR
-----------------------------

O processo de correção ocorre da seguinte forma:

1. O frontend ou cliente envia a imagem da folha;
2. O Flask recebe o arquivo;
3. O tamanho da imagem é validado;
4. A imagem é decodificada pelo OpenCV;
5. A folha é localizada pelos marcadores;
6. O modelo de 10 ou 20 questões é identificado;
7. A imagem é binarizada;
8. As bolhas são avaliadas;
9. Marcações duplas e respostas vazias são identificadas;
10. O QR Code é lido;
11. A versão da prova é identificada;
12. O resultado é devolvido em JSON;
13. O backend pode armazenar o resultado da avaliação.

Os arquivos campos.pkl e resp.pkl contêm dados auxiliares usados pelo
processamento OMR. Eles devem ser tratados como recursos da aplicação até
que exista um processo oficial para sua regeneração.


11. CONFIGURAÇÃO DE AMBIENTE
-----------------------------

Variáveis utilizadas pelo backend:

    SECRET_KEY
        Chave secreta do Django.

    DATABASE_URL
        URL do banco de dados.

    EMAIL_BACKEND
        Backend de e-mail escolhido.

    EMAIL_HOST
        Servidor SMTP.

    EMAIL_PORT
        Porta SMTP.

    EMAIL_HOST_USER
        Usuário SMTP.

    EMAIL_HOST_PASSWORD
        Senha SMTP.

    EMAIL_USE_TLS
        Ativa ou desativa TLS no SMTP.

    BREVO_API_KEY
        Chave da API HTTP do Brevo.

    DEFAULT_FROM_EMAIL
        Remetente dos e-mails.

    FRONTEND_URL
        URL utilizada nos links de recuperação de senha.

    RESET_SENHA_MAX_AGE
        Tempo de validade do token de recuperação.

    CORS_EXTRA_ORIGINS
        Origens adicionais permitidas pelo backend.

Variável utilizada pelo serviço OMR:

    CORS_ORIGINS
        Lista de origens permitidas pelo serviço Flask.

    PORT
        Porta em que o serviço Flask será executado.

As credenciais reais devem ser configuradas no ambiente de execução e não
devem ser gravadas no código ou no repositório.


12. EXECUÇÃO LOCAL
-------------------

12.1 Criar ambiente virtual

No Windows:

    python -m venv .venv
    .venv\Scripts\activate

No Linux ou macOS:

    python3 -m venv .venv
    source .venv/bin/activate


12.2 Instalar dependências

Na raiz:

    pip install -r requirements.txt

Ou, utilizando a cópia Backend:

    cd Backend
    pip install -r requirements.txt


12.3 Configurar variáveis de ambiente

Defina pelo menos:

    SECRET_KEY=uma-chave-segura

Para desenvolvimento, o sistema pode utilizar SQLite local.

Para envio de e-mails, configure as variáveis SMTP ou:

    BREVO_API_KEY=chave-da-api
    DEFAULT_FROM_EMAIL=remetente-verificado


12.4 Executar o Django

A partir da raiz:

    python manage.py runserver

Ou, dentro de Backend:

    cd Backend
    python manage.py runserver


12.5 Executar o serviço OMR

Dentro do diretório correspondente:

    cd Backend\omr
    python app_web.py

A porta pode ser definida pela variável PORT.

Em produção, usar um servidor WSGI, por exemplo:

    gunicorn app_web:app


12.6 Executar o frontend

O frontend é estático. Pode ser aberto por um servidor local simples.

Exemplo com Python:

    cd Frontend
    python -m http.server 5500

Depois, abrir:

    http://localhost:5500


13. BANCO DE DADOS
------------------

Durante o desenvolvimento, o projeto pode utilizar:

    Backend/db.sqlite3

Em produção, a configuração suporta banco PostgreSQL por meio de
DATABASE_URL e psycopg.

O arquivo SQLite local não deve ser utilizado como banco definitivo de
produção e deve permanecer fora do versionamento.


14. DEPLOY
----------

Frontend:

- Pode ser hospedado no Netlify;
- O arquivo netlify.toml configura o proxy /api/*;
- O frontend encaminha as chamadas para o backend hospedado.

Backend:

- Pode ser executado em uma plataforma como Render;
- O domínio configurado atualmente é flylearn.onrender.com;
- O processo deve usar servidor adequado para produção;
- As variáveis de ambiente devem ser configuradas na plataforma.

OMR:

- Deve ser executado como serviço Flask separado ou integrado conforme a
  estratégia de deploy;
- Deve utilizar Gunicorn em produção;
- CORS_ORIGINS deve ser restrito ao frontend e aos serviços necessários.


15. ARQUIVOS IGNORADOS PELO GIT
-------------------------------

Os arquivos .gitignore ignoram:

- Ambientes virtuais;
- Caches Python;
- Arquivos .env;
- Bancos SQLite;
- Uploads;
- Arquivos estáticos gerados;
- Caches de testes;
- Arquivos de cobertura;
- Builds;
- Logs;
- Dependências Node;
- Configurações locais de IDE;
- Arquivos temporários do sistema operacional.

Os arquivos .pkl utilizados pelo OMR não foram ignorados, pois podem ser
necessários para a execução da aplicação.


16. ESTADO ATUAL DO PROJETO
----------------------------

O FlyLearn possui uma estrutura funcional para:

- Gerenciar dados escolares;
- Montar provas;
- Gerar versões;
- Trabalhar com QR Codes;
- Processar folhas de respostas;
- Corrigir avaliações.

Antes da publicação definitiva, é importante concluir:

- Autenticação real dos usuários;
- Autorização por professor;
- Integração completa entre frontend e backend;
- Definição de uma única cópia oficial do backend;
- Configuração segura da SECRET_KEY;
- Revisão de CSRF e CORS;
- Validação do banco e das migrations;
- Confirmação dos templates do OMR;
- Testes automatizados dos principais fluxos.


17. RESUMO
----------

O FlyLearn é uma plataforma web de apoio à avaliação escolar.

Ele combina:

- Django para a API e regras de negócio;
- Flask para o processamento OMR;
- OpenCV e NumPy para leitura de imagens;
- QR Code para identificação das provas;
- ReportLab para geração de PDFs;
- HTML, CSS e JavaScript para a interface;
- SQLite no desenvolvimento;
- PostgreSQL como opção para produção;
- Netlify para hospedagem e proxy do frontend;
- Render como ambiente possível para o backend;
- Brevo ou SMTP para envio de e-mails.

O sistema foi projetado para acompanhar o professor desde a criação da
questão até a correção da avaliação, centralizando a organização da turma,
a montagem da prova e a leitura automática das respostas.

