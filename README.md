# Como executar

No terminal, na pasta do projeto, inicie o container Docker:

```bash
./start_container.sh
```

Dentro do container, execute um dos comandos:

- `./run_multi.sh` para reproduzir os experimentos do paper.
- `./run.sh` para executar uma única evolução, com os parâmetros desejados no script.

Os resultados são salvos em `outputs/`.
