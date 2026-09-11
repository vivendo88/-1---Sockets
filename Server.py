#####################################################
#                                                   #
# Título do trabalho: Trabalho de Sockets           #
#         Disciplina: Redes de Computadores PPComp  #
#                                                   #
#####################################################

import socket
import threading
import queue
from Config import *
from ControlItem import *
from DeviceThread import DeviceThread


def CarregarTabelas():
        # Carrega a tabela de ambientes
        try:
                with open(ARQUIVO_AMBIENTES, 'r', encoding='utf-8') as f:
                        for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                        parts = line.split(',')
                                        roomID = parts[0].strip()
                                        roomName = parts[1].strip()
                                        AddRoomItem(RoomItem(roomID, roomName))
        except Exception as e:
                print(f'Erro ao carregar {ARQUIVO_AMBIENTES}: {e}')
                exit()

        # Carrega a tabela de tipos de dispositivos
        try:
                with open(ARQUIVO_TIPOS_DISPOSITIVOS, 'r', encoding='utf-8') as f:
                        for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                        parts = line.split(',')
                                        typeID = parts[0].strip()
                                        typeCode = parts[1].strip()
                                        typeName = parts[2].strip()
                                        AddTypeItem(TypeItem(typeID, typeCode, typeName))
        except Exception as e:
                print(f'Erro ao carregar {ARQUIVO_TIPOS_DISPOSITIVOS}: {e}')
                exit()


def ControlThread(controlQueue):
        print('Thread de controle iniciada...')
        while True:
                item = controlQueue.get()
                if item == None:
                        break

                # Manutenção de atuadores (Lâmpada / Ar-Condicionado)
                if item.deviceTypeCode == COD_LAMPADA or item.deviceTypeCode == COD_AR_CONDICIONADO:
                        roomItem = GetRoomItem(item.roomID)
                        if roomItem != None:
                                if item.command == INCLUIR_LAMPADA:
                                        roomItem.AddLamp(item.deviceID, item.lampQueue)
                                elif item.command == EXCLUIR_LAMPADA:
                                        roomItem.DelLamp(item.deviceID)

                # Sensor de Presença acionando atuadores do ambiente
                elif item.deviceTypeCode == COD_SENSOR_PRESENCA:
                        roomItem = GetRoomItem(item.roomID)
                        if roomItem != None:
                                if item.command == PRESENCA_DETECTADA:
                                        print(f'Presença detectada no ambiente [{item.roomID}] {roomItem.roomName}')
                                        roomItem.Sensor(LUZ_ACESA)
                                elif item.command == PRESENCA_NAO_DETECTADA:
                                        print(f'Presença não detectada no ambiente [{item.roomID}] {roomItem.roomName}')
                                        roomItem.Sensor(LUZ_APAGADA)

                # Leitura do Termômetro: liga se temperatura for maior que 22, caso contrário desliga
                elif item.deviceTypeCode == COD_TERMOMETRO:
                        roomItem = GetRoomItem(item.roomID)
                        if roomItem != None:
                                try:
                                        temp = float(item.command)
                                        if temp > 22.0:
                                                print(f'Temperatura {temp} > 22.0 no ambiente [{item.roomID}] {roomItem.roomName}: Acionando atuadores (LIGAR)')
                                                roomItem.Sensor(LUZ_ACESA)
                                        else:
                                                print(f'Temperatura {temp} <= 22.0 no ambiente [{item.roomID}] {roomItem.roomName}: Acionando atuadores (DESLIGAR)')
                                                roomItem.Sensor(LUZ_APAGADA)
                                except (ValueError, TypeError):
                                        print(f'Valor de temperatura inválido recebido: {item.command}')


if __name__ == '__main__':
        print('Inicializando Servidor...')
        CarregarTabelas()

        controlQueue = queue.Queue()
        ctrlThread = threading.Thread(target=ControlThread, args=(controlQueue,))
        ctrlThread.daemon = True
        ctrlThread.start()

        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
                serverSocket.bind((SERVIDOR, PORTA))
                serverSocket.listen(5)
                print(f'Servidor pronto e escutando em {SERVIDOR}:{PORTA}...')
        except Exception as e:
                print(f'Falha ao iniciar o socket do servidor: {e}')
                exit()

        try:
                while True:
                        connection, clientAddress = serverSocket.accept()
                        clientIP = f'{clientAddress[0]}:{clientAddress[1]}'
                        t = threading.Thread(target=DeviceThread, args=(connection, clientIP, controlQueue))
                        t.daemon = True
                        t.start()
        except KeyboardInterrupt:
                print('\nEncerrando servidor...')
        finally:
                serverSocket.close()#####################################################
