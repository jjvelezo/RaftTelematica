import csv
import service_pb2
import service_pb2_grpc
import grpc
from concurrent import futures
import os
import time
import random
from threading import Thread

# Archivo CSV para simular la base de datos
DB_FILE = 'database.csv'

# Variables globales de estado
ROLE = 'follower'
CURRENT_TERM = 0
VOTED_FOR = None
LEADER_ID = None
TIMEOUT = random.uniform(0.15, 0.3)  # Timeout en segundos

# Lista de nodos DB para conexión (debe ser ajustada con las IPs de cada instancia)
OTHER_DB_NODES = ['10.0.2.162', '10.0.2.234']
#OTHER_DB_NODES = ['10.0.2.250', '10.0.2.234']
#OTHER_DB_NODES = ['10.0.2.250', '10.0.2.162']

class DatabaseService(service_pb2_grpc.DatabaseServiceServicer):
    def ReadData(self, request, context):
        print(f"[{ROLE}] - Read operation requested")
        with open(DB_FILE, mode='r') as csv_file:
            reader = csv.reader(csv_file)
            rows = [','.join(row) for row in reader]
            result = "\n".join(rows)
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
            return service_pb2.WriteResponse(status="SUCCESS")
        else:
            return service_pb2.WriteResponse(status="ERROR: Cannot write to follower")

    def RequestVote(self, request, context):
        global CURRENT_TERM, VOTED_FOR, ROLE
        term = request.term
        candidate_id = request.candidate_id

        if term > CURRENT_TERM:
            CURRENT_TERM = term
            VOTED_FOR = candidate_id
            print(f"[{ROLE}] - Voted for {candidate_id} in term {term}")
            return service_pb2.VoteResponse(granted=True)
        elif term == CURRENT_TERM and (VOTED_FOR is None or VOTED_FOR == candidate_id):
            VOTED_FOR = candidate_id
            return service_pb2.VoteResponse(granted=True)
        
        return service_pb2.VoteResponse(granted=False)

    def AppendEntries(self, request, context):
        global CURRENT_TERM, LEADER_ID, ROLE, TIMEOUT
        if request.term >= CURRENT_TERM:
            CURRENT_TERM = request.term
            LEADER_ID = request.leader_id
            ROLE = 'follower'
            TIMEOUT = random.uniform(0.15, 0.3)
            return service_pb2.AppendEntriesResponse(success=True)
        return service_pb2.AppendEntriesResponse(success=False)

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
                    print(f"[{ROLE}] - Error contacting node {node_ip}: {e}")

            if vote_count > len(OTHER_DB_NODES) // 2:
                ROLE = 'leader'
                LEADER_ID = 'self'
                start_heartbeats()
            else:
                ROLE = 'follower'

def start_heartbeats():
    global ROLE, LEADER_ID, TIMEOUT
    while ROLE == 'leader':
        for node_ip in OTHER_DB_NODES:
            try:
                channel = grpc.insecure_channel(f'{node_ip}:50051')
                stub = service_pb2_grpc.DatabaseServiceStub(channel)
                stub.AppendEntries(service_pb2.AppendEntriesRequest(leader_id='self', term=CURRENT_TERM))
            except Exception as e:
                print(f"[{ROLE}] - Error sending heartbeat to node {node_ip}: {e}")
        time.sleep(1)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_DatabaseServiceServicer_to_server(DatabaseService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    Thread(target=start_election).start()
    server.wait_for_termination()

if __name__ == '__main__':
    ROLE = 'follower'
    CURRENT_TERM = 0
    VOTED_FOR = None
    LEADER_ID = None
    serve()