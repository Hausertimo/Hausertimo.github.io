"""
Timeline Feature Blueprint
==========================

Display company milestones and achievements in a beautiful card-based timeline.

Features:
- Public timeline view at /timeline
- Admin management at /timelineadmin
- Custom flairs/tags with colors
- Expandable timeline entries
- Date-based chronological display

Database Tables (Run in Supabase SQL Editor):

-- Timeline Flairs (tags with colors)
CREATE TABLE IF NOT EXISTS public.timeline_flairs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL DEFAULT '#3869FA',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Timeline Entries
CREATE TABLE IF NOT EXISTS public.timeline_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    topic TEXT NOT NULL,
    description TEXT,
    flair_id UUID REFERENCES public.timeline_flairs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_timeline_entries_date ON public.timeline_entries(date DESC);

-- RLS Policies (Public read, authenticated write)
ALTER TABLE public.timeline_flairs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.timeline_entries ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Allow public read access to flairs" ON public.timeline_flairs FOR SELECT USING (true);
CREATE POLICY "Allow public read access to entries" ON public.timeline_entries FOR SELECT USING (true);

-- Allow authenticated users to manage (you can restrict this to specific admin users)
CREATE POLICY "Allow authenticated users to manage flairs" ON public.timeline_flairs FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Allow authenticated users to manage entries" ON public.timeline_entries FOR ALL USING (auth.role() = 'authenticated');
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from functools import wraps

logger = logging.getLogger(__name__)

# Create Blueprint
timeline_bp = Blueprint('timeline', __name__)

# Supabase client (will be initialized)
supabase = None


def init_dependencies(supabase_client):
    """Initialize dependencies for timeline blueprint"""
    global supabase
    supabase = supabase_client
    logger.info("Timeline blueprint dependencies initialized")


def get_current_user_id():
    """Get current user ID from session"""
    from normscout_auth import get_current_user_id as auth_get_user
    return auth_get_user()


def require_auth(f):
    """Require authentication for admin routes"""
    from normscout_auth import require_auth as auth_require
    return auth_require(f)


# ============================================================================
# PUBLIC ROUTES
# ============================================================================

@timeline_bp.route("/timeline")
def timeline_view():
    """Public timeline view - shows all timeline entries"""
    return render_template('timeline.html')


# ============================================================================
# ADMIN ROUTES
# ============================================================================

@timeline_bp.route("/timelineadmin")
@require_auth
def timeline_admin():
    """Admin page for managing timeline entries and flairs"""
    return render_template('timeline_admin.html')


# ============================================================================
# API ENDPOINTS - Timeline Entries
# ============================================================================

@timeline_bp.route("/api/timeline/entries", methods=['GET'])
def get_timeline_entries():
    """Get all timeline entries with their flairs"""
    try:
        # Query timeline entries joined with flairs, ordered by date DESC
        result = supabase.table('timeline_entries') \
            .select('*, timeline_flairs(id, name, color)') \
            .order('date', desc=True) \
            .execute()

        return jsonify({
            'success': True,
            'entries': result.data
        })
    except Exception as e:
        logger.error(f"Error fetching timeline entries: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@timeline_bp.route("/api/timeline/entries", methods=['POST'])
@require_auth
def create_timeline_entry():
    """Create a new timeline entry"""
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('date') or not data.get('topic'):
            return jsonify({
                'success': False,
                'error': 'Date and topic are required'
            }), 400

        # Create entry
        entry_data = {
            'date': data['date'],
            'topic': data['topic'],
            'description': data.get('description', ''),
            'flair_id': data.get('flair_id')
        }

        result = supabase.table('timeline_entries') \
            .insert(entry_data) \
            .execute()

        return jsonify({
            'success': True,
            'entry': result.data[0]
        })
    except Exception as e:
        logger.error(f"Error creating timeline entry: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@timeline_bp.route("/api/timeline/entries/<entry_id>", methods=['PUT'])
@require_auth
def update_timeline_entry(entry_id):
    """Update an existing timeline entry"""
    try:
        data = request.get_json()

        # Build update data
        update_data = {
            'updated_at': datetime.utcnow().isoformat()
        }

        if 'date' in data:
            update_data['date'] = data['date']
        if 'topic' in data:
            update_data['topic'] = data['topic']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'flair_id' in data:
            update_data['flair_id'] = data['flair_id']

        result = supabase.table('timeline_entries') \
            .update(update_data) \
            .eq('id', entry_id) \
            .execute()

        return jsonify({
            'success': True,
            'entry': result.data[0] if result.data else None
        })
    except Exception as e:
        logger.error(f"Error updating timeline entry: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@timeline_bp.route("/api/timeline/entries/<entry_id>", methods=['DELETE'])
@require_auth
def delete_timeline_entry(entry_id):
    """Delete a timeline entry"""
    try:
        supabase.table('timeline_entries') \
            .delete() \
            .eq('id', entry_id) \
            .execute()

        return jsonify({
            'success': True
        })
    except Exception as e:
        logger.error(f"Error deleting timeline entry: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API ENDPOINTS - Flairs/Tags
# ============================================================================

@timeline_bp.route("/api/timeline/flairs", methods=['GET'])
def get_timeline_flairs():
    """Get all timeline flairs"""
    try:
        result = supabase.table('timeline_flairs') \
            .select('*') \
            .order('name') \
            .execute()

        return jsonify({
            'success': True,
            'flairs': result.data
        })
    except Exception as e:
        logger.error(f"Error fetching timeline flairs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@timeline_bp.route("/api/timeline/flairs", methods=['POST'])
@require_auth
def create_timeline_flair():
    """Create a new flair"""
    try:
        data = request.get_json()

        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Flair name is required'
            }), 400

        flair_data = {
            'name': data['name'],
            'color': data.get('color', '#3869FA')
        }

        result = supabase.table('timeline_flairs') \
            .insert(flair_data) \
            .execute()

        return jsonify({
            'success': True,
            'flair': result.data[0]
        })
    except Exception as e:
        logger.error(f"Error creating timeline flair: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@timeline_bp.route("/api/timeline/flairs/<flair_id>", methods=['PUT'])
@require_auth
def update_timeline_flair(flair_id):
    """Update an existing flair"""
    try:
        data = request.get_json()

        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'color' in data:
            update_data['color'] = data['color']

        result = supabase.table('timeline_flairs') \
            .update(update_data) \
            .eq('id', flair_id) \
            .execute()

        return jsonify({
            'success': True,
            'flair': result.data[0] if result.data else None
        })
    except Exception as e:
        logger.error(f"Error updating timeline flair: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@timeline_bp.route("/api/timeline/flairs/<flair_id>", methods=['DELETE'])
@require_auth
def delete_timeline_flair(flair_id):
    """Delete a flair"""
    try:
        supabase.table('timeline_flairs') \
            .delete() \
            .eq('id', flair_id) \
            .execute()

        return jsonify({
            'success': True
        })
    except Exception as e:
        logger.error(f"Error deleting timeline flair: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
