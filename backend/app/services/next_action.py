
NEXT_ACTIONS = {
    "DRAFT": "Complete your application details.",
    "SUBMITTED": "Check your application acknowledgement.",
    "UNDER_REVIEW": "Wait for an official update and check periodically.",
    "DOCUMENT_REQUIRED": "Submit the required documents.",
    "APPROVED": "Check the benefit disbursement or next official step.",
    "REJECTED": "Review the rejection reason and verify appeal options.",
    "WITHDRAWN": "Check whether you need to start a new application.",
}


def get_next_action(status: str) -> str:
    return NEXT_ACTIONS.get(
        status,
        "Check your application status and contact the official department if needed.",
    )