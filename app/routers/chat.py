from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, HTTPException
from jose import JWTError, jwt

from ..websocket.manager import manager
from ..database import SessionLocal
from .. import models
from ..config import settings
from ..services import message_service

router = APIRouter(tags=["Chat"])


def get_user_id_from_ws_token(token: str | None) -> int |None:
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        return int(payload.get("user_id"))

    except (JWTError, TypeError, ValueError):
        return None


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: str | None = None,
):

    authenticated_user_id = get_user_id_from_ws_token(token)

    if authenticated_user_id != user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user_id, websocket)
    await manager.broadcast_online_status(user_id, True)

    try:

        while True:

            data = await websocket.receive_json()

            message_type = data.get("type")

            # ==========================================
            # Typing
            # ==========================================

            if message_type == "typing":

                receiver_id = data.get("receiver_id")

                if receiver_id:
                    await manager.send_personal_message(
                        receiver_id,
                        {
                            "type": "typing",
                            "user_id": user_id,
                        },
                    )

                continue

            # ==========================================
            # Stop Typing
            # ==========================================

            if message_type == "stop_typing":

                receiver_id = data.get("receiver_id")

                if receiver_id:
                    await manager.send_personal_message(
                        receiver_id,
                        {
                            "type": "stop_typing",
                            "user_id": user_id,
                        },
                    )

                continue

            # ==========================================
            # Seen
            # ==========================================

            if message_type == "seen":

                db = SessionLocal()
                try:
                    message = message_service.mark_message_seen(
                        message_id=data.get("message_id"),
                        current_user_id=user_id,
                        db=db,
                    )

                    seen_payload = {
                        "type": "seen",
                        "message_id": message.id,
                    }

                    sender_id = message.sender_id

                except HTTPException as e:

                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": e.detail,
                        }
                    )

                    continue

                finally:
                    db.close()

                await manager.send_personal_message(
                    sender_id,
                    seen_payload,
                )

                continue

            # ==========================================
            # Normal Message
            # ==========================================

            if message_type != "message":
                continue

            receiver_id = data.get("receiver_id")

            if receiver_id is None:

                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "receiver_id is required",
                    }
                )

                continue

            db = SessionLocal()
            try:
                new_message = message_service.create_message(
                    sender_id=user_id,
                    receiver_id=receiver_id,
                    content=(data.get("content") or "").strip(),
                    image_url=data.get("image_url"),
                    audio_url=data.get("audio_url"),
                    db=db,
                )

                # IMPORTANT: build the payload BEFORE closing the session.
                # message_service.create_message() triggers a second commit
                # internally (via notification_service.create_notification),
                # which expires new_message's attributes. If we wait until
                # after db.close() to read them, SQLAlchemy raises a
                # DetachedInstanceError trying to lazily reload from a
                # closed session — an exception that isn't an HTTPException,
                # so it was silently killing this loop iteration before the
                # broadcast ever ran.
                payload = {
                    "type": "message",
                    "id": new_message.id,
                    "sender_id": new_message.sender_id,
                    "receiver_id": new_message.receiver_id,
                    "content": new_message.content,
                    "image_url": new_message.image_url,
                    "audio_url": new_message.audio_url,
                    "is_seen": new_message.is_seen,
                    "created_at": str(new_message.created_at),
                }

            except HTTPException as e:

                await websocket.send_json(
                    {
                        "type": "error",
                        "message": e.detail,
                    }
                )

                continue

            finally:
                db.close()

            await manager.send_personal_message(user_id, payload)

            await manager.send_personal_message(receiver_id, payload)

    except WebSocketDisconnect:

        await manager.disconnect(user_id)

        await manager.broadcast_online_status(
            user_id,
            False,
        )

@router.get("/online-users", tags=["Chat"])
def get_online_users():
    return {
        "online_users": manager.online_users
    }