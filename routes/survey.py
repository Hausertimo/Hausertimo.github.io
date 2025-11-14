"""
AI Survey Chat Routes
Conversational surveys with topic-based data gathering
"""
from flask import Blueprint, render_template, request, jsonify
import logging
import uuid
from datetime import datetime
import json

from normscout_auth import supabase, require_auth, get_current_user_id
from services.survey_chat import (
    analyze_topic_completion,
    generate_survey_question,
    generate_welcome_message,
    generate_completion_message,
    check_mandatory_topics,
    calculate_completion_percentage,
    extract_structured_data
)

logger = logging.getLogger(__name__)

survey_bp = Blueprint('survey', __name__)


# ============================================================================
# FRONTEND PAGES
# ============================================================================

@survey_bp.route('/survey')
def survey_page():
    """Render the survey chat page (public-facing)"""
    # Get survey_id from query parameter
    survey_id = request.args.get('id')
    if not survey_id:
        return render_template('error.html',
                             error="Survey Not Found",
                             message="Please provide a valid survey ID."), 404

    # Check if survey exists and is active
    try:
        result = supabase.table('survey_configs')\
            .select('*')\
            .eq('id', survey_id)\
            .eq('is_active', True)\
            .eq('is_deleted', False)\
            .execute()

        if not result.data or len(result.data) == 0:
            return render_template('error.html',
                                 error="Survey Not Found",
                                 message="This survey doesn't exist or is no longer active."), 404

        survey = result.data[0]
        return render_template('survey_chat.html', survey=survey)

    except Exception as e:
        logger.exception(f"Error loading survey page: {e}")
        return render_template('error.html',
                             error="Error",
                             message="Unable to load survey."), 500


@survey_bp.route('/surveycreate')
@require_auth
def survey_create_page():
    """Render the survey creation/management page (admin)"""
    return render_template('survey_builder.html')


# ============================================================================
# SURVEY CONFIG MANAGEMENT (Admin Routes)
# ============================================================================

