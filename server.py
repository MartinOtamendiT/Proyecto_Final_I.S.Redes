import asyncio
from Crypto.Cipher import AES
from dotenv import load_dotenv
import os

load_dotenv()

HOST = "0.0.0.0"
PORT = os.getenv('PORT')
shared_key = os.getenv('CRYPTOKEY')
remote_addresses = list()
if not shared_key:
    raise ValueError("La variable de entorno SHARED_KEY no está definida en el archivo .env")
encoded_key = shared_key.encode("utf-8")
trunk_encoded_key = encoded_key[:16]

async def handle_clients(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    connected_address = writer.get_extra_info('peername')
    if connected_address[0] in remote_addresses:
        print(f"cliente {connected_address[0]} ya está conectado, nueva conexión rechazada")
        writer.close()
        await writer.wait_closed()
    else:
        print(f"Nueva conexión recibida desde la IP {connected_address[0]}") 
        remote_addresses.append(connected_address[0])

    await login(reader,writer)
    cipher = AES.new(trunk_encoded_key,AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest("Salir".encode())
    writer.write(cipher.nonce + ciphertext)
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def login(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    cipher = AES.new(trunk_encoded_key,AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest("Bienvenido a el servidor, para iniciar por favor introduce tu nombre de usuario: ".encode())
    writer.write(cipher.nonce + ciphertext)
    await writer.drain()
    username = await reader.read(1024)
    cipher = AES.new(trunk_encoded_key, AES.MODE_EAX, nonce=username[:16])
    message = cipher.decrypt(username[16:])
    print(ciphertext)
    cipher = AES.new(trunk_encoded_key,AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest("Ahora introduce tu contraseña: ".encode())
    writer.write(cipher.nonce + ciphertext)
    await writer.drain()
    password = await reader.read(1024)
    cipher = AES.new(trunk_encoded_key, AES.MODE_EAX, nonce=password[:16])
    message = cipher.decrypt(password[16:])
    print(ciphertext)

async def run_server():
    server = await asyncio.start_server(handle_clients,HOST,PORT)

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(run_server())
