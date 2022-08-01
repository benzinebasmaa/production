

{
    "name": "Quality control",
    "version": "11.0.1.1.0",
    "category": "Quality control",
    "license": "AGPL-3",
    "summary": "Generic infrastructure for quality tests.",
    "author": "OdooMRP team, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/manufacture/tree/10.0/quality_control",
    "depends": [
        "product",
    ],
    "data": [
        "data/quality_control_data.xml",
        "views/qc_menus.xml",
        "views/qc_inspection_view.xml",
        "views/qc_test_category_view.xml",
        "views/qc_test_view.xml",
        "views/product_template_view.xml"
    ],

    "installable": True,
}
