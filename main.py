import subprocess
from src.config import settings
from fastapi import FastAPI, HTTPException
from src.db import db, redis_client
from src.api import auth, parking, user

app = FastAPI()
app.include_router(router=auth.router, prefix="/auth", tags=["Auth"])
app.include_router(router=user.router, prefix="/user", tags=["user"])
app.include_router(router=parking.router, prefix="/parking", tags=["Parking"])


@app.get("/healthcheck")
async def healthcheck():
    """
    Health check endpoint to validate application health.
    Checks connectivity to MongoDB and Redis.
    """
    # Check MongoDB connection
    try:
        mongo_response = await db.command("ping")
        if mongo_response.get("ok") != 1:
            raise Exception("MongoDB ping failed")
    except Exception as e:
        # Log the error if logging is set up
        # logger.error(f"MongoDB healthcheck failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"MongoDB health check failed: {str(e)}"
        )

    # Check Redis connection
    try:
        redis_response = await redis_client.ping()
        if not redis_response:
            raise Exception("Redis ping failed")
    except Exception as e:
        # Log the error if logging is set up
        # logger.error(f"Redis healthcheck failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Redis health check failed: {str(e)}"
        )

    return {"status": "healthy"}


def main():

    command = [
        "gunicorn",
        "-w",
        str(settings.worker_count),
        "-k",
        "uvicorn.workers.UvicornWorker",
        "--bind",
        f"{settings.webserver_host}:{settings.webserver_port}",
        "main:app",
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:

        print(f"An error occurred while running Gunicorn: {e}")


if __name__ == "__main__":
    main()
