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
                        response = stub.Ping(service_pb2.PingRequest(message="ping"))
                        if self.server_status[ip]["state"] != "active" or self.server_status[ip]["role"] != response.role:
                            print(f"Node {ip} is now active with role {response.role}")
                        self.server_status[ip] = {"role": response.role, "state": response.state}

                        if response.role == "leader" and self.server_status[ip]["state"] == "active":
                            leaders.append(ip)
                            if self.current_leader != ip:
                                self.current_leader = ip
                                print(f"\nNew leader identified: {self.current_leader}")

                    except grpc.RpcError as e:
                        if self.server_status[ip]["state"] != "inactive":
                            if e.code() == grpc.StatusCode.UNAVAILABLE:
                                print(f"Node {ip} is unavailable (Connection refused)")
                            else:
                                print(f"Error contacting node {ip}: {e.details() if e.details() else 'Unknown error'}")
                            self.server_status[ip] = {"role": "unknown", "state": "inactive"}

                # Si hay más de un lider, degradar a los otros
                if len(leaders) > 1:
                    print(f"\nMultiple leaders detected: {leaders}. Degrading extra leaders to followers.")
                    for ip in leaders:
                        if ip != self.current_leader:  
                            self.degrade_to_follower(ip)

                # Imprimir el estado actual de los servidores
                print("\nEstado actual de los servidores:")
                for ip, status in self.server_status.items():
                    print(f"Servidor {ip} - Rol: {status['role']}, Estado: {status['state']}")

                self.send_active_list_to_all()
                time.sleep(5)

        ping_thread = threading.Thread(target=ping_servers)
        ping_thread.daemon = True
        ping_thread.start()

#Solicitud de lider a follower
    def degrade_to_follower(self, ip):
        print(f"Degrading leader {ip} to follower.")
        try:
            stub = self.db_channels[ip]
            stub.DegradeToFollower(service_pb2.DegradeRequest())  # Enviar solicitud de degradacion
        except grpc.RpcError as e:
            print(f"Error contacting leader {ip} for degradation: {e}")


    def send_active_list_to_all(self):
        active_instances = [ip for ip, status in self.server_status.items() if status["state"] == "active"]

        for ip, stub in self.db_channels.items():
            if self.server_status[ip]["state"] == "active":
                try:
                    # Enviar la lista de instancias activas a cada nodo
                    request = service_pb2.UpdateRequest(active_nodes=active_instances)
                    stub.UpdateActiveNodes(request)
                    print(f"Sent active node list to {ip}: {active_instances}")

                    # Si es la primera vez que un nodo se vuelve "active", replicar los datos
                    if self.server_status[ip].get("just_activated", False):
                        print(f"Replicating data to newly activated node {ip}")
                        self.replicate_data_to_new_node(ip)

                        # Marcar que ya no es "just_activated"
                        self.server_status[ip]["just_activated"] = False
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
        if self.current_leader is None:
            self.find_leader()

        if self.current_leader:
            leader_stub = self.db_channels[self.current_leader]
            try:
                response = leader_stub.WriteData(request)
                return response
            except grpc.RpcError as e:
                print(f"Error writing data to leader: {e}")
                self.find_leader()
                return service_pb2.WriteResponse(status="ERROR: Unable to write data.")
        else:
            return service_pb2.WriteResponse(status="ERROR: No leader available for writing.")
        
    def replicate_data_to_new_node(self, new_node_ip):
        if self.current_leader:
            try:
                # Abrir el canal gRPC con el líder
                leader_stub = self.db_channels[self.current_leader]

                # Pedir al líder que replique sus datos al nuevo nodo
                print(f"Requesting leader {self.current_leader} to replicate data to {new_node_ip}")
                request = service_pb2.WriteRequest(data="")
                response = leader_stub.ReplicateData(request)

                if response.status.startswith("ERROR"):
                    print(f"Failed to replicate data to {new_node_ip}: {response.status}")
                else:
                    # Si la replicación es exitosa, escribir los datos en el nuevo nodo
                    print(f"Replication data: {response.status}")
                    self.write_data_to_follower(new_node_ip, response.status)  # Escribir los datos en el nuevo nodo
            except grpc.RpcError as e:
                print(f"Error contacting leader {self.current_leader} for data replication: {e.details()}")

    def write_data_to_follower(self, new_node_ip, data):
        try:
            # Abrir el canal gRPC con el nuevo nodo
            follower_stub = self.db_channels[new_node_ip]
            write_request = service_pb2.WriteRequest(data=data)
            response = follower_stub.WriteData(write_request)
            if response.status == "SUCCESS":
                print(f"Data successfully written to follower {new_node_ip}")
            else:
                print(f"Failed to write data to follower {new_node_ip}: {response.status}")
        except grpc.RpcError as e:
            print(f"Error writing data to follower {new_node_ip}: {e.details()}")



def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_DatabaseServiceServicer_to_server(ProxyService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Proxy server started on port 50052.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()