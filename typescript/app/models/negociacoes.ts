import { Negociacao } from "./negociacao"

export class Negociacoes {
    // private negociacoes: Array<Negociacao> = [];
    private negociacoes: Negociacao[] = [];

    adiciona(negociacao: Negociacao) {
        this.negociacoes.push(negociacao);
    }

    lista(): readonly Negociacao[] {
        return this.negociacoes;
    }
}