@survey_bp.route('/api/survey/create', methods=['POST'])
@require_auth
def create_survey():
    """
    Create a new survey configuration

    Expects:
        {
            "name": "Customer Feedback Survey",
            "description": "...",
            "model": "openai/gpt-4o-mini",
            "temperature": 0.7,
            "character_prompt": "You are Emma, a friendly...",
            "survey_explanation": "We're gathering feedback...",
            "topics": [
                {"name": "Name", "mandatory": true, "order": 1},
                {"name": "Email", "mandatory": true, "order": 2},
                ...
            ]
        }

    Returns:
        {"survey_id": "uuid", "message": "Survey created"}
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Validate required fields
        name = data.get('name', 'Untitled Survey').strip()
        topics = data.get('topics', [])

        if not topics or len(topics) == 0:
            return jsonify({"error": "At least one topic is required"}), 400

        # Sort topics by order
        topics = sorted(topics, key=lambda t: t.get('order', 0))

        # Prepare survey config
        survey_data = {
            "user_id": user_id,
            "name": name,
            "description": data.get('description', ''),
            "model": data.get('model', 'openai/gpt-4o-mini'),
            "temperature": float(data.get('temperature', 0.7)),
            "character_prompt": data.get('character_prompt', 'You are a friendly survey assistant.'),
            "survey_explanation": data.get('survey_explanation', ''),
            "topics": json.dumps(topics),
            "is_active": True,
            "is_deleted": False
        }

        # Insert into database
        result = supabase.table('survey_configs').insert(survey_data).execute()

        if not result.data or len(result.data) == 0:
            raise Exception("Failed to create survey")

        survey_id = result.data[0]['id']
        logger.info(f"Created survey {survey_id} for user {user_id}")

        return jsonify({
            "survey_id": survey_id,
            "message": "Survey created successfully"
        }), 201

    except Exception as e:
        logger.exception(f"Error creating survey: {e}")
        return jsonify({"error": str(e)}), 500


@survey_bp.route('/api/survey/configs', methods=['GET'])
@require_auth
def get_surveys():
    """
    Get all surveys for the current user

    Returns:
        {
            "surveys": [
                {
                    "id": "uuid",
                    "name": "...",
                    "is_active": true,
                    "created_at": "...",
                    "response_count": 10
                },
                ...
            ]
        }
    """
    try:
        user_id = get_current_user_id()

        # Get surveys
        result = supabase.table('survey_configs')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('is_deleted', False)\
            .order('created_at', desc=True)\
            .execute()

        surveys = result.data if result.data else []

        # Get response counts for each survey
        for survey in surveys:
            count_result = supabase.table('survey_conversations')\
                .select('id', count='exact')\
                .eq('survey_id', survey['id'])\
                .execute()

            survey['response_count'] = count_result.count if count_result.count else 0

        return jsonify({"surveys": surveys})

    except Exception as e:
        logger.exception(f"Error fetching surveys: {e}")
        return jsonify({"error": str(e)}), 500


@survey_bp.route('/api/survey/config/<survey_id>', methods=['GET'])
@require_auth
def get_survey(survey_id):
    """Get a specific survey config"""
    try:
        user_id = get_current_user_id()

        result = supabase.table('survey_configs')\
            .select('*')\
            .eq('id', survey_id)\
            .eq('user_id', user_id)\
            .eq('is_deleted', False)\
            .execute()

        if not result.data or len(result.data) == 0:
            return jsonify({"error": "Survey not found"}), 404

        survey = result.data[0]
        return jsonify(survey)

    except Exception as e:
        logger.exception(f"Error fetching survey: {e}")
        return jsonify({"error": str(e)}), 500


@survey_bp.route('/api/survey/config/<survey_id>', methods=['PUT'])
@require_auth
def update_survey(survey_id):
    """Update a survey configuration"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Verify ownership
        result = supabase.table('survey_configs')\
            .select('id')\
            .eq('id', survey_id)\
            .eq('user_id', user_id)\
            .execute()

        if not result.data or len(result.data) == 0:
            return jsonify({"error": "Survey not found"}), 404

        # Prepare update data
        update_data = {}

        if 'name' in data:
            update_data['name'] = data['name']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'model' in data:
            update_data['model'] = data['model']
        if 'temperature' in data:
            update_data['temperature'] = float(data['temperature'])
        if 'character_prompt' in data:
            update_data['character_prompt'] = data['character_prompt']
        if 'survey_explanation' in data:
            update_data['survey_explanation'] = data['survey_explanation']
        if 'topics' in data:
            topics = sorted(data['topics'], key=lambda t: t.get('order', 0))
            update_data['topics'] = json.dumps(topics)
        if 'is_active' in data:
            update_data['is_active'] = data['is_active']

        # Update
        result = supabase.table('survey_configs')\
            .update(update_data)\
            .eq('id', survey_id)\
            .execute()

        logger.info(f"Updated survey {survey_id}")
        return jsonify({"message": "Survey updated successfully"})

    except Exception as e:
        logger.exception(f"Error updating survey: {e}")
        return jsonify({"error": str(e)}), 500


