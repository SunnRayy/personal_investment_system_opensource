export interface Taxonomy {
    id: number;
    name: string;
    description?: string;
    is_hierarchical: boolean;
    allow_multiple: boolean;
    tags_count: number;
}

export interface Tag {
    id: number;
    name: string;
    description?: string;
    color: string;
    parent_id?: number;
    parent_name?: string;
    is_top_level: boolean;
    taxonomy_id?: number;
}

export interface ClassificationRule {
    id: number;
    name: string;
    description?: string;
    taxonomy_id: number;
    tag_id: number;
    match_type: string;
    match_field: string;
    pattern: string;
    priority: number;
    is_active: boolean;
    taxonomy_name?: string;
    tag_name?: string;
}

export interface RiskProfile {
    id: number;
    name: string;
    description?: string;
    is_active: boolean;
}

export interface TargetAllocation {
    id: number;
    tag_id: number;
    tag_name: string;
    target_weight: number;
}
