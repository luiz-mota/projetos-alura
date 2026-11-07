import { Negociacaocontroller } from "./controllers/negociacao-controllers.js";

const controller = new Negociacaocontroller();
const form = document.querySelector('.form');

form.addEventListener('submit', (event: Event) => {
    event.preventDefault();
    controller.adiciona();
})

