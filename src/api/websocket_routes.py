"""
WebSocket routes for interactive data collection
"""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.services.session_manager import session_manager
from src.services.response_validator import ResponseValidator
from src.services.question_service import QuestionService
from src.services.workflow_service import WorkflowService

router = APIRouter()
validator = ResponseValidator()
question_service = QuestionService()
workflow_service = WorkflowService()


@router.websocket("/ws/collect")
async def websocket_collect(websocket: WebSocket):
    """
    WebSocket endpoint for interactive data collection
    
    Flow:
    1. Client connects, receives session_id
    2. Server asks first question
    3. Client responds
    4. Server validates response
    5. If unsatisfactory, ask follow-up (max 1 follow-up per question)
    6. If still unsatisfactory after follow-up, skip and move to next question
    7. Repeat until all required fields are filled
    8. Send completion message with collected data
    """
    await websocket.accept()
    
    # Create new session
    session_id = session_manager.create_session()
    
    # Keepalive task to send ping every 30 seconds
    async def keepalive():
        while True:
            await asyncio.sleep(30)
            try:
                await websocket.send_json({"type": "ping"})
            except:
                break
    
    keepalive_task = asyncio.create_task(keepalive())
    
    try:
        # Send session ID and welcome message
        await websocket.send_json({
            "type": "session_started",
            "session_id": session_id,
            "message": "Welcome! I'll help you collect information about your project. Let's start!"
        })
        
        # Main conversation loop
        while True:
            # Get collected data
            session = session_manager.get_session(session_id)
            if not session:
                await websocket.send_json({
                    "type": "error",
                    "message": "Session not found"
                })
                break
            
            # Get skipped fields
            skipped_fields = session.skipped_fields.copy() if hasattr(session, 'skipped_fields') else set()
            
            # Check if all fields are complete using question service
            # Use full session.data to include empty strings for skipped fields
            is_done = question_service.is_complete(session.data, skipped_fields)
            
            # Debug logging
            if is_done:
                print(f"✅ All fields complete! Starting workflow...")
                print(f"   Collected fields: {[k for k, v in session.data.items() if v]}")
                print(f"   Skipped fields: {skipped_fields}")
            
            if is_done:
                # All done collecting data!
                data = session_manager.get_data(session_id)
                print(f"📊 Collected data keys: {list(data.keys())}")
                
                try:
                    await websocket.send_json({
                        "type": "complete",
                        "message": "Thank you! I've collected all the necessary information. Now generating TRD, time and cost estimates...",
                        "data": data
                    })
                    print("✅ Sent 'complete' message")
                    
                    # Execute workflow in background
                    await websocket.send_json({
                        "type": "workflow_started",
                        "message": "Starting workflow generation..."
                    })
                    print("✅ Sent 'workflow_started' message")
                    
                    print("🔄 Executing workflow...")
                    workflow_result = await workflow_service.execute_workflow(data)
                    print(f"✅ Workflow result: success={workflow_result.get('success')}")
                    
                    if workflow_result["success"]:
                        # Send workflow results
                        await websocket.send_json({
                            "type": "workflow_complete",
                            "message": "Workflow completed successfully!",
                            "trd": workflow_result["trd"],
                            "time_estimate": workflow_result["time_estimate"],
                            "cost_estimate": workflow_result["cost_estimate"],
                            "backend_status": workflow_result["backend_status"]
                        })
                        print("✅ Sent 'workflow_complete' message")
                    else:
                        # Workflow failed
                        error_msg = workflow_result.get('error', 'Unknown error')
                        print(f"❌ Workflow failed: {error_msg}")
                        await websocket.send_json({
                            "type": "workflow_error",
                            "message": f"Workflow generation failed: {error_msg}",
                            "error": error_msg
                        })
                        
                except Exception as e:
                    import traceback
                    error_msg = f"Error executing workflow: {str(e)}"
                    print(f"❌ Workflow error: {error_msg}")
                    print(traceback.format_exc())
                    try:
                        await websocket.send_json({
                            "type": "workflow_error",
                            "message": error_msg,
                            "error": str(e)
                        })
                    except Exception as send_error:
                        print(f"❌ Could not send error message: {str(send_error)}")
                
                break
            
            # Use question service to determine what to ask next
            # Pass skipped fields to never ask them again
            next_field = question_service.get_next_field_to_ask(session.data, skipped_fields)
            
            if next_field is None:
                # Should not happen if is_complete check worked, but handle it
                await websocket.send_json({
                    "type": "error",
                    "message": "Unable to determine next question. Please try again."
                })
                break
            
            # Generate question using OpenAI
            session.current_question = next_field
            # Get context of already filled fields
            context = {k: v for k, v in session.data.items() if v is not None}
            question = await question_service.generate_question(next_field, context)
            
            await websocket.send_json({
                "type": "question",
                "field": next_field,
                "question": question,
                "session_id": session_id
            })
            
            # Handle responses for this question (including follow-ups)
            question_answered = False
            current_question = question  # Track the current question (original or follow-up)
            while not question_answered:
                try:
                    data = await websocket.receive_json()
                    
                    # Handle ping/pong for keepalive
                    if data.get("type") == "pong":
                        continue  # Just acknowledge, don't process
                    
                    if data.get("type") == "response":
                        response_text = data.get("response", "").strip()
                        
                        if not response_text:
                            # Empty response, ask follow-up
                            follow_up_count = session_manager.get_follow_up_count(session_id, next_field)
                            if follow_up_count < 2:
                                # Generate follow-up question using OpenAI
                                follow_up_question = await question_service.generate_follow_up_question(
                                    current_question, response_text, next_field
                                )
                                await websocket.send_json({
                                    "type": "follow_up",
                                    "field": next_field,
                                    "question": follow_up_question,
                                    "session_id": session_id
                                })
                                session_manager.increment_follow_up(session_id, next_field)
                                current_question = follow_up_question  # Update current question to the follow-up
                                # Stay in loop to wait for follow-up response
                                continue
                            else:
                                # Already asked 2 follow-ups, accept empty and move on
                                session_manager.update_field(session_id, next_field, "")
                                await websocket.send_json({
                                    "type": "accepted",
                                    "field": next_field,
                                    "message": "Moving on to the next question.",
                                    "session_id": session_id
                                })
                                question_answered = True
                                break
                        
                        # Validate response
                        try:
                            is_satisfactory, follow_up_question = await validator.is_response_satisfactory(
                                current_question, response_text, next_field
                            )
                        except Exception as e:
                            # If validation fails, accept the response and move on
                            import traceback
                            print(f"⚠️ Validation error for {next_field}: {str(e)}")
                            print(traceback.format_exc())
                            is_satisfactory = True
                            follow_up_question = None
                        
                        if is_satisfactory:
                            # Save the response
                            session_manager.update_field(session_id, next_field, response_text)
                            await websocket.send_json({
                                "type": "accepted",
                                "field": next_field,
                                "message": "Thank you! I've saved that information.",
                                "session_id": session_id
                            })
                            question_answered = True
                        else:
                            # Response not satisfactory
                            follow_up_count = session_manager.get_follow_up_count(session_id, next_field)
                            if follow_up_count < 2:
                                # Generate follow-up question using OpenAI to clarify
                                try:
                                    if follow_up_question:
                                        follow_up_q = follow_up_question
                                    else:
                                        follow_up_q = await question_service.generate_follow_up_question(
                                            current_question, response_text, next_field
                                        )
                                    await websocket.send_json({
                                        "type": "follow_up",
                                        "field": next_field,
                                        "question": follow_up_q,
                                        "session_id": session_id
                                    })
                                    session_manager.increment_follow_up(session_id, next_field)
                                    current_question = follow_up_q  # Update current question to the follow-up
                                    # Stay in loop to wait for follow-up response
                                    continue
                                except Exception as e:
                                    # If follow-up generation fails, accept the response and move on
                                    import traceback
                                    print(f"⚠️ Follow-up generation error for {next_field}: {str(e)}")
                                    print(traceback.format_exc())
                                    session_manager.update_field(session_id, next_field, response_text)
                                    await websocket.send_json({
                                        "type": "accepted",
                                        "field": next_field,
                                        "message": "Thank you! I've saved that information.",
                                        "session_id": session_id
                                    })
                                    question_answered = True
                            else:
                                # Already asked 2 follow-ups, accept the response and move on
                                session_manager.update_field(session_id, next_field, response_text)
                                await websocket.send_json({
                                    "type": "accepted",
                                    "field": next_field,
                                    "message": "Thank you! I've saved that information.",
                                    "session_id": session_id
                                })
                                question_answered = True
                    
                    elif data.get("type") == "skip":
                        # User wants to skip this question
                        # First 3 fields (appName, problemSolved, coreFeatures) cannot be skipped
                        required_fields = ["appName", "problemSolved", "coreFeatures"]
                        if next_field in required_fields:
                            await websocket.send_json({
                                "type": "error",
                                "field": next_field,
                                "message": f"{next_field} is a required field and cannot be skipped. Please provide an answer.",
                                "session_id": session_id
                            })
                            # Don't mark as answered, continue asking
                            continue
                        else:
                            # Mark as permanently skipped
                            session_manager.mark_field_skipped(session_id, next_field)
                            await websocket.send_json({
                                "type": "skipped",
                                "field": next_field,
                                "message": f"Skipped {next_field} as requested.",
                                "session_id": session_id
                            })
                            question_answered = True
                    
                    elif data.get("type") == "cancel":
                        # User wants to cancel
                        await websocket.send_json({
                            "type": "cancelled",
                            "message": "Session cancelled."
                        })
                        return  # Exit the entire function
                        
                except WebSocketDisconnect:
                    return  # Exit the entire function
                except Exception as e:
                    import traceback
                    error_msg = f"Error processing response: {str(e)}"
                    print(f"❌ WebSocket error: {error_msg}")
                    print(traceback.format_exc())
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "message": error_msg
                        })
                    except:
                        pass  # Connection might be closed
                    question_answered = True  # Move to next question on error
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        import traceback
        error_msg = f"An error occurred: {str(e)}"
        print(f"❌ WebSocket outer error: {error_msg}")
        print(traceback.format_exc())
        try:
            await websocket.send_json({
                "type": "error",
                "message": error_msg
            })
        except:
            pass
    finally:
        # Cancel keepalive task
        keepalive_task.cancel()
        try:
            await keepalive_task
        except asyncio.CancelledError:
            pass
        # Clean up session (optional - you might want to keep it for a while)
        # session_manager.delete_session(session_id)