@survey_bp.route('/api/survey/config/<survey_id>', methods=['DELETE'])
@require_auth
def delete_survey(survey_id):
    """Soft delete a survey"""
    try:
        user_id = get_current_user_id()

        # Verify ownership
        result = supabase.table('survey_configs')\
            .select('id')\
            .eq('id', survey_id)\
            .eq('user_id', user_id)\
            .execute()

        if not result.data or len(result.data) == 0:
            return jsonify({"error": "Survey not found"}), 404

        # Soft delete
        supabase.table('survey_configs')\
            .update({"is_deleted": True, "is_active": False})\
            .eq('id', survey_id)\
            .execute()

        logger.info(f"Deleted survey {survey_id}")
        return jsonify({"message": "Survey deleted successfully"})

    except Exception as e:
        logger.exception(f"Error deleting survey: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SURVEY CONVERSATION (Public Routes - No Auth Required)
# ============================================================================

@survey_bp.route('/api/survey/start', methods=['POST'])
def start_survey():
    """
    Start a new survey conversation

    Expects:
        {
            "survey_id": "uuid",
            "session_identifier": "optional_browser_fingerprint"
        }

    Returns:
        {
            "conversation_id": "uuid",
            "welcome_message": "Hi! I'm Emma...",
            "first_question": "Let's start with your name..."
        }
    """
    try:
        data = request.get_json()
        survey_id = data.get('survey_id')

        if not survey_id:
            return jsonify({"error": "survey_id is required"}), 400

        # Get survey config
        result = supabase.table('survey_configs')\
            .select('*')\
            .eq('id', survey_id)\
            .eq('is_active', True)\
            .eq('is_deleted', False)\
            .execute()

        if not result.data or len(result.data) == 0:
            return jsonify({"error": "Survey not found or inactive"}), 404

        config = result.data[0]
        topics = json.loads(config['topics']) if isinstance(config['topics'], str) else config['topics']

        # Generate welcome message
        welcome_msg = generate_welcome_message({
            "character_prompt": config['character_prompt'],
            "survey_explanation": config['survey_explanation'],
            "topics": topics
        })

        # Generate first question
        first_topic = topics[0] if topics else None
        if not first_topic:
            return jsonify({"error": "Survey has no topics"}), 400

        first_question = generate_survey_question(
            config={
                "model": config['model'],
                "temperature": config['temperature'],
                "character_prompt": config['character_prompt'],
                "survey_explanation": config['survey_explanation']
            },
            topic=first_topic,
            messages=[],
            attempt_count=1
        )

        # Create conversation record
        conversation_data = {
            "survey_id": survey_id,
            "session_identifier": data.get('session_identifier'),
            "messages": json.dumps([
                {"role": "assistant", "content": welcome_msg, "timestamp": datetime.now().isoformat()},
                {"role": "assistant", "content": first_question, "timestamp": datetime.now().isoformat()}
            ]),
            "topic_progress": json.dumps({}),
            "status": "in_progress",
            "current_topic": first_topic['name'],
            "current_topic_index": 0,
            "gathered_data": json.dumps({}),
            "completion_percentage": 0.0,
            "total_messages": 2
        }

        # Insert conversation
        conv_result = supabase.table('survey_conversations').insert(conversation_data).execute()

        if not conv_result.data or len(conv_result.data) == 0:
            raise Exception("Failed to create conversation")

        conversation_id = conv_result.data[0]['id']
        logger.info(f"Started survey conversation {conversation_id} for survey {survey_id}")

        return jsonify({
            "conversation_id": conversation_id,
            "welcome_message": welcome_msg,
            "first_question": first_question,
            "survey_name": config['name']
        }), 201

    except Exception as e:
        logger.exception(f"Error starting survey: {e}")
        return jsonify({"error": str(e)}), 500


@survey_bp.route('/api/survey/message', methods=['POST'])
def send_message():
    """
    Send a message and get AI response

    Expects:
        {
            "conversation_id": "uuid",
            "message": "My name is John"
        }

    Returns:
        {
            "response": "Great! Now, what's your email?",
            "completed": false,
            "completion_percentage": 16.67,
            "current_topic": "Email"
        }
        OR
        {
            "response": "Thank you!",
            "completed": true,
            "gathered_data": {"Name": "John", "Email": "john@example.com", ...}
        }
    """
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        user_message = data.get('message', '').strip()

        if not conversation_id or not user_message:
            return jsonify({"error": "conversation_id and message are required"}), 400

        # Get conversation
        conv_result = supabase.table('survey_conversations')\
            .select('*')\
            .eq('id', conversation_id)\
            .execute()

        if not conv_result.data or len(conv_result.data) == 0:
            return jsonify({"error": "Conversation not found"}), 404

        conversation = conv_result.data[0]

        # Get survey config
        config_result = supabase.table('survey_configs')\
            .select('*')\
            .eq('id', conversation['survey_id'])\
            .execute()

        if not config_result.data or len(config_result.data) == 0:
            return jsonify({"error": "Survey not found"}), 404

        config = config_result.data[0]
        topics = json.loads(config['topics']) if isinstance(config['topics'], str) else config['topics']

        # Parse conversation data
        messages = json.loads(conversation['messages']) if isinstance(conversation['messages'], str) else conversation['messages']
        topic_progress = json.loads(conversation['topic_progress']) if isinstance(conversation['topic_progress'], str) else conversation['topic_progress']
        current_topic_index = conversation['current_topic_index']

        # Add user message
        messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })

        # Get current topic
        current_topic = topics[current_topic_index]

        # Analyze if topic is complete
        completion_analysis = analyze_topic_completion(
            messages=messages,
            topic=current_topic,
            character_prompt=config['character_prompt'],
            survey_explanation=config['survey_explanation']
        )

        # Update topic progress
        topic_name = current_topic['name']
        if topic_name not in topic_progress:
            topic_progress[topic_name] = {"attempts": 0}

        topic_progress[topic_name]['attempts'] = completion_analysis['attempts']

        if completion_analysis['is_complete']:
            # Topic completed!
            topic_progress[topic_name]['completed'] = True
            topic_progress[topic_name]['data'] = completion_analysis['extracted_data']

            # Move to next topic
            current_topic_index += 1

            if current_topic_index >= len(topics):
                # Survey complete!
                gathered_data = extract_structured_data(topic_progress)
                completion_msg = generate_completion_message(config, gathered_data)

                messages.append({
                    "role": "assistant",
                    "content": completion_msg,
                    "timestamp": datetime.now().isoformat()
                })

                # Update conversation as completed
                update_data = {
                    "messages": json.dumps(messages),
                    "topic_progress": json.dumps(topic_progress),
                    "status": "completed",
                    "gathered_data": json.dumps(gathered_data),
                    "completion_percentage": 100.0,
                    "completed_at": datetime.now().isoformat(),
                    "total_messages": len(messages)
                }

                supabase.table('survey_conversations')\
                    .update(update_data)\
                    .eq('id', conversation_id)\
                    .execute()

                logger.info(f"Survey conversation {conversation_id} completed")

                return jsonify({
                    "response": completion_msg,
                    "completed": True,
                    "gathered_data": gathered_data,
                    "completion_percentage": 100.0
                })

            else:
                # Move to next topic
                next_topic = topics[current_topic_index]
                next_question = generate_survey_question(
                    config={
                        "model": config['model'],
                        "temperature": config['temperature'],
                        "character_prompt": config['character_prompt'],
                        "survey_explanation": config['survey_explanation']
                    },
                    topic=next_topic,
                    messages=messages,
                    attempt_count=1
                )

                messages.append({
                    "role": "assistant",
                    "content": next_question,
                    "timestamp": datetime.now().isoformat()
                })

                completion_pct = calculate_completion_percentage(topics, topic_progress)

                # Update conversation
                update_data = {
                    "messages": json.dumps(messages),
                    "topic_progress": json.dumps(topic_progress),
                    "current_topic": next_topic['name'],
                    "current_topic_index": current_topic_index,
                    "completion_percentage": completion_pct,
                    "total_messages": len(messages)
                }

                supabase.table('survey_conversations')\
                    .update(update_data)\
                    .eq('id', conversation_id)\
                    .execute()

                return jsonify({
                    "response": next_question,
                    "completed": False,
                    "completion_percentage": completion_pct,
                    "current_topic": next_topic['name']
                })

        else:
            # Topic not complete, ask follow-up
            follow_up = generate_survey_question(
                config={
                    "model": config['model'],
                    "temperature": config['temperature'],
                    "character_prompt": config['character_prompt'],
                    "survey_explanation": config['survey_explanation']
                },
                topic=current_topic,
                messages=messages,
                attempt_count=completion_analysis['attempts'] + 1
            )

            messages.append({
                "role": "assistant",
                "content": follow_up,
                "timestamp": datetime.now().isoformat()
            })

            completion_pct = calculate_completion_percentage(topics, topic_progress)

            # Update conversation
            update_data = {
                "messages": json.dumps(messages),
                "topic_progress": json.dumps(topic_progress),
                "completion_percentage": completion_pct,
                "total_messages": len(messages)
            }

            supabase.table('survey_conversations')\
                .update(update_data)\
                .eq('id', conversation_id)\
                .execute()

            return jsonify({
                "response": follow_up,
                "completed": False,
                "completion_percentage": completion_pct,
                "current_topic": current_topic['name']
            })

    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SURVEY RESULTS & ANALYTICS (Admin Routes)
