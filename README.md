# Sistema de Votação Eletrônica

Sistema de votação eletrônica desenvolvido em Python, com painel administrativo,
urnas conectadas em rede e apuração em tempo real. Projeto da disciplina de POO
(ADS).

## Funcionalidades

- **Painel do administrador:** login com senha criptografada (hash + salt),
  cadastro de eleitores (foto, CPF validado e biometria simulada), cadastro de
  candidatos com foto, número e partido, e criação e encerramento de eleições.
- **Urna eletrônica:** teclado com CONFIRMA, CORRIGE, BRANCO e NULO, foto do
  candidato, identificação do eleitor pelo título e confirmação biométrica.
- **Votação em rede:** várias urnas votam ao mesmo tempo em um servidor TCP
  central, sem precisar de acesso de administrador.
- **Apuração:** resultados por cargo atualizados automaticamente, com votos
  válidos, brancos e nulos.
- **Relatórios:** exportação dos resultados em PDF e Excel.
- **Auditoria:** registro de todas as ações (logins, votos, criação de
  eleições), atualizado ao vivo.

## Tecnologias

Python 3.13 · CustomTkinter · SQLite · Sockets TCP · Pillow · OpenPyXL · ReportLab

## Arquitetura

Padrão MVC em camadas: `models` (entidades e repositório), `controllers`
(regras de negócio), `views` (telas), `database` (conexão e schema), `rede`
(cliente da urna) e `utils` (validadores, imagens e exportação).

## Como executar

Instale as dependências:

    pip install -r requirements.txt

**Administrador** (na máquina do servidor):

    python servidor.py     # servidor de votação (porta 5050)
    python main.py         # painel administrativo

**Urna em outro computador:**

    python main_urna.py IP_DO_SERVIDOR

O servidor e o painel administrativo devem rodar na mesma máquina e na mesma
pasta, pois usam o mesmo arquivo de banco de dados.

## Acesso de teste

Usuários criados automaticamente na primeira execução: `admin` / `admin123` e
`maria` / `maria123`. Troque as senhas antes de qualquer uso real.
