import csv
import service_pb2
import service_pb2_grpc
import grpc
from concurrent import futures
import os
import time
import random
from threading import Thread
import socket

FIRST_RUN = True
DB_FILE = 'database.csv'


if os.path.exists(DB_FILE):
    print(f"El archivo '{DB_FILE}' ya existe. Se eliminará para crear uno nuevo.")
    os.remove(DB_FILE)
else:
    print(f"El archivo '{DB_FILE}' no existe. Creando uno nuevo.")

with open(DB_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['id', 'name', 'email'])

print(f"Archivo '{DB_FILE}' creado con la estructura: id, name, email.")

def get_private_ip():
    return socket.gethostbyname(socket.gethostname())

ROLE = 'follower'
CURRENT_TERM = 0
VOTED_FOR = None
LEADER_ID = None
TIMEOUT = random.uniform(3.0, 5.0) if FIRST_RUN else random.uniform(1.5, 3.0)
LAST_HEARTBEAT = time.time()

SERVER_IP = get_private_ip()

ALL_DB_NODES = ['10.0.2.250', '10.0.2.162', '10.0.2.234']
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

            # Verificar si el ID ya existe
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
            print(f"[{ROLE}] - Error al contactar candidato {candidate_id}: {e.code()}")
            return service_pb2.VoteResponse(granted=False)

    def AppendEntries(self, request, context):
        global ROLE, LEADER_ID, TIMEOUT, LAST_HEARTBEAT, FIRST_RUN
        LEADER_ID = request.leader_id
        LAST_HEARTBEAT = time.time()

        if FIRST_RUN:
            FIRST_RUN = False
            TIMEOUT = random.uniform(1.5, 3.0)
            request_database_sync()
        
        print(f"[{ROLE}] - Received heartbeat from leader {LEADER_ID}")
        return service_pb2.AppendEntriesResponse(success=True)

    def Ping(self, request, context):
        global ROLE
        return service_pb2.PingResponse(role=ROLE, state="active")
    
    def SyncDatabase(self, request, context):
        global ROLE
        if ROLE == 'leader':
            print(f"[{ROLE}] - Sync request received from follower")
            try:
                with open(DB_FILE, mode='r') as csv_file:
                    data = csv_file.read()  # Leer todo el archivo CSV
                return service_pb2.SyncResponse(database=data)
            except Exception as e:
                print(f"[{ROLE}] - Error sending database: {e}")
                return service_pb2.SyncResponse(database="")
        else:
            print(f"[{ROLE}] - Cannot sync database, not the leader.")
            return service_pb2.SyncResponse(database="")
        

    def request_database_sync():
        global LEADER_ID, ROLE
        if ROLE == 'follower' and LEADER_ID:  # Solo si soy un follower y hay líder
            print(f"[{ROLE}] - Requesting database sync from leader {LEADER_ID}")
            try:
                channel = grpc.insecure_channel(f'{LEADER_ID}:50051')
                stub = service_pb2_grpc.DatabaseServiceStub(channel)
                sync_request = service_pb2.SyncRequest()
                response = stub.SyncDatabase(sync_request)
                if response.database:
                    with open(DB_FILE, mode='w') as csv_file:
                        csv_file.write(response.database)
                    print(f"[{ROLE}] - Database successfully synced from leader.")
                else:
                    print(f"[{ROLE}] - Failed to sync database from leader.")
            except Exception as e:
                print(f"[{ROLE}] - Error syncing database from leader: {e}")


    def RequestDatabase(self, request, context):
        """Método para que el líder envíe la base de datos completa"""
        if ROLE == 'leader':
            print(f"[{ROLE}] - Request for database received, sending database.")
            with open(DB_FILE, mode='r') as csv_file:
                reader = csv.reader(csv_file)
                rows = [','.join(row) for row in reader]
                database_data = "\n".join(rows)
            return service_pb2.DatabaseResponse(database=database_data)
        else:
            return service_pb2.DatabaseResponse(database="ERROR: Not a leader")

    def UpdateDatabase(self, request, context):
        """Método para actualizar la base de datos local con datos del líder"""
        print(f"[{ROLE}] - Updating local database with received data.")
        try:
            with open(DB_FILE, mode='w') as csv_file:
                csv_file.write(request.database)
            print(f"[{ROLE}] - Local database updated successfully.")
            return service_pb2.UpdateResponse(status="SUCCESS")
        except Exception as e:
            print(f"[{ROLE}] - Error updating local database: {e}")
            return service_pb2.UpdateResponse(status=f"ERROR: {e}")

def request_database_from_leader():
    """Función para que un follower solicite la base de datos al líder al conectarse."""
    if ROLE == 'follower' and LEADER_ID:
        try:
            channel = grpc.insecure_channel(f'{LEADER_ID}:50051')
            stub = service_pb2_grpc.DatabaseServiceStub(channel)
            response = stub.RequestDatabase(service_pb2.DatabaseRequest())
            if response.database != "ERROR: Not a leader":
                print(f"[{ROLE}] - Database received from leader, updating local database.")
                # Actualizar la base de datos local
                stub.UpdateDatabase(service_pb2.DatabaseUpdateRequest(database=response.database))
            else:
                print(f"[{ROLE}] - Failed to retrieve database from leader.")
        except grpc.RpcError as e:
            print(f"[{ROLE}] - Error requesting database from leader: {e}")

# Después de cada conexión a un líder, solicitar la base de datos
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
                # Solicitar la base de datos al líder cuando nos convertimos en follower
                request_database_from_leader()



#Degradar un líder a follower

    def DegradeToFollower(self, request, context):

        global ROLE
        print(f"[{ROLE}] - Degrading to follower by request.")
        ROLE = 'follower'
        return service_pb2.DegradeResponse(status="SUCCESS")

    def UpdateActiveNodes(self, request, context):
        global OTHER_DB_NODES
        active_nodes = list(request.active_nodes)
        OTHER_DB_NODES = [ip for ip in active_nodes if ip != SERVER_IP]
        print(f"[{ROLE}] - Updated active node list: {OTHER_DB_NODES}")
        return service_pb2.UpdateResponse(status="SUCCESS")

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
        for node_ip in OTHER_DB_NODES:
            try:
                channel = grpc.insecure_channel(f'{node_ip}:50051')
                stub = service_pb2_grpc.DatabaseServiceStub(channel)
                heartbeat_request = service_pb2.AppendEntriesRequest(leader_id='self')
                stub.AppendEntries(heartbeat_request)
                print(f"[{ROLE}] - Heartbeat successfully sent to node {node_ip}")
            except grpc.RpcError as e:
                print(f"[{ROLE}] - Error sending heartbeat to node {node_ip}: {e}")
        
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
