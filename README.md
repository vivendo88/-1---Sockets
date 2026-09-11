1 ) Fundamentos de Sockets TCP

Um socket TCP é uma interface de comunicação fornecida pelo sistema operacional que permite que dois programas troquem dados através de uma rede utilizando o protocolo TCP. Ele funciona como um ponto de comunicação entre uma aplicação e a pilha de protocolos de rede, permitindo que o programa envie e receba dados por meio de uma conexão TCP . 

Uma comunicação TCP normalmente envolve um cliente e um servidor. O servidor cria um socket, associa esse socket a um endereço IP e a uma porta por meio de bind(), coloca-o em estado de escuta com listen() e aguarda conexões usando accept(). O cliente cria seu próprio socket e utiliza connect() para solicitar uma conexão com o endereço IP e a porta do servidor.

Quando a conexão é estabelecida, os dois lados podem utilizar operações como send() e recv() para trocar dados. O TCP garante características importantes para essa comunicação, como entrega confiável dos dados, ordenação dos bytes, controle de fluxo, controle de congestionamento e retransmissão de dados perdidos. 

É importante destacar que o TCP trabalha com um fluxo contínuo de bytes, e não com mensagens individuais. Durante a transmissão, os dados enviados via send() são gravados nos buffers de envio do sistema e trafegam até os buffers de recepção da outra ponta (com leituras limitadas a tamanhos configurados, como TAM_BUFFER = 1024). Por essa razão, não se pode garantir que cada chamada de send() em uma extremidade resulte em exatamente um recv() na extremidade oposta: uma única mensagem pode ser fragmentada em múltiplos recv(), ou mensagens distintas enviadas em sequência podem ser agrupadas e entregues em um único recv().

Por esses motivos, a aplicação precisa tratar o recebimento de mensagens através de um buffer próprio (como a estrutura Device.buffer) associado a funções de leitura e enquadramento (ReceiveMessage) . Esse mecanismo acumula os bytes lidos do socket até completar uma mensagem inteira e válida segundo o protocolo e as definições do sistema (MSG_REGISTRO, MSG_LISTA_AMBIENTES, MSG_SELECIONA_AMBIENTE, MSG_SENSOR, MSG_LAMPADA, MSG_STATUS), preservando eventuais dados restantes para as próximas leituras. 


2) Detalhe do Fluxograma a Thread Principal  basicamente o sistema funciona assim:

A Thread Principal é a primeira a rodar. Ela é responsável por iniciar tudo que o servidor precisa, como carregar as estruturas de dados e ficar "ouvindo" se algum dispositivo vai se conectar via TCP. Quando um cliente aparece, ela cria uma DeviceThread especial só para ele, que vai cuidar de toda a comunicação com aquele dispositivo específico.
Assim que a DeviceThread é criada, ela faz um handshake com o dispositivo. Isso é como uma "conversa inicial" para verificar qual é o modelo do dispositivo (se é Lâmpada, Sensor de Presença ou Termômetro). Depois, ela envia a lista de ambientes disponíveis, o usuário escolhe um, e a thread atribui um ID exclusivo para aquele cliente. E olha, esse processo de atribuir ID precisa ser feito com cuidado, usando Lock, para evitar que dois dispositivos recebam o mesmo ID ao mesmo tempo (concorrência, né?).
Agora, cada categoria de dispositivo se comporta de um jeito diferente:
    • Termômetro: É o mais simples. Ele só recebe as variações de temperatura que o cliente envia, atualiza o valor interno e manda uma confirmação de volta (como um "LEITURA_RECEBIDA"). Não faz mais nada além disso.
    • Sensor de Presença: Esse é mais ativo. Quando ele detecta movimento (0 = ninguém, 1 = tem gente), ele cria um objeto chamado MonitorItem, coloca as informações lá dentro e publica esse objeto em uma fila global chamada controlQueue. Depois disso, ele também confirma pro cliente que recebeu a informação.
    • Lâmpada: Essa é a mais complexa. Quando uma lâmpada se conecta, a DeviceThread dela cria uma fila própria chamada lampQueue (que vai ser usada só para enviar comandos pra ela). Em seguida, ela publica na controlQueue um pedido de INCLUIR_LAMPADA para avisar que entrou no sistema. Depois disso, ela entra em espera bloqueante, ou seja, fica parada aguardando alguém colocar algo na lampQueue dela.
