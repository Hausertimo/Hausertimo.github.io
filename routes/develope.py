"""
/develope route - AI-powered product compliance development workspace
Conversational norm matching and compliance guidance
"""
from flask import Blueprint, render_template, request, jsonify, session, Response, stream_with_context
import logging
import uuid
from datetime import datetime
import json

from services.product_conversation import (
    analyze_completeness,
    generate_next_question,
    build_final_summary
)
from services.norm_matcher import match_norms, match_norms_streaming

logger = logging.getLogger(__name__)

develope_bp = Blueprint('develope', __name__)

# In-memory storage for sessions (TODO: move to Redis)
conversation_sessions = {}


@develope_bp.route('/develope')
def develope_page():
    """Render the main develope page"""
    return render_template('develope.html')


@develope_bp.route('/api/develope/start', methods=['POST'])
def start_conversation():
    """
    Start a new product conversation session

    Expects:
        {"initial_input": "user's product description"}

    Returns:
        {"session_id": "uuid", "response": "AI response"}
    """
    try:
        data = request.get_json()
        initial_input = data.get('initial_input', '').strip()

        if not initial_input:
            return jsonify({"error": "No input provided"}), 400

        # Create new session
        session_id = str(uuid.uuid4())
        conversation_history = [
            {"role": "user", "content": initial_input}
        ]

        # Check completeness
        completeness = analyze_completeness(conversation_history)

        if completeness["is_complete"]:
            # Already have enough info!
            response = {
                "session_id": session_id,
                "complete": True,
                "message": f"Perfect! I have all the information I need. {completeness['reasoning']}"
            }
        else:
            # Generate follow-up question
            question = generate_next_question(
                conversation_history,
                completeness["missing_info"]
            )

            conversation_history.append({"role": "assistant", "content": question})

            response = {
                "session_id": session_id,
                "complete": False,
                "message": question,
                "missing": completeness["missing_info"]
            }

        # Store session
        conversation_sessions[session_id] = {
            "history": conversation_history,
            "started": datetime.now().isoformat(),
            "complete": completeness["is_complete"]
        }

        logger.info(f"Started conversation session {session_id}")
        return jsonify(response)

    except Exception as e:
        logger.exception(f"Error starting conversation: {e}")
        return jsonify({"error": str(e)}), 500


@develope_bp.route('/api/develope/respond', methods=['POST'])
def respond_to_conversation():
    """
    Continue an existing conversation

    Expects:
        {"session_id": "uuid", "message": "user's response"}

    Returns:
        {"complete": bool, "message": "AI response"}
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        user_message = data.get('message', '').strip()

        if not session_id or session_id not in conversation_sessions:
            return jsonify({"error": "Invalid session"}), 400

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Get session
        session_data = conversation_sessions[session_id]
        conversation_history = session_data["history"]

        # Add user response
        conversation_history.append({"role": "user", "content": user_message})

        # Check completeness
        completeness = analyze_completeness(conversation_history)

        if completeness["is_complete"]:
            # Done!
            session_data["complete"] = True
            response = {
                "complete": True,
                "message": f"Excellent! I have all the information I need. {completeness['reasoning']}",
                "reasoning": completeness["reasoning"]
            }
        else:
            # Generate next question
            question = generate_next_question(
                conversation_history,
                completeness["missing_info"]
            )

            conversation_history.append({"role": "assistant", "content": question})

            response = {
                "complete": False,
                "message": question,
                "missing": completeness["missing_info"]
            }

        logger.info(f"Conversation {session_id} - complete: {completeness['is_complete']}")
        return jsonify(response)

    except Exception as e:
        logger.exception(f"Error in conversation: {e}")
        return jsonify({"error": str(e)}), 500


@develope_bp.route('/api/develope/analyze', methods=['POST'])
def analyze_norms():
    """
    Analyze norms for a completed conversation

    Expects:
        {"session_id": "uuid"}

    Returns:
        {"product_description": "...", "norms": [...]}
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if not session_id or session_id not in conversation_sessions:
            return jsonify({"error": "Invalid session"}), 400

        session_data = conversation_sessions[session_id]

        if not session_data.get("complete"):
            return jsonify({"error": "Conversation not complete"}), 400

        # Build final product description
        product_description = build_final_summary(session_data["history"])

        # Match norms (this will take a while)
        matched_norms = match_norms(product_description, max_workers=10)

        # Store results in session
        session_data["product_description"] = product_description
        session_data["matched_norms"] = matched_norms
        session_data["analyzed"] = datetime.now().isoformat()

        logger.info(f"Analyzed norms for session {session_id}: {len(matched_norms)} norms matched")

        return jsonify({
            "product_description": product_description,
            "norms": matched_norms,
            "total_norms": len(matched_norms)
        })

    except Exception as e:
        logger.exception(f"Error analyzing norms: {e}")
        return jsonify({"error": str(e)}), 500


@develope_bp.route('/api/develope/analyze-stream', methods=['GET'])
def analyze_norms_stream():
    """
    Analyze norms with real-time progress updates via Server-Sent Events

    Expects:
        ?session_id=uuid (query parameter)

    Returns:
        SSE stream with progress updates
    """
    session_id = request.args.get('session_id')

    if not session_id or session_id not in conversation_sessions:
        return jsonify({"error": "Invalid session"}), 400

    session_data = conversation_sessions[session_id]

    if not session_data.get("complete"):
        return jsonify({"error": "Conversation not complete"}), 400

    def generate():
        try:
            # Phase 1: Building summary
            yield f"data: {json.dumps({'phase': 'summary', 'status': 'Building product summary...'})}\n\n"

            product_description = build_final_summary(session_data["history"])

            # Phase 2: Stream norm matching with real-time progress
            matched_norms = None

            for event_type, *event_data in match_norms_streaming(product_description, max_workers=10):
                if event_type == 'progress':
                    completed, total, norm_id = event_data

                    # Create varied, descriptive status messages
                    if completed <= total * 0.33:
                        status = f"Analyzing safety requirements... ({completed}/{total})"
                    elif completed <= total * 0.66:
                        status = f"Checking compliance standards... ({completed}/{total})"
                    else:
                        status = f"Reviewing regulations... ({completed}/{total})"

                    progress_data = {
                        'phase': 'analyzing',
                        'progress': completed,
                        'total': total,
                        'status': status
                    }
                    yield f"data: {json.dumps(progress_data)}\n\n"

                elif event_type == 'complete':
                    matched_norms = event_data[0]

            # Phase 3: Finalization
            yield f"data: {json.dumps({'phase': 'finalizing', 'status': 'Finalizing results...'})}\n\n"

            # Store results in session
            session_data["product_description"] = product_description
            session_data["matched_norms"] = matched_norms
            session_data["analyzed"] = datetime.now().isoformat()

            logger.info(f"Analyzed norms for session {session_id}: {len(matched_norms)} norms matched")

            # Phase 4: Complete with results
            yield f"data: {json.dumps({'phase': 'complete', 'product_description': product_description, 'norms': matched_norms, 'total_norms': len(matched_norms)})}\n\n"

        except Exception as e:
            logger.exception(f"Error in streaming analysis: {e}")
            yield f"data: {json.dumps({'phase': 'error', 'error': str(e)})}\n\n"

    response = Response(stream_with_context(generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


@develope_bp.route('/api/develope/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session data"""
    if session_id not in conversation_sessions:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(conversation_sessions[session_id])
