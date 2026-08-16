import os
from app import application

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting WSGI server on port {port}...")
    server = make_server('0.0.0.0', port, application)
    server.serve_forever()
