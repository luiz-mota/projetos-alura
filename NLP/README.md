# Análise de sentimento em avaliações de produtos (NLP)

Notebooks do curso de NLP da Alura. Classificação de avaliações de clientes
em positivas ou negativas, do texto bruto até um modelo salvo que classifica
avaliações novas.

Cada notebook é cumulativo: `Aula_5.ipynb` contém o fluxo completo.

| Aula | Conteúdo |
|------|----------|
| 1 | Exploração dos dados, vetorização (Bag of Words) e primeiro classificador |
| 2 | Nuvem de palavras, frequência por sentimento e tokenização |
| 3 | Limpeza: stopwords, pontuação, acentuação e caixa |
| 4 | Stemming, TF-IDF, n-gramas e efeito do número de features |
| 5 | Salvar e carregar o modelo, função de pré-processamento e classificação de novas avaliações |

## Técnicas
Tokenização · remoção de stopwords · normalização · stemming · Bag of Words ·
TF-IDF · n-gramas · Regressão Logística · persistência com joblib

## Stack
Python · pandas · NLTK · scikit-learn · WordCloud · matplotlib/seaborn

## Como rodar
Abra os notebooks no Jupyter ou no Google Colab e execute as células. A base é
baixada automaticamente do repositório público do curso. As saídas foram
removidas porque exibiam trechos de avaliações com dados de contato de clientes.
