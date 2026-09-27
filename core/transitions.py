from rest_framework.exceptions import ValidationError


def validate_status(*, attrs, instance, graph, initial, label):
    """Enforce a status graph. `initial` is required on create; pass None to allow any start."""
    new_status = attrs.get("status")
    if instance is None:
        if initial is not None and new_status not in (None, initial):
            raise ValidationError({"status": f"A new {label} must start as '{initial}'."})
        return

    current = instance.status
    target = new_status if new_status is not None else current
    if target == current:
        return

    allowed = graph.get(current, ())
    if target not in allowed:
        allowed_text = ", ".join(sorted(str(item) for item in allowed)) or "no further status"
        raise ValidationError(
            {
                "status": (
                    f"Cannot move {label} from '{current}' to '{target}'. "
                    f"Allowed: {allowed_text}."
                )
            }
        )
