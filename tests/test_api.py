async def test_schedule(client):
    await client.post("/schedule")
