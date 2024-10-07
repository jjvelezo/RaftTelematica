import service_pb2
import service_pb2_grpc
import grpc
from concurrent import futures

DB_HOST = '10.0.2.250'  #  IP privada de la instancia de la base de datos
DB_PORT = '50051'

class ProxyService(service_pb2_grpc.DatabaseServiceServicer):

    def __init__(self):
        # Crear el canal gRPC con la base de datos
        self.db_channel = grpc.insecure_channel(f'{DB_HOST}:{DB_PORT}')
        self.db_stub = service_pb2_grpc.DatabaseServiceStub(self.db_channel)

    def ReadData(self, request, context):
        # Redirigir solicitud de lectura al servidor de base de datos
        response = self.db_stub.ReadData(request)
        return response

    def WriteData(self, request, context):
        # Redirigir solicitud de escritura al servidor de base de datos
        response = self.db_stub.WriteData(request)
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_DatabaseServiceServicer_to_server(ProxyService(), server)
    server.add_insecure_port('[::]:50052')  # Puerto del proxy
    server.start()
    print("Proxy server started on port 50052.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