Enquanto isso, tem a Thread de Controle Geral, que fica rodando num loop infinito consumindo tudo o que chega na controlQueue. Ela é como se fosse o "cérebro" do sistema, orquestrando tudo.
Quando ela processa um evento de INCLUIR_LAMPADA, ela associa a lampQueue daquela lâmpada ao ambiente (RoomItem) correspondente. Isso faz com que o sistema saiba quais lâmpadas estão em cada cômodo.
Quando ela recebe uma notificação de presença (o MonitorItem do Sensor), ela procura todas as lâmpadas daquele ambiente e envia o comando (acender ou apagar) para cada uma das lampQueues.
Aí a DeviceThread da lâmpada, que estava parada esperando, é desbloqueada quando aparece algo na fila dela. Ela pega o comando, envia via TCP para a lâmpada física, e fica esperando a confirmação de que o comando foi executado. Depois que recebe essa confirmação, ela volta a monitorar a fila de novo.
E se por algum motivo a lâmpada desconectar, a DeviceThread dela publica um evento EXCLUIR_LAMPADA na controlQueue, e a Thread de Controle remove a lâmpada do ambiente, garantindo que não fique nenhum "resquício" no sistema.


<img width="3114" height="4813" alt="fluxograma" src="https://github.com/user-attachments/assets/b3edac0b-e431-47d0-8ff4-030fc5246092" />


O Protocolo de Comunicação: 

O fluxo inicia com o cliente enviando uma solicitação de registro (MSG_REGISTRO) contendo o tipo de dispositivo.
    • O servidor valida o dispositivo e responde enviando a lista com os ambientes disponíveis (MSG_LISTA_AMBIENTES).
    • O cliente envia a seleção do ambiente escolhido (MSG_SELECIONA_AMBIENTE), associando-se ao local desejado.
    • O servidor confirma o cadastro enviando status de registrado (MSG_STATUS com DISPOSITIVO_REGISTRADO) e o ID gerado.
    • Em operação, o sensor envia leituras (MSG_SENSOR) com seus valores lidos e aguarda o servidor responder.
    • O servidor responde ao sensor confirmando o recebimento por meio de mensagem de status (MSG_STATUS com LEITURA_RECEBIDA).
    • Para atuadores, o servidor envia comandos de acionamento (MSG_LAMPADA) indicando se a lâmpada deve acender ou apagar.
    • Ao executar a ação, o dispositivo lâmpada devolve uma mensagem de confirmação (MSG_STATUS com ACAO_EXECUTADA).
    • O cabeçalho fixo estrutura os campos obrigatórios em ordem: código da mensagem, data/hora do envio e ID do dispositivo.
    • Tais campos possuem tamanhos múltiplos de 1 byte (octetos), seguidos pelo payload específico de cada tipo de mensagem.

Mensagem enviada pelo Cliente (Sensor de Presença) ao Servidor:
    • Tipo da mensagem: MSG_SENSOR (código 5)
    • Campos da mensagem:
        ◦ Código da mensagem: 5 (MSG_SENSOR)
        ◦ Data e hora: 2026-09-09 11:35:45
        ◦ ID do dispositivo: 1 (identificador atribuído durante o registro)
        ◦ Payload (valor do sensor): 1 (PRESENCA_DETECTADA)
Mensagem de resposta enviada pelo Servidor ao Cliente:
    • Tipo da mensagem: MSG_STATUS (código 1)
    • Campos da mensagem:
        ◦ Código da mensagem: 1 (MSG_STATUS)
        ◦ Data e hora: 2026-09-09 11:35:45
        ◦ ID do dispositivo: 1
        ◦ Payload (status retornado): 2 (LEITURA_RECEBIDA)

<img width="1718" height="496" alt="6 1 Mensagens enviadas pelos sensor " src="https://github.com/user-attachments/assets/de616755-4e29-4589-9529-3c9bd9ebc81b" />



 O ROTEIRO DE TESTE


    Abra o local do arquivo 
    cd Downloads/src

<img width="615" height="116" alt="1 local dos arquivos" src="https://github.com/user-attachments/assets/a966fa1b-5875-4d7d-9869-8dce8b6b7a51" />

     Inicie o Servidor 
       python3 Sever.py
       
  <img width="574" height="623" alt="2 Iniciando servidor" src="https://github.com/user-attachments/assets/8c0feb7d-02a7-430a-8616-fa416ac17b7a" />

          • Inicie o dispositivo lâmpada
            python3 Cliente_Lampada.py 
           #Repare que o servidor já atribui uma porta de comunicação pra ele

