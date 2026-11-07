import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-titulo',
  template: `
      <h2>Componente desafio</h2>
      <p>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Commodi recusandae, est ipsam odit porro tenetur doloribus corrupti quia ipsum, nulla enim amet. Impedit ratione eos error inventore expedita blanditiis cumque.</p>

  `,
  styles: ['h2, p{color: blue}']
})
export class TituloComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
  }

}