# ============================================================================

@survey_bp.route('/api/survey/responses/<survey_id>', methods=['GET'])
@require_auth
def get_survey_responses(survey_id):
    """
    Get all responses for a survey

    Returns:
        {
            "responses": [
                {
                    "id": "uuid",
                    "started_at": "...",
                    "completed_at": "...",
                    "status": "completed",
                    "gathered_data": {...},
                    "total_messages": 12
                },
                ...
            ]
        }
    """
    try:
        user_id = get_current_user_id()

        # Verify ownership
        config_result = supabase.table('survey_configs')\
            .select('id')\
            .eq('id', survey_id)\
            .eq('user_id', user_id)\
            .execute()

        if not config_result.data or len(config_result.data) == 0:
            return jsonify({"error": "Survey not found"}), 404

        # Get responses
        result = supabase.table('survey_conversations')\
            .select('id, started_at, completed_at, status, gathered_data, total_messages, completion_percentage')\
            .eq('survey_id', survey_id)\
            .order('started_at', desc=True)\
            .execute()

        responses = result.data if result.data else []

        return jsonify({"responses": responses})

    except Exception as e:
        logger.exception(f"Error fetching responses: {e}")
        return jsonify({"error": str(e)}), 500


@survey_bp.route('/api/survey/conversation/<conversation_id>', methods=['GET'])
@require_auth
def get_conversation(conversation_id):
    """Get full conversation details (admin only)"""
    try:
        user_id = get_current_user_id()

        # Get conversation with survey check
        result = supabase.table('survey_conversations')\
            .select('*, survey_configs!inner(user_id)')\
            .eq('id', conversation_id)\
            .execute()

        if not result.data or len(result.data) == 0:
            return jsonify({"error": "Conversation not found"}), 404

        conversation = result.data[0]

        # Check ownership
        if conversation['survey_configs']['user_id'] != user_id:
            return jsonify({"error": "Unauthorized"}), 403

        return jsonify(conversation)

    except Exception as e:
        logger.exception(f"Error fetching conversation: {e}")
        return jsonify({"error": str(e)}), 500


