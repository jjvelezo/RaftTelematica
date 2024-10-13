import csv
import service_pb2
import service_pb2_grpc
import grpc
from concurrent import futures
import os
import time
import random
from threading import Thread
import socket  # para leer ip propia

DB_FILE = 'database.csv'

# Verificar si el archivo ya existe
if os.path.exists(DB_FILE):
    print(f"El archivo '{DB_FILE}' ya existe. Se eliminará para crear uno nuevo.")
    os.remove(DB_FILE)  # Eliminar el archivo si existe
else:
    print(f"El archivo '{DB_FILE}' no existe. Creando uno nuevo.")

# Crear un nuevo archivo CSV con la estructura especificada
with open(DB_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['id', 'name', 'email'])

print(f"Archivo '{DB_FILE}' creado con la estructura: id, name, email.")

# Obtener la IP privada del servidor
def get_private_ip():
    return socket.gethostbyname(socket.gethostname())

ROLE = 'follower'
CURRENT_TERM = 0
VOTED_FOR = None
LEADER_ID = None
TIMEOUT_INITIAL = random.uniform(3.0, 5.0)  # Timeout inicial más largo
TIMEOUT_NORMAL = random.uniform(1.5, 3.0)  # Timeout normal
TIMEOUT = TIMEOUT_INITIAL
LAST_HEARTBEAT = time.time()

SERVER_IP = get_private_ip()

ALL_DB_NODES = [
    '10.0.2.250',
    '10.0.2.162',
    '10.0.2.234'
]

OTHER_DB_NODES = [ip for ip in ALL_DB_NODES if ip != SERVER_IP]
print(OTHER_DB_NODES)

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

            with open(DB_FILE, mode='r') as csv_file:
                reader = csv.reader(csv_file)
                for row in reader:
                    if row[0] == new_id:
                        print(f"[{ROLE}] - Write operation failed: ID already exists")
                        return service_pb2.WriteResponse(status="ERROR: ID ya existente")

            with open(DB_FILE, mode='a') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(data)
            
            print(f"[{ROLE}] - Write operation completed")

            # Replicar los datos a los seguidores
            self.replicate_to_followers(data)

            return service_pb2.WriteResponse(status="SUCCESS")
        else:
            print(f"[{ROLE}] - Write operation attempted on follower - Redirect to leader required")
            return service_pb2.WriteResponse(status="ERROR: Cannot write to follower")

    def ReplicateData(self, request, context):
        print(f"[{ROLE}] - Replication request received")
        data = request.data.split(',')
        print(f"[{ROLE}] - Data to replicate: {data}")

        try:
            with open(DB_FILE, mode='a') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(data)
            print(f"[{ROLE}] - Replication completed successfully")
            return service_pb2.WriteResponse(status="SUCCESS")
        except Exception as e:
            print(f"[{ROLE}] - Replication failed: {e}")
            return service_pb2.WriteResponse(status=f"ERROR: {e}")

    def replicate_to_followers(self, data):
        for follower_ip in OTHER_DB_NODES:
            try:
                channel = grpc.insecure_channel(f'{follower_ip}:50051')
                stub = service_pb2_grpc.DatabaseServiceStub(channel)
                replicate_request = service_pb2.WriteRequest(data=','.join(data))
                response = stub.ReplicateData(replicate_request)
                if response.status == "SUCCESS":
                    print(f"[{ROLE}] - Data successfully replicated to {follower_ip}")
                else:
                    print(f"[{ROLE}] - Replication to {follower_ip} failed: {response.status}")
            except Exception as e:
                print(f"[{ROLE}] - Error replicating to {follower_ip}: {e}")

    def RequestVote(self, request, context):
        global CURRENT_TERM, VOTED_FOR
        term = request.term
        candidate_id = request.candidate_id

        try:
            if term > CURRENT_TERM or (term == CURRENT_TERM and VOTED_FOR is None):
                VOTED_FOR = candidate_id
                CURRENT_TERM = term
                print(f"[{ROLE}] - Voted for {candidate_id} in term {term}")
                return service_pb2.VoteResponse(granted=True)
            
            print(f"[{ROLE}] - Vote denied to {candidate_id} in term {term}")
            return service_pb2.VoteResponse(granted=False)
        except grpc.RpcError as e:
            print(f"[{ROLE}] - Error contacting candidate {candidate_id}: {e.code()}")
            return service_pb2.VoteResponse(granted=False)

    def AppendEntries(self, request, context):
        global ROLE, LEADER_ID, TIMEOUT, LAST_HEARTBEAT

        # Si un líder recibe un heartbeat de otro líder, debe pasar a ser follower
        if ROLE == 'leader' and request.leader_id != LEADER_ID:
            print(f"[{ROLE}] - Conflict detected! Another leader {request.leader_id} exists. Switching to follower.")
            ROLE = 'follower'

        LEADER_ID = request.leader_id
        LAST_HEARTBEAT = time.time()

        if TIMEOUT == TIMEOUT_INITIAL:
            TIMEOUT = TIMEOUT_NORMAL
            print(f"[{ROLE}] - First heartbeat received, switching to normal timeout: {TIMEOUT} seconds")

        print(f"[{ROLE}] - Received heartbeat from leader {LEADER_ID}")
        return service_pb2.AppendEntriesResponse(success=True)

    def Ping(self, request, context):
        global ROLE
        return service_pb2.PingResponse(role=ROLE, state="active")

