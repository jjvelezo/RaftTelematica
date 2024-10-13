# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: service.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'service.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rservice.proto\x12\x08\x64\x61tabase\"\x1c\n\x0bReadRequest\x12\r\n\x05query\x18\x01 \x01(\t\"\x1e\n\x0cReadResponse\x12\x0e\n\x06result\x18\x01 \x01(\t\"\x1c\n\x0cWriteRequest\x12\x0c\n\x04\x64\x61ta\x18\x01 \x01(\t\"\x1f\n\rWriteResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\"1\n\x0bVoteRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x14\n\x0c\x63\x61ndidate_id\x18\x02 \x01(\t\"\x1f\n\x0cVoteResponse\x12\x0f\n\x07granted\x18\x01 \x01(\x08\")\n\x14\x41ppendEntriesRequest\x12\x11\n\tleader_id\x18\x01 \x01(\t\"(\n\x15\x41ppendEntriesResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x10\n\x0e\x44\x65gradeRequest\"!\n\x0f\x44\x65gradeResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\"\x1e\n\x0bPingRequest\x12\x0f\n\x07message\x18\x01 \x01(\t\"A\n\x0cPingResponse\x12\x0c\n\x04role\x18\x01 \x01(\t\x12\r\n\x05state\x18\x02 \x01(\t\x12\x14\n\x0c\x61\x63tive_nodes\x18\x03 \x03(\t\"%\n\rUpdateRequest\x12\x14\n\x0c\x61\x63tive_nodes\x18\x01 \x03(\t\" \n\x0eUpdateResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\"1\n\x1aReplicateToFollowerRequest\x12\x13\n\x0b\x66ollower_ip\x18\x01 \x01(\t\"#\n\x11ReplicateResponse\x12\x0e\n\x06status\x18\x01 \x01(\t2\xff\x04\n\x0f\x44\x61tabaseService\x12\x39\n\x08ReadData\x12\x15.database.ReadRequest\x1a\x16.database.ReadResponse\x12<\n\tWriteData\x12\x16.database.WriteRequest\x1a\x17.database.WriteResponse\x12<\n\x0bRequestVote\x12\x15.database.VoteRequest\x1a\x16.database.VoteResponse\x12P\n\rAppendEntries\x12\x1e.database.AppendEntriesRequest\x1a\x1f.database.AppendEntriesResponse\x12\x35\n\x04Ping\x12\x15.database.PingRequest\x1a\x16.database.PingResponse\x12\x46\n\x11UpdateActiveNodes\x12\x17.database.UpdateRequest\x1a\x18.database.UpdateResponse\x12H\n\x11\x44\x65gradeToFollower\x12\x18.database.DegradeRequest\x1a\x19.database.DegradeResponse\x12@\n\rReplicateData\x12\x16.database.WriteRequest\x1a\x17.database.WriteResponse\x12X\n\x13ReplicateToFollower\x12$.database.ReplicateToFollowerRequest\x1a\x1b.database.ReplicateResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'service_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_READREQUEST']._serialized_start=27
  _globals['_READREQUEST']._serialized_end=55
  _globals['_READRESPONSE']._serialized_start=57
  _globals['_READRESPONSE']._serialized_end=87
  _globals['_WRITEREQUEST']._serialized_start=89
  _globals['_WRITEREQUEST']._serialized_end=117
  _globals['_WRITERESPONSE']._serialized_start=119
  _globals['_WRITERESPONSE']._serialized_end=150
  _globals['_VOTEREQUEST']._serialized_start=152
  _globals['_VOTEREQUEST']._serialized_end=201
  _globals['_VOTERESPONSE']._serialized_start=203
  _globals['_VOTERESPONSE']._serialized_end=234
  _globals['_APPENDENTRIESREQUEST']._serialized_start=236
  _globals['_APPENDENTRIESREQUEST']._serialized_end=277
  _globals['_APPENDENTRIESRESPONSE']._serialized_start=279
  _globals['_APPENDENTRIESRESPONSE']._serialized_end=319
  _globals['_DEGRADEREQUEST']._serialized_start=321
  _globals['_DEGRADEREQUEST']._serialized_end=337
  _globals['_DEGRADERESPONSE']._serialized_start=339
  _globals['_DEGRADERESPONSE']._serialized_end=372
  _globals['_PINGREQUEST']._serialized_start=374
  _globals['_PINGREQUEST']._serialized_end=404
  _globals['_PINGRESPONSE']._serialized_start=406
  _globals['_PINGRESPONSE']._serialized_end=471
  _globals['_UPDATEREQUEST']._serialized_start=473
  _globals['_UPDATEREQUEST']._serialized_end=510
  _globals['_UPDATERESPONSE']._serialized_start=512
  _globals['_UPDATERESPONSE']._serialized_end=544
  _globals['_REPLICATETOFOLLOWERREQUEST']._serialized_start=546
  _globals['_REPLICATETOFOLLOWERREQUEST']._serialized_end=595
  _globals['_REPLICATERESPONSE']._serialized_start=597
  _globals['_REPLICATERESPONSE']._serialized_end=632
  _globals['_DATABASESERVICE']._serialized_start=635
  _globals['_DATABASESERVICE']._serialized_end=1274
# @@protoc_insertion_point(module_scope)
