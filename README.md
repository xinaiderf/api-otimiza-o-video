Aqui está o passo a passo completo para instalar o FFmpeg dentro de um contêiner:

Veja o id do conteiner: docker ps

Entre no contêiner (substitua nome_do_container pelo nome do seu contêiner):

docker exec -it nome_do_container bash

Atualize os pacotes no contêiner e instale as dependências necessáriase ffmpeg: apt-get update && apt-get install -y apt-transport-https software-properties-common && apt-get install -y ffmpeg

Verifique a instalação do FFmpeg: ffmpeg -version

Esses comandos vão garantir que o FFmpeg seja instalado corretamente dentro do seu contêiner.