def start_election():
    global ROLE, CURRENT_TERM, VOTED_FOR, LEADER_ID, LAST_HEARTBEAT

    while True:
        time.sleep(0.1)

        if ROLE == 'follower' and (time.time() - LAST_HEARTBEAT) > TIMEOUT:
            print(f"[{ROLE}] - Timeout expired, starting election")
            ROLE = 'candidate'
            CURRENT_TERM += 1
            VOTED_FOR = None
            LEADER_ID = None

            vote_count = 1  
            for node_ip in OTHER_DB_NODES:
                try:
                    channel = grpc.insecure_channel(f'{node_ip}:50051')
                    stub = service_pb2_grpc.DatabaseServiceStub(channel)
                    vote_request = service_pb2.VoteRequest(term=CURRENT_TERM, candidate_id='self')
                    vote_response = stub.RequestVote(vote_request)
                    if vote_response.granted:
                        vote_count += 1
                except Exception as e:
                    print(f"[{ROLE}] - Error contacting node {node_ip}")

            if vote_count > (len(OTHER_DB_NODES) + 1) // 2:
                print(f"[{ROLE}] - Became leader for term {CURRENT_TERM}")
                ROLE = 'leader'
                LEADER_ID = 'self'
                start_heartbeats()
            else:
                print(f"[{ROLE}] - Did not receive enough votes, remaining as follower")
                ROLE = 'follower'
                LAST_HEARTBEAT = time.time()

def start_heartbeats():
    global LEADER_ID, ROLE

    while ROLE == 'leader':
        print(f"[{ROLE}] - Sending heartbeats to followers")
        success = True  # Variable para rastrear si todos los beats son exitosos
        for node_ip in OTHER_DB_NODES:
            try:
                channel = grpc.insecure_channel(f'{node_ip}:50051')
                stub = service_pb2_grpc.DatabaseServiceStub(channel)
                heartbeat_request = service_pb2.AppendEntriesRequest(leader_id='self')
                stub.AppendEntries(heartbeat_request)
                print(f"[{ROLE}] - Heartbeat successfully sent to node {node_ip}")
            except grpc.RpcError as e:
                status_code = e.code()
                success = False
                if status_code == grpc.StatusCode.UNAVAILABLE:
                    print(f"[{ROLE}] - Node {node_ip} is unreachable (Status: UNAVAILABLE)")
                elif status_code == grpc.StatusCode.CANCELLED:
                    print(f"[{ROLE}] - Heartbeat to node {node_ip} was cancelled (Status: CANCELLED)")
                else:
                    print(f"[{ROLE}] - Unexpected error sending heartbeat to node {node_ip}: {e}")
        
        if not success:
            print(f"[{ROLE}] - Lost contact with some nodes, switching to follower")
            ROLE = 'follower'
            LEADER_ID = None
            break

        time.sleep(1)

def serve():
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