<img width="1595" height="903" alt="3 Iniciando Cliente_lampada" src="https://github.com/user-attachments/assets/00f6de61-595e-4f27-9e7b-b05df00e60aa" />

        • Selecione o ambiente do dispositivo
       #Repare que o servido já registra o dispositivo e ambiente que ele esta

<img width="1052" height="388" alt="4 Selecionando_ambiente" src="https://github.com/user-attachments/assets/79c4b3ea-f954-451f-8880-ad1ffc212f68" />


Inicie o sensor de presença 
    	python3 Cliente_Presenca.py 
        #Lembre de após iniciar sensor de presença selecionar o mesmo local selecionado na lâmpada
        
<img width="1236" height="800" alt="5 Iniciado sensor_presença" src="https://github.com/user-attachments/assets/0b8d4be4-d796-4279-9dcc-26486bca1337" />

 • Executando sensor de Presença 
#Após selecionar opção 1 repare que o servido envia uma mensagem pra lampada acionando a mesma 
<img width="1416" height="624" alt="6 executando comando sensor de presença" src="https://github.com/user-attachments/assets/29a4ae6c-5711-447e-99a2-09aa096c4249" />

• Mensagens trocadas entre o Cliente_Presença e Servidor 
      
Cliente → Servidor de código 5: Ao selecionar a opção 1 (presença detectada), o sensor envia a mensagem 5: Leitura, Dispositivo: 1, Valor do sensor: 1 (1.0). O servidor encaminha o comando recebido para a fila de controle do ambiente (Comando chegando na fila do controle do ambiente 1.
 Servidor →  Cliente código 1: O servidor retorna uma mensagem de confirmação com status LEITURA_RECEBIDA (Leitura recebida pelo servidor!!!), concluindo o ciclo de leitura.
 <img width="1718" height="496" alt="6 1 Mensagens enviadas pelos sensor " src="https://github.com/user-attachments/assets/49728000-0926-451f-a203-352e3e57229e" />

• Simulando um dispositivo com falha
Realizado alteração na linha “device = Device(connection, NUM_SENSOR_PRESENCA) “
para “device = Device(connection, 45)”  para forçar falha de registro.

<img width="938" height="976" alt="8 Simulando falha dispositvo não cadastrado" src="https://github.com/user-attachments/assets/d4635747-942b-44fc-befd-b4f40925d2f4" />
<img width="936" height="1004" alt="8 1 Simulando falha dispositvo não cadastrado" src="https://github.com/user-attachments/assets/e86e3870-b5a4-4f7e-b0aa-26e0dd9f651e" />



No log do servidor, a tentativa de conexão vinda da porta  51800 registra a seguinte sequência:



<img width="1869" height="997" alt="8 2 Simulando falha dispositvo não cadastrado" src="https://github.com/user-attachments/assets/3557265c-5c3b-4c36-a42c-0b8ec7dcae62" />





***3 )Extensão do Sistema***

  Criado o arquivo "Cliente_Arcondicionado.py"
  <img width="913" height="926" alt="10 2 - criado o arquivo que executa o disposivo arcondicionado" src="https://github.com/user-attachments/assets/6d36dc41-7900-4295-9da5-f0d9889d61aa" /> 


  Adicionado no arquivo dispostivo.txt o novo dispositivo "ar-condicionado"

  <img width="545" height="150" alt="10 - adicionando ar_conficionado no arquivo disposivo" src="https://github.com/user-attachments/assets/b57343e0-619c-47c4-9d1d-2331761f57aa" />


   
   Editado o arquivo de Config.py

   <img width="675" height="976" alt="10 1 - adicionando codigos ar_conficionado no arquivo config" src="https://github.com/user-attachments/assets/a736c1e6-09c7-4142-8e33-e6a3fefa0a8f" />

   
   
   Editado o arquivo Server.py

   <img width="1454" height="700" alt="10 3 2- Editado arquivo Sever py" src="https://github.com/user-attachments/assets/d9c7342b-5bcb-470d-ba96-a9afe138c745" />

   
   
   Editado o arquivo DeciceThread.py


   <img width="1416" height="550" alt="10 3 3- Editado arquivo DeviceThread py" src="https://github.com/user-attachments/assets/57785832-1af4-4ee6-8252-2bb5c8e0caf0" />



   



   


   


  

  















    





       

    

    



        
          
