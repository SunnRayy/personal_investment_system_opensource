from flask import jsonify, request, render_template
from src.database import get_session, Taxonomy, Tag, AssetTag, Asset, CalculationStrategy, ClassificationRule, RiskProfile, TargetAllocation
from . import logic_studio_bp
import logging

logger = logging.getLogger(__name__)

@logic_studio_bp.route('/')
def index():
    """Render the Logic Studio main page"""
    return render_template('logic_studio/index.html')

# --- Taxonomy APIs ---

@logic_studio_bp.route('/api/taxonomies', methods=['GET'])
def get_taxonomies():
    """List all taxonomies"""
    session = get_session()
    try:
        taxonomies = session.query(Taxonomy).all()
        return jsonify([{
            'id': t.id,
            'name': t.name,
            'description': t.description,
            'is_hierarchical': t.is_hierarchical,
            'allow_multiple': t.allow_multiple,
            'tags_count': len(t.tags)
        } for t in taxonomies])
    finally:
        session.close()

@logic_studio_bp.route('/api/taxonomies', methods=['POST'])
def create_taxonomy():
    """Create a new taxonomy"""
    data = request.json
    session = get_session()
    try:
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
            
        taxonomy = Taxonomy(
            name=data['name'],
            description=data.get('description'),
            is_hierarchical=data.get('is_hierarchical', False),
            allow_multiple=data.get('allow_multiple', False)
        )
        session.add(taxonomy)
        session.commit()
        return jsonify({'message': 'Taxonomy created', 'id': taxonomy.id})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# --- Tag APIs ---

@logic_studio_bp.route('/api/taxonomies/<int:taxonomy_id>/tags', methods=['GET'])
def get_tags(taxonomy_id):
    """List tags for a specific taxonomy"""
    session = get_session()
    try:
        tags = session.query(Tag).filter_by(taxonomy_id=taxonomy_id).all()
        return jsonify([{
            'id': t.id,
            'name': t.name,
            'description': t.description,
            'color': t.color,
            'parent_id': t.parent_id,
            'parent_name': t.parent.name if t.parent else None,
            'is_top_level': t.is_top_level
        } for t in tags])
    finally:
        session.close()