@survey_bp.route('/api/survey/stats/<survey_id>', methods=['GET'])
@require_auth
def get_survey_stats(survey_id):
    """
    Get statistics for a survey

    Returns:
        {
            "total_conversations": 50,
            "completed": 40,
            "in_progress": 8,
            "abandoned": 2,
            "avg_completion_rate": 85.5,
            "avg_messages": 8.5
        }
    """
    try:
        user_id = get_current_user_id()

        # Verify ownership
        config_result = supabase.table('survey_configs')\
            .select('id')\
            .eq('id', survey_id)\
            .eq('user_id', user_id)\
            .execute()

        if not config_result.data or len(config_result.data) == 0:
            return jsonify({"error": "Survey not found"}), 404

        # Get all conversations for this survey
        result = supabase.table('survey_conversations')\
            .select('status, completion_percentage, total_messages')\
            .eq('survey_id', survey_id)\
            .execute()

        conversations = result.data if result.data else []

        # Calculate stats
        total = len(conversations)
        completed = sum(1 for c in conversations if c['status'] == 'completed')
        in_progress = sum(1 for c in conversations if c['status'] == 'in_progress')
        abandoned = sum(1 for c in conversations if c['status'] == 'abandoned')

        avg_completion = sum(c.get('completion_percentage', 0) for c in conversations) / total if total > 0 else 0
        avg_messages = sum(c.get('total_messages', 0) for c in conversations) / total if total > 0 else 0

        return jsonify({
            "total_conversations": total,
            "completed": completed,
            "in_progress": in_progress,
            "abandoned": abandoned,
            "avg_completion_rate": round(avg_completion, 2),
            "avg_messages": round(avg_messages, 2)
        })

    except Exception as e:
        logger.exception(f"Error fetching stats: {e}")
        return jsonify({"error": str(e)}), 500
