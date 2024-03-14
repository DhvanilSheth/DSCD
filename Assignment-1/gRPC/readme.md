Steps to run the code:
    0. source myenv/bin/activate in google cloud instance
    1. Start the market.py file: python market.py
    2. Start the seller clients by running the seller.py file
        a. python seller.py -[market address to connect to (default: localhost:50051)] -[notification port of this seller client (default: 50052)]
        EG: python seller.py localhost:50051 50052
    3. Start the buyer clients by running the buyer.py file
        a. python buyer.py -[market address to connect to (default: localhost:50051)] -[notification port of this buyer client (default: 50053)]
        EG: python buyer.py localhost:50051 50052

Points to Note:
    1. The market, seller and buyer clients can be run on different machines by providing the relevant IP addresses.
    2. Multiple buyer and seller clients can be started by running the buyer.py and seller.py files multiple times.
    3. The buyer can connect only after the market has been initiated.
    4. If required, you can regenerate the proto file by running the command
       (python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. market.proto)