# Python-interfaceWSL

Interface gráfica em Python com execução de scripts automatizados (.exe) no Windows, projetada para facilitar o controle de serviços WSL e automações pessoais.

## Funcionalidades

- Interface visual com tema roxo/preto
- Execução de arquivos .exe com um clique
- Terminal embutido com logs em tempo real
- Botão para limpar logs
- Estrutura leve e compilável com PyInstaller

## Estrutura

\\\
Python-interfaceWSL/
├── main_interface.py
├── executers/
│   ├── ativarwsl.exe
│   ├── desativarwsl.exe
│   └── pythonnoupdate.exe
├── .gitignore
└── README.md
\\\

## Compilação (PyInstaller)

\\\
pyinstaller --onefile --windowed --add-data "executers;executers" main_interface.py
\\\

## Como usar

1. Clique no botão correspondente ao script que deseja executar
2. Veja os logs no terminal embutido
3. Use o botão 🧹 para limpar a saída

---
Criado por Akira (Felipe) | Projeto de automação pessoal de interface com controles de serviços.

=======


É um projeto antigo que salvou a minha vida por muito tempo por conta do meu OS, vou atualizar de acordo com as minhas necessidades.

