from flask import render_template, request, jsonify
from flask_login import login_required
import logging
from . import simulation_bp
from src.web_app.services.simulation_service import SimulationService

logger = logging.getLogger(__name__)

# Note: We do NOT use a singleton here because goals.yaml can change externally.
# Each request gets a fresh instance to ensure goals are loaded from disk.
def get_simulation_service():
    return SimulationService()

@simulation_bp.route('/')
@login_required
def index():
    """Render the Simulation Analysis page."""
    service = get_simulation_service()
    metadata = service.get_simulation_metadata()
    return render_template('reports/simulation.html', **metadata)

@simulation_bp.route('/api/run', methods=['POST'])
@login_required
def run_simulation():
    """Run a Monte Carlo simulation based on provided parameters."""
    try:
        data = request.json
        initial_value = float(data.get('initial_value', 0))
        expected_return = float(data.get('expected_return', 0.07))
        volatility = float(data.get('volatility', 0.15))
        annual_contribution = float(data.get('annual_contribution', 0))
        num_simulations = int(data.get('num_simulations', 1000))
        force_refresh = data.get('force_refresh', False)

        service = get_simulation_service()
        result = service.run_monte_carlo(
            initial_value=initial_value,
            expected_return=expected_return,
            volatility=volatility,
            annual_contribution=annual_contribution,
            num_simulations=num_simulations,
            force_refresh=force_refresh
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running simulation: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@simulation_bp.route('/api/metadata')
@login_required
def get_metadata():
    """Get goals and default assumptions."""
    try:
        service = get_simulation_service()
        return jsonify(service.get_simulation_metadata())
    except Exception as e:
        logger.error(f"Error fetching metadata: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@simulation_bp.route('/api/goals', methods=['GET'])
@login_required
def get_goals():
    """List all goals."""
    try:
        service = get_simulation_service()
        goals = service.goal_manager.list_goals()
        return jsonify({g_id: g.to_dict() for g_id, g in goals.items()})
    except Exception as e:
        logger.error(f"Error listing goals: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@simulation_bp.route('/api/goals', methods=['POST'])
@login_required
def add_goal():
    """Add a new goal."""
    try:
        data = request.json
        goal_id = data.get('id')
        if not goal_id:
            # Generate ID from name if not provided
            goal_id = data.get('name', 'new_goal').lower().replace(' ', '_')
            
        from src.goal_planning.goal_manager import Goal
        new_goal = Goal(
            name=data.get('name'),
            target_amount=float(data.get('target_amount')),
            target_date=data.get('target_date'),
            priority=data.get('priority', 'medium'),
            category=data.get('category', 'retirement'),
            description=data.get('description', ''),
            current_progress=float(data.get('current_progress', 0))
        )
        
        service = get_simulation_service()
        service.goal_manager.add_goal(goal_id, new_goal)
        service.goal_manager.save_goals()
        
        return jsonify({'status': 'success', 'goal_id': goal_id, 'goal': new_goal.to_dict()})
    except Exception as e:
        logger.error(f"Error adding goal: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@simulation_bp.route('/api/goals/<goal_id>', methods=['PUT'])
@login_required
def update_goal(goal_id):
    """Update an existing goal."""
    try:
        data = request.json
        logger.info(f"Received update request for goal_id: '{goal_id}' with data: {data}")
        service = get_simulation_service()
        
        # Debug available goals
        available_goals = list(service.goal_manager.list_goals().keys())
        logger.info(f"Available goals in manager: {available_goals}")
        
        if service.goal_manager.update_goal(goal_id, data):
            service.goal_manager.save_goals()
            updated_goal = service.goal_manager.get_goal(goal_id)
            return jsonify({'status': 'success', 'goal': updated_goal.to_dict()})
        else:
            return jsonify({'error': 'Goal not found'}), 404
    except Exception as e:
        logger.error(f"Error updating goal: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@simulation_bp.route('/api/goals/<goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    """Delete a goal."""
    try:
        service = get_simulation_service()
        if service.goal_manager.remove_goal(goal_id):
            service.goal_manager.save_goals()
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Goal not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting goal: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
