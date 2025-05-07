openapi_codegen:
    datamodel-codegen --input openapi.json --openapi-scopes schemas --input-file-type openapi --output src/api/schemas/generated.py

[working-directory: 'src/grpc/generated']
grpc_codegen:
    python -m grpc_tools.protoc -I ../../../protos/ --python_out=. --pyi_out=. --grpc_python_out=. ../../../protos/schedule.proto
