import csv
import service_pb2
import service_pb2_grpc
import grpc
from concurrent import futures
import os
import time
import random
from threading import Thread

DB_FILE = 'database.csv'

# Estado inicial del nodo
ROLE = 'follower'
CURRENT_TERM = 0
VOTED_FOR = None
LEADER_ID = None
TIMEOUT = random.uniform(0.15, 0.3)


OTHER_DB_NODES = ['10.0.2.162', '10.0.2.234']
#OTHER_DB_NODES = ['10.0.2.250', '10.0.2.234']
#OTHER_DB_NODES = ['10.0.2.250', '10.0.2.162']

class DatabaseService(service_pb2_grpc.DatabaseServiceServicer):

    def ReadData(self, request, context):
        global ROLE
        print(f"[{ROLE}] - Read operation requested")
        
        with open(DB_FILE, mode='r') as csv_file:
            reader = csv.reader(csv_file)
            rows = [','.join(row) for row in reader]
            result = "\n".join(rows)
        
        print(f"[{ROLE}] - Read operation completed")
        return service_pb2.ReadResponse(result=result)

    def WriteData(self, request, context):
        global ROLE
        if ROLE == 'leader':
            print(f"[{ROLE}] - Write operation requested")
            data = request.data.split(',')
            new_id = data[0]

            # Verificar si el ID ya existe
            with open(DB_FILE, mode='r') as csv_file:
                reader = csv.reader(csv_file)
                for row in reader:
                    if row[0] == new_id:
                        print(f"[{ROLE}] - Write operation failed: ID already exists")
                        return service_pb2.WriteResponse(status="ERROR: ID ya existente")

            # Si el ID no existe, agregar al CSV
            with open(DB_FILE, mode='a') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(data)
            
            print(f"[{ROLE}] - Write operation completed")
            return service_pb2.WriteResponse(status="SUCCESS")
        else:
            print(f"[{ROLE}] - Write operation attempted on follower - Redirect to leader required")
            return service_pb2.WriteResponse(status="ERROR: Cannot write to follower")

    def RequestVote(self, request, context):
        global CURRENT_TERM, VOTED_FOR
        term = request.term
        candidate_id = request.candidate_id

        # Votar si el término del candidato es mayor al actual y aún no ha votado en este término
        if term > CURRENT_TERM or (term == CURRENT_TERM and VOTED_FOR is None):
            VOTED_FOR = candidate_id
            CURRENT_TERM = term
            print(f"[{ROLE}] - Voted for {candidate_id} in term {term}")
            return service_pb2.VoteResponse(granted=True)
        
        print(f"[{ROLE}] - Vote denied to {candidate_id} in term {term}")
        return service_pb2.VoteResponse(granted=False)

    def AppendEntries(self, request, context):
        global ROLE, LEADER_ID, CURRENT_TERM, TIMEOUT
        if request.term >= CURRENT_TERM:
            CURRENT_TERM = request.term
            LEADER_ID = request.leader_id
            ROLE = 'follower'
            TIMEOUT = random.uniform(0.15, 0.3)  # Restablecer el timeout
            print(f"[{ROLE}] - Received heartbeat from leader {LEADER_ID}")
        else:
            print(f"[{ROLE}] - Ignoring heartbeat from leader {request.leader_id} due to lower term")
        return service_pb2.AppendEntriesResponse(success=True)


def start_election():
    global ROLE, CURRENT_TERM, VOTED_FOR, LEADER_ID

    while True:
        time.sleep(TIMEOUT)

        if LEADER_ID is None:  
            print(f"[{ROLE}] - Timeout expired, starting election")
            ROLE = 'candidate'
            CURRENT_TERM += 1
            VOTED_FOR = 'self'
            LEADER_ID = None

            # Pedir votos a los otros nodos
            vote_count = 1  # Se vota a sí mismo
            for node_ip in OTHER_DB_NODES:
                try:
                    channel = grpc.insecure_channel(f'{node_ip}:50051')
                    stub = service_pb2_grpc.DatabaseServiceStub(channel)
                    vote_request = service_pb2.VoteRequest(term=CURRENT_TERM, candidate_id='self')
                    vote_response = stub.RequestVote(vote_request)
                    if vote_response.granted:
                        vote_count += 1
                except Exception as e:
                    print(f"[{ROLE}] - Error contacting node {node_ip}: {e}")

            # Si consigue la mayoría de votos se convierte en líder
            if vote_count > (len(OTHER_DB_NODES) + 1) // 2:
                print(f"[{ROLE}] - Became leader for term {CURRENT_TERM}")
                ROLE = 'leader'
                LEADER_ID = 'self'
                start_heartbeats()
            else:
                ROLE = 'follower'
                LEADER_ID = None


def start_heartbeats():
    global LEADER_ID, ROLE, TIMEOUT

    while ROLE == 'leader':
        print(f"[{ROLE}] - Sending heartbeats to followers")
        for node_ip in OTHER_DB_NODES:
            try:
                channel = grpc.insecure_channel(f'{node_ip}:50051')
                stub = service_pb2_grpc.DatabaseServiceStub(channel)
                heartbeat_request = service_pb2.AppendEntriesRequest(leader_id='self')
                stub.AppendEntries(heartbeat_request)
            except Exception as e:
                print(f"[{ROLE}] - Error sending heartbeat to node {node_ip}: {e}")
        time.sleep(1)  # Enviar heartbeats cada 1 segundo

def serve():
    # Reiniciar el estado del nodo al iniciar
    global ROLE, CURRENT_TERM, VOTED_FOR, LEADER_ID
    ROLE = 'follower'
    CURRENT_TERM = 0
    VOTED_FOR = None
    LEADER_ID = None

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_DatabaseServiceServicer_to_server(DatabaseService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print(f"Database server ({ROLE}) started on port 50051.")
    
    Thread(target=start_election).start()

    server.wait_for_termination()

if __name__ == '__main__':
    serve()
