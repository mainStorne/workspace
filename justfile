openapi_codegen:
    uv run datamodel-codegen --input openapi.yaml --output api/modules/users/user_scheme.py

grpc_codegen:
    cd api/gRPC/generated
    python -m grpc_tools.protoc -I ../../../protos/ --python_out=. --pyi_out=. --grpc_python_out=. ../../../protos/schedule.proto
