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




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rservice.proto\x12\x08\x64\x61tabase\"\x1c\n\x0bReadRequest\x12\r\n\x05query\x18\x01 \x01(\t\"\x1e\n\x0cReadResponse\x12\x0e\n\x06result\x18\x01 \x01(\t\"\x1c\n\x0cWriteRequest\x12\x0c\n\x04\x64\x61ta\x18\x01 \x01(\t\"\x1f\n\rWriteResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\"1\n\x0bVoteRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x14\n\x0c\x63\x61ndidate_id\x18\x02 \x01(\t\"\x1f\n\x0cVoteResponse\x12\x0f\n\x07granted\x18\x01 \x01(\x08\":\n\x14\x41ppendEntriesRequest\x12\x11\n\tleader_id\x18\x01 \x01(\t\x12\x0f\n\x07\x65ntries\x18\x02 \x03(\t\";\n\x15\x41ppendEntriesResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x11\n\tleader_id\x18\x02 \x01(\t\"\x1e\n\x0bPingRequest\x12\x0f\n\x07message\x18\x01 \x01(\t\"A\n\x0cPingResponse\x12\x0c\n\x04role\x18\x01 \x01(\t\x12\r\n\x05state\x18\x02 \x01(\t\x12\x14\n\x0c\x61\x63tive_nodes\x18\x03 \x03(\t\"%\n\rUpdateRequest\x12\x14\n\x0c\x61\x63tive_nodes\x18\x01 \x03(\t\" \n\x0eUpdateResponse\x12\x0e\n\x06status\x18\x01 \x01(\t2\xdb\x03\n\x0f\x44\x61tabaseService\x12\x39\n\x08ReadData\x12\x15.database.ReadRequest\x1a\x16.database.ReadResponse\x12<\n\tWriteData\x12\x16.database.WriteRequest\x1a\x17.database.WriteResponse\x12<\n\x0bRequestVote\x12\x15.database.VoteRequest\x1a\x16.database.VoteResponse\x12P\n\rAppendEntries\x12\x1e.database.AppendEntriesRequest\x1a\x1f.database.AppendEntriesResponse\x12\x35\n\x04Ping\x12\x15.database.PingRequest\x1a\x16.database.PingResponse\x12\x46\n\x11UpdateActiveNodes\x12\x17.database.UpdateRequest\x1a\x18.database.UpdateResponse\x12@\n\rReplicateData\x12\x16.database.WriteRequest\x1a\x17.database.WriteResponseb\x06proto3')

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
  _globals['_APPENDENTRIESREQUEST']._serialized_end=294
  _globals['_APPENDENTRIESRESPONSE']._serialized_start=296
  _globals['_APPENDENTRIESRESPONSE']._serialized_end=355
  _globals['_PINGREQUEST']._serialized_start=357
  _globals['_PINGREQUEST']._serialized_end=387
  _globals['_PINGRESPONSE']._serialized_start=389
  _globals['_PINGRESPONSE']._serialized_end=454
  _globals['_UPDATEREQUEST']._serialized_start=456
  _globals['_UPDATEREQUEST']._serialized_end=493
  _globals['_UPDATERESPONSE']._serialized_start=495
  _globals['_UPDATERESPONSE']._serialized_end=527
  _globals['_DATABASESERVICE']._serialized_start=530
  _globals['_DATABASESERVICE']._serialized_end=1005
# @@protoc_insertion_point(module_scope)
