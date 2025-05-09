import uvicorn

from aibolit_app.main import make_app

if __name__ == '__main__':
    app = make_app()
    uvicorn.run(app)
