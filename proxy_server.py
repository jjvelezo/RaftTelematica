import service_pb2
import service_pb2_grpc
import grpc
from concurrent import futures
import random
import time, threading

DB_SERVERS = [
    {'host': '10.0.2.250', 'port': '50051'},   
    {'host': '10.0.2.234', 'port': '50051'},   
    {'host': '10.0.2.162', 'port': '50051'}    
]

class ProxyService(service_pb2_grpc.DatabaseServiceServicer):

    def __init__(self):
        self.db_channels = {}
        for server in DB_SERVERS:
            channel = grpc.insecure_channel(f'{server["host"]}:{server["port"]}', options=[
                ('grpc.keepalive_timeout_ms', 1000)  # Timeout de 1 segundo
            ])
            stub = service_pb2_grpc.DatabaseServiceStub(channel)
            self.db_channels[server["host"]] = stub

        self.current_leader = None
        self.server_status = {server["host"]: {"role": "unknown", "state": "inactive"} for server in DB_SERVERS}

        # Iniciar el ciclo de Pings
        self.start_ping_loop()

    def start_ping_loop(self):
        def ping_servers():
            while True:
                leaders = []
                for ip, stub in self.db_channels.items():
                    try:
                        # Ping para obtener el estado y rol del nodo
                        response = stub.Ping(service_pb2.PingRequest(message="ping"))
                        
                        # Verificar si el estado ha cambiado
                        if self.server_status[ip]["state"] != "active" or self.server_status[ip]["role"] != response.role:
                            print(f"Node {ip} is now active with role {response.role}")
                        
                        # Actualizar el estado y rol del nodo en el proxy
                        self.server_status[ip] = {"role": response.role, "state": response.state}

                        # Si el nodo es líder y está activo, agregar a la lista de líderes
                        if response.role == "leader" and self.server_status[ip]["state"] == "active":
                            leaders.append(ip)
                            if self.current_leader != ip:
                                self.current_leader = ip
                                print(f"\nNew leader identified: {self.current_leader}")

                    except grpc.RpcError as e:
                        if self.server_status[ip]["state"] != "inactive":
                            # Error al contactar con el nodo
                            if e.code() == grpc.StatusCode.UNAVAILABLE:
                                print(f"Node {ip} is unavailable (Connection refused)")
                            else:
                                print(f"Error contacting node {ip}: {e.details() if e.details() else 'Unknown error'}")
                            self.server_status[ip] = {"role": "unknown", "state": "inactive"}

                # Si hay más de un líder, degradar a los otros
                if len(leaders) > 1:
                    print(f"\nMultiple leaders detected: {leaders}. Degrading extra leaders to followers.")
                    for ip in leaders:
                        if ip != self.current_leader:  
                            self.degrade_to_follower(ip)

                # Imprimir el estado actual de los servidores
                print("\nEstado actual de los servidores:")
                for ip, status in self.server_status.items():
                    print(f"Servidor {ip} - Rol: {status['role']}, Estado: {status['state']}")

                # Enviar la lista de nodos activos a todos los nodos
                self.send_active_list_to_all()
                time.sleep(5)

        ping_thread = threading.Thread(target=ping_servers)
        ping_thread.daemon = True
        ping_thread.start()

    def degrade_to_follower(self, ip):
        """Degradar un líder adicional a seguidor"""
        print(f"Degrading leader {ip} to follower.")
        try:
            stub = self.db_channels[ip]
            stub.DegradeToFollower(service_pb2.DegradeRequest())  # Enviar solicitud de degradación
        except grpc.RpcError as e:
            print(f"Error contacting leader {ip} for degradation: {e}")

    def send_active_list_to_all(self):
        """Enviar la lista de instancias activas a todos los nodos activos."""
        active_instances = [ip for ip, status in self.server_status.items() if status["state"] == "active"]

        for ip, stub in self.db_channels.items():
            if self.server_status[ip]["state"] == "active":
                try:
                    request = service_pb2.UpdateRequest(active_nodes=active_instances)
                    stub.UpdateActiveNodes(request)
                    print(f"Sent active node list to {ip}: {active_instances}")
                except grpc.RpcError as e:
                    print(f"Error sending active node list to {ip}: {e.details() if e.details() else 'Unknown error'}")
                    self.server_status[ip]["state"] = "inactive"

    def find_leader(self):
        """Encuentra y asigna el líder actual."""
        for ip, status in self.server_status.items():
            if status["role"] == "leader" and status["state"] == "active":
                self.current_leader = ip
                print(f"Líder encontrado: {self.current_leader}")
                return
            
        print("No se encontró líder activo.")
        self.current_leader = None

    def ReadData(self, request, context):
        """Leer datos de cualquier follower disponible."""
        followers = [ip for ip, status in self.server_status.items() if status["role"] == "follower" and status["state"] == "active"]
        if followers:
            follower_stub = random.choice([self.db_channels[ip] for ip in followers])
            try:
                response = follower_stub.ReadData(request)
                return response
            except Exception as e:
                print(f"Error reading data from follower: {e}")
                return service_pb2.ReadResponse(result="ERROR: Unable to read data.")
        else:
            return service_pb2.ReadResponse(result="ERROR: No followers available.")

    def WriteData(self, request, context):
        """Escribir datos en el líder."""
        if self.current_leader is None:
            self.find_leader()

        if self.current_leader:
            leader_stub = self.db_channels[self.current_leader]
            try:
                response = leader_stub.WriteData(request)
                return response
            except grpc.RpcError as e:
                print(f"Error writing data to leader: {e}")
                self.find_leader()  # Reintentar encontrar un nuevo líder
                return service_pb2.WriteResponse(status="ERROR: Unable to write data.")
        else:
            return service_pb2.WriteResponse(status="ERROR: No leader available for writing.")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_DatabaseServiceServicer_to_server(ProxyService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Proxy server started on port 50052.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()