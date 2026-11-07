# Memoteca — mural de pensamentos em Angular

Aplicação do curso de Angular da Alura: um mural onde o usuário cria, lista,
edita e exclui "pensamentos" (citação, autoria e modelo de card). Esta é a
versão final do projeto. `memoteca-v1` e `memoteca-v2` são etapas
intermediárias do mesmo curso.

## Funcionalidades
- Listagem dos pensamentos em cards
- Criação com escolha de modelo visual
- Edição e exclusão com tela de confirmação
- Persistência numa API REST fake (json-server)

## Arquitetura
```
src/app/componentes/
├── cabecalho/ · rodape/          layout
└── pensamentos/
    ├── listar-pensamento/        lista (GET)
    ├── criar-pensamento/         formulário (POST)
    ├── editar-pensamento/        formulário (GET por id + PUT)
    ├── excluir-pensamento/       confirmação (DELETE)
    ├── pensamento/               card
    └── pensamento.service.ts     acesso à API via HttpClient
backend/db.json                   dados do json-server
```

Conceitos praticados: componentes, data binding, rotas com parâmetros,
serviços com injeção de dependência, `HttpClient` e `Observable`.

## Como rodar
```bash
# API fake (porta 3000)
cd backend && npm install && npm start

# Front-end (porta 4200)
npm install && npm start
```

## Stack
Angular 14 · TypeScript · RxJS · json-server
