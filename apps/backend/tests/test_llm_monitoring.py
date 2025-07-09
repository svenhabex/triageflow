"""
Test script to demonstrate LLM monitoring and optimization.
Compares original intake agent vs optimized version.
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from src.agents.coordinator import CoordinatorAgent
from src.agents.intake import IntakeAgent
from src.agents.optimized_intake import OptimizedIntakeAgent
from src.agents.triage import TriageAgent
from src.core.llm_monitor import llm_monitor
from src.state import CoordinatorAgentState, IntakeAgentState, TriageAgentState

load_dotenv()

# Test conversation with patient name
TEST_CONVERSATION = """
Nurse: Hello, what brings you in today?
Patient: Hi, I'm Tony Stark. I've been having severe headaches for the past week.
Nurse: Can you rate your pain on a scale of 1 to 10?
Patient: It's about an 8 out of 10. The pain is really affecting my work.
Nurse: Are you taking any medications currently?
Patient: Just my regular blood pressure medication and some ibuprofen for the headaches.
Nurse: Do you have any known allergies?
Patient: I'm allergic to penicillin.
Nurse: When did these headaches start exactly?
Patient: About a week ago. They're getting worse, especially in the mornings.
"""


async def test_original_intake_agent():
    """Test the original intake agent and track LLM requests."""
    print("\n🔍 Testing Original Intake Agent...")

    agent = IntakeAgent(max_iterations=5)

    initial_state = IntakeAgentState(
        messages=[HumanMessage(content=TEST_CONVERSATION)],
    )

    result = await agent.run(initial_state)

    print(f"✅ Original agent completed. Messages: {len(result.get('messages', []))}")
    if result.get("patient_info"):
        patient = result["patient_info"]
        print(f"📋 Patient found: {patient.first_name} {patient.last_name}")

    return result


async def test_optimized_intake_agent():
    """Test the optimized intake agent and track LLM requests."""
    print("\n⚡ Testing Optimized Intake Agent...")

    agent = OptimizedIntakeAgent(max_iterations=3)

    initial_state = IntakeAgentState(
        messages=[HumanMessage(content=TEST_CONVERSATION)],
    )

    result = await agent.run(initial_state)

    print(f"✅ Optimized agent completed. Messages: {len(result.get('messages', []))}")
    if result.get("patient_info"):
        patient = result["patient_info"]
        print(f"📋 Patient found: {patient.first_name} {patient.last_name}")

    return result


async def test_full_workflow():
    """Test the complete workflow: intake -> triage -> coordination."""
    print("\n🏥 Testing Full Workflow (Intake -> Triage -> Coordinator)...")

    # Step 1: Intake
    intake_agent = OptimizedIntakeAgent()
    initial_state = IntakeAgentState(
        messages=[HumanMessage(content=TEST_CONVERSATION)],
    )

    intake_result = await intake_agent.run(initial_state)
    print(
        f"✅ Intake completed. Patient info: {intake_result.get('patient_info') is not None}"
    )

    # Step 2: Triage
    # Map intake result to TriageAgentState
    triage_input = TriageAgentState(
        messages=intake_result.get("messages", []),
        patient_info=intake_result.get("patient_info"),
        intake_conversation_info=intake_result.get("intake_conversation_info"),
    )

    triage_agent = TriageAgent()
    triage_result = await triage_agent.run(triage_input)
    print(
        f"✅ Triage completed. Triage info: {triage_result.get('triage_info') is not None}"
    )

    if triage_result.get("triage_info"):
        triage_info = triage_result["triage_info"]
        print(f"🏷️ Triage Level: {getattr(triage_info, 'urgency_level', 'N/A')}")
        print(f"🏥 Medical Category: {getattr(triage_info, 'medical_category', 'N/A')}")

    # Step 3: Coordination
    # Map triage result to CoordinatorAgentState
    coordinator_input = CoordinatorAgentState(
        messages=triage_result.get("messages", []),
        patient_info=triage_result.get("patient_info"),
        intake_conversation_info=triage_result.get("intake_conversation_info"),
        triage_info=triage_result.get("triage_info"),
    )

    coordinator_agent = CoordinatorAgent()
    final_result = await coordinator_agent.run(coordinator_input)
    print(
        f"✅ Coordination completed. Staff found: {len(final_result.get('available_staff', []))}"
    )

    return final_result


async def compare_agents():
    """Compare original vs optimized intake agents."""
    print("\n" + "=" * 60)
    print("🔬 LLM REQUEST MONITORING & OPTIMIZATION ANALYSIS")
    print("=" * 60)

    # Clear any existing monitoring data
    llm_monitor.clear_all()

    # Test original agent
    await test_original_intake_agent()

    # Test optimized agent
    await test_optimized_intake_agent()

    # Test full workflow
    await test_full_workflow()

    # Generate comparison reports
    print("\n" + "=" * 60)
    print("📊 COMPARISON ANALYSIS")
    print("=" * 60)

    # Original agent stats
    print("\n🔍 ORIGINAL INTAKE AGENT:")
    original_stats = llm_monitor.get_stats("original_test_session")
    original_insights = llm_monitor.get_optimization_insights("original_test_session")

    print(f"  Total LLM Requests: {original_stats.total_requests}")
    print(f"  Estimated Cost: ${original_stats.total_cost_estimate:.4f}")
    print(f"  Avg Duration: {original_stats.avg_duration_ms:.1f}ms")
    print(
        f"  Retry Rate: {(original_stats.retry_count / max(original_stats.total_requests, 1)) * 100:.1f}%"
    )

    # Optimized agent stats
    print("\n⚡ OPTIMIZED INTAKE AGENT:")
    optimized_stats = llm_monitor.get_stats("optimized_test_session")
    optimized_insights = llm_monitor.get_optimization_insights("optimized_test_session")

    print(f"  Total LLM Requests: {optimized_stats.total_requests}")
    print(f"  Estimated Cost: ${optimized_stats.total_cost_estimate:.4f}")
    print(f"  Avg Duration: {optimized_stats.avg_duration_ms:.1f}ms")
    print(
        f"  Retry Rate: {(optimized_stats.retry_count / max(optimized_stats.total_requests, 1)) * 100:.1f}%"
    )

    # Full workflow stats
    print("\n🏥 FULL WORKFLOW:")
    workflow_stats = llm_monitor.get_stats("full_workflow_session")
    workflow_insights = llm_monitor.get_optimization_insights("full_workflow_session")

    print(f"  Total LLM Requests: {workflow_stats.total_requests}")
    print(f"  Estimated Cost: ${workflow_stats.total_cost_estimate:.4f}")
    print(f"  Avg Duration: {workflow_stats.avg_duration_ms:.1f}ms")

    # Calculate savings
    if original_stats.total_requests > 0 and optimized_stats.total_requests > 0:
        request_reduction = (
            (original_stats.total_requests - optimized_stats.total_requests)
            / original_stats.total_requests
        ) * 100
        cost_reduction = (
            (original_stats.total_cost_estimate - optimized_stats.total_cost_estimate)
            / max(original_stats.total_cost_estimate, 0.0001)
        ) * 100

        print("\n💰 OPTIMIZATION SAVINGS:")
        print(f"  Request Reduction: {request_reduction:.1f}%")
        print(f"  Cost Reduction: {cost_reduction:.1f}%")

    # Print detailed summaries
    llm_monitor.print_summary("original_test_session")
    llm_monitor.print_summary("optimized_test_session")
    llm_monitor.print_summary("full_workflow_session")

    # Overall insights
    print("\n" + "=" * 60)
    print("🎯 OPTIMIZATION RECOMMENDATIONS")
    print("=" * 60)

    all_recommendations = []
    for session in [
        "original_test_session",
        "optimized_test_session",
        "full_workflow_session",
    ]:
        insights = llm_monitor.get_optimization_insights(session)
        all_recommendations.extend(insights.get("recommendations", []))

    if all_recommendations:
        high_priority = [r for r in all_recommendations if r["priority"] == "high"]
        medium_priority = [r for r in all_recommendations if r["priority"] == "medium"]
        low_priority = [r for r in all_recommendations if r["priority"] == "low"]

        for priority, recommendations in [
            ("HIGH", high_priority),
            ("MEDIUM", medium_priority),
            ("LOW", low_priority),
        ]:
            if recommendations:
                print(f"\n{priority} PRIORITY:")
                for rec in recommendations:
                    print(f"  • {rec['message']}")
    else:
        print("🎉 No optimization issues detected!")

    print("\n" + "=" * 60)
    print("📈 SUMMARY & NEXT STEPS")
    print("=" * 60)

    print("""
Key Optimization Strategies Implemented:
1. ✅ LLM Request Monitoring - Track usage patterns and costs
2. ✅ Combined Operations - Reduced intake agent from 2 to 1 LLM call
3. ✅ Reduced Max Iterations - Lowered retry limits for efficiency
4. ✅ Smart Tool Usage - Only call tools when patient names are mentioned

Additional Optimization Opportunities:
1. 🔄 Caching - Cache patient records and staff lookups
2. 📝 Prompt Engineering - Optimize prompts for shorter responses
3. 🎯 Model Selection - Use smaller models for simple tasks
4. 🔀 Batching - Combine multiple operations when possible
5. ⚡ Early Exit - Skip unnecessary steps when possible

Monitor your production usage with: llm_monitor.print_summary()
""")


if __name__ == "__main__":
    # Set up environment
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY environment variable not set!")
        print("Please set it to run this test.")
        exit(1)

    # Run the comparison
    asyncio.run(compare_agents())
