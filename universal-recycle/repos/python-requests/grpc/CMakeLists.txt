cmake_minimum_required(VERSION 3.16)
project(python_requests_grpc)

find_package(Protobuf REQUIRED)
find_package(gRPC REQUIRED)

# Generate protobuf and gRPC files
protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS python_requests.proto)
protobuf_generate_grpc_cpp(GRPC_SRCS GRPC_HDRS python_requests.proto)

# Create gRPC server library
add_library(python_requests_grpc_server
    ${PROTO_SRCS}
    ${PROTO_HDRS}
    ${GRPC_SRCS}
    ${GRPC_HDRS}
    server.cpp
)

target_link_libraries(python_requests_grpc_server
    protobuf::libprotobuf
    gRPC::grpc++
)

# Create gRPC client library
add_library(python_requests_grpc_client
    ${PROTO_SRCS}
    ${PROTO_HDRS}
    ${GRPC_SRCS}
    ${GRPC_HDRS}
    client.cpp
)

target_link_libraries(python_requests_grpc_client
    protobuf::libprotobuf
    gRPC::grpc++
)
