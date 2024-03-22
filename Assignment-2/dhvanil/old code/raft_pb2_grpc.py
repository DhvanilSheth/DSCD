# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import raft_pb2 as raft__pb2


class RaftServiceStub(object):
    """The Raft service definition.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.RequestVote = channel.unary_unary(
                '/raft.RaftService/RequestVote',
                request_serializer=raft__pb2.RequestVoteMessage.SerializeToString,
                response_deserializer=raft__pb2.VoteResponseMessage.FromString,
                )
        self.AppendEntries = channel.unary_unary(
                '/raft.RaftService/AppendEntries',
                request_serializer=raft__pb2.AppendEntriesMessage.SerializeToString,
                response_deserializer=raft__pb2.AppendEntriesResponseMessage.FromString,
                )
        self.SetVal = channel.unary_unary(
                '/raft.RaftService/SetVal',
                request_serializer=raft__pb2.KeyValMessage.SerializeToString,
                response_deserializer=raft__pb2.OperationResponseMessage.FromString,
                )
        self.GetVal = channel.unary_unary(
                '/raft.RaftService/GetVal',
                request_serializer=raft__pb2.KeyMessage.SerializeToString,
                response_deserializer=raft__pb2.ValResponseMessage.FromString,
                )
        self.GetLeader = channel.unary_unary(
                '/raft.RaftService/GetLeader',
                request_serializer=raft__pb2.EmptyMessage.SerializeToString,
                response_deserializer=raft__pb2.LeaderMessage.FromString,
                )
        self.Suspend = channel.unary_unary(
                '/raft.RaftService/Suspend',
                request_serializer=raft__pb2.TimePeriodMessage.SerializeToString,
                response_deserializer=raft__pb2.EmptyMessage.FromString,
                )
        self.GetStatus = channel.unary_unary(
                '/raft.RaftService/GetStatus',
                request_serializer=raft__pb2.EmptyMessage.SerializeToString,
                response_deserializer=raft__pb2.EmptyMessage.FromString,
                )


class RaftServiceServicer(object):
    """The Raft service definition.
    """

    def RequestVote(self, request, context):
        """Sends a request vote message to other nodes.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AppendEntries(self, request, context):
        """Appends entries to the log, used for log replication and heartbeats.
        Modified to include lease interval duration.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetVal(self, request, context):
        """Client-facing RPCs for setting and getting key-value pairs.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetVal(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetLeader(self, request, context):
        """Additional RPCs for management and testing.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Suspend(self, request, context):
        """Suspend the node for a given time period in case of network partitioning. 
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetStatus(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_RaftServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'RequestVote': grpc.unary_unary_rpc_method_handler(
                    servicer.RequestVote,
                    request_deserializer=raft__pb2.RequestVoteMessage.FromString,
                    response_serializer=raft__pb2.VoteResponseMessage.SerializeToString,
            ),
            'AppendEntries': grpc.unary_unary_rpc_method_handler(
                    servicer.AppendEntries,
                    request_deserializer=raft__pb2.AppendEntriesMessage.FromString,
                    response_serializer=raft__pb2.AppendEntriesResponseMessage.SerializeToString,
            ),
            'SetVal': grpc.unary_unary_rpc_method_handler(
                    servicer.SetVal,
                    request_deserializer=raft__pb2.KeyValMessage.FromString,
                    response_serializer=raft__pb2.OperationResponseMessage.SerializeToString,
            ),
            'GetVal': grpc.unary_unary_rpc_method_handler(
                    servicer.GetVal,
                    request_deserializer=raft__pb2.KeyMessage.FromString,
                    response_serializer=raft__pb2.ValResponseMessage.SerializeToString,
            ),
            'GetLeader': grpc.unary_unary_rpc_method_handler(
                    servicer.GetLeader,
                    request_deserializer=raft__pb2.EmptyMessage.FromString,
                    response_serializer=raft__pb2.LeaderMessage.SerializeToString,
            ),
            'Suspend': grpc.unary_unary_rpc_method_handler(
                    servicer.Suspend,
                    request_deserializer=raft__pb2.TimePeriodMessage.FromString,
                    response_serializer=raft__pb2.EmptyMessage.SerializeToString,
            ),
            'GetStatus': grpc.unary_unary_rpc_method_handler(
                    servicer.GetStatus,
                    request_deserializer=raft__pb2.EmptyMessage.FromString,
                    response_serializer=raft__pb2.EmptyMessage.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'raft.RaftService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class RaftService(object):
    """The Raft service definition.
    """

    @staticmethod
    def RequestVote(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/raft.RaftService/RequestVote',
            raft__pb2.RequestVoteMessage.SerializeToString,
            raft__pb2.VoteResponseMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AppendEntries(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/raft.RaftService/AppendEntries',
            raft__pb2.AppendEntriesMessage.SerializeToString,
            raft__pb2.AppendEntriesResponseMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SetVal(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/raft.RaftService/SetVal',
            raft__pb2.KeyValMessage.SerializeToString,
            raft__pb2.OperationResponseMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetVal(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/raft.RaftService/GetVal',
            raft__pb2.KeyMessage.SerializeToString,
            raft__pb2.ValResponseMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetLeader(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/raft.RaftService/GetLeader',
            raft__pb2.EmptyMessage.SerializeToString,
            raft__pb2.LeaderMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Suspend(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/raft.RaftService/Suspend',
            raft__pb2.TimePeriodMessage.SerializeToString,
            raft__pb2.EmptyMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetStatus(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/raft.RaftService/GetStatus',
            raft__pb2.EmptyMessage.SerializeToString,
            raft__pb2.EmptyMessage.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
