# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: shopping_platform.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x17shopping_platform.proto\x12\x10shoppingplatform\"\xac\x01\n\x04Item\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x0c\n\x04name\x18\x02 \x01(\t\x12,\n\x08\x63\x61tegory\x18\x03 \x01(\x0e\x32\x1a.shoppingplatform.Category\x12\x10\n\x08quantity\x18\x04 \x01(\x05\x12\x13\n\x0b\x64\x65scription\x18\x05 \x01(\t\x12\x16\n\x0eseller_address\x18\x06 \x01(\t\x12\r\n\x05price\x18\x07 \x01(\x01\x12\x0e\n\x06rating\x18\x08 \x01(\x01\"=\n\x15RegisterSellerRequest\x12\x16\n\x0eseller_address\x18\x01 \x01(\t\x12\x0c\n\x04uuid\x18\x02 \x01(\t\"\xad\x01\n\x1aSellerItemOperationRequest\x12\x0c\n\x04uuid\x18\x01 \x01(\t\x12\x0f\n\x07item_id\x18\x02 \x01(\x05\x12\x0c\n\x04name\x18\x03 \x01(\t\x12,\n\x08\x63\x61tegory\x18\x04 \x01(\x0e\x32\x1a.shoppingplatform.Category\x12\x10\n\x08quantity\x18\x05 \x01(\x05\x12\x13\n\x0b\x64\x65scription\x18\x06 \x01(\t\x12\r\n\x05price\x18\x07 \x01(\x01\";\n\x13\x44isplayItemsRequest\x12\x16\n\x0eseller_address\x18\x01 \x01(\t\x12\x0c\n\x04uuid\x18\x02 \x01(\t\"O\n\x11SearchItemRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12,\n\x08\x63\x61tegory\x18\x02 \x01(\x0e\x32\x1a.shoppingplatform.Category\"J\n\x0e\x42uyItemRequest\x12\x0f\n\x07item_id\x18\x01 \x01(\x05\x12\x10\n\x08quantity\x18\x02 \x01(\x05\x12\x15\n\rbuyer_address\x18\x03 \x01(\t\"9\n\x0fWishlistRequest\x12\x0f\n\x07item_id\x18\x01 \x01(\x05\x12\x15\n\rbuyer_address\x18\x02 \x01(\t\"I\n\x0fRateItemRequest\x12\x0f\n\x07item_id\x18\x01 \x01(\x05\x12\x0e\n\x06rating\x18\x02 \x01(\x05\x12\x15\n\rbuyer_address\x18\x03 \x01(\t\"\x1b\n\x08Response\x12\x0f\n\x07message\x18\x01 \x01(\t\";\n\x13NotifyClientRequest\x12$\n\x04item\x18\x01 \x01(\x0b\x32\x16.shoppingplatform.Item*=\n\x08\x43\x61tegory\x12\x0f\n\x0b\x45LECTRONICS\x10\x00\x12\x0b\n\x07\x46\x41SHION\x10\x01\x12\n\n\x06OTHERS\x10\x02\x12\x07\n\x03\x41NY\x10\x03\x32\xc7\x06\n\rMarketService\x12U\n\x0eRegisterSeller\x12\'.shoppingplatform.RegisterSellerRequest\x1a\x1a.shoppingplatform.Response\x12T\n\x08SellItem\x12,.shoppingplatform.SellerItemOperationRequest\x1a\x1a.shoppingplatform.Response\x12V\n\nUpdateItem\x12,.shoppingplatform.SellerItemOperationRequest\x1a\x1a.shoppingplatform.Response\x12V\n\nDeleteItem\x12,.shoppingplatform.SellerItemOperationRequest\x1a\x1a.shoppingplatform.Response\x12U\n\x12\x44isplaySellerItems\x12%.shoppingplatform.DisplayItemsRequest\x1a\x16.shoppingplatform.Item0\x01\x12K\n\nSearchItem\x12#.shoppingplatform.SearchItemRequest\x1a\x16.shoppingplatform.Item0\x01\x12G\n\x07\x42uyItem\x12 .shoppingplatform.BuyItemRequest\x1a\x1a.shoppingplatform.Response\x12N\n\rAddToWishlist\x12!.shoppingplatform.WishlistRequest\x1a\x1a.shoppingplatform.Response\x12I\n\x08RateItem\x12!.shoppingplatform.RateItemRequest\x1a\x1a.shoppingplatform.Response\x12Q\n\x0cNotifyClient\x12%.shoppingplatform.NotifyClientRequest\x1a\x1a.shoppingplatform.Responseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'shopping_platform_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_CATEGORY']._serialized_start=901
  _globals['_CATEGORY']._serialized_end=962
  _globals['_ITEM']._serialized_start=46
  _globals['_ITEM']._serialized_end=218
  _globals['_REGISTERSELLERREQUEST']._serialized_start=220
  _globals['_REGISTERSELLERREQUEST']._serialized_end=281
  _globals['_SELLERITEMOPERATIONREQUEST']._serialized_start=284
  _globals['_SELLERITEMOPERATIONREQUEST']._serialized_end=457
  _globals['_DISPLAYITEMSREQUEST']._serialized_start=459
  _globals['_DISPLAYITEMSREQUEST']._serialized_end=518
  _globals['_SEARCHITEMREQUEST']._serialized_start=520
  _globals['_SEARCHITEMREQUEST']._serialized_end=599
  _globals['_BUYITEMREQUEST']._serialized_start=601
  _globals['_BUYITEMREQUEST']._serialized_end=675
  _globals['_WISHLISTREQUEST']._serialized_start=677
  _globals['_WISHLISTREQUEST']._serialized_end=734
  _globals['_RATEITEMREQUEST']._serialized_start=736
  _globals['_RATEITEMREQUEST']._serialized_end=809
  _globals['_RESPONSE']._serialized_start=811
  _globals['_RESPONSE']._serialized_end=838
  _globals['_NOTIFYCLIENTREQUEST']._serialized_start=840
  _globals['_NOTIFYCLIENTREQUEST']._serialized_end=899
  _globals['_MARKETSERVICE']._serialized_start=965
  _globals['_MARKETSERVICE']._serialized_end=1804
# @@protoc_insertion_point(module_scope)
