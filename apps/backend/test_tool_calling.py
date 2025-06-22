"""
Test script for the IntakeAgent with natural tool calling capabilities.
"""

import asyncio

from langchain_core.messages import HumanMessage

from src.agents.intake import intake_agent
from src.state import WorkflowState


async def test_natural_tool_calling():
    """Test scenarios where LLM should naturally decide when to use tools."""

    test_scenarios = [
        {
            "name": "Patient with clear name mentioned",
            "conversation": """
            Nurse: Hello, what brings you in today?
            Patient: Hi, I'm Tony Stark. I've been having severe headaches for the past week.
            Nurse: Can you rate your pain on a scale of 1 to 10?
            Patient: It's about an 8 out of 10.
            Nurse: Are you taking any medications currently?
            Patient: Just my regular blood pressure medication.
            Nurse: Do you have any known allergies?
            Patient: I'm allergic to penicillin.
            """,
            "should_call_tools": True,
            "expected_patient": "Tony Stark",
        },
        {
            "name": "Patient name mentioned casually",
            "conversation": """
            Nurse: What's your name?
            Patient: Bruce Wayne.
            Nurse: What brings you in, Bruce?
            Patient: I've been having trouble sleeping lately. The pain keeps me awake.
            Nurse: How would you rate the pain?
            Patient: About a 7 out of 10 most nights.
            """,
            "should_call_tools": True,
            "expected_patient": "Bruce Wayne",
        },
        {
            "name": "No patient name mentioned",
            "conversation": """
            Nurse: What brings you in today?
            Patient: I've been having headaches.
            Nurse: How long have they been going on?
            Patient: About a week.
            Nurse: Any medications?
            Patient: Just some ibuprofen.
            """,
            "should_call_tools": False,
            "expected_patient": None,
        },
        {
            "name": "Only first name mentioned",
            "conversation": """
            Nurse: Hi there, what's your name?
            Patient: I'm Peter.
            Nurse: What brings you in, Peter?
            Patient: I've been having some joint pain in my wrists.
            Nurse: How long has this been going on?
            Patient: About two weeks. It's really affecting my daily activities.
            """,
            "should_call_tools": True,
            "expected_patient": "Peter",
        },
        {
            "name": "General checkup - no specific symptoms",
            "conversation": """
            Nurse: Hello, how can I help you today?
            Patient: I'm just here for my annual checkup.
            Nurse: Any concerns or symptoms?
            Patient: No, feeling pretty good overall.
            """,
            "should_call_tools": False,
            "expected_patient": None,
        },
        {
            "name": "Patient name not in database",
            "conversation": """
            Nurse: Hello, what's your name?
            Patient: I'm John Smith.
            Nurse: What brings you in today, John?
            Patient: I've been having chest pain for the last few hours.
            Nurse: How severe is the pain on a scale of 1 to 10?
            Patient: It's about a 9 out of 10.
            """,
            "should_call_tools": True,
            "expected_patient": None,  # Will fail to find patient, should set patient_info to None
            "expect_tool_failure": True,
        },
    ]

    print("🏥 Testing Natural Tool Calling Behavior")
    print("=" * 60)

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 SCENARIO {i}: {scenario['name']}")
        print("=" * 50)

        # Create initial state
        initial_state = WorkflowState(
            messages=[HumanMessage(content=scenario["conversation"])], retry_count=0
        )

        try:
            # Run the intake agent
            result = await intake_agent.run(initial_state)

            # Analyze if tools were called
            messages = result.get("messages", [])
            tool_calls_made = []

            for msg in messages:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_calls_made.append(
                            {
                                "tool": tool_call["name"],
                                "args": tool_call.get("args", {}),
                            }
                        )

            tools_called = len(tool_calls_made) > 0

            # Print results
            print("📋 Conversation analysis complete")
            print(f"🛠️  Tools called: {'✅ Yes' if tools_called else '❌ No'}")
            print(
                f"🎯 Should call tools: {'✅ Yes' if scenario['should_call_tools'] else '❌ No'}"
            )

            # Check if behavior matches expectation
            behavior_correct = tools_called == scenario["should_call_tools"]
            print(
                f"🏆 Behavior: {'✅ CORRECT' if behavior_correct else '❌ UNEXPECTED'}"
            )

            if tool_calls_made:
                print("🔍 Tool calls made:")
                for call in tool_calls_made:
                    print(f"   • {call['tool']} with args: {call['args']}")

            # Check if patient info was retrieved
            if result.get("patient_info"):
                patient = result["patient_info"]
                print(f"👤 Patient found: {patient.first_name} {patient.last_name}")

                # Verify it's the expected patient
                if scenario["expected_patient"]:
                    expected_name = scenario["expected_patient"].lower()
                    actual_name = f"{patient.first_name} {patient.last_name}".lower()
                    if expected_name in actual_name or any(
                        part in actual_name for part in expected_name.split()
                    ):
                        print("✅ Correct patient identified")
                    else:
                        print(
                            f"❌ Wrong patient: expected {scenario['expected_patient']}, got {actual_name}"
                        )
            else:
                # Check if this was expected (no patient name or tool failure)
                if (
                    scenario.get("expect_tool_failure")
                    or not scenario["expected_patient"]
                ):
                    print("✅ No patient info retrieved (as expected)")
                else:
                    print("❌ Expected patient info but none found")

            # Check for tool failures in messages
            tool_errors = []
            for msg in messages:
                if (
                    hasattr(msg, "content")
                    and hasattr(msg, "name")
                    and "Unable to retrieve patient record" in str(msg.content)
                ):
                    tool_errors.append(str(msg.content))

            if tool_errors:
                print("🚨 Tool execution errors:")
                for error in tool_errors:
                    print(f"   • {error}")

                # Verify this was expected
                if scenario.get("expect_tool_failure"):
                    print("✅ Tool failure was expected for this scenario")
                else:
                    print("❌ Unexpected tool failure")

            # Print conversation analysis
            if result.get("intake_conversation_info"):
                info = result["intake_conversation_info"]
                print(f"📝 Chief complaint: {info.chief_complaint}")

            print(f"📊 Iterations: {result.get('retry_count', 0)}")

        except Exception as e:
            print(f"❌ Error in scenario {i}: {str(e)}")
            import traceback

            print(f"📍 Traceback: {traceback.format_exc()}")


async def test_specific_patient_search():
    """Test searching for specific patients by name."""

    print("\n🔍 Testing Specific Patient Search")
    print("=" * 40)

    from src.agents.intake import get_patient_medical_record

    test_searches = [
        "Tony Stark",
        "Bruce Wayne",
        "Peter Parker",
        "Tony",  # First name only
        "Wayne",  # Last name only
        "4",  # ID number
        "",  # Empty string - should fail
        "   ",  # Whitespace only - should fail
        "Unknown Person",  # Should fail
    ]

    for search_term in test_searches:
        try:
            patient = get_patient_medical_record(search_term)
            print(
                f"✅ '{search_term}' → {patient.first_name} {patient.last_name} (ID: {patient.patient_id})"
            )
        except Exception as e:
            print(f"❌ '{search_term}' → {str(e)}")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_natural_tool_calling())
    asyncio.run(test_specific_patient_search())
