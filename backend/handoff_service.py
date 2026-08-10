import asyncio
from typing import Optional, List, Dict, Any
from database import get_agents, create_handoff
from ai.crm_ai import auto_route_agent

def trigger_handoff(
    customer_message: str,
    sentiment_score: Optional[float],
    emotion: Optional[str],
    channel: str,
    sender_id: Optional[str] = None,
    sender_name: Optional[str] = None,
    session_id: Optional[str] = None,
    conversation_history: List[Dict[str, Any]] = None,
    customer_id: Optional[int] = None
) -> int:
    """
    Called from ANY channel whenever action == ESCALATE.
    Creates a handoff record and makes it appear in the Agent Console queue.
    """
    if conversation_history is None:
        conversation_history = []
        
    issue_preview = customer_message[:200]
    
    # Use AI routing to pick specialization
    route_info = auto_route_agent(issue_preview)
    specialization = route_info.get("specialization", "general")
    reason = route_info.get("reason", "Needs human assistance")

    # Find best agent
    agents = get_agents()
    available = [a for a in agents if a["status"] == "online" and a["current_conversations"] < a["max_conversations"]]
    
    selected_agent = None
    if available:
        matching = [a for a in available if a["specialization"] == specialization]
        pool = matching if matching else available
        pool.sort(key=lambda x: x["current_conversations"])
        selected_agent = pool[0]

    # Priority logic
    priority = "medium"
    if sentiment_score is not None:
        if sentiment_score < 0.2:
            priority = "urgent"
        elif sentiment_score < 0.4:
            priority = "high"

    agent_id = selected_agent["id"] if selected_agent else None
    
    if session_id is None:
        session_id = f"{channel}-{sender_id or 'unknown'}"
        
    hid = create_handoff(
        session_id=session_id,
        customer_id=customer_id,
        agent_id=agent_id,
        reason=f"[{specialization.upper()}] {reason}",
        sentiment_score=sentiment_score,
        emotion=emotion,
        priority=priority,
        conversation_history=conversation_history,
        channel=channel,
        sender_id=sender_id,
        sender_name=sender_name
    )

    print(f"Handoff triggered for {channel} (ID: {hid})")
    
    # Broadcast to Agent Console
    try:
        import main # Import here to avoid circular dependency
        payload = {
            "type": "new_handoff",
            "handoff": {
                "id": hid,
                "session_id": session_id,
                "channel": channel,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "customer_id": customer_id,
                "agent_id": agent_id,
                "reason": f"[{specialization.upper()}] {reason}",
                "sentiment_score": sentiment_score,
                "emotion": emotion,
                "priority": priority,
                "status": "pending",
                "customer_name": sender_name, # Fallback for frontend
                "message_preview": issue_preview
            }
        }
        # Run coroutine since we might not be in an async context
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(main.agent_manager.broadcast(payload))
        except RuntimeError:
            asyncio.run(main.agent_manager.broadcast(payload))
    except Exception as e:
        print(f"Failed to broadcast handoff {hid}: {e}")

    return hid
