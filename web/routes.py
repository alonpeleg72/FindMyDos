"""
Web routes for the FindMyDos application.
"""

from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import desc
from findmydos.storage.models import Protest
from findmydos.storage.repository import ProtestRepository

# Create blueprint
bp = Blueprint('main', __name__)

# Initialize repository
protest_repo = ProtestRepository()

@bp.route('/')
def index():
    """
    Main page showing recent protests.

    Query parameters:
        limit: Number of protests to show (default: 20)
        offset: Offset for pagination (default: 0)
    """
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    protests = protest_repo.get_recent(limit=limit, offset=offset)

    return render_template('index.html', protests=protests)

@bp.route('/protest/<int:protest_id>')
def protest_detail(protest_id):
    """
    Detailed view of a specific protest.

    Args:
        protest_id: ID of the protest to display
    """
    protest = protest_repo.get_by_id(protest_id)

    if protest is None:
        return render_template('errors/404.html'), 404

    return render_template('protest_detail.html', protest=protest)

@bp.route('/api/protests')
def api_protests():
    """
    API endpoint for getting protests as JSON.

    Query parameters:
        limit: Number of protests to show (default: 20)
        offset: Offset for pagination (default: 0)
    """
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    protests = protest_repo.get_recent(limit=limit, offset=offset)

    return jsonify([protest.to_dict() for protest in protests])

@bp.route('/map')
def map_view():
    """
    Map view showing all protests.
    """
    protests = protest_repo.get_all()
    return render_template('map.html', protests=protests)