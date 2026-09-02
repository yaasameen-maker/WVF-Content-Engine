"""
CLI to create or reset an approver's passcode — the passcode gate on the
"Approve" action (see app/models/approver.py's module docstring for why
this exists: two named people, Nancy and Maria, need to be individually
identifiable as the one who approved a piece of content, now that
approval is the hard gate before scheduled auto-posting to X).

Run manually against a provisioned database:
    cd backend && python manage_approvers.py create "Nancy" nancy@wvf-ny.org
    cd backend && python manage_approvers.py create "Maria" motero@wvf-ny.org
    cd backend && python manage_approvers.py reset "Nancy"
    cd backend && python manage_approvers.py set-email "Nancy" nancy@wvf-ny.org
    cd backend && python manage_approvers.py list

email (optional on create, or set later via set-email) enables
self-service "forgot passcode" — see app/routers/approvers.py. An
approver with no email on file can still be reset, just not by
themselves; use `reset` for that.

The generated passcode is printed ONCE to the terminal and never stored
or logged anywhere in plaintext — write it down immediately and hand it
to that person directly (not over an unencrypted channel like plain
email/Slack if you can help it). If it's lost, use `reset` to generate a
new one; there's no way to recover the old one.

This script is safe to commit — it contains no secrets itself, it only
generates them at runtime.
"""

import secrets
import sys

import bcrypt

from app.database import SessionLocal
from app.models import Approver

# Passcodes are short (staff will type these by hand each approval, not
# store them in a password manager) but still have real entropy — 8
# random alphanumeric characters, ~47 bits, far more than a 4-6 digit PIN
# while staying quick to type.
PASSCODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I — avoids transcription errors
PASSCODE_LENGTH = 8


def generate_passcode() -> str:
    return "".join(secrets.choice(PASSCODE_ALPHABET) for _ in range(PASSCODE_LENGTH))


def hash_passcode(passcode: str) -> str:
    return bcrypt.hashpw(passcode.encode(), bcrypt.gensalt()).decode()


def create_approver(name: str, email: str | None = None) -> None:
    db = SessionLocal()
    existing = db.query(Approver).filter(Approver.name == name).first()
    if existing:
        print(f'An approver named "{name}" already exists (id={existing.id}). Use `reset` to change their passcode.')
        db.close()
        return

    passcode = generate_passcode()
    approver = Approver(name=name, email=email, passcode_hash=hash_passcode(passcode))
    db.add(approver)
    db.commit()
    print(f'Created approver "{name}" (id={approver.id}).')
    if email:
        print(f"Email on file: {email} (enables self-service passcode reset)")
    else:
        print("No email on file — self-service reset unavailable until set via `set-email`.")
    print(f"Passcode: {passcode}")
    print("Write this down now — it will not be shown again.")
    db.close()


def set_email(name: str, email: str) -> None:
    db = SessionLocal()
    approver = db.query(Approver).filter(Approver.name == name).first()
    if not approver:
        print(f'No approver named "{name}" found. Use `create` first.')
        db.close()
        return
    approver.email = email
    db.commit()
    print(f'Set email for "{name}" to {email}.')
    db.close()


def reset_approver(name: str) -> None:
    db = SessionLocal()
    approver = db.query(Approver).filter(Approver.name == name).first()
    if not approver:
        print(f'No approver named "{name}" found. Use `create` first.')
        db.close()
        return

    passcode = generate_passcode()
    approver.passcode_hash = hash_passcode(passcode)
    db.commit()
    print(f'Reset passcode for "{name}".')
    print(f"New passcode: {passcode}")
    print("Write this down now — it will not be shown again. The old passcode no longer works.")
    db.close()


def list_approvers() -> None:
    db = SessionLocal()
    approvers = db.query(Approver).order_by(Approver.name).all()
    if not approvers:
        print("No approvers yet.")
    for a in approvers:
        email_note = a.email or "(no email — self-service reset unavailable)"
        print(f"  {a.id}: {a.name} — {email_note} (created {a.created_at.date()})")
    db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("create", "reset", "list", "set-email"):
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    if command == "list":
        list_approvers()
    elif command == "reset":
        if len(sys.argv) < 3:
            print('Usage: python manage_approvers.py reset "<Name>"')
            sys.exit(1)
        reset_approver(sys.argv[2])
    elif command == "create":
        if len(sys.argv) < 3:
            print('Usage: python manage_approvers.py create "<Name>" [email]')
            sys.exit(1)
        name = sys.argv[2]
        email = sys.argv[3] if len(sys.argv) > 3 else None
        create_approver(name, email)
    elif command == "set-email":
        if len(sys.argv) < 4:
            print('Usage: python manage_approvers.py set-email "<Name>" <email>')
            sys.exit(1)
        set_email(sys.argv[2], sys.argv[3])
