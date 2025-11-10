@pytest.mark.asyncio
async def test_order_happy_path(async_client, db_session):
    # create order
    r = await async_client.post("/orders", json={...})
    assert r.status_code == 201
    order = r.json()

    # assign slot
    r = await async_client.patch(f"/orders/{order['id']}/slot", json={"slot_id": slot_id})
    assert r.status_code == 200

    # simulate webhook
    await simulate_payment_webhook(order["payment_id"])

    db_order = await get_order(db_session, order["id"])
    assert db_order.status == "paid"

@pytest.mark.asyncio
async def test_slot_conflict(async_client):
    order1 = await create_order(async_client)
    order2 = await create_order(async_client)

    r1, r2 = await asyncio.gather(
        async_client.patch(f"/orders/{order1['id']}/slot", json={"slot_id": SLOT}),
        async_client.patch(f"/orders/{order2['id']}/slot", json={"slot_id": SLOT}),
    )

    assert {r1.status_code, r2.status_code} == {200, 409}
