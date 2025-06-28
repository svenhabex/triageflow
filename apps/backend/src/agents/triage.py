import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from src.models import TriageInformation
from src.state import WorkflowState


def _get_model():
    """Get the ChatGoogleGenerativeAI model, initialized lazily."""

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-05-20",
        temperature=1.0,
        max_retries=1,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )


ASSESS_NODE = "assess"


class TriageAgent:
    """
    Triage agent, analyzes the patient's symptoms and history to determine the appropriate level of care.
    """

    def __init__(self):
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        self._model = None

    @property
    def model(self):
        """Lazily initialize the model when first accessed."""
        if self._model is None:
            self._model = _get_model()

        return self._model

    def _build_graph(self) -> StateGraph:
        """Build the graph for the triage agent."""

        workflow = StateGraph(WorkflowState, output=WorkflowState)

        workflow.add_node(ASSESS_NODE, self._assess)
        workflow.set_entry_point(ASSESS_NODE)
        workflow.add_edge(ASSESS_NODE, END)

        return workflow

    async def run(self, state: WorkflowState) -> WorkflowState:
        """Run the triage agent subgraph."""

        result = await self.app.ainvoke(state)

        return result

    async def _assess(self, state: WorkflowState) -> WorkflowState:
        """Assess the patient's symptoms and history to determine the appropriate level of care."""

        try:
            # Build the system prompt content with context data
            system_content = """
        System Prompt: Clinical Triage Agent
            ROLE AND GOAL:
            You are an expert triage AI assistant. Your purpose is to accurately assess a patient's situation based on provided data and assign a triage level according to the 5-level Emergency Severity Index (ESI) algorithm. You must provide clear reasoning for your decision based on the steps of the algorithm.

            INPUT DATA FORMAT:
            You will receive a JSON object containing the intake conversation data. And the patient's medical record.

            TRIAGE INSTRUCTIONS (Follow these steps in order):

            Step 1: Decision Point A - Is immediate life-saving intervention required?

            Check for any of the following: Not breathing, pulseless, severe respiratory distress, SpO2 < 90%, acute mental status change, unresponsive.

            If YES, assign ESI Level 1 and stop.

            Step 2: Decision Point B - Is this a high-risk situation?

            If the patient is not ESI Level 1, evaluate if they are in a high-risk situation. This means they cannot safely wait for treatment.

            Consider:

            Is this a patient who could deteriorate quickly? (e.g., potential for active chest pain in a patient with cardiac risk factors).

            Is there a threat to life, limb, or organ?

            Is the patient confused, lethargic, or disoriented?

            Is the patient in severe pain or distress (rated 7/10 or higher)?

            If YES, assign ESI Level 2 and stop.

            Step 3: Decision Point C - How many resources are needed?

            If the patient is stable (not ESI Level 1 or 2), predict the number of resources needed to reach a disposition (discharge, admit, transfer).

            Resources Include: Labs (blood, urine), ECG, X-rays, CT/MRI/Ultrasound, IV fluids, IV/IM medications, specialty consultation.

            NOT Resources: History & physical exam, oral medications, simple wound care (dressings), crutches/splints.

            Based on the number of predicted resources:

            Many resources (2 or more): Assign ESI Level 3.

            One resource: Assign ESI Level 4.

            No resources: Assign ESI Level 5.

            Step 4: Decision Point D - Check Vital Signs

            Only for ESI Level 3 patients from Step 3. Review the vital signs. If any vital sign exceeds the danger thresholds listed below, upgrade the patient to ESI Level 2.

            Heart Rate: > 100

            Respiratory Rate: > 20

            Oxygen Saturation (SpO2): < 92%

            If the patient was assigned Level 3 and their vitals are dangerous, change the level to 2. Otherwise, keep the level from Step 3.

            Step 5: Determine Medical Category and Format Output

            Based on the symptoms and history, determine the most likely medical category from this list: [Cardiology, Neurology, Pulmonology, Orthopedics, Gastroenterology, General, Trauma].
        """

            patient_info = state.get("patient_info")
            intake_conversation_info = state.get("intake_conversation_info")

            # Add patient information to system prompt if available
            if patient_info:
                system_content += f"\n\nPATIENT INFORMATION:\n{patient_info.model_dump_json(indent=2)}"

            # Add intake conversation info to system prompt if available
            if intake_conversation_info:
                system_content += f"\n\nINTAKE CONVERSATION DATA:\n{intake_conversation_info.model_dump_json(indent=2)}"

            system_prompt = SystemMessage(content=system_content)

            # Add a user message to initiate the triage assessment
            user_message = HumanMessage(
                content="Please perform a triage assessment based on the provided patient information and intake conversation data. Follow the ESI algorithm steps and provide your assessment."
            )

            base_model = _get_model()
            structured_model = base_model.with_structured_output(TriageInformation)

            response = await structured_model.ainvoke([system_prompt, user_message])

            return {**state, "triage_info": response}

        except Exception as e:
            # Return state with error information
            return {
                **state,
                "errors": state.get("errors", [])
                + [f"Triage assessment failed: {str(e)}"],
                "triage_info": None,
            }


triage_agent = TriageAgent()
