"""
Local guardrail test harness for Katy Assistant.

This DOES NOT send anything to Slack.
It simulates incoming Slack messages and checks whether the assistant
would be allowed to answer them automatically.
"""

import re

KATY_USER_ID = "U0BK67UNQBT"
KATY_MENTION = f"<@{KATY_USER_ID}>"


# Things the assistant must NEVER invent from old Slack messages.
SITUATIONAL_PATTERNS = [
    r"\beta\b",
    r"\barriv",
    r"\bon[- ]?site\b",
    r"\bon site\b",
    r"\btechnician\b",
    r"\btech\b",
    r"\bconfirmed\b",
    r"\bconfirmation\b",
    r"\bschedul",
    r"\bappointment\b",
    r"\bcomplete(?:d|tion)?\b",
    r"\bfinished\b",
    r"\bdeliver",
    r"\bshipment\b",
    r"\btomorrow\b",
    r"\btoday\b",
    r"\bfriday\b",
]

SENSITIVE_PATTERNS = [
    r"\bpassword\b",
    r"\bcredential",
    r"\bapprove\b",
    r"\bapproval\b",
    r"\binvoice\b",
    r"\brefund\b",
    r"\bpayment\b",
    r"\bcharge\b",
    r"\bfire(?:d|s|ing)?\b",
    r"\bterminated\b",
    r"\btermination\b",
    r"\blegal\b",
    r"\blawsuit\b",
    r"\battorney\b",
]


def contains_any(text, patterns):
    text = text.lower()
    return any(re.search(pattern, text) for pattern in patterns)


def classify_message(text):
    """
    First-pass LOCAL safety classifier.

    This happens before an LLM or historical Slack retrieval is trusted.
    """

    # No actual @Katy mention = ignore
    if KATY_MENTION not in text:
        return {
            "classification": "IGNORE",
            "action": "NONE",
            "followup": False,
            "reason": "Katy was not @mentioned.",
        }

    if contains_any(text, SENSITIVE_PATTERNS):
        return {
            "classification": "SENSITIVE",
            "action": "ACKNOWLEDGE_ONLY",
            "followup": True,
            "reason": "Sensitive/approval/security/HR/legal topic.",
        }

    if contains_any(text, SITUATIONAL_PATTERNS):
        return {
            "classification": "SITUATIONAL",
            "action": "ACKNOWLEDGE_ONLY",
            "followup": True,
            "reason": "Answer depends on current information.",
        }

    return {
        "classification": "UNKNOWN",
        "action": "RETRIEVE_HISTORY",
        "followup": True,
        "reason": "Safe to search history, but not automatically trusted.",
    }


TESTS = [
    # Should be completely ignored
    {
        "name": "No Katy mention",
        "message": "Does anybody know the ETA for Site 528?",
        "expected": "IGNORE",
    },

    # Situational/current
    {
        "name": "Technician ETA",
        "message": f"{KATY_MENTION} what's the ETA for the technician at Site 528?",
        "expected": "SITUATIONAL",
    },
    {
        "name": "Technician status",
        "message": f"{KATY_MENTION} is the technician on site?",
        "expected": "SITUATIONAL",
    },
    {
        "name": "Tomorrow confirmation",
        "message": f"{KATY_MENTION} is tomorrow's appointment confirmed?",
        "expected": "SITUATIONAL",
    },
    {
        "name": "Completion promise",
        "message": f"{KATY_MENTION} can we tell them this will be completed tomorrow?",
        "expected": "SITUATIONAL",
    },
    {
        "name": "Equipment arrival",
        "message": f"{KATY_MENTION} what time will the equipment arrive?",
        "expected": "SITUATIONAL",
    },

    # Sensitive
    {
        "name": "Invoice approval",
        "message": f"{KATY_MENTION} can you approve this $2,500 invoice?",
        "expected": "SENSITIVE",
    },
    {
        "name": "Password",
        "message": f"{KATY_MENTION} what's John's password?",
        "expected": "SENSITIVE",
    },
    {
        "name": "Employment",
        "message": f"{KATY_MENTION} did we fire Mike?",
        "expected": "SENSITIVE",
    },
    {
        "name": "Legal complaint",
        "message": f"{KATY_MENTION} the customer is threatening legal action.",
        "expected": "SENSITIVE",
    },
    {
        "name": "Refund",
        "message": f"{KATY_MENTION} can this customer get a refund?",
        "expected": "SENSITIVE",
    },

    # Candidate for historical retrieval
    {
        "name": "Completion photo procedure",
        "message": f"{KATY_MENTION} where do completion photos get uploaded?",
        "expected": "UNKNOWN",
    },
]


def run_tests():
    print("=" * 70)
    print("KATY ASSISTANT - LOCAL GUARDRAIL TEST")
    print("=" * 70)
    print()

    passed = 0

    for number, test in enumerate(TESTS, start=1):
        result = classify_message(test["message"])

        success = result["classification"] == test["expected"]

        if success:
            passed += 1

        print(f"TEST {number:02}: {test['name']}")
        print(f"Message:        {test['message']}")
        print(f"Classification: {result['classification']}")
        print(f"Action:         {result['action']}")
        print(f"Follow-up:      {result['followup']}")
        print(f"Reason:         {result['reason']}")
        print(f"Expected:       {test['expected']}")
        print(f"RESULT:         {'PASS' if success else 'FAIL'}")
        print("-" * 70)

    print()
    print("=" * 70)
    print(f"RESULT: {passed}/{len(TESTS)} TESTS PASSED")
    print("=" * 70)

    if passed == len(TESTS):
        print("Guardrail test suite PASSED.")
    else:
        print("Guardrail test suite FAILED. Do NOT enable AUTO_SEND.")


if __name__ == "__main__":
    run_tests()