#                                                   #
# Título do trabalho: Trabalho de Sockets           #
#         Disciplina: Redes de Computadores PPComp  #
#                                                   #
#####################################################

import socket
import threading
import queue
from Config import *
from ControlItem import *
from DeviceThread import DeviceThread


def CarregarTabelas():
        # Carrega a tabela de ambientes
        try:
                with open(ARQUIVO_AMBIENTES, 'r', encoding='utf-8') as f:
                        for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                        parts = line.split(',')
                                        roomID = parts[0].strip()
                                        roomName = parts[1].strip()
                                        AddRoomItem(RoomItem(roomID, roomName))
        except Exception as e:
                print(f'Erro ao carregar {ARQUIVO_AMBIENTES}: {e}')
                exit()

        # Carrega a tabela de tipos de dispositivos
        try:
                with open(ARQUIVO_TIPOS_DISPOSITIVOS, 'r', encoding='utf-8') as f:
                        for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                        parts = line.split(',')
                                        typeID = parts[0].strip()
                                        typeCode = parts[1].strip()
                                        typeName = parts[2].strip()
                                        AddTypeItem(TypeItem(typeID, typeCode, typeName))
        except Exception as e:
                print(f'Erro ao carregar {ARQUIVO_TIPOS_DISPOSITIVOS}: {e}')
                exit()


def ControlThread(controlQueue):
        print('Thread de controle iniciada...')
        while True:
                item = controlQueue.get()
                if item == None:
                        break

                # Manutenção de atuadores (Lâmpada / Ar-Condicionado)
                if item.deviceTypeCode == COD_LAMPADA:
                        roomItem = GetRoomItem(item.roomID)
                        if roomItem != None:
                                if item.command == INCLUIR_LAMPADA:
                                        roomItem.AddLamp(item.deviceID, item.lampQueue)
                                elif item.command == EXCLUIR_LAMPADA:
                                        roomItem.DelLamp(item.deviceID)

                # Sensor de Presença acionando atuadores do ambiente
                elif item.deviceTypeCode == COD_SENSOR_PRESENCA:
                        roomItem = GetRoomItem(item.roomID)
                        if roomItem != None:
                                if item.command == PRESENCA_DETECTADA:
                                        print(f'Presença detectada no ambiente [{item.roomID}] {roomItem.roomName}')
                                        roomItem.Sensor(LUZ_ACESA)
                                elif item.command == PRESENCA_NAO_DETECTADA:
                                        print(f'Presença não detectada no ambiente [{item.roomID}] {roomItem.roomName}')
                                        roomItem.Sensor(LUZ_APAGADA)

                # Leitura do Termômetro: liga se temperatura for maior que 22, caso contrário desliga
                elif item.deviceTypeCode == COD_TERMOMETRO:
                        roomItem = GetRoomItem(item.roomID)
                        if roomItem != None:
                                try:
                                        temp = float(item.command)
                                        if temp > 22.0:
                                                print(f'Temperatura {temp} > 22.0 no ambiente [{item.roomID}] {roomItem.roomName}: Acionando atuadores (LIGAR)')
                                                roomItem.Sensor(LUZ_ACESA)
                                        else:
                                                print(f'Temperatura {temp} <= 22.0 no ambiente [{item.roomID}] {roomItem.roomName}: Acionando atuadores (DESLIGAR)')
                                                roomItem.Sensor(LUZ_APAGADA)
                                except (ValueError, TypeError):
                                        print(f'Valor de temperatura inválido recebido: {item.command}')


if __name__ == '__main__':
        print('Inicializando Servidor...')
        CarregarTabelas()

        controlQueue = queue.Queue()
        ctrlThread = threading.Thread(target=ControlThread, args=(controlQueue,))
        ctrlThread.daemon = True
        ctrlThread.start()

        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
                serverSocket.bind((SERVIDOR, PORTA))
                serverSocket.listen(5)
                print(f'Servidor pronto e escutando em {SERVIDOR}:{PORTA}...')
        except Exception as e:
                print(f'Falha ao iniciar o socket do servidor: {e}')
                exit()

        try:
                while True:
                        connection, clientAddress = serverSocket.accept()
                        clientIP = f'{clientAddress[0]}:{clientAddress[1]}'
                        t = threading.Thread(target=DeviceThread, args=(connection, clientIP, controlQueue))
                        t.daemon = True
                        t.start()
        except KeyboardInterrupt:
                print('\nEncerrando servidor...')
        finally:
                serverSocket.close()
