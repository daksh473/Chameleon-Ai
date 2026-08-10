import sys
sys.path.append('backend')
from routers.handoff import agent_message, AgentMessageRequest, call_customer, add_phone, AddPhoneRequest

try:
    print("Testing agent_message...")
    agent_message(6, AgentMessageRequest(message="test"))
    print("Agent message success")
except Exception as e:
    import traceback
    traceback.print_exc()

try:
    print("Testing add_phone...")
    add_phone(6, AddPhoneRequest(phone="1234567890"))
    print("Add phone success")
except Exception as e:
    import traceback
    traceback.print_exc()

try:
    print("Testing call_customer...")
    call_customer(6)
    print("Call customer success")
except Exception as e:
    import traceback
    traceback.print_exc()
