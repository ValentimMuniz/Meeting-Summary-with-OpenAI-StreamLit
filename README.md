# Meeting Summary with OpenAI
Desenvolvido por: Valentim Uliana

Essa aplicação tem como intuito a facilitação no dia-dia de quem faz muitas reuniões, onde a partir de uma gravação de reunião, é possível gerar um resumo usando o ChatGPT e trazer tudo que foi acordado numa reunião, desde tópicos abordados até  próximos passos.

# Requisitos
   Python(3.8+)<br>
   Testado com sistema operacional Windows 11 e Linux Ubuntu 20.0 <br>
   <a href="https://ffmpeg.org/">FFMPEG </a>: Uma solução completa e multiplataforma para gravar, converter e transmitir áudio e vídeo.<br>
   <a href="https://alphacephei.com/vosk/">VOSK </a>: Ferramenta para reconhecimento de fala offline, pois suporta PT-BR muito bem e não é preciso pagar alguma API.<br>
   <a href="https://platform.openai.com/docs/introduction">OpenAI </a>: Utilizado a API do OpenAI para fazer o resumo das reuniões (aqui é pago, por exemplo, eu utilizei $5 e já upei mais de 50 reuniões e ainda tenho créditos)<br>
   Use: <b>pip install -r requirements.txt</b> para instalar as bibliotecas necessárias<br>
