from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail

from apps.audit.constants import AuditAction
from apps.audit.services import safe_audit
from apps.supplier_reservations.services import SupplierReservationService
from core.exceptions import ValidationError


EMAIL_TYPES = (
    ("request", "Reservation request"),
    ("followup", "Confirmation follow-up"),
    ("rooming", "Rooming list"),
    ("change", "Change request"),
    ("cancellation", "Cancellation"),
)

AGENCY = getattr(settings, "AGENCY_NAME", None) or "TourOps Travel Agency"


def _dear(name: str) -> str:
    label = (name or "Supplier").strip() or "Supplier"
    if not label.lower().endswith("team"):
        label = f"{label} Team"
    return f"Dear {label},"


def _allocation_lines(reservation: dict) -> str:
    if reservation.get("is_hotel"):
        lines = []
        for line in reservation.get("room_allocations") or []:
            lines.append(
                f"{line['quantity']} {line['type_label']} rooms\n"
                f"Occupancy: {line['occupancy']} guest(s) per room\n"
                f"Sleeping capacity: {line['beds']} guests"
            )
        return "\n\n".join(lines) or "Allocation to be confirmed."
    quantity = reservation.get("quantity") or 1
    return f"{quantity} × {reservation.get('service_label') or 'service'}"


def _signoff() -> str:
    return f"Kind regards,\n\n{AGENCY}"


