{
    'name': 'Cetic production',
    'summary': 'Gestion de la production',
    'sequence': 30,
    'category': 'Industries',
    'depends': ['mrp', 'hr'],
    'data': [
        'data/sequence_data.xml',
        'views/equipement.xml',
        'views/equipement_view.xml',
        'views/document_view.xml',
        'views/marque_view.xml',
        'views/outils_view.xml',
        'views/composant_view.xml',


    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
