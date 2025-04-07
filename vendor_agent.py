import os
import random
import json 
from typing import TypedDict, List, Annotated, Sequence, Optional
import operator

# Langchain & Langgraph Imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from dotenv import load_dotenv
load_dotenv()


vendors = [
    {
        "vendor_id": "V001",
        "name": "Rapid Plumbers",
        "category_expertise": ["repairs", "plumbing"],
        "response_time_hours": 1,
        "preferred_communication_style": "casual",
        "past_reliability_score": 4.8,
        "constraints": ["Only serves downtown area", "Requires 2hr lead time for non-urgent tasks"]
    },
    {
        "vendor_id": "V002",
        "name": "City Cabs Express",
        "category_expertise": ["travel", "transport"],
        "response_time_hours": 0.25, # 15 minutes
        "preferred_communication_style": "formal",
        "past_reliability_score": 4.5,
        "constraints": ["No airport pickups after midnight"]
    },
    {
        "vendor_id": "V003",
        "name": "Handy Helpers",
        "category_expertise": ["errands", "repairs", "gardening"],
        "response_time_hours": 4,
        "preferred_communication_style": "casual",
        "past_reliability_score": 4.2,
        "constraints": ["Only accepts tasks with >12h lead time"] # [cite: 5]
    },
    {
        "vendor_id": "V004",
        "name": "Formal Fleet",
        "category_expertise": ["travel", "corporate transport"],
        "response_time_hours": 2,
        "preferred_communication_style": "formal",
        "past_reliability_score": 4.9,
        "constraints": ["Minimum booking duration 2 hours"]
    },
     {
        "vendor_id": "V005",
        "name": "Expert Electricians",
        "category_expertise": ["repairs", "electrical"],
        "response_time_hours": 3,
        "preferred_communication_style": "formal",
        "past_reliability_score": 4.6,
        "constraints": ["Requires clear description of issue beforehand", "Does not work on weekends"]
    }
]


class AgentState(TypedDict):
    task: dict                
    available_vendors: List[dict]
    selected_vendor: Optional[dict]
    rejected_vendors: List[str] 
    message: str              
    error: Optional[str]
    max_retries: int          
    retries_left: int         

