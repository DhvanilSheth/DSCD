# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: kmeans.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0ckmeans.proto\x12\x06kmeans\"X\n\rMapperRequest\x12\x11\n\tmapper_id\x18\x01 \x01(\x05\x12\x12\n\ninput_data\x18\x02 \x01(\t\x12 \n\tcentroids\x18\x03 \x03(\x0b\x32\r.kmeans.Point\"E\n\x0eMapperResponse\x12\x11\n\tmapper_id\x18\x01 \x01(\x05\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\x0f\n\x07message\x18\x03 \x01(\t\"2\n\x0eReducerRequest\x12\x12\n\nreducer_id\x18\x01 \x01(\x05\x12\x0c\n\x04keys\x18\x02 \x03(\x05\"G\n\x0fReducerResponse\x12\x12\n\nreducer_id\x18\x01 \x01(\x05\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\x0f\n\x07message\x18\x03 \x01(\t\"(\n\x05Point\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x13\n\x0b\x63oordinates\x18\x02 \x03(\x02\x32\x8c\x01\n\rKMeansService\x12:\n\x07MapTask\x12\x15.kmeans.MapperRequest\x1a\x16.kmeans.MapperResponse\"\x00\x12?\n\nReduceTask\x12\x16.kmeans.ReducerRequest\x1a\x17.kmeans.ReducerResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'kmeans_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_MAPPERREQUEST']._serialized_start=24
  _globals['_MAPPERREQUEST']._serialized_end=112
  _globals['_MAPPERRESPONSE']._serialized_start=114
  _globals['_MAPPERRESPONSE']._serialized_end=183
  _globals['_REDUCERREQUEST']._serialized_start=185
  _globals['_REDUCERREQUEST']._serialized_end=235
  _globals['_REDUCERRESPONSE']._serialized_start=237
  _globals['_REDUCERRESPONSE']._serialized_end=308
  _globals['_POINT']._serialized_start=310
  _globals['_POINT']._serialized_end=350
  _globals['_KMEANSSERVICE']._serialized_start=353
  _globals['_KMEANSSERVICE']._serialized_end=493
# @@protoc_insertion_point(module_scope)
