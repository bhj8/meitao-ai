import time
from fastapi import Depends, HTTPException
from app.security.auth import verify_token

# A dictionary to store the last request time for each user
user_last_request_time = {}


async def rate_limiter(token_data: dict = Depends(verify_token)):
    global user_last_request_time
    user_id = int(token_data["sub"])

    current_time = time.time()
    allowed_request_interval = 2  # The minimum time between requests in seconds

    if user_id in user_last_request_time:
        time_since_last_request = current_time - user_last_request_time[user_id]

        if time_since_last_request < allowed_request_interval:
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Please try again after {allowed_request_interval - time_since_last_request:.2f} seconds.",
            )

    user_last_request_time[user_id] = current_time
