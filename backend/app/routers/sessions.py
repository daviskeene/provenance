from typing import List
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from crypto import (
    sign_data,
    hash_data,
    load_private_key,
    load_public_key,
    verify_signature,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


from database import get_db

router = APIRouter()
private_key: Ed25519PrivateKey = load_private_key()  # Load once at import time
public_key: Ed25519PublicKey = load_public_key()  # Load at import time


@router.post("/sessions/start", response_model=schemas.StartSessionResponse)
def start_session(db: Session = Depends(get_db)):
    db_session = models.Session()
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return schemas.StartSessionResponse(session_id=db_session.id)


@router.post("/sessions/{session_id}/events")
def record_events(
    session_id: int, events: List[schemas.EventCreate], db: Session = Depends(get_db)
):
    db_session = (
        db.query(models.Session).filter(models.Session.id == session_id).first()
    )
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    if db_session.finalized:
        raise HTTPException(status_code=400, detail="Session already finalized")

    for event_data in events:
        ev = models.Event(session_id=session_id, character=event_data.character)
        db.add(ev)
    db.commit()
    return {"status": "events recorded"}


@router.post(
    "/sessions/{session_id}/finalize", response_model=schemas.FinalizeSessionResponse
)
def finalize_session(session_id: int, db: Session = Depends(get_db)):
    db_session = (
        db.query(models.Session).filter(models.Session.id == session_id).first()
    )
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    if db_session.finalized:
        raise HTTPException(status_code=400, detail="Session already finalized")

    # Fetch all events for this session
    events = (
        db.query(models.Event)
        .filter(models.Event.session_id == session_id)
        .order_by(models.Event.timestamp)
        .all()
    )
    # Convert events to a stable JSON representation
    events_data = []
    for ev in events:
        events_data.append(
            {"character": ev.character, "timestamp": ev.timestamp.isoformat()}
        )
    events_json = json.dumps(events_data, separators=(",", ":"))  # Compact JSON

    # Hash the events
    data_digest = hash_data(events_json)
    # Sign the hash
    signature = sign_data(private_key, data_digest)

    # Store the hash and signature
    db_session.data_hash = data_digest.hex()
    db_session.signature = signature
    db_session.finalized = True
    db.commit()

    return schemas.FinalizeSessionResponse(success=True)


@router.get("/sessions/{session_id}/verify", response_model=schemas.VerifyResponse)
def verify_session(session_id: int, db: Session = Depends(get_db)):
    db_session = (
        db.query(models.Session).filter(models.Session.id == session_id).first()
    )
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not db_session.signature or not db_session.data_hash:
        return schemas.VerifyResponse(
            verified=False, message="No signature or data hash found."
        )

    # Rebuild the event data and re-hash it
    events = (
        db.query(models.Event)
        .filter(models.Event.session_id == session_id)
        .order_by(models.Event.timestamp)
        .all()
    )
    events_data = [
        {"character": ev.character, "timestamp": ev.timestamp.isoformat()}
        for ev in events
    ]
    events_json = json.dumps(events_data, separators=(",", ":"))
    current_hash = hash_data(events_json)

    # Compare the current hash with the stored data_hash
    if current_hash.hex() != db_session.data_hash:
        return schemas.VerifyResponse(
            verified=False,
            message="Data hash mismatch, data may have been tampered with.",
        )

    # Verify the signature using the public key
    verified = verify_signature(public_key, current_hash, db_session.signature)
    if verified:
        return schemas.VerifyResponse(verified=True, message="Verification successful.")
    else:
        return schemas.VerifyResponse(
            verified=False, message="Signature verification failed."
        )
