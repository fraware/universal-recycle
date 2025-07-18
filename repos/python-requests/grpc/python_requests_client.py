# Auto-generated gRPC client for python_requests
import grpc
import python_requests_pb2
import python_requests_pb2_grpc

class python_requestsClient:
    def __init__(self, host='localhost', port=50051):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = python_requests_pb2_grpc.python_requestsServiceStub(self.channel)
    
    def get_info(self, query: str) -> str:
        request = python_requests_pb2.GetInfoRequest(query=query)
        response = self.stub.GetInfo(request)
        return response.info if response.success else "Error"
    
    def close(self):
        self.channel.close()
