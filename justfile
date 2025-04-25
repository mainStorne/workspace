openapi_codegen:
    uv run datamodel-codegen --input openapi.yaml --output api/modules/users/user_scheme.py

grpc_codegen:
    python -m grpc_tools.protoc -I protos --python_out=api/grpc/generated --pyi_out=api/grpc/generated --grpc_python_out=api/grpc/generated protos/schedule.proto