class SupplierEmailService:
    def build(self, reservation_id, kind: str = "request", *, extra_note: str = "") -> dict:
        reservation = SupplierReservationService().get_presented(reservation_id)
        if not reservation.get("supplier_email"):
            raise ValidationError("This supplier has no email address on file.")
        kind = (kind or "request").strip().lower()
        builders = {
            "request": self._request,
            "followup": self._followup,
            "rooming": self._rooming,
            "change": self._change,
            "cancellation": self._cancellation,
        }
        if kind not in builders:
            raise ValidationError("Unknown email type.")
        payload = builders[kind](reservation)
        if extra_note:
            payload["body"] = f"{payload['body']}\n\n{extra_note.strip()}"
        payload.update(
            {
                "to": reservation["supplier_email"],
                "kind": kind,
                "kind_label": dict(EMAIL_TYPES).get(kind, kind),
                "reservation_id": reservation["id"],
                "reservation_number": reservation["number"],
                "supplier": reservation["supplier"],
                "tour": reservation["tour"],
            }
        )
        return payload

    def build_reservation_request(self, reservation_id, **kwargs) -> dict:
        return self.build(reservation_id, "request", **kwargs)

    def build_confirmation_followup(self, reservation_id, **kwargs) -> dict:
        return self.build(reservation_id, "followup", **kwargs)

    def build_rooming_list_email(self, reservation_id, **kwargs) -> dict:
        return self.build(reservation_id, "rooming", **kwargs)

    def build_change_request(self, reservation_id, **kwargs) -> dict:
        return self.build(reservation_id, "change", **kwargs)

    def build_cancellation_email(self, reservation_id, **kwargs) -> dict:
        return self.build(reservation_id, "cancellation", **kwargs)

    def send(self, *, to: str, subject: str, body: str, actor_id, reservation_id) -> dict:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "noreply@tourops.local"
        try:
            sent = send_mail(subject, body, from_email, [to], fail_silently=False)
        except Exception as extra:
            return {"sent": False, "reason": str(extra) or "Email sending is not configured."}
        if not sent:
            return {"sent": False, "reason": "Email sending is not configured in this environment."}
        safe_audit(
            actor_id=actor_id,
            action=AuditAction.EMAIL_SENT.value,
            entity_type="supplier_reservations",
            entity_id=reservation_id,
            description=f"Email sent to {to}: {subject}",
        )
        return {"sent": True, "reason": ""}

    def mark_generated(self, *, actor_id, reservation_id, subject: str) -> None:
        safe_audit(
            actor_id=actor_id,
            action=AuditAction.EMAIL_GENERATED.value,
            entity_type="supplier_reservations",
            entity_id=reservation_id,
            description=f"Email generated: {subject}",
        )

    def _request(self, reservation: dict) -> dict:
        subject = f"{reservation['service_label']} Reservation Request — {reservation['tour']} — {reservation['start_label']}"
        body = "\n".join(
            [
                _dear(reservation["supplier"]),
                "",
                f"We would like to arrange {reservation['service_label'].lower()} for the following TourOps group:",
                "",
                f"Tour:\n{reservation['tour']}",
                "",
                f"Arrival:\n{reservation['start_label']}",
                "",
                f"Departure:\n{reservation['end_label']}",
                "",
                "Requested arrangement:",
                "",
                _allocation_lines(reservation),
                "",
                "Please confirm availability for the above arrangement and provide your reservation confirmation/reference number.",
                "",
                "If you require any additional information, please let us know.",
                "",
                _signoff(),
            ]
        )
        return {"subject": subject, "body": body}

    def _followup(self, reservation: dict) -> dict:
        subject = f"Confirmation Follow-up — {reservation['tour']} — {reservation['number']}"
        body = "\n".join(
            [
                _dear(reservation["supplier"]),
                "",
                f"We are following up regarding our {reservation['service_label'].lower()} request",
                f"for {reservation['tour']} from {reservation['start_label']} to {reservation['end_label']}.",
                "",
                f"Reservation:\n{reservation['number']}",
                "",
                "Requested allocation:",
                _allocation_lines(reservation),
                "",
                "Please confirm the reservation and provide your confirmation/reference number.",
                "",
                _signoff(),
            ]
        )
        return {"subject": subject, "body": body}

    def _rooming(self, reservation: dict) -> dict:
        listing = SupplierReservationService().rooming_list(
            reservation["tour_id"],
            reservation_id=reservation["id"],
        )
        rooms = listing.get("rooms") or []
        assigned = sum(len(room.get("guests") or []) for room in rooms)
        lines = []
        for room in rooms:
            guests = " / ".join(person.get("name") or "Guest" for person in room.get("guests") or [])
            lines.append(f"Room {room.get('room_number')}  {room.get('type_label')}\n{guests}")
        rooming_block = "\n\n".join(lines) if lines else "Room assignments are still being completed."
        subject = f"Rooming List — {reservation['tour']} — {reservation['start_label']}"
        body = "\n".join(
            [
                _dear(reservation["supplier"]),
                "",
                "Please find the rooming list for our upcoming group:",
                "",
                f"Tour:\n{reservation['tour']}",
                "",
                f"Arrival:\n{reservation['start_label']}",
                "",
                f"Departure:\n{reservation['end_label']}",
                "",
                f"Total travelers assigned:\n{assigned}",
                "",
                f"Rooms assigned:\n{len(rooms)}",
                "",
                "Rooming list:",
                "",
                rooming_block,
                "",
                _signoff(),
            ]
        )
        return {"subject": subject, "body": body}

    def _change(self, reservation: dict) -> dict:
        subject = f"Change Request — {reservation['tour']} — {reservation['number']}"
        body = "\n".join(
            [
                _dear(reservation["supplier"]),
                "",
                f"Please review a change to reservation {reservation['number']} for {reservation['tour']}.",
                "",
                f"Dates: {reservation['dates']}",
                "",
                "Current allocation:",
                _allocation_lines(reservation),
                "",
                "Please confirm the revised arrangement and advise if the confirmation number remains the same.",
                "",
                _signoff(),
            ]
        )
        return {"subject": subject, "body": body}

    def _cancellation(self, reservation: dict) -> dict:
        subject = f"Cancellation — {reservation['tour']} — {reservation['number']}"
        body = "\n".join(
            [
                _dear(reservation["supplier"]),
                "",
                f"Please cancel reservation {reservation['number']} for {reservation['tour']}",
                f"({reservation['dates']}).",
                "",
                "This notice is sent by TourOps on behalf of the travel agency. Please confirm cancellation in writing.",
                "",
                _signoff(),
            ]
        )
        return {"subject": subject, "body": body}
