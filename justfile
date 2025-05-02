openapi_codegen:
    uv run datamodel-codegen --input openapi.yaml --output src/api/schemas/generated.py

[working-directory: 'src/grpc/generated']
grpc_codegen:
    python -m grpc_tools.protoc -I ../../../protos/ --python_out=. --pyi_out=. --grpc_python_out=. ../../../protos/schedule.proto
