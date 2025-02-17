import socket

def udp_listener(port):
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Bind the socket to the port
    server_address = ('127.0.0.1', port)
    sock.bind(server_address)
    
    print(f"Listening for UDP packets on port {port}...")
    
    while True:
        data, address = sock.recvfrom(4096)  # Buffer size of 4096 bytes
        print(f"Received: {decode_telemetry(data.decode(errors='ignore'))}")

def decode_telemetry(data: str):
    parts = data.split(',')
    return [float(num) for num in parts[1:]]

if __name__ == "__main__":
    PORT = 10022  # Change this to the desired port
    udp_listener(PORT)