@logic_studio_bp.route('/api/taxonomies/<int:taxonomy_id>/tags', methods=['POST'])
def create_tag(taxonomy_id):
    """Create a new tag in a taxonomy"""
    data = request.json
    session = get_session()
    try:
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
            
        tag = Tag(
            taxonomy_id=taxonomy_id,
            name=data['name'],
            description=data.get('description'),
            color=data.get('color', 'blue'),
            parent_id=data.get('parent_id'),
            is_top_level=data.get('is_top_level', False)
        )
        session.add(tag)
        session.commit()
        return jsonify({'message': 'Tag created', 'id': tag.id})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@logic_studio_bp.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """Delete a tag and cleanup dependencies"""
    session = get_session()
    try:
        tag = session.query(Tag).get(tag_id)
        if not tag:
            return jsonify({'error': 'Tag not found'}), 404
            
        # 1. Unlink children (set parent_id to None)
        # Or should we delete them? For now, unlink to be safe.
        children = session.query(Tag).filter_by(parent_id=tag.id).all()
        for child in children:
            child.parent_id = None
            
        # 2. Delete Target Allocations
        session.query(TargetAllocation).filter_by(tag_id=tag.id).delete()
        
        # 3. Delete Asset Tags (remove associations)
        session.query(AssetTag).filter_by(tag_id=tag.id).delete()
        
        # 4. Delete Classification Rules
        session.query(ClassificationRule).filter_by(tag_id=tag.id).delete()
        
        # 5. Delete the Tag
        session.delete(tag)
        
        session.commit()
        return jsonify({'message': 'Tag deleted'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@logic_studio_bp.route('/api/tags/<int:tag_id>', methods=['PUT'])
def update_tag(tag_id):
    """Update a tag"""
    data = request.json
    session = get_session()
    try:
        tag = session.query(Tag).get(tag_id)
        if not tag:
            return jsonify({'error': 'Tag not found'}), 404
            
        if 'name' in data:
            tag.name = data['name']
        if 'description' in data:
            tag.description = data['description']
        if 'color' in data:
            tag.color = data['color']
            
        session.commit()
        return jsonify({'message': 'Tag updated'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# ... (Strategy APIs remain unchanged) ...

# --- Rule APIs ---
# ... (Rule APIs remain unchanged) ...

# --- Audit API ---

@logic_studio_bp.route('/api/audit', methods=['GET'])
def get_asset_audit():
    """
    Get audit data for all assets.
    Returns: Asset Name, Current Tag, Top Level Class, Active Rule
    """
    session = get_session()
    try:
        # Fetch all assets
        assets = session.query(Asset).all()
        
        # Fetch all active rules for matching context
        rules = session.query(ClassificationRule).filter_by(is_active=True).order_by(ClassificationRule.priority.desc()).all()
        
        # Helper to find matching rule (simple version)
        def find_matching_rule(asset):
            from src.logic_layer.auto_tagger import AutoTagger
            # We reuse the matching logic from AutoTagger but without applying
            # This is a bit inefficient for large datasets but fine for now
            tagger = AutoTagger(session) 
            for rule in rules:
                if tagger._matches(rule, asset):
                    return rule.name
            return None

        audit_data = []
        for asset in assets:
            # Get current tags
            # We assume one primary tag for classification for now, or list all
            asset_tags = session.query(AssetTag).filter_by(asset_id=asset.asset_id).all()
            
            primary_tag = None
            top_level = None
            
            if asset_tags:
                # Just take the first one for now, or prioritize 'Asset Class' taxonomy
                # Ideally we filter by taxonomy_id corresponding to 'Asset Class'
                tag = asset_tags[0].tag
                primary_tag = tag.name
                if tag.parent:
                    top_level = tag.parent.name
                elif tag.is_top_level:
                    top_level = tag.name # It is its own top level
            
            audit_data.append({
                'asset_id': asset.asset_id,
                'asset_name': asset.asset_name,
                'asset_type': asset.asset_type,
                'current_tag': primary_tag,
                'top_level_class': top_level,
                'active_rule': find_matching_rule(asset)
            })
            
        return jsonify(audit_data)
    finally:
        session.close()

@logic_studio_bp.route('/api/tier-audit', methods=['GET'])
def get_tier_audit():
    """
    Get audit data for Asset Tier classification.
    Returns: Asset Name, Current Tier (if assigned), Active Tier Rule
    """
    session = get_session()
    try:
        TIER_TAXONOMY_ID = 2  # Asset Tier taxonomy
        
        # Fetch all assets
        assets = session.query(Asset).all()
        
        # Fetch active Tier rules
        tier_rules = session.query(ClassificationRule).filter_by(
            taxonomy_id=TIER_TAXONOMY_ID,
            is_active=True
        ).order_by(ClassificationRule.priority.desc()).all()
        
        # Get tier tags for lookup
        tier_tags = {tag.id: tag.name for tag in session.query(Tag).filter_by(taxonomy_id=TIER_TAXONOMY_ID).all()}
        
        # Helper to find matching tier rule
        def find_tier_rule(asset):
            from src.logic_layer.auto_tagger import AutoTagger
            tagger = AutoTagger(session)
            for rule in tier_rules:
                if tagger._matches(rule, asset):
                    return rule.name
            return None
        
        audit_data = []
        for asset in assets:
            # Get Asset Tier tag specifically
            tier_tag_link = session.query(AssetTag).join(Tag).filter(
                AssetTag.asset_id == asset.asset_id,
                Tag.taxonomy_id == TIER_TAXONOMY_ID
            ).first()
            
            current_tier = None
            if tier_tag_link:
                current_tier = tier_tags.get(tier_tag_link.tag_id)
            
            audit_data.append({
                'asset_id': asset.asset_id,
                'asset_name': asset.asset_name,
                'asset_type': asset.asset_type,
                'current_tier': current_tier,
                'active_rule': find_tier_rule(asset)
            })
            
        return jsonify(audit_data)
    finally:
        session.close()

@logic_studio_bp.route('/api/assets/<asset_id>', methods=['POST'])
def update_asset(asset_id):
    """Update asset details (e.g. Type)"""
    data = request.json
    session = get_session()
    try:
        asset = session.query(Asset).filter_by(asset_id=asset_id).first()
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
            
        if 'asset_type' in data:
            asset.asset_type = data['asset_type']
            
        session.commit()
        return jsonify({'message': 'Asset updated'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@logic_studio_bp.route('/api/assets/batch-update', methods=['POST'])
def batch_update_assets():
    """Batch update assets (e.g. set Type for multiple assets)"""
    data = request.json
    session = get_session()
    try:
        asset_ids = data.get('asset_ids', [])
        updates = data.get('updates', {})
        
        if not asset_ids or not updates:
            return jsonify({'error': 'Missing asset_ids or updates'}), 400
            
        assets = session.query(Asset).filter(Asset.asset_id.in_(asset_ids)).all()
        count = 0
        for asset in assets:
            if 'asset_type' in updates:
                asset.asset_type = updates['asset_type']
            count += 1
            
        session.commit()
        return jsonify({'message': f'Updated {count} assets'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# --- Risk Profile APIs ---

@logic_studio_bp.route('/api/risk-profiles', methods=['GET'])
def get_risk_profiles():
    """List all risk profiles"""
    session = get_session()
    try:
        profiles = session.query(RiskProfile).all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'is_active': p.is_active
        } for p in profiles])
    finally:
        session.close()

@logic_studio_bp.route('/api/risk-profiles/<int:profile_id>/allocations', methods=['GET'])
def get_allocations(profile_id):
    """Get allocations for a profile"""
    session = get_session()
    try:
        allocations = session.query(TargetAllocation).filter_by(profile_id=profile_id).all()
        return jsonify([{
            'id': a.id,
            'tag_id': a.tag_id,
            'tag_name': a.tag.name,
            'target_weight': a.target_weight
        } for a in allocations])
    finally:
        session.close()

@logic_studio_bp.route('/api/risk-profiles/<int:profile_id>/allocations', methods=['POST'])
def update_allocations(profile_id):
    """Update allocations for a profile"""
    data = request.json
    session = get_session()
    try:
        # data should be a list of {tag_id: weight} or {tag_name: weight}
        # Let's assume list of {tag_id: 1, weight: 0.5}
        
        updates = data.get('allocations', [])
        
        for item in updates:
            tag_id = item.get('tag_id')
            weight = item.get('weight')
            
            allocation = session.query(TargetAllocation).filter_by(profile_id=profile_id, tag_id=tag_id).first()
            if allocation:
                allocation.target_weight = weight
            else:
                allocation = TargetAllocation(profile_id=profile_id, tag_id=tag_id, target_weight=weight)
                session.add(allocation)
        
        session.commit()
        
        # Invalidate Report Cache so compass updates immediately
        try:
            from src.web_app.services.report_service import get_report_service
            get_report_service().clear_cache()
            logger.info("Cleared report cache after allocation update")
        except Exception as cache_e:
            logger.warning(f"Failed to clear report cache: {cache_e}")

        return jsonify({'message': 'Allocations updated'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@logic_studio_bp.route('/api/risk-profiles/<int:profile_id>/activate', methods=['POST'])
def set_active_profile(profile_id):
    """Set a risk profile as active"""
    session = get_session()
    try:
        # Deactivate all
        session.query(RiskProfile).update({RiskProfile.is_active: False})
        
        # Activate target
        profile = session.query(RiskProfile).get(profile_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
            
        profile.is_active = True
        session.commit()
        
        # Invalidate Report Cache so compass updates immediately
        try:
            from src.web_app.services.report_service import get_report_service
            get_report_service().clear_cache()
            logger.info("Cleared report cache after profile activation")
        except Exception as cache_e:
            logger.warning(f"Failed to clear report cache: {cache_e}")

        return jsonify({'message': f'Profile {profile.name} is now active'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@logic_studio_bp.route('/api/risk-profiles', methods=['POST'])
def create_risk_profile():
    """Create a new risk profile"""
    data = request.json
    session = get_session()
    try:
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
            
        profile = RiskProfile(
            name=data['name'],
            description=data.get('description'),
            is_active=False
        )
        session.add(profile)
        session.commit()
        return jsonify({'message': 'Risk Profile created', 'id': profile.id})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# --- UI Routes ---

@logic_studio_bp.route('/allocations')
def allocations():
    """Render the Target Allocations editor"""
    return render_template('logic_studio/allocations.html')

# --- Auto-Tagging API ---

@logic_studio_bp.route('/api/auto-tag', methods=['POST'])
def trigger_auto_tagging():
    """Trigger the auto-tagging engine for all assets"""
    from src.logic_layer.auto_tagger import AutoTagger
    
    try:
        tagger = AutoTagger()
        count = tagger.process_all_assets()
        return jsonify({'message': f'Auto-tagging completed. Updated {count} assets.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Strategy APIs ---

@logic_studio_bp.route('/api/strategies/<asset_id>', methods=['GET'])
def get_strategy(asset_id):
    """Get calculation strategy for an asset"""
    session = get_session()
    try:
        strategy = session.query(CalculationStrategy).filter_by(asset_id=asset_id).first()
        if not strategy:
            return jsonify({})
            
        return jsonify({
            'asset_id': strategy.asset_id,
            'cost_basis_method': strategy.cost_basis_method,
            'currency_strategy': strategy.currency_strategy,
            'fixed_currency_rate': strategy.fixed_currency_rate,
            'dividend_strategy': strategy.dividend_strategy,
            'notes': strategy.notes
        })
    finally:
        session.close()

@logic_studio_bp.route('/api/strategies/<asset_id>', methods=['POST'])
def save_strategy(asset_id):
    """Save or update calculation strategy for an asset"""
    data = request.json
    session = get_session()
    try:
        strategy = session.query(CalculationStrategy).filter_by(asset_id=asset_id).first()
        
        if not strategy:
            strategy = CalculationStrategy(asset_id=asset_id)
            session.add(strategy)
            
        strategy.cost_basis_method = data.get('cost_basis_method', 'FIFO')
        strategy.currency_strategy = data.get('currency_strategy', 'Spot')
        strategy.fixed_currency_rate = data.get('fixed_currency_rate')
        strategy.dividend_strategy = data.get('dividend_strategy', 'Cash')
        strategy.notes = data.get('notes')
        
        session.commit()
        return jsonify({'message': 'Strategy saved'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# --- Rule APIs ---

@logic_studio_bp.route('/api/rules', methods=['GET'])
def get_rules():
    """List all classification rules"""
    session = get_session()
    try:
        rules = session.query(ClassificationRule).order_by(ClassificationRule.priority.desc()).all()
        return jsonify([{
            'id': r.id,
            'name': r.name,
            'description': r.description,
            'taxonomy_id': r.taxonomy_id,
            'tag_id': r.tag_id,
            'match_type': r.match_type,
            'match_field': r.match_field,
            'pattern': r.pattern,
            'priority': r.priority,
            'is_active': r.is_active,
            'taxonomy_name': r.taxonomy.name if r.taxonomy else '',
            'tag_name': r.tag.name if r.tag else ''
        } for r in rules])
    finally:
        session.close()

@logic_studio_bp.route('/api/rules', methods=['POST'])
def create_rule():
    """Create a new classification rule"""
    data = request.json
    session = get_session()
    try:
        if not data.get('name') or not data.get('pattern'):
            return jsonify({'error': 'Name and Pattern are required'}), 400
            
        rule = ClassificationRule(
            name=data['name'],
            description=data.get('description'),
            taxonomy_id=data['taxonomy_id'],
            tag_id=data['tag_id'],
            match_type=data.get('match_type', 'contains'),
            match_field=data.get('match_field', 'asset_name'),
            pattern=data['pattern'],
            priority=data.get('priority', 0),
            is_active=data.get('is_active', True)
        )
        session.add(rule)
        session.commit()
        return jsonify({'message': 'Rule created', 'id': rule.id})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@logic_studio_bp.route('/api/rules/<int:rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """Delete a classification rule"""
    session = get_session()
    try:
        rule = session.query(ClassificationRule).get(rule_id)
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
            
        session.delete(rule)
        session.commit()
        return jsonify({'message': 'Rule deleted'})
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


