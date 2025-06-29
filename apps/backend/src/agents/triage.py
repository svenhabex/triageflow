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
        """
        Assess the patient's symptoms and history to determine the appropriate level of care.
        Uses structured JSON context instead of full message history.
        """
        from .utils import build_context_from_state, format_context_as_json

        try:
            required_context = ["patient_info", "intake_conversation_info"]
            context_data = build_context_from_state(state, required_context)

            system_message = SystemMessage(
                content="""You are an expert triage AI assistant. Your purpose is to accurately assess a patient's situation based on provided data and assign a triage level according to the 5-level Emergency Severity Index (ESI) algorithm.

                TRIAGE INSTRUCTIONS (Follow these steps in order):

                Step 1: Decision Point A - Is immediate life-saving intervention required?
                Check for: Not breathing, pulseless, severe respiratory distress, SpO2 < 90%, acute mental status change, unresponsive.
                If YES, assign ESI Level 1 and stop.

                Step 2: Decision Point B - Is this a high-risk situation?
                Consider: Could deteriorate quickly, threat to life/limb/organ, confused/lethargic/disoriented, severe pain (7/10+).
                If YES, assign ESI Level 2 and stop.

                Step 3: Decision Point C - How many resources are needed?
                Resources: Labs, ECG, X-rays, CT/MRI/Ultrasound, IV fluids, IV/IM medications, specialty consultation.
                NOT Resources: History & physical, oral medications, simple wound care, crutches/splints.
                - Many resources (2+): ESI Level 3
                - One resource: ESI Level 4  
                - No resources: ESI Level 5

                Step 4: Decision Point D - Check Vital Signs (ESI Level 3 only)
                Danger thresholds: HR > 100, RR > 20, SpO2 < 92%
                If dangerous vitals, upgrade to ESI Level 2.

                Step 5: Determine Medical Category
                Choose from: [Cardiology, Neurology, Pulmonology, Orthopedics, Gastroenterology, General, Trauma]

                Patient data will be provided in JSON format."""
            )

            context_message = HumanMessage(
                content=f"""Please perform a triage assessment based on the following patient data:
                {format_context_as_json(context_data)}
                Follow the ESI algorithm steps and provide your assessment with clear reasoning."""
            )

            base_model = _get_model()
            structured_model = base_model.with_structured_output(TriageInformation)

            triage_messages = [system_message, context_message]
            triage_response = await structured_model.ainvoke(triage_messages)

            full_messages = state.get("messages", [])
            updated_messages = full_messages + triage_messages

            return {
                **state,
                "messages": updated_messages,
                "triage_info": triage_response,
            }

        except Exception as e:
            return {
                **state,
                "errors": state.get("errors", [])
                + [f"Triage assessment failed: {str(e)}"],
                "triage_info": None,
            }
