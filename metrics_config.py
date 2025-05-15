"""Configuration file for metrics and performance tables."""

# Dictionary mapping roles to their URLs
ROLE_URLS = {
    'forklift_driver': 'https://unisco0-my.sharepoint.com/:w:/g/personal/raj_shah_unisco_com/Ee0rUEVWR9BJtH9iWeuGTNsBtG5gF-iD9XiT97Pi_ge6cA?e=9d6nPk',
    'picker_packer': 'https://unisco0-my.sharepoint.com/:w:/g/personal/raj_shah_unisco_com/ESHNS_gDRdlBjxEfOycKNyYBFoDP6pFYFTINQ2t_jOKUHA?e=5yp9bY',
    'bendi_driver': 'https://unisco0-my.sharepoint.com/:w:/g/personal/raj_shah_unisco_com/EZpyeq3lM_RIsr7tVSZuK48BHN4dMX5EcSsEX-IWhKL7fg?e=gKCkT3',
    'consolidation': 'https://unisco0-my.sharepoint.com/:w:/g/personal/raj_shah_unisco_com/Ed6u1ibr3gVEluDH1BjUv-UB7OZRC-3cGfq3s4TnrmBIPQ?e=vYNjFA',
    'lumper': 'https://unisco0-my.sharepoint.com/:w:/g/personal/raj_shah_unisco_com/EQsd3xgbC_ZOmi8V6LjyS4IBmHyls22OGvZtibIcXV7VnA?e=schNVl',
    'receiver': 'https://unisco0-my.sharepoint.com/:w:/g/personal/raj_shah_unisco_com/Eds2vl1Jgh9NnSQZHA6v1ksBicOMtSLIwYaa7nwN09zzJw?e=1ExE07',
    'general_labor': 'https://unisco0-my.sharepoint.com/:w:/g/personal/raj_shah_unisco_com/EeUPBbHILtlKnzaulGQMPEwBG6ue-nqyZ8tFzr9Cs4B0Sw?e=u99mOX'
}

# Default URL for roles not found in the mapping
DEFAULT_ROLE_URL = 'https://unisco0-my.sharepoint.com/:w:/g/personal/raj_shah_unisco_com/EeUPBbHILtlKnzaulGQMPEwBG6ue-nqyZ8tFzr9Cs4B0Sw?e=aUbvnM'

# Training requirements per role
TRAINING_REQUIREMENTS = {
    'forklift_driver': {
        'required_training': ['safety', 'equipment_operation', 'warehouse_procedures'],
        'certification_renewal_months': 12
    },
    'picker_packer': {
        'required_training': ['safety', 'warehouse_procedures', 'quality_control'],
        'certification_renewal_months': 24
    },
    'bendi_driver': {
        'required_training': ['safety', 'equipment_operation', 'warehouse_procedures'],
        'certification_renewal_months': 12
    },
    'consolidation': {
        'required_training': ['safety', 'warehouse_procedures', 'quality_control'],
        'certification_renewal_months': 24
    },
    'lumper': {
        'required_training': ['safety', 'warehouse_procedures'],
        'certification_renewal_months': 24
    },
    'receiver': {
        'required_training': ['safety', 'equipment_operation', 'warehouse_procedures'],
        'certification_renewal_months': 12
    },
    'general_labor': {
        'required_training': ['safety', 'warehouse_procedures'],
        'certification_renewal_months': 24
    }
} 