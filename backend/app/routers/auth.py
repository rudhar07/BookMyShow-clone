"""
routers/auth.py — a mock "sign in".
===================================
  POST /api/auth/login  {name, email, phone?}  → the User row

Real BookMyShow signs you in with a phone number + OTP. We don't run an SMS
gateway, so this is a deliberately simple **find-or-create by email**: if the
email exists we return that user (and refresh name/phone); otherwise we create
one. The frontend then remembers the returned user (localStorage) as the
"session". The same `users` table already backs the booking flow, so a booking
made while signed in is linked to the same person by email.

This is honestly a mock — no password, no token. In a real build I'd add OTP or
OAuth and issue a JWT. The point here is a working, demoable session.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.UserOut)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if user is None:
        user = models.User(name=req.name, email=req.email, phone=req.phone)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    # Existing user: keep their details fresh if the form supplied new values.
    changed = False
    if req.name and user.name != req.name:
        user.name = req.name
        changed = True
    if req.phone and user.phone != req.phone:
        user.phone = req.phone
        changed = True
    if changed:
        db.commit()
        db.refresh(user)
    return user
