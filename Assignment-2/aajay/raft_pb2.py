# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: raft.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nraft.proto\x12\x04raft\"\x84\x01\n\x12RequestVoteRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x13\n\x0b\x63\x61ndidateId\x18\x02 \x01(\x05\x12\x14\n\x0clastLogIndex\x18\x03 \x01(\x05\x12\x13\n\x0blastLogTerm\x18\x04 \x01(\x05\x12 \n\x18knownLeaderLeaseDuration\x18\x05 \x01(\x05\"8\n\x13RequestVoteResponse\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x13\n\x0bvoteGranted\x18\x02 \x01(\x08\"\xb5\x01\n\x14\x41ppendEntriesRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x10\n\x08leaderId\x18\x02 \x01(\x05\x12\x14\n\x0cprevLogIndex\x18\x03 \x01(\x05\x12\x13\n\x0bprevLogTerm\x18\x04 \x01(\x05\x12\x1f\n\x07\x65ntries\x18\x05 \x03(\x0b\x32\x0e.raft.LogEntry\x12\x14\n\x0cleaderCommit\x18\x06 \x01(\x05\x12\x1b\n\x13leaderLeaseDuration\x18\x07 \x01(\x05\"6\n\x15\x41ppendEntriesResponse\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x0f\n\x07success\x18\x02 \x01(\x08\"4\n\x08LogEntry\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x0b\n\x03key\x18\x02 \x01(\t\x12\r\n\x05value\x18\x03 \x01(\t\"+\n\rKeyValMessage\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t\"!\n\x0eSuccessMessage\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x19\n\nKeyMessage\x12\x0b\n\x03key\x18\x01 \x01(\t\"3\n\x11SuccessValMessage\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\r\n\x05value\x18\x02 \x01(\t\"\x1f\n\rPeriodMessage\x12\x0e\n\x06period\x18\x01 \x01(\x05\"\x0e\n\x0c\x45mptyMessage\"0\n\rLeaderMessage\x12\x0e\n\x06leader\x18\x01 \x01(\x05\x12\x0f\n\x07\x61\x64\x64ress\x18\x02 \x01(\t2\x9d\x03\n\x04Raft\x12\x42\n\x0bRequestVote\x12\x18.raft.RequestVoteRequest\x1a\x19.raft.RequestVoteResponse\x12H\n\rAppendEntries\x12\x1a.raft.AppendEntriesRequest\x1a\x1b.raft.AppendEntriesResponse\x12\x32\n\x07Suspend\x12\x13.raft.PeriodMessage\x1a\x12.raft.EmptyMessage\x12\x34\n\tGetLeader\x12\x12.raft.EmptyMessage\x1a\x13.raft.LeaderMessage\x12\x33\n\x06SetVal\x12\x13.raft.KeyValMessage\x1a\x14.raft.SuccessMessage\x12\x33\n\x06GetVal\x12\x10.raft.KeyMessage\x1a\x17.raft.SuccessValMessage\x12\x33\n\tGetStatus\x12\x12.raft.EmptyMessage\x1a\x12.raft.EmptyMessageb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'raft_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_REQUESTVOTEREQUEST']._serialized_start=21
  _globals['_REQUESTVOTEREQUEST']._serialized_end=153
  _globals['_REQUESTVOTERESPONSE']._serialized_start=155
  _globals['_REQUESTVOTERESPONSE']._serialized_end=211
  _globals['_APPENDENTRIESREQUEST']._serialized_start=214
  _globals['_APPENDENTRIESREQUEST']._serialized_end=395
  _globals['_APPENDENTRIESRESPONSE']._serialized_start=397
  _globals['_APPENDENTRIESRESPONSE']._serialized_end=451
  _globals['_LOGENTRY']._serialized_start=453
  _globals['_LOGENTRY']._serialized_end=505
  _globals['_KEYVALMESSAGE']._serialized_start=507
  _globals['_KEYVALMESSAGE']._serialized_end=550
  _globals['_SUCCESSMESSAGE']._serialized_start=552
  _globals['_SUCCESSMESSAGE']._serialized_end=585
  _globals['_KEYMESSAGE']._serialized_start=587
  _globals['_KEYMESSAGE']._serialized_end=612
  _globals['_SUCCESSVALMESSAGE']._serialized_start=614
  _globals['_SUCCESSVALMESSAGE']._serialized_end=665
  _globals['_PERIODMESSAGE']._serialized_start=667
  _globals['_PERIODMESSAGE']._serialized_end=698
  _globals['_EMPTYMESSAGE']._serialized_start=700
  _globals['_EMPTYMESSAGE']._serialized_end=714
  _globals['_LEADERMESSAGE']._serialized_start=716
  _globals['_LEADERMESSAGE']._serialized_end=764
  _globals['_RAFT']._serialized_start=767
  _globals['_RAFT']._serialized_end=1180
# @@protoc_insertion_point(module_scope)