class VendorAgent:
    def __init__(self, model_name="gemini-2.0-flash-001", temperature=0.7):
        """Initialize the VendorAgent with a Google Generative AI model."""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-001",
            temperature=0.7,
        )
        self.app = self._build_graph()  # Build the state graph
    
    def filter_vendors_by_category(self, vendors, task):
        task_category = task.get("category")
        if not task_category:
            return vendors
        return [v for v in vendors if task_category in v.get("category_expertise", [])]

    def format_vendors_for_prompt(self, vendors):
        if not vendors:
            return "No suitable vendors found for this category or criteria."
        # Include details relevant for selection
        return "\n".join([
            f"- ID: {v['vendor_id']}, Name: {v['name']}, Expertise: {v['category_expertise']}, "
            f"Reliability: {v['past_reliability_score']}, Response Time (hrs): {v['response_time_hours']}, Constraints: {v['constraints']}"
            for v in vendors
        ])

    def select_vendor(self, state: AgentState) -> AgentState:
        """Selects the best vendor based on task and available vendors, excluding rejected ones."""
        print("--- Node: select_vendor ---")
        task = state['task']
        all_vendors = state['available_vendors']
        rejected_ids = state['rejected_vendors']
        retries_left = state['retries_left']

        if retries_left <= 0:
            print("Max retries reached.")
            return {"error": "Max retries reached. Sending to human review."}

        # 1. Filter by category
        filtered_by_cat = self.filter_vendors_by_category(all_vendors, task)

        # 2. Exclude rejected vendors
        eligible_vendors = [v for v in filtered_by_cat if v['vendor_id'] not in rejected_ids]

        if not eligible_vendors:
            print("No eligible vendors found after filtering and exclusion.")
            return {"error": "No eligible vendors left. Sending to human review."}

        # 3. Prepare prompt for LLM
        vendor_list_str = self.format_vendors_for_prompt(eligible_vendors)
        prompt = ChatPromptTemplate.from_template(
            """
            Task Description: {task_description}
            Urgency: {urgency}
            Special Requirements: {special_requirements}

            Eligible Vendors (filtered by category '{task_category}' and excluding previously rejected):
            {vendor_list_str}

            Instructions: Analyze the task and the eligible vendors. Consider expertise, reliability, response time, constraints, and task urgency/requirements.
            Select the single best vendor ID for this task. If multiple are equally good, pick one. If none seem suitable, output 'None'.
            Explain your reasoning briefly and output the chosen vendor ID in the format: Selected Vendor ID: VXXX or Selected Vendor ID: None
            """
        ).format(
            task_description=task['task_description'],
            urgency=task['urgency'],
            special_requirements=task['special_requirements'],
            task_category=task.get('category', 'N/A'),
            vendor_list_str=vendor_list_str
        )

        # 4. Call LLM
        try:
            response_compete = self.llm.invoke(prompt)
            response = response_compete.content
            print(f"LLM Selection Response: {response}")

            # 5. Parse LLM Response (Robust parsing needed here!)
            # Example simple parsing (adapt based on actual LLM output format):
            selected_id = None
            if "Selected Vendor ID:" in response:
                potential_id = response.split("Selected Vendor ID:")[-1].strip()
                if potential_id.startswith("V") and potential_id != "None":
                    selected_id = potential_id

            if selected_id:
                selected_vendor_details = next((v for v in eligible_vendors if v['vendor_id'] == selected_id), None)
                if selected_vendor_details:
                    print(f"Selected Vendor: {selected_id}")
                    return {"selected_vendor": selected_vendor_details, "error": None} # Successfully selected
                else:
                    print(f"Error: LLM selected ID {selected_id} not found in eligible list.")
                    # Maybe retry selection or error out
                    return {"error": f"LLM selected invalid vendor ID {selected_id}"}
            else:
                print("LLM did not select a vendor ('None' or parsing failed).")
                return {"error": "LLM could not select a suitable vendor."}

        except Exception as e:
            print(f"Error during vendor selection LLM call: {e}")
            return {"error": f"LLM call failed: {str(e)}"}


    def generate_communication(self, state: AgentState) -> AgentState:
        """Generates communication message for the selected vendor."""
        print("--- Node: generate_communication ---")
        task = state['task']
        vendor = state['selected_vendor']

        if not vendor:
            # Should not happen if graph logic is correct, but good practice to check
            print("Error: generate_communication called without a selected vendor.")
            return {"message": "", "error": "Cannot generate message without selected vendor."}

        # 1. Prepare prompt
        comm_prompt = ChatPromptTemplate.from_template(
        """
            Generate a message body to send to the vendor '{vendor_name}' about a new task assignment.

            Vendor Details:
            - Preferred Communication Style: {preferred_communication_style}

            Task Details:
            - Description: {task_description}
            - Urgency: {urgency}
            - Special Requirements: {special_requirements}

            Instructions:
            - Write the message in a {preferred_communication_style} tone.
            - Include all relevant task details clearly.
            - Make the message action-oriented with clear next steps (e.g., 'Please reply to confirm you can take this task' or 'Let us know your availability').
            - Generate only the message body, without greetings like 'Hi...' or closings like 'Thanks,...'.
            """
        ).format(
            vendor_name=vendor['name'],
            preferred_communication_style=vendor['preferred_communication_style'],
            task_description=task['task_description'],
            urgency=task['urgency'],
            special_requirements=task['special_requirements']
        )

        # 2. Call LLM
        try:
            message_body = self.llm.invoke(comm_prompt) # Assuming llm is initialized
            print(f"Generated Message: {message_body}")
            return {"message": message_body, "error": None}
        except Exception as e:
            print(f"Error during communication generation LLM call: {e}")
            return {"message": "", "error": f"LLM call failed: {str(e)}"}

    def simulate_vendor_response(self, state: AgentState) -> AgentState:
        """Simulates vendor accepting or rejecting the task."""
        print("--- Node: simulate_vendor_response ---")
        vendor = state['selected_vendor']
        task = state['task']
        if not vendor:
            return {"error": "Cannot simulate response without a selected vendor."} # Should not happen

        # --- Add your simulation logic here ---
        # Example: Vendor V003 rejects urgent tasks, otherwise 50/50 chance
        rejected = False
        if vendor['vendor_id'] == 'V003' and task['urgency'] == 'high':
            rejected = True
            print(f"Simulating REJECTION for {vendor['vendor_id']} (Urgent task for V003)")
        elif random.random() < 0.3: # 30% chance of random rejection
            rejected = True
            print(f"Simulating REJECTION for {vendor['vendor_id']} (Random chance)")
        else:
            print(f"Simulating ACCEPTANCE for {vendor['vendor_id']}")

        if rejected:
            current_rejected = state.get('rejected_vendors', [])
            new_rejected_list = current_rejected + [vendor['vendor_id']]
            # Decrement retries for the next attempt
            new_retries_left = state['retries_left'] - 1
            return {
                "rejected_vendors": new_rejected_list,
                "selected_vendor": None, # Clear current vendor as they rejected
                "message": "",           # Clear message
                "retries_left": new_retries_left,
                "error": "Vendor rejected" # Signal rejection
            }
        else:
            return {"error": None}


    def should_continue(self, state: AgentState) -> str:
        """Determines the next step based on state."""
        error = state.get('error')
        retries_left = state['retries_left']

        if error == "Vendor rejected":
            print(f"Decision: Vendor rejected, {retries_left} retries left.")
            if retries_left > 0:
                return "retry_select_vendor" # Route back to select_vendor
            else:
                print("Decision: Max retries reached.")
                return "human_review" # Route to end state for human review
        elif error:
            # Any other error (no vendors found, LLM failed, etc.)
            print(f"Decision: Error encountered - {error}. Routing to human review.")
            return "human_review" # Route to end state for human review
        else:
            # No error means vendor presumably accepted in the simulation
            print("Decision: Vendor accepted/no error.")
            return "end_process" # Task successfully assigned (or simulated as such)

    
    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("select_vendor", self.select_vendor)
        workflow.add_node("generate_communication", self.generate_communication)
        workflow.add_node("simulate_response", self.simulate_vendor_response)
        workflow.add_node("human_review_node", lambda state: print("--- Task Sent for Human Review --- \nState:", state) or {"error": "Requires Human Intervention"}) # Simple end node

        # Define edges
        workflow.set_entry_point("select_vendor")
        workflow.add_edge("select_vendor", "generate_communication")
        workflow.add_edge("generate_communication", "simulate_response")

        # Conditional edge
        workflow.add_conditional_edges(
            "simulate_response", # Source node
            self.should_continue,     # Function to decide the route
            {
                "retry_select_vendor": "select_vendor", # If retry, go back to select
                "human_review": "human_review_node",    # If error/max retries, go to human review
                "end_process": END                      # If accepted, end the graph
            }
        )

        # Add an edge from the human_review node to END
        workflow.add_edge("human_review_node", END)


        # Compile the graph
        app = workflow.compile()
        return app

        
    def run_workflow(self, task, max_retries=3):
        """Run the vendor selection workflow for a given task."""
        # Create initial state
        initial_state = AgentState(
            task=task,
            available_vendors=vendors,
            selected_vendor=None,
            rejected_vendors=[],
            message="",
            error=None,
            max_retries=max_retries,
            retries_left=max_retries
        )
        
        # Invoke the workflow
        final_state = self.app.invoke(initial_state)
        print(final_state)
        return final_state
