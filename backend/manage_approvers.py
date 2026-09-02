"""
CLI to create or reset an approver's passcode — the passcode gate on the
"Approve" action (see app/models/approver.py's module docstring for why
this exists: two named people, Nancy and Maria, need to be individually
identifiable as the one who approved a piece of content, now that
approval is the hard gate before scheduled auto-posting to X).

Run manually against a provisioned database:
    cd backend && python manage_approvers.py create "Nancy"
    cd backend && python manage_approvers.py create "Maria"
    cd backend && python manage_approvers.py reset "Nancy"
    cd backend && python manage_approvers.py list

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


def create_approver(name: str) -> None:
    db = SessionLocal()
    existing = db.query(Approver).filter(Approver.name == name).first()
    if existing:
        print(f'An approver named "{name}" already exists (id={existing.id}). Use `reset` to change their passcode.')
        db.close()
        return

    passcode = generate_passcode()
    approver = Approver(name=name, passcode_hash=hash_passcode(passcode))
    db.add(approver)
    db.commit()
    print(f'Created approver "{name}" (id={approver.id}).')
    print(f"Passcode: {passcode}")
    print("Write this down now — it will not be shown again.")
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
        print(f"  {a.id}: {a.name} (created {a.created_at.date()})")
    db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("create", "reset", "list"):
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    if command == "list":
        list_approvers()
    elif command in ("create", "reset"):
        if len(sys.argv) < 3:
            print(f"Usage: python manage_approvers.py {command} \"<Name>\"")
            sys.exit(1)
        name = sys.argv[2]
        if command == "create":
            create_approver(name)
        else:
            reset_approver(name)
